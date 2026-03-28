# Phase 0: Tag Definition Injection

**Status:** Ready to implement
**Effort:** ~30 min
**Cost impact:** +$0.0004/extraction call (negligible)
**Files to modify:** 1 file — `smart_extractor.py` (4 changes)
**Source:** `/Users/dez/Projects/oclaw_brain/update1/smart_extractor.py`
**Deploy to:** VM `~/.openclaw/workspace/skills/clawbot-memory/smart_extractor.py`

---

## Problem

`extract_known_tags()` parses TAG_REGISTRY.md but only extracts **tag names**, not definitions. The LLM sees:
```
TAG REGISTRY (use these, or create new if needed):
  type: decision, pivot, preference, hypothesis, validation, ...
  domain: product, growth, monetization, funding, ...
```

It does NOT see "pivot = reversal of a previous decision" or "validation = hypothesis confirmed or killed". This causes:
- Overuse of safe defaults (`type:context`, `type:insight`)
- Underuse of specific tags (`type:validation`, `type:competitive`)
- Misclassification (e.g., `type:decision` for observations that aren't choices)

## Pre-Check

Run before implementing to confirm the problem:
```bash
ssh oclaw "sqlite3 ~/.claude-memory/memory.db \"SELECT tags, COUNT(*) as c FROM memories WHERE active=1 GROUP BY tags ORDER BY c DESC LIMIT 20\""
```

If `type:context` or `type:insight` dominate (40%+), this fix has high ROI.

---

## Changes (4 edits to smart_extractor.py)

### Change 1: `extract_known_tags()` returns definitions (~line 260-272)

Current:
```python
def extract_known_tags(registry: str) -> dict:
    tags = {}
    dim = None
    for line in registry.split("\n"):
        dm = re.match(r"###\s+`(\w+):`", line)
        if dm:
            dim = dm.group(1)
            tags[dim] = []
        tm = re.match(r"\|\s*`(\w[\w:_-]+\w)`\s*\|", line)
        if tm and dim:
            tags[dim].append(tm.group(1))
    return tags
```

New — returns `dict[str, list[tuple[str, str]]]` (name, definition):
```python
def extract_known_tags(registry: str) -> dict:
    tags = {}
    dim = None
    for line in registry.split("\n"):
        dm = re.match(r"###\s+`(\w+):`", line)
        if dm:
            dim = dm.group(1)
            tags[dim] = []
        # Match: | `tag_name` | definition text | ...
        tm = re.match(r"\|\s*`([\w:_-]+)`\s*\|\s*([^|]+)", line)
        if tm and dim:
            tag_name = tm.group(1).split(":")[-1]  # strip prefix
            definition = tm.group(2).strip().rstrip("|").strip()
            tags[dim].append((tag_name, definition))
    return tags
```

### Change 2: New helper `_get_tag_usage_counts()` (add near line 258)

```python
def _get_tag_usage_counts() -> dict:
    """Count tag usage from SQLite for frequency hints."""
    counts = {}
    try:
        import sqlite3
        db_path = os.path.expanduser("~/.claude-memory/memory.db")
        if not os.path.exists(db_path):
            return counts
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT tags FROM memories WHERE active=1").fetchall()
        conn.close()
        for (tags_str,) in rows:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    counts[tag] = counts.get(tag, 0) + 1
    except Exception:
        pass  # non-critical
    return counts
```

### Change 3: `tag_ref` includes definitions + counts (~line 307-308)

Current:
```python
known = extract_known_tags(load_tag_registry())
tag_ref = "\n".join(f"  {d}: {', '.join(v)}" for d, v in known.items())
```

New:
```python
known = extract_known_tags(load_tag_registry())
tag_counts = _get_tag_usage_counts()
tag_ref_lines = []
for dim, entries in known.items():
    tag_ref_lines.append(f"  {dim}:")
    for name, definition in entries:
        full_tag = f"{dim}:{name}"
        count = tag_counts.get(full_tag, 0)
        count_hint = f" ({count} uses)" if count > 0 else ""
        tag_ref_lines.append(f"    {name}{count_hint} -- {definition}")
tag_ref = "\n".join(tag_ref_lines)
```

### Change 4: Fix callers of `extract_known_tags()` (return type changed)

**`update_tag_registry()` (~line 279-280):**
```python
# Old
for vals in extract_known_tags(registry).values():
    all_known.update(vals)
# New
for entries in extract_known_tags(registry).values():
    all_known.update(name for name, _ in entries)
```

**`store_facts()` (~line 454):**
```python
# Old
for v in extract_known_tags(load_tag_registry()).values():
    all_known.update(v)
# New
for entries in extract_known_tags(load_tag_registry()).values():
    all_known.update(name for name, _ in entries)
```

### Change 5: Tighten prompt wording (~line 321)

```python
# Old
"TAG REGISTRY (use these, or create new if needed):"
# New
"TAG REGISTRY (PREFER these -- only create new if NONE fit):"
```

---

## What the LLM Will See After

Before:
```
TAG REGISTRY (use these, or create new if needed):
  type: decision, pivot, preference, hypothesis, validation, ...
```

After:
```
TAG REGISTRY (PREFER these -- only create new if NONE fit):
  type:
    decision (47 uses) -- A choice made between alternatives
    pivot (8 uses) -- A reversal of a previous decision
    preference (12 uses) -- A stated or inferred preference
    hypothesis -- An untested assumption
    validation -- A hypothesis confirmed or killed
    error_pattern (3 uses) -- A recurring error and its cause
  domain:
    infrastructure (31 uses) -- Cloud, devops, CI/CD, deployment
    ai (22 uses) -- AI features, embeddings, agents, memory
    product (5 uses) -- Core product features, UX, design
```

---

## Testing

### Unit tests (run locally before deploy)

```python
# test_extract_known_tags.py
def test_extracts_names_and_definitions():
    registry = """### `type:` -- What kind?
| Tag | Definition | Example |
|-----|-----------|---------|
| `type:decision` | A choice made between alternatives | "Chose X" |
| `type:pivot` | A reversal of a previous decision | "Switched from X" |
"""
    result = extract_known_tags(registry)
    assert "type" in result
    assert result["type"][0] == ("decision", "A choice made between alternatives")
    assert result["type"][1] == ("pivot", "A reversal of a previous decision")

def test_handles_empty_registry():
    assert extract_known_tags("") == {}

def test_callers_unpack_tuples():
    """Verify update_tag_registry and store_facts still work."""
    known = extract_known_tags(load_tag_registry())
    all_known = set()
    for entries in known.values():
        all_known.update(name for name, _ in entries)
    assert "decision" in all_known
    assert isinstance(all_known.pop(), str)
```

### A/B comparison (on VM, manual)

```bash
# Baseline (current prompt — flat tag list)
python3 smart_extractor.py extract --session SESSION_ID --dry-run > /tmp/baseline.json

# Deploy changes, then run same session
python3 smart_extractor.py extract --session SESSION_ID --dry-run > /tmp/candidate.json

# Compare tag diversity and accuracy
diff <(jq '.[].tags' /tmp/baseline.json) <(jq '.[].tags' /tmp/candidate.json)
```

Look for:
- Less `type:context` / `type:insight` overuse
- More specific tags (`type:validation`, `type:pivot`)
- No increase in invented free-form tags

---

## Deploy Steps

1. Edit `smart_extractor.py` locally (5 changes above)
2. Run unit tests locally
3. `scp` to VM: `scp smart_extractor.py oclaw:~/.openclaw/workspace/skills/clawbot-memory/`
4. SSH in and run A/B test on one session
5. If results look good, let daily cron pick it up (20:15 UTC)
6. Check next day's extraction log for tag distribution shift

---

## Rollback

Revert `smart_extractor.py` to the pre-change version. No schema changes, no index changes, no other files affected.
