"""Endpoints for storing and serving raw HTML pages."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..models import PageCreate, PageResponse
from ..repositories import RepositoryError, create_html_page, get_html_page

router = APIRouter(prefix="/pages", tags=["pages"])


@router.post("", response_model=PageResponse, status_code=201)
def create_page(payload: PageCreate) -> PageResponse:
  try:
    page = create_html_page(payload)
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  return PageResponse(page_slug=page["slug"])


@router.get("/{slug}", response_class=Response, name="render_html_page")
def read_page(slug: str) -> Response:
  page = get_html_page(slug)
  if not page:
    raise HTTPException(status_code=404, detail="Page not found.")

  return Response(content=page["html"], media_type="text/html; charset=utf-8")
