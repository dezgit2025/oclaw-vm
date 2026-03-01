# Azure AI Foundry Cost Report — February 2026

**Subscription:** MCAPS-Hybrid-REQ-129391-2025-dvillanueva
**Tenant:** 16b3c013-d300-468d-ac64-7eda0820b6d3
**Region:** US East 2
**Period:** Jan 1 – Mar 1, 2026 (primarily February usage)
**Generated:** 2026-03-01

---

## Summary

| Category | Cost (USD) |
|----------|-----------|
| Foundry Models (inference) | $129.90 |
| Foundry Tools (observability) | $1.97 |
| Azure Cognitive Search (AI Search) | $16.47 |
| **Grand Total** | **$148.35** |

---

## Foundry Models — By Month

| Month | Sub-Category | Cost (USD) |
|-------|-------------|-----------|
| January | Azure OpenAI | $0.44 |
| February | Azure OpenAI | $97.40 |
| February | Azure OpenAI GPT5 | $11.15 |
| February | Azure Kimi | $2.74 |
| March (1 day) | Azure OpenAI | $6.20 |

---

## Foundry Models — By Model (Jan–Feb Total)

| Model | Cost (USD) | Breakdown |
|-------|-----------|-----------|
| GPT-4.1 mini | $112.36 | $77.09 cached input + $34.10 input + $1.16 output |
| GPT-5.2 | $11.15 | $7.39 input + $3.57 output + $0.19 cached input |
| Kimi K2.5 Thinking | $2.74 | $2.67 input + $0.07 output |
| GPT-4.1 | $1.66 | $0.82 input + $0.57 output + $0.26 cached input |
| GPT-4o (0806) | $0.03 | $0.005 input + $0.019 output + $0.004 cached input |
| GPT-4o-mini (0718) | $0.001 | Negligible |
| text-embedding-3-large | $0.000005 | Negligible |

---

## Foundry Tools

| Meter | Cost (USD) |
|-------|-----------|
| Evaluations input tokens | $1.74 |
| Evaluations output tokens | $0.24 |
| **Total** | **$1.97** |

---

## Azure Cognitive Search

| Month | Cost (USD) |
|-------|-----------|
| February | $14.85 |
| March (1 day) | $1.62 |
| **Total** | **$16.47** |

---

## Notes

- GPT-4.1 mini is ~85% of Foundry inference spend, driven by cached input tokens (ClawBot memory extraction/hooks)
- Azure Cognitive Search cost is AI Search basic tier (flat-rate ~$74/mo prorated — only $16.47 here suggests partial month or shared billing)
- Cost Management API query method: `az rest --method post` to `/subscriptions/{id}/providers/Microsoft.CostManagement/query?api-version=2023-11-01`
- Service names in Cost Management: `Foundry Models`, `Foundry Tools`, `Azure Cognitive Search`
