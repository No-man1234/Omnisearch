import json
import uuid
from typing import List, Dict, Any, Optional
from db import get_db
from embeddings import get_embedding

def create_tenant(name: str, slug: str, description: Optional[str] = None) -> Dict[str, Any]:
    with get_db() as cur:
        cur.execute(
            """
            INSERT INTO tenants (name, slug, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
            RETURNING id, name, slug, description, created_at;
            """,
            (name, slug, description)
        )
        return cur.fetchone()

def list_tenants() -> List[Dict[str, Any]]:
    with get_db() as cur:
        cur.execute("SELECT id, name, slug, description, created_at FROM tenants ORDER BY name ASC;")
        return cur.fetchall()

def ingest_document(tenant_id: str, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Ingests a document for a specific tenant:
    1. Computes the dense embedding vector.
    2. Stores title, content, metadata, embedding, and generated tsvector in Postgres.
    3. RLS ensures this document is strictly associated with tenant_id.
    """
    if metadata is None:
        metadata = {}

    # Generate dense vector embedding
    embedding_vec = get_embedding(f"{title}\n{content}")
    vec_str = f"[{','.join(f'{x:.6f}' for x in embedding_vec)}]"

    with get_db(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            INSERT INTO documents (tenant_id, title, content, metadata, embedding)
            VALUES (%s, %s, %s, %s::jsonb, %s::vector)
            RETURNING id, tenant_id, title, content, metadata, created_at;
            """,
            (tenant_id, title, content, json.dumps(metadata), vec_str)
        )
        return cur.fetchone()

def list_documents(tenant_id: str) -> List[Dict[str, Any]]:
    """Returns documents strictly belonging to tenant_id (enforced by RLS)."""
    with get_db(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            SELECT id, tenant_id, title, content, metadata, created_at
            FROM documents
            ORDER BY created_at DESC;
            """
        )
        return cur.fetchall()

def hybrid_search(
    tenant_id: str,
    query: str,
    top_k: int = 10,
    candidate_limit: int = 30,
    rrf_k: int = 60,
    min_vector_sim: float = 0.35
) -> List[Dict[str, Any]]:
    """
    Performs Reciprocal Rank Fusion (RRF) combining:
    1. Dense Vector Search (pgvector HNSW cosine distance with relevance cutoff)
    2. Sparse Lexical Search (Postgres tsvector / websearch_to_tsquery)
    
    All execution happens within PostgreSQL under Row-Level Security (RLS) for tenant_id.
    """
    query_vec = get_embedding(query)
    vec_str = f"[{','.join(f'{x:.6f}' for x in query_vec)}]"

    query_sql = """
    WITH vector_matches AS (
        SELECT 
            id, 
            title, 
            content, 
            metadata,
            ROW_NUMBER() OVER (ORDER BY embedding <=> %(vec)s::vector) AS rank_vec,
            (1 - (embedding <=> %(vec)s::vector)) AS vector_similarity
        FROM documents
        WHERE (1 - (embedding <=> %(vec)s::vector)) >= %(min_sim)s
        ORDER BY embedding <=> %(vec)s::vector
        LIMIT %(candidate_limit)s
    ),
    keyword_matches AS (
        SELECT 
            id, 
            title, 
            content, 
            metadata,
            ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('english', %(query)s)) DESC) AS rank_kw,
            ts_rank_cd(tsv, websearch_to_tsquery('english', %(query)s)) AS kw_score
        FROM documents
        WHERE tsv @@ websearch_to_tsquery('english', %(query)s)
        ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('english', %(query)s)) DESC
        LIMIT %(candidate_limit)s
    )
    SELECT 
        COALESCE(v.id, k.id) AS id,
        COALESCE(v.title, k.title) AS title,
        COALESCE(v.content, k.content) AS content,
        COALESCE(v.metadata, k.metadata) AS metadata,
        v.rank_vec,
        k.rank_kw,
        COALESCE(v.vector_similarity, 0.0) AS vector_similarity,
        COALESCE(k.kw_score, 0.0) AS kw_score,
        (
            COALESCE(1.0 / (%(rrf_k)s + v.rank_vec), 0.0) +
            COALESCE(1.0 / (%(rrf_k)s + k.rank_kw), 0.0)
        ) AS rrf_score
    FROM vector_matches v
    FULL OUTER JOIN keyword_matches k ON v.id = k.id
    ORDER BY rrf_score DESC
    LIMIT %(top_k)s;
    """

    with get_db(tenant_id=tenant_id) as cur:
        cur.execute(
            query_sql,
            {
                "vec": vec_str,
                "query": query,
                "candidate_limit": candidate_limit,
                "rrf_k": rrf_k,
                "top_k": top_k,
                "min_sim": min_vector_sim
            }
        )
        return cur.fetchall()

def vector_only_search(tenant_id: str, query: str, top_k: int = 10, min_vector_sim: float = 0.35) -> List[Dict[str, Any]]:
    """Performs pure semantic vector search under tenant RLS."""
    query_vec = get_embedding(query)
    vec_str = f"[{','.join(f'{x:.6f}' for x in query_vec)}]"
    
    with get_db(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            SELECT 
                id, 
                title, 
                content, 
                metadata,
                (1 - (embedding <=> %s::vector)) AS vector_similarity,
                ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS rank_vec
            FROM documents
            WHERE (1 - (embedding <=> %s::vector)) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (vec_str, vec_str, vec_str, min_vector_sim, vec_str, top_k)
        )
        return cur.fetchall()

def keyword_only_search(tenant_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Performs pure BM25/FTS keyword search under tenant RLS."""
    with get_db(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            SELECT 
                id, 
                title, 
                content, 
                metadata,
                ts_rank_cd(tsv, websearch_to_tsquery('english', %s)) AS kw_score,
                ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('english', %s)) DESC) AS rank_kw
            FROM documents
            WHERE tsv @@ websearch_to_tsquery('english', %s)
            ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('english', %s)) DESC
            LIMIT %s;
            """,
            (query, query, query, top_k)
        )
        return cur.fetchall()
