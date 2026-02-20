---
name: mcp-mslearn
description: Query Microsoft Learn via its MCP server (streamable HTTP) for trusted docs + code samples.
version: 0.1.0
---

Use this when you want trusted Microsoft documentation and code samples, via the Microsoft Learn MCP server.

## Commands

### Search Microsoft docs

Run:

```bash
node /home/desazure/.openclaw/workspace/skills/mcp-mslearn/scripts/mslearn_search.mjs "<query>"
```

### Fetch a specific doc URL

Run:

```bash
node /home/desazure/.openclaw/workspace/skills/mcp-mslearn/scripts/mslearn_fetch.mjs "<url>"
```

### Search code samples

Run:

```bash
node /home/desazure/.openclaw/workspace/skills/mcp-mslearn/scripts/mslearn_code_search.mjs "<query>"
```

## Notes / Safety
- Uses outbound HTTPS only; no inbound ports opened.
- Endpoint: https://learn.microsoft.com/api/mcp (streamable HTTP)
- Tool names may change; scripts call listTools on connect.
