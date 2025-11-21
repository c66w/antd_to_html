"""Application factory for the FastAPI service."""

from __future__ import annotations

from fastapi import FastAPI
import logging
import time

from .api import html_pages, instances, pages, runtime, templates


def _configure_logging() -> None:
  """Route standard logging to Uvicorn handlers so our logs show up."""
  try:
    uvicorn_logger = logging.getLogger("uvicorn.error")
    if not uvicorn_logger.handlers:
      return
    root = logging.getLogger()
    # Attach uvicorn handlers to root so app loggers propagate to console
    root.handlers = uvicorn_logger.handlers
    root.setLevel(logging.INFO)
    # Also make sure our ad-hoc 'http' logger is visible
    http_logger = logging.getLogger("http")
    http_logger.setLevel(logging.INFO)
    http_logger.propagate = True
  except Exception:
    # Never fail app creation due to logging setup
    pass


def create_app() -> FastAPI:
  app = FastAPI(title="antd-to-html service", version="0.1.0")
  _configure_logging()
  app.include_router(pages.router)
  app.include_router(templates.router)
  app.include_router(instances.router)
  app.include_router(runtime.router)
  app.include_router(html_pages.router)

  # HTTP request/response logging middleware (covers all interfaces)
  http_logger = logging.getLogger("http")

  @app.middleware("http")
  async def log_requests(request, call_next):  # type: ignore[no-redef]
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    query = request.url.query
    content_type = request.headers.get("content-type") or "-"
    content_length = request.headers.get("content-length") or "-"
    http_logger.info(
      "HTTP request: %s %s%s ct=%s len=%s",
      method,
      path,
      ("?" + query) if query else "",
      content_type,
      content_length,
    )
    try:
      response = await call_next(request)
    except Exception:
      duration_ms = (time.perf_counter() - start) * 1000.0
      http_logger.exception("HTTP error: %s %s took=%.2fms", method, path, duration_ms)
      raise

    duration_ms = (time.perf_counter() - start) * 1000.0
    resp_len = response.headers.get("content-length") or "-"
    http_logger.info(
      "HTTP response: %s %s status=%s len=%s took=%.2fms",
      method,
      path,
      response.status_code,
      resp_len,
      duration_ms,
    )
    return response

  # Print all routes at startup
  route_logger = logging.getLogger(__name__)
  route_logger.info("FastAPI app created: routers registered [pages, templates, instances, runtime, html_pages]")
  for route in app.routes:
    methods = sorted([m for m in getattr(route, "methods", set()) or set() if m])
    path = getattr(route, "path", None) or getattr(route, "path_format", None) or str(route)
    if methods and path:
      route_logger.info("Route: %s %s", ",".join(methods), path)
  return app
