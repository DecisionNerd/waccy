# WACCY Experience

This document describes the target user experience for WACCY across its distribution surfaces.

## Primary Users

WACCY should serve people who need professional financial analysis but start from imperfect records:

- advisors and accountants cleaning up small-business financials
- investors, lenders, and buyers evaluating small companies
- operators and founders trying to understand performance and cash flow
- developers building automated finance workflows on Python, Node, or Rust

The product should assume the user is capable and busy. It should avoid magic, expose uncertainty, and make review efficient.

## Distribution Surfaces

WACCY ships the same financial modeling engine across four surfaces:

| Surface | Audience | Install |
|---|---|---|
| CLI (`waccy`) | analysts, power users | `brew install waccy` |
| MCP server (`waccy-mcp`) | AI agent workflows | `claude mcp add waccy $(which waccy-mcp)` |
| Python (`waccy` on PyPI) | data scientists, notebooks | `pip install waccy` |
| Node (`@waccy/core` on npm) | web apps, Next.js, SaaS | `npm install @waccy/core` |

All surfaces share the same Rust core. No surface reimplements financial logic independently.

## CLI Workflow

```bash
# Extract from QuickBooks fixture or live connection
waccy extract quickbooks

# Extract from SEC EDGAR
waccy extract edgar --option cik=0001234567

# Build three-statement model
waccy model

# Inspect results
waccy query "SELECT account_id, period_label, amount FROM records ORDER BY 1, 2"

# Export workbook
waccy model --export xlsx --output model.xlsx
```

## AI Agent Workflow

With the MCP server registered, ask your agent:

> "Build a three-statement model from my QuickBooks data."
> "What drove the change in operating cash flow between 2023 and 2024?"
> "Does the balance sheet balance?"
> "Which accounts couldn't be mapped automatically?"

## Python Workflow

```python
import json
import waccy

# Extract
data_json = waccy.extract_edgar(companyfacts_json, periods=4)
data_json = waccy.extract_qbo(qbo_payload_json)

# Build model
model = json.loads(waccy.build_model(data_json))

# Query results as DataFrame
income_df = waccy.income_statement("2024").to_pandas()
balance_df = waccy.balance_sheet("2024").to_pandas()
cf_df = waccy.cash_flow("2024").to_pandas()
```

## Node / Next.js Workflow

```ts
import { extractEdgar, buildModel, incomeStatement } from '@waccy/core'

// app/api/model/route.ts
export async function POST(req: Request) {
  const { companyfactsJson } = await req.json()
  const dataJson = await extractEdgar(companyfactsJson)
  const model = buildModel(dataJson)
  return Response.json(model)
}

// Server Action
const rows = await incomeStatement("2024")
```

## Data Quality Experience

WACCY treats messy records as normal, not exceptional. When source data is incomplete or ambiguous, the experience should:

- identify the issue clearly with a structured `code` and `message`
- show which source accounts or periods are involved
- explain the likely impact on the model
- provide an override path where appropriate
- preserve the audit trail after correction

Users should be able to answer:

- Which source records produced this line item?
- Which accounts were mapped automatically vs flagged as ambiguous or unmapped?
- Which periods are incomplete?
- Does the balance sheet balance?
- Does cash flow tie to the change in cash?
- What severity are the validation issues?

## v0.1.0 Scope

The first Rust-centered release targets the narrow path that the Python v0.1.0 proved:

1. Load QBO or EDGAR fixture data
2. Normalize source accounts into the WACCY chart of accounts
3. Build a three-statement model
4. Inspect validation issues (balance check, cash-flow tie-out, unmapped accounts)
5. Export to XLSX or pandas DataFrame

Live QBO OAuth, live EDGAR HTTP fetching, and advanced model types (DCF, LBO, comparables) are planned but do not block the first release.
