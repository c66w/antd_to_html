"""Comprehensive test suite for all API endpoints."""

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
  message = f"[✓] {step}"
  if detail:
    message += f": {detail}"
  print(message)


def _assert_status(resp: requests.Response, expected: int, step: str) -> None:
  if resp.status_code != expected:
    raise TestFailure(
      f"{step} failed (status {resp.status_code}): {resp.text[:400]}"
    )


def test_create_template(client: "ApiClient", slug: str) -> Dict[str, Any]:
  """测试创建模板接口"""
  print("\n=== 测试 1: POST /form-templates ===")
  payload = {
    "slug": slug,
    "title": "完整测试模板",
    "description": "用于测试所有接口的模板",
    "theme": "default",
    "definition": {
      "title": "完整测试表单",
      "subtitle": "这是一个测试表单",
      "items": [
        {"type": "input", "name": "username", "label": "用户名", "required": True},
        {"type": "password", "name": "password", "label": "密码", "required": True},
        {
          "type": "select",
          "name": "country",
          "label": "国家",
          "options": [
            {"label": "中国", "value": "cn"},
            {"label": "美国", "value": "us"},
          ],
        },
        {
          "type": "radio-group",
          "name": "plan",
          "label": "计划",
          "options": [
            {"label": "免费", "value": "free"},
            {"label": "专业", "value": "pro"},
          ],
          "defaultValue": "free",
        },
      ],
      "submit": {
        "callback": {
          "url": "https://example.com/callback",
          "method": "POST",
          "headers": {"X-Test": "true"},
        },
      },
    },
    "html_options": {
      "title": "测试表单",
      "contextBanner": {"label": "测试", "value": "true"},
    },
    "version": 1,
  }
  resp = client.post("/form-templates", json=payload, timeout=10.0)
  _assert_status(resp, 200, "创建模板")
  data = resp.json()
  assert "slug" in data, "响应应包含 slug 字段"
  assert data["slug"] == slug, "slug 应匹配"
  assert data["title"] == payload["title"], "标题应匹配"
  _log("创建模板成功", f"slug={data['slug']}")
  return data


def test_read_template_by_slug(client: "ApiClient", slug: str) -> None:
  """测试通过 slug 读取模板"""
  print("\n=== 测试 2: GET /form-templates/{slug} ===")
  resp = client.get(f"/form-templates/{slug}", timeout=10.0)
  _assert_status(resp, 200, "通过 slug 读取模板")
  data = resp.json()
  assert data["slug"] == slug, "slug 应匹配"
  _log("通过 slug 读取模板成功")


def test_preview_template(client: "ApiClient", slug: str) -> None:
  """测试预览模板接口"""
  print("\n=== 测试 3: GET /form-templates/{slug}/preview ===")
  resp = client.get(f"/form-templates/{slug}/preview", timeout=10.0)
  _assert_status(resp, 200, "预览模板")
  assert "text/html" in resp.headers.get("content-type", ""), "应返回 HTML"
  assert "<!DOCTYPE html>" in resp.text, "应包含 HTML 文档"
  assert "预览模式" in resp.text, "应包含预览提示"
  _log("预览模板成功", f"HTML 长度={len(resp.text)}")


def test_create_instance(client: "ApiClient", template_slug: str) -> Dict[str, Any]:
  """测试创建实例接口"""
  print("\n=== 测试 4: POST /form-instances ===")
  payload = {
    "template_slug": template_slug,
    "name": "测试实例",
    "runtime_config": {
      "submit": {
        "callback": {
          "url": "https://example.com/runtime-callback",
          "method": "POST",
          "params": {"test": "true"},
          "headers": {"X-Runtime": "test"},
        },
        "persistence": {
          "endpoint": "https://example.com/persistence",
          "headers": {"X-Persistence": "test"},
          "load_on_init": True,
          "update_text": "更新",
        },
      },
      "html": {
        "title": "运行时标题",
      },
    },
  }
  resp = client.post("/form-instances", json=payload, timeout=10.0)
  _assert_status(resp, 200, "创建实例")
  data = resp.json()
  assert "slug" in data, "响应应包含 slug 字段"
  assert data["template_slug"] == template_slug, "template_slug 应匹配"
  _log("创建实例成功", f"slug={data['slug']}")
  return data


def test_read_instance(client: "ApiClient", instance_slug: str) -> None:
  """测试读取实例接口"""
  print("\n=== 测试 5: GET /form-instances/{instance_slug} ===")
  resp = client.get(f"/form-instances/{instance_slug}", timeout=10.0)
  _assert_status(resp, 200, "读取实例")
  data = resp.json()
  assert "instance" in data, "响应应包含 instance 字段"
  assert "template" in data, "响应应包含 template 字段"
  assert data["instance"]["slug"] == instance_slug, "实例 slug 应匹配"
  _log("读取实例成功")


def test_render_form(client: "ApiClient", instance_slug: str) -> None:
  """测试渲染表单接口"""
  print("\n=== 测试 6: GET /forms/{instance_slug}/view ===")
  resp = client.get(f"/forms/{instance_slug}/view", timeout=10.0)
  _assert_status(resp, 200, "渲染表单")
  assert "text/html" in resp.headers.get("content-type", ""), "应返回 HTML"
  assert "<!DOCTYPE html>" in resp.text, "应包含 HTML 文档"
  assert "form" in resp.text.lower(), "应包含表单元素"
  _log("渲染表单成功", f"HTML 长度={len(resp.text)}")


def test_create_submission(client: "ApiClient", instance_slug: str) -> Dict[str, Any]:
  """测试创建提交接口"""
  print("\n=== 测试 7: POST /forms/{instance_slug}/submissions ===")
  payload = {
    "payload": {
      "values": {
        "username": "testuser",
        "password": "testpass",
        "country": "cn",
        "plan": "pro",
      },
    },
    "status": "submitted",
    "callback_status": "pending",
    "callback_info": {"message": "测试提交"},
  }
  resp = client.post(f"/forms/{instance_slug}/submissions", json=payload, timeout=10.0)
  _assert_status(resp, 200, "创建提交")
  data = resp.json()
  assert "id" in data, "响应应包含 id 字段（提交记录的主键）"
  assert data["instance_id"] == instance_slug, "instance_id 应匹配"
  assert data["status"] == "submitted", "status 应匹配"
  _log("创建提交成功", f"id={data['id']}")
  return data


def test_update_submission(client: "ApiClient", instance_slug: str, submission_id: str) -> None:
  """测试更新提交接口"""
  print("\n=== 测试 8: POST /forms/{instance_slug}/submissions (更新) ===")
  payload = {
    "submission_id": submission_id,
    "payload": {
      "values": {
        "username": "updated_user",
        "password": "updated_pass",
        "country": "us",
        "plan": "free",
      },
    },
    "status": "completed",
    "callback_status": "success",
    "callback_info": {"message": "更新成功"},
  }
  resp = client.post(f"/forms/{instance_slug}/submissions", json=payload, timeout=10.0)
  _assert_status(resp, 200, "更新提交")
  data = resp.json()
  assert data["id"] == submission_id, "提交 id 应匹配"
  assert data["status"] == "completed", "status 应更新"
  assert data["payload"]["values"]["username"] == "updated_user", "数据应更新"
  _log("更新提交成功")


def test_get_submission(client: "ApiClient", instance_slug: str, submission_id: str) -> None:
  """测试获取提交接口（指定 submission_id）"""
  print("\n=== 测试 9: GET /forms/{instance_slug}/submissions?submission_id=xxx ===")
  resp = client.get(
    f"/forms/{instance_slug}/submissions",
    params={"submission_id": submission_id},
    timeout=10.0,
  )
  _assert_status(resp, 200, "获取指定提交")
  data = resp.json()
  assert data["id"] == submission_id, "提交 id 应匹配"
  assert data["payload"]["values"]["username"] == "updated_user", "数据应正确"
  _log("获取指定提交成功")


def test_get_latest_submission(client: "ApiClient", instance_slug: str) -> None:
  """测试获取最新提交接口"""
  print("\n=== 测试 10: GET /forms/{instance_slug}/submissions ===")
  resp = client.get(f"/forms/{instance_slug}/submissions", timeout=10.0)
  _assert_status(resp, 200, "获取最新提交")
  data = resp.json()
  assert "id" in data, "响应应包含 id 字段"
  assert data["instance_id"] == instance_slug, "instance_id 应匹配"
  _log("获取最新提交成功", f"id={data['id']}")


def test_delete_template(client: "ApiClient", slug: str) -> None:
  """测试删除模板接口"""
  print("\n=== 测试 11: DELETE /form-templates/{slug} ===")
  resp = client.delete(f"/form-templates/{slug}", timeout=10.0)
  _assert_status(resp, 204, "删除模板")
  _log("删除模板成功")


def test_template_not_found(client: "ApiClient", slug: str) -> None:
  """测试模板不存在的情况"""
  print("\n=== 测试 12: GET /form-templates/{slug} (404) ===")
  resp = client.get(f"/form-templates/{slug}", timeout=10.0)
  _assert_status(resp, 404, "模板应不存在")
  _log("验证模板已删除")


def cleanup(client: "ApiClient", instance_slug: str) -> None:
  """清理测试数据"""
  print("\n=== 清理测试数据 ===")
  try:
    db.execute("DELETE FROM form_submissions WHERE instance_id = %s", (instance_slug,))
    db.execute("DELETE FROM form_instances WHERE slug = %s", (instance_slug,))
    _log("清理完成")
  except Exception as e:
    print(f"[警告] 清理失败: {e}")


def main() -> int:
  """主测试函数"""
  print("=" * 60)
  print("开始测试所有 API 接口")
  print("=" * 60)

  settings = get_settings()
  _log("加载配置", f"数据库={settings.pg_database}, 服务地址={BASE_URL}")

  # 生成唯一的测试标识
  timestamp = int(time.time())
  slug = f"test-all-apis-{timestamp}"

  try:
    with ApiClient(BASE_URL) as client:
      # 测试模板管理接口
      template = test_create_template(client, slug)
      template_slug = template["slug"]
      test_read_template_by_slug(client, template_slug)
      test_preview_template(client, template_slug)

      # 测试实例管理接口
      instance = test_create_instance(client, template_slug)
      instance_slug = instance["slug"]
      test_read_instance(client, instance_slug)

      # 测试运行时接口
      test_render_form(client, instance_slug)
      submission = test_create_submission(client, instance_slug)
      submission_id = submission["id"]
      test_update_submission(client, instance_slug, submission_id)
      test_get_submission(client, instance_slug, submission_id)
      test_get_latest_submission(client, instance_slug)

      # 测试删除接口
      cleanup(client, instance_slug)
      test_delete_template(client, template_slug)
      test_template_not_found(client, template_slug)

    print("\n" + "=" * 60)
    print("✓ 所有接口测试通过！")
    print("=" * 60)
    return 0

  except TestFailure as exc:
    print("\n" + "=" * 60)
    print(f"✗ 测试失败: {exc}")
    print("=" * 60)
    return 1
  except Exception as exc:
    print("\n" + "=" * 60)
    print(f"✗ 未预期的错误: {exc}")
    import traceback
    traceback.print_exc()
    print("=" * 60)
    return 1


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except KeyboardInterrupt:
    print("\n[中断] 测试被用户中断")
    raise SystemExit(1)

