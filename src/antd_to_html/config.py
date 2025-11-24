"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
  pg_host: str = "localhost"
  pg_port: int = 5432
  pg_database: str = "form"
  pg_user: str = "postgres"
  pg_password: str = ""
  es_endpoint: str = "http://localhost:9200"
  es_username: str = ""
  es_password: str = ""
  es_index: str = "html_pages"
  api_base_url: str = ""  # API 基础 URL，用于生成完整的 submissionEndpoint

  @property
  def pg_dsn(self) -> str:
    user = quote_plus(self.pg_user)
    password = quote_plus(self.pg_password)
    return (
      f"postgresql://{user}:{password}"
      f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings(
    pg_host=os.getenv("PG_HOST", Settings.pg_host),
    pg_port=int(os.getenv("PG_PORT", Settings.pg_port)),
    pg_database=os.getenv("PG_DATABASE", Settings.pg_database),
    pg_user=os.getenv("PG_USER", Settings.pg_user),
    pg_password=os.getenv("PG_PASSWORD", Settings.pg_password),
    es_endpoint=os.getenv("ES_ENDPOINT", Settings.es_endpoint),
    es_username=os.getenv("ES_USERNAME", Settings.es_username),
    es_password=os.getenv("ES_PASSWORD", Settings.es_password),
    es_index=os.getenv("ES_INDEX", Settings.es_index),
    api_base_url=os.getenv("API_BASE_URL", Settings.api_base_url),
  )
