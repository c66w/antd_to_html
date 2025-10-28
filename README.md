# antd-to-html

Convert Ant Design form JSON definitions into self-contained HTML markup. The tool reads a simplified Ant Design schema, maps known components to semantic HTML, applies layout rules, and emits a ready-to-use `<form>` document with an Ant Design–inspired visual theme.

## Quick start

1. Prepare a form schema (see [`examples/basic.json`](examples/basic.json) for a reference).
2. Run the converter:

   ```bash
   node src/cli.js examples/basic.json --title "注册表单" -o build/form.html
   ```

3. Open the generated HTML in your browser.

The default output includes a polished gradient background, card-like form container, and button/input styling that mirrors Ant Design. Pass `--no-styles` to strip the theme, or provide `--styles custom.css` to inject your own stylesheet.

### Run as an HTTP API

```bash
npm run serve
```

The service exposes a `POST /render-form` endpoint that expects the same Ant Design form JSON in the request body:

```http
POST /render-form
Content-Type: application/json

{
  "definition": {
    "id": "registration-form",
    "title": "注册账号",
    "items": [
      { "type": "input", "name": "username", "label": "用户名", "required": true },
      { "type": "password", "name": "password", "label": "密码", "required": true }
    ],
    "actions": [{ "label": "提交", "primary": true }]
  },
  "htmlOptions": {
    "title": "自定义标题",
    "includeStyles": true
  }
}
```

The response is a JSON payload containing the rendered HTML string:

```json
{
  "html": "<!DOCTYPE html>..."
}
```

Extras:

- `definition` can be omitted if you send the schema at the root level.
- `htmlOptions` is optional; any properties you previously passed to the CLI are supported.
- A lightweight CORS setup is enabled for convenience; adjust as needed before production.

### Docker (port 6422)

```bash
docker build -t antd-to-html .
docker run -d -p 6422:6422 --name antd-to-html antd-to-html
```

The container uses `PORT=6422` by default, so publishing `6422:6422` makes the API accessible from other hosts (e.g., `http://<server-ip>:6422/render-form`).

## Usage

```
node src/cli.js <input.json> [output.html]
```

- `input.json`: Path to a JSON file describing the Ant Design form.
- `output.html`: Optional path where the generated HTML should be written. If omitted, the HTML prints to stdout.

## Development Notes

The implementation is intentionally dependency-free. Core modules:

- `src/schema.js`: input validation helpers.
- `src/mappers.js`: maps Ant Design-like components to HTML snippets.
- `src/layout.js`: interprets grid/layout properties.
- `src/render.js`: assembles the final HTML document.
- `src/index.js`: public API for converting JSON to HTML.
- `src/cli.js`: command-line interface.

See `examples/basic.json` for a sample schema.

### Supported field types

- `input`, `password`, `textarea`, `number`, `date-picker`, `switch`
- `select`, `radio-group`, `checkbox-group`
- `form-list` (dynamic repeated group with add/remove handlers)
- `divider`

Each item supports common props such as `label`, `description`, `help`, `colSpan`, `className`, `controlClassName`, `placeholder`, `required`, `disabled`, and `htmlAttributes` for low-level overrides. The `form-list` item receives an `item` definition describing its inner field along with list-specific options (`addLabel`, `removeLabel`, `emptyText`, `startEmpty`, `min`, `max`).

### Form metadata

- `title` / `subtitle`: adds a typographic header above the form.
- `description`: used as a fallback subtitle when present.
- `form.className`: append additional classes to the `<form>` element.

These metadata fields work alongside the default theme so you can quickly produce branded previews.

### Submit callback

To embed an async submit workflow (disabled by default), add a `submit` object to the form definition. The generator will inline a lightweight script that gathers all field values, validates required inputs, merges your `callbackParams`, and posts them to `callbackUrl` as JSON.

```jsonc
{
  "actions": [
    {
      "label": "确认提交",
      "primary": true,
      "htmlAttributes": { "id": "submit-btn" }
    }
  ],
  "submit": {
    "callbackUrl": "https://api.example.com/form/submit",
    "callbackParams": { "operate_type": "task_execute" },
    "buttonSelector": "#submit-btn",
    "pendingText": "Submitting...",
    "successText": "Done",
    "failureText": "Retry",
    "validationMessagePrefix": "请填写所有必填项："
  }
}
```

By default the script targets `button[type="submit"]`; set `buttonSelector` (and give your button an `id` via `htmlAttributes`) if you need a different selector. The payload sent to `callbackUrl` looks like:

```jsonc
{
  "operate_type": "task_execute",
  "feedback_data": {
    "user_collect_data": {
      "form_info": [{ "label": "用户名", "name": "username", "value": "cooper" }]
    }
  }
}
```

Use `idleText`, `pendingText`, `successText`, and `failureText` to control the button copy across submit states. Custom headers (for example tokens) can be set through `submit.headers`.
