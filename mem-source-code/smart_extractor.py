"""
Smart Memory Extractor v2
==========================
Auto-extracts important facts from ClawBot sessions.
LLM-powered tagging with noise filtering + secrets scrubbing.

TRIGGER MODEL (hybrid):
  SCHEDULED: 2x daily (noon + midnight) — sweep all unprocessed sessions
  EVENT-BASED: fires immediately when session has:
    - >20 tool calls (complex = high signal)
    - >30k tokens consumed (lots of content)
    - context window >80% (flush before overflow)
    - user says "remember this" / "save this"

DEDUP MODEL (cursor + hash):
  - Cursor: tracks last-processed session ID, skips already-extracted
  - Hash: SHA256 of conversation content, safety net against re-processing
  - Semantic dedup: at daily Azure sync, merge memories >0.92 cosine sim

SECURITY:
  - Secrets filter catches API keys, passwords, tokens, connection strings
  - PII filter catches emails, phone numbers, SSNs, credit cards
  - Secrets NEVER stored. Redacted version kept if fact is valuable.

Usage:
  python3 smart_extractor.py sweep                        # scheduled sweep
  python3 smart_extractor.py session --path session.json   # event trigger
  python3 smart_extractor.py extract --text "User chose.." # direct text
  python3 smart_extractor.py sweep --dry-run               # preview
  python3 smart_extractor.py status                        # check state
"""

import os
import re
import json
import glob
import hashlib
import subprocess
import argparse
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("smart_extractor")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
TAG_REGISTRY_PATH = os.path.join(SKILL_DIR, "TAG_REGISTRY.md")
MEM_CLI = os.path.join(SKILL_DIR, "cli", "mem.py")
SESSIONS_DIR = os.path.expanduser("~/.openclaw/logs/sessions")
EXTRACT_STATE_FILE = os.path.expanduser("~/.agent-memory/.extract_state.json")

# Event trigger thresholds
TRIGGER_TOOL_CALLS = 20
TRIGGER_TOKENS = 30_000
TRIGGER_CONTEXT_PCT = 80
TRIGGER_KEYWORDS = [
    "remember this", "save this", "don't forget", "store this",
    "keep this in memory", "note this down",
]


# ====================================================================
# SECRETS & PII FILTER
# ====================================================================

SECRETS_PATTERNS = [
    # API Keys & Tokens
    (r"sk-[a-zA-Z0-9\-_]{20,}", "API_KEY"),
    (r"sk-ant-[a-zA-Z0-9\-_]{20,}", "ANTHROPIC_KEY"),
    (r"sk-proj-[a-zA-Z0-9\-_]{20,}", "OPENAI_KEY"),
    (r"xox[bpas]-[a-zA-Z0-9\-]{10,}", "SLACK_TOKEN"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GITHUB_TOKEN"),
    (r"github_pat_[a-zA-Z0-9_]{20,}", "GITHUB_PAT"),
    (r"gho_[a-zA-Z0-9]{36,}", "GITHUB_OAUTH"),
    (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY"),
    (r"eyJ[a-zA-Z0-9\-_]{20,}\.eyJ[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}", "JWT_TOKEN"),
    (r"bearer\s+[a-zA-Z0-9\-_.~+/]{20,}", "BEARER_TOKEN"),
    (r"token[\"']?\s*[:=]\s*[\"'][a-zA-Z0-9\-_.]{20,}[\"']", "GENERIC_TOKEN"),
    (r"npm_[a-zA-Z0-9]{36}", "NPM_TOKEN"),

    # Azure-specific
    (r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+", "AZURE_CONN_STRING"),
    (r"Endpoint=sb://[^;]+;SharedAccessKeyName=[^;]+;SharedAccessKey=[^;]+", "AZURE_SB_CONN"),
    (r"[a-fA-F0-9]{32,}==", "AZURE_STORAGE_KEY"),
    (r"https://[a-z0-9\-]+\.openai\.azure\.com/[^\s\"']+key=[a-zA-Z0-9]+", "AZURE_OPENAI_URL_KEY"),

    # Passwords & secrets
    (r"password[\"']?\s*[:=]\s*[\"'][^\s\"']{6,}[\"']", "PASSWORD"),
    (r"passwd[\"']?\s*[:=]\s*[\"'][^\s\"']{6,}[\"']", "PASSWORD"),
    (r"secret[\"']?\s*[:=]\s*[\"'][^\s\"']{6,}[\"']", "SECRET"),
    (r"private[_-]?key[\"']?\s*[:=]\s*[\"'][^\s\"']{10,}[\"']", "PRIVATE_KEY"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "PEM_KEY"),
    (r"-----BEGIN\s+CERTIFICATE-----", "CERTIFICATE"),

    # Connection strings
    (r"mongodb(\+srv)?://[^\s\"']+:[^\s\"']+@[^\s\"']+", "MONGODB_URI"),
    (r"postgres(ql)?://[^\s\"']+:[^\s\"']+@[^\s\"']+", "POSTGRES_URI"),
    (r"mysql://[^\s\"']+:[^\s\"']+@[^\s\"']+", "MYSQL_URI"),
    (r"redis://[^\s\"']+:[^\s\"']+@[^\s\"']+", "REDIS_URI"),
    (r"Server=[^;]+;Database=[^;]+;User\s*Id=[^;]+;Password=[^;]+", "SQL_CONN_STRING"),
]

PII_PATTERNS = [
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "EMAIL"),
    (r"\b(\+?1[\-.\s]?)?\(?\d{3}\)?[\-.\s]?\d{3}[\-.\s]?\d{4}\b", "PHONE"),
    (r"\b\d{3}[\-\s]?\d{2}[\-\s]?\d{4}\b", "SSN"),
    (r"\b(?:\d{4}[\-\s]?){3}\d{4}\b", "CREDIT_CARD"),
    (r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b", "INTERNAL_IP"),
]


def scan_secrets(text: str) -> list:
    """Scan for secrets. Returns list of {type, match, start, end}."""
    findings = []
    for pattern, stype in SECRETS_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            findings.append({"type": stype, "match": m.group(), "start": m.start(), "end": m.end()})
    return findings


def scan_pii(text: str) -> list:
    """Scan for PII. Same format."""
    findings = []
    for pattern, ptype in PII_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            findings.append({"type": ptype, "match": m.group(), "start": m.start(), "end": m.end()})
    return findings


def redact_text(text: str, findings: list) -> str:
    """Replace secrets/PII with [REDACTED:TYPE]."""
    for f in sorted(findings, key=lambda x: x["start"], reverse=True):
        text = text[:f["start"]] + f"[REDACTED:{f['type']}]" + text[f["end"]:]
    return text


def is_fact_safe(fact: str) -> tuple:
    """
    Returns (safe: bool, cleaned_fact: str|None, findings: list).
    Secrets → redact, reject if >40% redacted.
    PII → redact, keep fact.
    """
    secrets = scan_secrets(fact)
    pii = scan_pii(fact)

    if secrets:
        redacted = redact_text(fact, secrets + pii)
        redaction_ratio = redacted.count("[REDACTED:") / max(len(redacted.split()), 1)
        if redaction_ratio > 0.4:
            return False, None, secrets
        return True, redacted, secrets

    if pii:
        return True, redact_text(fact, pii), pii

    return True, fact, []


# ====================================================================
# EXTRACTION STATE (cursor + hash dedup)
# ====================================================================

def load_extract_state() -> dict:
    if os.path.exists(EXTRACT_STATE_FILE):
        with open(EXTRACT_STATE_FILE) as f:
            return json.load(f)
    return {
        "last_processed_session_id": None,
        "last_processed_timestamp": None,
        "processed_hashes": {},
        "total_extracted": 0,
        "total_skipped_noise": 0,
        "total_skipped_secrets": 0,
        "total_skipped_dupe": 0,
    }


def save_extract_state(state: dict):
    os.makedirs(os.path.dirname(EXTRACT_STATE_FILE), exist_ok=True)
    # Prune hashes older than 30 days
    cutoff = datetime.now(timezone.utc).timestamp() - (30 * 86400)
    state["processed_hashes"] = {
        h: ts for h, ts in state.get("processed_hashes", {}).items() if ts > cutoff
    }
    with open(EXTRACT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def session_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ====================================================================
# NOISE FILTER
# ====================================================================

NOISE_PATTERNS = [
    r"^(sure|ok|yes|no|thanks|thank you|hey|hi|hello|hmm|got it|sounds good|great|alright)",
    r"^(let me|i'll|i can|i will|i'm going to|looking at|checking|searching)",
    r"^(here's|here is) (the|a|an|my|your) (output|result|response)",
    r"^(sure,?\s)?(let me|i'll|i can)",  # "sure, let me check that"
    r"(```[\s\S]*?```)",
    r"^(error|traceback|exception|warning):",
    r"^\s*[\-\*]\s",
    r"(running|executing|installing|downloading)\s",
    r"^(search|web_search|tool_use|bash_tool)",
    r"^(no problem|of course|absolutely|definitely|certainly)",
    r"^(I think|I believe|I would|it seems|it looks like)\s.{0,20}$",  # short hedging
]

SIGNAL_PATTERNS = [
    (r"(chose|decided|switched to|going with|selected)\s", 0.15),
    (r"(prefer|always use|like to use|rather have)\s", 0.13),
    (r"(uses?|built with|running on|deployed to)\s", 0.12),
    (r"(endpoint|route|api|schema|table|column)\s", 0.12),
    (r"(deadline|due date|milestone|sprint)\s", 0.11),
    (r"(failed|broke|crashed|overflow|timeout)\s", 0.13),
    (r"(improved|reduced|saved|optimized|faster)\s", 0.13),
    (r"(pattern|always|never|rule|convention)\s", 0.12),
    (r"(learned|realized|discovered|turns out)\s", 0.12),
]


def noise_score(text: str) -> float:
    """0.0 = noise, 1.0 = high signal. <0.3 skipped."""
    t = text.lower().strip()
    if len(t) < 10: return 0.0
    if len(t) > 500: return 0.1

    score = 0.5
    for p in NOISE_PATTERNS:
        if re.search(p, t, re.IGNORECASE): score -= 0.2
    for p, boost in SIGNAL_PATTERNS:
        if re.search(p, t, re.IGNORECASE): score += boost

    if re.search(r"\d+(\.\d+)+", text): score += 0.1
    if re.search(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+", text): score += 0.05
    if re.search(r"/[\w/\-\.]+", text): score += 0.05
    if re.search(r"\b(v\d|port \d|\d+ms|\d+%)\b", text): score += 0.1
    if re.match(r"(user|project|team|system|skill|clawbot)", t): score += 0.1

    return max(0.0, min(1.0, score))


# ====================================================================
# TAG REGISTRY I/O
# ====================================================================

def load_tag_registry() -> str:
    if os.path.exists(TAG_REGISTRY_PATH):
        with open(TAG_REGISTRY_PATH) as f:
            return f.read()
    return ""


def extract_known_tags(registry: str) -> dict:
    """Returns dict[dimension, list[tuple[name, definition]]]."""
    tags = {}
    dim = None
    for line in registry.split("\n"):
        dm = re.match(r"###\s+`(\w+):`", line)
        if dm:
            dim = dm.group(1)
            tags[dim] = []
            continue
        tm = re.match(r"\|\s*`(?:[\w]+:)?([\w\-]+)`\s*\|\s*([^|]+)", line)
        if tm and dim:
            tag_name = tm.group(1)
            definition = tm.group(2).strip().rstrip("|").strip()
            tags[dim].append((tag_name, definition))
    return tags


def _get_tag_usage_counts() -> dict:
    """Count tag usage from SQLite for frequency hints."""
    counts = {}
    try:
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
        pass
    return counts


def update_tag_registry(new_tags: list):
    if not new_tags: return
    registry = load_tag_registry()
    all_known = set()
    for entries in extract_known_tags(registry).values():
        all_known.update(name for name, _ in entries)

    truly_new = [t for t in new_tags if ":" in t and t.split(":", 1)[1] not in all_known]
    if not truly_new: return

    lines = registry.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if "| Tag | First seen | Count | Promote? |" in line:
            insert_idx = i + 2
            break
    if insert_idx is None: return

    today = datetime.now().strftime("%Y-%m-%d")
    new_rows = [f"| `{t}` | {today} | 1 | |" for t in truly_new]
    lines = lines[:insert_idx] + new_rows + lines[insert_idx:]
    with open(TAG_REGISTRY_PATH, "w") as f:
        f.write("\n".join(lines))


# ====================================================================
# LLM EXTRACTION + TAGGING
# ====================================================================

def extract_and_tag(conversation_text: str, project: str = None) -> list:
    from auth_provider import get_chat_client

    known = extract_known_tags(load_tag_registry())
    tag_counts = _get_tag_usage_counts()
    # Exclude pin: and permanent: — these are user-applied only, never LLM-assigned
    EXCLUDE_DIMS = {"pin", "permanent"}
    tag_ref_lines = []
    for dim, entries in known.items():
        if dim in EXCLUDE_DIMS:
            continue
        tag_ref_lines.append(f"  {dim}:")
        for name, definition in entries:
            full_tag = f"{dim}:{name}"
            count = tag_counts.get(full_tag, 0)
            count_hint = f" ({count} uses)" if count > 0 else ""
            tag_ref_lines.append(f"    {name}{count_hint} -- {definition}")
    tag_ref = "\n".join(tag_ref_lines)

    today = datetime.now().strftime("%Y-%m-%d")
    week = datetime.now().strftime("%Y-W%V")

    # --- Priority-order the content for LLM ---
    # Instead of naive first-12K truncation, reorder by signal quality
    prioritized = _prioritize_content(conversation_text)

    # --- Chunk if necessary ---
    # Sonnet handles ~16K input well; chunk at 14K to leave room for prompt
    chunks = _chunk_content(prioritized, max_chars=14000)

    all_facts = []
    client = get_chat_client()

    for i, chunk in enumerate(chunks):
        chunk_label = f"(chunk {i+1}/{len(chunks)})" if len(chunks) > 1 else ""

        prompt = f"""You are ClawBot's memory extractor. ClawBot is a cofounder/AI agent
for a startup. Extract facts that build institutional memory.

TODAY: {today} (week {week})
{chunk_label}

CONVERSATION:
{chunk}

TAG REGISTRY (PREFER these -- only create new if NONE fit):
{tag_ref}

EXAMPLES:
<example>
Input: "The VM has 4 vCPU and 16 GiB RAM on Standard_D4s_v3"
Output: {{"reasoning": "Objective infrastructure specification = type:fact, not type:context", "fact": "Azure VM oclaw2026linux runs on Standard_D4s_v3 (4 vCPU / 16 GiB RAM)", "tags": ["type:fact", "domain:infrastructure"], "confidence": 0.95}}
</example>
<example>
Input: "The watchdog runs every 2 minutes via cron"
Output: {{"reasoning": "Recurring operational pattern, not a decision", "fact": "Tailscale exit node watchdog runs every 2 minutes via cron", "tags": ["type:pattern", "domain:ops"], "confidence": 0.9}}
</example>
<example>
Input: "npm audit ENOLOCK — fixed by running npm install first"
Output: {{"reasoning": "Error with specific fix = type:error_pattern", "fact": "npm audit ENOLOCK error — fix by running npm install first", "tags": ["type:error_pattern", "domain:infrastructure", "severity:low"], "confidence": 0.85}}
</example>

SIGNAL PRIORITY (highest → lowest):
- [thinking:] blocks = GOLD — contain reasoning, analysis, cost calculations
- [user:] messages = decisions, corrections, explicit preferences
- [assistant:] = explanations, summaries of actions taken
- [tool:] = what was executed (reveals tech stack, infra decisions)
- Everything else = context

EXTRACT THESE (high value):
- DECISIONS: chose X over Y, with reasoning if stated
- PIVOTS: changed direction from previous decision — flag as type:pivot
- STRATEGY: funding, marketing, growth, monetization, positioning
- PRODUCT: features, UX decisions, user feedback, design choices
- METRICS: any specific numbers, KPIs, cost savings, performance data
- COMPETITIVE: insights about competitors, market positioning
- INVESTOR: feedback from investors, pitch deck changes, valuation
- HYPOTHESES: untested assumptions about users/market ("we believe...")
- VALIDATIONS: data that confirmed or killed a hypothesis
- TECH STACK: tools, frameworks, versions, infra decisions
- ARCHITECTURE: endpoints, schemas, configs, system design, IPs, ports
- OPEN QUESTIONS: decisions still pending, unresolved debates
- TEAM/CONTEXT: deadlines, milestones, team changes, constraints
- ERROR PATTERNS: recurring errors, breaking changes between versions
- COST IMPACTS: any dollar amounts, savings, expenses mentioned

SKIP:
- Greetings, small talk, acknowledgments
- Raw code blocks (extract DECISIONS about code, not code itself)
- Debug output, stack traces
- Routine operational commands ("restart gateway", "check logs") UNLESS
  they reveal a decision or fix a problem worth remembering
- Questions without answers
- Transient actions ("let me search...")

🔒 CRITICAL SECURITY — NEVER EXTRACT:
- API keys, tokens, passwords, secrets of ANY kind
- Connection strings with credentials
- Private keys, certificates
- Email addresses, phone numbers, SSNs, credit cards
- Environment variable VALUES (names ok: "uses AZURE_SEARCH_KEY env var")
- Describe secrets generically:
  ✅ "Project uses Azure OpenAI text-embedding-3-large deployment"
  ❌ "Azure OpenAI key is sk-abc123..."

FORMAT:
- Third person: "Team decided X" or "User prefers X"
- STRICTLY ATOMIC: ONE fact per entry. If you find yourself writing "and" to connect
  two pieces of information, split into two separate entries. Never compress multiple
  facts into one entry — more entries with single facts is always better.
- Specific: versions, numbers, dates, metrics, IPs, costs
- Include a "reasoning" field BEFORE tags explaining why you chose those tags
- Include REASONING when stated: "Chose X over Y because Z"
- For decisions: always include decided:{today} in tags
- For pivots: include decided:{today} and note what it replaces

Return JSON array (no markdown fences):
[
  {{
    "reasoning": "Explicit cost-saving infrastructure decision with specific dollar amount",
    "fact": "Removed Azure Bastion — saves ~$138/month. Tailscale replaces all SSH access",
    "tags": ["type:decision", "domain:infrastructure", "decided:{today}", "status:active", "confidence:high"],
    "confidence": 0.95
  }},
  {{
    "reasoning": "Reversal of a previous monetization decision based on investor input",
    "fact": "Switched monetization from freemium to paid-only after investor feedback",
    "tags": ["type:pivot", "domain:monetization", "decided:{today}", "status:active", "source:investor"],
    "confidence": 0.9,
    "supersedes_search": "freemium monetization"
  }}
]
Return [] if nothing worth extracting."""

        try:
            resp = client.chat.completions.create(
                model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
                max_completion_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            err_str = str(e)
            if "content_filter" in err_str or "content_management_policy" in err_str:
                logger.warning(f"Chunk {i+1} skipped: Azure content filter triggered (jailbreak/policy). Continuing.")
                continue
            raise  # Re-raise non-content-filter errors
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            facts = json.loads(text)
            if isinstance(facts, list):
                all_facts.extend(facts)
        except json.JSONDecodeError:
            logger.error(f"Parse failed on chunk {i+1}: {text[:200]}")

    # Post-process: check for pivots that need contradiction detection
    for item in all_facts:
        tags = item.get("tags", [])
        if "type:pivot" in tags and item.get("supersedes_search"):
            superseded = _find_superseded_memory(item["supersedes_search"])
            if superseded:
                item["_superseded_fact"] = superseded
                tags.append(f"supersedes:{superseded.get('id', 'unknown')}")
                item["_mark_superseded"] = superseded.get("id")

    return all_facts


def _prioritize_content(content: str) -> str:
    """
    Reorder content by signal quality instead of chronological order.

    Priority:
      1. [thinking:] blocks — reasoning, analysis, decisions
      2. [user:] messages — human intent, corrections
      3. [assistant:] responses — trimmed to 200 chars each
      4. [tool:] calls — what was executed
      5. Metadata lines — files modified, session notes
    """
    lines = content.split('\n')

    thinking = []
    user = []
    assistant = []
    tools = []
    metadata = []
    other = []

    for line in lines:
        if not line.strip():
            continue
        if line.startswith('[thinking'):
            thinking.append(line)
        elif line.startswith('[user:'):
            user.append(line)
        elif line.startswith('[assistant:'):
            # Trim verbose assistant responses
            assistant.append(line[:300])
        elif line.startswith('[tool:') and not line.startswith('[tool_'):
            tools.append(line)
        elif line.startswith('[tool_error'):
            thinking.append(line)  # Errors are high signal
        elif line.startswith(('[files_', '[session_', '[background:', '[task:')):
            metadata.append(line)
        else:
            other.append(line[:200])

    # Build priority-ordered output
    sections = []

    if thinking:
        sections.append("=== REASONING (highest signal) ===")
        sections.extend(thinking)

    if user:
        sections.append("\n=== USER MESSAGES ===")
        sections.extend(user)

    if assistant:
        sections.append("\n=== ASSISTANT RESPONSES (trimmed) ===")
        sections.extend(assistant)

    if tools:
        sections.append("\n=== TOOL CALLS ===")
        sections.extend(tools)

    if metadata:
        sections.append("\n=== SESSION METADATA ===")
        sections.extend(metadata)

    return '\n'.join(sections)


def _chunk_content(content: str, max_chars: int = 14000) -> list:
    """
    Split content into chunks for LLM processing.

    Strategy: split at section boundaries (=== headers) or
    at line boundaries if sections are too large.
    """
    if len(content) <= max_chars:
        return [content]

    chunks = []
    current = []
    current_len = 0

    for line in content.split('\n'):
        line_len = len(line) + 1  # +1 for newline

        if current_len + line_len > max_chars and current:
            chunks.append('\n'.join(current))
            current = []
            current_len = 0

        current.append(line)
        current_len += line_len

    if current:
        chunks.append('\n'.join(current))

    return chunks


def _find_superseded_memory(search_query: str) -> dict:
    """Search existing memories for the decision this pivot replaces."""
    cmd = ["python3", MEM_CLI, "search", search_query, "-k", "3"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().split("\n")
            for line in lines:
                # Look for decision-type memories
                if any(kw in line.lower() for kw in ["decided", "chose", "picked", "selected", "going with", "switched to"]):
                    # Try to extract ID if the mem CLI outputs it
                    # Format varies — just return the text for now
                    return {"text": line.strip(), "id": "unknown"}
            # If no decision keyword match, return first result
            if lines:
                return {"text": lines[0].strip(), "id": "unknown"}
    except Exception as e:
        logger.warning(f"Superseded search failed: {e}")
    return None


# ====================================================================
# STORE PIPELINE — 4-gate filter
# ====================================================================

def store_facts(facts: list, project: str = None, dry_run: bool = False) -> dict:
    """
    Gate 1: Noise score (>0.3)
    Gate 2: Secrets/PII scan (redact or reject)
    Gate 3: Confidence (>0.4)
    Gate 4: Dedup (word overlap <60%)
    Gate 5: Contradiction check (for pivots)
    """
    stats = {
        "stored": 0, "skipped_noise": 0, "skipped_secrets": 0,
        "skipped_low_confidence": 0, "skipped_duplicate": 0,
        "redacted_pii": 0, "new_tags": [], "contradictions": [],
    }
    all_known = set()
    for entries in extract_known_tags(load_tag_registry()).values():
        all_known.update(name for name, _ in entries)

    today = datetime.now().strftime("%Y-%m-%d")

    for item in facts:
        fact = item.get("fact", "").strip()
        tags = item.get("tags", [])
        conf = item.get("confidence", 0.5)

        # Gate 1: Noise
        sig = noise_score(fact)
        if sig < 0.3:
            stats["skipped_noise"] += 1
            if dry_run: print(f"  ❌ NOISE ({sig:.2f}): {fact[:80]}")
            continue

        # Gate 2: Secrets/PII
        safe, cleaned, findings = is_fact_safe(fact)
        if not safe:
            stats["skipped_secrets"] += 1
            if dry_run:
                print(f"  🔒 SECRET ({', '.join(f['type'] for f in findings)}): {fact[:50]}...")
            continue
        if cleaned != fact:
            stats["redacted_pii"] += 1
            if dry_run: print(f"  🔏 REDACTED: {fact[:40]}... → {cleaned[:60]}")
            fact = cleaned

        # Gate 3: Confidence
        if conf < 0.4:
            stats["skipped_low_confidence"] += 1
            if dry_run: print(f"  ⚠️  LOW CONF ({conf:.2f}): {fact[:80]}")
            continue

        # Gate 4: Dedup
        if not dry_run and _is_likely_duplicate(fact, project):
            stats["skipped_duplicate"] += 1
            continue

        # --- Ensure temporal tag on decisions ---
        is_decision = any(t in tags for t in ["type:decision", "type:pivot"])
        has_date = any(t.startswith("decided:") for t in tags)
        if is_decision and not has_date:
            tags.append(f"decided:{today}")

        # --- Ensure status:active on new decisions ---
        if is_decision and not any(t.startswith("status:") for t in tags):
            tags.append("status:active")

        # --- Gate 5: Contradiction / Pivot handling ---
        if "type:pivot" in tags:
            superseded = item.get("_superseded_fact")
            if superseded:
                stats["contradictions"].append({
                    "new": fact,
                    "old": superseded.get("text", "unknown"),
                })
                if dry_run:
                    print(f"  🔄 PIVOT: \"{fact[:60]}\"")
                    print(f"       replaces: \"{superseded.get('text', '?')[:60]}\"")
                # TODO: mark old memory as status:superseded via mem CLI
                # This requires mem CLI to support updating tags

        # Track new tags
        for tag in tags:
            if ":" in tag:
                dim, val = tag.split(":", 1)
                if dim in ("decided", "supersedes", "status", "source"):
                    continue  # Dynamic tags, not registered
                if val not in all_known:
                    stats["new_tags"].append(tag)

        if conf < 0.7 and "confidence:low" not in tags:
            tags.append("confidence:low")

        tag_str = ",".join(tags)
        if dry_run:
            emoji = "🔄" if "type:pivot" in tags else "❓" if "type:open_question" in tags else "✅"
            print(f"  {emoji} STORE: \"{fact[:80]}\" [{tag_str}]")
        else:
            _mem_add(fact, tags=tag_str, project=project)
        stats["stored"] += 1

    if stats["new_tags"] and not dry_run:
        update_tag_registry(stats["new_tags"])

    # Print contradiction summary
    if stats["contradictions"]:
        print(f"\n⚠️  CONTRADICTIONS DETECTED ({len(stats['contradictions'])}):")
        for c in stats["contradictions"]:
            print(f"  NEW: {c['new'][:70]}")
            print(f"  OLD: {c['old'][:70]}")
            print()

    return stats


def _mem_add(fact, tags="", project=None):
    cmd = ["python3", MEM_CLI, "add", fact]
    if tags: cmd.extend(["-t", tags])
    if project: cmd.extend(["-p", project])
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as e:
        logger.error(f"mem add: {e}")


def _is_likely_duplicate(fact, project=None):
    words = fact.split()
    q = " ".join(words[:5]) if len(words) > 4 else fact
    cmd = ["python3", MEM_CLI, "search", q, "-k", "3"]
    if project: cmd.extend(["-p", project])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            fw = set(fact.lower().split())
            for line in r.stdout.strip().split("\n"):
                lw = set(line.lower().split())
                if len(fw & lw) / max(len(fw), 1) > 0.6:
                    return True
    except Exception:
        pass
    return False


# ====================================================================
# SESSION LOADING + EVENT TRIGGERS
# ====================================================================

def load_session(path: str) -> dict:
    """
    Parse session file intelligently. Handles:
      - OpenClaw v3 event stream JSONL (type=session/message/model_change/...)
      - OpenClaw v2 event stream JSONL (type=user/assistant/progress/system/...)
      - Standard Anthropic JSONL ({role, content} per line)
      - Single JSON with "messages" array
      - Plain text fallback

    OpenClaw v2 format has top-level 'type' field:
      user      → message.content = string (human) or list (tool_results)
      assistant → message.content = list of {text, thinking, tool_use, tool_result}
      progress  → streaming bash/file output (SKIP)
      system    → turn duration, metadata (telemetry)
      file-history-snapshot → file backups (extract paths only)
      queue-operation → background task results

    OpenClaw v3 format has top-level 'type' field:
      session              → metadata (version, id, cwd)
      message              → .message.role + .message.content (string or [{type,text}])
      model_change         → provider/model change (skip for content)
      thinking_level_change → thinking level change (skip)
      custom               → customType-dependent (model-snapshot, prompt-error, etc.)
      compaction            → context compaction (skip)
    """
    with open(path) as f:
        raw = f.read()
    h = session_hash(raw)

    # Try JSONL first (one JSON per line)
    lines = raw.strip().split("\n")
    events = []
    jsonl_parsed = False
    if len(lines) > 1:
        try:
            events = [json.loads(line) for line in lines if line.strip()]
            jsonl_parsed = True
        except json.JSONDecodeError:
            pass

    # Detect format: OpenClaw v2, OpenClaw v3, or standard
    openclaw_version = None
    if jsonl_parsed and events:
        first = events[0]
        if isinstance(first, dict) and 'type' in first:
            # v3 format: first event is type="session" with version=3,
            # or events use v3 types (message, model_change, etc.)
            if first.get('type') == 'session' or first.get('type') in (
                'message', 'model_change', 'thinking_level_change',
                'custom', 'compaction'
            ):
                openclaw_version = 3
            # v2 format: events use v2 types (user, assistant, etc.)
            elif first.get('type') in (
                'user', 'assistant', 'progress', 'system',
                'file-history-snapshot', 'queue-operation'
            ):
                openclaw_version = 2

    if openclaw_version == 3:
        return _parse_openclaw_v3_session(events, path, h)

    if openclaw_version == 2:
        return _parse_openclaw_session(events, path, h)

    # Standard Anthropic format: try {role, content} at top level
    messages = events if jsonl_parsed else []

    if not jsonl_parsed:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict) and "messages" in data:
                messages = data["messages"]
        except json.JSONDecodeError:
            return {
                "id": os.path.basename(path),
                "content": _scrub_raw_text(raw),
                "hash": h,
                "metadata": {},
                "tool_summary": "",
                "path": path,
            }

    return _parse_standard_messages(messages, path, h)


def _parse_openclaw_session(events: list, path: str, h: str) -> dict:
    """
    Parse OpenClaw event stream JSONL.

    Signal hierarchy:
      1. THINKING blocks (highest signal — reasoning, decisions)
      2. User human text (requests, corrections, decisions)
      3. Assistant text (responses, explanations)
      4. Tool calls (what was invoked — decisions)
      5. File changes (what files were modified)
      6. System metadata (duration, model, tokens)

    Skip:
      - progress events (streaming bash output)
      - tool_result content (bulk output)
      - tool_results passed back as user messages
      - <local-command>, <task-notification> prefixed strings
    """
    extractable = []
    tool_summary = []
    secrets_found = []
    metadata = {
        "format": "openclaw",
        "total_events": len(events),
        "tool_calls": 0,
        "thinking_blocks": 0,
        "context_overflows": 0,
        "models_used": set(),
        "total_duration_ms": 0,
        "files_modified": [],
        "token_usage": {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0},
    }

    session_id = None
    cwd = None

    for event in events:
        if not isinstance(event, dict):
            continue

        etype = event.get("type", "")

        # Grab session metadata from first event
        if not session_id:
            session_id = event.get("sessionId")
            cwd = event.get("cwd")

        # ── USER EVENTS ──────────────────────────────────────────
        if etype == "user":
            msg = event.get("message", {})
            content = msg.get("content", "")
            ts = event.get("timestamp", "")
            time_str = ts[11:16] if len(ts) > 16 else ""

            if isinstance(content, str) and content.strip():
                text = content.strip()

                # Skip tool_results flowing back as user messages
                if text.startswith("<tool_result") or text.startswith("<function_result"):
                    continue

                # Skip local command outputs
                if text.startswith("<local-command"):
                    continue

                # Detect context overflow continuations
                if "continued from a previous conversation" in text:
                    metadata["context_overflows"] += 1
                    # Still extract — the summary often contains key context
                    cleaned = _clean_message_text(text[:2000])
                    if cleaned:
                        extractable.append(f"[user:{time_str}] [CONTEXT OVERFLOW CONTINUATION] {cleaned}")
                    continue

                # Skip task notifications (background job results)
                if text.startswith("<task-notification"):
                    # Extract just the summary
                    import re as _re
                    summary = _re.search(r'<summary>(.*?)</summary>', text)
                    if summary:
                        extractable.append(f"[task:{time_str}] {summary.group(1)}")
                    continue

                # Normal human text — HIGH SIGNAL
                cleaned = _clean_message_text(text)
                if cleaned:
                    extractable.append(f"[user:{time_str}] {cleaned}")

            elif isinstance(content, list):
                # Tool results being sent back — SKIP bulk output
                # But check for secrets in the output
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_output = str(block.get("content", ""))
                        secs = scan_secrets(tool_output)
                        if secs:
                            secrets_found.extend(secs)

        # ── ASSISTANT EVENTS ─────────────────────────────────────
        elif etype == "assistant":
            msg = event.get("message", {})
            content = msg.get("content", [])
            model = msg.get("model", "")
            usage = msg.get("usage", {})
            ts = event.get("timestamp", "")
            time_str = ts[11:16] if len(ts) > 16 else ""

            if model:
                metadata["models_used"].add(model)

            # Accumulate token usage
            if usage:
                metadata["token_usage"]["input"] += usage.get("input_tokens", 0)
                metadata["token_usage"]["output"] += usage.get("output_tokens", 0)
                metadata["token_usage"]["cache_read"] += usage.get("cache_read_input_tokens", 0)
                cache_create = usage.get("cache_creation_input_tokens", 0)
                # Also check nested cache_creation object
                cc = usage.get("cache_creation", {})
                if isinstance(cc, dict):
                    cache_create += sum(v for v in cc.values() if isinstance(v, int))
                metadata["token_usage"]["cache_create"] += cache_create

            if isinstance(content, str) and content.strip():
                cleaned = _clean_message_text(content)
                if cleaned:
                    extractable.append(f"[assistant:{time_str}] {cleaned}")
                continue

            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")

                if btype == "thinking":
                    # HIGHEST SIGNAL — reasoning, analysis, decisions
                    thinking = block.get("thinking", "")
                    metadata["thinking_blocks"] += 1
                    if thinking and len(thinking) > 50:
                        # Trim very long thinking blocks but keep the reasoning
                        trimmed = thinking[:1500]
                        cleaned = _clean_message_text(trimmed)
                        if cleaned:
                            extractable.append(f"[thinking:{time_str}] {cleaned}")

                elif btype == "text":
                    text = block.get("text", "")
                    cleaned = _clean_message_text(text)
                    if cleaned:
                        extractable.append(f"[assistant:{time_str}] {cleaned}")

                elif btype == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    metadata["tool_calls"] += 1
                    input_summary = _summarize_tool_input(tool_name, tool_input)
                    tool_line = f"[tool:{time_str}] {tool_name}({input_summary})"
                    tool_summary.append(tool_line)
                    extractable.append(tool_line)

                elif btype == "tool_result":
                    # Tool output — summarize briefly, scan for secrets
                    tool_output = str(block.get("content", ""))
                    secs = scan_secrets(tool_output)
                    if secs:
                        secrets_found.extend(secs)
                        tool_output = redact_text(tool_output, secs)
                    piis = scan_pii(tool_output)
                    if piis:
                        tool_output = redact_text(tool_output, piis)

                    is_error = block.get("is_error", False)
                    if is_error:
                        err_summary = _summarize_tool_output(tool_output, max_len=300)
                        extractable.append(f"[tool_error:{time_str}] {err_summary}")
                        tool_summary.append(f"  ERROR: {err_summary[:150]}")
                    else:
                        out_summary = _summarize_tool_output(tool_output, max_len=200)
                        if out_summary:
                            tool_summary.append(f"  result: {out_summary[:100]}")

        # ── SYSTEM EVENTS ────────────────────────────────────────
        elif etype == "system":
            duration = event.get("durationMs", 0)
            metadata["total_duration_ms"] += duration

        # ── FILE HISTORY SNAPSHOTS ───────────────────────────────
        elif etype == "file-history-snapshot":
            snap = event.get("snapshot", {})
            backups = snap.get("trackedFileBackups", {})
            if isinstance(backups, dict):
                for filepath in backups.keys():
                    if filepath not in metadata["files_modified"]:
                        metadata["files_modified"].append(filepath)

        # ── QUEUE OPERATIONS ─────────────────────────────────────
        elif etype == "queue-operation":
            op_content = event.get("content", "")
            if isinstance(op_content, str) and "<summary>" in op_content:
                import re as _re
                summary = _re.search(r'<summary>(.*?)</summary>', op_content)
                if summary:
                    ts = event.get("timestamp", "")
                    time_str = ts[11:16] if len(ts) > 16 else ""
                    extractable.append(f"[background:{time_str}] {summary.group(1)}")

        # ── PROGRESS EVENTS ──────────────────────────────────────
        # elif etype == "progress":
        #     SKIP entirely — streaming bash output noise

    # Convert set to list for JSON serialization
    metadata["models_used"] = list(metadata["models_used"])

    sid = session_id or os.path.basename(path)

    if secrets_found:
        logger.warning(
            f"Session {sid}: found {len(secrets_found)} secrets in tool outputs "
            f"(types: {', '.join(set(s['type'] for s in secrets_found))}). "
            f"These were in raw tool output and have been discarded."
        )

    # Add metadata summary to extractable for LLM context
    if metadata["files_modified"]:
        file_list = ", ".join(os.path.basename(f) for f in metadata["files_modified"][:10])
        extractable.append(f"[files_modified] {file_list}")

    if metadata["context_overflows"]:
        extractable.append(f"[session_note] {metadata['context_overflows']} context overflow(s) occurred")

    return {
        "id": sid,
        "content": "\n".join(extractable),
        "hash": h,
        "metadata": metadata,
        "tool_summary": "\n".join(tool_summary),
        "secrets_in_tools": len(secrets_found),
        "path": path,
    }


def _parse_openclaw_v3_session(events: list, path: str, h: str) -> dict:
    """
    Parse OpenClaw v3 event stream JSONL.

    v3 format differences from v2:
      - First event is type="session" (metadata: version, id, cwd)
      - Messages are type="message" with .message.role and .message.content
      - Content is always a list of {type:"text", text:"..."} or {type:"toolCall", ...}
      - Tool calls use type="toolCall" with .name and .arguments (not tool_use/input)
      - Usage uses camelCase: cacheRead, cacheWrite (not cache_read_input_tokens)
      - Model/provider are on the message object directly
      - Other event types: model_change, thinking_level_change, custom, compaction
    """
    extractable = []
    tool_summary = []
    secrets_found = []
    metadata = {
        "format": "openclaw_v3",
        "total_events": len(events),
        "tool_calls": 0,
        "thinking_blocks": 0,
        "context_overflows": 0,
        "models_used": set(),
        "total_duration_ms": 0,
        "files_modified": [],
        "token_usage": {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0},
    }

    session_id = None
    cwd = None

    for event in events:
        if not isinstance(event, dict):
            continue

        etype = event.get("type", "")

        # ── SESSION METADATA ──────────────────────────────────────
        if etype == "session":
            session_id = event.get("id")
            cwd = event.get("cwd")
            continue

        # ── MODEL/THINKING CHANGES ────────────────────────────────
        if etype in ("model_change", "thinking_level_change", "compaction"):
            continue

        # ── CUSTOM EVENTS ─────────────────────────────────────────
        if etype == "custom":
            custom_type = event.get("customType", "")
            # model-snapshot: extract model info
            if custom_type == "model-snapshot":
                data = event.get("data", {})
                model = data.get("modelId", "")
                if model:
                    metadata["models_used"].add(model)
            # prompt-error: note but skip content extraction
            # Other custom types: skip
            continue

        # ── MESSAGE EVENTS ────────────────────────────────────────
        if etype != "message":
            continue

        msg = event.get("message", {})
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        content = msg.get("content", "")
        model = msg.get("model", "")
        usage = msg.get("usage", {})
        ts = event.get("timestamp", "")
        time_str = ts[11:16] if len(ts) > 16 else ""

        if model:
            metadata["models_used"].add(model)

        # Accumulate token usage (v3 uses camelCase)
        if usage and isinstance(usage, dict):
            metadata["token_usage"]["input"] += usage.get("input", 0)
            metadata["token_usage"]["output"] += usage.get("output", 0)
            metadata["token_usage"]["cache_read"] += usage.get("cacheRead", 0)
            metadata["token_usage"]["cache_create"] += usage.get("cacheWrite", 0)

        # --- Extract text from content ---
        # Content can be a string or a list of {type, text/...} blocks
        if isinstance(content, str) and content.strip():
            text = content.strip()
            if role in ("user", "human"):
                # Skip tool results flowing back
                if text.startswith("<tool_result") or text.startswith("<function_result"):
                    continue
                if text.startswith("<local-command"):
                    continue
                # Detect context overflow
                if "continued from a previous conversation" in text:
                    metadata["context_overflows"] += 1
                    cleaned = _clean_message_text(text[:2000])
                    if cleaned:
                        extractable.append(f"[user:{time_str}] [CONTEXT OVERFLOW CONTINUATION] {cleaned}")
                    continue
                if text.startswith("<task-notification"):
                    summary = re.search(r'<summary>(.*?)</summary>', text)
                    if summary:
                        extractable.append(f"[task:{time_str}] {summary.group(1)}")
                    continue
                cleaned = _clean_message_text(text)
                if cleaned:
                    extractable.append(f"[user:{time_str}] {cleaned}")
            elif role == "assistant":
                cleaned = _clean_message_text(text)
                if cleaned:
                    extractable.append(f"[assistant:{time_str}] {cleaned}")

        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")

                if btype == "text":
                    text = block.get("text", "")
                    if not text or not text.strip():
                        continue

                    if role in ("user", "human"):
                        text = text.strip()
                        if text.startswith("<tool_result") or text.startswith("<function_result"):
                            continue
                        if text.startswith("<local-command"):
                            continue
                        if "continued from a previous conversation" in text:
                            metadata["context_overflows"] += 1
                            cleaned = _clean_message_text(text[:2000])
                            if cleaned:
                                extractable.append(f"[user:{time_str}] [CONTEXT OVERFLOW CONTINUATION] {cleaned}")
                            continue
                        if text.startswith("<task-notification"):
                            summary = re.search(r'<summary>(.*?)</summary>', text)
                            if summary:
                                extractable.append(f"[task:{time_str}] {summary.group(1)}")
                            continue
                        cleaned = _clean_message_text(text)
                        if cleaned:
                            extractable.append(f"[user:{time_str}] {cleaned}")

                    elif role == "assistant":
                        cleaned = _clean_message_text(text)
                        if cleaned:
                            extractable.append(f"[assistant:{time_str}] {cleaned}")

                elif btype == "thinking":
                    # Thinking blocks (if present with thinking-capable models)
                    thinking = block.get("thinking", "")
                    metadata["thinking_blocks"] += 1
                    if thinking and len(thinking) > 50:
                        trimmed = thinking[:1500]
                        cleaned = _clean_message_text(trimmed)
                        if cleaned:
                            extractable.append(f"[thinking:{time_str}] {cleaned}")

                elif btype == "toolCall":
                    # v3 tool calls: {type:"toolCall", name:"...", arguments:{...}}
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("arguments", {})
                    metadata["tool_calls"] += 1
                    input_summary = _summarize_tool_input(tool_name, tool_input)
                    tool_line = f"[tool:{time_str}] {tool_name}({input_summary})"
                    tool_summary.append(tool_line)
                    extractable.append(tool_line)

                elif btype == "tool_use":
                    # v2-style tool_use blocks (in case v3 mixes formats)
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    metadata["tool_calls"] += 1
                    input_summary = _summarize_tool_input(tool_name, tool_input)
                    tool_line = f"[tool:{time_str}] {tool_name}({input_summary})"
                    tool_summary.append(tool_line)
                    extractable.append(tool_line)

                elif btype == "tool_result":
                    # Tool output — summarize briefly, scan for secrets
                    tool_output = str(block.get("content", ""))
                    secs = scan_secrets(tool_output)
                    if secs:
                        secrets_found.extend(secs)
                        tool_output = redact_text(tool_output, secs)
                    piis = scan_pii(tool_output)
                    if piis:
                        tool_output = redact_text(tool_output, piis)
                    is_error = block.get("is_error", False)
                    if is_error:
                        err_summary = _summarize_tool_output(tool_output, max_len=300)
                        extractable.append(f"[tool_error:{time_str}] {err_summary}")
                        tool_summary.append(f"  ERROR: {err_summary[:150]}")
                    else:
                        out_summary = _summarize_tool_output(tool_output, max_len=200)
                        if out_summary:
                            tool_summary.append(f"  result: {out_summary[:100]}")

    # Convert set to list for JSON serialization
    metadata["models_used"] = list(metadata["models_used"])

    sid = session_id or os.path.basename(path)

    if secrets_found:
        logger.warning(
            f"Session {sid}: found {len(secrets_found)} secrets in tool outputs "
            f"(types: {', '.join(set(s['type'] for s in secrets_found))}). "
            f"These were in raw tool output and have been discarded."
        )

    # Add metadata summary to extractable for LLM context
    if metadata["files_modified"]:
        file_list = ", ".join(os.path.basename(f) for f in metadata["files_modified"][:10])
        extractable.append(f"[files_modified] {file_list}")

    if metadata["context_overflows"]:
        extractable.append(f"[session_note] {metadata['context_overflows']} context overflow(s) occurred")

    return {
        "id": sid,
        "content": "\n".join(extractable),
        "hash": h,
        "metadata": metadata,
        "tool_summary": "\n".join(tool_summary),
        "secrets_in_tools": len(secrets_found),
        "path": path,
    }


def _parse_standard_messages(messages: list, path: str, h: str) -> dict:
    """Parse standard Anthropic format: [{role, content}, ...]"""
    extractable = []
    tool_summary = []
    secrets_found = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        content = msg.get("content", "")

        # Handle content that's a list of blocks (Anthropic format)
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")

                if btype == "text":
                    # Assistant or user text — extractable
                    text = block.get("text", "")
                    cleaned = _clean_message_text(text)
                    if cleaned:
                        extractable.append(f"[{role}] {cleaned}")

                elif btype == "tool_use":
                    # Tool invocation — KEEP as signal (what was called + why)
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    input_summary = _summarize_tool_input(tool_name, tool_input)
                    tool_line = f"[tool] {tool_name}({input_summary})"
                    tool_summary.append(tool_line)
                    # Tool calls ARE extractable — they reveal decisions
                    extractable.append(tool_line)

                elif btype == "tool_result":
                    # Tool output — SUMMARIZE, don't dump raw
                    tool_output = str(block.get("content", ""))

                    # Scan for secrets in raw output (discard, never store)
                    secs = scan_secrets(tool_output)
                    if secs:
                        secrets_found.extend(secs)
                        tool_output = redact_text(tool_output, secs)

                    # Scan PII in tool output too
                    piis = scan_pii(tool_output)
                    if piis:
                        tool_output = redact_text(tool_output, piis)

                    is_error = block.get("is_error", False)

                    if is_error:
                        # Errors are HIGH signal — keep first 300 chars
                        err_summary = _summarize_tool_output(tool_output, max_len=300)
                        result_line = f"[tool_error] {err_summary}"
                        extractable.append(result_line)
                        tool_summary.append(f"  ERROR: {err_summary[:150]}")
                    else:
                        # Success — keep brief summary (first 200 chars)
                        # Skip bulk output (pip logs, full files, HTML)
                        out_summary = _summarize_tool_output(tool_output, max_len=200)
                        if out_summary:
                            result_line = f"[tool_result] {out_summary}"
                            extractable.append(result_line)
                            tool_summary.append(f"  result: {out_summary[:100]}")

                # Skip: image blocks, document blocks, etc.

        elif isinstance(content, str):
            # Simple string content
            if role in ("user", "human"):
                cleaned = _clean_message_text(content)
                if cleaned:
                    extractable.append(f"[user] {cleaned}")
            elif role in ("assistant",):
                cleaned = _clean_message_text(content)
                if cleaned:
                    extractable.append(f"[assistant] {cleaned}")
            # Skip system messages — they're the prompt, not facts

    # Build session ID
    sid = os.path.basename(path)
    for msg in messages[:3]:
        if isinstance(msg, dict):
            for key in ("session_id", "id", "sessionId"):
                if msg.get(key):
                    sid = msg[key]
                    break

    # Log secrets found in tool outputs (never stored, just awareness)
    if secrets_found:
        logger.warning(
            f"Session {sid}: found {len(secrets_found)} secrets in tool outputs "
            f"(types: {', '.join(set(s['type'] for s in secrets_found))}). "
            f"These were in raw tool output and have been discarded."
        )

    return {
        "id": sid,
        "content": "\n".join(extractable),
        "hash": h,
        "metadata": {"format": "standard"},
        "tool_summary": "\n".join(tool_summary),
        "secrets_in_tools": len(secrets_found),
        "path": path,
    }


def _clean_message_text(text: str) -> str:
    """
    Clean a message for extraction. Removes:
    - Code blocks (keep the comment/description before them)
    - Inline tool references
    - Raw JSON/XML blobs
    - URLs (keep domain only for context)
    """
    if not text or not text.strip():
        return ""

    cleaned = text

    # Remove code blocks but keep the line before (often describes the decision)
    cleaned = re.sub(r"```[\s\S]*?```", "[code block removed]", cleaned)

    # Remove large JSON blobs (>200 chars of JSON-looking content)
    cleaned = re.sub(r"\{[^{}]{200,}\}", "[JSON removed]", cleaned)

    # Remove XML/HTML blocks
    cleaned = re.sub(r"<[a-zA-Z][^>]*>[\s\S]{100,}?</[a-zA-Z]+>", "[markup removed]", cleaned)

    # Remove base64 data
    cleaned = re.sub(r"[A-Za-z0-9+/]{50,}={0,2}", "[base64 removed]", cleaned)

    # Simplify URLs: keep domain only
    cleaned = re.sub(
        r"https?://([a-zA-Z0-9\-.]+)[^\s\"']*",
        r"[url:\1]",
        cleaned
    )

    # Remove raw file paths that look like tool output
    cleaned = re.sub(r"(/[a-zA-Z0-9_\-./]+){4,}", "[path removed]", cleaned)

    # Collapse multiple newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Skip if what's left is too short to be useful
    stripped = cleaned.strip()
    if len(stripped) < 15:
        return ""

    # Final secrets scan on cleaned text
    secs = scan_secrets(stripped)
    if secs:
        stripped = redact_text(stripped, secs)

    return stripped


def _summarize_tool_input(tool_name: str, tool_input: dict) -> str:
    """
    Create a brief summary of tool input for metadata.
    Never includes full content — just enough to know what was done.
    """
    if not isinstance(tool_input, dict):
        return ""

    # Common tool patterns
    if tool_name in ("web_search", "search"):
        return tool_input.get("query", "")[:80]
    if tool_name in ("bash_tool", "bash"):
        cmd = tool_input.get("command", "")[:100]
        return cmd
    if tool_name in ("read", "view", "cat"):
        return tool_input.get("path", tool_input.get("file", ""))[:80]
    if tool_name in ("write", "create_file", "edit", "str_replace"):
        path = tool_input.get("path", tool_input.get("file", ""))[:80]
        desc = tool_input.get("description", "")[:60]
        return f"{path} — {desc}" if desc else path
    if tool_name in ("memory_store", "mem_add"):
        # Keep the fact being stored — that IS the signal
        content = tool_input.get("content", tool_input.get("fact", ""))[:100]
        tags = tool_input.get("tags", "")
        return f"\"{content}\" tags={tags}" if tags else f"\"{content}\""
    if tool_name in ("memory_search", "mem_search"):
        return tool_input.get("query", "")[:80]
    if tool_name in ("web_fetch", "fetch"):
        return tool_input.get("url", "")[:100]

    # Generic: show keys + brief values
    parts = []
    for k, v in list(tool_input.items())[:4]:
        vs = str(v)[:40]
        parts.append(f"{k}={vs}")
    return ", ".join(parts)


def _summarize_tool_output(output: str, max_len: int = 200) -> str:
    """
    Summarize tool output: keep signal, discard bulk.

    KEEP:
      - First meaningful lines (decisions, results, status)
      - Error messages
      - Short outputs (<max_len) verbatim

    DISCARD:
      - pip install logs (hundreds of lines of "Downloading...")
      - Full file contents from `view` or `cat`
      - Raw HTML from web_fetch
      - Long JSON API responses
      - Repeated patterns (log lines)
    """
    if not output or not output.strip():
        return ""

    text = output.strip()

    # If short enough, keep it (after cleaning)
    if len(text) <= max_len:
        # Still remove code blocks and JSON blobs
        text = re.sub(r"```[\s\S]*?```", "[code]", text)
        text = re.sub(r"\{[^{}]{100,}\}", "[json]", text)
        return text.strip()

    # --- Detect and discard known bulk patterns ---

    # pip install output
    if re.search(r"(Downloading|Collecting|Installing collected|Successfully installed)", text[:1000]):
        installed = re.findall(r"Successfully installed (.+)", text)
        if installed:
            return f"pip installed: {installed[-1][:max_len]}"
        collecting = re.findall(r"Collecting (\S+)", text)
        if collecting:
            return f"pip installing: {', '.join(set(collecting))[:max_len]}"
        return f"pip output ({len(text)} chars)"

    # npm install output
    if re.search(r"(added \d+ packages|npm warn|npm notice)", text[:500]):
        added = re.findall(r"added (\d+) packages", text)
        if added:
            return f"npm installed {added[-1]} packages"
        return f"npm install output ({len(text)} chars)"

    # Raw HTML
    if re.search(r"<html|<!DOCTYPE|<head|<body", text[:200], re.IGNORECASE):
        title = re.findall(r"<title>(.*?)</title>", text, re.IGNORECASE)
        return f"HTML page: {title[0][:80]}" if title else f"HTML content ({len(text)} chars)"

    # Large JSON
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                keys = list(parsed.keys())[:5]
                return f"JSON object with keys: {', '.join(keys)}"
            elif isinstance(parsed, list):
                return f"JSON array with {len(parsed)} items"
        except json.JSONDecodeError:
            pass

    # File content dump (lots of code-like lines)
    lines = text.split("\n")
    if len(lines) > 20:
        code_lines = sum(1 for l in lines if re.match(r"^\s*(def |class |import |from |#|//|/\*|\*)", l))
        if code_lines > len(lines) * 0.3:
            return f"code file ({len(lines)} lines, {code_lines} code lines)"

    # Generic: first N chars + truncation marker
    first_part = text[:max_len].rsplit(" ", 1)[0]  # don't cut mid-word
    return f"{first_part}... [{len(text)} chars total]"


def _scrub_raw_text(text: str) -> str:
    """For plain text sessions, do a basic scrub before extraction."""
    # Remove obvious code blocks
    text = re.sub(r"```[\s\S]*?```", "[code removed]", text)
    # Remove large JSON
    text = re.sub(r"\{[^{}]{200,}\}", "[JSON removed]", text)
    # Scan and redact secrets
    secs = scan_secrets(text)
    if secs:
        text = redact_text(text, secs)
    pii = scan_pii(text)
    if pii:
        text = redact_text(text, pii)
    return text


def should_trigger_event(meta: dict) -> tuple:
    """Check event trigger thresholds. Returns (trigger: bool, reasons: list)."""
    reasons = []
    invocations = meta.get("skill_invocations", [])
    tc = sum(s.get("tool_calls", 0) for s in invocations)
    if tc > TRIGGER_TOOL_CALLS:
        reasons.append(f"tool_calls={tc}")

    tokens = meta.get("total_tokens", meta.get("total_tokens_in", 0) + meta.get("total_tokens_out", 0))
    if tokens > TRIGGER_TOKENS:
        reasons.append(f"tokens={tokens}")

    ctx = meta.get("context_window_peak_pct", 0)
    if ctx > TRIGGER_CONTEXT_PCT:
        reasons.append(f"context={ctx}%")

    content = meta.get("content", "")
    if isinstance(content, str):
        cl = content.lower()
        for kw in TRIGGER_KEYWORDS:
            if kw in cl:
                reasons.append(f"keyword='{kw}'")
                break

    return bool(reasons), reasons


def get_unprocessed_sessions(state: dict) -> list:
    if not os.path.isdir(SESSIONS_DIR): return []
    hashes = state.get("processed_hashes", {})
    sessions = []
    for path in sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json"))):
        s = load_session(path)
        if s["hash"] not in hashes:
            sessions.append(s)
    return sessions


# ====================================================================
# COMMANDS
# ====================================================================

def cmd_sweep(dry_run=False, project=None):
    state = load_extract_state()
    print(f"{'=' * 60}")
    print(f"🧬 EXTRACTION SWEEP — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}")

    sessions = get_unprocessed_sessions(state)
    print(f"\n📥 {len(sessions)} unprocessed sessions")
    if not sessions:
        print("  Nothing to process.")
        return

    totals = {k: 0 for k in ["sessions", "stored", "noise", "secrets", "low_conf", "dupe", "pii"]}
    new_tags = []

    for s in sessions:
        print(f"\n📄 Session: {s['id']}")
        is_evt, reasons = should_trigger_event(s.get("metadata", {}))
        if is_evt: print(f"  ⚡ High-signal: {', '.join(reasons)}")

        if len(s["content"].strip()) < 50:
            print("  ⏭️  Too short")
            state.setdefault("processed_hashes", {})[s["hash"]] = datetime.now(timezone.utc).timestamp()
            continue

        facts = extract_and_tag(s["content"], project)
        print(f"  🔍 {len(facts)} candidates")

        stats = store_facts(facts, project, dry_run)
        totals["sessions"] += 1
        totals["stored"] += stats["stored"]
        totals["noise"] += stats["skipped_noise"]
        totals["secrets"] += stats["skipped_secrets"]
        totals["low_conf"] += stats["skipped_low_confidence"]
        totals["dupe"] += stats["skipped_duplicate"]
        totals["pii"] += stats["redacted_pii"]
        new_tags.extend(stats.get("new_tags", []))

        if not dry_run:
            state.setdefault("processed_hashes", {})[s["hash"]] = datetime.now(timezone.utc).timestamp()
            state["last_processed_session_id"] = s["id"]
            ts = s.get("metadata", {}).get("timestamp")
            if ts: state["last_processed_timestamp"] = ts

    if not dry_run:
        state["total_extracted"] = state.get("total_extracted", 0) + totals["stored"]
        state["total_skipped_noise"] = state.get("total_skipped_noise", 0) + totals["noise"]
        state["total_skipped_secrets"] = state.get("total_skipped_secrets", 0) + totals["secrets"]
        state["total_skipped_dupe"] = state.get("total_skipped_dupe", 0) + totals["dupe"]
        save_extract_state(state)

    print(f"\n{'=' * 60}")
    print(f"📊 SWEEP SUMMARY")
    print(f"  Sessions:     {totals['sessions']}")
    print(f"  Stored:       {totals['stored']}")
    print(f"  Noise:        {totals['noise']}")
    print(f"  🔒 Secrets:   {totals['secrets']}")
    print(f"  🔏 Redacted:  {totals['pii']}")
    print(f"  Low conf:     {totals['low_conf']}")
    print(f"  Duplicates:   {totals['dupe']}")
    if new_tags: print(f"  New tags:     {', '.join(set(new_tags))}")
    print(f"{'=' * 60}")


def cmd_session(path, dry_run=False, project=None):
    state = load_extract_state()
    s = load_session(path)
    if s["hash"] in state.get("processed_hashes", {}):
        print("  ⏭️  Already processed (hash match)")
        return

    print(f"🧬 EVENT EXTRACTION — {s['id']}")
    is_evt, reasons = should_trigger_event(s.get("metadata", {}))
    if is_evt: print(f"  ⚡ Trigger: {', '.join(reasons)}")

    facts = extract_and_tag(s["content"], project)
    print(f"  🔍 {len(facts)} candidates")
    stats = store_facts(facts, project, dry_run)

    if not dry_run:
        state.setdefault("processed_hashes", {})[s["hash"]] = datetime.now(timezone.utc).timestamp()
        state["last_processed_session_id"] = s["id"]
        state["total_extracted"] = state.get("total_extracted", 0) + stats["stored"]
        save_extract_state(state)

    print(f"  ✅ {stats['stored']} stored | 🔒 {stats['skipped_secrets']} secrets blocked | 🔏 {stats['redacted_pii']} redacted")


def cmd_extract_text(text, dry_run=False, project=None):
    facts = extract_and_tag(text, project)
    stats = store_facts(facts, project, dry_run)
    print(f"Stored: {stats['stored']} | Noise: {stats['skipped_noise']} | 🔒 Secrets: {stats['skipped_secrets']}")


def cmd_status():
    s = load_extract_state()
    print(json.dumps({
        "last_processed": s.get("last_processed_session_id"),
        "last_timestamp": s.get("last_processed_timestamp"),
        "sessions_tracked": len(s.get("processed_hashes", {})),
        "total_extracted": s.get("total_extracted", 0),
        "total_noise": s.get("total_skipped_noise", 0),
        "total_secrets_blocked": s.get("total_skipped_secrets", 0),
        "total_dupes": s.get("total_skipped_dupe", 0),
    }, indent=2))


# ====================================================================
# DECISION JOURNAL — Exportable timeline of all decisions
# ====================================================================

def _search_all_memories(project=None, query="*", limit=500):
    """Pull all memories from local mem CLI."""
    # Search with broad queries to gather everything
    queries = [
        "decision chose selected picked",
        "switched changed pivoted reversed",
        "hypothesis believe assume",
        "metric ratio percentage rate",
        "competitor competes alternative",
        "open question deciding exploring",
        "strategy marketing funding growth",
        "product feature design UX",
        "pricing monetization subscription",
        "investor pitch valuation funding",
        "team hired contractor role",
    ]
    seen = set()
    results = []
    for q in queries:
        cmd = ["python3", MEM_CLI, "search", q, "-k", "20"]
        if project:
            cmd.extend(["-p", project])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                for line in r.stdout.strip().split("\n"):
                    line = line.strip()
                    if line and line not in seen:
                        seen.add(line)
                        results.append(_parse_mem_line(line))
        except Exception as e:
            logger.warning(f"Journal search failed for '{q[:20]}': {e}")
    return results


def _parse_mem_line(line: str) -> dict:
    """Parse a line from mem search output into structured data.

    mem CLI output format: [mem_id] (tags) content text
    Also handles legacy formats: [tags] fact text, fact text [tags], or just fact text.
    """
    import re as _re
    mem_id = ""
    tags = ""
    text = line

    # Try canonical mem CLI format: [mem_id] (tags) content
    canonical = _re.match(r'^\[([^\]]+)\]\s*\(([^)]*)\)\s*(.*)', line)
    if canonical:
        mem_id = canonical.group(1)
        tags = canonical.group(2)
        text = canonical.group(3).strip()
        return {"id": mem_id, "text": text, "tags": tags}

    # Legacy fallback: look for tags in brackets with ':'
    tag_match = _re.search(r'\[([^\]]+)\]', line)
    if tag_match:
        potential_tags = tag_match.group(1)
        if ":" in potential_tags:  # looks like tags
            tags = potential_tags
            text = line[:tag_match.start()].strip() or line[tag_match.end():].strip()

    return {"id": mem_id, "text": text, "tags": tags}


def _extract_date_from_tags(tags: str) -> str:
    """Pull decided:YYYY-MM-DD from tag string."""
    import re as _re
    m = _re.search(r'decided:(\d{4}-\d{2}-\d{2})', tags)
    if m:
        return m.group(1)
    m = _re.search(r'decided:(\d{4}-W\d{2})', tags)
    if m:
        return m.group(1)
    return ""


def _extract_domain_from_tags(tags: str) -> str:
    """Pull domain:xxx from tag string."""
    import re as _re
    domains = _re.findall(r'domain:(\S+?)(?:,|$|\s)', tags)
    return ", ".join(domains) if domains else ""


def _extract_type_from_tags(tags: str) -> str:
    """Pull type:xxx from tag string."""
    import re as _re
    m = _re.search(r'type:(\S+?)(?:,|$|\s)', tags)
    return m.group(1) if m else ""


def cmd_journal(project=None, output_path=None):
    """
    Generate a decision journal — timeline of all decisions, pivots,
    open questions, and contradictions.

    Investor-ready. Board-ready. Future-you-ready.
    """
    all_memories = _search_all_memories(project)

    if not all_memories:
        print("📓 No memories found. Run extraction first.")
        return

    # Categorize
    buckets = {
        "pivot": [], "decision": [], "open_question": [],
        "hypothesis": [], "validation": [], "metric": [],
        "competitive": [], "feedback": [], "other": [],
    }
    for mem in all_memories:
        mem_type = _extract_type_from_tags(mem["tags"])
        mem["date"] = _extract_date_from_tags(mem["tags"])
        mem["domain"] = _extract_domain_from_tags(mem["tags"])
        bucket = mem_type if mem_type in buckets else "other"
        buckets[bucket].append(mem)

    # Sort each bucket by date
    for lst in buckets.values():
        lst.sort(key=lambda x: x.get("date") or "9999-99-99")

    # Build output path
    if not output_path:
        output_path = os.path.expanduser("~/.openclaw/decision-journal.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append(f"# 📓 Decision Journal")
    lines.append(f"Generated: {today}")
    if project:
        lines.append(f"Project: {project}")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Category | Count |")
    lines.append(f"|----------|-------|")
    for name, lst in buckets.items():
        if lst:
            emoji = {"pivot": "🔄", "decision": "✅", "open_question": "❓",
                     "hypothesis": "🧪", "validation": "📊", "metric": "📈",
                     "competitive": "🏁", "feedback": "💬"}.get(name, "📝")
            lines.append(f"| {emoji} {name.replace('_', ' ').title()} | {len(lst)} |")
    lines.append("")

    # --- Pivots (most important for investors) ---
    if buckets["pivot"]:
        lines.append("## 🔄 Pivots (Direction Changes)")
        lines.append("")
        lines.append("*These are moments where the team changed course.*")
        lines.append("")
        for p in buckets["pivot"]:
            date = p["date"] or "undated"
            domain = p["domain"] or "general"
            lines.append(f"- **[{date}]** ({domain}) {p['text']}")
        lines.append("")

    # --- Open Questions ---
    if buckets["open_question"]:
        lines.append("## ❓ Open Questions")
        lines.append("")
        lines.append("*Unresolved decisions that need answers.*")
        lines.append("")
        for q in buckets["open_question"]:
            domain = q["domain"] or "general"
            lines.append(f"- ({domain}) {q['text']}")
        lines.append("")

    # --- Active Decisions by Domain ---
    if buckets["decision"]:
        lines.append("## ✅ Active Decisions")
        lines.append("")
        # Group by domain
        by_domain = {}
        for d in buckets["decision"]:
            dom = d["domain"] or "general"
            by_domain.setdefault(dom, []).append(d)
        for dom in sorted(by_domain.keys()):
            lines.append(f"### {dom.title()}")
            lines.append("")
            for d in by_domain[dom]:
                date = d["date"] or "undated"
                lines.append(f"- **[{date}]** {d['text']}")
            lines.append("")

    # --- Hypotheses ---
    if buckets["hypothesis"]:
        lines.append("## 🧪 Hypotheses (Untested)")
        lines.append("")
        for h in buckets["hypothesis"]:
            lines.append(f"- {h['text']}")
        lines.append("")

    # --- Validations ---
    if buckets["validation"]:
        lines.append("## 📊 Validations (Tested)")
        lines.append("")
        for v in buckets["validation"]:
            date = v["date"] or "undated"
            lines.append(f"- **[{date}]** {v['text']}")
        lines.append("")

    # --- Metrics ---
    if buckets["metric"]:
        lines.append("## 📈 Tracked Metrics")
        lines.append("")
        for m in buckets["metric"]:
            date = m["date"] or "undated"
            lines.append(f"- **[{date}]** {m['text']}")
        lines.append("")

    # --- Competitive ---
    if buckets["competitive"]:
        lines.append("## 🏁 Competitive Intelligence")
        lines.append("")
        for c in buckets["competitive"]:
            lines.append(f"- {c['text']}")
        lines.append("")

    # --- Feedback ---
    if buckets["feedback"]:
        lines.append("## 💬 Feedback Received")
        lines.append("")
        for f in buckets["feedback"]:
            source = ""
            if "source:investor" in f["tags"]:
                source = " *(investor)*"
            elif "source:user-research" in f["tags"]:
                source = " *(user research)*"
            lines.append(f"- {f['text']}{source}")
        lines.append("")

    # Write
    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)

    print(f"📓 Decision journal written to: {output_path}")
    print(f"   {sum(len(v) for v in buckets.values())} memories across {sum(1 for v in buckets.values() if v)} categories")
    return output_path


# ====================================================================
# PROACTIVE RECALL — Pre-load relevant memories into system prompt
# ====================================================================


def rrf_fuse(query_results: list, k: int = 10) -> list:
    """Reciprocal Rank Fusion across multiple query result lists.

    Each element of query_results is a list of parsed memory dicts
    (as returned by _parse_mem_line) from a single sub-query.
    Returns a single fused list sorted by RRF score descending,
    with tag priority as tiebreaker.
    """
    scores = {}       # memory_id → cumulative RRF score
    memory_map = {}   # memory_id → memory dict

    for results in query_results:
        for rank, mem in enumerate(results):
            mid = mem["id"]
            memory_map[mid] = mem
            scores[mid] = scores.get(mid, 0) + 1.0 / (k + rank + 1)

    # Sort by RRF score descending, then by tag priority as tiebreaker
    ranked = sorted(
        scores.keys(),
        key=lambda mid: (
            -scores[mid],
            -memory_map[mid].get("priority", 0),
        ),
    )
    return [memory_map[mid] for mid in ranked]


def cmd_recall(topic: str, project=None, max_memories=10):
    """
    Given a conversation topic, search memory and generate a context
    block that can be injected into ClawBot's system prompt.

    This is the "ClawBot knows you from turn 1" feature.

    Returns a formatted string suitable for system prompt injection.
    """
    # Expand topic into multiple search dimensions
    search_queries = _expand_topic_queries(topic)

    # Gather per-query results as separate lists for RRF fusion
    all_query_results = []

    for q in search_queries:
        cmd = ["python3", MEM_CLI, "search", q, "-k", "5"]
        if project:
            cmd.extend(["-p", project])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                query_memories = []
                for line in r.stdout.strip().split("\n"):
                    line = line.strip()
                    if line:
                        parsed = _parse_mem_line(line)
                        # Tag priority for RRF tiebreaker
                        priority = 0
                        if "type:decision" in parsed["tags"]: priority = 3
                        if "type:pivot" in parsed["tags"]: priority = 4
                        if "type:open_question" in parsed["tags"]: priority = 5
                        if "type:metric" in parsed["tags"]: priority = 2
                        if "type:competitive" in parsed["tags"]: priority = 2
                        parsed["priority"] = priority
                        query_memories.append(parsed)
                if query_memories:
                    all_query_results.append(query_memories)
        except Exception:
            pass

    # Fuse results with Reciprocal Rank Fusion, take top N
    memories = rrf_fuse(all_query_results, k=10)[:max_memories]

    # Increment access_count for recalled memories
    recalled_ids = [m["id"] for m in memories if m.get("id")]
    if recalled_ids:
        try:
            _db = os.path.expanduser("~/.claude-memory/memory.db")
            if os.path.exists(_db):
                import sqlite3 as _sqlite3
                _conn = _sqlite3.connect(_db)
                for _mid in recalled_ids:
                    _conn.execute(
                        "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                        (_mid,),
                    )
                _conn.commit()
                _conn.close()
        except Exception:
            pass  # access_count is best-effort; never break recall


    if not memories:
        print("No relevant memories found.")
        return ""

    # Build the system prompt injection block
    lines = []
    lines.append("<clawbot_context>")
    lines.append(f"Topic: {topic}")
    lines.append(f"Retrieved: {len(memories)} relevant memories")
    lines.append("")

    # Group by priority for cleaner output
    active_decisions = [m for m in memories if "type:decision" in m["tags"] or "type:pivot" in m["tags"]]
    open_questions = [m for m in memories if "type:open_question" in m["tags"]]
    context = [m for m in memories if m not in active_decisions and m not in open_questions]

    if active_decisions:
        lines.append("ACTIVE DECISIONS:")
        for m in active_decisions:
            date = _extract_date_from_tags(m["tags"])
            prefix = "🔄 PIVOT" if "type:pivot" in m["tags"] else "✅"
            lines.append(f"  {prefix} [{date}] {m['text']}")

    if open_questions:
        lines.append("OPEN QUESTIONS:")
        for m in open_questions:
            lines.append(f"  ❓ {m['text']}")

    if context:
        lines.append("RELEVANT CONTEXT:")
        for m in context:
            lines.append(f"  • {m['text']}")

    lines.append("</clawbot_context>")

    output = "\n".join(lines)
    print(output)
    return output


_LLM_EXPANSION_CACHE: dict = {}


def _llm_expand_query(query: str) -> list:
    """Call GPT-4.1-mini to generate related search terms. 1s timeout."""
    cache_key = query.lower().strip()
    if cache_key in _LLM_EXPANSION_CACHE:
        return _LLM_EXPANSION_CACHE[cache_key]
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="http://127.0.0.1:18791/v1",
            api_key="LOCAL",
            timeout=1.0,
        )
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{
                "role": "user",
                "content": (
                    "Given this search query, generate 5 related search terms "
                    "that would find relevant memories in a personal knowledge base. "
                    "Return only the terms, one per line.\n\n"
                    f"Query: {query}"
                ),
            }],
            temperature=0.0,
        )
        terms = [
            line.strip() for line in
            resp.choices[0].message.content.strip().split("\n")
            if line.strip()
        ]
        _LLM_EXPANSION_CACHE[cache_key] = terms
        return terms
    except Exception:
        return []


def _expand_topic_queries(topic: str) -> list:
    """
    Expand a topic into multiple search queries to get broader recall.

    "pricing" → ["pricing", "monetization", "subscription", "revenue",
                  "freemium", "payment"]

    Uses a static domain map first (free, instant), then LLM expansion
    via GPT-4.1-mini (cached, 1s timeout), then falls back to word-based
    expansion as last resort.
    """
    # Topic expansion map — domain-specific associations
    expansions = {
        "pricing": ["monetization", "subscription", "revenue", "freemium", "payment", "pricing"],
        "monetization": ["pricing", "revenue", "subscription", "freemium", "ads", "monetization"],
        "funding": ["investor", "pitch", "valuation", "fundraise", "seed", "series", "funding"],
        "investor": ["funding", "pitch deck", "valuation", "VC", "angel", "investor"],
        "marketing": ["growth", "acquisition", "viral", "CAC", "marketing", "brand"],
        "growth": ["marketing", "retention", "viral", "DAU", "MAU", "growth"],
        "onboarding": ["retention", "signup", "tutorial", "first-time", "onboarding"],
        "retention": ["churn", "engagement", "DAU", "MAU", "onboarding", "retention"],
        "competitor": ["competitive", "alternative", "market", "competitor"],
        "design": ["UX", "UI", "interface", "wireframe", "design", "product"],
        "product": ["feature", "roadmap", "MVP", "design", "product"],
        "tech": ["stack", "framework", "infrastructure", "backend", "frontend", "tech"],
        "legal": ["incorporation", "IP", "terms", "privacy", "GDPR", "legal"],
        "hiring": ["team", "role", "contractor", "equity", "cofounder", "hiring"],
        "launch": ["release", "app store", "beta", "launch", "go-live"],
        "users": ["user research", "persona", "interview", "survey", "feedback", "users"],
        # Infrastructure & ops domains (added for ClawBot recall)
        "tailscale": ["VPN", "wireguard", "exit node", "mesh network", "tailscale"],
        "gateway": ["openclaw", "claude-opus", "copilot", "LLM", "model config", "gateway"],
        "oauth": ["reauth", "token refresh", "google auth", "credentials", "oauth"],
        "memory": ["extraction", "smart_extractor", "session facts", "recall", "memory"],
        "azure": ["VM", "foundry", "managed identity", "NSG", "cost", "azure"],
        "weather": ["NWS", "forecast", "snowfall", "storm", "alert", "weather"],
        "docker": ["container", "compose", "drawio", "foundry", "docker"],
        "cron": ["watchdog", "scheduled", "timer", "periodic", "cron"],
    }

    STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "can", "shall",
                 "to", "of", "in", "for", "on", "with", "at", "by", "from",
                 "as", "into", "about", "between", "through", "after", "before",
                 "and", "but", "or", "not", "so", "if", "then", "than", "that",
                 "this", "what", "which", "who", "whom", "how", "when", "where",
                 "why", "it", "we", "they", "i", "you", "he", "she", "my", "our"}

    # Start with the raw topic
    words = topic.lower().split()
    queries = [topic]
    matched_static = False

    # Add expansions for each word from static map
    for word in words:
        if word in expansions:
            queries.extend(expansions[word])
            matched_static = True

    # Dynamic fallback: if no static match, try LLM then word-based
    if not matched_static:
        llm_terms = _llm_expand_query(topic)
        if llm_terms:
            queries.extend(llm_terms)
        else:
            # Word-based fallback (last resort — LLM unavailable or timed out)
            significant = [w for w in words if w not in STOPWORDS and len(w) > 2]
            queries.extend(significant)
            for i in range(len(significant) - 1):
                queries.append(f"{significant[i]} {significant[i+1]}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)

    return unique[:8]  # Cap at 8 queries to stay fast


# ====================================================================
# EXTRACTION CALIBRATION — Score and refine extraction quality
# ====================================================================

def cmd_calibrate(session_paths: list, project=None):
    """
    Run extraction calibration on real session files.

    For each session:
      1. Parse with load_session
      2. Run extract_and_tag
      3. Score extraction quality
      4. Report gaps and recommendations

    This is the "did we catch what matters?" feedback loop.
    Run monthly against a sample of recent sessions.
    """
    from auth_provider import get_chat_client

    print(f"🔬 EXTRACTION CALIBRATION — {len(session_paths)} sessions")
    print("=" * 60)

    all_scores = []
    all_recommendations = []

    for path in session_paths:
        print(f"\n📄 {os.path.basename(path)}")

        # Step 1: Parse
        session = load_session(path)
        meta = session.get("metadata", {})
        content = session["content"]
        lines = content.split('\n')

        print(f"   Format: {meta.get('format', '?')}")
        print(f"   Lines: {len(lines)}")
        print(f"   Thinking blocks: {meta.get('thinking_blocks', 0)}")
        print(f"   Tool calls: {meta.get('tool_calls', 0)}")

        # Step 2: Run extraction
        facts = extract_and_tag(content, project)
        print(f"   Extracted: {len(facts)} facts")

        # Step 3: Score with LLM judge
        score = _score_extraction_quality(content, facts)
        all_scores.append(score)

        print(f"   Quality score: {score.get('overall', 0)}/10")
        if score.get("missed"):
            print(f"   ⚠️  Missed facts:")
            for m in score["missed"][:5]:
                print(f"      - {m}")
        if score.get("noise"):
            print(f"   🗑️  Noise (shouldn't have been extracted):")
            for n in score["noise"][:3]:
                print(f"      - {n}")
        if score.get("recommendations"):
            all_recommendations.extend(score["recommendations"])

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 CALIBRATION SUMMARY")
    avg_score = sum(s.get("overall", 0) for s in all_scores) / max(len(all_scores), 1)
    print(f"   Average quality: {avg_score:.1f}/10")
    total_missed = sum(len(s.get("missed", [])) for s in all_scores)
    total_noise = sum(len(s.get("noise", [])) for s in all_scores)
    print(f"   Total missed facts: {total_missed}")
    print(f"   Total noise facts: {total_noise}")

    if all_recommendations:
        # Deduplicate
        unique_recs = list(dict.fromkeys(all_recommendations))
        print(f"\n   🔧 RECOMMENDATIONS:")
        for r in unique_recs[:10]:
            print(f"      • {r}")

    # Write calibration report
    report_path = os.path.expanduser("~/.openclaw/calibration-report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessions_analyzed": len(session_paths),
        "average_quality": round(avg_score, 1),
        "total_missed": total_missed,
        "total_noise": total_noise,
        "scores": all_scores,
        "recommendations": list(dict.fromkeys(all_recommendations)),
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n   Report saved: {report_path}")
    return report


def _score_extraction_quality(content: str, facts: list) -> dict:
    """
    Use LLM as judge to score extraction quality.

    Sends the original content + extracted facts to an LLM
    and asks it to identify:
      - Missed facts (high-value info that wasn't extracted)
      - Noise (low-value info that shouldn't have been extracted)
      - Quality score (1-10)
    """
    from auth_provider import get_chat_client

    # Build facts summary
    facts_text = "\n".join(
        f"  - {f.get('fact', '')} [{','.join(f.get('tags', []))}]"
        for f in facts
    )

    # Use priority content (trimmed) for the judge
    trimmed_content = _prioritize_content(content)[:10000]

    prompt = f"""You are an extraction quality judge. Score how well facts were extracted.

ORIGINAL CONVERSATION (priority-ordered):
{trimmed_content}

EXTRACTED FACTS:
{facts_text or "(none extracted)"}

Score the extraction:
1. MISSED: List important facts from the conversation that SHOULD have been extracted but weren't. Focus on decisions, config changes, cost impacts, architecture choices, error patterns.
2. NOISE: List extracted facts that are too trivial or operational to be worth storing long-term.
3. QUALITY: Overall score 1-10 (10 = perfect extraction, caught everything important, no noise)
4. RECOMMENDATIONS: Specific improvements to the extraction prompt or process.

Return JSON (no markdown fences):
{{
  "overall": 7,
  "missed": ["fact that should have been extracted", "another missed fact"],
  "noise": ["fact that was too trivial"],
  "recommendations": ["Add X to extraction prompt", "Increase chunk size for long sessions"]
}}"""

    try:
        client = get_chat_client()
        resp = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.2"),
            max_completion_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        return {"overall": 0, "missed": [], "noise": [], "recommendations": []}


# ====================================================================
# CLI
# ====================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="ClawBot Smart Extractor v3")
    sub = parser.add_subparsers(dest="command")

    sw = sub.add_parser("sweep", help="Scheduled sweep")
    sw.add_argument("--dry-run", action="store_true")
    sw.add_argument("-p", "--project", type=str)

    se = sub.add_parser("session", help="Event trigger")
    se.add_argument("--path", required=True)
    se.add_argument("--dry-run", action="store_true")
    se.add_argument("-p", "--project", type=str)

    ex = sub.add_parser("extract", help="Direct text")
    ex.add_argument("--text", "-t", required=True)
    ex.add_argument("--dry-run", action="store_true")
    ex.add_argument("-p", "--project", type=str)

    sub.add_parser("status", help="Show state")

    jo = sub.add_parser("journal", help="Export decision journal")
    jo.add_argument("-p", "--project", type=str)
    jo.add_argument("-o", "--output", type=str, help="Output path (default: ~/.openclaw/decision-journal.md)")

    rc = sub.add_parser("recall", help="Proactive memory recall for a topic")
    rc.add_argument("topic", type=str, help="Conversation topic")
    rc.add_argument("-p", "--project", type=str)
    rc.add_argument("-k", "--max", type=int, default=10, help="Max memories to retrieve")

    ca = sub.add_parser("calibrate", help="Score extraction quality against real sessions")
    ca.add_argument("sessions", nargs="+", help="Session JSONL file paths")
    ca.add_argument("-p", "--project", type=str)

    args = parser.parse_args()
    if args.command == "sweep": cmd_sweep(args.dry_run, args.project)
    elif args.command == "session": cmd_session(args.path, args.dry_run, args.project)
    elif args.command == "extract": cmd_extract_text(args.text, args.dry_run, args.project)
    elif args.command == "status": cmd_status()
    elif args.command == "journal": cmd_journal(args.project, args.output)
    elif args.command == "recall": cmd_recall(args.topic, args.project, args.max)
    elif args.command == "calibrate": cmd_calibrate(args.sessions, args.project)
    else: parser.print_help()
