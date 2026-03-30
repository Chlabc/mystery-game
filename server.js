const http = require('http');
const fs = require('fs');
const path = require('path');
const { apiKey, port } = require('./config');

const ROOT = __dirname;
const DEFAULT_FILE = 'lab_breakout_integrated (7).html';
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MAX_BODY_SIZE = 1024 * 1024;

const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(payload));
}

function sendText(res, statusCode, message) {
  res.writeHead(statusCode, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end(message);
}

function safePathname(urlPathname) {
  const decoded = decodeURIComponent(urlPathname);
  const relativePath = decoded === '/' ? `/${DEFAULT_FILE}` : decoded;
  const normalized = path.normalize(relativePath).replace(/^(\.\.[/\\])+/, '');
  const resolved = path.resolve(ROOT, `.${normalized}`);
  if (!resolved.startsWith(ROOT)) return null;
  return resolved;
}

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let total = 0;
    const chunks = [];

    req.on('data', (chunk) => {
      total += chunk.length;
      if (total > MAX_BODY_SIZE) {
        reject(new Error('Request body too large.'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      try {
        const body = chunks.length ? Buffer.concat(chunks).toString('utf8') : '{}';
        resolve(JSON.parse(body));
      } catch {
        reject(new Error('Invalid JSON body.'));
      }
    });

    req.on('error', reject);
  });
}

async function handleGroqChat(req, res) {
  if (!apiKey) {
    sendJson(res, 500, { error: 'GROQ_API_KEY is not configured on the server.' });
    return;
  }

  let payload;
  try {
    payload = await readRequestBody(req);
  } catch (error) {
    sendJson(res, 400, { error: error.message });
    return;
  }

  if (!Array.isArray(payload.messages) || payload.messages.length === 0) {
    sendJson(res, 400, { error: 'A non-empty messages array is required.' });
    return;
  }

  try {
    const upstream = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: payload.model || 'llama-3.3-70b-versatile',
        messages: payload.messages,
        max_tokens: payload.maxTokens ?? 180,
        temperature: payload.temperature ?? 0.8,
      }),
    });

    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      sendJson(res, upstream.status, {
        error: data?.error?.message || `Groq request failed with status ${upstream.status}.`,
      });
      return;
    }

    const content = data?.choices?.[0]?.message?.content?.trim();
    if (!content) {
      sendJson(res, 502, { error: 'Groq returned an empty response.' });
      return;
    }

    sendJson(res, 200, { content });
  } catch (error) {
    sendJson(res, 502, { error: error.message || 'Unable to reach Groq.' });
  }
}

function handleStaticFile(req, res) {
  const filePath = safePathname(new URL(req.url, `http://${req.headers.host}`).pathname);
  if (!filePath) {
    sendText(res, 403, 'Forbidden');
    return;
  }

  fs.stat(filePath, (statError, stats) => {
    if (statError || !stats.isFile()) {
      sendText(res, 404, 'Not found');
      return;
    }

    const extension = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[extension] || 'application/octet-stream';

    res.writeHead(200, { 'Content-Type': contentType });
    if (req.method === 'HEAD') {
      res.end();
      return;
    }

    fs.createReadStream(filePath).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const requestUrl = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'GET' && requestUrl.pathname === '/api/status') {
    sendJson(res, 200, { hasGroqKey: Boolean(apiKey) });
    return;
  }

  if (req.method === 'POST' && requestUrl.pathname === '/api/chat') {
    void handleGroqChat(req, res);
    return;
  }

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    sendText(res, 405, 'Method not allowed');
    return;
  }

  handleStaticFile(req, res);
});

server.listen(port, () => {
  console.log(`Mystery Game server running at http://localhost:${port}`);
});
