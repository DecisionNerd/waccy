# waccy-quickbooks

WACCY extension for QuickBooks Online integration.

## Installation

```bash
uv pip install waccy-quickbooks
```

Or install with the core platform:

```bash
uv pip install "waccy[quickbooks]"
```

## Usage

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("quickbooks")()

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

