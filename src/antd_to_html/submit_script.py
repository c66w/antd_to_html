"""Generate client-side submit script for inline execution."""

from __future__ import annotations

import json
from typing import Any, Mapping

DEFAULT_HEADERS = {
  "Accept": "application/json, text/x-json",
  "Content-Type": "application/json"
}


def build_submit_script(submit_config: Mapping[str, Any]) -> str:
  method = str(submit_config.get("method", "POST")).upper()
  callback_url = submit_config.get("callback_url")
  callback_params = submit_config.get("callback_params") or {}
  config = {
    "callback_url": callback_url,
    "method": method,
    "callback_params": callback_params,
    "headers": {**DEFAULT_HEADERS, **(submit_config.get("headers") or {})},
    "buttonSelector": submit_config.get("buttonSelector") or 'button[type="submit"]',
    "idleText": submit_config.get("idleText"),
    "pendingText": submit_config.get("pendingText") or "提交中...",
    "successText": submit_config.get("successText") or "提交成功",
    "failureText": submit_config.get("failureText") or "提交失败",
    "errorClass": submit_config.get("errorClass") or "field-error",
    "validationMessagePrefix": submit_config.get("validationMessagePrefix")
    or "Please fill all required fields: ",
    "submissionEndpoint": submit_config.get("submissionEndpoint"),
    "submissionHeaders": submit_config.get("submissionHeaders") or {},
    "submissionId": submit_config.get("submissionId"),
    "loadSubmissionOnInit": submit_config.get("loadSubmissionOnInit", True),
    "updateText": submit_config.get("updateText"),
  }

  serialized = _sanitize_json(config)
  script = """
(function() {{
  var CONFIG = __CONFIG_JSON__;
  var callback_url = CONFIG.callback_url || null;
  var callback_params = CONFIG.callback_params || {};

  var submissionState = {{
    endpoint: CONFIG.submissionEndpoint || null,
    headers: mergeHeaders(CONFIG.submissionHeaders),
    id: CONFIG.submissionId || null,
    status: null
  }};

  var updateText = CONFIG.updateText || '更新';

  ready(function() {{
    var button = document.querySelector(CONFIG.buttonSelector || 'button[type=\"submit\"]');
    if (!button) return;
    var form = button.closest('form') || document.querySelector('form');
    if (!form) return;

    var errorClass = CONFIG.errorClass || 'field-error';

    var idleText = typeof CONFIG.idleText === 'string' ? CONFIG.idleText : button.textContent;
    var pendingText = CONFIG.pendingText || button.textContent;
    var successText = CONFIG.successText || button.textContent;
    var failureText = CONFIG.failureText || button.textContent;

    if (typeof CONFIG.idleText === 'string') {{
      button.textContent = CONFIG.idleText;
    }}

    if (submissionState.endpoint && CONFIG.loadSubmissionOnInit !== false) {{
      loadExistingSubmission(form, button);
    }}

    function handle(event) {{
      event.preventDefault();

      var fields = collectFieldInfo(form);

      clearErrors(fields, errorClass);

      var invalid = [];
      for (var i = 0; i < fields.length; i += 1) {{
        var info = fields[i];
        if (info.required && !hasValue(info)) {{
          invalid.push(info);
        }}
      }}

      if (invalid.length) {{
        setButtonState(button, idleText, false);
        markErrors(invalid, errorClass);
        alertMissing(invalid);
        return;
      }}

      setButtonState(button, pendingText, true);

      var submissionPayload = collectPayload(fields);
      var callbackPayload = buildCallbackPayload(submissionPayload);

      saveSubmission(submissionPayload, {{
        status: callback_url ? 'submitted' : 'completed',
        callbackStatus: callback_url ? 'pending' : 'success'
      }})
        .then(function(row) {{
          submissionState.id = row.id || submissionState.id;
          submissionState.status = row.status || submissionState.status;

          if (!callback_url) {{
            setButtonState(button, successText, true);
            return null;
          }}

          return sendCallback(callbackPayload)
            .then(function(responseBody) {{
              return saveSubmission(submissionPayload, {{
                status: 'completed',
                callbackStatus: 'success',
                callbackInfo: responseBody || null,
                submissionId: submissionState.id
              }}).catch(function() {{ return null; }});
            }})
            .then(function() {{
              setButtonState(button, successText, true);
            }});
        })
        .catch(function(error) {{
          console.error('[form-submit] request failed:', error);
          if (submissionState.endpoint && submissionState.id) {{
            saveSubmission(submissionPayload, {{
              status: 'failed',
              callbackStatus: 'failed',
              callbackInfo: {{ error: String(error && error.message ? error.message : error) }},
              submissionId: submissionState.id
            }}).catch(function() {{ return null; }});
          }}
          setButtonState(button, failureText, false);
        }});
    }}

    form.addEventListener('submit', handle);
    if (button.type !== 'submit') {{
      button.addEventListener('click', handle);
    }}
  }});

  function mergeHeaders(custom) {{
    var base = {{
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }};
    if (custom && typeof custom === 'object') {{
      for (var key in custom) {{
        if (Object.prototype.hasOwnProperty.call(custom, key)) {{
          base[key] = custom[key];
        }}
      }}
    }}
    return base;
  }}

  function ready(fn) {{
    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', fn);
    }} else {{
      fn();
    }}
  }}

  function loadExistingSubmission(form, button) {{
    if (!submissionState.endpoint) return;
    var url = submissionState.endpoint;
    if (submissionState.id) {{
      url += '?submission_id=' + encodeURIComponent(submissionState.id);
    }}
    fetch(url, {{
      method: 'GET',
      headers: submissionState.headers
    }})
      .then(function(response) {{
        if (!response.ok) {{
          throw new Error('Load submission failed with status ' + response.status);
        }}
        return response.json();
      }})
      .then(function(data) {{
        if (!data || !data.payload) return;
        submissionState.id = data.id || submissionState.id;
        submissionState.status = data.status || submissionState.status;
        applyPayloadToForm(form, data.payload);
        if (updateText) {{
          setButtonState(button, updateText, false);
        }}
      }})
      .catch(function(error) {{
        if (error && console && console.warn) {{
          console.warn('[form-submit] unable to load submission:', error);
        }}
      }});
  }}

  function findLabelFor(element) {{
    if (!element || !element.id) return null;
    var labels = document.querySelectorAll('label[for]');
    for (var i = 0; i < labels.length; i += 1) {{
      if (labels[i].htmlFor === element.id) {{
        return labels[i];
      }}
    }}
    return null;
  }}

  function resolveFieldLabel(element, fallback) {{
    var direct = findLabelFor(element);
    if (direct && direct.textContent) {{
      return direct.textContent.trim() || fallback;
    }}
    var container = element ? element.closest('.form-item') : null;
    if (container) {{
      var formLabel = container.querySelector('.form-label');
      if (formLabel && formLabel.textContent) {{
        return formLabel.textContent.trim() || fallback;
      }}
    }}
    var listItem = element ? element.closest('.form-list-item') : null;
    if (listItem) {{
      var listLabel = listItem.querySelector('.form-list-item-label');
      if (listLabel && listLabel.textContent) {{
        return listLabel.textContent.trim() || fallback;
      }}
    }}
    return fallback;
  }}

  function detectFieldType(element) {{
    if (!element) return 'text';
    if (element.type === 'checkbox') return 'checkbox';
    if (element.type === 'radio') return 'radio';
    if (element.tagName === 'SELECT') {{
      return element.multiple ? 'select-multiple' : 'select';
    }}
    return 'text';
  }}

  function getOptionLabel(element, fallback) {{
    var label = element.closest('label');
    if (label && label.childNodes.length > 0) {{
      var clone = label.cloneNode(true);
      var inputs = clone.querySelectorAll('input');
      for (var i = inputs.length - 1; i >= 0; i -= 1) {{
        inputs[i].remove();
      }}
      var text = clone.textContent ? clone.textContent.trim() : '';
      return text || fallback;
    }}
    if (element.tagName === 'OPTION') {{
      return element.textContent.trim() || fallback;
    }}
    return fallback;
  }}

  function collectFieldInfo(form) {{
    var map = Object.create(null);
    var order = [];
    var controls = form.querySelectorAll('[name]');
    for (var i = 0; i < controls.length; i += 1) {{
      var control = controls[i];
      var name = control.getAttribute('name');
      if (!name) continue;
      if (!map[name]) {{
        map[name] = {{
          name: name,
          elements: [],
          label: resolveFieldLabel(control, name),
          required: false,
          type: detectFieldType(control),
          container: control.closest('.form-item') || null
        }};
        order.push(map[name]);
      }}
      var info = map[name];
      info.elements.push(control);
      if (control.required) {{
        info.required = true;
      }}
      var detected = detectFieldType(control);
      if (detected !== 'text') {{
        info.type = detected;
      }}
      if (!info.container) {{
        info.container = control.closest('.form-item') || null;
      }}
    }}
    return order;
  }}

  function hasValue(info) {{
    if (!info || !info.elements.length) return false;
    if (info.type === 'checkbox') {{
      for (var i = 0; i < info.elements.length; i += 1) {{
        if (info.elements[i].checked) return true;
      }}
      return false;
    }}
    if (info.type === 'radio') {{
      for (var j = 0; j < info.elements.length; j += 1) {{
        if (info.elements[j].checked) return true;
      }}
      return false;
    }}
    if (info.type === 'select-multiple') {{
      var select = info.elements[0];
      var options = select && select.selectedOptions ? select.selectedOptions : [];
      return options.length > 0;
    }}
    var element = info.elements[0];
    if (typeof element.value === 'string') {{
      return element.value.trim() !== '';
    }}
    return Boolean(element.value);
  }}

  function collectPayload(fields) {{
    var rows = [];
    var values = Object.create(null);
    for (var i = 0; i < fields.length; i += 1) {{
      var info = fields[i];
      if (!info.elements.length) continue;
      if (info.type === 'checkbox') {{
        var checked = [];
        var simple = [];
        for (var j = 0; j < info.elements.length; j += 1) {{
          var checkbox = info.elements[j];
          if (!checkbox.checked) continue;
          var entry = {{
            label: getOptionLabel(checkbox, info.label),
            value: checkbox.value
          }};
          checked.push(entry);
          simple.push(entry.value);
        }}
        if (checked.length) {{
          rows.push({{ label: info.label, name: info.name, value: checked }});
          values[info.name] = simple;
        }} else {{
          values[info.name] = [];
        }}
        continue;
      }}
      if (info.type === 'radio') {{
        var selected = null;
        for (var k = 0; k < info.elements.length; k += 1) {{
          if (info.elements[k].checked) {{
            selected = info.elements[k];
            break;
          }}
        }}
        if (selected) {{
          var payloadValue = {{
            label: getOptionLabel(selected, info.label),
            value: selected.value
          }};
          rows.push({{ label: info.label, name: info.name, value: payloadValue }});
          values[info.name] = payloadValue.value;
        }} else {{
          values[info.name] = null;
        }}
        continue;
      }}
      if (info.type === 'select-multiple') {{
        var select = info.elements[0];
        var opts = select && select.selectedOptions ? select.selectedOptions : [];
        var selectedValues = [];
        var simpleValues = [];
        for (var m = 0; m < opts.length; m += 1) {{
          var option = opts[m];
          selectedValues.push({{
            label: getOptionLabel(option, option.value),
            value: option.value
          }});
          simpleValues.push(option.value);
        }}
        rows.push({{ label: info.label, name: info.name, value: selectedValues }});
        values[info.name] = simpleValues;
        continue;
      }}
      var element = info.elements[0];
      rows.push({{ label: info.label, name: info.name, value: element.value }});
      values[info.name] = element.value;
    }}
    return {{ form_info: rows, values: values }};
  }}

  function buildCallbackPayload(submissionPayload) {{
    var base = {{}};
    if (callback_params && typeof callback_params === 'object') {{
      base = Object.assign(base, callback_params);
    }}
    base.feedback_data = {{ user_collect_data: submissionPayload }};
    return base;
  }}

  function clearErrors(fields, errorClass) {{
    for (var i = 0; i < fields.length; i += 1) {{
      var info = fields[i];
      for (var j = 0; j < info.elements.length; j += 1) {{
        var el = info.elements[j];
        el.classList.remove('error');
        el.removeAttribute('data-submit-error');
      }}
      if (info.container) {{
        info.container.classList.remove(errorClass);
      }}
    }}
  }}

  function markErrors(fields, errorClass) {{
    for (var i = 0; i < fields.length; i += 1) {{
      var info = fields[i];
      for (var j = 0; j < info.elements.length; j += 1) {{
        var el = info.elements[j];
        el.classList.add('error');
        el.setAttribute('data-submit-error', 'true');
      }}
      if (info.container) {{
        info.container.classList.add(errorClass);
      }}
    }}
  }}

  function alertMissing(fields) {{
    if (!fields.length) return;
    var labels = [];
    for (var i = 0; i < fields.length; i += 1) {{
      labels.push(fields[i].label);
    }}
    var message = labels.join(', ');
    var prefix = typeof CONFIG.validationMessagePrefix === 'string'
      ? CONFIG.validationMessagePrefix
      : 'Please fill all required fields: ';
    try {{
      window.alert(prefix + message);
    }} catch (_) {{}}
    var target = fields[0];
    if (target) {{
      var focusable = target.elements[0];
      if (focusable && typeof focusable.focus === 'function') {{
        focusable.focus({{ preventScroll: false }});
      }}
      var container = target.container || focusable;
      if (container && typeof container.scrollIntoView === 'function') {{
        container.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}
    }}
  }}

  function setButtonState(button, text, disabled) {{
    if (typeof text === 'string' && text.length) {{
      button.textContent = text;
    }}
    if (typeof disabled === 'boolean') {{
      button.disabled = disabled;
      button.classList.toggle('submit-btn-disabled', disabled);
      button.classList.toggle('is-submit-disabled', disabled);
    }}
  }}

  function saveSubmission(payload, options) {{
    if (!submissionState.endpoint) {{
      return Promise.resolve({{ id: submissionState.id, status: submissionState.status }});
    }}
    var status = options && options.status ? options.status : 'draft';
    var callbackStatus = options && options.callbackStatus ? options.callbackStatus : 'idle';
    var body = {{
      payload: payload,
      status: status,
      callback_status: callbackStatus
    }};
    if (options && options.callbackInfo) {{
      body.callback_info = options.callbackInfo;
    }}
    var submissionId = options && options.submissionId ? options.submissionId : submissionState.id;
    if (submissionId) {{
      body.submission_id = submissionId;
    }}
    return fetch(submissionState.endpoint, {{
      method: 'POST',
      headers: submissionState.headers,
      body: JSON.stringify(body)
    }})
      .then(function(response) {{
        if (!response.ok) {{
          throw new Error('Failed to save submission (' + response.status + ')');
        }}
        return response.json();
      }})
      .then(function(data) {{
        if (data && data.id) {{
          submissionState.id = data.id;
        }}
        if (data && data.status) {{
          submissionState.status = data.status;
        }}
        return data || {{}};
      }});
  }}

  function sendCallback(payload) {{
    if (!callback_url) {{
      return Promise.resolve(null);
    }}
    return fetch(callback_url, {{
      method: CONFIG.method,
      headers: CONFIG.headers,
      body: JSON.stringify(payload)
    }})
      .then(function(response) {{
        if (!response.ok) {{
          throw new Error('Request failed with status ' + response.status);
        }}
        var contentType = response.headers.get('content-type') || '';
        if (response.status === 204 || !contentType.includes('application/json')) {{
          return null;
        }}
        return response.json().catch(function() {{ return null; }});
      }});
  }}

  function applyPayloadToForm(form, payload) {{
    if (!payload || typeof payload !== 'object') return;
    var values = extractValues(payload);
    for (var name in values) {{
      if (!Object.prototype.hasOwnProperty.call(values, name)) continue;
      setControlValue(form, name, values[name]);
    }}
  }}

  var cssEscapeFn = (typeof CSS !== 'undefined' && CSS && typeof CSS.escape === 'function')
    ? CSS.escape
    : function(value) {{
        return String(value).replace(/[^a-zA-Z0-9_\\-]/g, '\\\\$&');
      }};

  function setControlValue(form, name, value) {{
    var controls = form.querySelectorAll('[name=\"' + cssEscapeFn(name) + '\"]');
    if (!controls || !controls.length) return;
    var type = detectFieldType(controls[0]);
    if (type === 'checkbox') {{
      var values = toValueList(value);
      for (var i = 0; i < controls.length; i += 1) {{
        var control = controls[i];
        control.checked = values.indexOf(control.value) !== -1;
      }}
      return;
    }}
    if (type === 'radio') {{
      var radioValue = toScalarValue(value);
      for (var j = 0; j < controls.length; j += 1) {{
        var radio = controls[j];
        radio.checked = radio.value === String(radioValue);
      }}
      return;
    }}
    var primary = controls[0];
    if (type === 'select-multiple') {{
      var multiValues = toValueList(value);
      var options = primary.options || [];
      for (var m = 0; m < options.length; m += 1) {{
        options[m].selected = multiValues.indexOf(options[m].value) !== -1;
      }}
      return;
    }}
    if (type === 'select') {{
      var singleValue = toScalarValue(value);
      primary.value = singleValue != null ? String(singleValue) : '';
      return;
    }}
    primary.value = toScalarValue(value) != null ? String(toScalarValue(value)) : '';
  }}

  function extractValues(payload) {{
    if (payload && typeof payload === 'object' && payload.values && typeof payload.values === 'object') {{
      return payload.values;
    }}
    if (payload && Array.isArray(payload.form_info)) {{
      var map = Object.create(null);
      for (var i = 0; i < payload.form_info.length; i += 1) {{
        var row = payload.form_info[i];
        map[row.name] = row.value;
      }}
      return map;
    }}
    return Object.create(null);
  }}

  function toScalarValue(value) {{
    if (value && typeof value === 'object' && Object.prototype.hasOwnProperty.call(value, 'value')) {{
      return value.value;
    }}
    if (Array.isArray(value)) {{
      return value.length ? toScalarValue(value[0]) : null;
    }}
    return value;
  }}

  function toValueList(value) {{
    if (!Array.isArray(value)) {{
      var scalar = toScalarValue(value);
      return scalar == null ? [] : [String(scalar)];
    }}
    var list = [];
    for (var i = 0; i < value.length; i += 1) {{
      var entry = value[i];
      if (entry && typeof entry === 'object' && Object.prototype.hasOwnProperty.call(entry, 'value')) {{
        list.push(String(entry.value));
      }} else if (entry != null) {{
        list.push(String(entry));
      }}
    }}
    return list;
  }}
})();
""".strip()

  script = script.replace("{{", "{").replace("}}", "}")
  return script.replace("__CONFIG_JSON__", serialized)


def _sanitize_json(payload: Mapping[str, Any]) -> str:
  text = json.dumps(payload, ensure_ascii=False)
  return (
    text.replace("<", "\\u003c")
    .replace(">", "\\u003e")
    .replace("\u2028", "\\u2028")
    .replace("\u2029", "\\u2029")
  )
