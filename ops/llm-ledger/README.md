# LLM Ledger + Cost Reporting

This folder documents and scripts the “full system model ledger” and monthly cost reports.

## Data sources

- Full-system daily ledger (JSONL):
  - `./logs/llm_full_ledger_daily.jsonl`
- Ledger state (for daily deltas):
  - `./logs/llm_full_ledger_state.json`
- Legacy main-session snapshots (older):
  - `./logs/llm_token_snapshots.jsonl`

## Scripts

- Full-system daily ledger writer:
  - `/home/desazure/.openclaw/workspace/scripts/llm_full_ledger.py`
  - Runs nightly via cron (10pm ET).

- Monthly cost report:
  - `./monthly_cost_report.py`
  - Uses `./pricing_usd_per_1m_tokens.json` for rates.

## Pricing

Rates are stored in:
- `./pricing_usd_per_1m_tokens.json`

Notes:
- Azure OpenAI pricing varies by SKU (Global vs Regional vs Data Zone). If you change deployment type, update this file.

## Cron

- Nightly full-system token ledger: writes daily rows.
- Monthly cost report: posts a summary on the 1st of the month.
