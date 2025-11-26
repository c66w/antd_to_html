"""One-off migration: move form data from PostgreSQL to Elasticsearch."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus

from elasticsearch import Elasticsearch, helpers
from psycopg import connect, rows

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


TEMPLATE_MAPPING = {
  "slug": {"type": "keyword"},
  "title": {"type": "text"},
  "description": {"type": "text"},
  "theme": {"type": "keyword"},
  "definition": {"type": "object", "enabled": True},
  "html_options": {"type": "object", "enabled": True},
  "version": {"type": "integer"},
  "created_at": {"type": "date"},
  "updated_at": {"type": "date"},
}

INSTANCE_MAPPING = {
  "slug": {"type": "keyword"},
  "template_slug": {"type": "keyword"},
  "name": {"type": "text"},
  "runtime_config": {"type": "object", "enabled": True},
  "created_at": {"type": "date"},
  "updated_at": {"type": "date"},
}

SUBMISSION_MAPPING = {
  "id": {"type": "keyword"},
  "instance_slug": {"type": "keyword"},
  # Payload can be arbitrary nested JSON; disable indexing to avoid mapping conflicts.
  "payload": {"type": "object", "enabled": False},
  "status": {"type": "keyword"},
  "callback_status": {"type": "keyword"},
  "callback_info": {"type": "object", "enabled": False},
  "submitted_at": {"type": "date"},
  "updated_at": {"type": "date"},
}


@dataclass
class Settings:
  pg_host: str
  pg_port: int
  pg_database: str
  pg_user: str
  pg_password: str
  es_endpoint: str
  es_username: str
  es_password: str
  es_template_index: str
  es_instance_index: str
  es_submission_index: str

  @property
  def pg_dsn(self) -> str:
    user = quote_plus(self.pg_user)
    password = quote_plus(self.pg_password)
    return f"postgresql://{user}:{password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"


def main() -> None:
  settings = load_settings()
  client = make_client(settings)
  logger.info("Starting migration: pg=%s es=%s", settings.pg_dsn, settings.es_endpoint)

  ensure_index(client, settings.es_template_index, TEMPLATE_MAPPING)
  ensure_index(client, settings.es_instance_index, INSTANCE_MAPPING)
  ensure_index(client, settings.es_submission_index, SUBMISSION_MAPPING)

  with connect(settings.pg_dsn) as conn:
    with conn.cursor(row_factory=rows.dict_row) as cur:
      templates = fetch_all(cur, "SELECT * FROM form_templates")
      instances = fetch_all(cur, "SELECT * FROM form_instances")
      submissions = fetch_all(cur, "SELECT * FROM form_submissions")

  logger.info("Fetched rows: templates=%s instances=%s submissions=%s", len(templates), len(instances), len(submissions))
  bulk_templates(client, settings.es_template_index, templates)
  bulk_instances(client, settings.es_instance_index, instances)
  bulk_submissions(client, settings.es_submission_index, submissions)
  logger.info("Migration completed.")


def ensure_index(client: Elasticsearch, index: str, properties: dict) -> None:
  drop_existing = os.getenv("ES_RESET_INDICES") == "1"
  if client.indices.exists(index=index):
    if drop_existing:
      logger.warning("Index exists and will be dropped: %s", index)
      client.indices.delete(index=index)
    else:
      logger.info("Index exists, skipping creation: %s", index)
      return
  logger.info("Creating index: %s", index)
  client.indices.create(
    index=index,
    settings={
      "number_of_shards": 3,
      "number_of_replicas": 2,
    },
    mappings={"properties": properties},
  )


def fetch_all(cur, sql: str):
  cur.execute(sql)
  return cur.fetchall()


def bulk_templates(client: Elasticsearch, index: str, rows: list[dict]) -> None:
  actions = []
  for row in rows:
    actions.append(
      {
        "_op_type": "index",
        "_index": index,
        "_id": row["slug"],
        "_source": {
          "slug": row["slug"],
          "title": row.get("title"),
          "description": row.get("description"),
          "theme": row.get("theme"),
          "definition": row.get("definition"),
          "html_options": row.get("html_options"),
          "version": row.get("version"),
          "created_at": _as_iso(row.get("created_at")),
          "updated_at": _as_iso(row.get("updated_at")),
        },
      }
    )
  _do_bulk(client, actions, "templates")


def bulk_instances(client: Elasticsearch, index: str, rows: list[dict]) -> None:
  actions = []
  for row in rows:
    actions.append(
      {
        "_op_type": "index",
        "_index": index,
        "_id": row["slug"],
        "_source": {
          "slug": row["slug"],
          "template_slug": row.get("template_slug"),
          "name": row.get("name"),
          "runtime_config": row.get("runtime_config"),
          "created_at": _as_iso(row.get("created_at")),
          "updated_at": _as_iso(row.get("updated_at")),
        },
      }
    )
  _do_bulk(client, actions, "instances")


def bulk_submissions(client: Elasticsearch, index: str, rows: list[dict]) -> None:
  actions = []
  for row in rows:
    payload = normalize_form_info(row.get("payload"))
    actions.append(
      {
        "_op_type": "index",
        "_index": index,
        "_id": row["id"],
        "_source": {
          "id": row["id"],
          "instance_slug": row.get("instance_slug"),
          "payload": payload,
          "status": row.get("status"),
          "callback_status": row.get("callback_status"),
          "callback_info": row.get("callback_info"),
          "submitted_at": _as_iso(row.get("submitted_at")),
          "updated_at": _as_iso(row.get("updated_at")),
        },
      }
    )
  _do_bulk(client, actions, "submissions")


def _do_bulk(client: Elasticsearch, actions: list[dict], label: str) -> None:
  if not actions:
    logger.info("No %s to migrate.", label)
    return
  logger.info("Migrating %s %s...", len(actions), label)
  try:
    helpers.bulk(client, actions, refresh=True)
  except helpers.BulkIndexError as exc:
    errors = exc.errors if hasattr(exc, "errors") else []
    sample = errors[:5]
    logger.error("Bulk failed: %s errors. Sample: %s", len(errors), sample)
    raise
  logger.info("Finished migrating %s %s.", len(actions), label)


def _as_iso(value) -> str | None:
  if value is None:
    return None
  if isinstance(value, datetime):
    return value.isoformat()
  return str(value)


def normalize_form_info(payload: dict | None) -> dict | None:
  """Ensure form_info[].value is always an object to avoid mapping conflicts."""
  if not payload:
    return payload
  form_info = payload.get("form_info")
  if not isinstance(form_info, list):
    return payload

  updated = False
  for item in form_info:
    if not isinstance(item, dict) or "value" not in item:
      continue
    value = item["value"]
    if isinstance(value, dict):
      continue
    updated = True
    item["value"] = {"label": str(value), "value": value}
  if updated:
    payload["form_info"] = form_info
  return payload


def make_client(settings: Settings):
  kwargs = {
    "headers": {
      # Force plain JSON to avoid versioned media-type compatibility headers mismatching cluster version.
      "Accept": "application/json",
      "Content-Type": "application/json",
    }
  }
  if settings.es_username:
    kwargs["basic_auth"] = (settings.es_username, settings.es_password)
  return Elasticsearch(settings.es_endpoint, **kwargs)


def load_settings() -> Settings:
  return Settings(
    pg_host=os.getenv("PG_HOST", "localhost"),
    pg_port=int(os.getenv("PG_PORT", 5432)),
    pg_database=os.getenv("PG_DATABASE", "form"),
    pg_user=os.getenv("PG_USER", "postgres"),
    pg_password=os.getenv("PG_PASSWORD", ""),
    es_endpoint=os.getenv("ES_ENDPOINT", "http://localhost:9200"),
    es_username=os.getenv("ES_USERNAME", ""),
    es_password=os.getenv("ES_PASSWORD", ""),
    es_template_index=os.getenv("ES_TEMPLATE_INDEX", "form_templates"),
    es_instance_index=os.getenv("ES_INSTANCE_INDEX", "form_instances"),
    es_submission_index=os.getenv("ES_SUBMISSION_INDEX", "form_submissions"),
  )


if __name__ == "__main__":
  main()
