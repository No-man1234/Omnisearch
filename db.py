import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment or .env file.")

@contextmanager
def get_db(tenant_id: str | None = None):
    """
    Context manager that yields a psycopg cursor with Row-Level Security (RLS)
    scoped strictly to the given tenant_id.
    
    1. 'SET LOCAL ROLE authenticated' drops superuser/bypassrls privileges for this transaction.
    2. 'SELECT set_config('app.current_tenant_id', ..., true)' binds the tenant strictly to the transaction.
    3. When the transaction commits or aborts, both the role and session config are reset automatically.
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.transaction():
            if tenant_id:
                with conn.cursor() as cur:
                    # Switch to authenticated role which obeys RLS
                    cur.execute("SET LOCAL ROLE authenticated;")
                    cur.execute("SELECT set_config('app.current_tenant_id', %s, true);", (str(tenant_id),))
            
            with conn.cursor() as cur:
                yield cur
