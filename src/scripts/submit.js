const DEFAULT_HEADERS = {
  Accept: 'application/json, text/x-json',
  'Content-Type': 'application/json'
};

export function buildSubmitScript(submitConfig) {
  const method = (submitConfig.method || 'POST').toUpperCase();
  const configForClient = {
    callbackUrl: submitConfig.callbackUrl,
    method,
    callbackParams: submitConfig.callbackParams || {},
    headers: { ...DEFAULT_HEADERS, ...(submitConfig.headers || {}) },
    buttonSelector: submitConfig.buttonSelector || 'button[type="submit"]',
    idleText: submitConfig.idleText ?? null,
    pendingText: submitConfig.pendingText || 'Submitting...',
    successText: submitConfig.successText || 'Submitted',
    failureText: submitConfig.failureText || 'Submit failed',
    errorClass: submitConfig.errorClass || 'field-error',
    validationMessagePrefix:
      submitConfig.validationMessagePrefix || 'Please fill all required fields: '
  };

  const serializedConfig = serializeConfig(configForClient);

  return `
(function() {
  var CONFIG = ${serializedConfig};

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  function findLabelFor(element) {
    if (!element || !element.id) return null;
    var labels = document.querySelectorAll('label[for]');
    for (var i = 0; i < labels.length; i += 1) {
      if (labels[i].htmlFor === element.id) {
        return labels[i];
      }
    }
    return null;
  }

  function resolveFieldLabel(element, fallback) {
    var direct = findLabelFor(element);
    if (direct && direct.textContent) {
      return direct.textContent.trim() || fallback;
    }
    var container = element ? element.closest('.form-item') : null;
    if (container) {
      var formLabel = container.querySelector('.form-label');
      if (formLabel && formLabel.textContent) {
        return formLabel.textContent.trim() || fallback;
      }
    }
    var listItem = element ? element.closest('.form-list-item') : null;
    if (listItem) {
      var listLabel = listItem.querySelector('.form-list-item-label');
      if (listLabel && listLabel.textContent) {
        return listLabel.textContent.trim() || fallback;
      }
    }
    return fallback;
  }

  function detectFieldType(element) {
    if (!element) return 'text';
    if (element.type === 'checkbox') return 'checkbox';
    if (element.type === 'radio') return 'radio';
    if (element.tagName === 'SELECT') {
      return element.multiple ? 'select-multiple' : 'select';
    }
    return 'text';
  }

  function collectFieldInfo(form) {
    var map = Object.create(null);
    var order = [];
    var controls = form.querySelectorAll('[name]');
    for (var i = 0; i < controls.length; i += 1) {
      var control = controls[i];
      var name = control.getAttribute('name');
      if (!name) continue;
      if (!map[name]) {
        map[name] = {
          name: name,
          elements: [],
          label: resolveFieldLabel(control, name),
          required: false,
          type: detectFieldType(control),
          container: control.closest('.form-item') || null
        };
        order.push(map[name]);
      }
      var info = map[name];
      info.elements.push(control);
      if (control.required) {
        info.required = true;
      }
      var detected = detectFieldType(control);
      if (detected !== 'text') {
        info.type = detected;
      }
      if (!info.container) {
        info.container = control.closest('.form-item') || null;
      }
    }
    return order;
  }

  function hasValue(info) {
    if (!info || !info.elements.length) return false;
    if (info.type === 'checkbox') {
      for (var i = 0; i < info.elements.length; i += 1) {
        if (info.elements[i].checked) return true;
      }
      return false;
    }
    if (info.type === 'radio') {
      for (var j = 0; j < info.elements.length; j += 1) {
        if (info.elements[j].checked) return true;
      }
      return false;
    }
    if (info.type === 'select-multiple') {
      var select = info.elements[0];
      var options = select && select.selectedOptions ? select.selectedOptions : [];
      return options.length > 0;
    }
    var element = info.elements[0];
    if (typeof element.value === 'string') {
      return element.value.trim() !== '';
    }
    return Boolean(element.value);
  }

  function getOptionLabel(element, fallback) {
    var label = element.closest('label');
    if (label && label.childNodes.length > 0) {
      var clone = label.cloneNode(true);
      var inputs = clone.querySelectorAll('input');
      for (var i = inputs.length - 1; i >= 0; i -= 1) {
        inputs[i].remove();
      }
      var text = clone.textContent ? clone.textContent.trim() : '';
      return text || fallback;
    }
    if (element.tagName === 'OPTION') {
      return element.textContent.trim() || fallback;
    }
    return fallback;
  }

  function collectPayload(fields) {
    var rows = [];
    for (var i = 0; i < fields.length; i += 1) {
      var info = fields[i];
      if (!info.elements.length) continue;
      if (info.type === 'checkbox') {
        var values = [];
        for (var j = 0; j < info.elements.length; j += 1) {
          var checkbox = info.elements[j];
          if (!checkbox.checked) continue;
          values.push({
            label: getOptionLabel(checkbox, info.label),
            value: checkbox.value
          });
        }
        if (values.length) {
          rows.push({ label: info.label, name: info.name, value: values });
        }
        continue;
      }
      if (info.type === 'radio') {
        var selected = null;
        for (var k = 0; k < info.elements.length; k += 1) {
          if (info.elements[k].checked) {
            selected = info.elements[k];
            break;
          }
        }
        if (selected) {
          rows.push({
            label: info.label,
            name: info.name,
            value: {
              label: getOptionLabel(selected, info.label),
              value: selected.value
            }
          });
        }
        continue;
      }
      if (info.type === 'select-multiple') {
        var select = info.elements[0];
        var options = select && select.selectedOptions ? select.selectedOptions : [];
        var selectedValues = [];
        for (var m = 0; m < options.length; m += 1) {
          var option = options[m];
          selectedValues.push({
            label: getOptionLabel(option, option.value),
            value: option.value
          });
        }
        rows.push({ label: info.label, name: info.name, value: selectedValues });
        continue;
      }
      var element = info.elements[0];
      rows.push({ label: info.label, name: info.name, value: element.value });
    }
    return { form_info: rows };
  }

  function clearErrors(fields, errorClass) {
    for (var i = 0; i < fields.length; i += 1) {
      var info = fields[i];
      for (var j = 0; j < info.elements.length; j += 1) {
        var el = info.elements[j];
        el.classList.remove('error');
        el.removeAttribute('data-submit-error');
      }
      if (info.container) {
        info.container.classList.remove(errorClass);
      }
    }
  }

  function markErrors(fields, errorClass) {
    for (var i = 0; i < fields.length; i += 1) {
      var info = fields[i];
      for (var j = 0; j < info.elements.length; j += 1) {
        var el = info.elements[j];
        el.classList.add('error');
        el.setAttribute('data-submit-error', 'true');
      }
      if (info.container) {
        info.container.classList.add(errorClass);
      }
    }
  }

  function alertMissing(fields) {
    if (!fields.length) return;
    var labels = [];
    for (var i = 0; i < fields.length; i += 1) {
      labels.push(fields[i].label);
    }
    var message = labels.join(', ');
    var prefix = typeof CONFIG.validationMessagePrefix === 'string'
      ? CONFIG.validationMessagePrefix
      : 'Please fill all required fields: ';
    try {
      window.alert(prefix + message);
    } catch (_) {
      // ignore alert errors
    }
    var target = fields[0];
    if (target) {
      var focusable = target.elements[0];
      if (focusable && typeof focusable.focus === 'function') {
        focusable.focus({ preventScroll: false });
      }
      var container = target.container || focusable;
      if (container && typeof container.scrollIntoView === 'function') {
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }

  function setButtonState(button, text, disabled) {
    if (typeof text === 'string' && text.length) {
      button.textContent = text;
    }
    if (typeof disabled === 'boolean') {
      button.disabled = disabled;
      button.classList.toggle('submit-btn-disabled', disabled);
      button.classList.toggle('is-submit-disabled', disabled);
    }
  }

  function buildRequestPayload(fields) {
    var base = Object.assign({}, CONFIG.callbackParams || {});
    base.feedback_data = { user_collect_data: collectPayload(fields) };
    return base;
  }

  ready(function() {
    var button = document.querySelector(CONFIG.buttonSelector || 'button[type="submit"]');
    if (!button) return;
    var form = button.closest('form') || document.querySelector('form');
    if (!form) return;

    var errorClass = CONFIG.errorClass || 'field-error';

    var idleText = typeof CONFIG.idleText === 'string' ? CONFIG.idleText : button.textContent;
    var pendingText = CONFIG.pendingText || button.textContent;
    var successText = CONFIG.successText || button.textContent;
    var failureText = CONFIG.failureText || button.textContent;

    if (typeof CONFIG.idleText === 'string') {
      button.textContent = CONFIG.idleText;
    }

    function handle(event) {
      event.preventDefault();

      var fields = collectFieldInfo(form);

      clearErrors(fields, errorClass);

      var invalid = [];
      for (var i = 0; i < fields.length; i += 1) {
        var info = fields[i];
        if (info.required && !hasValue(info)) {
          invalid.push(info);
        }
      }

      if (invalid.length) {
        setButtonState(button, idleText, false);
        markErrors(invalid, errorClass);
        alertMissing(invalid);
        return;
      }

      setButtonState(button, pendingText, true);

      var payload = buildRequestPayload(fields);

      fetch(CONFIG.callbackUrl, {
        method: CONFIG.method,
        headers: CONFIG.headers,
        body: JSON.stringify(payload)
      })
        .then(function(response) {
          if (!response.ok) {
            throw new Error('Request failed with status ' + response.status);
          }
          var contentType = response.headers.get('content-type') || '';
          if (response.status === 204 || !contentType.includes('application/json')) {
            return null;
          }
          return response.json().catch(function() { return null; });
        })
        .then(function() {
          setButtonState(button, successText, true);
        })
        .catch(function(error) {
          console.error('[form-submit] request failed:', error);
          setButtonState(button, failureText, false);
        });
    }

    form.addEventListener('submit', handle);
    if (button.type !== 'submit') {
      button.addEventListener('click', handle);
    }
  });
})();
  `.trim();
}

function serializeConfig(config) {
  return JSON.stringify(config)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}
