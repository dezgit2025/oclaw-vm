# Plan: OpenClaw Azure Cost Checker Skill

**Created:** 2026-03-28
**Status:** COMPLETE — Skill deployed and verified via ClawBot on 2026-03-28
**Goal:** Create an OpenClaw skill on the VM so ClawBot can answer "check my Azure costs"

---

## What's Done

- [x] VM managed identity (system-assigned) confirmed working: principal ID `56afe324-cd9e-4d5d-b7c3-3d5847e5bdc6`
- [x] Assigned `Cost Management Reader` role at subscription scope (`c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc`)
- [x] az CLI v2.84.0 installed on VM
- [x] `az account show` returns correct subscription
- [x] IMDS token acquisition working (`curl` and `az login --identity` both succeed)
- [x] Cost query via `az rest` confirmed working from VM
- [x] IMDS route heartbeat cron installed (every 5 min) — prevents Tailscale from wiping the rule

## Resolved Blocker: IMDS Token Timeout

`az login --identity` fails with:

```
HTTPConnectionPool(host='169.254.169.254', port=80): Max retries exceeded
Connection to 169.254.169.254 timed out
```

**Root cause:** The `az login --identity` command hits IMDS at `169.254.169.254` to get an OAuth token. Even though we have an ip rule (priority 100) routing IMDS traffic through `eth0`, the `az rest` command also needs to refresh the MI token via IMDS for each API call. The token acquisition is timing out.

**Current ip rules on VM:**
```
0:   from all lookup local
100: from all to 169.254.169.254 lookup main      ← IMDS route
101: from all to 168.63.129.16 lookup main         ← Wire server route (just added)
5210-5270: Tailscale fwmark rules
```

**Paradox:** `curl -s -H Metadata:true 'http://169.254.169.254/metadata/instance/compute/vmId?...'` works fine (we tested it earlier — returned VM ID). But `az login --identity` (which hits the same IMDS endpoint on a different path `/metadata/identity/oauth2/token`) times out.

### Root Cause (resolved 2026-03-28)

Tailscale periodically refreshes its routing table and wipes the IMDS ip rule. The boot script (`/etc/networkd-dispatcher/routable.d/50-imds-route.sh`) only fires on network up — if Tailscale re-routes after boot, the rule disappears and IMDS traffic goes through `tailscale0` instead of `eth0`.

### Fix Applied

1. Re-added ip rules manually
2. Created `/usr/local/bin/ensure-imds-route.sh` — heartbeat script that re-adds rules if missing
3. Added root cron: `*/5 * * * * /usr/local/bin/ensure-imds-route.sh`

This ensures both `169.254.169.254` (IMDS) and `168.63.129.16` (Wire Server) always route through `eth0`, even after Tailscale wipes them.

---

## Remaining Steps (after blocker resolved)

- [ ] Confirm cost query works from VM via MI
- [ ] Create skill directory: `~/.openclaw/workspace/skills/azure-cost-checker/`
- [ ] Write SKILL.md directive for ClawBot
- [ ] Write `check_costs.py` script (Python, uses MI token + Cost Management REST API)
- [ ] Test via ClawBot: "check my Azure costs"
- [ ] Add to OPEN-CLAW-SKILL-INDEX.md
- [ ] Document in SOP

## Architecture

```
User asks ClawBot: "check my Azure costs"
  → ClawBot reads SKILL.md
  → Runs check_costs.py on VM
  → Script: MI token via IMDS → Cost Management REST API
  → Returns formatted cost table
  → ClawBot presents results
```

## Reference

- Subscription ID: `c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc`
- MI Principal ID: `56afe324-cd9e-4d5d-b7c3-3d5847e5bdc6`
- RBAC Role: `Cost Management Reader` (subscription scope)
- API: `POST /subscriptions/{id}/providers/Microsoft.CostManagement/query?api-version=2023-11-01`
- Query recipes: `~/Projects/work-brain/STANDARD-OPS-PROCEDURE.md` SOP-001
- Cost tracker: `~/Projects/work-brain/AZURE-COST-TRACKER.md`
