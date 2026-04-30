"""
Database initialization: PostgreSQL tables + DrugBank XML seeding.
"""
import sys
from pathlib import Path

from ....legacy import printmeup as pm


def seed_drugs_if_empty():
    """Check if the drug catalog has data; if empty, run the seed script."""
    from .sql_client import init_sql_db
    from .seed_drugbank_sql import is_db_seeded, main as seed_main

    init_sql_db()

    if is_db_seeded():
        pm.inf("Drug catalog already contains data — skipping seed.")
        return

    pm.inf("Drug catalog is empty — seeding from DrugBank XML …")

    project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        seed_main([])
    except Exception as e:
        pm.err(e=e, m="Failed to seed drug catalog from DrugBank XML")


async def init_tables():
    """Initialize all PostgreSQL tables and seed drug data."""
    from .sql_client import init_sql_db

    pm.inf("Initializing PostgreSQL tables...")

    try:
        init_sql_db()
        seed_drugs_if_empty()
        pm.suc("All databases initialized")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize databases")
        raise
