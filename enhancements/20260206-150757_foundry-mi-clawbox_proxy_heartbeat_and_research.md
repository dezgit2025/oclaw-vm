# Azure AI Foundry (Managed Identity) → OpenClaw Compatibility Proxy ("ClawBox")

**Timestamp:** 2026-02-06 15:07:57 UTC

## Why we’re doing this
OpenClaw can talk to “model providers” that look like standard OpenAI/Anthropic APIs (often using a static API key).

Azure AI Foundry can be called with **Entra Managed Identity** (MI), but MI requires fetching a **fresh Bearer token** from the VM’s Instance Metadata Service (IMDS) at request time.

That dynamic token step is the missing glue: OpenClaw can’t (yet) mint MI tokens per request on its own.

So we add a **tiny localhost-only proxy** (“ClawBox” for Foundry) that:

1. Receives OpenAI-compatible requests from OpenClaw
2. Fetches an MI access token from IMDS (`169.254.169.254`)
3. Forwards the request to the Azure AI Foundry endpoint with `Authorization: Bearer <token>`
4. Returns the response back to OpenClaw

This makes Foundry-hosted models (like **Kimi K2.5**) behave like a “normal” provider from OpenClaw’s point of view.

## What it’s for

### 1) Heartbeat: use Kimi K2.5 for periodic check-ins
We route Gateway heartbeats (periodic check-ins) to **Kimi K2.5** without changing the main chat/coding model.

- Primary model stays: `github-copilot/gpt-5.2`
- Heartbeat model becomes: `foundry/Kimi-K2.5`

### 2) Framework for “Research mode” (future feature)
This proxy is also the foundation for a planned research workflow:

- Retrieval: OpenClaw tools `web_search` (Brave) + `web_fetch` (page extraction)
- Synthesis: call `foundry/Kimi-K2.5` through this proxy

Benefits:
- Keeps coding/chat on GPT-5.2
- Offloads token-heavy summarization/synthesis to a cheaper Foundry model
- Provides a single place to add caps (max tokens), retries, logging, and response normalization

## Security posture
- **Bound to localhost only** (`127.0.0.1`), not reachable from LAN/Internet.
- No static secrets stored (token is minted on-demand via MI).
- Minimizes attack surface by proxying only required endpoints.

## How it works (call flow)

OpenClaw → `http://127.0.0.1:18791/v1/chat/completions`
→ proxy fetches IMDS token
→ proxy forwards to `https://pitchbook-resource.openai.azure.com/openai/v1/chat/completions`
→ response back to OpenClaw

## Implementation notes
- Proxy server: `/home/desazure/.openclaw/workspace/foundry-proxy/server.mjs`
- systemd user service: `~/.config/systemd/user/openclaw-foundry-proxy.service`

### Ops
- Health check: `curl http://127.0.0.1:18791/healthz`
- Logs: `journalctl --user -u openclaw-foundry-proxy.service -n 100 --no-pager`

## Known quirks
Some Foundry responses may populate `message.reasoning_content` instead of `message.content`.
The proxy normalizes this by copying `reasoning_content` into `content` when `content` is empty so OpenClaw receives a standard content field.
