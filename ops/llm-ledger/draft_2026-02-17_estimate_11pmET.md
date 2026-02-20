Subject: Rough token+cost estimate at 11pm ET (hypothetical Azure GPT-5.2 Global)

Assumptions
- This is a *modeling estimate* only.
- Uses the current OpenClaw /status snapshot for the main chat session (github-copilot/gpt-5.2): ~1,100 input tokens / ~268 output tokens as of ~5:30pm ET.
- Projects linearly from now until 11:00pm ET (scale factor = 23.0h / 17.5h ≈ 1.314).
- Converts tokens → $ using *Azure OpenAI GPT‑5.2 Global* rates (even though the real provider for main chat is Copilot):
  - Input: $1.75 / 1M tokens
  - Output: $14.00 / 1M tokens

Projected tokens by 11:00pm ET
- Input tokens:  ~1,446
- Output tokens: ~352

Projected cost by 11:00pm ET (Azure GPT‑5.2 Global rates)
- Input cost:  ~$0.00253
- Output cost: ~$0.00493
- Total:      ~$0.00746

If you want a less hand-wavy estimate, tell me the window definition (midnight ET → 11pm ET) and we’ll compute from the full-system ledger once it has stable daily coverage.
