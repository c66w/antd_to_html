import { escapeHtml, attributesToString, normalizeArray } from './utils.js';
import { renderFormList } from './renderers/formList.js';

const typeRenderers = {
  input: renderTextInput,
  textarea: renderTextArea,
  password: renderPassword,
  number: renderNumber,
  select: renderSelect,
  'radio-group': renderRadioGroup,
  'checkbox-group': renderCheckboxGroup,
  switch: renderSwitch,
  'date-picker': renderDatePicker,
  divider: () => '<hr class="form-divider" />',
  'form-list': (item, renderField) => renderFormList(item, renderField)
};

export function renderField(item) {
  const renderer = typeRenderers[item.type];
  if (!renderer) {
    return `<div><!-- Unsupported field type: ${escapeHtml(item.type || 'unknown')} --></div>`;
  }
  return renderer(item, renderField);
}

function renderTextInput(item) {
  const attrs = controlAttributes(item, {
    type: 'text',
    value: defaultValue(item)
  });
  return `<input ${attrs} />`;
}

function renderTextArea(item) {
  const attrs = controlAttributes(item, {
    rows: item.rows || 4
  });
  const value = defaultValue(item);
  return `<textarea ${attrs}>${escapeHtml(value ?? '')}</textarea>`;
}

function renderPassword(item) {
  const attrs = controlAttributes(item, {
    type: 'password',
    value: defaultValue(item)
  });
  return `<input ${attrs} />`;
}

function renderNumber(item) {
  const attrs = controlAttributes(item, {
    type: 'number',
    min: numberOrNull(item.min),
    max: numberOrNull(item.max),
    step: numberOrNull(item.step),
    value: defaultValue(item)
  });
  return `<input ${attrs} />`;
}

function renderSelect(item) {
  const values = valueSet(defaultValue(item));
  const attrs = controlAttributes(item, {
    multiple: item.mode === 'multiple' || item.multiple || undefined
  });
  const options = (item.options || []).map(option => {
    const value = option.value ?? option.key ?? option.label ?? '';
    const label = option.label ?? option.value ?? '';
    const optionAttrs = attributesToString({
      value,
      selected: values.has(value)
    });
    return `<option ${optionAttrs}>${escapeHtml(label)}</option>`;
  });

  return `<select ${attrs}>\n  ${options.join('\n  ')}\n</select>`;
}

function renderRadioGroup(item) {
  const value = defaultValue(item);
  const groupName = item.name || '';
  const options = (item.options || []).map((option, index) => {
    const optionValue = option.value ?? option.key ?? option.label ?? '';
    const id = option.id || `${groupName}-${index}`;
    const attrs = attributesToString({
      type: 'radio',
      id,
      name: groupName,
      value: optionValue,
      checked: option.checked || optionValue === value,
      disabled: option.disabled
    });
    return `<label for="${escapeHtml(id)}"><input ${attrs} /> ${escapeHtml(option.label ?? optionValue)}</label>`;
  });

  const classes = ['radio-group', item.controlClassName || ''].filter(Boolean).join(' ');
  return `<div class="${classes}">${options.join('')}</div>`;
}

function renderCheckboxGroup(item) {
  const values = valueSet(defaultValue(item));
  const groupName = item.name || '';
  const options = (item.options || []).map((option, index) => {
    const optionValue = option.value ?? option.key ?? option.label ?? '';
    const id = option.id || `${groupName}-${index}`;
    const attrs = attributesToString({
      type: 'checkbox',
      id,
      name: groupName,
      value: optionValue,
      checked: option.checked || values.has(optionValue),
      disabled: option.disabled
    });
    return `<label for="${escapeHtml(id)}"><input ${attrs} /> ${escapeHtml(option.label ?? optionValue)}</label>`;
  });

  const classes = ['checkbox-group', item.controlClassName || ''].filter(Boolean).join(' ');
  return `<div class="${classes}">${options.join('')}</div>`;
}

function renderSwitch(item) {
  const attrs = {
    type: 'checkbox',
    id: item.id || item.name || undefined,
    name: item.name || undefined,
    checked: item.checked ?? Boolean(defaultValue(item)),
    required: item.required,
    disabled: item.disabled,
    readonly: item.readOnly ?? item.readonly
  };

  if (item.htmlAttributes && typeof item.htmlAttributes === 'object') {
    Object.assign(attrs, item.htmlAttributes);
  }

  return `
<label class="switch">
  <input ${attributesToString(attrs)} />
  <span class="slider"></span>
</label>
  `.trim();
}

function renderDatePicker(item) {
  const attrs = controlAttributes(item, {
    type: item.showTime ? 'datetime-local' : 'date',
    value: defaultValue(item)
  });
  return `<input ${attrs} />`;
}

function controlAttributes(item, extra = {}) {
  const attrs = {
    id: item.id || item.name || undefined,
    name: item.name || undefined,
    placeholder: item.placeholder,
    required: item.required,
    disabled: item.disabled,
    readonly: item.readOnly ?? item.readonly,
    ...extra
  };

  if (item.controlClassName) {
    attrs.class = attrs.class
      ? `${attrs.class} ${item.controlClassName}`
      : item.controlClassName;
  }

  if (item.htmlAttributes && typeof item.htmlAttributes === 'object') {
    Object.assign(attrs, item.htmlAttributes);
  }

  return attributesToString(attrs);
}

function defaultValue(item) {
  if (item.defaultValue !== undefined) return item.defaultValue;
  if (item.initialValue !== undefined) return item.initialValue;
  if (item.value !== undefined) return item.value;
  return undefined;
}

function numberOrNull(value) {
  return typeof value === 'number' ? value : null;
}

function valueSet(value) {
  return new Set(normalizeArray(value));
}
