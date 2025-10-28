import { buildLayoutContext, renderItemWithLayout } from './layout.js';
import { renderField } from './mappers.js';
import { buildSubmitScript } from './scripts/submit.js';
import { escapeHtml, attributesToString } from './utils.js';

const DEFAULT_HTML_OPTIONS = Object.freeze({
  title: 'Generated Form',
  includeStyles: true,
  styles: null
});

const BASE_STYLES = `
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
a {
  color: var(--primary-color);
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
.form-header {
  margin-bottom: 32px;
}
.form-title {
  margin: 0 0 12px;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-color);
}
.form-subtitle {
  margin: 0;
  font-size: 16px;
  color: var(--text-secondary);
}
.form-row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -12px 24px;
}
.form-col {
  padding: 0 12px;
  box-sizing: border-box;
}
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
.form-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  text-transform: none;
}
.required-asterisk {
  color: var(--danger-color);
  font-size: 16px;
  margin-left: 4px;
}
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
input:disabled,
select:disabled,
textarea:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
}
textarea {
  resize: vertical;
  min-height: 120px;
}
::placeholder {
  color: var(--text-tertiary);
}
.form-description {
  color: var(--text-secondary);
  font-size: 14px;
}
.form-help {
  color: var(--text-tertiary);
  font-size: 13px;
}
.form-extra {
  color: var(--text-tertiary);
  font-size: 13px;
}
.radio-group,
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.radio-group label,
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: var(--text-secondary);
  cursor: pointer;
}
.radio-group input,
.checkbox-group input {
  width: auto;
  accent-color: var(--primary-color);
}
.form-divider {
  border: none;
  border-bottom: 1px dashed rgba(22, 119, 255, 0.3);
  margin: 32px 0;
}
.switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 54px;
  height: 28px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.switch .slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s ease;
  border-radius: 28px;
}
.switch .slider::before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s ease;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.switch input:checked + .slider {
  background-color: var(--primary-color);
}
.switch input:checked + .slider::before {
  transform: translateX(26px);
}
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}
button {
  font-family: inherit;
  font-size: 15px;
  line-height: 1;
  border-radius: 10px;
  padding: 12px 20px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
  background-color: #fff;
  color: var(--text-color);
  border-color: var(--border-color);
}
button:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px -18px var(--shadow-color);
}
button:active {
  transform: translateY(0);
  box-shadow: none;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.primary-button {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: #fff;
  border: none;
  box-shadow: 0 18px 30px -20px rgba(9, 88, 217, 0.7);
}
.primary-button:hover {
  background: linear-gradient(135deg, var(--primary-hover), var(--primary-color));
}
.secondary-button {
  background: #fff;
  color: var(--primary-color);
  border-color: rgba(22, 119, 255, 0.4);
}
.secondary-button:hover {
  background: var(--primary-light);
}
.form-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-list-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-list-item {
  border: 1px dashed rgba(22, 119, 255, 0.4);
  border-radius: 12px;
  padding: 18px 20px;
  background: rgba(22, 119, 255, 0.04);
  position: relative;
}
.form-list-item-label {
  font-weight: 600;
  color: var(--text-color);
}
.form-list-item-description {
  color: var(--text-secondary);
  font-size: 13px;
}
.form-list-item-help {
  color: var(--text-tertiary);
  font-size: 12px;
}
.form-list-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
  padding: 14px;
  border: 1px dashed rgba(22, 119, 255, 0.35);
  border-radius: 12px;
  background: rgba(22, 119, 255, 0.06);
}
.list-add,
.list-remove {
  border-style: dashed;
  border-width: 1px;
  padding: 10px 16px;
  font-size: 14px;
}
.list-add {
  color: var(--primary-color);
  border-color: rgba(22, 119, 255, 0.4);
  background: rgba(22, 119, 255, 0.08);
}
.list-add:hover {
  background: rgba(22, 119, 255, 0.15);
}
.list-remove {
  color: var(--danger-color);
  border-color: rgba(255, 77, 79, 0.4);
  background: rgba(255, 77, 79, 0.08);
}
.list-remove:hover {
  background: rgba(255, 77, 79, 0.16);
}
@media (max-width: 900px) {
  .generated-form {
    padding: 32px 28px;
  }
}
@media (max-width: 768px) {
  body {
    padding: 32px 12px;
  }
  .form-row {
    flex-direction: column;
    margin: 0 0 20px;
  }
  .form-col {
    padding: 0 !important;
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }
  .form-item {
    padding: 16px 18px;
  }
  .form-actions {
    justify-content: stretch;
  }
  .form-actions button {
    flex: 1;
  }
}
`.trim();

export function mapFormToHtml(definition, options = {}) {
  const htmlOptions = { ...DEFAULT_HTML_OPTIONS, ...options.html };
  const pageTitle =
    htmlOptions.title ||
    definition.title ||
    definition.form?.title ||
    DEFAULT_HTML_OPTIONS.title;
  const layoutCtx = buildLayoutContext(definition.form || {});
  const renderedItems = (definition.items || []).map(item =>
    renderItemWithLayout(item, layoutCtx, renderField)
  );
  const hasFormList = containsFormList(definition.items || []);
  const header = renderFormHeader(definition);

  const actions = Array.isArray(definition.actions)
    ? definition.actions.map(renderActionButton).join('\n')
    : defaultActions();

  const formClasses = [
    'generated-form',
    definition.form?.className || null,
    definition.form?.layout ? `layout-${definition.form.layout}` : null
  ]
    .filter(Boolean)
    .join(' ');

  const formAttrs = attributesToString({
    id: definition.id || null,
    class: formClasses || null,
    action: definition.action || '#',
    method: definition.method || 'post',
    novalidate: definition.novalidate ? 'novalidate' : null
  });
  const formAttributeString = formAttrs ? ` ${formAttrs}` : '';
  const scripts = [];

  if (hasFormList) {
    scripts.push(FORM_LIST_SCRIPT);
  }

  if (definition.submit) {
    scripts.push(buildSubmitScript(definition.submit));
  }

  const scriptBlock = scripts.length > 0
    ? scripts.map(script => `<script>\n${script}\n</script>`).join('\n')
    : '';

  const doc = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(pageTitle)}</title>
  ${htmlOptions.includeStyles ? `<style>\n${htmlOptions.styles || BASE_STYLES}\n</style>` : ''}
</head>
<body>
  <div class="form-container">
    <form${formAttributeString}>
      ${header}
      ${renderedItems.join('\n')}
      <div class="form-actions">
        ${actions}
      </div>
    </form>
  </div>
  ${scriptBlock}
</body>
</html>
`.trim();

  return doc;
}

function renderActionButton(action) {
  const type = action.htmlType || (action.primary ? 'submit' : 'button');
  const classNames = [];
  if (action.primary) {
    classNames.push('primary-button');
  } else if (!action.className) {
    classNames.push('secondary-button');
  }
  if (action.className) {
    classNames.push(action.className);
  }
  const attrObject = {
    type,
    class: classNames.join(' ') || null
  };

  if (action.htmlAttributes && typeof action.htmlAttributes === 'object') {
    Object.assign(attrObject, action.htmlAttributes);
  }

  const attrs = attributesToString(attrObject);

  return `<button ${attrs}>${escapeHtml(action.label || 'Submit')}</button>`;
}

function defaultActions() {
  return [
    '<button type="submit" class="primary-button">Submit</button>',
    '<button type="reset" class="secondary-button">Reset</button>'
  ].join('\n');
}

function renderFormHeader(definition) {
  const title = definition.title || definition.form?.title;
  const subtitle =
    definition.subtitle ||
    definition.form?.subtitle ||
    definition.description ||
    definition.form?.description;

  if (!title && !subtitle) {
    return '';
  }

  const titleMarkup = title ? `<h1 class="form-title">${escapeHtml(title)}</h1>` : '';
  const subtitleMarkup = subtitle
    ? `<p class="form-subtitle">${escapeHtml(subtitle)}</p>`
    : '';

  return `<header class="form-header">${titleMarkup}${subtitleMarkup}</header>`;
}

function containsFormList(items) {
  for (const item of items) {
    if (item?.type === 'form-list') {
      return true;
    }
    if (Array.isArray(item?.items) && containsFormList(item.items)) {
      return true;
    }
    if (item?.item && containsFormList([item.item])) {
      return true;
    }
  }
  return false;
}

const FORM_LIST_SCRIPT = `
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
          if (!baseName || !base || preserve) {
            return;
          }
          if (base.includes('[') || base.includes(']')) {
            return;
          }
          control.name = baseName + '[' + index + '].' + base;
          const sanitized = base
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
          if (control.id) {
            control.id = baseName + '-' + index + '-' + sanitized;
          }
        });
      });
    };

    refresh();

    list.addEventListener('click', event => {
      const action = event.target.dataset.action;
      if (action === 'add') {
        if (itemsContainer.querySelectorAll('.form-list-item').length >= max) {
          return;
        }
        const prototype = template.content.firstElementChild;
        if (!prototype) return;
        const clone = prototype.cloneNode(true);
        itemsContainer.appendChild(clone);
        refresh();
      }
      if (action === 'remove') {
        const item = event.target.closest('.form-list-item');
        if (!item) return;
        if (itemsContainer.querySelectorAll('.form-list-item').length <= min) {
          return;
        }
        item.remove();
        refresh();
      }
    });
  });
});
`.trim();
