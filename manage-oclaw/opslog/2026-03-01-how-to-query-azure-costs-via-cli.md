# How to Query Azure Costs via CLI (Cost Management REST API)

**Date:** 2026-03-01
**Applies to:** All Azure costs (AI Foundry, VMs, Storage, etc.)

---

## Overview

The `az costmanagement` extension only has `export` — no query command. Use `az rest` against the Cost Management REST API directly.

## Prerequisites

```bash
az login
az account show  # verify correct subscription
```

## Basic Query — All Services

```bash
SUB_ID=$(az account show --query id -o tsv)

az rest --method post \
  --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {
      "from": "2026-01-01",
      "to": "2026-03-01"
    },
    "dataset": {
      "granularity": "None",
      "aggregation": {
        "totalCost": { "name": "Cost", "function": "Sum" }
      },
      "grouping": [
        { "type": "Dimension", "name": "ServiceName" }
      ]
    }
  }' -o json
```

## AI Foundry Only — With Monthly Breakdown

```bash
az rest --method post \
  --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {
      "from": "2026-02-01",
      "to": "2026-03-01"
    },
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {
        "totalCost": { "name": "Cost", "function": "Sum" }
      },
      "grouping": [
        { "type": "Dimension", "name": "ServiceName" },
        { "type": "Dimension", "name": "MeterSubcategory" }
      ],
      "filter": {
        "or": [
          { "dimensions": { "name": "ServiceName", "operator": "In", "values": ["Foundry Models", "Foundry Tools"] } },
          { "dimensions": { "name": "ServiceName", "operator": "In", "values": ["Azure Cognitive Search"] } }
        ]
      }
    }
  }' -o json
```

## Per-Model Breakdown (Meter + Product)

```bash
az rest --method post \
  --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {
      "from": "2026-02-01",
      "to": "2026-03-01"
    },
    "dataset": {
      "granularity": "None",
      "aggregation": {
        "totalCost": { "name": "Cost", "function": "Sum" }
      },
      "grouping": [
        { "type": "Dimension", "name": "Meter" },
        { "type": "Dimension", "name": "Product" }
      ],
      "filter": {
        "dimensions": {
          "name": "ServiceName",
          "operator": "In",
          "values": ["Foundry Models", "Foundry Tools"]
        }
      }
    }
  }' -o json
```

## Key Reference

### Service Names (as they appear in Cost Management)

| Service Name | What It Covers |
|-------------|----------------|
| `Foundry Models` | All inference: GPT-4.1, GPT-4.1-mini, GPT-5.2, Kimi, embeddings |
| `Foundry Tools` | Observability, evaluations |
| `Azure Cognitive Search` | AI Search (basic tier) |
| `Virtual Machines` | Compute |
| `Storage` | Blob, disks, etc. |
| `Bandwidth` | Egress |
| `Microsoft Defender for Cloud` | Security |

### Valid Grouping Dimensions

`ResourceGroup`, `ResourceGroupName`, `ResourceType`, `ResourceId`, `ResourceLocation`, `SubscriptionId`, `SubscriptionName`, `MeterCategory`, `MeterSubcategory`, `Meter`, `ServiceFamily`, `UnitOfMeasure`, `PartNumber`, `Product`, `ResourceGuid`, `ChargeType`, `ServiceName`, `ProductOrderId`, `ProductOrderName`, `PublisherType`, `Frequency`, `PricingModel`, `BillingMonth`, `Provider`

**NOT valid:** `MeterName` (use `Meter` instead)

### Timeframe Options

- `Custom` (requires `timePeriod` with `from`/`to`)
- `MonthToDate`
- `TheLastMonth`
- `TheLastBillingMonth`

### Granularity Options

- `None` — single total
- `Monthly` — per-month rows
- `Daily` — per-day rows

### Filter Syntax

Single filter:
```json
{ "dimensions": { "name": "ServiceName", "operator": "In", "values": ["Foundry Models"] } }
```

Multiple filters (need `or`/`and` with 2+ expressions):
```json
{
  "or": [
    { "dimensions": { "name": "ServiceName", "operator": "In", "values": ["Foundry Models", "Foundry Tools"] } },
    { "dimensions": { "name": "ServiceName", "operator": "In", "values": ["Azure Cognitive Search"] } }
  ]
}
```

## Gotchas

- **Rate limit:** ~3 requests per 10 seconds. Wait 10s between calls if you get 429.
- **`or`/`and` filters require 2+ expressions** — single-item `or` returns Bad Request.
- **Dimension names are case-sensitive** — `ServiceName` not `servicename`.
- **Max 2 grouping dimensions** per query.
- **`az costmanagement query` does not exist** — only `export` and `show-operation-result`.
