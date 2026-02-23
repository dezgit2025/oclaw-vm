---
name: rob-proctor-high-frequency
description: Generate a 3-minute “high frequency” morning routine (Bob/Rob Proctor style): breath + 3 rotating affirmations + gratitude + one-win. Use when user says “Bob Proctor”, “Rob Proctor”, “high frequency routine”, or wants a quick morning mindset ritual.
user-invocable: true
metadata: {"openclaw": {"emoji": "☀️"}}
---

# Rob Proctor — High Frequency Morning Routine (3 minutes)

Use this skill when the user wants a quick morning routine to get into a “high frequency” state.

## What to do

1) Run the generator script to get today’s routine:

```bash
/home/desazure/.openclaw/workspace/.venv-gmail/bin/python \
  /home/desazure/.openclaw/workspace/skills/rob-proctor-high-frequency/scripts/generate_routine.py
```

2) Send the output as a short, clean message.

Optional:
- If the user wants audio, call **TTS** with the routine text.
- If the user wants a daily automatic push, schedule a **cron** systemEvent that tells them it’s their “Rob Proctor 3‑minute routine” and includes the generated text (or tells them to reply “Bob Proctor” to generate it).

## Routine format (always)
- 0:00–1:00 Breath (6 slow breaths: 4s in / 6s out)
- 1:00–2:00 3 affirmations (rotating)
- 2:00–3:00 Gratitude + One Win + First Step (<5 min)
- Close with: **“Thank you, God for my abundance, wealth, and health.”**

## Edit / expand affirmations
Affirmations live in:
- `scripts/affirmations.md`
Add/remove bullets freely; keep each line short.
