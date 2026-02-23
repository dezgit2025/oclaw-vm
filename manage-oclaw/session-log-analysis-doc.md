# OpenClaw Session Log (.jsonl) Structure Analysis

**Source file:** `c49b5fce-a00e-494a-9d51-7edd1950199b.jsonl` (10 MB, 2,350 entries)
**Session span:** 2026-02-06 04:31 UTC → 2026-02-09 15:33 UTC (~3.5 days)
**Format:** JSONL (one JSON object per line)

---

## File Overview

```
  Session .jsonl file
  ===================

  Line 1:     { "type": "session", ... }           ← header (1 per file)
  Line 2:     { "type": "model_change", ... }       ← config (1 per file)
  Line 3:     { "type": "thinking_level_change" }   ← config (1 per file)
  Line 4:     { "type": "custom", ... }             ← config snapshot (1 per file)
  Line 5:     { "type": "message", role: "user" }   ← conversation starts
  Line 6:     { "type": "message", role: "assistant" }
  Line 7:     { "type": "message", role: "toolResult" }
  ...
  Line 205:   { "type": "compaction", ... }         ← summary checkpoint
  ...
  Line 2350:  { "type": "message", role: "assistant" }
```

---

## Entry Types

| Type | Count | Size | Pct of File | Description |
|------|------:|-----:|------------:|-------------|
| `message` | 2,336 | 9,925 KB | 97.8% | User messages, assistant responses, tool results |
| `compaction` | 10 | 223 KB | 2.2% | Summary checkpoints (append-only, don't remove originals) |
| `session` | 1 | < 1 KB | 0.0% | Session header — ID, version, working directory |
| `model_change` | 1 | < 1 KB | 0.0% | Model switch record |
| `thinking_level_change` | 1 | < 1 KB | 0.0% | Thinking level config |
| `custom` | 1 | < 1 KB | 0.0% | Model snapshot at session start |

---

## Entry Type Schemas

### 1. `session` (header — line 1)

```json
{
  "type": "session",
  "version": 3,
  "id": "c49b5fce-a00e-494a-9d51-7edd1950199b",
  "timestamp": "2026-02-06T04:31:11.769Z",
  "cwd": "/home/desazure/.openclaw/workspace"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | string | Always `"session"` |
| `version` | int | Session format version (currently 3) |
| `id` | string | UUID — unique session identifier |
| `timestamp` | string | ISO 8601 creation time |
| `cwd` | string | Working directory at session start |

---

### 2. `model_change`

```json
{
  "type": "model_change",
  "id": "495320bc",
  "parentId": null,
  "timestamp": "2026-02-06T04:31:11.770Z",
  "provider": "github-copilot",
  "modelId": "gpt-5.2"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | string | Always `"model_change"` |
| `id` | string | Short hex ID for this entry |
| `parentId` | string/null | Previous entry ID (linked list) |
| `timestamp` | string | ISO 8601 |
| `provider` | string | LLM provider name |
| `modelId` | string | Model identifier |

---

### 3. `thinking_level_change`

```json
{
  "type": "thinking_level_change",
  "id": "4fd845bb",
  "parentId": "495320bc",
  "timestamp": "2026-02-06T04:31:11.770Z",
  "thinkingLevel": "low"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `thinkingLevel` | string | Thinking mode: `"low"`, `"medium"`, `"high"` |

---

### 4. `custom` (model snapshot)

```json
{
  "type": "custom",
  "customType": "model-snapshot",
  "data": {
    "timestamp": 1770352271771,
    "provider": "github-copilot",
    "modelApi": "openai-responses",
    "modelId": "gpt-5.2"
  },
  "id": "805ca477",
  "parentId": "4fd845bb",
  "timestamp": "2026-02-06T04:31:11.771Z"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `customType` | string | Sub-type identifier (e.g. `"model-snapshot"`) |
| `data` | object | Payload — varies by `customType` |

---

### 5. `message` (the bulk — 99.4% of entries)

All messages share a common envelope:

```json
{
  "type": "message",
  "id": "96403ee3",
  "parentId": "805ca477",
  "timestamp": "2026-02-06T04:31:11.778Z",
  "message": { ... }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | string | Always `"message"` |
| `id` | string | Short hex ID |
| `parentId` | string | Previous entry ID (forms a linked list) |
| `timestamp` | string | ISO 8601 |
| `message` | object | The actual message payload (varies by role) |

The `message` object has three variants based on `role`:

---

#### 5a. `message.role = "user"` (416 entries, 2.2 MB)

```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "the user's message text..." },
    { "type": "image", "source": { ... } }
  ],
  "timestamp": 1770352271775
}
```

| Key | Type | Description |
|-----|------|-------------|
| `role` | string | `"user"` |
| `content` | array | Content blocks (see Content Types below) |
| `timestamp` | int | Unix epoch ms |

**Size stats:** avg 5.4 KB, max 295 KB, min 0.3 KB

---

#### 5b. `message.role = "assistant"` (1,110 entries, 3.6 MB)

```json
{
  "role": "assistant",
  "content": [
    { "type": "thinking", "thinking": "...", "thinkingSignature": "..." },
    { "type": "text", "text": "assistant's reply..." },
    { "type": "toolCall", "toolCallId": "...", "toolName": "exec", "input": { ... } }
  ],
  "api": "openai-responses",
  "provider": "github-copilot",
  "model": "gpt-5.2",
  "usage": { ... },
  "stopReason": "end_turn",
  "timestamp": 1770352274439
}
```

| Key | Type | Description |
|-----|------|-------------|
| `role` | string | `"assistant"` |
| `content` | array | Content blocks (text, thinking, toolCall) |
| `api` | string | API type used (e.g. `"openai-responses"`) |
| `provider` | string | Provider name (e.g. `"github-copilot"`) |
| `model` | string | Model used (e.g. `"gpt-5.2"`) |
| `usage` | object | Token usage stats |
| `stopReason` | string | Why generation stopped (e.g. `"end_turn"`, `"tool_use"`) |
| `timestamp` | int | Unix epoch ms |

**Size stats:** avg 3.3 KB, max 28 KB, min 0.3 KB

---

#### 5c. `message.role = "toolResult"` (810 entries, 3.9 MB)

```json
{
  "role": "toolResult",
  "toolCallId": "call_RePDYRDzmn3auxJbQ1vynIyX|...",
  "toolName": "exec",
  "content": [
    { "type": "text", "text": "command output here..." }
  ],
  "details": {
    "status": "completed",
    "exitCode": 0,
    "durationMs": 17,
    "aggregated": "command output here...",
    "cwd": "/home/desazure/.openclaw/workspace"
  },
  "isError": false,
  "timestamp": 1770352274457
}
```

| Key | Type | Description |
|-----|------|-------------|
| `role` | string | `"toolResult"` |
| `toolCallId` | string | Links back to the assistant's `toolCall` |
| `toolName` | string | Which tool was called |
| `content` | array | Tool output content blocks |
| `details` | object | Execution metadata (present on 697 of 810) |
| `isError` | bool | Whether the tool call failed |
| `timestamp` | int | Unix epoch ms |

**Size stats:** avg 4.9 KB, max 568 KB, min 0.7 KB
**Note:** Tool results are the largest entries — the top 5 biggest lines in the file are all `toolResult` entries with large command outputs stored verbatim.

---

### 6. `compaction` (10 entries, 223 KB)

```json
{
  "type": "compaction",
  "id": "0eb987ce",
  "parentId": "3c181717",
  "timestamp": "2026-02-06T14:49:12.455Z",
  "summary": "## Goal\n- Change OpenClaw to use...",
  "tokensBefore": 45230,
  "firstKeptEntryId": "96403ee3",
  "fromHook": true,
  "details": {
    "readFiles": [...],
    "modifiedFiles": [...]
  }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | string | Always `"compaction"` |
| `summary` | string | Markdown summary of conversation so far |
| `tokensBefore` | int | Token count before compaction |
| `firstKeptEntryId` | string | ID of earliest entry still in context |
| `fromHook` | bool | Whether compaction was triggered by a hook |
| `details` | object | Files read/modified during the compacted period |

**Summary sizes grew over time:**

| # | Summary Size | Note |
|---|-------------|------|
| 1 | 5.1 KB | First compaction |
| 2 | 10.7 KB | |
| 3 | 17.0 KB | |
| 4 | 19.0 KB | |
| 5 | 17.7 KB | |
| 6 | 21.8 KB | |
| 7 | 18.1 KB | |
| 8 | 25.0 KB | |
| 9 | 32.2 KB | |
| 10 | 34.6 KB | Summaries themselves growing |

**Key problem:** Compaction appends summaries but does NOT remove original entries. The file only grows.

---

## Content Block Types

The `content` array in messages can contain these block types:

| Block Type | Found In | Count | Description |
|------------|----------|------:|-------------|
| `text` | user, assistant, toolResult | 1,655 | Plain text content |
| `toolCall` | assistant | 748 | Tool invocation request |
| `thinking` | assistant | 416 | LLM reasoning (encrypted signature) |
| `image` | user | 29 | Image attachments (screenshots, etc.) |

---

## Tool Usage

| Tool Name | Calls | Description |
|-----------|------:|-------------|
| `exec` | 307 | Shell command execution |
| `process` | 97 | Process management |
| `web_fetch` | 87 | Fetch URL content |
| `web_search` | 72 | Web search (Brave API) |
| `edit` | 65 | Edit file |
| `write` | 59 | Write file |
| `read` | 57 | Read file |
| `gateway` | 20 | Gateway control |
| `cron` | 18 | Cron job management |
| `session_status` | 7 | Session status check |
| `memory_search` | 7 | Search memory |
| `sessions_spawn` | 5 | Spawn sub-sessions |
| `browser` | 4 | Browser control |
| `sessions_history` | 3 | Session history |
| `sessions_list` | 2 | List sessions |

---

## Models & Providers

| Provider | Model | Count |
|----------|-------|------:|
| `github-copilot` | `gpt-5.2` | 1,096 |
| `openclaw` | `delivery-mirror` | 13 |

API: All calls used `openai-responses` (1,109 assistant turns).

---

## Message Role Breakdown

```
  Total messages: 2,336
  =====================

  +------------------+-------+--------+---------+
  | Role             | Count |  Size  |   Pct   |
  +------------------+-------+--------+---------+
  | user             |   416 | 2.2 MB |  17.8%  |
  | assistant        | 1,110 | 3.6 MB |  47.5%  |
  | toolResult       |   810 | 3.9 MB |  34.7%  |
  +------------------+-------+--------+---------+

  Typical conversation turn:
  ==========================

  user (1 msg)
       |
       v
  assistant (1+ msgs)  ←→  toolResult (0+ msgs)
       |                      |
       | text reply            | tool output
       | + toolCall(s)         | (can be huge)
       v                      v
  user (next msg)
```

---

## Size Distribution

| Size Bucket | Entries | Description |
|-------------|--------:|-------------|
| < 1 KB | 692 | Small messages, config entries |
| 1-10 KB | 1,516 | Typical messages |
| 10-50 KB | 119 | Longer responses or tool outputs |
| 50-100 KB | 17 | Large tool outputs |
| > 100 KB | 6 | Very large tool outputs (file contents, API responses) |

### Top 15 Largest Entries

| Line | Size | Type | Note |
|-----:|-----:|------|------|
| 40 | 568 KB | toolResult | Largest single entry |
| 663 | 295 KB | message | |
| 681 | 249 KB | message | |
| 1414 | 199 KB | message | |
| 1534 | 128 KB | message | |
| 740 | 112 KB | message | |
| 2187 | 91 KB | message | |
| 924 | 86 KB | message | |
| 685 | 79 KB | message | |
| 1054 | 78 KB | message | |
| 1602 | 76 KB | message | |
| 1052 | 75 KB | message | |
| 683 | 68 KB | message | |
| 2154 | 65 KB | message | |
| 2152 | 62 KB | message | |

**Top 5 alone = 1,439 KB (1.4 MB) — 14% of the file in just 5 entries.**

---

## Entry Linked List (parentId chain)

Every entry has an `id` and a `parentId` forming a singly-linked list:

```
  session (id: A, parentId: null)
       ↓
  model_change (id: B, parentId: null)
       ↓
  thinking_level_change (id: C, parentId: B)
       ↓
  custom (id: D, parentId: C)
       ↓
  message/user (id: E, parentId: D)
       ↓
  message/assistant (id: F, parentId: E)
       ↓
  message/toolResult (id: G, parentId: F)
       ↓
  message/assistant (id: H, parentId: G)
       ↓
  ...continues for 2,350 entries...
```

This chain preserves ordering and allows branch tracking if the conversation forks.

---

## Why It Grew to 10 MB

```
  Session Start (Feb 6)              Session End (Feb 9)
  ====================               ==================

  4 config entries                    4 config entries
  + ~20 messages                      + 2,336 messages
  + 0 compactions                     + 10 compactions (append-only!)
  = ~8 KB                             = 10 MB

  Growth over 3.5 days:
  =====================

  Day 1 (Feb 6):  ~600 messages   ~2.5 MB
  Day 2 (Feb 7):  ~600 messages   ~5.0 MB
  Day 3 (Feb 8):  ~600 messages   ~7.5 MB
  Day 4 (Feb 9):  ~536 messages   ~10.0 MB  ← OVERFLOW
```

**Contributing factors:**

1. **No session rotation** — single session ran 3.5 days
2. **Compaction doesn't delete** — 10 summaries appended (223 KB) but originals kept
3. **Large tool outputs stored verbatim** — 6 entries > 100 KB each
4. **High tool usage** — 810 toolResult entries, many containing full file contents
5. **Summaries grow** — each compaction summary is larger than the last (5 KB → 35 KB)

---

## File Location

```
VM: ~/.openclaw/agents/main/sessions/{UUID}.jsonl
```

Session index: `VM: ~/.openclaw/agents/main/sessions/sessions.json`

---

## Quick Analysis Commands

```bash
# Count entries by type
ssh oclaw "cat ~/.openclaw/agents/main/sessions/CURRENT.jsonl | python3 -c '
import json, sys; from collections import Counter
c = Counter(json.loads(l).get(\"type\",\"?\") for l in sys.stdin if l.strip())
for t,n in c.most_common(): print(f\"{t}: {n}\")
'"

# Check file size
ssh oclaw "ls -lh ~/.openclaw/agents/main/sessions/*.jsonl"

# Count lines
ssh oclaw "wc -l ~/.openclaw/agents/main/sessions/*.jsonl"

# Find large entries (>50KB per line)
ssh oclaw "awk 'length > 51200 { print NR, length }' ~/.openclaw/agents/main/sessions/CURRENT.jsonl"
```
