# WORKFLOW_AUTO.md

Bare-minimum autopilot workflow for this OpenClaw workspace.

## Daily / Nightly

### 7:30pm ET — Security Scan Tier 1
- Cron runs Tier 1 security scan and writes: `logs/security-scan-latest.md`
- Output includes a dashboard line + executive summary bullets.

### 8:00pm ET — Daily carryover
When nightly carryover reminder fires:
- If user replies `carryover:` → log key decisions/context into `memory/YYYY-MM-DD.md`
- If user replies `summarize today` → produce 10–30 bullet summary + 0–10 durable items
- Include **Security HUD** in carryover:
  - Run: `python3 ops/scripts/security_hud.py`
  - Paste output under a `## 🛡️ Security HUD` heading in the daily note

### Maintenance
- If user says `archive memory` / `-archive memory` / `rotate+archive`:
  1) Run: `python3 /home/desazure/.openclaw/workspace/manage-oclaw/session_gc.py`
  2) Rotate/archive session logs to keep last ~3 days (if configured)

## Always-on monitors (cron)
- Tailscale exit-node watchdog: alerts only on state change (down/recovery)
- Foundry proxy monitor: investigate 500s; common cause is Azure IMDS route exception missing under Tailscale egress

## File-sharing policy
- Only intended sharing paths:
  1) Gmail drafts (draft-only)
  2) Google Drive uploads to OpenClawShared

## Workspace organization
- External/collab repos live under: `repos/` (ignored by workspace git)

