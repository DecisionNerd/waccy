---
name: waccy-status
description: Show the current status of the WACCY dataset — last extraction time, record count, and whether it's up to date.
---

# WACCY Status

Check the status of the current financial dataset.

## When to Use

- "What's the status of my financial data?"
- "When was waccy last updated?"
- "How many records does waccy have?"

## Steps

Call the `status` MCP tool:

```
waccy status
```

Report:
- Whether a dataset exists
- Last extraction time
- Number of records
- Data directory path

If no dataset exists, suggest: `waccy extract quickbooks` or `waccy extract edgar`.
