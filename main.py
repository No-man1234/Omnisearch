import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import search_engine

app = FastAPI(
    title="Multi-Tenant Hybrid Search Engine",
    description="PostgreSQL + Row-Level Security (RLS) + pgvector (HNSW) + Full-Text Search (BM25) with Reciprocal Rank Fusion (RRF)",
    version="1.0.0"
)

# Static files for the single-page frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class TenantCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class DocumentCreate(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    tenant_id: str
    query: str
    mode: str = "hybrid"  # 'hybrid', 'vector', or 'keyword'
    top_k: int = 10
    candidate_limit: int = 30
    rrf_k: int = 60

class IsolationTestRequest(BaseModel):
    source_tenant_id: str
    target_tenant_id: str
    query: str

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Multi-Tenant Hybrid Search Engine API is running. Check /docs for Swagger UI."}

@app.get("/api/tenants")
def get_tenants():
    return search_engine.list_tenants()

@app.post("/api/tenants")
def post_tenant(tenant: TenantCreate):
    return search_engine.create_tenant(name=tenant.name, slug=tenant.slug, description=tenant.description)

@app.get("/api/tenants/{tenant_id}/documents")
def get_documents(tenant_id: str):
    return search_engine.list_documents(tenant_id=tenant_id)

@app.post("/api/tenants/{tenant_id}/documents")
def post_document(tenant_id: str, doc: DocumentCreate):
    return search_engine.ingest_document(
        tenant_id=tenant_id,
        title=doc.title,
        content=doc.content,
        metadata=doc.metadata
    )

@app.post("/api/search")
def search(req: SearchRequest):
    if not req.query.strip():
        return []
    
    if req.mode == "vector":
        return search_engine.vector_only_search(
            tenant_id=req.tenant_id,
            query=req.query,
            top_k=req.top_k
        )
    elif req.mode == "keyword":
        return search_engine.keyword_only_search(
            tenant_id=req.tenant_id,
            query=req.query,
            top_k=req.top_k
        )
    else:  # hybrid
        return search_engine.hybrid_search(
            tenant_id=req.tenant_id,
            query=req.query,
            top_k=req.top_k,
            candidate_limit=req.candidate_limit,
            rrf_k=req.rrf_k
        )

@app.post("/api/isolation-test")
def test_isolation(req: IsolationTestRequest):
    """
    Directly demonstrates PostgreSQL Row-Level Security:
    Executes the exact same query under both source_tenant_id and target_tenant_id.
    """
    source_results = search_engine.hybrid_search(
        tenant_id=req.source_tenant_id,
        query=req.query,
        top_k=5
    )
    target_results = search_engine.hybrid_search(
        tenant_id=req.target_tenant_id,
        query=req.query,
        top_k=5
    )
    
    return {
        "query": req.query,
        "source_tenant": {
            "tenant_id": req.source_tenant_id,
            "hits_count": len(source_results),
            "hits": source_results
        },
        "target_tenant": {
            "tenant_id": req.target_tenant_id,
            "hits_count": len(target_results),
            "hits": target_results
        },
        "isolation_verified": len(target_results) == 0 or all(r["id"] not in [s["id"] for s in source_results] for r in target_results),
        "explanation": "PostgreSQL Row-Level Security guarantees that no rows outside the authenticated tenant_id can ever be read, even when performing global vector nearest-neighbor graph searches or text match scans."
    }
