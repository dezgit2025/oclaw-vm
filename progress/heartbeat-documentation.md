# heartbeat-documentation.md

## What OpenClaw “heartbeat” is
A heartbeat is a **periodic mini agent turn**.

Its purpose is to let the assistant:
- read a small checklist file (HEARTBEAT.md)
- decide if anything needs doing right now
- either stay quiet / acknowledge, or proactively report something

It’s not a message broker or queue. It’s a scheduled “should I do anything?” decision loop.

## What heartbeat does (typical flow)

```
Timer / scheduler
   │
   ▼
Heartbeat turn (LLM)
   │  reads HEARTBEAT.md
   │  decides action
   ├─► if nothing to do → respond HEARTBEAT_OK
   └─► if something to do → run tool(s) / send message(s)
```

### Important behavior
- If **HEARTBEAT.md is empty**, the correct outcome is usually just `HEARTBEAT_OK`.
- If **HEARTBEAT.md contains tasks**, heartbeat can choose to perform them (e.g., check calendar, check alerts) and then message you.

## Why heartbeat uses an LLM
Heartbeat is implemented as a **mini assistant turn**, so it needs an LLM to:
- interpret the heartbeat instructions/checklist
- decide what to run
- format any report message

If you want a *zero-LLM* heartbeat, the alternative is **cron running scripts directly** (deterministic monitors) and only sending messages on conditions.

## What LLM model heartbeat uses (current)
Current config:
- `agents.defaults.heartbeat.model = "foundry/gpt-4.1-mini"`

Source: `/home/desazure/.openclaw/openclaw.json`

## Relationship to “Kimi proxy monitor”
Heartbeat and the Kimi proxy monitor are different:
- **Heartbeat**: assistant behavior loop (reads HEARTBEAT.md; may send messages)
- **Proxy monitor (cron)**: infrastructure health check (service active, /healthz OK, and a tiny test completion request)

Both can involve LLM calls, but for different reasons.

## Delivery semantics (what happens if something is down)
- Heartbeat does **not** queue outbound notifications like SQS/RabbitMQ.
- Telegram can buffer **inbound** messages you send *to the bot*, so the bot can catch up.
- For **outbound** alerts (bot → you), reliability requires retries/outbox on our side if you need guaranteed delivery.

## Practical recommendation
- Keep heartbeat on a **cheap/fast model** (like `foundry/gpt-4.1-mini`) because most heartbeats do very little.
- Put anything that must be deterministic/guaranteed into **cron + scripts**, and alert on failure.
