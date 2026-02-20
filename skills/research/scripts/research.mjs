#!/usr/bin/env node
/**
 * Research runner for OpenClaw.
 * - Queries Brave Search API (key is read from OpenClaw config)
 * - Synthesizes with Kimi K2.5 through the local Foundry MI proxy
 */

import fs from 'node:fs';

const OPENCLAW_CONFIG = process.env.OPENCLAW_CONFIG || '/home/desazure/.openclaw/openclaw.json';
const PROXY_BASE = process.env.FOUNDRY_PROXY_BASE || 'http://127.0.0.1:18791/v1';
const MODEL = process.env.FOUNDRY_MODEL || 'Kimi-K2.5';

function usage() {
  console.error('Usage: research.mjs "your query"');
  process.exit(2);
}

function loadConfig() {
  const raw = fs.readFileSync(OPENCLAW_CONFIG, 'utf8');
  return JSON.parse(raw);
}

function getBraveKey(cfg) {
  const k = cfg?.tools?.web?.search?.apiKey;
  if (!k) throw new Error('Missing Brave API key at tools.web.search.apiKey');
  return k;
}

async function braveSearch({ apiKey, q, count = 5 }) {
  const url = new URL('https://api.search.brave.com/res/v1/web/search');
  url.searchParams.set('q', q);
  url.searchParams.set('count', String(count));

  const r = await fetch(url, {
    headers: {
      Accept: 'application/json',
      'X-Subscription-Token': apiKey,
    },
  });

  const text = await r.text();
  if (!r.ok) throw new Error(`Brave search failed: ${r.status} ${text.slice(0, 300)}`);
  return JSON.parse(text);
}

function normalizeResults(braveJson) {
  const items = braveJson?.web?.results || [];
  return items.slice(0, 5).map((it) => ({
    title: it.title,
    url: it.url,
    description: it.description,
    age: it.age,
  }));
}

function buildPrompt(query, results) {
  return [
    'You are a research assistant.',
    'Use ONLY the sources provided below. Do not use outside knowledge.',
    '',
    'Output requirements:',
    '- Output MUST be Markdown bullet points only (each line starts with "- ").',
    '- No preface, no meta commentary (e.g., do not write "The user wants...").',
    '- Include inline citations as plain URLs in parentheses at the end of bullets.',
    '- If sources conflict or seem low-trust, include a bullet that says so.',
    '- Keep it to a ~4-minute skim (max ~12 bullets).',
    '',
    `Query: ${query}`,
    '',
    'Sources (use only these):',
    ...results.map((r, i) => `(${i + 1}) ${r.title}\n${r.url}\n${r.description || ''}`),
  ].join('\n');
}

function postProcess(out) {
  let s = String(out || '').trim();

  // Strip common meta lead-ins.
  s = s.replace(/^The user wants[\s\S]*?(?=\n\s*- )/i, '').trim();
  s = s.replace(/^I need to[\s\S]*?(?=\n\s*- )/i, '').trim();

  // Keep bullet lines only; normalize indentation.
  const blacklist = [
    'markdown bullet points only',
    'no preface',
    'no meta commentary',
    'include inline citations',
    'inline citations',
    'if sources conflict',
    'keep it to',
    'max ~',
    'output must be',
    'output requirements',
    'sources (use only these)',
    'let me check',
    'do they mention',
    'i will',
    'i need',
    'report what',
    'report that',
    'note that',
    'possibly',
  ];

  const rawLines = s
    .split(/\r?\n/)
    .map((l) => l.trimEnd())
    .filter((l) => l.trim().startsWith('- '))
    .map((l) => '- ' + l.trim().slice(2).trim())
    .filter((l) => {
      const low = l.toLowerCase();
      return !blacklist.some((b) => low.includes(b));
    });

  // De-dupe + cap (keep it skimmable).
  const seen = new Set();
  const lines = [];
  for (const l of rawLines) {
    const key = l.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    lines.push(l);
    if (lines.length >= 12) break;
  }

  return lines.join('\n').trim();
}

function applyCitations(text, results) {
  const urls = results.map((r) => r.url);
  // Replace (source 3) / (sources 1, 2, 3) etc with actual URLs.
  return text.replace(/\((sources?)\s+([0-9,\s]+)\)/gi, (_m, _s, nums) => {
    const ids = nums
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean)
      .map((x) => parseInt(x, 10))
      .filter((n) => Number.isFinite(n) && n >= 1 && n <= urls.length);
    const picked = [...new Set(ids)].map((n) => urls[n - 1]);
    if (!picked.length) return '';
    return '(' + picked.join(' ') + ')';
  });
}

async function kimiSynthesize({ query, results }) {
  const prompt = buildPrompt(query, results);

  const body = {
    model: MODEL,
    messages: [
      {
        role: 'system',
        content:
          'Answer in the normal content field. Do not include hidden reasoning. Follow the user instructions exactly.',
      },
      { role: 'user', content: prompt },
    ],
    max_tokens: 900,
    temperature: 0.2,
  };

  const r = await fetch(`${PROXY_BASE}/chat/completions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });

  const text = await r.text();
  if (!r.ok) throw new Error(`Kimi proxy failed: ${r.status} ${text.slice(0, 600)}`);

  const j = JSON.parse(text);
  const msg = j?.choices?.[0]?.message || {};
  const content = (msg.content ?? msg.reasoning_content ?? '').trim();
  const cleaned = postProcess(content);
  return applyCitations(cleaned, results);
}

async function main() {
  const q = process.argv.slice(2).join(' ').trim();
  if (!q) usage();

  const cfg = loadConfig();
  const braveKey = getBraveKey(cfg);

  const braveJson = await braveSearch({ apiKey: braveKey, q, count: 5 });
  const results = normalizeResults(braveJson);

  const out = await kimiSynthesize({ query: q, results });
  process.stdout.write(out + (out.endsWith('\n') ? '' : '\n'));
}

main().catch((e) => {
  console.error('ERROR:', e?.stack || String(e));
  process.exit(1);
});
