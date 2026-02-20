# How Telegram “buffering” works (and what it does *not* buffer)

This note clarifies a common confusion: **Telegram can buffer inbound updates for a bot, but it is *not* a general-purpose outbound message queue for alerts**.

## Definitions
- **Inbound (to the bot):** Messages that *you (a human)* send in Telegram **to the bot**.
- **Outbound (from the bot):** Messages that *the bot* sends **to you (a human)** (notifications/alerts).

## Inbound: Telegram buffers updates for the bot
Telegram will keep bot updates on **Telegram’s servers** for some period so the bot can catch up.

Typical behaviors:
- **Long polling (`getUpdates`)**: the bot asks Telegram for updates, using an `offset` so it doesn’t re-process old ones. If the bot is briefly offline, it can often fetch missed updates when it comes back.
- **Webhook delivery**: Telegram sends HTTP requests to your webhook. Telegram may retry for a limited period if your endpoint is temporarily unavailable.

So inbound is “queue-like”: the bot can often catch up after downtime.

## Outbound: Telegram does NOT buffer messages the bot failed to send
If your bot (OpenClaw) is down at the moment it *would have sent* an alert, Telegram cannot buffer a message that was never submitted.

Outbound reliability requires *your* side to do at least one of:
- **Retry logic** (send again if Telegram API call fails)
- **Durable outbox** (write the intended message to disk/DB first, then a sender worker retries until Telegram confirms)
- **Idempotency** (store Telegram `message_id` / a unique key so retries don’t duplicate)

## Practical rule
- **Don’t worry about missing commands you sent to the bot** (inbound) during short outages — it can usually catch up.
- **Do worry about missing alerts from the bot** (outbound) during outages — fix this with an outbox + retries if it matters.
