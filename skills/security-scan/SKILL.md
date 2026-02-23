---
name: security-scan
description: Tiered daily/weekly security scanning for OpenClaw deployments — vulnerability monitoring, deep dive analysis, and hardening audits.
---

# security-scan

## Architecture — 3 Tiers

### Tier 1 — Daily Scan (7:30pm ET)
- **Model:** `foundry/gpt-4.1` (good search/parsing, cost-efficient)
- **Schedule:** Daily at 00:30 UTC (7:30pm ET)
- **Delivery:** None (feeds into 8pm ET nightly carryover)
- **Cron ID:** `bdb61206-4d9f-435c-a6c8-474c43c1b909`
- **Output:** `logs/security-scan-latest.md`
- **Purpose:** Broad sweep of trusted sources for new vulnerabilities

**Sources checked:**
1. OpenClaw GitHub — security issues, advisories, security-related commits
2. Node.js security blog — vulnerability announcements
3. Python 3.12 CVEs — NVD/advisory databases
4. Linux kernel 6.17 CVEs — Ubuntu security notices
5. AI agent security — prompt injection, LLM supply chain attacks
6. npm audit — local dependency vulnerabilities

**Escalation:** If any Critical/High item affects our stack, the report includes
`🔴 ESCALATION NEEDED` in the Summary, triggering Tier 2.

### Tier 2 — Deep Dive (on-demand)
- **Model:** `github-copilot/gpt-5.2` (strong reasoning for impact analysis)
- **Schedule:** Disabled by default; triggered manually or by carryover when Tier 1 escalates
- **Delivery:** Announce (sends results to user)
- **Cron ID:** `a819529a-dbd2-4f1e-bbed-721e698b1d7c`
- **Output:** `logs/security-deepdive-latest.md`
- **Purpose:** Detailed impact analysis of critical findings
- **Baked-in formatting:** Tier 2 now uses the same 🟢/🟡/🔴 dashboard + executive summary style as Tier 1 for easy carryover reading.

**What it does:**
1. Reads the Tier 1 report
2. For each Critical/High item: fetches full CVE details, checks version match, assesses exploitability
3. Provides specific remediation commands
4. Flags confirmed vulnerabilities with `🚨 ACTION REQUIRED`

**Manual trigger:** Run cron job `a819529a-dbd2-4f1e-bbed-721e698b1d7c` or ask "run a security deep dive"

### Tier 3 — Weekly Hardening Audit (Sunday 7pm ET)
- **Model:** `github-copilot/gpt-5.2` (thorough system analysis)
- **Schedule:** Every Sunday at 19:00 ET (23:00 UTC)
- **Delivery:** Announce (sends results to user)
- **Cron ID:** `59ae7366-4300-4fc3-834a-5c60735e0816`
- **Output:** `logs/security-hardening-weekly.md`
- **Purpose:** Comprehensive hardening audit of the full deployment
- **Baked-in formatting:** Starts with a Tier 1-style dashboard + executive summary, then the detailed scorecard.

**Audit areas:**
1. System packages — security-relevant updates pending
2. Node.js — version vs latest LTS, npm audit
3. Python — outdated packages in venv
4. Open ports — unexpected listeners
5. File permissions — tokens, keys, configs
6. SSH config — PasswordAuth, root login, key-only
7. Tailscale — peer list, config drift
8. OpenClaw config — sandbox, allowlists, security settings
9. Git secrets — accidental commits
10. Firewall — ufw/iptables status
11. Trend analysis — patterns from weekly Tier 1 reports

**Scoring:** Each area rated ✅ (good), ⚠️ (needs attention), or 🔴 (critical)

## Our Stack (for version matching)
- **OS:** Ubuntu on Azure, kernel 6.17.0-1008-azure (x64)
- **Node.js:** v22.22.0
- **Python:** 3.12 (system-managed, venv for packages)
- **OpenClaw:** latest from GitHub
- **Tailscale:** exit node via chromeos-nissa
- **Key services:** OpenClaw gateway, Foundry proxy, Google Drive API

## Report Formats

### Tier 1 — `logs/security-scan-latest.md`
```markdown
# Security Scan — YYYY-MM-DD

## ✅ Executive Summary (carryover-ready)
**Dashboard:** `OpenClaw 🟢 | Node 🟢 | Kernel 🟡 | Python 🟡 | Supply chain 🟡`

- OpenClaw: 🟢 Not affected / 🟡 Needs review / 🔴 Affected — (1 line why)
- Node.js:  🟢/🟡/🔴 — (mention our version)
- Linux kernel / Ubuntu: 🟢/🟡/🔴 — (mention our kernel)
- Python 3.12: 🟢/🟡/🔴
- Supply chain (npm/skills): 🟢/🟡/🔴

## 🔴 Critical / Zero-Day
## 🟠 High
## 🟡 Medium/Low (optional)
## 🔵 OpenClaw-specific
## 🛡️ Hardening Recommendations
## ℹ️ AI Agent Security

## Summary
```

Legend: 🟢 not affected / ✅ good • 🟡 needs review • 🔴 affected / escalation

### Tier 2 — `logs/security-deepdive-latest.md`
```markdown
# Security Deep Dive — YYYY-MM-DD

## ✅ Executive Summary (carryover-ready)
**Dashboard:** `OpenClaw 🟢 | Node 🟢 | Kernel 🟡 | Python 🟢 | Supply chain 🟡`

- OpenClaw: 🟢/🟡/🔴 — (1 line)
- Node: 🟢/🟡/🔴 — (1 line)
- Kernel/Ubuntu: 🟢/🟡/🔴 — (1 line)
- Python: 🟢/🟡/🔴 — (1 line)
- Supply chain: 🟢/🟡/🔴 — (1 line)

## Findings
### [CVE-XXXX-XXXXX] Title
- Severity:
- Affected versions:
- Our version:
- Are we affected?:
- Exploitability:
- Remediation:
- References:

## Summary
```

### Tier 3 — `logs/security-hardening-weekly.md`
```markdown
# Weekly Hardening Audit — YYYY-MM-DD

## ✅ Executive Summary (carryover-ready)
**Dashboard:** `OpenClaw 🟡 | Network 🟡 | Firewall 🔴 | SSH 🟡 | Secrets 🔴 | Supply chain 🟡`

- OpenClaw posture: 🟢/🟡/🔴 — (1 line)
- Network exposure: 🟢/🟡/🔴 — (1 line)
- Firewall: 🟢/🟡/🔴 — (1 line)
- SSH: 🟢/🟡/🔴 — (1 line)
- Secrets & permissions: 🟢/🟡/🔴 — (1 line)
- Supply chain: 🟢/🟡/🔴 — (1 line)

## Scorecard
| Area | Status | Notes |
|------|--------|-------|

## Detailed Findings
## Action Items (prioritized)
```

## Integration with Nightly Carryover
The 8pm ET carryover reads `logs/security-scan-latest.md` Summary section and includes it
under the **Security** heading in the daily notes. If `🔴 ESCALATION NEEDED` is present,
the carryover triggers Tier 2 by running its cron job.

## File Locations (per GLOBAL_FOLDER_STRUCTURE.md)
- Skill: `skills/security-scan/SKILL.md`
- Reports: `logs/security-scan-latest.md`, `logs/security-deepdive-latest.md`, `logs/security-hardening-weekly.md`
- Docs: `ops/docs/security-scan-overview.md`
