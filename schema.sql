CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION generate_short_id(len integer DEFAULT 9)
RETURNS text AS $$
DECLARE
  chars text := 'abcdefghijklmnopqrstuvwxyz0123456789';
  result text := '';
BEGIN
  IF len <= 0 THEN
    RETURN result;
  END IF;
  FOR i IN 1..len LOOP
    result := result || substr(chars, 1 + floor(random() * length(chars))::int, 1);
  END LOOP;
  RETURN result;
END;
$$ LANGUAGE plpgsql VOLATILE;

CREATE TABLE IF NOT EXISTS form_templates (
  id           TEXT PRIMARY KEY DEFAULT generate_short_id(9),
  slug         TEXT UNIQUE,
  title        TEXT NOT NULL,
  description  TEXT,
  theme        TEXT,
  definition   JSONB NOT NULL,
  html_options JSONB NOT NULL DEFAULT '{}'::jsonb,
  version      INTEGER NOT NULL DEFAULT 1,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS form_instances (
  id             TEXT PRIMARY KEY DEFAULT generate_short_id(9),
  template_id    TEXT NOT NULL REFERENCES form_templates(id),
  name           TEXT,
  runtime_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS form_submissions (
  id             TEXT PRIMARY KEY DEFAULT generate_short_id(12),
  instance_id    TEXT NOT NULL REFERENCES form_instances(id) ON DELETE CASCADE,
  submitted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload        JSONB NOT NULL,
  status         TEXT NOT NULL DEFAULT 'draft',
  callback_status TEXT NOT NULL DEFAULT 'idle',
  callback_info  JSONB,
  CONSTRAINT form_submissions_instance_unique UNIQUE (instance_id)
);

CREATE INDEX IF NOT EXISTS idx_form_templates_slug ON form_templates(slug);
CREATE INDEX IF NOT EXISTS idx_form_instances_template ON form_instances(template_id);
CREATE INDEX IF NOT EXISTS idx_form_submissions_instance ON form_submissions(instance_id);
