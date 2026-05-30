---
name: cash-flow
description: Show the cash flow statement for the modelled periods — operating, investing, and financing activities.
---

# Cash Flow Statement

Show the cash flow statement from the financial model.

## When to Use

- "Show the cash flow statement"
- "What's the operating cash flow?"
- "How much did we spend on capex?"
- "Show financing activities"

## Steps

Use the `cash_flow` MCP tool, optionally filtered by period:

```
cash_flow(period="2024")
```

Present the results as a formatted table:

**Operating Activities**
- Net Income
- + D&A
- ± Working Capital changes
- **Cash from Operations**

**Investing Activities**
- Capital Expenditures (CapEx)
- **Cash from Investing**

**Financing Activities**
- Debt proceeds / repayments
- **Cash from Financing**

**Net Change in Cash**
**Verify: ties to balance sheet cash change**
