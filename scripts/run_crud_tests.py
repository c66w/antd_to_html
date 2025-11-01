"""End-to-end smoke test covering create/read/update/delete flows."""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict

import requests

from antd_to_html import db
from antd_to_html.config import get_settings

BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://localhost:8400")


class TestFailure(RuntimeError):
  """Raised when a test step fails."""


class ApiClient:
  """Minimal wrapper around requests.Session with base URL support."""

  def __init__(self, base_url: str):
    self.base_url = base_url.rstrip("/")
    self.session = requests.Session()

  def __enter__(self) -> "ApiClient":
    return self

  def __exit__(self, exc_type, exc, tb) -> None:
    self.session.close()

  def _url(self, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
      return path
    return f"{self.base_url}{path}"

  def get(self, path: str, **kwargs) -> requests.Response:
    return self.session.get(self._url(path), **kwargs)

  def post(self, path: str, **kwargs) -> requests.Response:
    return self.session.post(self._url(path), **kwargs)

  def delete(self, path: str, **kwargs) -> requests.Response:
    return self.session.delete(self._url(path), **kwargs)


def _log(step: str, detail: str = "") -> None:
  message = f"[OK] {step}"
  if detail:
    message += f": {detail}"
  print(message)


def _assert_status(resp: requests.Response, expected: int, step: str) -> None:
  if resp.status_code != expected:
    raise TestFailure(
      f"{step} failed (status {resp.status_code}): {resp.text[:400]}"
    )


def _create_template(client: "ApiClient", slug: str) -> Dict[str, Any]:
  payload = {
    "slug": slug,
    "title": "CRUD 测试模板",
    "description": "自动化测试用模板",
    "definition": {
      "title": "CRUD 测试模板",
      "items": [
        {"type": "input", "name": "field_a", "label": "字段A", "required": True},
        {"type": "select", "name": "field_b", "label": "字段B", "options": [
          {"label": "选项1", "value": "opt-1"},
          {"label": "选项2", "value": "opt-2"},
        ]},
      ],
      "submit": {
        "callback": {
          "url": "https://example.com/callback",
          "method": "POST",
          "headers": {"X-Demo": "crud-test"}
        }
      },
    },
    "html_options": {"title": "CRUD 模板"},
  }
  resp = client.post("/form-templates", json=payload, timeout=10.0)
  _assert_status(resp, 200, "Create template")
  data = resp.json()
  _log("Create template", f"id={data['id']}")
  return data


def _read_template(client: "ApiClient", template_id: str, slug: str) -> None:
  resp = client.get(f"/form-templates/{template_id}", timeout=10.0)
  _assert_status(resp, 200, "Read template by id")
  _log("Read template by id")

  resp = client.get(f"/form-templates/{slug}", timeout=10.0)
  _assert_status(resp, 200, "Read template by slug")
  _log("Read template by slug")


def _create_instance(client: "ApiClient", slug: str) -> Dict[str, Any]:
  payload = {
    "template_slug": slug,
    "name": "crud-instance",
    "runtime_config": {
      "submit": {
        "callback": {
          "url": "https://example.com/runtime-callback",
          "method": "POST",
          "headers": {"X-Instance": "crud"}
        },
        "persistence": {"load_on_init": True, "update_text": "更新数据"}
      },
    },
  }
  resp = client.post("/form-instances", json=payload, timeout=10.0)
  _assert_status(resp, 200, "Create instance")
  data = resp.json()
  _log("Create instance", f"id={data['id']}")
  return data


def _read_instance(client: "ApiClient", instance_id: str) -> None:
  resp = client.get(f"/form-instances/{instance_id}", timeout=10.0)
  _assert_status(resp, 200, "Read instance")
  _log("Read instance detail")


def _render_runtime(client: "ApiClient", instance_id: str) -> None:
  resp = client.get(f"/forms/{instance_id}/view", timeout=10.0)
  _assert_status(resp, 200, "Render runtime view")
  content_type = resp.headers.get("content-type", "")
  if "text/html" not in content_type:
    raise TestFailure("Runtime view did not return HTML content.")
  _log("Render runtime view", f"content-length={len(resp.text)}")


def _submission_roundtrip(client: "ApiClient", instance_id: str) -> str:
  payload = {
    "payload": {"values": {"field_a": "hello", "field_b": "opt-2"}},
    "status": "submitted",
    "callback_status": "pending",
  }
  resp = client.post(
    f"/forms/{instance_id}/submissions",
    json=payload,
    timeout=10,
  )
  _assert_status(resp, 200, "Create submission")
  data = resp.json()
  submission_id = data["id"]
  _log("Create submission", f"id={submission_id}")

  # Update the existing submission by reusing submission_id
  payload_update = {
    "submission_id": submission_id,
    "payload": {"values": {"field_a": "updated", "field_b": "opt-1"}},
    "status": "completed",
    "callback_status": "success",
    "callback_info": {"message": "ok"},
  }
  resp = client.post(
    f"/forms/{instance_id}/submissions",
    json=payload_update,
    timeout=10,
  )
  _assert_status(resp, 200, "Update submission")
  _log("Update submission")

  resp = client.get(
    f"/forms/{instance_id}/submissions",
    params={"submission_id": submission_id},
    timeout=10,
  )
  _assert_status(resp, 200, "Read submission")
  returned = resp.json()
  if returned["payload"]["values"]["field_a"] != "updated":
    raise TestFailure("Submission did not persist updated payload.")
  _log("Read submission", "payload verified")
  return submission_id


def _cleanup(client: "ApiClient", instance_id: str, template_id: str) -> None:
  # Remove submission and instance rows directly to allow deleting template via API.
  db.execute("DELETE FROM form_submissions WHERE instance_id = %s", (instance_id,))
  db.execute("DELETE FROM form_instances WHERE id = %s", (instance_id,))

  resp = client.delete(f"/form-templates/{template_id}", timeout=10.0)
  _assert_status(resp, 204, "Delete template")
  _log("Delete template via API")

  resp = client.get(f"/form-templates/{template_id}", timeout=10.0)
  if resp.status_code != 404:
    raise TestFailure("Template was not deleted.")
  _log("Verify template deleted")


def main() -> int:
  settings = get_settings()  # Ensures env vars are loaded for DB cleanup.
  _log("Loaded settings", f"DB={settings.pg_database}")

  slug = f"crud-test-{int(time.time())}"
  with ApiClient(BASE_URL) as client:
    template = _create_template(client, slug)
    template_id = template["id"]
    _read_template(client, template_id, slug)

    instance = _create_instance(client, slug)
    instance_id = instance["id"]
    _read_instance(client, instance_id)

    _render_runtime(client, instance_id)
    _submission_roundtrip(client, instance_id)
    _cleanup(client, instance_id, template_id)
  _log("CRUD smoke test completed successfully")
  return 0


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except TestFailure as exc:
    print(f"[FAIL] {exc}", file=sys.stderr)
    raise SystemExit(1)
