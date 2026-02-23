# Security Scan — Operational Overview

## Summary
Three-tier automated security monitoring for the OpenClaw deployment on Azure VM.

## Tiers

| Tier | Schedule | Model | Output | Delivery | Cost |
|------|----------|-------|--------|----------|------|
| 1 — Daily Scan | 7:30pm ET daily | `foundry/gpt-4.1` | `logs/security-scan-latest.md` | None (feeds carryover) | Low |
| 2 — Deep Dive | On-demand (escalation) | `github-copilot/gpt-5.2` | `logs/security-deepdive-latest.md` | Announce | Medium |
| 3 — Weekly Audit | Sunday 7pm ET | `github-copilot/gpt-5.2` | `logs/security-hardening-weekly.md` | Announce | Medium |

## Cron Job IDs
- **Tier 1:** `bdb61206-4d9f-435c-a6c8-474c43c1b909`
- **Tier 2:** `a819529a-dbd2-4f1e-bbed-721e698b1d7c` (disabled by default)
- **Tier 3:** `59ae7366-4300-4fc3-834a-5c60735e0816`

## Flow
```
7:30pm ET → Tier 1 scans sources → saves report
                ↓
8:00pm ET → Nightly carryover includes "Security HUD" (Tier 1 dashboard + summary)
                ↓ (if 🔴 ESCALATION NEEDED)
            → Triggers Tier 2 deep dive → announces to user
                ↓
Sunday 7pm ET → Tier 3 full hardening audit → announces to user
```

## Security HUD (for nightly carryover)
Use:
```bash
python3 /home/desazure/.openclaw/workspace/ops/scripts/security_hud.py
```
It extracts the dashboards + executive summary bullets from:
- `logs/security-scan-latest.md` (Tier 1)
- `logs/security-deepdive-latest.md` (Tier 2, if present)

Paste the output into the nightly carryover note under a "Security HUD" heading.

## Stack Monitored
- Ubuntu / Linux kernel 6.17.0-1008-azure
- Node.js v22.22.0
- Python 3.12 (system + .venv-gmail)
- OpenClaw (latest)
- Tailscale (chromeos-nissa exit node)
- npm dependencies
- Google API tokens and credentials

## Manual Commands
- Run Tier 1 now: trigger cron `bdb61206-4d9f-435c-a6c8-474c43c1b909`
- Run Tier 2 now: trigger cron `a819529a-dbd2-4f1e-bbed-721e698b1d7c`
- Run Tier 3 now: trigger cron `59ae7366-4300-4fc3-834a-5c60735e0816`
- Or ask the agent: "run a security scan" / "run a security deep dive" / "run a hardening audit"

## Created
2026-02-21
