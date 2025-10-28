const SUPPORTED_FIELD_TYPES = new Set([
  'input',
  'textarea',
  'password',
  'number',
  'select',
  'radio-group',
  'checkbox-group',
  'switch',
  'date-picker',
  'form-list',
  'divider'
]);

const TYPES_REQUIRING_OPTIONS = new Set(['select', 'radio-group', 'checkbox-group']);
const TYPES_REQUIRING_NAME = new Set([
  'input',
  'textarea',
  'password',
  'number',
  'select',
  'radio-group',
  'checkbox-group',
  'switch',
  'date-picker',
  'form-list'
]);

export function validateFormDefinition(definition) {
  const errors = [];

  if (typeof definition !== 'object' || definition === null) {
    return ['Form definition must be an object.'];
  }

  if (!Array.isArray(definition.items)) {
    errors.push('Form definition must include an "items" array.');
  } else {
    definition.items.forEach((item, index) => {
      validateFormItem(item, `items[${index}]`, errors);
    });
  }

  if (definition.submit !== undefined) {
    validateSubmitConfig(definition.submit, errors);
  }

  return errors;
}

function validateFormItem(item, path, errors) {
  if (typeof item !== 'object' || item === null) {
    errors.push(`${path} must be an object.`);
    return;
  }

  if (!item.type || !SUPPORTED_FIELD_TYPES.has(item.type)) {
    errors.push(`${path}.type must be one of: ${Array.from(SUPPORTED_FIELD_TYPES).join(', ')}.`);
  }

  if (TYPES_REQUIRING_NAME.has(item.type) && typeof item.name !== 'string') {
    errors.push(`${path}.name is required for type "${item.type}".`);
  }

  if (TYPES_REQUIRING_OPTIONS.has(item.type) && !Array.isArray(item.options)) {
    errors.push(`${path}.options must be an array for type "${item.type}".`);
  }

  if (item.type === 'form-list') {
    if (!item.item) {
      errors.push(`${path}.item is required for form-list.`);
    } else {
      validateFormItem(item.item, `${path}.item`, errors);
    }
  }
}

function validateSubmitConfig(submit, errors) {
  if (typeof submit !== 'object' || submit === null || Array.isArray(submit)) {
    errors.push('submit must be an object when provided.');
    return;
  }

  if (typeof submit.callbackUrl !== 'string' || submit.callbackUrl.trim() === '') {
    errors.push('submit.callbackUrl must be a non-empty string.');
  }

  if ('callbackParams' in submit && !isPlainObject(submit.callbackParams)) {
    errors.push('submit.callbackParams must be an object when provided.');
  }

  if ('method' in submit && !isHttpMethod(submit.method)) {
    errors.push('submit.method must be one of: POST, PUT, PATCH, DELETE.');
  }

  const stringFields = [
    'buttonSelector',
    'idleText',
    'pendingText',
    'successText',
    'failureText',
    'errorClass',
    'validationMessagePrefix'
  ];

  stringFields.forEach(field => {
    if (field in submit && typeof submit[field] !== 'string') {
      errors.push(`submit.${field} must be a string when provided.`);
    }
  });

  if ('headers' in submit && !isPlainObject(submit.headers)) {
    errors.push('submit.headers must be an object whose values are strings.');
  } else if (submit.headers) {
    Object.entries(submit.headers).forEach(([key, value]) => {
      if (typeof value !== 'string') {
        errors.push(`submit.headers[${key}] must be a string.`);
      }
    });
  }
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isHttpMethod(value) {
  if (typeof value !== 'string') return false;
  const upper = value.toUpperCase();
  return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(upper);
}
