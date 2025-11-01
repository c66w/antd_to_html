"""PostgreSQL connection utilities."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Optional

from psycopg import rows
from psycopg_pool import ConnectionPool

from .config import get_settings

_pool: Optional[ConnectionPool] = None


def _ensure_pool() -> ConnectionPool:
  global _pool
  if _pool is None:
    settings = get_settings()
    _pool = ConnectionPool(
      conninfo=settings.pg_dsn,
      min_size=1,
      max_size=5,
      kwargs={"autocommit": True},
    )
  return _pool


@contextmanager
def get_connection():
  pool = _ensure_pool()
  with pool.connection() as conn:
    yield conn


def fetch_one(query: str, params: Iterable[Any] | None = None):
  with get_connection() as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      cur.execute(query, params or ())
      return cur.fetchone()


def fetch_all(query: str, params: Iterable[Any] | None = None):
  with get_connection() as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      cur.execute(query, params or ())
      return cur.fetchall()


def execute(query: str, params: Iterable[Any] | None = None):
  with get_connection() as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      cur.execute(query, params or ())
      if cur.description:
        return cur.fetchone()
      return None
