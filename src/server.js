import http from 'node:http';
import { URL } from 'node:url';
import process from 'node:process';

import { convertAntdFormToHtml } from './index.js';

const PORT = Number.parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';
const MAX_BODY_SIZE = 1024 * 1024; // 1MB

const server = http.createServer(async (req, res) => {
  const origin = req.headers.origin || '*';
  setCorsHeaders(res, origin);

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  let pathname = '/';
  try {
    // Use the incoming Host header when available, otherwise fall back to HOST:PORT.
    const fallbackHost = `${HOST}:${PORT}`;
    const url = new URL(req.url || '/', `http://${req.headers.host || fallbackHost}`);
    pathname = url.pathname;
  } catch (error) {
    respondJson(res, 400, { error: 'Invalid request URL.' });
    return;
  }

  if (req.method === 'GET' && pathname === '/health') {
    respondJson(res, 200, { status: 'ok' });
    return;
  }

  if (req.method !== 'POST' || pathname !== '/render-form') {
    respondJson(res, 404, { error: 'Route not found.' });
    return;
  }

  try {
    const body = await readJsonBody(req);
    const html = convertAntdFormToHtml(body.definition || body, {
      html: body.htmlOptions
    });
    respondJson(res, 200, { html });
  } catch (error) {
    if (error.type === 'entity.too.large') {
      respondJson(res, 413, { error: 'Request body exceeds limit (1MB).' });
      return;
    }

    if (error.type === 'invalid_json') {
      respondJson(res, 400, { error: 'Request body must be valid JSON.' });
      return;
    }

    if (Array.isArray(error.details)) {
      respondJson(res, 422, { error: error.message, details: error.details });
      return;
    }

    console.error('[render-form] unexpected error:', error);
    respondJson(res, 500, { error: 'Internal server error.' });
  }
});

server.listen(PORT, () => {
  console.log(`antd-to-html API listening on http://${HOST}:${PORT}`);
});

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;

    req.on('data', chunk => {
      total += chunk.length;
      if (total > MAX_BODY_SIZE) {
        reject({ type: 'entity.too.large' });
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      try {
        const raw = Buffer.concat(chunks).toString('utf8');
        const parsed = raw ? JSON.parse(raw) : {};
        resolve(parsed);
      } catch {
        reject({ type: 'invalid_json' });
      }
    });

    req.on('error', err => reject(err));
  });
}

function respondJson(res, statusCode, payload) {
  if (!res.headersSent) {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
  }
  res.writeHead(statusCode);
  res.end(JSON.stringify(payload));
}

function setCorsHeaders(res, origin) {
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Max-Age', '86400');
}
