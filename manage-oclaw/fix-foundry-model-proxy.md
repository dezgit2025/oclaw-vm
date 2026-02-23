# Fix: Foundry Proxy "Unknown Model" Error

**Date:** 2026-02-09
**Severity:** Service-impacting — Kimi proxy monitor alerts, heartbeat failures
**Error:** `{"error":{"code":"unknown_model","message":"Unknown model: foundry/kimi-k2.5"}}`

---

## Summary

The Foundry MI proxy (`server.mjs`) was forwarding the model name from OpenClaw to Azure Foundry **as-is**, including the `foundry/` provider prefix. Azure Foundry doesn't understand prefixed model IDs — it expects bare names like `Kimi-K2.5`.

**Fix:** Added `stripModelPrefix()` to the proxy that removes the provider prefix before forwarding.

---

## Root Cause

```
  OpenClaw config (openclaw.json)
  ================================

  agents.defaults.models:
    "foundry/Kimi-K2.5"        <-- provider/model naming convention
    "foundry/gpt-4.1-mini"

  agents.defaults.heartbeat:
    model: "foundry/gpt-4.1-mini"
```

OpenClaw uses `provider/model` internally to route requests to the correct provider. When calling the Foundry provider, it sends the full name in the request body:

```
  OpenClaw agent                    Foundry Proxy                     Azure Foundry
  ==============                    =============                     =============

  POST /v1/chat/completions         Receives request                  Receives request
  {                                 {                                 {
    "model": "foundry/Kimi-K2.5"     "model": "foundry/Kimi-K2.5"     "model": "foundry/Kimi-K2.5"
    ...                               ...                               ...
  }                                 }                                 }
                                    |                                 |
                                    | Forwards body AS-IS             | "Unknown model!"
                                    | (no prefix stripping)           |
                                    v                                 v
                                    PROBLEM: prefix not removed       400 error returned
```

---

## The Fix

Added `stripModelPrefix()` function to `server.mjs`:

```
  BEFORE (broken)                             AFTER (fixed)
  ===============                             =============

  POST body received                          POST body received
       |                                           |
       v                                           v
  readBody(req)                               readBody(req)
       |                                           |
       |  (body forwarded as-is)                   v
       |                                      stripModelPrefix(bodyBuf)
       |                                           |
       |                                      "foundry/Kimi-K2.5"
       |                                           |
       |                                      split('/').pop()
       |                                           |
       |                                      "Kimi-K2.5"  ✓
       v                                           v
  fetch(upstream, { body })                   fetch(upstream, { body })
       |                                           |
       v                                           v
  400 "Unknown model" ✗                       200 OK ✓
```

### Code change

```javascript
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
```

Called in the request handler:

```javascript
const bodyBuf = await readBody(req);
const forwardBody = stripModelPrefix(bodyBuf);  // <-- NEW
// ...
const upstream = await fetch(upstreamUrl, {
  // ...
  body: forwardBody,  // <-- was: bodyBuf
});
```

---

## End-to-End Flow (Fixed)

```
  OpenClaw Agent (heartbeat / monitor / chat)
       |
       | POST /v1/chat/completions
       | model: "foundry/Kimi-K2.5"
       v
  +--------------------------------------------+
  | Foundry MI Proxy (server.mjs)              |
  | http://127.0.0.1:18791                     |
  |                                            |
  | 1. readBody(req)                           |
  | 2. stripModelPrefix(body)                  |
  |    "foundry/Kimi-K2.5" → "Kimi-K2.5"  ✓   |
  | 3. getManagedIdentityToken() via IMDS      |
  | 4. Forward to Azure Foundry                |
  | 5. normalizeChatCompletion() on response   |
  |    (copy reasoning_content → content)      |
  +--------------------------------------------+
       |
       | POST /chat/completions
       | model: "Kimi-K2.5"  (prefix stripped)
       | Authorization: Bearer <MI token>
       v
  +--------------------------------------------+
  | Azure IMDS (169.254.169.254)               |
  | Returns Managed Identity access_token      |
  +--------------------------------------------+
       |
       v
  +--------------------------------------------+
  | Azure AI Foundry                           |
  | pitchbook-resource.openai.azure.com        |
  |                                            |
  | Deployed models:                           |
  |   - Kimi-K2.5                              |
  |   - gpt-4.1-mini                           |
  +--------------------------------------------+
       |
       | 200 OK + chat completion response
       v
  +--------------------------------------------+
  | Foundry MI Proxy                           |
  | normalizeChatCompletion():                 |
  |   if content is null but                   |
  |   reasoning_content exists → copy it       |
  +--------------------------------------------+
       |
       | Normalized response
       v
  OpenClaw Agent (processes response)
```

---

## Model Name Mapping

| OpenClaw config name | What proxy receives | What proxy sends to Azure | Azure deployment name |
|---------------------|--------------------|--------------------------|-----------------------|
| `foundry/Kimi-K2.5` | `foundry/Kimi-K2.5` | `Kimi-K2.5` | `Kimi-K2.5` |
| `foundry/gpt-4.1-mini` | `foundry/gpt-4.1-mini` | `gpt-4.1-mini` | `gpt-4.1-mini` |
| `Kimi-K2.5` (no prefix) | `Kimi-K2.5` | `Kimi-K2.5` (unchanged) | `Kimi-K2.5` |

---

## Verification Tests

All three patterns now work:

```bash
# With foundry/ prefix (the actual problem case)
curl -s http://127.0.0.1:18791/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"foundry/Kimi-K2.5","messages":[{"role":"user","content":"say OK"}],"max_tokens":5}'
# → 200 OK ✓

# Without prefix (already worked)
curl -s http://127.0.0.1:18791/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Kimi-K2.5","messages":[{"role":"user","content":"say OK"}],"max_tokens":5}'
# → 200 OK ✓

# gpt-4.1-mini with prefix
curl -s http://127.0.0.1:18791/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"foundry/gpt-4.1-mini","messages":[{"role":"user","content":"say OK"}],"max_tokens":5}'
# → 200 OK ✓

# Health check
curl -s http://127.0.0.1:18791/healthz
# → {"ok":true,"service":"foundry-proxy"}
```

---

## Troubleshooting

### Error: "Unknown model: foundry/kimi-k2.5"

**Cause:** Proxy not stripping `foundry/` prefix. Check if `server.mjs` has the `stripModelPrefix` function.

```bash
# Check if the fix is deployed
ssh oclaw "grep -c 'stripModelPrefix' ~/.openclaw/workspace/foundry-proxy/server.mjs"
# Should return 2 (function definition + call site)

# If missing, restore from backup and re-apply fix, or redeploy
ssh oclaw "ls ~/.openclaw/workspace/foundry-proxy/server.mjs*"
```

### Error: "IMDS token fetch failed"

**Cause:** VM Managed Identity not configured or IMDS endpoint unreachable.

```bash
# Test IMDS directly
ssh oclaw "curl -s -H 'Metadata: true' \
  'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://cognitiveservices.azure.com/'"
```

### Proxy not responding

```bash
# Check service status
ssh oclaw "systemctl --user status openclaw-foundry-proxy.service"

# Check if port is listening
ssh oclaw "ss -tlnp | grep 18791"

# Restart
ssh oclaw "systemctl --user restart openclaw-foundry-proxy.service"

# Check logs
ssh oclaw "journalctl --user -u openclaw-foundry-proxy.service --no-pager -n 30"
```

### Proxy starts but requests fail

```bash
# Test health check
ssh oclaw "curl -s http://127.0.0.1:18791/healthz"

# Test actual completion (bare model name)
ssh oclaw "curl -s http://127.0.0.1:18791/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{\"model\":\"Kimi-K2.5\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}'"

# Check if Azure Foundry endpoint is reachable from VM
ssh oclaw "curl -s -o /dev/null -w '%{http_code}' https://pitchbook-resource.openai.azure.com/"
```

---

## Key File Locations

| File | Location | Purpose |
|------|----------|---------|
| Proxy server (patched) | `VM: ~/.openclaw/workspace/foundry-proxy/server.mjs` | Node.js proxy with prefix stripping |
| Proxy backup (pre-fix) | `VM: ~/.openclaw/workspace/foundry-proxy/server.mjs.backup-20260209` | Original without prefix stripping |
| Proxy docs | `VM: ~/.openclaw/workspace/foundry-proxy/README.md` | Original proxy documentation |
| Call path docs | `VM: ~/.openclaw/workspace/progress/foundry-mi-clawbox-call-path-and-normalization.md` | End-to-end call path documentation |
| systemd unit | `VM: ~/.config/systemd/user/openclaw-foundry-proxy.service` | Service definition |
| OpenClaw config | `VM: ~/.openclaw/openclaw.json` | Model definitions with `foundry/` prefix |
| Models config | `VM: ~/.openclaw/agents/main/agent/models.json` | Provider + model registry |
| This fix doc | `local: manage-oclaw/fix-foundry-model-proxy.md` | This document |

---

## Service Management

```bash
# Restart proxy after code changes
ssh oclaw "systemctl --user restart openclaw-foundry-proxy.service"

# View live logs
ssh oclaw "journalctl --user -u openclaw-foundry-proxy.service -f"

# Stop / start
ssh oclaw "systemctl --user stop openclaw-foundry-proxy.service"
ssh oclaw "systemctl --user start openclaw-foundry-proxy.service"
```

---

## Rollback

If the fix causes issues, restore the backup:

```bash
ssh oclaw "cp ~/.openclaw/workspace/foundry-proxy/server.mjs.backup-20260209 \
              ~/.openclaw/workspace/foundry-proxy/server.mjs && \
           systemctl --user restart openclaw-foundry-proxy.service"
```

Note: Rolling back will re-introduce the "Unknown model" error for requests with the `foundry/` prefix.

---

## Fix #2: Monitor Script (LLM-Generated Bash Failures)

### Problem

The Kimi proxy monitor cron job (`44a10e09` in `jobs.json`) was an `agentTurn` — meaning every 30 minutes, the LLM was asked to **generate bash from scratch** to run the health checks. The LLM kept producing broken bash:

```
  Cron timer (every 30 min)
       |
       v
  +----------------------------------+
  | OpenClaw cron job (agentTurn)    |
  |                                  |
  | Sends prompt to LLM:            |
  | "Run these 3 checks..."         |
  +----------------------------------+
       |
       v
  +----------------------------------+
  | LLM (gpt-4.1-mini)              |
  |                                  |
  | Generates bash script            |   <-- DIFFERENT every time!
  | (often broken)                   |
  +----------------------------------+
       |
       v
  +----------------------------------+
  | Bash execution                   |
  |                                  |
  | Fails with:                      |
  | - syntax errors                  |
  | - wrong model names (KimiHB)    |
  | - bad regex patterns             |
  | - broken heredocs                |
  +----------------------------------+
```

**Errors seen in logs (all from LLM-generated bash):**

| Time | Error |
|------|-------|
| 21:52 | `model: "KimiHB"` — used alias instead of `Kimi-K2.5` |
| 21:53 | `healthz body missing ok` — couldn't parse valid `{"ok":true}` |
| 21:54 | `Unknown model: kimihb` — alias lowercased by Azure |
| 22:24 | `expected "ok":true or literal ok` — broken grep pattern |
| 22:54 | `syntax error near unexpected token (` — unescaped regex |
| 22:55 | `Unknown model: foundry/kimi-k2.5` — prefix not stripped |

### Root Cause

The LLM regenerated the entire bash monitor script on every cron run. Each generation was slightly different and frequently broken because:

1. **Bash syntax** — heredocs, quoting, regex escaping are hard for LLMs to get right consistently
2. **Model name confusion** — used alias `KimiHB` (from openclaw.json config) instead of actual deployment name `Kimi-K2.5`
3. **JSON parsing in bash** — complex `grep`/`python3` pipelines generated incorrectly each time
4. **No persistence** — the `sessionTarget: "isolated"` means no memory between runs, so previous fixes don't carry over

### Fix: Static Monitor Script

Replaced the LLM-generated bash with a **deterministic static script** (`foundry-monitor.sh`):

```
  BEFORE (broken)                           AFTER (fixed)
  ===============                           =============

  Cron timer (30 min)                       Cron timer (30 min)
       |                                         |
       v                                         v
  LLM generates bash                        LLM runs ONE command:
  (different every time)                    `bash foundry-monitor.sh`
       |                                         |
       v                                         v
  Bash execution                            Static script runs
  (often fails)                             (deterministic, tested)
       |                                         |
       v                                         v
  Broken alerts / false alarms              Reliable OK / ALERT output
```

**The script** (`~/.openclaw/workspace/scripts/foundry-monitor.sh`) runs 3 checks:

```
  CHECK 1: systemd service
  systemctl --user is-active openclaw-foundry-proxy.service
       |
       | must be "active"
       v
  CHECK 2: /healthz endpoint
  curl → python3 JSON parse → require ok == true
       |
       | must be HTTP 200 + valid JSON
       v
  CHECK 3: chat completion roundtrip
  curl POST → python3 JSON parse → require sentinel in content
       |
       | must be HTTP 200 + "OK_foundry_mini_monitor" in response
       v
  OUTPUT: "OK" (all pass) or "ALERT: <details>" (any fail)
```

**The cron job** now tells the LLM:
- Run `bash foundry-monitor.sh`
- If output starts with `ALERT:` → send Telegram + email
- If output is `OK` → reply NO_REPLY
- **Do NOT write your own bash checks**

### Cron Job Config Change

```
  jobs.json entry 44a10e09
  ========================

  BEFORE:
    payload.message = (200+ word prompt describing all 3 checks
                       with curl commands, python parsing, etc.
                       LLM must generate all bash from scratch)

  AFTER:
    payload.message = "Run foundry-monitor.sh, handle ALERT/OK output"
                      (LLM just runs the script, no bash generation)
```

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| Monitor script | `VM: ~/.openclaw/workspace/scripts/foundry-monitor.sh` | Static bash — runs all 3 checks |
| Cron jobs config | `VM: ~/.openclaw/cron/jobs.json` | Updated monitor job (id: `44a10e09`) |
| Cron jobs backup | `VM: ~/.openclaw/cron/jobs.json.backup-20260209` | Pre-fix backup |
| Gateway service | `VM: systemctl --user ... openclaw-gateway.service` | Must restart to reload jobs.json |

### Test the Monitor Script

```bash
# Run directly on VM
ssh oclaw "bash ~/.openclaw/workspace/scripts/foundry-monitor.sh"
# Expected: OK

# Simulate failure (stop proxy first)
ssh oclaw "systemctl --user stop openclaw-foundry-proxy.service"
ssh oclaw "bash ~/.openclaw/workspace/scripts/foundry-monitor.sh"
# Expected: ALERT: [...] check: systemd | state: inactive
ssh oclaw "systemctl --user start openclaw-foundry-proxy.service"
```

### Rollback (Monitor)

```bash
# Restore original jobs.json
ssh oclaw "cp ~/.openclaw/cron/jobs.json.backup-20260209 ~/.openclaw/cron/jobs.json && \
           systemctl --user restart openclaw-gateway.service"
```

Note: Rolling back restores the LLM-generated bash approach, which will likely produce the same broken scripts.
