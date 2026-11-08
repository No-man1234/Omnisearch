import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from search_engine import list_tenants, hybrid_search, vector_only_search, keyword_only_search

tenants = list_tenants()
if not tenants:
    print("No tenants found. Run seed_data.py first.")
    sys.exit(1)

acme = next((t for t in tenants if t['slug'] == 'acme-finance'), tenants[0])
print(f"Executing search verification against tenant: {acme['name']}")

results = hybrid_search(tenant_id=str(acme['id']), query="revenue growth AI", top_k=5)
print(f"\nFound {len(results)} hybrid matches:")
for r in results:
    print(f" - [{r['title']}] RRF Score: {r['rrf_score']:.5f} | Vec Rank: #{r['rank_vec']} ({r['vector_similarity']*100:.1f}%) | KW Rank: #{r['rank_kw']} ({r['kw_score']:.3f})")
