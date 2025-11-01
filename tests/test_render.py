from __future__ import annotations

from antd_to_html.render import convert_antd_form_to_html


def test_basic_render():
  definition = {
    "title": "测试表单",
    "items": [
      {
        "type": "input",
        "name": "username",
        "label": "用户名",
        "required": True,
      }
    ],
  }

  html = convert_antd_form_to_html(definition)
  assert "<!DOCTYPE html>" in html
  assert "测试表单" in html
  assert 'name="username"' in html
