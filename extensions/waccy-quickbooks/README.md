# waccy-quickbooks

WACCY extension for QuickBooks Online integration.

## Status

This package currently provides fixture-first QuickBooks/QBO-shaped extraction and the entry point for `ExtractorRegistry` discovery. Live QuickBooks OAuth and API extraction are not implemented yet. The v0.1.0 work is tracked in:

- [#5 Implement QuickBooks/QBO extraction for three-statement source data](https://github.com/DecisionNerd/waccy/issues/5)
- [v0.1.0 milestone](https://github.com/DecisionNerd/waccy/milestone/1)

## Installation

```bash
uv pip install waccy-quickbooks
```

Or install with the core platform:

```bash
uv pip install "waccy[quickbooks]"
```

## Current Usage

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("qbo")()
print(extractor.name)
```

The following live API path is planned but not runnable yet:

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("qbo")()

# Authenticate
extractor.authenticate({
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "access_token": "your_access_token"
})

# Extract data
data = extractor.extract({
    "company_id": "your_company_id",
    "date_range": ("2023-01-01", "2024-12-31")
})
```

## Development

This package is part of the WACCY monorepo. See the main [README](../README.md) for development setup.
