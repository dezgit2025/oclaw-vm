# OpenClaw Node — Mac Mini as Remote Coding Worker

**Date:** 2026-02-21
**Status:** Idea / Not implemented
**Version:** 1.0

## Goal

Use the Mac Mini as a native OpenClaw **node** paired with the VM gateway, so coding tasks are delegated to the Mac and executed locally — no MCP token overhead.

## Why Not MCP

MCP is chatty — every file read, every edit, every bash command is a tool-call round-trip that consumes tokens. A node uses native WebSocket dispatch: one command out, one result back.

| Approach | Tokens per coding task |
|----------|----------------------|
| MCP (tool calls) | High — every file read/write/bash is a round-trip with full context |
| Node (native) | Low — command dispatch only, execution is local on Mac |

## Architecture

```
VM (Gateway :18789)  <──WebSocket──  Mac Mini (node host)
     |                                    |
     |  "openclaw nodes run               |  executes locally
     |   --node mac-mini                  |  on Mac filesystem
     |   --raw 'cd /project && git diff'" |
     |                                    |
     └──── result comes back ─────────────┘
```

Network: Tailscale mesh (VM `100.111.79.93` <-> Mac `100.85.14.32`)

## How OpenClaw Nodes Work

A **node** is a headless host that connects to the Gateway via WebSocket and exposes `system.run` / `system.which` on the remote machine. Designed for "run commands on remote Linux/Windows boxes (build servers, lab machines, NAS)."

- Connection: WebSocket to gateway (works over Tailscale)
- Auth: Pairing + approval flow, creds stored in `~/.openclaw/node.json`
- Security: Exec approvals + per-agent allowlists — scoped command access
- Persistence: `openclaw node install` sets up launchd on Mac (auto-starts)

## Setup Steps

### 1. Install openclaw on Mac Mini

```bash
npm install -g openclaw
```

### 2. Run the node host, pointing at VM gateway via Tailscale

```bash
openclaw node run --host 100.111.79.93 --port 18789 --display-name "mac-mini-coder"
```

This generates a pairing request on the VM gateway.

### 3. Approve from VM

```bash
# See pending pairing request
openclaw nodes pending

# Approve it
openclaw nodes approve <requestId>
```

### 4. Install as persistent service (launchd on Mac)

```bash
openclaw node install
```

## Usage Examples

```bash
# Run commands on Mac from the VM
openclaw nodes run --node mac-mini-coder --raw "cd /project && git status"
openclaw nodes run --node mac-mini-coder --cwd /project --raw "npm test"

# Invoke structured commands
openclaw nodes invoke --node mac-mini-coder --command system.run --params '{"cmd":"ls"}'

# Check node status
openclaw nodes status
```

## CLI Reference (from v2026.2.17)

### `openclaw node` (runs ON the Mac)

| Command | Purpose |
|---------|---------|
| `node run` | Run the headless node host (foreground) |
| `node install` | Install as launchd/systemd service |
| `node status` | Show node host status |
| `node stop` | Stop node host service |
| `node restart` | Restart node host service |

### `openclaw nodes` (runs ON the VM gateway)

| Command | Purpose |
|---------|---------|
| `nodes status` | List known nodes with connection status |
| `nodes pending` | List pending pairing requests |
| `nodes approve` | Approve a pairing request |
| `nodes reject` | Reject a pairing request |
| `nodes run` | Run a shell command on a node |
| `nodes invoke` | Invoke a command on a paired node |
| `nodes describe` | Describe a node (capabilities) |
| `nodes rename` | Rename a paired node |

### `openclaw nodes run` options

| Option | Purpose |
|--------|---------|
| `--node <idOrNameOrIp>` | Target node |
| `--raw <command>` | Run a raw shell command string |
| `--cwd <path>` | Working directory on the node |
| `--env <key=val>` | Environment override (repeatable) |
| `--command-timeout <ms>` | Command timeout |
| `--security <mode>` | Exec security mode (deny/allowlist/full) |
| `--ask <mode>` | Exec ask mode (off/on-miss/always) |

## Auth Consideration: Azure AI Foundry

The VM currently authenticates to Azure AI Foundry using **Managed Identity** (IMDS at `169.254.169.254`). This only works on Azure VMs. If the Mac needs Foundry model access directly:

| Method | Works on Mac? | Notes |
|--------|--------------|-------|
| Managed Identity (IMDS) | No | Azure VM only |
| `az login` (DefaultAzureCredential) | Yes | Requires Azure CLI on Mac |
| API Key | Yes | Store in env var |
| Service Principal | Yes | AZURE_CLIENT_ID + SECRET + TENANT_ID |
| GitHub Copilot token | Yes | Same token works on any machine |

For coding tasks via GitHub Copilot models (`claude-opus-4.6`, `gpt-5.2`, etc.), the **GitHub Copilot auth works on any machine** — no Azure dependency.

## Open Questions

1. Can the gateway delegate an entire **agent session** (not just shell commands) to a node?
2. Can a node run `openclaw agent` locally with its own LLM context?
3. How does the skill system interact with nodes — can a skill route to a specific node?
4. What's the latency overhead of WebSocket dispatch over Tailscale?
5. Can we scope the node to only allow coding-related commands (git, npm, python, etc.)?

## Prerequisites

| Item | Status |
|------|--------|
| Tailscale on Mac | Done (`100.85.14.32`) |
| Tailscale on VM | Done (`100.111.79.93`) |
| OpenClaw on VM | Done (v2026.2.17) |
| OpenClaw on Mac | **Not installed** |
| Node pairing | **Not done** |
| GitHub Copilot auth on Mac | **Not tested** |

## Sources

- [OpenClaw Node Docs](https://docs.openclaw.ai/cli/node)
- [OpenClaw Nodes (gateway-side) Docs](https://docs.openclaw.ai/cli/nodes)
- [OpenClaw Multi-Agent Routing](https://docs.openclaw.ai/concepts/multi-agent)
- [OpenClaw Guide (DigitalOcean)](https://www.digitalocean.com/resources/articles/what-is-openclaw)
- [OpenClaw Overview (Medium)](https://medium.com/@gemQueenx/what-is-openclaw-open-source-ai-agent-in-2026-setup-features-8e020db20e5e)
- [GitHub Copilot Supported Models](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
