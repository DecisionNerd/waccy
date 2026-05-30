---
name: query
description: Execute SQL against the WACCY financial dataset to answer specific questions about the data.
---

# Query Financial Data

Run arbitrary SQL queries against the financial dataset.

## When to Use

- "Query the financial data"
- "How much revenue did we have in 2024?"
- "Show me all expense accounts"
- "What are the top expense categories?"

## Steps

Use the `query` MCP tool with a SQL statement. The primary table is `records` with columns:
- `source` — data source (quickbooks, edgar)
- `account_id` — standard account identifier
- `account_name` — display name
- `statement_kind` — income_statement / balance_sheet / cash_flow_statement
- `period_label` — e.g. 2024, 2024-Q1
- `amount` — numeric value
- `currency` — e.g. USD

Example queries:
```sql
-- Total revenue by period
SELECT period_label, SUM(amount) as revenue
FROM records WHERE account_id = 'revenue'
GROUP BY period_label ORDER BY period_label

-- All expense accounts
SELECT account_name, SUM(amount) as total
FROM records WHERE statement_kind = 'income_statement'
  AND account_type = 'expense'
GROUP BY account_name ORDER BY total DESC
```
