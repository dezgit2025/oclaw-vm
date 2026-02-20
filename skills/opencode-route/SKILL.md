---
name: opencode-route
description: Run OpenCode on demand (trigger: `opencode:`). Creates/uses a project folder under ~/Projects.
user-invocable: true
metadata: {"openclaw":{"emoji":"🧩"}}
---

# OpenCode optional route

Use this skill when the user wants to run **OpenCode** explicitly.

## Trigger

### Plain-text trigger (preferred)
If the user message starts with `opencode:` (case-insensitive), treat the rest of the message as the task prompt and run OpenCode.

Example:
- `opencode: create a small FastAPI app with a /healthz endpoint`

## Default working directory policy

- For **new coding projects**, create a new subfolder under: `~/Projects/`
- For work on an existing repo, run in that repo folder.

## Requirements

- `opencode` CLI must be installed and on PATH.
- One-time auth:
  - Launch `opencode`
  - Run `/connect` → choose **GitHub Copilot** → complete device login
  - Run `/models` to select a default model

Ref:
- Copilot + OpenCode: https://github.blog/changelog/2026-01-16-github-copilot-now-supports-opencode/
- OpenCode providers/models: https://opencode.ai/docs/providers/

## How to run (host)

Helper script:

```bash
bash {baseDir}/scripts/opencode_run.sh "<task prompt>"
```

Notes:
- The OpenCode TUI is interactive; use PTY when running via OpenClaw exec.
