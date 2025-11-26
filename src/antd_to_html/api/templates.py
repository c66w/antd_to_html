"""Endpoints for managing form templates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import logging
from fastapi import APIRouter, HTTPException, Response

from ..models import Template, TemplateCreate
from ..render import convert_antd_form_to_html
from ..repositories import (
  RepositoryError,
  TemplateConflictError,
  create_template,
  delete_template_by_id,
  get_template_by_id,
  get_template_by_slug,
)
from ..schema_validator import validate_form_definition

router = APIRouter(prefix="/form-templates", tags=["form-templates"])
logger = logging.getLogger(__name__)

PREVIEW_NOTICE = "预览模式：按钮已禁用，不会提交数据。"
PREVIEW_STYLES = """
<style>
.preview-banner {
  margin: 16px auto 24px;
  max-width: 920px;
  padding: 16px 20px;
  border-radius: 14px;
  background: rgba(22, 119, 255, 0.08);
  border: 1px solid rgba(22, 119, 255, 0.3);
  color: #0958d9;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.preview-banner strong {
  font-weight: 600;
}
.preview-banner span {
  color: #1f1f1f;
}
</style>
""".strip()
PREVIEW_BANNER_HTML = (
  '  <div class="preview-banner"><strong>预览模式</strong><span>按钮已禁用，不会提交数据。</span></div>'
)


@router.post("", response_model=Template)
async def create_form_template(payload: TemplateCreate) -> Template:
  logger.info(
    "Create template request: slug=%s title=%s version=%s def_keys=%s html_opt_keys=%s",
    payload.slug,
    payload.title,
    payload.version,
    list((payload.definition or {}).keys()),
    list((payload.html_options or {}).keys()),
  )
  errors = validate_form_definition(payload.definition)
  if errors:
    raise HTTPException(status_code=422, detail=errors)

  try:
    row = await create_template(payload)
  except TemplateConflictError as exc:
    raise HTTPException(status_code=409, detail=str(exc)) from exc
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  tmpl = Template.model_validate(row)
  logger.info("Template created: slug=%s title=%s version=%s", tmpl.slug, tmpl.title, tmpl.version)
  return tmpl


@router.get("/{identifier}", response_model=Template)
async def read_form_template(identifier: str) -> Template:
  logger.info("Read template request: identifier=%s", identifier)
  template = await _get_template_by_identifier(identifier)
  tmpl = Template.model_validate(template)
  logger.info("Returning template: slug=%s version=%s", tmpl.slug, tmpl.version)
  return tmpl


@router.delete("/{identifier}", status_code=204, response_class=Response)
async def delete_form_template(identifier: str) -> None:
  logger.info("Delete template request: identifier=%s", identifier)
  template = await _get_template_by_identifier(identifier)
  await delete_template_by_id(str(template["slug"]))
  logger.info("Template deleted: slug=%s", template["slug"]) 


@router.get("/{identifier}/preview", response_class=Response)
async def preview_form_template(identifier: str) -> Response:
  logger.info("Preview template request: identifier=%s", identifier)
  template = await _get_template_by_identifier(identifier)
  definition = deepcopy(template.get("definition") or {})
  html_options = deepcopy(template.get("html_options") or {})

  preview_definition = _build_preview_definition(definition)

  current_title = (
    html_options.get("title")
    or preview_definition.get("title")
    or (preview_definition.get("form") or {}).get("title")
  )
  if current_title:
    html_options["title"] = f"{current_title} · 预览"
  else:
    html_options["title"] = "表单模板 · 预览"

  slug = template.get("slug")
  if slug and not isinstance(html_options.get("contextBanner"), Mapping):
    html_options["contextBanner"] = {
      "label": "模板slug标识",
      "value": slug,
    }

  html = convert_antd_form_to_html(preview_definition, options={"html": html_options})
  html = _inject_preview_chrome(html)
  logger.info("Preview generated: slug=%s html_len=%s", template.get("slug"), len(html))
  return Response(content=html, media_type="text/html; charset=utf-8")


async def _get_template_by_identifier(identifier: str) -> Mapping[str, Any]:
  template = await get_template_by_id(identifier) or await get_template_by_slug(identifier)
  if not template:
    raise HTTPException(status_code=404, detail="Template not found.")
  return template


def _build_preview_definition(definition: Mapping[str, Any]) -> Mapping[str, Any]:
  preview = deepcopy(definition)
  preview.pop("submit", None)
  preview.pop("actions", None)

  subtitle = preview.get("subtitle")
  if subtitle:
    preview["subtitle"] = f"{subtitle}（预览）"

  form_section = preview.get("form")
  if isinstance(form_section, dict):
    if form_section.get("subtitle"):
      form_section["subtitle"] = f"{form_section['subtitle']}（预览）"
    elif not preview.get("subtitle"):
      form_section["subtitle"] = PREVIEW_NOTICE
  elif not preview.get("subtitle"):
    preview["subtitle"] = PREVIEW_NOTICE

  return preview


def _inject_preview_chrome(html: str) -> str:
  updated = html
  if "</head>" in updated:
    updated = updated.replace("</head>", f"{PREVIEW_STYLES}\n</head>", 1)
  if '<div class="form-container">' in updated:
    updated = updated.replace('<div class="form-container">', f"{PREVIEW_BANNER_HTML}\n  <div class=\"form-container\">", 1)
  return updated
