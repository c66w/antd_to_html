"""Database access helpers for templates, instances, and submissions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from elasticsearch import ConflictError, NotFoundError, TransportError
from psycopg.errors import UniqueViolation

from . import db, es
from .config import get_settings
from .ids import generate_short_id
from .models import InstanceCreate, PageCreate, SubmissionCreate, TemplateCreate

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
  """Base class for repository-level errors."""


class TemplateConflictError(RepositoryError):
  """Raised when a template slug already exists."""


class PageConflictError(RepositoryError):
  """Raised when a page slug already exists."""


def create_template(data: TemplateCreate) -> dict[str, Any]:
  slug = data.slug or generate_short_id()
  try:
    row = db.execute(
      """
      INSERT INTO form_templates (slug, title, description, theme, definition, html_options, version)
      VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
      RETURNING *
      """,
      (
        slug,
        data.title,
        data.description,
        data.theme,
        json.dumps(data.definition),
        json.dumps(data.html_options),
        data.version,
      ),
    )
  except UniqueViolation as exc:
    constraint = getattr(getattr(exc, "diag", None), "constraint_name", "") or ""
    if constraint.endswith("slug_key") or constraint.endswith("pkey"):
      message = "Template slug already exists."
    else:
      message = "Template already exists."
    raise TemplateConflictError(message) from exc

  if not row:
    raise RepositoryError("Failed to insert template.")
  return row


def get_template_by_id(template_id: str) -> Optional[dict[str, Any]]:
  # For backward compatibility, treat template_id as slug
  return db.fetch_one("SELECT * FROM form_templates WHERE slug = %s", (template_id,))


def get_template_by_slug(slug: str) -> Optional[dict[str, Any]]:
  return db.fetch_one("SELECT * FROM form_templates WHERE slug = %s", (slug,))


def delete_template_by_id(template_id: str) -> None:
  # For backward compatibility, treat template_id as slug
  db.execute("DELETE FROM form_templates WHERE slug = %s", (template_id,))


async def create_html_page(data: PageCreate) -> dict[str, Any]:
  slug = data.slug or generate_short_id()
  client = es.get_async_client()
  settings = get_settings()
  now = datetime.now(timezone.utc).isoformat()
  document = {
    "slug": slug,
    "html": data.html,
    "created_at": now,
    "updated_at": now,
  }
  try:
    await client.create(index=settings.es_index, id=slug, document=document)
  except ConflictError as exc:
    logger.warning("Attempted to create duplicate HTML page slug=%s", slug)
    raise PageConflictError("Page slug already exists.") from exc
  except TransportError as exc:
    logger.exception("Elasticsearch create failed for slug=%s", slug)
    raise RepositoryError(f"Failed to insert HTML page: {exc}") from exc

  logger.debug("Stored HTML page in Elasticsearch index=%s slug=%s", settings.es_index, slug)
  return document


async def get_html_page(slug: str) -> Optional[dict[str, Any]]:
  client = es.get_async_client()
  settings = get_settings()
  try:
    response = await client.get(index=settings.es_index, id=slug)
  except NotFoundError:
    logger.info("Elasticsearch page not found slug=%s", slug)
    return None
  except TransportError as exc:
    logger.exception("Elasticsearch get failed for slug=%s", slug)
    raise RepositoryError(f"Failed to load HTML page: {exc}") from exc

  source = response.get("_source") or {}
  if not source:
    return None
  return {
    "slug": slug,
    "html": source.get("html", ""),
    "created_at": source.get("created_at"),
    "updated_at": source.get("updated_at"),
  }


def create_instance(data: InstanceCreate, template_id: str) -> dict[str, Any]:
  instance_id = data.id or generate_short_id()
  row = db.execute(
    """
    INSERT INTO form_instances (slug, template_slug, name, runtime_config)
    VALUES (%s, %s, %s, %s::jsonb)
    RETURNING *
    """,
    (
      instance_slug,
      template_slug,
      data.name,
      json.dumps(data.runtime_config),
    ),
  )
  if not row:
    raise RepositoryError("Failed to insert instance.")
  return row


def get_instance(instance_id: str) -> Optional[dict[str, Any]]:
  # For backward compatibility, treat instance_id as slug
  return db.fetch_one("SELECT * FROM form_instances WHERE slug = %s", (instance_id,))


def get_instance_with_template(instance_id: str) -> Optional[dict[str, Any]]:
  # For backward compatibility, treat instance_id as slug
  row = db.fetch_one(
    """
    SELECT
      i.slug AS instance_slug,
      i.template_slug,
      i.name AS instance_name,
      i.runtime_config,
      i.created_at AS instance_created_at,
      i.updated_at AS instance_updated_at,
      t.slug AS template_slug,
      t.title AS template_title,
      t.description AS template_description,
      t.theme AS template_theme,
      t.definition AS template_definition,
      t.html_options AS template_html_options,
      t.version AS template_version,
      t.created_at AS template_created_at,
      t.updated_at AS template_updated_at
    FROM form_instances i
    JOIN form_templates t ON t.slug = i.template_slug
    WHERE i.slug = %s
    """,
    (instance_id,),
  )
  if not row:
    return None
  return {
    "instance": {
      "slug": row["instance_slug"],
      "template_slug": row["template_slug"],
      "name": row["instance_name"],
      "runtime_config": row["runtime_config"],
      "created_at": row["instance_created_at"],
      "updated_at": row["instance_updated_at"],
    },
    "template": {
      "slug": row["template_slug"],
      "title": row["template_title"],
      "description": row["template_description"],
      "theme": row["template_theme"],
      "definition": row["template_definition"],
      "html_options": row["template_html_options"],
      "version": row["template_version"],
      "created_at": row["template_created_at"],
      "updated_at": row["template_updated_at"],
    },
  }


def save_submission(instance_slug: str, data: SubmissionCreate) -> dict[str, Any]:
  status = data.status or "draft"
  callback_status = data.callback_status or "idle"
  payload_json = json.dumps(data.payload)
  callback_info_json = json.dumps(data.callback_info) if data.callback_info is not None else None
  submission_id = data.submission_id

  if submission_id:
    row = db.execute(
      """
      UPDATE form_submissions
         SET payload = %s::jsonb,
             status = %s,
             callback_info = %s::jsonb,
             callback_status = %s,
             updated_at = NOW()
       WHERE id = %s AND instance_slug = %s
       RETURNING *
      """,
      (
        payload_json,
        status,
        callback_info_json,
        callback_status,
        submission_id,
        instance_slug,
      ),
    )
  else:
    row = db.execute(
      """
      INSERT INTO form_submissions (instance_slug, payload, status, callback_info, callback_status)
      VALUES (%s, %s::jsonb, %s, %s::jsonb, %s)
      ON CONFLICT (instance_slug)
      DO UPDATE SET
        payload = EXCLUDED.payload,
        status = EXCLUDED.status,
        callback_info = EXCLUDED.callback_info,
        callback_status = EXCLUDED.callback_status,
        updated_at = NOW()
      RETURNING *
      """,
      (
        instance_slug,
        payload_json,
        status,
        callback_info_json,
        callback_status,
      ),
    )

  if not row:
    raise RepositoryError("Failed to save submission.")
  return row


def get_submission(
  instance_slug: str,
  submission_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
  if submission_id:
    return db.fetch_one(
      "SELECT * FROM form_submissions WHERE id = %s AND instance_slug = %s",
      (submission_id, instance_slug),
    )

  return db.fetch_one(
    """
    SELECT * FROM form_submissions
    WHERE instance_slug = %s
    ORDER BY updated_at DESC
    LIMIT 1
    """,
    (instance_slug,),
  )
