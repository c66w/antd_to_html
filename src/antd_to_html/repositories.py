"""Database access helpers for templates, instances, and submissions."""

from __future__ import annotations

import json
from typing import Any, Optional

from psycopg.errors import UniqueViolation

from . import db
from .ids import generate_short_id
from .models import InstanceCreate, SubmissionCreate, TemplateCreate


class RepositoryError(Exception):
  """Base class for repository-level errors."""


class TemplateConflictError(RepositoryError):
  """Raised when a template slug already exists."""


def create_template(data: TemplateCreate) -> dict[str, Any]:
  template_id = data.id or generate_short_id()
  slug = data.slug or template_id
  try:
    row = db.execute(
      """
      INSERT INTO form_templates (id, slug, title, description, theme, definition, html_options, version)
      VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
      RETURNING *
      """,
      (
        template_id,
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
    if constraint.endswith("slug_key"):
      message = "Template slug already exists."
    elif constraint.endswith("pkey"):
      message = "Template id already exists."
    else:
      message = "Template already exists."
    raise TemplateConflictError(message) from exc

  if not row:
    raise RepositoryError("Failed to insert template.")
  return row


def get_template_by_id(template_id: str) -> Optional[dict[str, Any]]:
  return db.fetch_one("SELECT * FROM form_templates WHERE id = %s", (template_id,))


def get_template_by_slug(slug: str) -> Optional[dict[str, Any]]:
  return db.fetch_one("SELECT * FROM form_templates WHERE slug = %s", (slug,))


def delete_template_by_id(template_id: str) -> None:
  db.execute("DELETE FROM form_templates WHERE id = %s", (template_id,))


def create_instance(data: InstanceCreate, template_id: str) -> dict[str, Any]:
  instance_id = data.id or generate_short_id()
  row = db.execute(
    """
    INSERT INTO form_instances (id, template_id, name, runtime_config)
    VALUES (%s, %s, %s, %s::jsonb)
    RETURNING *
    """,
    (
      instance_id,
      template_id,
      data.name,
      json.dumps(data.runtime_config),
    ),
  )
  if not row:
    raise RepositoryError("Failed to insert instance.")
  return row


def get_instance(instance_id: str) -> Optional[dict[str, Any]]:
  return db.fetch_one("SELECT * FROM form_instances WHERE id = %s", (instance_id,))


def get_instance_with_template(instance_id: str) -> Optional[dict[str, Any]]:
  row = db.fetch_one(
    """
    SELECT
      i.id AS instance_id,
      i.template_id,
      i.name AS instance_name,
      i.runtime_config,
      i.created_at AS instance_created_at,
      i.updated_at AS instance_updated_at,
      t.id AS template_id,
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
    JOIN form_templates t ON t.id = i.template_id
    WHERE i.id = %s
    """,
    (instance_id,),
  )
  if not row:
    return None
  return {
    "instance": {
      "id": row["instance_id"],
      "template_id": row["template_id"],
      "name": row["instance_name"],
      "runtime_config": row["runtime_config"],
      "created_at": row["instance_created_at"],
      "updated_at": row["instance_updated_at"],
    },
    "template": {
      "id": row["template_id"],
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


def save_submission(instance_id: str, data: SubmissionCreate) -> dict[str, Any]:
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
       WHERE id = %s AND instance_id = %s
       RETURNING *
      """,
      (
        payload_json,
        status,
        callback_info_json,
        callback_status,
        submission_id,
        instance_id,
      ),
    )
  else:
    row = db.execute(
      """
      INSERT INTO form_submissions (instance_id, payload, status, callback_info, callback_status)
      VALUES (%s, %s::jsonb, %s, %s::jsonb, %s)
      ON CONFLICT (instance_id)
      DO UPDATE SET
        payload = EXCLUDED.payload,
        status = EXCLUDED.status,
        callback_info = EXCLUDED.callback_info,
        callback_status = EXCLUDED.callback_status,
        updated_at = NOW()
      RETURNING *
      """,
      (
        instance_id,
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
  instance_id: str,
  submission_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
  if submission_id:
    return db.fetch_one(
      "SELECT * FROM form_submissions WHERE id = %s AND instance_id = %s",
      (submission_id, instance_id),
    )

  return db.fetch_one(
    """
    SELECT * FROM form_submissions
    WHERE instance_id = %s
    ORDER BY updated_at DESC
    LIMIT 1
    """,
    (instance_id,),
  )
