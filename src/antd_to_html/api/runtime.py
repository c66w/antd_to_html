"""Runtime endpoints for rendering forms and recording submissions."""

from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, HTTPException, Response

from ..models import Submission, SubmissionCreate
from ..render import convert_antd_form_to_html
from ..repositories import (
  RepositoryError,
  get_instance,
  get_instance_with_template,
  get_submission,
  save_submission,
)

router = APIRouter(tags=["runtime"])


@router.get("/forms/{instance_id}/view", response_class=Response)
def render_form(instance_id: str) -> Response:
  record = get_instance_with_template(instance_id)
  if not record:
    raise HTTPException(status_code=404, detail="Instance not found.")

  instance = record["instance"]
  template = record["template"]
  runtime_config = instance.get("runtime_config") or {}

  definition, html_options = merge_definition_with_runtime(template, runtime_config, instance["id"])

  try:
    html = convert_antd_form_to_html(definition, options={"html": html_options})
  except ValueError as exc:
    detail = getattr(exc, "details", None)
    raise HTTPException(status_code=422, detail=detail or str(exc)) from exc

  return Response(content=html, media_type="text/html; charset=utf-8")


@router.post("/forms/{instance_id}/submissions", response_model=Submission)
def submit_form(instance_id: str, payload: SubmissionCreate) -> Submission:
  record = get_instance_with_template(instance_id)
  if not record:
    raise HTTPException(status_code=404, detail="Instance not found.")

  if not payload.status:
    payload.status = "submitted"

  try:
    row = save_submission(instance_id, payload)
  except RepositoryError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc

  return Submission.model_validate(row)


@router.get("/forms/{instance_id}/submissions", response_model=Submission)
def load_submission(instance_id: str, submission_id: str | None = None) -> Submission:
  instance = get_instance(instance_id)
  if not instance:
    raise HTTPException(status_code=404, detail="Instance not found.")

  row = get_submission(instance_id, submission_id=submission_id)
  if not row:
    raise HTTPException(status_code=404, detail="Submission not found.")

  return Submission.model_validate(row)


def merge_definition_with_runtime(template: dict, runtime_config: dict, instance_id: str) -> tuple[dict, dict]:
  definition = deepcopy(template.get("definition") or {})
  html_options = deepcopy(template.get("html_options") or {})

  definition_overrides = runtime_config.get("definition") or runtime_config.get("definitionOverrides")
  if isinstance(definition_overrides, dict):
    _deep_merge(definition, definition_overrides)

  submit_override = runtime_config.get("submit")
  if isinstance(submit_override, dict):
    definition["submit"] = submit_override

  html_overrides = runtime_config.get("html") or runtime_config.get("htmlOptions")
  if isinstance(html_overrides, dict):
    html_options.update(html_overrides)

  submit_config = definition.setdefault("submit", {})
  submission_runtime = runtime_config.get("submission") or {}
  _normalize_submit_config(submit_config, submission_runtime)

  if "submissionEndpoint" not in submit_config:
    if submit_config.get("persistenceEndpoint"):
      submit_config["submissionEndpoint"] = submit_config.pop("persistenceEndpoint")
    elif submission_runtime.get("endpoint"):
      submit_config["submissionEndpoint"] = submission_runtime["endpoint"]
    else:
      submit_config["submissionEndpoint"] = f"/forms/{instance_id}/submissions"

  if "submissionHeaders" not in submit_config and submission_runtime.get("headers"):
    submit_config["submissionHeaders"] = submission_runtime["headers"]

  if submission_runtime.get("loadOnInit") is not None:
    submit_config["loadSubmissionOnInit"] = bool(submission_runtime["loadOnInit"])
  elif "loadSubmissionOnInit" not in submit_config:
    submit_config["loadSubmissionOnInit"] = True

  if "updateText" not in submit_config:
    submit_config["updateText"] = (
      submission_runtime.get("updateText") or submit_config.get("updateText") or "更新"
    )

  if submission_runtime.get("submissionId"):
    submit_config["submissionId"] = submission_runtime["submissionId"]

  return definition, html_options


def _deep_merge(target: dict, overrides: dict) -> None:
  for key, value in overrides.items():
    if key in target and isinstance(target[key], dict) and isinstance(value, dict):
      _deep_merge(target[key], value)
    else:
      target[key] = value


def _normalize_submit_config(submit_config: dict, submission_runtime: dict) -> None:
  callback = submit_config.get("callback")
  if isinstance(callback, dict):
    _apply_callback_config(submit_config, callback)

  persistence = submit_config.get("persistence")
  if isinstance(persistence, dict):
    _apply_persistence_config(submit_config, persistence)

  if submission_runtime:
    _apply_persistence_config(submit_config, submission_runtime, allow_primary_override=False)

  alias_map = {
    "submit_url": "submissionEndpoint",
    "persistence_endpoint": "submissionEndpoint",
    "submission_headers": "submissionHeaders",
    "callback_headers": "headers",
    "button_selector": "buttonSelector",
    "idle_text": "idleText",
    "pending_text": "pendingText",
    "success_text": "successText",
    "failure_text": "failureText",
  }
  for alias, target in alias_map.items():
    if alias in submit_config and target not in submit_config:
      submit_config[target] = submit_config[alias]
def _apply_callback_config(submit_config: dict, callback: dict) -> None:
  url = callback.get("url") or callback.get("callback_url")
  if url and "callback_url" not in submit_config:
    submit_config["callback_url"] = url

  method = callback.get("method")
  if method and "method" not in submit_config:
    submit_config["method"] = method

  headers = callback.get("headers")
  if headers and "headers" not in submit_config:
    submit_config["headers"] = headers

  params = (
    callback.get("params")
    or callback.get("callback_params")
  )
  if params and "callback_params" not in submit_config:
    submit_config["callback_params"] = params

  button_selector = callback.get("button_selector") or callback.get("buttonSelector")
  if button_selector and "buttonSelector" not in submit_config:
    submit_config["buttonSelector"] = button_selector

  for key in ("idleText", "pendingText", "successText", "failureText"):
    snake = key.replace("Text", "_text").lower()
    if snake in callback and key not in submit_config:
      submit_config[key] = callback[snake]


def _apply_persistence_config(
  submit_config: dict,
  persistence: dict,
  *,
  allow_primary_override: bool = True,
) -> None:
  endpoint = (
    persistence.get("endpoint")
    or persistence.get("url")
    or persistence.get("submission_endpoint")
    or persistence.get("submit_url")
  )
  if endpoint:
    if allow_primary_override or "persistenceEndpoint" not in submit_config:
      submit_config["persistenceEndpoint"] = endpoint

  headers = (
    persistence.get("headers")
    or persistence.get("submission_headers")
  )
  if headers and "submissionHeaders" not in submit_config:
    submit_config["submissionHeaders"] = headers

  load = (
    persistence.get("load_on_init")
    if "load_on_init" in persistence
    else persistence.get("loadSubmissionOnInit")
  )
  if load is not None and "loadSubmissionOnInit" not in submit_config:
    submit_config["loadSubmissionOnInit"] = bool(load)

  update = persistence.get("update_text") or persistence.get("updateText")
  if update and "updateText" not in submit_config:
    submit_config["updateText"] = update

  submission_id = (
    persistence.get("submission_id")
    or persistence.get("submissionId")
  )
  if submission_id and "submissionId" not in submit_config:
    submit_config["submissionId"] = submission_id
