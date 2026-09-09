"""
scripts/test_db_connection.py
------------------------------
Standalone sanity check for your DATABASE_URL — run this before wiring
up the full FastAPI app to confirm AWS RDS (or local Postgres) is
reachable, authenticated correctly, and that the calculation_logs
table can be created.

Usage (from the backend/ directory):
    python scripts/test_db_connection.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from database import engine, DATABASE_URL, init_db


def main() -> None:
    # Never print the password — show a redacted version of the URL.
    safe_url = DATABASE_URL
    if "@" in safe_url and "://" in safe_url:
        scheme, rest = safe_url.split("://", 1)
        creds, host_part = rest.split("@", 1)
        user = creds.split(":", 1)[0]
        safe_url = f"{scheme}://{user}:****@{host_part}"

    print(f"Connecting to: {safe_url}")

    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print("Connected successfully.")
            print(f"Server version: {version}")
    except Exception as exc:
        print("Connection FAILED.")
        print(f"Error: {exc}")
        sys.exit(1)

    try:
        init_db()
        print("calculation_logs table verified/created.")
    except Exception as exc:
        print("Connected, but failed to create/verify tables.")
        print(f"Error: {exc}")
        sys.exit(1)

    print("\nAll checks passed — your DATABASE_URL is ready to use.")


if __name__ == "__main__":
    main()
