#!/usr/bin/env node
/**
 * WIP standalone research runner.
 * - Queries Brave Search API
 * - Sends results to local Foundry MI proxy (Kimi K2.5) for synthesis
 */

import fs from 'node:fs';
import path from 'node:path';

const OPENCLAW_CONFIG = process.env.OPENCLAW_CONFIG || '/home/desazure/.openclaw/openclaw.json';
const PROXY_BASE = process.env.FOUNDRY_PROXY_BASE || 'http://127.0.0.1:18791/v1';
const MODEL = process.env.FOUNDRY_MODEL || 'Kimi-K2.5';

function usage() {
  console.error('Usage: node run.mjs "your query"');
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
      'Accept': 'application/json',
      'X-Subscription-Token': apiKey,
    },
  });

  const text = await r.text();
  if (!r.ok) throw new Error(`Brave search failed: ${r.status} ${text.slice(0, 200)}`);
  return JSON.parse(text);
}

function normalizeResults(braveJson) {
  const items = braveJson?.web?.results || [];
  return items.map((it) => ({
    title: it.title,
    url: it.url,
    description: it.description,
    age: it.age,
  }));
}

async function kimiSynthesize({ query, results }) {
  const prompt = [
    'You are a research assistant. Use ONLY the sources provided below.',
    'Write a concise briefing with bullet points and include inline citations as URLs.',
    'If sources disagree or are low-trust, say so.',
    '',
    `Query: ${query}`,
    '',
    'Sources:',
    ...results.map((r, i) => `(${i + 1}) ${r.title}\n${r.url}\n${r.description || ''}`),
  ].join('\n');

  const body = {
    model: MODEL,
    messages: [
      { role: 'system', content: 'Return your final answer in normal content. No hidden reasoning.' },
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
  if (!r.ok) throw new Error(`Kimi proxy failed: ${r.status} ${text.slice(0, 400)}`);
  const j = JSON.parse(text);
  const msg = j?.choices?.[0]?.message || {};
  return msg.content ?? msg.reasoning_content ?? '';
}

async function main() {
  const q = process.argv.slice(2).join(' ').trim();
  if (!q) usage();

  const cfg = loadConfig();
  const braveKey = getBraveKey(cfg);

  const braveJson = await braveSearch({ apiKey: braveKey, q, count: 5 });
  const results = normalizeResults(braveJson);

  const out = await kimiSynthesize({ query: q, results });
  process.stdout.write(out.trim() + '\n');
}

main().catch((e) => {
  console.error('ERROR:', e?.stack || String(e));
  process.exit(1);
});
