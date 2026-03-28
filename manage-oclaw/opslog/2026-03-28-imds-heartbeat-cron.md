# IMDS & Wire Server Route Heartbeat Cron

**Date:** 2026-03-28
**Impact:** VM backup agent, managed identity login, Foundry MI proxy
**Root cause:** Tailscale periodically wipes ip rules when refreshing routing table

---

## Problem

The boot script (`/etc/networkd-dispatcher/routable.d/50-imds-route.sh`) adds ip rules to route IMDS (`169.254.169.254`) and Wire Server (`168.63.129.16`) through `eth0` instead of the Tailscale exit node. However, Tailscale can wipe these rules at any time when it refreshes its routing table.

**Symptoms when rules are missing:**
- `az login --identity` times out (IMDS token acquisition fails)
- VM backup agent fails (can't reach Wire Server for auth)
- Foundry MI proxy returns 500 (can't get tokens)

**Timeline:**
- 2026-02-19: VM backup started failing (Wire Server unreachable)
- 2026-02-20: IMDS route boot script added (fixed LLM calls)
- 2026-03-28: Discovered boot script insufficient — Tailscale wiped the rule mid-session
- 2026-03-28: Added Wire Server route + heartbeat cron

## Solution

### Heartbeat script: `/usr/local/bin/ensure-imds-route.sh`

```bash
#!/bin/sh
# Ensure IMDS and Wire Server routes bypass Tailscale exit node
# Tailscale can wipe these rules when refreshing its routing table
ip rule show | grep -q "to 169.254.169.254" || ip rule add to 169.254.169.254 lookup main priority 100
ip rule show | grep -q "to 168.63.129.16" || ip rule add to 168.63.129.16 lookup main priority 101
```

### Root crontab

```
2,17,32,47 * * * * /usr/local/bin/ensure-imds-route.sh
```

Runs every 15 minutes at :02, :17, :32, :47 (offset to avoid collisions with other crons).

### Boot script (unchanged)

`/etc/networkd-dispatcher/routable.d/50-imds-route.sh` — still fires on network up as first line of defense.

## Verification

```bash
# Check rules are present
ssh oclaw "sudo ip rule list | grep -E '169.254.169.254|168.63.129.16'"

# Check routing path (should show eth0, not tailscale0)
ssh oclaw "ip route get 169.254.169.254"

# Test IMDS token acquisition
ssh oclaw "curl -sS -H 'Metadata:true' 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/' --connect-timeout 10 | head -c 100"

# Check cron is installed
ssh oclaw "sudo crontab -l | grep imds"
```

## Related

- Original IMDS issue: `manage-oclaw/opslog/2026-02-20-tailscale-exit-node-breaks-imds.md`
- CLAUDE.md section: "IMDS & Wire Server Route Exceptions"
- Tailscale exit node rules: `manage-oclaw/opslog/tailscale-exit-node-rules.md`
