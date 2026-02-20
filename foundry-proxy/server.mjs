import http from 'node:http';

const HOST = process.env.FOUNDRY_PROXY_HOST || '127.0.0.1';
const PORT = Number(process.env.FOUNDRY_PROXY_PORT || '18791');

const FOUNDRY_BASE_URL = process.env.FOUNDRY_BASE_URL || 'https://pitchbook-resource.openai.azure.com/openai/v1';
const IMDS_RESOURCE = process.env.IMDS_RESOURCE || 'https://cognitiveservices.azure.com/';

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
  });
  res.end(body);
}

async function getManagedIdentityToken() {
  const resource = encodeURIComponent(IMDS_RESOURCE);
  const url = `http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=${resource}`;
  const r = await fetch(url, { headers: { Metadata: 'true' } });
  if (!r.ok) {
    const text = await r.text().catch(() => '');
    throw new Error(`IMDS token fetch failed: ${r.status} ${text.slice(0, 200)}`);
  }
  const j = await r.json();
  if (!j.access_token) throw new Error('IMDS token missing access_token');
  return j.access_token;
}

async function readBody(req) {
  return await new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

/**
 * Strip provider prefix from model ID.
 * OpenClaw uses "provider/model" internally (e.g. "foundry/Kimi-K2.5")
 * but Azure Foundry expects bare model IDs (e.g. "Kimi-K2.5").
 */
function stripModelPrefix(bodyBuf) {
  try {
    const parsed = JSON.parse(bodyBuf.toString('utf8'));
    if (typeof parsed.model === 'string' && parsed.model.includes('/')) {
      parsed.model = parsed.model.split('/').pop();
      return Buffer.from(JSON.stringify(parsed));
    }
  } catch { /* not JSON or no model field — forward as-is */ }
  return bodyBuf;
}

function normalizeChatCompletion(respJson) {
  try {
    const choice = respJson?.choices?.[0];
    const msg = choice?.message;
    if (msg && (msg.content === null || msg.content === undefined) && msg.reasoning_content) {
      msg.content = msg.reasoning_content;
    }
    return respJson;
  } catch {
    return respJson;
  }
}

const server = http.createServer(async (req, res) => {
  // Simple health check
  if (req.method === 'GET' && (req.url === '/' || req.url === '/healthz')) {
    return sendJson(res, 200, { ok: true, service: 'foundry-proxy' });
  }

  // Only proxy OpenAI-compatible chat completions.
  if (req.method !== 'POST' || !req.url) {
    return sendJson(res, 404, { error: 'not_found' });
  }

  const allowedPaths = new Set(['/v1/chat/completions', '/chat/completions']);
  const path = req.url.split('?')[0];
  if (!allowedPaths.has(path)) {
    return sendJson(res, 404, { error: 'not_found' });
  }

  try {
    const bodyBuf = await readBody(req);
    const forwardBody = stripModelPrefix(bodyBuf);
    const token = await getManagedIdentityToken();

    const upstreamUrl = `${FOUNDRY_BASE_URL}${path.startsWith('/v1') ? path.slice(3) : path}`;

    const upstream = await fetch(upstreamUrl, {
      method: 'POST',
      headers: {
        'authorization': `Bearer ${token}`,
        'content-type': 'application/json',
      },
      body: forwardBody,
    });

    const text = await upstream.text();
    let out = text;
    let contentType = upstream.headers.get('content-type') || 'application/json';

    if (contentType.includes('application/json')) {
      try {
        const j = normalizeChatCompletion(JSON.parse(text));
        out = JSON.stringify(j);
      } catch {
        // fall back to original text
      }
    }

    res.writeHead(upstream.status, {
      'content-type': contentType,
      'content-length': Buffer.byteLength(out),
    });
    res.end(out);
  } catch (e) {
    return sendJson(res, 500, { error: 'proxy_error', message: String(e?.message || e) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`foundry-proxy listening on http://${HOST}:${PORT}`);
  console.log(`upstream: ${FOUNDRY_BASE_URL}`);
  console.log(`imds resource: ${IMDS_RESOURCE}`);
});
