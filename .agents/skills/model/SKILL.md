---
name: model
description: Build a three-statement financial model (income statement, balance sheet, cash flow) from the extracted dataset.
---

# Build Financial Model

Build an institutional-quality three-statement financial model from extracted data.

## When to Use

- "Build a financial model"
- "Generate the three-statement model"
- "Create income statement, balance sheet, and cash flow"
- "Model my financials"

## Steps

### 1 — Check dataset

Use the `status` MCP tool to confirm data exists. If not, run `/extract` first.

### 2 — Build model

Use the `model` MCP tool:

```
waccy model
```

Or from the CLI:
```bash
waccy model
```

### 3 — Present results

Query and present each statement:
- `/income-statement` — revenue, expenses, net income
- `/balance-sheet` — assets, liabilities, equity
- `/cash-flow` — operating, investing, financing cash flows

Highlight any reconciliation issues (balance sheet doesn't balance, cash flow doesn't tie).

### 4 — Export (optional)

```bash
waccy model --export xlsx --output model.xlsx
```
