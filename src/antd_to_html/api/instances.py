"""Endpoints for managing form instances."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models import Instance, InstanceCreate, InstanceDetail, Template
from ..repositories import (
  RepositoryError,
  create_instance,
  get_instance_with_template,
  get_template_by_id,
  get_template_by_slug,
)

router = APIRouter(prefix="/form-instances", tags=["form-instances"])
logger = logging.getLogger(__name__)


@router.post("", response_model=Instance)
def create_form_instance(payload: InstanceCreate) -> Instance:
  template_row = None
  if payload.template_id:
    template_row = get_template_by_id(payload.template_id)
    if not template_row and payload.template_slug:
      template_row = get_template_by_slug(payload.template_slug)
  elif payload.template_slug:
    template_row = get_template_by_slug(payload.template_slug)

  if not template_row:
    logger.warning(
      "Template not found when creating instance (template_id=%s, template_slug=%s).",
      payload.template_id,
      payload.template_slug,
    )
    raise HTTPException(status_code=404, detail="Template not found.")

  try:
    row = create_instance(payload, str(template_row["id"]))
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  return Instance.model_validate(row)


@router.get("/{instance_id}", response_model=InstanceDetail)
def read_form_instance(instance_id: str) -> InstanceDetail:
  record = get_instance_with_template(instance_id)
  if not record:
    raise HTTPException(status_code=404, detail="Instance not found.")

  instance = Instance.model_validate(record["instance"])
  template = Template.model_validate(record["template"])
  return InstanceDetail(instance=instance, template=template)
