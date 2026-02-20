# OpenClaw Workspace Folder Structure

## Layout

```
~/.openclaw/workspace/
├── skills/                    # Per-skill folders
│   ├── <skill-name>/
│   │   ├── scripts/           # Skill scripts
│   │   ├── SKILL.md           # Skill usage docs
│   │   └── references/        # Related docs, guides, config, directives for that skill
│   │        └── DIRECTIVES.md # Skill-specific special directive prompts
├── ops/                       # Operational/administrative workspace
│   ├── scripts/               # Glue/maintenance/automation scripts
│   ├── docs/                  # Cross-skill documentation, workflows, logs, config changes
│   │   ├── model_routing_report.md
│   │   ├── tailscale-exit-node-rules.md
│   │   └── SPECIAL_DIRECTIVES.md  # Global special directive prompts for AI or ops
│   └── watchdog/              # Watchdog scripts and monitoring tooling
│       ├── tailscale_egress_watchdog.py
│       ├── run_tailscale_egress_watchdog.sh
│       └── restart_gateway.py
├── config/                    # (Optional) Global/shared configuration files
├── docs/                      # General user, project-level docs unrelated to ops/skills
├── memory/                    # Durable memory logs, daily notes, checkpoints
└── GLOBAL_FOLDER_STRUCTURE.md # This file
```

## Conventions

### Directives

- **Skill-specific directives** live inside each skill's `references/DIRECTIVES.md` for focused control related to that skill's behavior.
- **Global workspace-wide directives** (multi-agent orchestration, routing rules, universal AI prompt instructions) live in `ops/docs/SPECIAL_DIRECTIVES.md`.
- This separation maintains clarity, version control, and context for directives depending on their scope and impact.
- Keeping directives in Markdown files lets you add explanations, examples, and maintain easily readable instructions.

### Ops

- `ops/watchdog/` — cron-driven health checks with state files and daily log rotation.
- `ops/scripts/` — one-off or scheduled maintenance scripts (auth, cleanup, migrations).
- `ops/docs/` — operational runbooks, rules, and cross-cutting documentation.

### Skills

- Each skill is self-contained in its own folder under `skills/`.
- `SKILL.md` is the entry point — describes what the skill does and how to use it.
- `scripts/` contains the executable code for the skill.
- `references/` holds supporting docs, API guides, and skill-specific directives.

### State and Logs (outside workspace)

| Path | Purpose |
|------|---------|
| `~/.local/state/openclaw/` | Watchdog state files (JSON) |
| `~/.openclaw/logs/` | Daily rotating logs per component |
| `~/.openclaw/openclaw.json` | Main gateway configuration |
| `~/.openclaw/agents/` | Agent session data |
| `~/.openclaw/canvas/` | Canvas static files |

## Code Entropy Prevention (Self-Healing Rule)

**Rule:** Every file in the workspace MUST live in the correct directory according to this structure. No orphaned files, no "temporary" dumps in the wrong folder.

### Placement Rules

| File type | Correct location | Example |
|-----------|-----------------|---------|
| Skill script | `skills/<skill-name>/scripts/` | `skills/gdrive/scripts/auth.py` |
| Skill docs | `skills/<skill-name>/SKILL.md` | `skills/gdrive/SKILL.md` |
| Skill directives | `skills/<skill-name>/references/DIRECTIVES.md` | |
| Watchdog/monitor script | `ops/watchdog/` | `ops/watchdog/tailscale_egress_watchdog.py` |
| Maintenance/automation script | `ops/scripts/` | `ops/scripts/google_reauth.sh` |
| Operational runbook/rules doc | `ops/docs/` | `ops/docs/tailscale-exit-node-rules.md` |
| Global directives | `ops/docs/SPECIAL_DIRECTIVES.md` | |
| Shared config | `config/` | |
| General project docs | `docs/` | |
| Memory/notes/checkpoints | `memory/` | |

### Clawbot Enforcement

When clawbot creates, modifies, or encounters a file:

1. **Before writing:** Check this structure. Place the file in the correct directory from the start.
2. **On discovery of misplaced files:** Move the file to the correct directory, then:
   - Log the move to `memory/entropy-fixes.md` (date, old path, new path, reason)
   - **Update clawbot's memory** with the new file location so future lookups reference the correct path. Any skill, doc, or script that was referenced by old path must have its memory entry updated to the new path.
3. **On new file types:** If a file doesn't fit any existing category, ask the user where it belongs before creating it. Do not dump files in the workspace root.
4. **Memory consistency:** After any file move, clawbot must check its memory for references to the old path and update them. Stale path references are a form of entropy too.

### Entropy Fix Log Format

```markdown
## YYYY-MM-DD

- Moved `workspace/some_script.py` → `ops/scripts/some_script.py` — maintenance script was in workspace root
- Moved `workspace/ops/watchdog/README.md` → `ops/docs/watchdog-guide.md` — doc was mixed in with scripts
```

### Why This Matters

- Prevents gradual workspace rot where files accumulate in wrong directories
- Makes it possible to find anything by knowing the structure, not by searching
- Keeps skills isolated and ops tooling organized
- Self-healing: entropy is corrected as it's discovered, not left to accumulate
