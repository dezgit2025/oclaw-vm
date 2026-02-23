# Tailscale Broke Azure AI Foundry Auth (Managed Identity / IMDS) — Incident Writeup

Date: 2026-02-21

## Problem
The **Azure AI Foundry / Azure OpenAI** requests routed through the local **Foundry Managed-Identity proxy** began failing.

Symptoms:
- Proxy `/healthz` returned **200 OK**
- Proxy `/v1/chat/completions` returned **HTTP 500** with:
  - `{"error":"proxy_error","message":"fetch failed"}`
- The periodic monitor (`scripts/foundry-monitor.sh`) fired alerts repeatedly:
  - `check: chat_http | http_code: 500 | body: {"error":"proxy_error","message":"fetch failed"}`

Impact:
- Any OpenClaw workflow that depended on the Foundry proxy (heartbeats/cron runs pinned to Foundry models) could not complete chat requests.

---

## Root Cause
The Foundry proxy authenticates to Azure AI Foundry using **Azure Managed Identity**, which requires fetching an access token from **Azure IMDS** (Instance Metadata Service):

- IMDS endpoint: `http://169.254.169.254/`
- Token path used by the proxy:
  - `http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A//cognitiveservices.azure.com/`

During the incident, IMDS token fetches were **timing out**, which caused the proxy’s internal `fetch()` call to throw, and it returned the generic `fetch failed` 500 error.

We verified this directly:
- `curl -H Metadata:true http://169.254.169.254/...` → **timeout**

---

## Why Tailscale Affected It
This VM routes *all* outbound internet traffic through a **Tailscale exit node** (residential egress) to avoid 403 blocks from datacenter IPs.

However:
- `169.254.169.254` is a **link-local** IP, only valid on the VM’s local network inside Azure.
- It must **not** be routed through the Tailscale tunnel/exit node.

If the routing exception is missing, the IMDS request can incorrectly follow the exit-node route, which leads to:
- no response / timeout
- Managed Identity token fetch failure
- AI Foundry auth failure

Simple diagram:

```
WORKING

VM -> IMDS (169.254.169.254) -> token -> Foundry endpoint -> 200

BROKEN

VM -> Tailscale exit-node tunnel (wrong path) -> IMDS unreachable -> timeout -> 500
```

---

## Fix
### 1) Add an IP rule forcing IMDS traffic to bypass Tailscale
We added (or restored) this rule:

```bash
sudo ip rule add to 169.254.169.254 lookup main priority 100
```

After adding the rule:
- IMDS token fetch succeeded immediately
- Foundry proxy chat requests returned **HTTP 200** again

### 2) Persist the rule across network events
A persistence hook existed but was **broken**:
- File: `/etc/networkd-dispatcher/routable.d/50-imds-route.sh`
- The shebang line was invalid (`#\!/bin/sh`), causing **Exec format error**, so the hook never ran.

We fixed the shebang and restarted the dispatcher:

```bash
sudo sed -i '1s/^#\\!\/bin\/sh/#!\/bin\/sh/' /etc/networkd-dispatcher/routable.d/50-imds-route.sh
sudo chmod +x /etc/networkd-dispatcher/routable.d/50-imds-route.sh
sudo systemctl restart networkd-dispatcher
```

---

## Verification
All checks passed after the fix:

1) Foundry monitor script:
```bash
bash /home/desazure/.openclaw/workspace/scripts/foundry-monitor.sh
# OK
```

2) IMDS token fetch:
```bash
curl -H Metadata:true \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A//cognitiveservices.azure.com/"
# returns JSON containing access_token
```

3) Proxy chat completion:
```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"model":"foundry/gpt-4.1-mini","messages":[{"role":"user","content":"Say OK"}],"max_tokens":8,"temperature":0}' \
  http://127.0.0.1:18791/v1/chat/completions
# HTTP 200
```

---

## Prevention / Hardening Ideas
- Add a Tier 3 hardening check: confirm `ip rule` contains the IMDS bypass rule.
- Add an alert when IMDS is unreachable (separate from Foundry proxy checks), so diagnosis is immediate.
- Consider keeping the gateway + proxy strictly bound to localhost/tailscale-only to reduce exposure.
