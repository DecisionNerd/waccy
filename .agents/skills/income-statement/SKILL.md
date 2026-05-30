---
name: income-statement
description: Show the income statement (P&L) for the modelled periods — revenue, expenses, and net income.
---

# Income Statement

Show the income statement for the financial model.

## When to Use

- "Show the income statement"
- "What's the P&L?"
- "Show revenue and expenses"
- "What was net income?"

## Steps

Use the `income_statement` MCP tool, optionally filtered by period:

```
income_statement(period="2024")
```

Present the results as a formatted table:
- Revenue
- Cost of Goods Sold
- Gross Profit
- Operating Expenses
- EBITDA
- D&A
- EBIT
- Interest
- EBT
- Tax
- **Net Income**

Highlight year-over-year changes where multiple periods are available.
