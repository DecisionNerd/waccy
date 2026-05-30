---
name: balance-sheet
description: Show the balance sheet for the modelled periods — assets, liabilities, and equity.
---

# Balance Sheet

Show the balance sheet from the financial model.

## When to Use

- "Show the balance sheet"
- "What are total assets?"
- "Show liabilities and equity"
- "Does the balance sheet balance?"

## Steps

Use the `balance_sheet` MCP tool, optionally filtered by period:

```
balance_sheet(period="2024")
```

Present the results as a formatted table:

**Assets**
- Cash & Equivalents
- Accounts Receivable
- Inventory
- PPE (net)
- **Total Assets**

**Liabilities**
- Accounts Payable
- Accrued Expenses
- Debt
- **Total Liabilities**

**Equity**
- Retained Earnings
- Total Equity

**Verify: Total Assets = Total Liabilities + Total Equity**

Flag any imbalance as a reconciliation error.
