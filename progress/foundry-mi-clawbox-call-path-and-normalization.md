# Foundry MI ClawBox: call path + response normalization

This documents the end-to-end request path from OpenClaw to Azure AI Foundry via the local “ClawBox” Managed Identity (MI) proxy, and explains the response-shape normalization we added.

## What this is
- **OpenClaw** calls an OpenAI-compatible API.
- A VM-local proxy (**ClawBox**) injects **Azure Managed Identity** auth (via IMDS) and forwards to **Azure AI Foundry**.
- The proxy also normalizes a response quirk where the model may return output in `reasoning_content` instead of `content`.

## End-to-end call path (diagram)

```
(1) OpenClaw agent (heartbeat OR monitor)
    |
    | HTTP POST /v1/chat/completions
    | model: foundry/Kimi-K2.5   (or foundry/gpt-4.1-mini)
    v
(2) Local ClawBox proxy (Node)
    http://127.0.0.1:18791/v1/chat/completions
    |
    | - mints Managed Identity token (IMDS)
    | - forwards request to Azure Foundry endpoint
    v
(3) Azure IMDS (Managed Identity)
    http://169.254.169.254/metadata/identity/oauth2/token
    resource=https://cognitiveservices.azure.com/
    |
    | returns access_token
    v
(4) Azure AI Foundry (OpenAI-compatible endpoint)
    https://pitchbook-resource.openai.azure.com/openai/v1/chat/completions
    |
    | runs the deployed model (Kimi-K2.5 or gpt-4.1-mini)
    | returns JSON response
    v
(5) Local ClawBox proxy (normalizes response)
    |
    | If choices[0].message.content is empty BUT reasoning_content exists:
    |    copy reasoning_content -> content
    v
(6) OpenClaw receives normalized response
    |
    | - heartbeat: decides HEARTBEAT_OK vs actions
    | - monitor: checks response contains expected sentinel and alerts if not
    v
(7) Telegram/email only if needed
```

## The response-shape quirk (why normalization exists)
OpenClaw (and most OpenAI-style client code) expects the assistant text at:
- `choices[0].message.content`

However, we observed responses from Foundry/Kimi where:
- `choices[0].message.content` was `null` or an empty string
- but `choices[0].message.reasoning_content` contained the actual text

### Visual

```
Foundry response JSON
┌───────────────────────────────┐
│ choices[0].message:           │
│   content: null   (or "")     │  ← empty
│   reasoning_content: "..."    │  ← actual text
└───────────────────────────────┘

Proxy-normalized output
┌───────────────────────────────┐
│ choices[0].message:           │
│   content: "..."              │  ← copied from reasoning_content
│   reasoning_content: "..."    │
└───────────────────────────────┘
```

## Why an end-to-end call matters (heartbeat + monitors)
A simple “service is up” check (systemd active + `/healthz` returns 200) does **not** prove:
- Managed Identity token minting is working
- Foundry endpoint is reachable
- the deployed model responds
- the JSON response shape is compatible

That’s why both heartbeat usage and the proxy monitor can rely on an actual `/chat/completions` roundtrip.

## Naming
In Clawbot/OpenClaw terms this is:
- **ClawBox Foundry MI proxy** (VM-local)
- plus a **response normalization shim** for OpenAI-compatible clients
