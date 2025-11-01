"""Render Ant Design-like form definitions into HTML."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Dict, List

from .schema_validator import validate_form_definition
from .submit_script import build_submit_script

DEFAULT_HTML_OPTIONS = {
  "title": "Generated Form",
  "includeStyles": True,
  "styles": None,
}

BASE_STYLES = """
:root {
  color-scheme: light;
  --primary-color: #1677ff;
  --primary-hover: #0958d9;
  --primary-light: #e6f4ff;
  --border-color: #d9d9d9;
  --border-strong: #bfbfbf;
  --surface-color: #ffffff;
  --surface-muted: #f7f9fc;
  --background-color: #eef1f8;
  --text-color: #1f1f1f;
  --text-secondary: #595959;
  --text-tertiary: #8c8c8c;
  --danger-color: #ff4d4f;
  --success-color: #52c41a;
  --shadow-color: rgba(15, 23, 42, 0.16);
  font-size: 16px;
}
*,
*::before,
*::after {
  box-sizing: border-box;
}
body {
  margin: 0;
  min-height: 100vh;
  font-family: "Inter", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: linear-gradient(180deg, #dcedff 0%, #eef6ff 45%, #ffffff 100%);
  padding: 48px 16px;
  color: var(--text-color);
  line-height: 1.55;
}
.form-container {
  max-width: 920px;
  margin: 0 auto;
  background: var(--surface-color);
  border-radius: 18px;
  border: 1px solid rgba(22, 119, 255, 0.08);
  box-shadow: 0 40px 90px -48px rgba(22, 44, 90, 0.35);
  overflow: hidden;
}
.generated-form {
  padding: 40px 48px;
  display: block;
}
.form-header { margin-bottom: 32px; }
.form-title { margin: 0 0 12px; font-size: 28px; font-weight: 600; color: var(--text-color); }
.form-subtitle { margin: 0; font-size: 16px; color: var(--text-secondary); }
.form-row { display: flex; flex-wrap: wrap; margin: 0 -12px 24px; }
.form-col { padding: 0 12px; box-sizing: border-box; }
.form-item {
  background: var(--surface-muted);
  border: 1px solid rgba(9, 88, 217, 0.08);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.form-item:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 12px 24px -16px rgba(22, 119, 255, 0.5);
  transform: translateY(-1px);
  background: #fbfdff;
}
.form-label { font-size: 14px; font-weight: 600; color: var(--text-color); }
.required-asterisk { color: var(--danger-color); margin-left: 4px; }
.form-item > input,
.form-item > select,
.form-item > textarea,
.form-item .radio-group,
.form-item .checkbox-group,
.form-item .switch,
.form-item .form-list {
  width: 100%;
}
input,
select,
textarea {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 15px;
  font-family: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background-color: #fff;
  color: var(--text-color);
}
input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.15);
}
.form-divider {
  border: none;
  border-bottom: 1px dashed rgba(22, 119, 255, 0.3);
  margin: 32px 0;
}
.form-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 16px;
  flex-wrap: wrap;
}
.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  padding: 12px 28px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.4px;
  border-radius: 999px;
  cursor: pointer;
  border: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
}
.primary-button {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: #fff;
  box-shadow: 0 18px 36px -18px rgba(9, 88, 217, 0.7);
}
.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 40px -16px rgba(9, 88, 217, 0.8);
}
.secondary-button {
  background: rgba(22, 119, 255, 0.08);
  color: var(--primary-color);
  border: 1px solid rgba(22, 119, 255, 0.35);
  box-shadow: none;
}
.secondary-button:hover {
  background: rgba(22, 119, 255, 0.12);
  border-color: rgba(22, 119, 255, 0.45);
}
.primary-button:active,
.secondary-button:active {
  transform: translateY(0);
  box-shadow: none;
}
@media (max-width: 768px) {
  body { padding: 32px 12px; }
  .form-row { flex-direction: column; margin: 0 0 20px; }
  .form-col { padding: 0 !important; max-width: 100% !important; flex: 0 0 100% !important; }
  .form-actions { justify-content: stretch; }
  .form-actions button { flex: 1; }
}
""".strip()

FORM_LIST_SCRIPT = """
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.form-list').forEach(list => {
    const template = list.querySelector('template');
    const itemsContainer = list.querySelector('.form-list-items');
    if (!template || !itemsContainer) return;
    const min = parseInt(itemsContainer.dataset.min, 10) || 0;
    const max = parseInt(itemsContainer.dataset.max, 10) || Infinity;
    const baseName = list.dataset.name || '';

    const refresh = () => {
      const items = Array.from(itemsContainer.querySelectorAll('.form-list-item'));
      const emptyState = list.querySelector('[data-empty]');
      if (emptyState) {
        emptyState.style.display = items.length ? 'none' : 'block';
      }
      items.forEach((item, index) => {
        item.querySelectorAll('[name]').forEach(control => {
          if (!control.dataset.baseName) {
            control.dataset.baseName = control.getAttribute('name') || '';
          }
          const preserve = control.dataset.preserveName === 'true';
          const base = control.dataset.baseName;
          if (!baseName || !base || preserve) return;
          if (base.includes('[') || base.includes(']')) return;
          control.name = baseName + '[' + index + '].' + base;
          if (control.id) {
            const sanitized = base
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-+|-+$/g, '');
            control.id = baseName + '-' + index + '-' + sanitized;
          }
        });
      });
    };

    refresh();

    list.addEventListener('click', event => {
      const action = event.target.dataset.action;
      if (action === 'add') {
        if (itemsContainer.querySelectorAll('.form-list-item').length >= max) return;
        const prototype = template.content.firstElementChild;
        if (!prototype) return;
        const clone = prototype.cloneNode(true);
        itemsContainer.appendChild(clone);
        refresh();
      }
      if (action === 'remove') {
        const item = event.target.closest('.form-list-item');
        if (!item) return;
        if (itemsContainer.querySelectorAll('.form-list-item').length <= min) return;
        item.remove();
        refresh();
      }
    });
  });
});
""".strip()

DEFAULT_SPAN = 24


def convert_antd_form_to_html(definition: Mapping[str, Any], *, options: Mapping[str, Any] | None = None) -> str:
  errors = validate_form_definition(definition)
  if errors:
    error = ValueError("Form definition failed validation.")
    error.details = errors  # type: ignore[attr-defined]
    raise error

  html_options = dict(DEFAULT_HTML_OPTIONS)
  if options:
    html_options.update(options.get("html", {}))  # type: ignore[arg-type]

  page_title = (
    html_options.get("title")
    or definition.get("title")
    or (definition.get("form") or {}).get("title")
    or DEFAULT_HTML_OPTIONS["title"]
  )

  layout_ctx = build_layout_context(definition.get("form") or {})
  rendered_items = [render_item_with_layout(item, layout_ctx) for item in definition.get("items", [])]
  header = render_form_header(definition)
  actions_markup = default_actions()

  form_classes = ["generated-form"]
  form_options = definition.get("form") or {}
  if form_options.get("className"):
    form_classes.append(form_options["className"])
  if form_options.get("layout"):
    form_classes.append(f"layout-{form_options['layout']}")

  form_attrs = attributes_to_string(
    {
      "id": definition.get("id"),
      "class": " ".join(form_classes),
      "action": definition.get("action") or "#",
      "method": definition.get("method") or "post",
      "novalidate": "novalidate" if definition.get("novalidate") else None,
    }
  )
  form_attr_string = f" {form_attrs}" if form_attrs else ""

  scripts: List[str] = []
  if contains_form_list(definition.get("items", [])):
    scripts.append(FORM_LIST_SCRIPT)
  if definition.get("submit"):
    scripts.append(build_submit_script(definition["submit"]))  # type: ignore[arg-type]
  script_block = "\n".join(f"<script>\n{script}\n</script>" for script in scripts)

  styles = None
  if html_options.get("includeStyles", True):
    styles = html_options.get("styles") or BASE_STYLES
  style_block = f"<style>\n{styles}\n</style>" if styles else ""

  html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape_html(page_title)}</title>
  {style_block}
</head>
<body>
  <div class="form-container">
    <form{form_attr_string}>
      {header}
      {'\n'.join(rendered_items)}
      <div class="form-actions">
        {actions_markup}
      </div>
    </form>
  </div>
  {script_block}
</body>
</html>"""

  return html.strip()


def build_layout_context(form_options: Mapping[str, Any]) -> Dict[str, Any]:
  label_col = form_options.get("labelCol") or {"span": 8}
  wrapper_col = form_options.get("wrapperCol") or {"span": 16}
  gutter = form_options.get("gutter") if isinstance(form_options.get("gutter"), (int, float)) else 24
  return {"labelCol": label_col, "wrapperCol": wrapper_col, "gutter": gutter, "formOptions": form_options}


def render_item_with_layout(item: Mapping[str, Any], layout_ctx: Mapping[str, Any]) -> str:
  if item.get("hidden"):
    return ""
  if item.get("type") == "divider":
    return '<hr class="form-divider" />'

  col_span = get_span(item.get("colSpan") or item.get("span"), DEFAULT_SPAN)
  width_percentage = (col_span / DEFAULT_SPAN) * 100
  col_styles = [
    f"flex: 0 0 {width_percentage:.6f}%",
    f"max-width: {width_percentage:.6f}%",
  ]
  if isinstance(item.get("style"), Mapping):
    col_styles.append(inline_style_string(item["style"]))  # type: ignore[index]
  col_style = "; ".join(filter(None, col_styles))

  label = render_label(item)
  control = render_field(item)
  description = (
    f'<div class="form-description">{escape_html(item["description"])}</div>'
    if item.get("description")
    else ""
  )
  help_text = f'<div class="form-help">{escape_html(item["help"])}</div>' if item.get("help") else ""
  extra = f'<div class="form-extra">{escape_html(item["extra"])}</div>' if item.get("extra") else ""

  row_class = " ".join(filter(None, ["form-row", item.get("rowClassName")]))
  col_class = " ".join(filter(None, ["form-col", item.get("colClassName")]))
  item_class = " ".join(filter(None, ["form-item", item.get("className")]))

  return (
    f'<div class="{row_class}">'
    f'<div class="{col_class}" style="{col_style}">'
    f'<div class="{item_class}">'
    f"{label}{control}{description}{help_text}{extra}"
    "</div></div></div>"
  )


def render_label(item: Mapping[str, Any]) -> str:
  label = item.get("label")
  if not label:
    return ""
  required = '<span class="required-asterisk">*</span>' if item.get("required") else ""
  name = escape_html(item.get("name") or "")
  return f'<label class="form-label" for="{name}">{escape_html(label)}{required}</label>'


def get_span(value: Any, fallback: int) -> int:
  if isinstance(value, (int, float)) and value > 0:
    return min(int(value), DEFAULT_SPAN)
  return fallback


def inline_style_string(styles: Mapping[str, Any]) -> str:
  parts = []
  for key, value in styles.items():
    kebab = "".join(f"-{c.lower()}" if c.isupper() else c for c in str(key))
    parts.append(f"{kebab}:{value}")
  return ";".join(parts)


def render_form_header(definition: Mapping[str, Any]) -> str:
  title = definition.get("title") or (definition.get("form") or {}).get("title")
  subtitle = (
    definition.get("subtitle")
    or (definition.get("form") or {}).get("subtitle")
    or definition.get("description")
    or (definition.get("form") or {}).get("description")
  )
  if not title and not subtitle:
    return ""

  title_markup = f'<h1 class="form-title">{escape_html(title)}</h1>' if title else ""
  subtitle_markup = f'<p class="form-subtitle">{escape_html(subtitle)}</p>' if subtitle else ""
  return f'<header class="form-header">{title_markup}{subtitle_markup}</header>'


def default_actions() -> str:
  return (
    '<button type="submit" class="primary-button">提交</button>\n'
    '<button type="reset" class="secondary-button">重置</button>'
  )


def contains_form_list(items: Iterable[Any]) -> bool:
  for item in items:
    if not isinstance(item, Mapping):
      continue
    if item.get("type") == "form-list":
      return True
    child_items = item.get("items")
    if isinstance(child_items, Iterable) and not isinstance(child_items, (str, bytes)):
      if contains_form_list(child_items):  # type: ignore[arg-type]
        return True
    child = item.get("item")
    if isinstance(child, Mapping) and contains_form_list([child]):
      return True
  return False


def render_field(item: Mapping[str, Any]) -> str:
  renderer = TYPE_RENDERERS.get(item.get("type"))
  if not renderer:
    return f"<div><!-- Unsupported field type: {escape_html(item.get('type') or 'unknown')} --></div>"
  return renderer(item)


def render_text_input(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(item, {"type": "text", "value": default_value(item)})
  return f"<input {attrs} />"


def render_textarea(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(item, {"rows": item.get("rows") or 4})
  value = default_value(item) or ""
  return f"<textarea {attrs}>{escape_html(value)}</textarea>"


def render_password(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(item, {"type": "password", "value": default_value(item)})
  return f"<input {attrs} />"


def render_number(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(
    item,
    {
      "type": "number",
      "min": number_or_null(item.get("min")),
      "max": number_or_null(item.get("max")),
      "step": number_or_null(item.get("step")),
      "value": default_value(item),
    },
  )
  return f"<input {attrs} />"


def render_select(item: Mapping[str, Any]) -> str:
  values = value_set(default_value(item))
  attrs = control_attributes(
    item,
    {"multiple": item.get("mode") == "multiple" or item.get("multiple") or None},
  )
  options_markup = []
  for option in item.get("options", []):
    value = option.get("value") or option.get("key") or option.get("label") or ""
    label = option.get("label") or option.get("value") or ""
    option_attrs = attributes_to_string({"value": value, "selected": value in values})
    options_markup.append(f"<option {option_attrs}>{escape_html(label)}</option>")
  return f"<select {attrs}>\n  {'\\n  '.join(options_markup)}\n</select>"


def render_radio_group(item: Mapping[str, Any]) -> str:
  selected = default_value(item)
  group_name = item.get("name") or ""
  options_markup = []
  for index, option in enumerate(item.get("options", [])):
    option_value = option.get("value") or option.get("key") or option.get("label") or ""
    option_id = option.get("id") or f"{group_name}-{index}"
    attrs = attributes_to_string(
      {
        "type": "radio",
        "id": option_id,
        "name": group_name,
        "value": option_value,
        "checked": option.get("checked") or option_value == selected,
        "disabled": option.get("disabled"),
      }
    )
    label = option.get("label") or option_value
    options_markup.append(
      f'<label for="{escape_html(option_id)}"><input {attrs} /> {escape_html(label)}</label>'
    )
  classes = " ".join(filter(None, ["radio-group", item.get("controlClassName")]))
  return f'<div class="{classes}">{"".join(options_markup)}</div>'


def render_checkbox_group(item: Mapping[str, Any]) -> str:
  values = value_set(default_value(item))
  group_name = item.get("name") or ""
  options_markup = []
  for index, option in enumerate(item.get("options", [])):
    option_value = option.get("value") or option.get("key") or option.get("label") or ""
    option_id = option.get("id") or f"{group_name}-{index}"
    attrs = attributes_to_string(
      {
        "type": "checkbox",
        "id": option_id,
        "name": group_name,
        "value": option_value,
        "checked": option.get("checked") or option_value in values,
        "disabled": option.get("disabled"),
      }
    )
    label = option.get("label") or option_value
    options_markup.append(
      f'<label for="{escape_html(option_id)}"><input {attrs} /> {escape_html(label)}</label>'
    )
  classes = " ".join(filter(None, ["checkbox-group", item.get("controlClassName")]))
  return f'<div class="{classes}">{"".join(options_markup)}</div>'


def render_switch(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(
    item,
    {
      "type": "checkbox",
      "checked": item.get("checked", default_value(item)),
    },
  )
  return f'<label class="switch"><input {attrs} /><span class="slider"></span></label>'


def render_date_picker(item: Mapping[str, Any]) -> str:
  attrs = control_attributes(
    item,
    {"type": "datetime-local" if item.get("showTime") else "date", "value": default_value(item)},
  )
  return f"<input {attrs} />"


def render_form_list(item: Mapping[str, Any]) -> str:
  field_config = item.get("item") or {}
  child_control = render_field(field_config)
  child_label = (
    f'<div class="form-list-item-label">{escape_html(field_config["label"])}</div>'
    if field_config.get("label")
    else ""
  )
  child_description = (
    f'<div class="form-list-item-description">{escape_html(field_config["description"])}</div>'
    if field_config.get("description")
    else ""
  )
  child_help = (
    f'<div class="form-list-item-help">{escape_html(field_config["help"])}</div>'
    if field_config.get("help")
    else ""
  )
  list_item_content = f"{child_label}{child_control}{child_description}{child_help}"

  start_empty = bool(item.get("startEmpty"))
  min_items = item.get("min") if isinstance(item.get("min"), (int, float)) else None
  max_items = item.get("max") if isinstance(item.get("max"), (int, float)) else None
  min_attr = str(int(min_items)) if min_items is not None else ""
  max_attr = str(int(max_items)) if max_items is not None else ""

  remove_label = escape_html(item.get("removeLabel") or "Remove")
  initial_items = ""
  if not start_empty:
    initial_items = (
      f'<div class="form-list-item">{list_item_content}'
      f'<button type="button" class="list-remove" data-action="remove">{remove_label}</button>'
      "</div>"
    )

  template = (
    f'<template id="{escape_html(item.get("name") or "")}-template">'
    f'<div class="form-list-item">{list_item_content}'
    f'<button type="button" class="list-remove" data-action="remove">{remove_label}</button>'
    "</div>"
    "</template>"
  )

  empty_text = ""
  if item.get("emptyText"):
    empty_text = f'<div class="form-list-empty" data-empty>{escape_html(item["emptyText"])}</div>'

  add_label = escape_html(item.get("addLabel") or "Add")
  return (
    f'<div class="form-list" data-name="{escape_html(item.get("name") or "")}">'
    f'<div class="form-list-items" data-min="{min_attr}" data-max="{max_attr}">{initial_items}</div>'
    f"{empty_text}"
    '<div class="form-list-actions">'
    f'<button type="button" class="list-add" data-action="add">{add_label}</button>'
    "</div>"
    f"{template}"
    "</div>"
  )


TYPE_RENDERERS = {
  "input": render_text_input,
  "textarea": render_textarea,
  "password": render_password,
  "number": render_number,
  "select": render_select,
  "radio-group": render_radio_group,
  "checkbox-group": render_checkbox_group,
  "switch": render_switch,
  "date-picker": render_date_picker,
  "divider": lambda item: '<hr class="form-divider" />',
  "form-list": render_form_list,
}


def control_attributes(item: Mapping[str, Any], extra: Mapping[str, Any] | None = None) -> str:
  attrs: Dict[str, Any] = {
    "id": item.get("id") or item.get("name"),
    "name": item.get("name"),
    "placeholder": item.get("placeholder"),
    "required": item.get("required"),
    "disabled": item.get("disabled"),
    "readonly": item.get("readOnly") or item.get("readonly"),
  }
  if extra:
    attrs.update(extra)

  if item.get("controlClassName"):
    attrs["class"] = (
      f'{attrs["class"]} {item["controlClassName"]}' if attrs.get("class") else item["controlClassName"]
    )

  if isinstance(item.get("htmlAttributes"), Mapping):
    attrs.update(item["htmlAttributes"])  # type: ignore[index]

  return attributes_to_string(attrs)


def default_value(item: Mapping[str, Any]) -> Any:
  for key in ("defaultValue", "initialValue", "value"):
    if key in item:
      return item[key]
  return None


def number_or_null(value: Any) -> Any:
  return value if isinstance(value, (int, float)) else None


def value_set(value: Any) -> set[Any]:
  return set(normalize_array(value))


def normalize_array(value: Any) -> List[Any]:
  if value is None:
    return []
  if isinstance(value, (list, tuple, set)):
    return list(value)
  return [value]


def escape_html(value: Any) -> str:
  text = "" if value is None else str(value)
  return (
    text.replace("&", "&amp;")
    .replace("<", "&lt;")
    .replace(">", "&gt;")
    .replace('"', "&quot;")
    .replace("'", "&#39;")
  )


def attributes_to_string(attrs: Mapping[str, Any]) -> str:
  parts: List[str] = []
  for key, value in attrs.items():
    if value in (None, False):
      continue
    if value is True:
      parts.append(str(key))
    else:
      parts.append(f'{key}="{escape_html(value)}"')
  return " ".join(parts)
