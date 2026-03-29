#!/usr/bin/env python3
"""Generate 20 benchmark queries (10 verbatim + 10 temporal) from memory snapshot."""

import json
import os
import re

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory_snapshot.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "recall_benchmark.json")


def load_memories():
    with open(SNAPSHOT_PATH) as f:
        return json.load(f)


def extract_keywords(content: str, n: int = 3) -> list[str]:
    """Extract top N distinctive words from content."""
    stop = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "and",
        "but", "or", "nor", "not", "so", "yet", "both", "either", "neither",
        "each", "every", "all", "any", "few", "more", "most", "other",
        "some", "such", "no", "only", "own", "same", "than", "too", "very",
        "just", "because", "if", "when", "where", "how", "what", "which",
        "who", "whom", "this", "that", "these", "those", "it", "its",
        "also", "then", "up", "out", "about", "over", "use", "used",
        "using", "run", "runs", "running", "team", "created", "updated",
        "added", "new", "including", "based", "via", "per", "e.g.",
    }
    words = re.findall(r"[A-Za-z][A-Za-z0-9_.-]+", content)
    seen = set()
    keywords = []
    for w in words:
        lower = w.lower()
        if lower not in stop and lower not in seen and len(lower) > 2:
            seen.add(lower)
            keywords.append(w)
            if len(keywords) >= n:
                break
    return keywords


def generate_verbatim_queries(memories: list[dict]) -> list[dict]:
    """Generate 10 verbatim fact-recall queries from top-importance memories.

    Picks memories with diverse topics and constructs natural questions.
    """
    # Sort by importance desc, then by date desc for tiebreaking
    sorted_mems = sorted(memories, key=lambda m: (-m["importance"], m["created_at"]))

    # Pick diverse memories — skip very similar ones
    selected = []
    seen_topics = set()

    # Prioritize the highest importance one first
    pinned = [m for m in sorted_mems if m["importance"] == 10]
    for m in pinned:
        selected.append(m)
        seen_topics.add(m["id"])

    # Then fill from remaining, preferring diversity
    for m in sorted_mems:
        if m["id"] in seen_topics:
            continue
        content_lower = m["content"].lower()
        # Skip test/trivial entries
        if content_lower.startswith("test") or len(m["content"]) < 40:
            continue
        selected.append(m)
        seen_topics.add(m["id"])
        if len(selected) >= 10:
            break

    # Generate a question for each selected memory
    query_templates = [
        # (condition_substring, question_template)
    ]

    queries = []
    for i, mem in enumerate(selected):
        content = mem["content"]
        mem_id = mem["id"]
        keywords = extract_keywords(content, 4)
        q_id = f"q{i+1:03d}"

        # Generate contextual question based on content
        question = _content_to_question(content)

        difficulty = "easy" if mem["importance"] >= 8 else "medium"

        queries.append({
            "id": q_id,
            "query": question,
            "category": "verbatim",
            "expected_memory_ids": [mem_id],
            "expected_keywords": keywords,
            "expected_absent": False,
            "difficulty": difficulty,
        })

    return queries[:10]


def _content_to_question(content: str) -> str:
    """Convert a memory content string into a natural question."""
    c = content.lower()

    # Tailscale exit node / residential IP
    if "exit-node" in c or "exit node" in c or "residential ip" in c:
        if "watchdog" in c and "preference" in c:
            return "What is the team's preference for how the Tailscale exit-node watchdog should behave?"
        if "residential" in c and "egress" in c:
            return "How does the OpenClaw VM egress through a residential IP address?"
        if "chromeos-nissa" in c and "watchdog" in c:
            return "What does the chromeos-nissa Tailscale exit-node watchdog cron job do?"

    # Weather
    if "weather" in c and "cron" in c and "1x/day" in c:
        return "What was decided about the NYC major weather alert cron schedule?"
    if "storm-mode" in c and "every 3 hours" in c:
        return "How does the weather alerting storm-mode cron job work?"
    if "nws" in c and "nyz072" in c and "standardized" in c:
        return "What API and zone does the team use for NYC weather alerts?"
    if "blizzard warning" in c:
        return "What NWS warning was being tracked for NYC zone NYZ072?"
    if "snowfallamount" in c:
        return "What NWS endpoint is used for snowfall forecasting?"
    if "westchester" in c and "white plains" in c:
        return "What NWS gridpoint is used for Westchester/White Plains weather forecasts?"
    if "weather-storm-alerts-nyc" in c:
        return "What skill and script handle NYC major weather alerts?"
    if "storm reminder" in c and "preparation checklist" in c:
        return "What was added to the major storm reminder message?"
    if "without a target" in c:
        return "What intermittent failure affected scheduled weather-alert delivery?"
    if "weather.gov" in c and "re-check" in c:
        return "What happens when a major NWS alert is active regarding weather.gov checks?"
    if "daily weather.gov check" in c:
        return "How often does the weather.gov check skill run?"

    # ClickUp
    if "clickup" in c and "1x/day" in c or ("clickup" in c and "once-daily" in c):
        return "What was decided about the NYC weather alert frequency?"
    if "clickup" in c and "2-3 lists" in c:
        return "What was decided about ClickUp list organization structure?"
    if "clickup" in c and "bills" in c and "urgent" in c:
        return "What is the default priority for the ClickUp Bills list?"
    if "clickup" in c and "12-hour" in c:
        return "What time format do ClickUp alerts use?"
    if "clickup" in c and "alert_mode" in c:
        return "What alert modes does the ClickUp due alerts system support?"
    if "clickup" in c and "task management" in c:
        return "What platform was used or considered for operational task management?"
    if "clickup" in c and "nagging" in c:
        return "What is the ClickUp vs OpenClaw alerting approach?"

    # Reddit / Digest
    if "reddit" in c and "json endpoints" in c:
        return "How was Reddit content fetched when the browser tool was unavailable?"
    if "r/claudecode" in c and "r/claudeai" in c:
        return "What subreddits are on the daily digest watchlist?"
    if "rss" in c and "atom" in c and "digest" in c:
        return "What content sources were added beyond Reddit for the daily digest?"
    if "high-signal ai digest" in c and "pipeline" in c and "reddit" in c:
        return "What is the high-signal AI digest pipeline architecture?"
    if "high_signal_digest" in c and "script" in c:
        return "What scripts implement the daily digest?"
    if "anthropic" in c and "digest source" in c:
        return "What happened when the team tried to add Anthropic as a digest source?"
    if "langchain" in c and "llamaindex" in c:
        return "What RSS feed sources are configured for the high-signal AI digest?"

    # Security
    if "tool confirmation" in c and "prompt-injection" in c:
        return "What security measure was implemented to reduce prompt-injection risk?"
    if "loopback" in c and "gateway bind" in c:
        return "How was the gateway bind address changed for security?"
    if "exfill-lockdown" in c or "sensitive_paths" in c:
        return "What security documentation was created for exfiltration lockdown?"

    # Memory system
    if "clawbot-memory" in c and "sqlite" in c and "azure ai search" in c:
        return "What is the architecture of the ClawBot memory system?"
    if "smart_extractor" in c and "sweep" in c:
        return "How does ClawBot extract facts from sessions?"
    if "ai-search-sync-guide" in c:
        return "Where is the AI Search sync instruction guide located?"

    # GDrive
    if "gdrive-openclawshared" in c:
        return "What is the Google Drive upload workflow and what hardening was planned?"

    # Tailscale / Bastion
    if "tailscale" in c and "bastion" in c:
        return "What was decided about Tailscale vs Azure Bastion for VM access?"

    # Vector DB
    if "vector db" in c and "read-only" in c:
        return "What architectural guidance was given for the vector DB integration?"

    # Work decision coach
    if "work-decision-coach" in c and "big-tech" in c:
        return "What does the work-decision-coach skill do?"
    if "work-decision-coach" in c and "template" in c:
        return "What is the work-decision-coach prompt template structure?"

    # Cron scheduling
    if "offset time" in c and "cron" in c:
        return "What is the scheduling rule for creating cron reminders?"

    # HingeX
    if "hingex" in c and "social connector" in c:
        return "What is the HingeX Social Connector MVP1 core loop and features?"
    if "geo-heat-map" in c and "research" in c and "classified" in c:
        return "Where is the classified geo-heat-map research document?"
    if "phase-plan-heat-map" in c:
        return "What does the classified phase plan for the heat map contain?"
    if "n/k/m" in c and "cluster" in c:
        return "What are the N/K/M cluster-based unlock thresholds for the Vibe Map?"

    # Browser automation
    if "playwright" in c and "headless" in c:
        return "Does Playwright headless work on the oclaw VM and how is it tested?"

    # Folder organization
    if "global_folder_structure" in c and "entropy" in c:
        return "What is the directive for folder organization and entropy prevention?"

    # Personal
    if "alo hat" in c or "hat cleaning" in c:
        return "What are the cleaning instructions for the Alo hat?"
    if "kettlebell" in c:
        return "What kettlebell alternatives were researched?"
    if "forearm" in c and "wrist" in c and "rehab" in c:
        return "What is the forearm/wrist rehab protocol?"

    # Edit pattern
    if "functions.edit" in c and "oldtext" in c:
        return "What was learned about the functions.edit oldText matching requirement?"

    # Versioned files
    if "_v2/_v3" in c and "versioned" in c:
        return "What is the coding preference for versioned file naming?"

    # Backup snapshot
    if "backup snapshot" in c and "git" in c:
        return "What was included in the local git backup snapshot commit?"
    if "backup snapshot" in c and "origin" in c:
        return "What commit hash was pushed as the backup snapshot?"

    # Security scan
    if "security scan" in c and "tier 3" in c:
        return "What is the weekly security scan cron job called?"

    # Subprocess error
    if "subprocess.check_output" in c:
        return "What error pattern was observed with Python subprocess execution?"

    # Tag index
    if "tag-index" in c:
        return "What documentation artifact was generated for tag indexing?"

    # AI subreddits
    if "ai-related subreddits" in c:
        return "What internal doc was added for AI subreddit monitoring?"

    # WORKFLOW_AUTO
    if "workflow_auto" in c:
        return "What document was updated to reflect the automated digest workflow?"

    # Hospital bill
    if "hospital bill" in c:
        return "What urgent personal finance task was flagged in ClickUp?"

    # Anthropic engineering
    if "anthropic engineering" in c:
        return "Why were Anthropic Engineering posts added as a daily digest source?"

    # OpenClaw path
    if "/home/desazure/.openclaw/" in c and "toolchain" in c:
        return "What does the /home/desazure/.openclaw/ path indicate about the local environment?"

    # Python script runs
    if "repeatedly executed" in c and "python script" in c:
        return "What pattern of Python script execution was observed on 2026-02-23?"

    # Snap Map
    if "snap map" in c:
        return "What primary sources were added to the geo-heat-map research about Snap Map?"

    # Tagging note
    if "phase-plan" in c and "tagging" in c:
        return "What tags should be used for the phase-plan-heat-map document?"

    # NYC weather reminder cron
    if "nyc major weather reminder" in c and "until ack" in c:
        return "What is the NYC major weather reminder cron job behavior?"

    # Fallback
    return f"What do you know about: {content[:80]}?"


def generate_temporal_queries(memories: list[dict]) -> list[dict]:
    """Generate 10 temporal/decision queries from memories with dates or decision tags."""
    # Find memories with decision/architecture/preference type or date references
    decision_mems = []
    for m in memories:
        tags = m.get("tags", "")
        content = m["content"]
        is_decision = "type:decision" in tags
        is_arch = "type:architecture" in tags
        is_pref = "type:preference" in tags
        has_date = bool(re.search(r"2026-\d{2}-\d{2}", content)) or "decided:" in tags
        if (is_decision or is_arch or is_pref or has_date) and len(content) > 40:
            decision_mems.append(m)

    # Sort by importance desc then date
    decision_mems.sort(key=lambda m: (-m["importance"], m["created_at"]))

    queries = []
    used_ids = set()

    # Manually craft temporal/decision queries
    temporal_templates = [
        {
            "match": "weather alert cron schedule",
            "query": "When did we decide to change the NYC weather alert frequency to once daily?",
            "keywords": ["NYC", "weather", "cron", "once-daily"],
            "difficulty": "medium",
        },
        {
            "match": "tailscale",
            "query": "What did we decide about replacing Azure Bastion with Tailscale?",
            "keywords": ["Tailscale", "Bastion", "SSH", "access"],
            "difficulty": "medium",
        },
        {
            "match": "NWS",
            "query": "When was the decision made to standardize on the weather.gov NWS API for NYC alerts?",
            "keywords": ["weather.gov", "NWS", "NYZ072", "standardized"],
            "difficulty": "hard",
        },
        {
            "match": "tool confirmation",
            "query": "What did we decide about tool confirmation gates for security?",
            "keywords": ["tool", "confirmation", "prompt-injection", "exfil"],
            "difficulty": "hard",
        },
        {
            "match": "ClickUp",
            "query": "When did we decide to keep ClickUp lists to 2-3 and create separate Bills and Habits lists?",
            "keywords": ["ClickUp", "lists", "Bills", "Habits"],
            "difficulty": "medium",
        },
        {
            "match": "vector db",
            "query": "What did we decide about how the vector DB should be integrated?",
            "keywords": ["vector", "read-only", "retrieval", "JSONL"],
            "difficulty": "hard",
        },
        {
            "match": "HingeX",
            "query": "When was the HingeX Social Connector MVP1 scope decided?",
            "keywords": ["HingeX", "MVP1", "proximity", "match"],
            "difficulty": "medium",
        },
        {
            "match": "Anthropic Engineering",
            "query": "What did we decide about adding Anthropic Engineering posts to the daily digest?",
            "keywords": ["Anthropic", "Engineering", "digest", "WORKFLOW_AUTO"],
            "difficulty": "easy",
        },
        {
            "match": "residential",
            "query": "When was the decision made to route VM traffic through a residential IP via Tailscale exit node?",
            "keywords": ["residential", "exit", "node", "Tailscale"],
            "difficulty": "medium",
        },
        {
            "match": "snowfallAmount",
            "query": "What did we decide about using the NWS forecastGridData endpoint for snowfall?",
            "keywords": ["NWS", "forecastGridData", "snowfallAmount"],
            "difficulty": "hard",
        },
        {
            "match": "gdrive-openclawshared",
            "query": "What did we decide about hardening the Google Drive upload workflow?",
            "keywords": ["gdrive-openclawshared", "OpenClawShared", "confirmation", "allowlist"],
            "difficulty": "medium",
        },
    ]

    # Match each template to a memory
    for i, tmpl in enumerate(temporal_templates):
        match_str = tmpl["match"].lower()
        matched_mem = None
        for m in decision_mems:
            if m["id"] in used_ids:
                continue
            if match_str in m["content"].lower():
                matched_mem = m
                break

        if not matched_mem:
            # Fallback: pick any unused decision memory
            for m in decision_mems:
                if m["id"] not in used_ids:
                    matched_mem = m
                    break

        if matched_mem:
            used_ids.add(matched_mem["id"])
            queries.append({
                "id": f"q{11+i:03d}",
                "query": tmpl["query"],
                "category": "temporal",
                "expected_memory_ids": [matched_mem["id"]],
                "expected_keywords": tmpl["keywords"],
                "expected_absent": False,
                "difficulty": tmpl["difficulty"],
            })

    return queries[:10]


def main():
    memories = load_memories()
    print(f"Loaded {len(memories)} memories from snapshot")

    verbatim = generate_verbatim_queries(memories)
    print(f"Generated {len(verbatim)} verbatim queries")

    temporal = generate_temporal_queries(memories)
    print(f"Generated {len(temporal)} temporal queries")

    benchmark = verbatim + temporal
    print(f"Total benchmark queries: {len(benchmark)}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(benchmark, f, indent=2)

    print(f"\nSaved to {OUTPUT_PATH}")
    print("\n--- Benchmark Queries ---")
    for q in benchmark:
        print(f"  [{q['id']}] ({q['category']}/{q['difficulty']}) {q['query']}")


if __name__ == "__main__":
    main()
