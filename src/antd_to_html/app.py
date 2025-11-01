"""Application factory for the FastAPI service."""

from __future__ import annotations

from fastapi import FastAPI

from .api import instances, runtime, templates


def create_app() -> FastAPI:
  app = FastAPI(title="antd-to-html service", version="0.1.0")
  app.include_router(templates.router)
  app.include_router(instances.router)
  app.include_router(runtime.router)
  return app
