---
name: research
description: Run a web research pass (Brave search) and synthesize with Kimi K2.5 via the local Foundry MI proxy.
user-invocable: true
metadata: {"openclaw":{"emoji":"🔎"}}
---

# Research (Brave → Kimi via Foundry MI proxy)

Use this when the user asks you to do a web research pass and return a concise, cited briefing.

## What it does

1) Uses Brave Search API (via OpenClaw config `tools.web.search`) to get top web results.
2) Sends the sources to **Kimi K2.5** via the localhost Foundry Managed Identity proxy.

## Invocation

- From chat (recommended): `/skill research <query>`

### Plain-text trigger
If the user starts a normal message with `research` (case-insensitive), treat it as a request to run this research workflow.
Examples:
- `research: latest Anthropic model updates`
- `research what changed in OpenAI pricing this week`

Treat everything after the trigger word (and optional `:`) as the query.

## How to run (host)

Run the helper script:

```bash
node {baseDir}/scripts/research.mjs "<query>"
```

## Output format

- Keep it to a **4-minute skim**.
- Bullet points.
- Include source URLs inline.
- If sources conflict or look low-trust, say so.

## Guardrails

- Use only the provided sources in the final synthesis.
- Do not invent citations.
- Prefer 5 results max (keep cost/latency reasonable).
