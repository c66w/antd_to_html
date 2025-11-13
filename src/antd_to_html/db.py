"""PostgreSQL connection utilities."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from typing import Any, Iterable, Optional

from psycopg import rows
from psycopg_pool import ConnectionPool

from .config import get_settings

logger = logging.getLogger(__name__)

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
      logger.debug("DB.fetch_one: %s params=%s", _shorten_sql(query), _shorten_params(params))
      cur.execute(query, params or ())
      return cur.fetchone()


def fetch_all(query: str, params: Iterable[Any] | None = None):
  with get_connection() as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      logger.debug("DB.fetch_all: %s params=%s", _shorten_sql(query), _shorten_params(params))
      cur.execute(query, params or ())
      return cur.fetchall()


def execute(query: str, params: Iterable[Any] | None = None):
  with get_connection() as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      logger.debug("DB.execute: %s params=%s", _shorten_sql(query), _shorten_params(params))
      cur.execute(query, params or ())
      if cur.description:
        return cur.fetchone()
      return None


def _shorten_sql(sql: str, max_len: int = 200) -> str:
  s = " ".join((sql or "").split())
  return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _shorten_params(params: Iterable[Any] | None, max_items: int = 10) -> str:
  if params is None:
    return "()"
  try:
    lst = list(params)
  except TypeError:
    return str(params)
  display = []
  for i, v in enumerate(lst):
    if i >= max_items:
      display.append("…")
      break
    s = str(v)
    if len(s) > 120:
      s = s[:117] + "..."
    display.append(s)
  return f"({', '.join(display)})"
