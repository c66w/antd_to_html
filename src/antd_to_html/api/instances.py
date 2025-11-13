"""Endpoints for managing form instances."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models import Instance, InstanceCreate, InstanceDetail, Template
from ..repositories import (
  RepositoryError,
  create_instance,
  get_instance_with_template,
  get_template_by_slug,
)

router = APIRouter(prefix="/form-instances", tags=["form-instances"])
logger = logging.getLogger(__name__)


@router.post("", response_model=Instance)
def create_form_instance(payload: InstanceCreate) -> Instance:
  logger.info(
    "Create instance request: slug=%s template_slug=%s name=%s runtime_keys=%s",
    payload.slug,
    payload.template_slug,
    payload.name,
    list((payload.runtime_config or {}).keys()),
  )
  if not payload.template_slug:
    raise HTTPException(status_code=400, detail="template_slug is required.")

  template_row = get_template_by_slug(payload.template_slug)
  if not template_row:
    logger.warning(
      "Template not found when creating instance (template_slug=%s).",
      payload.template_slug,
    )
    raise HTTPException(status_code=404, detail="Template not found.")

  try:
    row = create_instance(payload, str(template_row["slug"]))
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  instance = Instance.model_validate(row)
  logger.info("Returning instance: %s", instance.model_dump())
  return instance


@router.get("/{instance_id}", response_model=InstanceDetail)
def read_form_instance(instance_id: str) -> InstanceDetail:
  logger.info("Read instance request: id=%s", instance_id)
  record = get_instance_with_template(instance_id)
  if not record:
    raise HTTPException(status_code=404, detail="Instance not found.")

  instance = Instance.model_validate(record["instance"])
  template = Template.model_validate(record["template"])
  logger.info(
    "Returning instance detail: instance_slug=%s template_slug=%s",
    instance.slug,
    template.slug,
  )
  return InstanceDetail(instance=instance, template=template)
