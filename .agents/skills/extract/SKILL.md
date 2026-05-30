---
name: extract
description: Extract financial data from QuickBooks Online or SEC EDGAR and build the WACCY dataset.
---

# Extract Financial Data

Extract and load financial data from a supported source.

## When to Use

- "Extract my QuickBooks data"
- "Pull financials from EDGAR for Apple"
- "Update my financial data"
- "Sync my accounting data"

## Steps

### 1 — Identify the source

Ask the user which source to extract from if not specified:
- `quickbooks` — QuickBooks Online (requires OAuth credentials)
- `edgar` — SEC EDGAR (requires a CIK number)

### 2 — Run extraction

**QuickBooks:**
```bash
waccy extract quickbooks
```

**EDGAR:**
```bash
waccy extract edgar --option cik=<CIK>
```

### 3 — Check result

```bash
waccy status
```

Report the number of records extracted and any unmapped accounts.

### 4 — Build model

Offer to run `/model` to build the three-statement model from the extracted data.
