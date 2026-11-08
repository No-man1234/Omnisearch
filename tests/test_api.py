import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_system():
    res = client.get("/api/tenants")
    assert res.status_code == 200, "Failed to list tenants"
    tenants = res.json()
    assert len(tenants) > 0, "No tenants found"
    
    t_id = tenants[0]["id"]
    res_docs = client.get(f"/api/tenants/{t_id}/documents")
    assert res_docs.status_code == 200, "Failed to fetch tenant docs"
    
    search_res = client.post("/api/search", json={
        "tenant_id": t_id,
        "query": "revenue",
        "mode": "hybrid",
        "top_k": 5
    })
    assert search_res.status_code == 200, "Search query failed"
    print(f"API Test Passed: {len(tenants)} tenants, {len(res_docs.json())} docs, search successful.")

if __name__ == "__main__":
    test_system()
