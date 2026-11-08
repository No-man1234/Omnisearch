# OmniSearch — Multi-Tenant Hybrid Search Engine

[![PostgreSQL 17](https://img.shields.io/badge/PostgreSQL-17-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![pgvector 0.8.2](https://img.shields.io/badge/pgvector-0.8.2-blue?style=flat-square)](https://github.com/pgvector/pgvector)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![FastEmbed](https://img.shields.io/badge/FastEmbed-ONNX_CPU-orange?style=flat-square)](https://github.com/qdrant/fastembed)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

An enterprise-grade, multi-tenant hybrid search engine built entirely on **PostgreSQL**. It combines dense semantic retrieval (`pgvector` HNSW cosine distance) and sparse lexical matching (Postgres Full-Text Search `tsvector`) using **Reciprocal Rank Fusion (RRF)**, with bank-vault tenant data isolation enforced at the database engine level via **Row-Level Security (RLS)**.

---

## The Problem OmniSearch Solves

Most modern search and RAG (Retrieval-Augmented Generation) architectures suffer from two major problems:

1. **The Infrastructure Sprawl Nightmare**: Teams often deploy and sync three distinct distributed systems:
   * A relational database (Postgres/MySQL) for primary data
   * An external vector database (Pinecone/Milvus/Weaviate) for semantic search
   * A Lucene cluster (Elasticsearch/OpenSearch) for keyword matching
   
   Keeping these systems synchronized across updates, deletions, and failures is brittle, complex, and expensive.

2. **The Multi-Tenant Leakage Trap**: When using global vector indexes across multiple enterprise customers, traditional vector search performs nearest-neighbor lookups over all data. Without native row-level authorization, a nearest-neighbor traversal can easily surface documents belonging to other tenants.

**OmniSearch consolidates everything into a single PostgreSQL engine.**

---

## Architectural Overview

```
                                ┌─────────────────────────────┐
                                │   Precision Studio Web UI   │
                                │   (Tailwind + Alpine.js)    │
                                └──────────────┬──────────────┘
                                               │ HTTP / REST
                                               ▼
                                ┌─────────────────────────────┐
                                │       FastAPI Backend       │
                                │  (Async Transaction Pool)   │
                                └──────────────┬──────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       │                                               │
                       ▼                                               ▼
             ┌───────────────────┐                         ┌───────────────────────┐
             │     FastEmbed     │                         │   PostgreSQL 17 DB    │
             │ (Local ONNX, CPU) │                         │  Row-Level Security   │
             │  ~65MB footprint  │                         └───────────┬───────────┘
             └───────────────────┘                                     │
                                               ┌───────────────────────┴───────────────────────┐
                                               ▼                                               ▼
                                    ┌─────────────────────┐                         ┌─────────────────────┐
                                    │      pgvector       │                         │  Full-Text Search   │
                                    │  HNSW Cosine Index  │                         │      GIN Index      │
                                    │  vector(384) Dense  │                         │   tsvector Sparse   │
                                    └──────────┬──────────┘                         └──────────┬──────────┘
                                               │                                               │
                                               └───────────────────────┬───────────────────────┘
                                                                       │
                                                                       ▼
                                                        ┌─────────────────────────────┐
                                                        │ Reciprocal Rank Fusion (RRF)│
                                                        │    + Row-Level Security     │
                                                        └─────────────────────────────┘
```

---

## Key Features

- **Native Row-Level Security (RLS)**: Scoped strictly per-transaction with `set_config('app.current_tenant_id', ..., true)`. Zero cross-tenant data leakage, even on global vector graph traversals.
- **Reciprocal Rank Fusion (RRF)**: Merges dense semantic and sparse lexical ranks entirely inside PostgreSQL via a single SQL Common Table Expression (CTE).
- **HNSW Vector Indexing**: Sub-millisecond approximate nearest neighbor (ANN) vector queries with `pgvector 0.8.2`.
- **BM25-Equivalent Lexical Search**: Uses PostgreSQL `tsvector`, `GIN` indexing, and `websearch_to_tsquery` with position-density cover ranking (`ts_rank_cd`).
- **Feather-Light Local AI**: Generates 384-dimensional dense vectors using `FastEmbed` with `bge-small-en-v1.5` over CPU ONNX Runtime (~65 MB disk footprint, no PyTorch, 0 cloud API fees).
- **Precision Studio UI**: High-density developer interface crafted with clean typography (`Plus Jakarta Sans` + `JetBrains Mono`), dual-stream explainability, and an interactive RLS isolation verification laboratory.

---

## How Reciprocal Rank Fusion Works in SQL

For each document $d$ evaluated across the vector and keyword streams, the fused rank score is computed as:

$$\text{RRF Score}(d) = \sum_{m \in \{\text{vector}, \text{keyword}\}} \frac{1}{k + \text{rank}_m(d)}$$

Where $k$ is the smoothing constant (default: `60`).

```sql
WITH vector_matches AS (
    SELECT 
        id, title, content, metadata,
        ROW_NUMBER() OVER (ORDER BY embedding <=> %(vec)s::vector) AS rank_vec,
        (1 - (embedding <=> %(vec)s::vector)) AS vector_similarity
    FROM documents
    WHERE (1 - (embedding <=> %(vec)s::vector)) >= %(min_sim)s
    ORDER BY embedding <=> %(vec)s::vector
    LIMIT %(candidate_limit)s
),
keyword_matches AS (
    SELECT 
        id, title, content, metadata,
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
```

---

## Row-Level Security (RLS) Implementation

To prevent superuser privileges (`rolbypassrls = true`) from accidentally bypassing security checks during tenant queries, every connection executes within a transaction that drops privileges to a standard role:

```python
@contextmanager
def get_db(tenant_id: str | None = None):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.transaction():
            if tenant_id:
                with conn.cursor() as cur:
                    # Switch to non-bypass role
                    cur.execute("SET LOCAL ROLE authenticated;")
                    # Bind tenant context strictly to this transaction
                    cur.execute("SELECT set_config('app.current_tenant_id', %s, true);", (str(tenant_id),))
            with conn.cursor() as cur:
                yield cur
```

The table security policy enforces row validation:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON documents
FOR ALL
USING (
    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
)
WITH CHECK (
    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
);
```

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- A PostgreSQL 15+ database with `pgvector` enabled (e.g. [Supabase](https://supabase.com), [Neon](https://neon.tech), or self-hosted Postgres).

### 2. Clone and Setup
```bash
git clone https://github.com/No-man1234/Omnisearch.git
cd Omnisearch

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your connection string:
```bash
cp .env.example .env
```
```ini
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres?sslmode=require
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
```

### 4. Initialize Database & Seed Demo Data
```bash
# Creates tables, vector indexes, GIN full-text indexes, and RLS policies
python init_db.py

# Seeds 3 enterprise tenants (Finance, Defense, Biotech) with realistic documents
python seed_data.py
```

### 5. Start the Application Server
```bash
uvicorn main:app --reload --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/tenants` | List all registered tenants |
| `POST` | `/api/tenants` | Create a new tenant organization (`name`, `slug`, `description`) |
| `GET` | `/api/tenants/{tenant_id}/documents` | Retrieve all documents belonging to a tenant (RLS enforced) |
| `POST` | `/api/tenants/{tenant_id}/documents` | Ingest and vectorize a new document for a tenant |
| `POST` | `/api/search` | Execute hybrid RRF, vector-only, or keyword-only search |
| `POST` | `/api/isolation-test` | Run an automated cross-tenant security verification benchmark |

Interactive Swagger API docs are accessible at **`http://127.0.0.1:8000/docs`**.

---

## Project Structure

```
Omnisearch/
├── db.py               # Transaction-scoped connection manager with RLS bindings
├── embeddings.py       # FastEmbed ONNX local embedding engine
├── init_db.py          # PostgreSQL schema, pgvector HNSW & GIN indexes, RLS setup
├── main.py             # FastAPI backend application & API routing
├── search_engine.py    # Reciprocal Rank Fusion (RRF) query & ingestion pipeline
├── seed_data.py        # Multi-tenant sample data generator
├── static/
│   └── index.html      # Precision Studio UI (Tailwind + Alpine.js)
├── tests/
│   ├── test_api.py     # Endpoint integration test suite
│   ├── test_rls.py     # Row-Level Security isolation verification test
│   └── test_search.py  # Hybrid search and ranking validation test
├── .env.example        # Environment variable template
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

---

## License

This project is licensed under the [MIT License](LICENSE).
