# Memory System Locations — DO NOT MIX

Two completely separate memory systems exist. They share the same architecture (SQLite + Azure AI Search) but serve different agents and live in different places.

## ClawBot Memory (VM)

| Property | Value |
|----------|-------|
| **Serves** | ClawBot on the OpenClaw gateway (VM) |
| **SQLite DB** | `~/.claude-memory/memory.db` (on VM: `/home/desazure/.claude-memory/memory.db`) |
| **Azure AI Search index** | `clawbot-memory-store` |
| **Azure resource group** | `oclaw-rg` |
| **Extraction model** | GPT-5.2 via `smart_extractor.py` |
| **Recall hook** | `before_agent_start` (OpenClaw gateway hook) |
| **Sync mechanism** | `memory_bridge.py` daily cron on VM (20:35 UTC) |
| **CLI path (VM)** | `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py` |
| **CLI path (VM alt)** | `~/claude-memory/cli/mem.py` |
| **Source code (Mac)** | `~/Projects/oclaw_brain/oclaw_brain_skill_v1/` |
| **Deploy method** | `scp` from Mac to VM |
| **Health check** | `ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py status"` |
| **Cron jobs (VM)** | Extraction 20:15 UTC, sync 20:35 UTC, health check 20:00 UTC, cleanup 1st/month 22:00 UTC |

## Claude Code Memory (Mac)

| Property | Value |
|----------|-------|
| **Serves** | Claude Code sessions on the Mac |
| **SQLite DB** | `~/.agent-memory/memory.db` (on Mac: `/Users/dez/.agent-memory/memory.db`) |
| **Azure AI Search index** | `agent-code-memory` |
| **Azure resource group** | `oclaw-rg` (same) |
| **Extraction model** | GPT-5.2 via hooks |
| **Recall hook** | `UserPromptSubmit` (Claude Code hook) |
| **Sync mechanism** | `mem.py add` auto-triggers async sync from Mac |
| **CLI path (Mac)** | `~/.agent-memory/cli/mem.py` |
| **Source code (Mac)** | Same codebase, different DB_PATH config |
| **Health check** | `cd ~/.agent-memory/cli && python3 mem.py status` |

## Key Differences

| Aspect | ClawBot (VM) | Claude Code (Mac) |
|--------|-------------|-------------------|
| DB_PATH in mem.py | `~/.claude-memory/memory.db` | `~/.agent-memory/memory.db` |
| Where it runs | Azure VM (`oclaw2026linux`) | MacBook (`desis-macbook-air`) |
| How to access | `ssh oclaw` then run commands | Run locally on Mac |
| Who uses the memories | ClawBot (conversational partner) | Claude Code (dev assistant) |
| Cron location | VM crontab (`crontab -l` on VM) | Mac crontab or launchd (if any) |

## Rules

1. **NEVER run VM cron commands on Mac** — the DB paths are different
2. **NEVER deploy VM-pathed files to Mac** — `mem.py` on VM has `~/.claude-memory/`, Mac has `~/.agent-memory/`
3. **Source code is shared** — edit in `~/Projects/oclaw_brain/`, then deploy separately to each target
4. **When deploying to VM:** use `scp` to copy files, then fix DB_PATH if needed
5. **When deploying to Mac:** copy files to `~/.agent-memory/`, DB_PATH is already correct in source
6. **Azure AI Search is shared infrastructure** — both indexes live in `oclaw-rg`, same endpoint
7. **The built-in OpenClaw memory** (`~/.openclaw/memory/main.sqlite`) is a THIRD system — leave it untouched
