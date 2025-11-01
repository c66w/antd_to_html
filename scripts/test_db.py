"""Simple script to verify PostgreSQL connectivity."""

from __future__ import annotations

from antd_to_html.config import get_settings
from antd_to_html.db import get_connection


def main() -> None:
  settings = get_settings()
  print(f"Connecting to {settings.pg_dsn}")
  with get_connection() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT 1")
      result = cur.fetchone()
  print(f"Connection OK, result: {result}")


if __name__ == "__main__":
  main()
