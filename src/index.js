import { validateFormDefinition } from './schema.js';
import { mapFormToHtml } from './render.js';

export function convertAntdFormToHtml(definition, options = {}) {
  const { onError, ...restOptions } = options;
  const errors = validateFormDefinition(definition);

  if (errors.length > 0) {
    if (typeof onError === 'function') {
      onError(errors);
    }
    const error = new Error('Form definition failed validation.');
    error.details = errors;
    throw error;
  }

  return mapFormToHtml(definition, restOptions);
}

export default convertAntdFormToHtml;
