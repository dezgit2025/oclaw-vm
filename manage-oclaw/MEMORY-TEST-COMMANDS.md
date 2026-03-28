# Memory System Test Commands

Quick reference for testing the ClawBot memory system on the oclaw VM.
All commands run via SSH from Mac.

**DB Location (VM):** `~/.claude-memory/memory.db`
**CLI Location (VM):** `~/.openclaw/workspace/skills/clawbot-memory/cli/mem.py`
**Smart Extractor (VM):** `~/.openclaw/workspace/skills/clawbot-memory/smart_extractor.py`

---

## Health Dashboard

```bash
# Full 10-metric health check with visual dashboard
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py status"

# Cron one-liner format (for logs)
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py status --log-only"
```

**Passing score:** 7/10 GREEN = HEALTHY

---

## Search & List

```bash
# Search memories by keyword
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py search 'tailscale'"

# Search with more results
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py search 'Azure VM' -k 10"

# List memories by project
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py list"

# List memories for a specific project
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py list -p oclaw-vm"
```

---

## Pin / Unpin

```bash
# Pin a memory (critical = importance 10, important = 9, reference = 8)
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py pin MEM_ID critical"
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py pin MEM_ID important"
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py pin MEM_ID reference"

# Unpin (resets importance to 5)
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py unpin MEM_ID"

# Add a new memory with pin
ssh oclaw "cd ~/.openclaw/workspace/skills/clawbot-memory/cli && python3 mem.py add 'Some important fact' --pin critical -t 'type:fact,domain:infrastructure'"
```

---

## Recall (via smart_extractor — uses Azure AI Search)

```bash
# Recall memories relevant to a topic (hybrid search: BM25 + vector + semantic)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py recall 'Azure VM infrastructure'"

# Recall with more results
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py recall 'Tailscale exit node' -k 5"
```

---

## Extraction (dry-run)

```bash
# Test extraction on a session without storing (dry-run)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py session --path ~/.openclaw/agents/main/sessions/SESSION_ID.jsonl --dry-run"

# Run full extraction sweep (dry-run)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py sweep --dry-run"

# Check extraction state
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py status"
```

---

## Lifecycle

```bash
# Check what stale memories would be deleted (dry-run)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 memory_lifecycle.py --dry-run"

# List permanent memories (for quarterly review)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 -c \"from memory_lifecycle import list_permanent; [print(f'[{r[0]}] ({r[2]}) {r[1]}') for r in list_permanent()]\""
```

---

## Azure AI Search

```bash
# Test Azure search directly
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 -c \"
from memory_bridge import AzureSearchBridge
bridge = AzureSearchBridge()
results = bridge.search('Tailscale exit node', top=3)
for r in results:
    mid = r.get('id', '?')
    score = r.get('@search.score', '?')
    content = r.get('content', '')[:80]
    print(f'  [{mid}] score={score} {content}')
print(f'Total: {len(results)} results')
\""

# Force full sync to Azure
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 memory_bridge.py sync --full"

# Check sync state
ssh oclaw "cat ~/.claude-memory/.sync_state.json"
```

---

## Direct SQLite Queries

```bash
# Count active memories
ssh oclaw "python3 -c \"import sqlite3; c=sqlite3.connect('/home/desazure/.claude-memory/memory.db'); print('Active:', c.execute('SELECT COUNT(*) FROM memories WHERE active=1').fetchone()[0]); c.close()\""

# Tag distribution (top 10)
ssh oclaw "python3 -c \"
import sqlite3
from collections import Counter
c=sqlite3.connect('/home/desazure/.claude-memory/memory.db')
rows=c.execute('SELECT tags FROM memories WHERE active=1').fetchall()
c.close()
tags=Counter()
for r in rows:
    for t in r[0].split(','):
        t=t.strip()
        if t: tags[t]+=1
for tag,count in tags.most_common(10):
    print(f'  {count:3d}  {tag}')
\""

# Find memories with specific tag
ssh oclaw "python3 -c \"
import sqlite3
c=sqlite3.connect('/home/desazure/.claude-memory/memory.db')
rows=c.execute(\\\"SELECT id, substr(content,1,80), tags FROM memories WHERE active=1 AND tags LIKE '%pin:%'\\\").fetchall()
c.close()
for r in rows: print(f'[{r[0]}] ({r[2]}) {r[1]}')
print(f'Found: {len(rows)}')
\""

# Check access counts (which memories are actually being recalled?)
ssh oclaw "python3 -c \"
import sqlite3
c=sqlite3.connect('/home/desazure/.claude-memory/memory.db')
rows=c.execute('SELECT id, access_count, substr(content,1,60) FROM memories WHERE active=1 ORDER BY access_count DESC LIMIT 10').fetchall()
c.close()
for r in rows: print(f'  [{r[0]}] access={r[1]} {r[2]}')
\""
```

---

## Cron Jobs (check status)

```bash
# List all memory-related cron jobs
ssh oclaw "crontab -l | grep -A1 'memory\|Memory\|extract\|sync\|lifecycle'"

# Check health check logs
ssh oclaw "ls -la ~/.openclaw/logs/memory-health/ 2>/dev/null && cat ~/.openclaw/logs/memory-health/\$(date -u +%Y-%m-%d).log 2>/dev/null || echo 'No logs yet'"

# Check lifecycle cleanup logs
ssh oclaw "ls -la ~/.openclaw/logs/memory-lifecycle/ 2>/dev/null"

# Check extraction logs
ssh oclaw "ls -lt ~/claude-memory/logs/ 2>/dev/null | head -5"

# Check sync logs
ssh oclaw "cat ~/claude-memory/logs/sync.log 2>/dev/null | tail -10"
```

---

## Gateway Hook (memory recall injection)

```bash
# Check if memory hook is active
ssh oclaw "openclaw hooks list 2>/dev/null | grep -i memory"

# Test hook directly (simulates what happens on every ClawBot turn)
ssh oclaw "source ~/.bashrc && cd ~/.openclaw/workspace/skills/clawbot-memory && .venv/bin/python3 smart_extractor.py recall 'test query' -k 3"

# Check gateway status
ssh oclaw "systemctl --user status openclaw-gateway.service --no-pager"
```

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| `mem.py` says "not found" | DB path mismatch | Verify `~/.claude-memory/memory.db` exists |
| Recall returns empty | Azure sync may be stale | Run `memory_bridge.py sync --full` |
| Health shows 0% recall rate | access_count not incrementing | Check smart_extractor.py has the increment code |
| Extraction cron not running | Cron job missing | `crontab -l` and verify entries |
| Hook not injecting context | Hook file issue | `openclaw hooks list` and check handler.js |
| Azure search fails | Env vars missing | `echo $AZURE_SEARCH_ENDPOINT` on VM |
