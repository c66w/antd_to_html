"""Pydantic models used across the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TemplateCreate(BaseModel):
  model_config = ConfigDict(extra="ignore")

  id: Optional[str] = None
  slug: Optional[str] = None
  title: str
  description: Optional[str] = None
  theme: Optional[str] = None
  definition: dict[str, Any]
  html_options: dict[str, Any] = Field(default_factory=dict)
  version: int = 1


class Template(TemplateCreate):
  id: str
  created_at: datetime
  updated_at: datetime


class InstanceCreate(BaseModel):
  model_config = ConfigDict(extra="ignore")

  id: Optional[str] = None
  template_id: Optional[str] = None
  template_slug: Optional[str] = None
  name: Optional[str] = None
  runtime_config: dict[str, Any] = Field(default_factory=dict)

  @model_validator(mode="after")
  def ensure_template_reference(self):
    if not self.template_id and not self.template_slug:
      raise ValueError("template_id or template_slug is required.")
    return self


class Instance(InstanceCreate):
  id: str
  template_id: str
  created_at: datetime
  updated_at: datetime


class InstanceDetail(BaseModel):
  instance: Instance
  template: Template


class SubmissionBase(BaseModel):
  model_config = ConfigDict(extra="ignore", populate_by_name=True)

  payload: dict[str, Any]
  status: str = "draft"
  callback_info: Optional[dict[str, Any]] = None
  callback_status: Optional[str] = Field(default=None, alias="callback_status")


class SubmissionCreate(SubmissionBase):
  submission_id: Optional[str] = Field(default=None, alias="submission_id")


class Submission(SubmissionBase):
  id: str
  instance_id: str
  submitted_at: datetime
  updated_at: datetime
