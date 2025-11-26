"""Elasticsearch access helpers for templates, instances, and submissions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from elasticsearch import ConflictError, NotFoundError, TransportError

from . import es
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


async def create_template(data: TemplateCreate) -> dict[str, Any]:
  slug = data.slug or generate_short_id()
  settings = get_settings()
  client = es.get_async_client()
  now = _now_iso()
  logger.info(
    "Repo.create_template: slug=%s title=%s version=%s",
    slug,
    data.title,
    data.version,
  )
  document = {
    "slug": slug,
    "title": data.title,
    "description": data.description,
    "theme": data.theme,
    "definition": data.definition,
    "html_options": data.html_options,
    "version": data.version,
    "created_at": now,
    "updated_at": now,
  }
  try:
    await client.create(index=settings.es_template_index, id=slug, document=document)
  except ConflictError as exc:
    raise TemplateConflictError("Template slug already exists.") from exc
  except TransportError as exc:
    logger.exception("Elasticsearch create failed for template slug=%s", slug)
    raise RepositoryError(f"Failed to insert template: {exc}") from exc

  logger.info("Repo.create_template: created slug=%s", slug)
  return document


async def get_template_by_id(template_id: str) -> Optional[dict[str, Any]]:
  return await get_template_by_slug(template_id)


async def get_template_by_slug(slug: str) -> Optional[dict[str, Any]]:
  client = es.get_async_client()
  settings = get_settings()
  logger.debug("Repo.get_template_by_slug: %s", slug)
  try:
    res = await client.get(index=settings.es_template_index, id=slug)
  except NotFoundError:
    return None
  except TransportError as exc:
    logger.exception("Elasticsearch get failed for template slug=%s", slug)
    raise RepositoryError(f"Failed to load template: {exc}") from exc

  src = res.get("_source") or {}
  if not src:
    return None
  src["slug"] = slug
  return src


async def delete_template_by_id(template_id: str) -> None:
  client = es.get_async_client()
  settings = get_settings()
  logger.info("Repo.delete_template_by_id: %s", template_id)
  try:
    await client.delete(index=settings.es_template_index, id=template_id)
  except NotFoundError:
    return
  except TransportError as exc:
    logger.exception("Elasticsearch delete failed for template slug=%s", template_id)
    raise RepositoryError(f"Failed to delete template: {exc}") from exc


async def create_html_page(data: PageCreate) -> dict[str, Any]:
  slug = data.slug or generate_short_id()
  client = es.get_async_client()
  settings = get_settings()
  now = datetime.now(timezone.utc).isoformat()
  logger.info("Repo.create_html_page: slug=%s index=%s html_len=%s", slug, settings.es_index, len(data.html or ""))
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
  logger.info("Repo.get_html_page: slug=%s index=%s", slug, settings.es_index)
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
  logger.info("Repo.get_html_page: found slug=%s html_len=%s", slug, len(source.get("html") or ""))
  return {
    "slug": slug,
    "html": source.get("html", ""),
    "created_at": source.get("created_at"),
    "updated_at": source.get("updated_at"),
  }


async def create_instance(data: InstanceCreate, template_id: str) -> dict[str, Any]:
  # Use provided slug or generate a new one
  instance_slug = data.slug or generate_short_id()
  # Prefer the explicitly passed template identifier (slug),
  # fall back to the value in the payload for safety.
  template_slug = template_id or (data.template_slug or "")
  client = es.get_async_client()
  settings = get_settings()
  now = _now_iso()
  logger.info(
    "Repo.create_instance: instance_slug=%s template_slug=%s name=%s",
    instance_slug,
    template_slug,
    data.name,
  )

  document = {
    "slug": instance_slug,
    "template_slug": template_slug,
    "name": data.name,
    "runtime_config": data.runtime_config,
    "created_at": now,
    "updated_at": now,
  }
  try:
    await client.create(index=settings.es_instance_index, id=instance_slug, document=document)
  except ConflictError as exc:
    raise RepositoryError("Instance slug already exists.") from exc
  except TransportError as exc:
    logger.exception("Elasticsearch create failed for instance_slug=%s", instance_slug)
    raise RepositoryError(f"Failed to insert instance: {exc}") from exc

  logger.info("Repo.create_instance: created slug=%s", instance_slug)
  return document


async def get_instance(instance_id: str) -> Optional[dict[str, Any]]:
  # For backward compatibility, treat instance_id as slug
  client = es.get_async_client()
  settings = get_settings()
  logger.debug("Repo.get_instance: %s", instance_id)
  try:
    res = await client.get(index=settings.es_instance_index, id=instance_id)
  except NotFoundError:
    return None
  except TransportError as exc:
    logger.exception("Elasticsearch get failed for instance_slug=%s", instance_id)
    raise RepositoryError(f"Failed to load instance: {exc}") from exc

  src = res.get("_source") or {}
  if not src:
    return None
  src["slug"] = instance_id
  return src


async def get_instance_with_template(instance_id: str) -> Optional[dict[str, Any]]:
  client = es.get_async_client()
  settings = get_settings()
  logger.debug("Repo.get_instance_with_template: %s", instance_id)
  instance = await get_instance(instance_id)
  if not instance:
    return None

  try:
    template_res = await client.get(index=settings.es_template_index, id=instance["template_slug"])
  except NotFoundError:
    logger.warning("Template missing for instance_slug=%s template_slug=%s", instance_id, instance.get("template_slug"))
    return None
  except TransportError as exc:
    logger.exception("Elasticsearch get failed for template_slug=%s", instance.get("template_slug"))
    raise RepositoryError(f"Failed to load template: {exc}") from exc

  template_src = template_res.get("_source") or {}
  if not template_src:
    return None
  template_src["slug"] = template_res.get("_id") or instance.get("template_slug")

  logger.debug("Repo.get_instance_with_template: found instance_slug=%s template_slug=%s", instance.get("slug"), instance.get("template_slug"))
  return {
    "instance": {
      "slug": instance["slug"],
      "template_slug": instance["template_slug"],
      "name": instance.get("name"),
      "runtime_config": instance.get("runtime_config") or {},
      "created_at": instance.get("created_at"),
      "updated_at": instance.get("updated_at"),
    },
    "template": {
      "slug": template_src["slug"],
      "title": template_src.get("title"),
      "description": template_src.get("description"),
      "theme": template_src.get("theme"),
      "definition": template_src.get("definition"),
      "html_options": template_src.get("html_options"),
      "version": template_src.get("version"),
      "created_at": template_src.get("created_at"),
      "updated_at": template_src.get("updated_at"),
    },
  }


async def save_submission(instance_slug: str, data: SubmissionCreate) -> dict[str, Any]:
  status = data.status or "draft"
  callback_status = data.callback_status or "idle"
  submission_id = data.submission_id or generate_short_id(12)
  client = es.get_async_client()
  settings = get_settings()
  now = _now_iso()
  logger.info(
    "Repo.save_submission: instance_slug=%s submission_id=%s status=%s callback_status=%s payload_len=%s",
    instance_slug,
    submission_id,
    status,
    callback_status,
    len(data.payload or {}),
  )

  existing = await _find_submission_by_instance(client, settings, instance_slug)
  submission_id = submission_id or (existing.get("_id") if existing else None) or generate_short_id(12)
  submitted_at = (existing["_source"].get("submitted_at") if existing else None) or now

  document = {
    "id": submission_id,
    "instance_slug": instance_slug,
    "payload": _normalize_submission_payload(data.payload),
    "status": status,
    "callback_info": data.callback_info,
    "callback_status": callback_status,
    "submitted_at": submitted_at,
    "updated_at": now,
  }

  try:
    await client.index(index=settings.es_submission_index, id=submission_id, document=document)
  except TransportError as exc:
    logger.exception("Elasticsearch index failed for submission_id=%s instance_slug=%s", submission_id, instance_slug)
    raise RepositoryError(f"Failed to save submission: {exc}") from exc

  logger.info("Repo.save_submission: saved id=%s instance_slug=%s", submission_id, instance_slug)
  return document


async def get_submission(
  instance_slug: str,
  submission_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
  if submission_id:
    logger.info("Repo.get_submission: instance_slug=%s submission_id=%s", instance_slug, submission_id)
    client = es.get_async_client()
    settings = get_settings()
    try:
      res = await client.get(index=settings.es_submission_index, id=submission_id)
    except NotFoundError:
      return None
    except TransportError as exc:
      logger.exception("Elasticsearch get failed for submission_id=%s", submission_id)
      raise RepositoryError(f"Failed to load submission: {exc}") from exc

    src = res.get("_source") or {}
    if not src or src.get("instance_slug") != instance_slug:
      return None
    src["id"] = submission_id
    return src

  logger.info("Repo.get_submission latest: instance_slug=%s", instance_slug)
  existing = await _find_submission_by_instance(es.get_async_client(), get_settings(), instance_slug)
  if not existing:
    return None
  src = existing.get("_source") or {}
  src["id"] = existing.get("_id")
  return src


async def _find_submission_by_instance(client, settings, instance_slug: str) -> Optional[dict[str, Any]]:
  try:
    res = await client.search(
      index=settings.es_submission_index,
      query={"term": {"instance_slug": instance_slug}},
      sort=[{"updated_at": {"order": "desc"}}],
      size=1,
    )
  except NotFoundError:
    return None
  except TransportError as exc:
    logger.exception("Elasticsearch search failed for instance_slug=%s", instance_slug)
    raise RepositoryError(f"Failed to query submission: {exc}") from exc

  hits = (res.get("hits") or {}).get("hits") or []
  return hits[0] if hits else None


def _now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def _normalize_submission_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
  """Ensure form_info[].value uses a consistent object shape to avoid mapping conflicts."""
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
