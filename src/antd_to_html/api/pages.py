"""Endpoints for storing and serving raw HTML pages."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Response

from ..models import PageCreate, PageResponse
from ..repositories import PageConflictError, RepositoryError, create_html_page, get_html_page

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


@router.post("", response_model=PageResponse, status_code=201)
async def create_page(payload: PageCreate) -> PageResponse:
  html_len = len(payload.html or "") if hasattr(payload, "html") else 0
  logger.info(
    "Create page request: slug=%s html_len=%s",
    payload.slug,
    html_len,
  )
  try:
    page = await create_html_page(payload)
  except PageConflictError as exc:
    logger.warning("HTML page slug conflict: %s", payload.slug)
    raise HTTPException(status_code=409, detail=str(exc)) from exc
  except RepositoryError as exc:
    logger.exception("Failed to create HTML page: %s", exc)
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  logger.info(
    "HTML page created: slug=%s stored_html_len=%s",
    page.get("slug"),
    len((page.get("html") or "")),
  )
  return PageResponse(page_slug=page["slug"])


@router.get("/{slug}", response_class=Response, name="render_html_page")
async def read_page(slug: str) -> Response:
  logger.info("Read page request: slug=%s", slug)
  page = await get_html_page(slug)
  if not page:
    logger.warning("HTML page not found: %s", slug)
    raise HTTPException(status_code=404, detail="Page not found.")

  logger.info("Serving HTML page: slug=%s html_len=%s", slug, len(page.get("html") or ""))
  return Response(content=page["html"], media_type="text/html; charset=utf-8")
