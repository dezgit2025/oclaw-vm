# openclaw_vm Project Instructions

## IMPORTANT: Agent Orchestration Rules

**The main agent should ONLY orchestrate sub-agents — never process tasks directly.** Use sub-agents to process ALL tasks to preserve main agent context memory. Launch sub-agents **in parallel** whenever possible. Use sub-agents **aggressively** — even for small tasks, prefer delegation over direct execution.

---

## Project Overview

Management tools, scripts, and documentation for the **oclaw** Azure VM infrastructure. This includes SSH tunnel management, NSG configuration, Docker services (draw.io, Foundry GPT52), and Google Drive OAuth integration.

## Skill Index (Master Registry)

All OpenClaw skills are tracked in **[OPEN-CLAW-SKILL-INDEX.md](manage-oclaw/opslog/)** on the VM at `~/.openclaw/workspace/OPEN-CLAW-SKILL-INDEX.md`. This is the single source of truth for:

- All active skills (28 as of 2026-03-16) with descriptions, status, and dates
- Deprecated/disabled skills and reasons
- Skill categories (Google Suite, Social Media, Productivity, etc.)
- Changelog of all skill additions, updates, and deprecations

**Update this file whenever you add, modify, or deprecate a skill.** ClawBot can be told to read it for a full picture of available capabilities.

## OCLAW Brain CLI (copilot-cli-llm)

| Property | Value |
|----------|-------|
| Repo | `https://github.com/dezgit2025/copilot-cli-llm` (private) |
| Local path | `~/Projects/oclaw-brain/copilot-cli-llm/` |
| Language | Go 1.26+ |
| SDK | GitHub Copilot SDK for Go (`github.com/github/copilot-sdk/go` v0.1.32) |
| Default model | `gpt-5.4` |
| Think model | `claude-opus-4.6` (triggered by `think:` prefix) |
| Auth | `GH_TOKEN` from `dvillanueva_microsoft` enterprise account (personal `dezgit2025` lacks SDK org policy) |
| Deploy path (VM) | `~/.openclaw/workspace/bin/oclaw-brain` |
| Build plan | `plans/copilot-cli-llm-plans.md` |
| Progress | `plans/progress.md` |

## Azure Infrastructure

| Resource | Value |
|----------|-------|
| Resource Group (VM) | `RG_OCLAW2026` |
| Resource Group (AI Search) | `oclaw-rg` — Azure AI Search (`oclaw-search`) lives here, NOT in `RG_OCLAW2026` |
| Linux VM | `oclaw2026linux` (Standard_D4s_v3 — 4 vCPU / 16 GiB) |
| Windows VM | `oclaw-admin-win11m` |
| VM NSG | `oclaw2026linux-nsg` |
| Subnet NSG | `vnet-eastus2-snet-eastus2-1-nsg-eastus2` |
| Region | East US 2 |
| SSH Host | `oclaw` (defined in `~/.ssh/config`, uses Tailscale IP) |
| SSH User | `desazure` |
| SSH Key | `~/.ssh/oclaw-key-v4.pem` |
| VM Public IP | `20.81.190.88` (fallback only — use `oclaw-public` SSH alias) |
| VM Tailscale IP | `100.111.79.93` (primary — used by `oclaw` SSH alias) |

## Key Directories

| Path | Purpose |
|------|---------|
| `manage-oclaw/` | SSH tunnel manager, NSG setup script, OAuth docs |
| `manage-oclaw/opslog/` | Operational incident logs and breaking-change fixes |
| `docker/` | Docker-related configs |
| `venv/` | Local Python virtual environment |

## manage-oclaw/ Scripts

These are the primary operational scripts. See `manage-oclaw/README.md` for full docs.

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-setup-nsg-for-oclaw-ssh.py` | Detects public IP, creates/updates NSG rules on both subnet + VM NSGs, tests SSH | **Fallback only** — not needed with Tailscale |
| `create-manage-tunnel-oclaw.py` | Manages SSH tunnel (ports 18792-18797) | `start` / `stop` / `restart` / `status` |

### Typical Workflow

```bash
cd manage-oclaw/
./create-manage-tunnel-oclaw.py start  # start tunnel (SSH goes over Tailscale — no NSG step)
```

## SSH Tunnel Ports

| Port | Service |
|------|---------|
| 18792 | openclaw-gateway |
| 18793 | gdrive auth/services |
| 18794 | Google OAuth redirect (Drive) |
| 18795 | Google OAuth redirect (Docs) |
| 18796 | Google OAuth redirect (Sheets) |
| 18797 | Google OAuth redirect (Calendar) |

## VM Paths (on oclaw2026linux)

The VM workspace follows a standard folder structure documented in `~/.openclaw/workspace/GLOBAL_FOLDER_STRUCTURE.md` (also mirrored at [manage-oclaw/opslog/GLOBAL_FOLDER_STRUCTURE.md](manage-oclaw/opslog/GLOBAL_FOLDER_STRUCTURE.md)).

**Code entropy prevention:** All files on the VM must be placed in the correct directory per the folder structure. If clawbot finds a misplaced file, it must move it to the correct location, log the move to `memory/entropy-fixes.md`, and update its memory with the new path. See the "Code Entropy Prevention" section in GLOBAL_FOLDER_STRUCTURE.md for full rules.

| Path | Purpose |
|------|---------|
| `~/.openclaw/workspace/` | Main workspace root — see GLOBAL_FOLDER_STRUCTURE.md |
| `~/.openclaw/workspace/skills/` | Per-skill folders (scripts, docs, directives) |
| `~/.openclaw/workspace/ops/watchdog/` | Watchdog scripts (gateway, tailscale egress) |
| `~/.openclaw/workspace/ops/docs/` | Operational runbooks and rules |
| `~/.openclaw/workspace/ops/scripts/` | Maintenance/automation scripts |
| `~/.openclaw/openclaw.json` | Main gateway configuration |
| `~/.local/state/openclaw/` | Watchdog state files (JSON) |
| `~/.openclaw/logs/` | Daily rotating logs per component |
| `~/.config/openclaw-gdrive/credentials.json` | Google OAuth client secret |
| `~/.config/openclaw-gdrive/token-openclawshared.json` | Google Drive OAuth token (access + refresh) |
| `~/.config/openclaw-gdrive/token-docs-openclawshared.json` | Google Docs + Drive readonly OAuth token |
| `~/.openclaw/workspace/.venv-gmail/` | Python venv with google-auth-oauthlib |
| `~/.openclaw/workspace/skills/gdrive-openclawshared/scripts/auth.py` | OAuth auth script |
| `~/.openclaw/workspace/run-gdrive-auth.sh` | Shortcut to run the auth script |

## Tailscale

SSH to the VM uses Tailscale (WireGuard mesh) instead of the public IP. This eliminates the need for NSG rule management — Tailscale uses outbound-only connections, so no inbound firewall rules are required. Tailscale reconnects automatically after VM restart.

**Enable/disable Tailscale on Mac:** `tailscale up` / `tailscale down`. After reboot, open the app first then run CLI. Conflicts with MS Azure VPN — disable one before using the other. Full procedure: **[manage-oclaw/opslog/2026-02-25-tailscale-mac-enable-disable.md](manage-oclaw/opslog/2026-02-25-tailscale-mac-enable-disable.md)**

| Component | Value |
|-----------|-------|
| VM Tailscale IP | `100.111.79.93` |
| Mac Tailscale IP | `100.85.14.32` |
| Exit node | `chromeos-nissa` (`100.124.62.63`) — residential IP egress |
| SSH alias | `oclaw` → Tailscale IP; `oclaw-public` → public IP (fallback) |
| Tailscale version (VM) | 1.94.2 |

### Tailscale ACLs

Managed at https://login.tailscale.com/admin/acls. Current policy:

| Source | Destination | Allowed |
|--------|-------------|---------|
| MacBook | oclaw | Yes — all ports (SSH, admin) |
| oclaw | chromeos-nissa | Yes — exit node handshake |
| MacBook / oclaw | Internet (via exit node) | Yes |
| oclaw | MacBook | **Blocked** — deny by default |
| iPhone | oclaw | **Blocked** — deny by default |

### Exit Node (Residential IP Egress)

The VM routes **all internet traffic** through `chromeos-nissa` (Android/ChromeOS) via a Tailscale exit node to egress from a residential IP (`108.29.69.37`). This avoids 403 blocks that many services apply to Azure datacenter IPs.

**Routing summary:**

| State | Egress IP | Path |
|-------|-----------|------|
| Normal (exit node up) | `108.29.69.37` (residential) | VM → Tailscale tunnel → chromeos-nissa → Internet |
| Failover (exit node down) | `20.81.190.88` (Azure) | VM → Azure network → Internet |
| IMDS (always local) | n/a | VM → eth0 → `169.254.169.254` (ip rule exception) |

**Failover watchdog** runs every 2 min via cron:
- Checks if exit node is reachable (`tailscale ping`)
- After 2 consecutive failures (~4 min) → clears exit node (falls back to Azure native egress)
- When exit node recovers → re-enables residential egress (~2 min)
- Script: `~/.openclaw/workspace/ops/watchdog/tailscale_egress_watchdog.py`
- State: `~/.local/state/openclaw/tailscale-egress-watchdog.state`
- Logs: `~/.openclaw/logs/tailscale-egress-watchdog/YYYY-MM-DD.log`
- Full rules doc (on VM): `~/.openclaw/workspace/ops/docs/tailscale-exit-node-rules.md`

**Quick checks:**

```bash
# Current egress IP (residential = 108.29.69.37, Azure = 20.81.190.88)
ssh oclaw "curl -s ifconfig.me"

# Watchdog state
ssh oclaw "cat ~/.local/state/openclaw/tailscale-egress-watchdog.state"

# Tailscale status
ssh oclaw "tailscale status"
```

**Critical rules:**
- chromeos-nissa must be **powered on and awake** for residential egress. If it sleeps, the watchdog fails over to Azure automatically
- **NEVER run `tailscale set --advertise-exit-node` on oclaw** — Tailscale cannot use and be an exit node simultaneously. This clears chromeos-nissa and drops residential egress. The VM should only **use** an exit node, never **be** one
- See [exit node rules](manage-oclaw/opslog/tailscale-exit-node-rules.md) for full documentation

### IMDS Route Exception

The exit node routes all traffic — including Azure IMDS (`169.254.169.254`). An ip rule exception forces IMDS through `eth0`:

```bash
sudo ip rule add to 169.254.169.254 lookup main priority 100
```

This is persisted via `/etc/networkd-dispatcher/routable.d/50-imds-route.sh`. **Without this, the Foundry MI proxy cannot get tokens and all LLM calls fail with 500.** See [opslog](manage-oclaw/opslog/2026-02-20-tailscale-exit-node-breaks-imds.md).

### Gateway Tailscale Mode

The openclaw gateway has its own `tailscale.mode` setting in `~/.openclaw/openclaw.json`. This is a **separate concern** from SSH-over-Tailscale and exit node routing. Keep it set to `"mode": "off", "resetOnExit": false`. See [opslog](manage-oclaw/opslog/2026-02-20-gateway-crash-tailscale-mode-invalid.md) for what happens if it gets changed.

## NSG Rules (Locked Down)

**Not needed for normal operations** — Tailscale bypasses NSG entirely. Azure Bastion was removed on 2026-02-22 (saves ~$138/month). No inbound Allow rules remain.

**Current VM NSG rules (`oclaw2026linux-nsg`):**

| Rule | Priority | Action | Purpose |
|------|----------|--------|---------|
| `DenyOpenClawWebGateway` | 1001 | Deny | Blocks port 18789 from Internet — **DO NOT REMOVE** |
| `DenyOpenClawControl` | 1002 | Deny | Blocks port 18791 from Internet — **DO NOT REMOVE** |
| `JITRule_...` (Defender) | 4096 | Deny | Deny SSH from all (managed by Defender) |

**Subnet NSG:** No custom rules (default deny).

### Why Keep the Explicit Deny Rules

The default `DenyAllInBound` (priority 65500) already blocks Internet traffic, but the two explicit deny rules on ports 18789/18791 are kept as **intentional defense-in-depth** due to widespread exploitation of exposed openclaw instances:

- **42,665 exposed openclaw instances** found on the Internet (Jan-Feb 2026), 5,194 actively exploited
- **CVE-2026-25253** (CVSS 8.8): One-click RCE chain — even localhost-bound gateways exploitable via malicious webpage
- Default openclaw config previously bound to `0.0.0.0:18789` — tens of thousands of cloud instances were open
- `/api/export-auth` endpoint had no auth — attackers extracted API keys (Claude, OpenAI, Google) within minutes
- **ClawHavoc campaign**: 800+ malicious skills (~20% of ClawHub registry) distributing info-stealer malware
- Multiple hacking groups actively scanning for exposed port 18789

The explicit deny rules at low priority numbers protect against accidental Allow rules being added above `DenyAllInBound`. Our gateway (port 18789) is only reachable via the SSH tunnel over Tailscale — never exposed to Internet.

**References:** [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/), [Bitsight](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances), [Hunt.io CVE-2026-25253](https://hunt.io/blog/cve-2026-25253-openclaw-ai-agent-exposure)

**Emergency fallback** — only if Tailscale is down:

```bash
./manage-oclaw/check-setup-nsg-for-oclaw-ssh.py    # creates AllowSSH-MyIP rules
ssh oclaw-public "hostname"                          # uses public IP alias
```

- Rule name: `AllowSSH-MyIP` (priority 100)
- Applied to both subnet NSG and VM NSG
- NSG rules get cleared on VM deallocation

## VM Auto-Shutdown & Startup

The VM auto-shuts down at ~11 PM nightly. When the user says "turn on oclaw VM" or similar, follow the steps in **[manage-oclaw/turn_on_oclaw_vm.md](manage-oclaw/turn_on_oclaw_vm.md)**.

**Quick reference** (Azure CLI is installed, `az login` already done):

1. `az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`
2. `./manage-oclaw/create-manage-tunnel-oclaw.py start`

No NSG step — Tailscale reconnects automatically on boot.

## Check oclaw Gateway

The gateway is monitored by a lightweight watchdog cron job (no LLM). Full details: **[manage-oclaw/check_clawbot_gateway_test_ping_every_5_min_cron_.md](manage-oclaw/check_clawbot_gateway_test_ping_every_5_min_cron_.md)**

**Quick checks:**

```bash
# Gateway status
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"

# Watchdog logs (today)
ssh oclaw "cat ~/.openclaw/logs/gateway-watchdog/$(date -u +%Y-%m-%d).log"

# Watchdog state (fail count + last restart)
ssh oclaw "cat ~/.local/state/openclaw/gateway-watchdog.state"
```

**How it works:** Cron runs every 5 min → checks systemd unit + TCP port 18789 → restarts after 2 consecutive failures (rate-limited to once per 30 min) → logs to `~/.openclaw/logs/gateway-watchdog/`.

**Restart gateway manually:**

```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"
```

This script restarts `openclaw-gateway.service` via systemd (user unit), logs timestamps, and confirms the service is active after restart.

## Google OAuth Reauth

**Full workflow and troubleshooting:** **[GOOGLE-AUTH.md](GOOGLE-AUTH.md)**

**Trigger:** When user says "reauth google", "google reauth", "refresh google tokens", or similar.

**Prerequisites:** VM must be running and tunnel connected (ports 18793-18798 needed).

### GDrive Quick Reauth (single service)

```bash
ssh oclaw "~/.openclaw/workspace/ops/google-auth/reauth-drive.sh"
```

Script handles port cleanup, token deletion, and OAuth flow. Open the printed URL in your Mac browser.

### Full reauth (all 6 Google services)

```bash
echo "Y" | ./google-reauth/laptop_google_reauth.sh oclaw assistantdesi@gmail.com
```

| Service | Token Path (on VM) |
|---------|--------------------|
| Gmail | `~/.config/openclaw-gmail/token-assistantdesi_gmail_com.json` |
| GDrive | `~/.config/openclaw-gdrive/token-openclawshared.json` |
| GDocs | `~/.config/openclaw-gdrive/token-docs-openclawshared.json` |
| GSheets | `~/.config/openclaw-gdrive/token-sheets-openclawshared.json` |
| GCal (read) | `~/.config/openclaw-gcal/token-readonly.json` |
| GCal (write) | `~/.config/openclaw-gcal/token-write.json` |

### If auth fails (`invalid_grant`)

Delete the token first, then retry:
```bash
ssh oclaw "rm -f ~/.config/openclaw-gdrive/token-openclawshared.json"
```

### Script maintenance rule

Auth scripts must run **directly on the VM** — no inner `ssh oclaw` calls. If given a script with `ssh oclaw` inside, strip those calls so auth.py runs locally on the VM. Then deploy via `scp` + `chmod +x`. See [GOOGLE-AUTH.md](GOOGLE-AUTH.md) for full details.

**After reauth**, optionally run the audit:
```bash
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/google-auth/audit_google_oauth.py"
```

## Gateway Model Configuration

The gateway uses GitHub Copilot as its primary model provider. Model IDs must match the openclaw built-in registry exactly.

| Setting | Value |
|---------|-------|
| Primary model | `github-copilot/claude-opus-4.6` |
| Fallback | `github-copilot/gpt-5.2` |
| Config path | `agents.defaults.model` in `~/.openclaw/openclaw.json` |

**Important:** The model ID is `claude-opus-4.6`, **NOT** `copilot-opus-4.6`. Use `openclaw models list --all | grep github-copilot` to see valid IDs.

Full model reference, available IDs, and config examples: **[manage-oclaw/opslog/copilot-model-oclaw-notes.md](manage-oclaw/opslog/copilot-model-oclaw-notes.md)**

## Patches & Shims on VM

**Full patch registry:** **[SHIM-PATCH-LOG.md](SHIM-PATCH-LOG.md)** — single source of truth for all patches, config overrides, upgrade checklist, and retirement tracking.
**Version history:** **[OPEN-CLAW-VERSION-LOG.md](OPEN-CLAW-VERSION-LOG.md)** — records every OpenClaw version upgrade with smoke test results, patches re-applied/retired, breaking changes, and rollback notes.

**Upgrade workflow:** **[workflow/upgrade-openclaw.md](workflow/upgrade-openclaw.md)** — 7-phase procedure (research → baseline → upgrade → patches → smoke tests → docs → monitor). **Follow this workflow for every OpenClaw upgrade.** Never run `npm update -g openclaw` — always pin the version.

| Patch | Type | Date | Status | Quick Reference |
|-------|------|------|--------|-----------------|
| PATCH-001: `pollIntervalMs` Telegram schema | Dist patch | 2026-02-20 | Active | Re-apply after update |
| PATCH-002: Copilot Enterprise IDE headers | Config override | 2026-03-19 | Active | Survives updates |

## ClawBot Memory System (oclaw_brain)

**Memory locations guide:** **[MEMORY-LOCATIONS.md](MEMORY-LOCATIONS.md)** — Two separate memory systems exist (ClawBot on VM vs Claude Code on Mac). **Do not mix them.** Read this file before touching any memory DB, CLI, or cron.

Persistent cross-session memory for ClawBot, deployed 2026-02-23. Two injection paths: always-on hook + on-demand deep recall skill. Full learnings: **[plans/memory-learnings-v1.md](plans/memory-learnings-v1.md)**

**Memory CI Loop PRD:** **[MEMORY-CI-LOOP.PRD](MEMORY-CI-LOOP.PRD)** — Quality improvement system: research → extract → score → normalize → boost → decay → report → repeat.

**Memory test commands:** **[manage-oclaw/MEMORY-TEST-COMMANDS.md](manage-oclaw/MEMORY-TEST-COMMANDS.md)** — All SSH commands for health check, search, pin, recall, extraction, lifecycle, Azure search, SQLite queries, cron checks, and troubleshooting.

### Architecture

| Component | Path (on VM) | Purpose |
|-----------|-------------|---------|
| Skill files | `~/.openclaw/workspace/skills/clawbot-memory/` | Extraction, sync, recall scripts |
| Hook | `~/.openclaw/hooks/clawbot-memory/` | `before_agent_start` hook (HOOK.md + handler.js) |
| SQLite DB | `~/.claude-memory/memory.db` | Local memory store (source of truth) |
| Venv | `~/.openclaw/workspace/skills/clawbot-memory/.venv/` | Python deps (openai, azure-search-documents) |
| Session symlink | `~/.openclaw/logs/sessions` → `~/.openclaw/agents/main/sessions` | Bridges expected vs actual session path |
| Source code (laptop) | `/Users/dez/Projects/oclaw_brain/oclaw_brain_skill_v1/` | Original source files |

### How It Works

1. **Hook injection (always-on):** `before_agent_start` hook fires every turn → extracts user message → runs `smart_extractor.py recall` → returns 3-5 relevant facts as `<clawbot_context>` prepended to prompt. Latency: ~0.13s (budget: 4s timeout).
2. **SKILL.md deep recall (on-demand):** When ClawBot gets a memory query, it can run the full recall pipeline for topic-specific search with more results.
3. **Daily extraction:** Cron at 20:15 UTC runs `smart_extractor.py sweep` to extract facts from new sessions via GPT-5.2.
4. **Daily sync:** Cron at 20:35 UTC runs `memory_bridge.py sync` to push SQLite → Azure AI Search (3072-dim embeddings).
5. **Fallback chain:** Azure AI Search (hybrid) → SQLite FTS5 → skip silently.

### Cron Jobs (memory-related)

| Schedule (UTC) | Command | Purpose |
|----------------|---------|---------|
| `10 20 * * *` | `session_format_watchdog.py` | Validate session format before extraction |
| `15 20 * * *` | `smart_extractor.py sweep` | Extract facts from new sessions |
| `35 20 * * *` | `memory_bridge.py sync` | Sync SQLite → Azure AI Search |
| `0 3 * * *` | Log rotation | Keep 7 days of extraction/sync logs |

### Quick Checks

```bash
# Memory count
ssh oclaw "source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && cd ~/.openclaw/workspace/skills/clawbot-memory && python3 smart_extractor.py status"

# Test recall
ssh oclaw "source ~/.openclaw/workspace/skills/clawbot-memory/.venv/bin/activate && cd ~/.openclaw/workspace/skills/clawbot-memory && python3 smart_extractor.py recall 'topic here' -k 5"

# Session format watchdog
ssh oclaw "cat ~/.local/state/openclaw/session-format-watchdog.state"

# Hook status
ssh oclaw "openclaw hooks list 2>/dev/null"

# Extraction logs
ssh oclaw "ls -la ~/claude-memory/logs/"
```

### Memory Dedup & Project Normalization (2026-02-25)

`mem.py` now has fuzzy word-overlap dedup (>60% match = blocked, cross-project) and project name normalization via `PROJECT_ALIASES` map. Prevents future duplicate memories. `--force` flag bypasses dedup. Weekly LLM dedup sweep (GPT-4.1-mini) planned but not yet built. Full details: **[learnings/memory-learnings.md](learnings/memory-learnings.md)**

ClawBot memory instruction file pushed to VM: `~/.openclaw/workspace/skills/clawbot-memory/open-claw-md-teacher.md`

### Important Notes

- **Do NOT modify `smart_extractor.py` format detection** without testing against actual v3 session files — the v3 parser was added after a bug where v2-only detection returned 0 candidates
- **`mem.py` must exist at TWO locations:** `~/claude-memory/cli/mem.py` AND `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py` (smart_extractor.py references the skill dir path)
- **Gateway restart required** after changing hook files: `ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"`
- **Azure AI Search** is in `oclaw-rg` (not `RG_OCLAW2026`), costs ~$74/mo (basic tier, flat-rate)
- **Env vars required on VM:** `AZURE_SEARCH_ENDPOINT`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_ENDPOINT` (set in /etc/environment)
- **Azure sync runs from VM only** — the local Mac does NOT need `azure-search-documents` installed. `mem.py add` on the Mac writes to local SQLite; the VM cron (`memory_bridge.py sync`) handles pushing to Azure AI Search. Do not attempt local-to-Azure sync from the Mac.
- **This memory system (oclaw_brain) is separate from Claude Code's global memory** (`~/.agent-memory/`). The oclaw_brain system lives on the VM (`~/.claude-memory/` → Azure AI Search) and serves ClawBot via hooks. Claude Code on the Mac has its own independent `~/.agent-memory/memory.db` connected to the global CLAUDE.md agent memory. Do not mix the two.
- This is also separate from the built-in `~/.openclaw/memory/main.sqlite` — leave that untouched

## Foundry Proxy Fix

The Foundry MI proxy (`server.mjs`) strips `foundry/` prefix from model names before forwarding to Azure. The monitor cron job uses a static script instead of LLM-generated bash. Full details: **[manage-oclaw/fix-foundry-model-proxy.md](manage-oclaw/fix-foundry-model-proxy.md)**

## Starbucks WiFi Ops (Rate-Limit Bypass)

Docs and test results for bypassing Starbucks WiFi traffic shaping when working remotely. Full findings: **[starbucks_ops/rate-limit-bypass/findings-2026-02-19.md](starbucks_ops/rate-limit-bypass/findings-2026-02-19.md)**

**Key findings (2026-02-19):**
- Starbucks shapes **per-device (MAC address)** — ~15 Mbps cap per device to Azure
- Not per-port, per-protocol, or per-flow — tested SSH on ports 22/443/993/123, WireGuard UDP, ByeDPI packet manipulation
- Multiple parallel streams make it worse (4 streams = 6.7 Mbps vs 1 stream = 15 Mbps)
- VM itself has ~408 Mbps to Cloudflare — bottleneck is entirely the WiFi link

**Viable bypass: Multi-device bonding**
- Add a second device with different MAC → gets its own ~15 Mbps session
- **Android USB tether** passes WiFi through (iOS does NOT — only shares cellular)
- **GL.iNet travel router** ($30-70) with spoofed MAC + USB-C Ethernet to Mac
- Bond interfaces with `dispatch-proxy` (npm) → SOCKS proxy round-robins across links
- USB WiFi adapters do NOT work on Apple Silicon (no kernel extension support)

**TODO:** Test Android WiFi tethering + bonding at Starbucks

## Resolved Bug: 421 Misdirected Request (2026-03-18 → fixed 2026-03-19)

**Debug log:** [four21bug/four21bug-log.md](four21bug/four21bug-log.md) | **Patch:** PATCH-002 in [SHIM-PATCH-LOG.md](SHIM-PATCH-LOG.md)

Enterprise Copilot API requires IDE headers that OpenClaw doesn't send. Fixed via config override (survives updates). See SHIM-PATCH-LOG.md for full details and upgrade instructions.

## Sensitive Files (do not commit)

- `credentials.json` -- Google OAuth client secret
- `token.json` -- Azure/Google tokens
- `.env.*` files (non-example ones)
- `~/.ssh/oclaw-key-v4.pem`

> Task execution: Follow plans/AGENT-PLAN.md for all task execution, testing, and commit protocol.
