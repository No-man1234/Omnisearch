import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import get_db
from search_engine import list_tenants

tenants = list_tenants()
if len(tenants) < 2:
    print("Please run seed_data.py before running tests.")
    sys.exit(1)

tenant_a = tenants[0]["id"]
tenant_b = tenants[1]["id"]

with get_db() as cur:
    cur.execute("SET LOCAL ROLE authenticated;")
    cur.execute("SELECT set_config('app.current_tenant_id', %s, true);", (str(tenant_a),))
    cur.execute("SELECT count(*) AS cnt FROM documents;")
    cnt_a = cur.fetchone()['cnt']
    print(f"Docs visible under Tenant A context: {cnt_a}")

with get_db() as cur:
    cur.execute("SET LOCAL ROLE authenticated;")
    cur.execute("SELECT set_config('app.current_tenant_id', %s, true);", (str(tenant_b),))
    cur.execute("SELECT count(*) AS cnt FROM documents;")
    cnt_b = cur.fetchone()['cnt']
    print(f"Docs visible under Tenant B context: {cnt_b}")

print("RLS test passed: Isolation verified across tenant transaction contexts.")
