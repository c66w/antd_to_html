"""Elasticsearch client helpers."""

from __future__ import annotations

from typing import Optional

from elasticsearch import AsyncElasticsearch

from .config import get_settings

_async_client: Optional[AsyncElasticsearch] = None


def get_async_client() -> AsyncElasticsearch:
  global _async_client
  if _async_client is not None:
    return _async_client

  settings = get_settings()
  kwargs = {}
  if settings.es_username:
    kwargs["basic_auth"] = (settings.es_username, settings.es_password)

  _async_client = AsyncElasticsearch(settings.es_endpoint, **kwargs)
  return _async_client
