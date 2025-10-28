const DEFAULT_SPAN = 24;

export function buildLayoutContext(formOptions) {
  const labelCol = formOptions.labelCol || { span: 8 };
  const wrapperCol = formOptions.wrapperCol || { span: 16 };
  const gutter = typeof formOptions.gutter === 'number' ? formOptions.gutter : 24;

  return {
    labelCol,
    wrapperCol,
    gutter,
    formOptions
  };
}

export function renderItemWithLayout(item, layoutCtx, renderField) {
  if (item.hidden) {
    return '';
  }

  if (item.type === 'divider') {
    return '<hr class="form-divider" />';
  }

  const colSpan = getSpan(item.colSpan ?? item.span, DEFAULT_SPAN);
  const widthPercentage = (colSpan / DEFAULT_SPAN) * 100;
  const colStyle = [
    `flex: 0 0 ${widthPercentage}%`,
    `max-width: ${widthPercentage}%`,
    item.style ? inlineStyleString(item.style) : null
  ]
    .filter(Boolean)
    .join('; ');

  const label = renderLabel(item, layoutCtx.labelCol);
  const control = renderField(item);
  const description = item.description ? `<div class="form-description">${escapeHtml(item.description)}</div>` : '';
  const help = item.help ? `<div class="form-help">${escapeHtml(item.help)}</div>` : '';
  const extra = item.extra ? `<div class="form-extra">${escapeHtml(item.extra)}</div>` : '';
  const rowClass = ['form-row', item.rowClassName || ''].filter(Boolean).join(' ');
  const colClass = ['form-col', item.colClassName || ''].filter(Boolean).join(' ');
  const itemClass = ['form-item', item.className || ''].filter(Boolean).join(' ');

  return `
<div class="${rowClass}">
  <div class="${colClass}" style="${colStyle}">
    <div class="${itemClass}">
      ${label}
      ${control}
      ${description}
      ${help}
      ${extra}
    </div>
  </div>
</div>
  `.trim();
}

function renderLabel(item, labelCol) {
  if (!item.label) {
    return '';
  }
  const required = item.required ? '<span class="required-asterisk">*</span>' : '';
  return `<label class="form-label" for="${escapeHtml(item.name || '')}">${escapeHtml(item.label)}${required}</label>`;
}

function getSpan(input, fallback) {
  if (typeof input === 'number' && input > 0) {
    return Math.min(input, DEFAULT_SPAN);
  }
  return fallback;
}

function inlineStyleString(styleObject) {
  return Object.entries(styleObject)
    .map(([key, value]) => `${toKebabCase(key)}:${value}`)
    .join(';');
}

function toKebabCase(str) {
  return str.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
