# Fix: Foundry proxy 500 — Tailscale exit node routing IMDS traffic off-VM

**Date:** 2026-02-20
**Severity:** P1 — bot unresponsive (typing but no reply)
**Duration:** ~10 min
**Affected service:** `openclaw-gateway.service` via Foundry MI proxy on `oclaw2026linux`

## Symptom

Bot showed "typing" in Telegram but never sent a reply. Multiple messages queued with no response.

## Root Cause

The Tailscale exit node (`chromeos-nissa`) was routing **all** traffic — including `169.254.169.254` (Azure IMDS link-local address) — through the exit node tunnel. Tailscale's routing table 52 overrode the main table's correct `eth0` route.

The Foundry MI proxy (`server.mjs` on port 18791) calls IMDS to get Managed Identity tokens for Azure OpenAI. With IMDS routed through the exit node, the token fetch hung indefinitely, causing every LLM request to fail with:

```
FailoverError: HTTP 500: "proxy_error"
FailoverError: LLM request timed out.
```

### Routing before fix

```
$ ip route get 169.254.169.254
169.254.169.254 dev tailscale0 table 52 src 100.111.79.93   # WRONG — exit node
```

### Routing after fix

```
$ ip route get 169.254.169.254
169.254.169.254 via 172.20.0.1 dev eth0 src 172.20.0.4      # CORRECT — local
```

## Fix Applied

Added an ip policy rule to force IMDS traffic through the main routing table before Tailscale's table 52:

```bash
sudo ip rule add to 169.254.169.254 lookup main priority 100
```

### Persistence

Created `/etc/networkd-dispatcher/routable.d/50-imds-route.sh` so the rule survives reboots:

```sh
#!/bin/sh
# Ensure Azure IMDS (169.254.169.254) is routed via eth0, not Tailscale exit node
ip rule show | grep -q "to 169.254.169.254" || ip rule add to 169.254.169.254 lookup main priority 100
```

## Verification

```bash
# IMDS token fetch works
curl -s -H 'Metadata: true' 'http://169.254.169.254/metadata/identity/oauth2/token?...' → 200 + access_token

# Foundry proxy works
curl -s -X POST http://127.0.0.1:18791/v1/chat/completions ... → 200 + "Hi! How can I help you today?"

# Bot responds to Telegram messages
```

## Lesson

When using a Tailscale exit node on an Azure VM, link-local addresses (169.254.0.0/16) get routed through the exit node tunnel. Azure IMDS, Wireserver, and other link-local services will break. Always add an ip rule exception for `169.254.169.254` when configuring exit nodes on Azure VMs.

## Related

- Tailscale exit node setup: [2026-02-20-tailscale-ssh-and-egress.md](2026-02-20-tailscale-ssh-and-egress.md)
- Foundry proxy: `~/.openclaw/workspace/foundry-proxy/server.mjs` (port 18791)
- IMDS endpoint: `http://169.254.169.254/metadata/identity/oauth2/token`
