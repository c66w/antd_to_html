import { escapeHtml } from '../utils.js';

export function renderFormList(item, renderField) {
  const fieldConfig = item.item || {};
  const childControl = renderField(fieldConfig);
  const childLabel = fieldConfig.label
    ? `<div class="form-list-item-label">${escapeHtml(fieldConfig.label)}</div>`
    : '';
  const childDescription = fieldConfig.description
    ? `<div class="form-list-item-description">${escapeHtml(fieldConfig.description)}</div>`
    : '';
  const childHelp = fieldConfig.help
    ? `<div class="form-list-item-help">${escapeHtml(fieldConfig.help)}</div>`
    : '';
  const startEmpty = Boolean(item.startEmpty);
  const minDefined = getNumber(item.min);
  const minItems = minDefined ?? (startEmpty ? 0 : 1);
  const maxItems = getNumber(item.max) ?? Infinity;
  const minAttr = Number.isFinite(minItems) ? minItems : '';
  const maxAttr = Number.isFinite(maxItems) ? maxItems : '';
  const addLabel = escapeHtml(item.addLabel || 'Add');
  const removeLabel = escapeHtml(item.removeLabel || 'Remove');
  const emptyText = item.emptyText
    ? `<div class="form-list-empty" data-empty>${escapeHtml(item.emptyText)}</div>`
    : '';
  const listItemContent = `
    ${childLabel}
    ${childControl}
    ${childDescription}
    ${childHelp}
  `.trim();

  const initialItems = startEmpty ? '' : `<div class="form-list-item">${listItemContent}<button type="button" class="list-remove" data-action="remove">${removeLabel}</button></div>`;

  const template = `
<template id="${escapeHtml(item.name)}-template">
  <div class="form-list-item">
    ${listItemContent}
    <button type="button" class="list-remove" data-action="remove">${removeLabel}</button>
  </div>
</template>
`.trim();

  return `
<div class="form-list" data-name="${escapeHtml(item.name || '')}">
  <div class="form-list-items" data-min="${minAttr}" data-max="${maxAttr}">
    ${initialItems}
  </div>
  ${emptyText}
  <div class="form-list-actions">
    <button type="button" class="list-add" data-action="add">${addLabel}</button>
  </div>
  ${template}
</div>
  `.trim();
}

function getNumber(value) {
  return typeof value === 'number' ? value : null;
}
