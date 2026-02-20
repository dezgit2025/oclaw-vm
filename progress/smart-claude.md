# smart-claude.md — “Claude Code that talks to Telegram”

## Goal
Make **Claude Code** run long jobs on your VM and **push progress updates to Telegram** (like OpenClaw does), so you can kick off work remotely and get:
- periodic “still working” heartbeats
- milestone updates (tests passed, files changed, PR ready)
- final report + links
- ability to cancel/continue

Key constraint: Claude Code is an **interactive CLI** and may require auth; the “progress to Telegram” part is **not built-in** unless we wrap it.

---

## High-level architecture (recommended)

Use a small **Job Runner + Notifier** wrapper around Claude Code.

- **Telegram** is the UI.
- A **controller** receives commands and creates jobs.
- A **runner** executes Claude Code in an isolated context (repo sandbox).
- A **notifier** streams summarized progress to Telegram.

### Diagram

```
┌───────────────┐
│   Telegram    │
│  (chat UI)    │
└───────┬───────┘
        │ commands: /claude job …, /claude status, /claude cancel
        ▼
┌─────────────────────────┐
│ OpenClaw (or thin bot)   │
│ - command routing        │
│ - permissions/allowlist  │
│ - creates JobSpec        │
└───────────┬─────────────┘
            │ writes job.json + enqueues
            ▼
┌─────────────────────────┐
│ Job Runner (VM-local)    │
│ - executes Claude Code   │
│ - captures stdout/stderr │
│ - collects artifacts     │
│ - writes structured logs │
└───────────┬─────────────┘
            │ progress events (structured)
            ▼
┌─────────────────────────┐
│ Progress Summarizer      │
│ - throttles updates      │
│ - extracts milestones    │
│ - optionally LLM-summar. │
└───────────┬─────────────┘
            │ Telegram messages
            ▼
┌───────────────┐
│   Telegram     │
│  updates back  │
└───────────────┘
```

---

## What we need to make this real

### 1) A stable execution container (or locked user) for Claude Code
Claude Code will be able to “execute any task” inside the repo (tests, installs, edits), so we need a **hard boundary**.

Best practice (same as OpenCode autonomy):
- run in a **container** or as a dedicated Linux user
- mount only **one repo**
- restrict secrets (don’t mount $HOME/ssh)

Outcome: even if Claude Code goes off the rails, it can’t read or modify unrelated stuff.

### 2) Job queue + job state model
You need a durable state representation so you can ask “what’s happening?” from Telegram.

Minimal state machine:
- `queued` → `running` → (`succeeded` | `failed` | `canceled`)

JobSpec example:
```json
{
  "jobId": "2026-02-09T10-37-00Z_abc123",
  "repo": "/repo",
  "command": "claude code",
  "goal": "Refactor X and run tests",
  "createdBy": "telegram:1203774396",
  "createdAt": "2026-02-09T10:37:00Z",
  "notify": {
    "telegramUserId": "1203774396",
    "throttleSeconds": 120
  }
}
```

Persist this to disk:
- `/home/desazure/.openclaw/workspace/claude-jobs/<jobId>/job.json`
- `/home/desazure/.openclaw/workspace/claude-jobs/<jobId>/events.jsonl`
- `/home/desazure/.openclaw/workspace/claude-jobs/<jobId>/final.md`

### 3) A way to run Claude Code non-interactively
There are 3 common patterns:

**A) “Batch mode” (ideal)**
If Claude Code supports a non-interactive command like:
- `claude run "do X"` or `claude --json …`

…then we just run it and stream output.

**B) Run it in tmux (practical for interactive CLIs)**
- start a tmux session per job
- send keystrokes (if prompts occur)
- scrape pane output periodically

This is how you make “interactive CLI feels like a service.”

**C) Use a coding-agent that already has a programmatic mode**
If Claude Code remains finicky (auth prompts, etc.), route long-running work to tools that support programmatic control (OpenCode, etc.), and keep Claude Code for short tasks.

### 4) Progress extraction + throttled Telegram updates
Raw CLI output is noisy. You want **structured progress events**.

Approach:
- tail stdout/stderr
- detect milestones:
  - “editing file …”
  - “running tests …”
  - “tests passed/failed”
  - “created patch / diff size”
  - “blocked on prompt X”
- send updates at most every N seconds (e.g., 2 minutes) + immediate on milestone

Update message shape (good UX):
- 1–3 bullets
- last milestone
- what it’s doing now
- link to logs/artifacts

### 5) Telegram command surface
You want simple verbs:
- `claude job <goal>`
- `claude status <jobId>`
- `claude cancel <jobId>`
- `claude logs <jobId>`

If built *inside OpenClaw*, these become skill triggers.
If built *outside*, it’s a Telegram bot.

---

## “Use OpenClaw as the controller” (best fit for your setup)
Because you already have:
- Telegram connectivity
- cron + background jobs
- existing coding-agent routing patterns

We can implement this as an OpenClaw skill:

### Components
1) **Skill**: `smart-claude`
   - scripts:
     - `enqueue_job.py` (creates JobSpec on disk)
     - `runner.sh` (starts tmux/sessiond job)
     - `status.py` (reads job state)
     - `cancel.sh` (kills tmux/systemd unit)

2) **Daemon**: `smart-claude-runner.service` (systemd user)
   - watches the queue dir
   - runs jobs
   - writes progress events

3) **Notifier**
   - simplest: runner itself calls OpenClaw `message` tool via a tiny “notify” command
   - or: runner writes events and OpenClaw cron polls + sends messages

### Why daemon + queue is better than “cron runs claude”
- cron is good for *periodic checks*; daemons are good for *long running jobs*
- you get job lifecycle, cancellation, logs, crash recovery

---

## Deep dive: how progress gets from Claude Code → Telegram

### A) Capture output
Run Claude Code under a PTY so it behaves like a terminal:
- `script -q -f /path/to/logfile -- command …`
- or tmux pane capture

Write raw logs:
- `raw.log`

### B) Convert output → structured events
Parse incrementally:

Example `events.jsonl` entry:
```json
{"ts":"2026-02-09T10:40:12Z","level":"info","kind":"milestone","msg":"Running tests","data":{"cmd":"pnpm test"}}
```

### C) Throttle + summarize
Rules:
- send on: `milestone`, `blocked`, `finished`, `error`
- also send every 120s “still running” if output is active
- include:
  - jobId
  - last milestone
  - last 20 lines link/summary

### D) Telegram delivery
Two ways:
1) **Use OpenClaw message tool** (best)
   - keeps your current channel routing + auth

2) Direct Telegram bot API
   - separate token and infrastructure; not needed if OpenClaw is already your bridge

---

## Security & safety rails (non-negotiable if autonomous)

1) **Repo allowlist**
- runner refuses any repo path not in allowlist

2) **Least privilege secrets**
- don’t mount global credentials
- consider per-repo tokens

3) **Network policy (optional)**
- allow outbound only to:
  - package registries
  - Git remotes
  - docs
- or fully open outbound if you prefer convenience

4) **Kill switch**
- `claude cancel <jobId>` kills the job
- timeouts by default (e.g., 2h)

5) **Audit**
- all commands + diffs logged

---

## What I’d build first (MVP)

### MVP scope
- One repo allowlisted
- `claude job <goal>` launches tmux session
- Every 2 minutes: send 1 progress message (last milestone + “still running”)
- On completion: send final summary + where logs live

### “V2” scope
- parse structured milestones
- attach patch/diff
- open PR automatically
- multi-job queue + concurrency controls

---

## Open questions (needed before implementation)
1) **Which repo path** on the VM do you want Claude Code restricted to?
2) Should the runner have **network access**? (yes/no)
3) Do you want Claude Code to be allowed to run installs (npm/pip)?
4) What cadence is ideal? (every 2 minutes vs every 5)

---

## References
- MCP: https://modelcontextprotocol.io/
- Microsoft Learn MCP endpoint docs (tools list): https://learn.microsoft.com/en-us/training/support/mcp-developer-reference
