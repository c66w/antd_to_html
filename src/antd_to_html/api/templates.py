"""Endpoints for managing form templates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

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
def create_form_template(payload: TemplateCreate) -> Template:
  errors = validate_form_definition(payload.definition)
  if errors:
    raise HTTPException(status_code=422, detail=errors)

  try:
    row = create_template(payload)
  except TemplateConflictError as exc:
    raise HTTPException(status_code=409, detail=str(exc)) from exc
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  return Template.model_validate(row)


@router.get("/{identifier}", response_model=Template)
def read_form_template(identifier: str) -> Template:
  template = _get_template_by_identifier(identifier)
  return Template.model_validate(template)


@router.delete("/{identifier}", status_code=204)
def delete_form_template(identifier: str) -> None:
  template = _get_template_by_identifier(identifier)
  delete_template_by_id(str(template["id"]))


@router.get("/{identifier}/preview", response_class=Response)
def preview_form_template(identifier: str) -> Response:
  template = _get_template_by_identifier(identifier)
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

  html = convert_antd_form_to_html(preview_definition, options={"html": html_options})
  html = _inject_preview_chrome(html)
  return Response(content=html, media_type="text/html; charset=utf-8")


def _get_template_by_identifier(identifier: str) -> Mapping[str, Any]:
  template = get_template_by_id(identifier) or get_template_by_slug(identifier)
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
