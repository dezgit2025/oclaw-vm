# GitHub Copilot Model Configuration for OpenClaw

**Date:** 2026-02-21
**Gateway version:** v2026.2.17

## Model ID Format

OpenClaw uses `github-copilot/<model-id>` format. The model IDs must match the built-in registry — use `openclaw models list --all | grep github-copilot` to see valid IDs.

## Common Mistake

The model ID for Claude Opus 4.6 is `claude-opus-4.6`, **NOT** `copilot-opus-4.6`. The `copilot-` prefix is wrong and will show as `missing` in the registry.

## Available GitHub Copilot Models (v2026.2.17)

From `openclaw models list --all | grep github-copilot`:

| Model ID | Input | Context |
|----------|-------|---------|
| `github-copilot/claude-opus-4.6` | text+image | 125k |
| `github-copilot/claude-opus-4.5` | text+image | 125k |
| `github-copilot/claude-sonnet-4.5` | text+image | 125k |
| `github-copilot/claude-sonnet-4` | text+image | 125k |
| `github-copilot/claude-haiku-4.5` | text+image | 125k |
| `github-copilot/gpt-5.2` | text+image | 125k |
| `github-copilot/gpt-5.2-codex` | text+image | 266k |
| `github-copilot/gpt-5.1-codex-max` | text+image | 125k |
| `github-copilot/gpt-5.1-codex-mini` | text+image | 125k |
| `github-copilot/gpt-5.1-codex` | text+image | 125k |
| `github-copilot/gpt-5.1` | text+image | 125k |
| `github-copilot/gpt-5-mini` | text+image | 125k |
| `github-copilot/gpt-5` | text+image | 125k |
| `github-copilot/gpt-4.1` | text+image | 63k |
| `github-copilot/gpt-4o` | text+image | 63k |
| `github-copilot/gemini-2.5-pro` | text+image | 125k |
| `github-copilot/gemini-3-flash-preview` | text+image | 125k |
| `github-copilot/gemini-3-pro-preview` | text+image | 125k |
| `github-copilot/grok-code-fast-1` | text | 125k |

## Current Config (on VM)

In `~/.openclaw/openclaw.json`:

```json
"agents": {
  "defaults": {
    "model": {
      "primary": "github-copilot/gpt-5.2",
      "fallbacks": ["foundry/gpt-4.1-mini"]
    },
    "models": {
      "github-copilot/gpt-5.2": {},
      "foundry/Kimi-K2.5": {"alias": "KimiHB"},
      "foundry/gpt-4.1-mini": {},
      "github-copilot/claude-opus-4.6": {},
      "github-copilot/gpt-5.3-codex": {},
      "github-copilot/gpt-5.2-codex": {},
      "github-copilot/gemini-3-pro-preview": {},
      "github-copilot/gemini-3.1-pro-preview": {}
    }
  }
}
```

## Config Properties

Model entries in `agents.defaults.models` accept:
- `{}` — empty object (use defaults from registry)
- `{"alias": "Name"}` — custom alias for the model

The `"name"` key is **NOT valid** in v2026.2.17 strict schema — was rejected with `Unrecognized key: "name"`.

## Auth Setup

```bash
openclaw models auth login-github-copilot
openclaw models set github-copilot/claude-opus-4.6
```

## How to Check

```bash
# List configured models
openclaw models list

# List ALL available models in registry
openclaw models list --all | grep github-copilot

# Check if a model is valid
openclaw models list --all | grep claude-opus
```

## Model Registry Source

Model IDs are defined in `src/providers/github-copilot-models.ts` (`DEFAULT_MODEL_IDS` array) in the openclaw source. The dist files are at:
- `/home/desazure/.npm-global/lib/node_modules/openclaw/dist/model-catalog-*.js`

## Fixes Applied (2026-02-21)

| Fix | Details |
|-----|---------|
| Renamed `copilot-opus-4.6` → `claude-opus-4.6` | In both `model.primary` and `models` map |
| Removed `{"name": "..."}` from model entry | v2026.2.17 rejects `name` key |
| Removed `gpt-4.1-mini-2025-04-14` | Not in registry |
| Removed `gpt-4.1-mini` | Not in registry (use `gpt-4.1` instead) |
| Added `gpt-5.3-codex` | `github-copilot/gpt-5.3-codex: {}` — not in registry yet but gateway accepts it |
| Added `gpt-5.2-codex` | `github-copilot/gpt-5.2-codex: {}` — in registry (266k context) |
| Added `gemini-3-pro-preview` | `github-copilot/gemini-3-pro-preview: {}` — in registry (125k context) |
| Added `gemini-3.1-pro-preview` | `github-copilot/gemini-3.1-pro-preview: {}` — not in registry yet, GA on GitHub Copilot |
| Changed primary model (user) | `claude-opus-4.6` → `gpt-5.2`, fallback `gpt-5.2` → `foundry/gpt-4.1-mini` (2026-02-22) |

## GPT-5.3-Codex Status

`gpt-5.3-codex` is **GA for GitHub Copilot** (all tiers) per GitHub docs, but openclaw's built-in registry (v2026.2.17) hasn't added `github-copilot/gpt-5.3-codex` yet — highest codex is `github-copilot/gpt-5.2-codex`. Available via other providers (`openai/gpt-5.3-codex`, `azure-openai-responses/gpt-5.3-codex`).

**Added to gateway config (2026-02-21):** `github-copilot/gpt-5.3-codex: {}` — gateway accepts it without schema error even though it's not in the local registry. Gateway restarted and running stable (PID 80868).

VS Code also has a known bug where gpt-5.3-codex disappears from the model picker dropdown after switching away from it ([VS Code Issue #295438](https://github.com/microsoft/vscode/issues/295438)).

## How Models Were Added — Step-by-Step

### What was edited

| Location | File | What changed |
|----------|------|-------------|
| VM (`oclaw2026linux`) | `/home/desazure/.openclaw/openclaw.json` | Added `"github-copilot/gpt-5.3-codex": {}` to `agents.defaults.models` |

### How the edit was done

```bash
ssh oclaw "python3 -c \"
import json
with open('/home/desazure/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
cfg['agents']['defaults']['models']['github-copilot/gpt-5.3-codex'] = {}
with open('/home/desazure/.openclaw/openclaw.json', 'w') as f:
    json.dump(cfg, f, indent=2)
\""

# Restart gateway
ssh oclaw "python3 /home/desazure/.openclaw/workspace/ops/watchdog/restart_gateway.py"

# Verify stable
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"
```

### Where the correct model names were found

| Source | URL | What it told us |
|--------|-----|-----------------|
| GitHub Docs — Supported Models | https://docs.github.com/en/copilot/reference/ai-models/supported-models | `GPT-5.3-Codex` is GA for all Copilot tiers |
| Neowin article | https://ai505.com/gpt-5-3-codex-is-now-ga-for-github-copilot-here-s-what-changed/ | Confirmed GA rollout date and tier availability |
| `openclaw models list --all` on VM | (local CLI command) | Registry only goes up to `gpt-5.2-codex` — `gpt-5.3-codex` not yet added to openclaw |
| VS Code Issue #295438 | https://github.com/microsoft/vscode/issues/295438 | VS Code model picker also missing gpt-5.3-codex (known bug) |
| MS Learn — Copilot Studio Models | https://learn.microsoft.com/microsoft-copilot-studio/authoring-select-agent-model | GPT-5.2 listed as Experimental; confirmed model naming conventions |

### Config schema rules (v2026.2.17)

| Rule | Detail |
|------|--------|
| Model entry value | Must be `{}` or `{"alias": "Name"}` |
| Invalid keys | `"name"` causes crash (`Unrecognized key`) |
| Unknown model IDs | Accepted — gateway does NOT reject model IDs missing from the built-in registry |
| Model ID format | `github-copilot/<model-name>` where `<model-name>` matches GitHub's naming (e.g., `claude-opus-4.6`, `gpt-5.3-codex`) |

### Laptop files (documentation only, not config)

| File | Path (on Mac) | Purpose |
|------|---------------|---------|
| This doc | `/Users/dez/Projects/openclaw_vm/manage-oclaw/opslog/copilot-model-oclaw-notes.md` | Model configuration reference and change log |
| CLAUDE.md | `/Users/dez/Projects/openclaw_vm/CLAUDE.md` | References this doc in "Gateway Model Configuration" section |

## References

- [OpenClaw GitHub Copilot Provider Docs](https://docs.openclaw.ai/providers/github-copilot)
- [GitHub Copilot Supported Models](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
- [OpenClaw Issue #10091 — Add claude-opus-4.6 support](https://github.com/openclaw/openclaw/issues/10091)
- [OpenClaw Issue #15014 — Update Copilot model list](https://github.com/openclaw/openclaw/issues/15014)
- [Microsoft Learn — Foundry Models (Anthropic)](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-from-partners?view=foundry-classic#anthropic)
- [VS Code AI Language Models Docs](https://code.visualstudio.com/docs/copilot/customization/language-models)
- [VS Code Issue #295438 — GPT-5.3-Codex missing from model picker](https://github.com/microsoft/vscode/issues/295438)
- [Neowin — GitHub Copilot adds GPT-5.3-Codex](https://ai505.com/gpt-5-3-codex-is-now-ga-for-github-copilot-here-s-what-changed/)
- [MS Learn — Copilot Studio Model Selection](https://learn.microsoft.com/microsoft-copilot-studio/authoring-select-agent-model)
