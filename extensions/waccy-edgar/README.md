# waccy-edgar

WACCY extension for SEC EDGAR filing parsing and pattern learning.

## Installation

```bash
uv pip install waccy-edgar
```

Or install with the core platform:

```bash
uv pip install "waccy[edgar]"
```

## Usage

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("edgar")()

# Extract data from SEC filings
data = extractor.extract({
    "ticker": "AAPL",
    "filing_types": ["10-K", "10-Q"],
    "date_range": ("2022-01-01", "2024-12-31")
})
```

## Development

This package is part of the WACCY monorepo. See the main [README](../README.md) for development setup.

