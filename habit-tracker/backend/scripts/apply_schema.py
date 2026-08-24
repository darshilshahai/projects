"""Apply backend/sql/001_schema.sql using DATABASE_URL from .env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = (os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or "").strip()
SCHEMA_PATH = ROOT / "sql" / "001_schema.sql"


def main() -> int:
    if not DATABASE_URL:
        print(
            "Missing DATABASE_URL in backend/.env\n"
            "Add:\n"
            "DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.YOUR_REF.supabase.co:5432/postgres\n"
            "or the pooler URI from Supabase → Project Settings → Database."
        )
        return 1

    if not SCHEMA_PATH.exists():
        print(f"Schema file not found: {SCHEMA_PATH}")
        return 1

    try:
        import psycopg
    except ImportError:
        print("Install psycopg first: uv add 'psycopg[binary]'")
        return 1

    sql = SCHEMA_PATH.read_text()
    print(f"Applying {SCHEMA_PATH.name} …")
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            # quick verify
            cur.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                  and table_name in (
                    'habits', 'habit_entries', 'manifestations',
                    'daily_quotes', 'ai_manifestation_cache'
                  )
                order by table_name
                """
            )
            tables = [row[0] for row in cur.fetchall()]

    print("Done. Tables present:", ", ".join(tables) if tables else "(none)")
    if len(tables) < 5:
        print("Warning: expected 5 tables; check SQL output / permissions.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
