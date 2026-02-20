# Model Routing Report Script

This Python script analyzes your Telegram model routing logs to report daily usage statistics of different AI models.

## Location
- Script code: `/home/desazure/.openclaw/workspace/ops/scripts/model_routing_report.py`
- Logs analyzed: `/home/desazure/.openclaw/workspace/logs/model_routing.log`

## Purpose
To count daily requests routed to each model (e.g., Foundry GPT-4.1-mini and Copilot GPT-5.2) and produce a summary report to monitor usage and manage costs.

## Features
- Parses the log file and extracts routing timestamp and model used.
- Counts requests per model for the current day.
- Prints a summary with counts and percentages per model.

## Automation
- Run daily via cron job at 8pm ET (America/New_York timezone).
- Cron job command:
  ```
  python3 /home/desazure/.openclaw/workspace/ops/scripts/model_routing_report.py
  ```
- Daily report sent to the main session.

## Log Rotation
- Logs retain 2 days of entries, with older logs deleted to save space.
- Logs are compressed after 1 day.

## Usage
Run the script manually anytime to get an immediate report.

```bash
python3 /home/desazure/.openclaw/workspace/ops/scripts/model_routing_report.py
```

---

## Updated Hybrid Routing Diagram

Here’s the updated hybrid routing diagram with explanation:

```
User message
     │
     ▼
  Check message prefix
     │
 ┌───┴─────────────┐
 │                 │
Prefix like      No prefix
“think hard”      (normal chat)
or “think deep”    │
 │                 ▼
 ▼            GPT-4.1-mini  ←── Hybrid routing: GPT-4.1-mini can escalate internally to GPT-5.2
Use GPT-5.2         │
(direct for          │
complex tasks)       ▼
               Internal heuristic
               routing inside GPT-4.1-mini
               can escalate to GPT-5.2
                   if needed
                   │
                   ▼
           Generate response and
           reply to user
```

### Explanation
- If you use “think hard” or “think deep,” the message is routed **directly to GPT-5.2**.
- Without prefix, messages go to **GPT-4.1-mini**, which can still **internally escalate** complex queries to GPT-5.2 automatically, based on its understanding.
- This hybrid lets you keep most chat on the cost-effective GPT-4.1-mini while still handling complex questions well.
