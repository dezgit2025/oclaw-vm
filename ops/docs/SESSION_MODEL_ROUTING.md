# Session-Level Model Routing Feature

## Overview
This feature allows the user to dynamically switch the main reasoning model for the current session via natural language commands in Telegram chat. It includes forced model locks, toggle/reset commands, fallback handling, and logging.

## Current Implementation Status

### ✅ Completed
- **"think hard" command:** Detects phrase in user input, sets session-level forced model to `github-copilot/gpt-5.2` for the session.
- **"default thinking" command:** Reverts session routing back to the default model with user confirmation (yes/no).
- **Token limit fallback:** When forced model hits token limits, auto-falls back to `github-copilot/gpt-5.2`, logs the event, and alerts the user.
- **Fallback script tested and working.**

### ❌ Not Yet Implemented
- **3-hour time-based expiration:** Session forced model currently persists for the entire session with no auto-revert timer.
- **Auto-revert after expiration:** No logic to check timestamps and clear forced model after duration expires.
- **User-specified custom duration:** e.g., "use Opus 4.6 for 1 hour."
- **Pre/post switch model testing:** Validating the target model works before and after switching.
- **Model selection by name:** e.g., "for this session use Opus 4.6" with dynamic model parsing.

---

## Architecture

### Components

| Component | Location | Description |
|-----------|----------|-------------|
| Routing hook (JS) | `ops/hooks/gateway_model_routing_hook.js` | Main routing logic: detects commands, sets session flags, routes to forced or default model |
| Fallback script (Python) | `ops/scripts/model_fallback_routing.py` | Token limit error detection, fallback execution, logging, and alerting |
| Fallback test script | `ops/scripts/test_model_fallback.py` | Unit test simulating token limit error and verifying fallback behavior |

### Flow Diagram

```
User Prompt
    │
    ▼
Detect "think hard" or "default thinking" command
    │
    ├─ "think hard" → Set session.forced_model = GPT-5.2
    │                  Notify user: "Engaged GPT-5.2 for this session."
    │
    ├─ "default thinking" → Ask user for confirmation
    │       ├─ yes → Clear forced_model, revert to default routing
    │       └─ no  → Keep forced model active
    │
    ▼
Check session.forced_model flag
    ├─ If set → Route to forced model
    │       ├─ Success → Return response
    │       └─ Token limit error → Log + Alert + Fallback to GPT-5.2
    │
    └─ If not set → Use default routing logic
```

---

## Routing Hook Code (Current)

**File:** `ops/hooks/gateway_model_routing_hook.js`

```javascript
const sessionForcedFlagKey = 'forced_model';
const sessionToggleConfirmKey = 'awaiting_toggle_confirm';

async function sendMessageToUser(sessionId, message) {
  console.log(`Message to session ${sessionId}: ${message}`);
}

async function routeModel(session, prompt) {
  const lowerPrompt = prompt.toLowerCase();

  if (lowerPrompt.includes('think hard')) {
    session[sessionForcedFlagKey] = 'github-copilot/gpt-5.2';
    session[sessionToggleConfirmKey] = false;
    console.log(`Session ${session.id}: Forced model set to GPT-5.2.`);
    await sendMessageToUser(session.id, "Engaged GPT-5.2 for this session.");
  }

  if (lowerPrompt.includes('default thinking')) {
    session[sessionToggleConfirmKey] = true;
    await sendMessageToUser(session.id, "Switch back to default model? Reply yes or no.");
  }

  if (session[sessionToggleConfirmKey]) {
    if (lowerPrompt.match(/^(yes|confirm|yep)$/)) {
      delete session[sessionForcedFlagKey];
      session[sessionToggleConfirmKey] = false;
      await sendMessageToUser(session.id, "Model routing reset to default.");
      return defaultRouting(session, prompt);
    } else if (lowerPrompt.match(/^(no|cancel|stop)$/)) {
      session[sessionToggleConfirmKey] = false;
      await sendMessageToUser(session.id, "Continuing with forced model.");
    }
  }

  if (session[sessionForcedFlagKey]) {
    return callModelAPI(session[sessionForcedFlagKey], prompt);
  }

  return defaultRouting(session, prompt);
}
```

---

## Fallback Logic Code (Current)

**File:** `ops/scripts/model_fallback_routing.py`

```python
def call_forced_model_with_fallback(session, prompt):
    forced_model = session.get('forced_model')
    if not forced_model:
        return call_model_api('default', prompt)

    try:
        response = call_model_api(forced_model, prompt)
        return response
    except TokenLimitError as e:
        fallback_model = 'github-copilot/gpt-5.2'
        log_fallback(session, forced_model, e, prompt, fallback_model)
        alert_user(session, f"Model {forced_model} hit token limit; falling back to {fallback_model}.")
        session.pop('forced_model', None)
        session.pop('model_expiration', None)
        response = call_model_api(fallback_model, prompt)
        return response
    except Exception as e:
        raise
```

---

## Planned Enhancements

1. **3-hour timed expiration** with auto-revert to default model.
2. **Custom duration support** via user command parsing (e.g., "use Opus 4.6 for 1 hour").
3. **Pre/post switch model testing** to validate availability before committing.
4. **Dynamic model name parsing** from user input (e.g., "for this session use Opus 4.6").
5. **Feature flag toggle** to enable/disable the routing override for debugging.

---

## Related Configuration

- Primary model: `github-copilot/claude-opus-4.6`
- Fallback model: `github-copilot/gpt-5.2`
- Heartbeat model: `foundry/gpt-4.1-mini`
- Config file: `~/.openclaw/openclaw.json`

---

*Last updated: 2026-02-21*
