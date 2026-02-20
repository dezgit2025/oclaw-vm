# cbot-skill-building

## When I stop asking questions (simple rule)
I stop asking questions when I have enough info to build something that works end-to-end **without guessing the important bits**.

**Rule of thumb:** I only ask questions that would **change the code**. If it wouldn’t change implementation much, I’ll pick a safe default and clearly state the assumption.

---

## The 5 things I need to build a new skill
Think of a skill like a small app. I need:

1) **Trigger / input**
- What you’ll say/send (text? photo? URL? file?)
- A concrete example input is ideal

2) **Output**
- What you want back (chat message? file? Google Sheet row? Drive upload?)

3) **Source of truth**
- Where data should live (local JSON, Google Sheet, ClickUp, etc.)
- Any constraints (e.g., “must be under OpenClawShared”)

4) **Rules & edge cases**
- What to do when info is missing (“estimate,” “ask,” “skip,” etc.)
- Any safety rules (no auto-sends, no cookies, etc.)

5) **Schedule / automation (optional)**
- On-demand only vs cron vs both

Once those are clear enough, I build.

---

## When I keep asking questions (because code would differ)
I keep asking if the answer changes the implementation path, e.g.:
- Which provider/API to use (Rakuten vs scraping vs manual)
- Which exact item/variant matters (milk type, burger type, etc.)
- How to handle edits vs “correction rows”
- Token/auth storage method
- Strictness: fail-fast vs best-effort

---

## When I stop asking and just build
I stop when:
- There’s **one obvious path**, or
- Multiple paths exist but a **safe default** is fine, and I can say:
  - “I’m going to assume **X**; if you want **Y**, tell me and I’ll adjust.”

---

## Definition of done (what “finished” means)
A skill is ready when it has:
- `SKILL.md` with **how to run it**
- A working script + dependencies
- A **dry-run/test** command
- Clear defaults + how to override
- Useful logs/errors for debugging

---

## Practical workflow
If you send:
- “Build a skill that takes ___ and writes to ___, and it should behave like ___”

…I’ll usually only ask **1–3 clarifying questions** max.

If you don’t answer, I’ll build with defaults and mark assumptions.

---

## Suggested subfolder architecture (recommended)
Use one top-level folder per skill, plus a small number of predictable subfolders:

```
skills/<skill-name>/
  SKILL.md                 # human-facing usage + examples
  scripts/                 # the actual implementation
    <entrypoint>.py|.sh
    lib/                   # helper modules (optional)
  assets/                  # sample inputs, test fixtures, prompt templates
  docs/                    # deeper design notes, diagrams, troubleshooting
  tests/                   # lightweight tests (optional)
```

For ops/reliability helpers that aren’t “skills,” keep them in:

```
ops/<area>/
  README.md
  run_<thing>.sh
  <thing>.py
```

---

## Tiny checklist before you ask me to build a skill
Send me these in one message:
- Input example
- Output expectation
- Where it should write/store
- Any must-have rules
- Whether it should be scheduled
