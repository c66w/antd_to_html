"""Elasticsearch client helpers."""

from __future__ import annotations

from typing import Optional
import logging

from elasticsearch import AsyncElasticsearch

from .config import get_settings

logger = logging.getLogger(__name__)

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
  logger.info("Elasticsearch async client created: endpoint=%s index=%s", settings.es_endpoint, settings.es_index)
  return _async_client
