"""Validation helpers for Ant Design-like form definitions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SUPPORTED_FIELD_TYPES = {
  "input",
  "textarea",
  "password",
  "number",
  "select",
  "radio-group",
  "checkbox-group",
  "switch",
  "date-picker",
  "form-list",
  "divider",
}

TYPES_REQUIRING_OPTIONS = {"select", "radio-group", "checkbox-group"}
TYPES_REQUIRING_NAME = {
  "input",
  "textarea",
  "password",
  "number",
  "select",
  "radio-group",
  "checkbox-group",
  "switch",
  "date-picker",
  "form-list",
}


def validate_form_definition(definition: Any) -> list[str]:
  if not isinstance(definition, Mapping):
    return ["Form definition must be an object."]

  errors: list[str] = []
  items = definition.get("items")
  if not isinstance(items, list):
    errors.append('Form definition must include an "items" array.')
  else:
    for index, item in enumerate(items):
      validate_form_item(item, f"items[{index}]", errors, item)

  submit = definition.get("submit")
  if submit is not None:
    validate_submit_config(submit, errors)

  return errors


def validate_form_item(item: Any, path: str, errors: list[str], raw_item: Any | None = None) -> None:
  if not isinstance(item, Mapping):
    errors.append(f"{path} must be an object.")
    return

  item_type = item.get("type")
  if item_type not in SUPPORTED_FIELD_TYPES:
    supported = ", ".join(sorted(SUPPORTED_FIELD_TYPES))
    errors.append(f'{path}.type must be one of: {supported}.')

  if item_type in TYPES_REQUIRING_NAME:
    if not isinstance(item.get("name"), str):
      errors.append(f'{path}.name is required for type "{item_type}".')

  if item_type in TYPES_REQUIRING_OPTIONS:
    if not isinstance(item.get("options"), list):
      actual = type(item.get("options")).__name__
      descriptor = _format_item(raw_item or item)
      errors.append(
        f'{path}.options must be an array for type "{item_type}" '
        f'(received {actual}). Item: {descriptor}'
      )

  if item_type == "form-list":
    child = item.get("item")
    if child is None:
      errors.append(f"{path}.item is required for form-list.")
    else:
      validate_form_item(child, f"{path}.item", errors, child)


def validate_submit_config(submit: Any, errors: list[str]) -> None:
  if not isinstance(submit, Mapping):
    errors.append("submit must be an object when provided.")
    return

  callback = submit.get("callback")
  if isinstance(callback, Mapping):
    callback_url = callback.get("url") or callback.get("callback_url")
    if not isinstance(callback_url, str) or not callback_url.strip():
      errors.append("submit.callback.url must be a non-empty string.")
    callback_params = callback.get("params") or callback.get("callback_params")
    if callback_params is not None and not _is_plain_object(callback_params):
      errors.append("submit.callback.params must be an object when provided.")
  else:
    callback_url = submit.get("callback_url")
    if callback_url is not None:
      if not isinstance(callback_url, str) or not callback_url.strip():
        errors.append("submit.callback_url must be a non-empty string.")

    if "callback_params" in submit and not _is_plain_object(submit.get("callback_params")):
      errors.append("submit.callback_params must be an object when provided.")

  persistence = submit.get("persistence")
  if persistence is not None and not isinstance(persistence, Mapping):
    errors.append("submit.persistence must be an object when provided.")

  if "method" in submit and not _is_http_method(submit.get("method")):
    errors.append("submit.method must be one of: POST, PUT, PATCH, DELETE.")

  string_fields = [
    "buttonSelector",
    "idleText",
    "pendingText",
    "successText",
    "failureText",
    "errorClass",
    "validationMessagePrefix",
  ]

  for field in string_fields:
    if field in submit and not isinstance(submit.get(field), str):
      errors.append(f"submit.{field} must be a string when provided.")

  headers = submit.get("headers")
  if "headers" in submit and not _is_plain_object(headers):
    errors.append("submit.headers must be an object whose values are strings.")
  elif isinstance(headers, Mapping):
    for key, value in headers.items():
      if not isinstance(value, str):
        errors.append(f"submit.headers[{key}] must be a string.")


def _is_plain_object(value: Any) -> bool:
  return isinstance(value, Mapping)


def _is_http_method(value: Any) -> bool:
  if not isinstance(value, str):
    return False
  return value.upper() in {"POST", "PUT", "PATCH", "DELETE"}


def _format_item(item: Any) -> str:
  try:
    import json

    return json.dumps(item, ensure_ascii=False, separators=(",", ":"), default=str)
  except Exception:
    return str(item)
