# waccy-edgar

WACCY extension for SEC EDGAR filing parsing and pattern learning.

## Status

This package currently provides the extension package shell and entry point for `ExtractorRegistry` discovery. EDGAR fetching, parsing, and extraction are not implemented yet. The v0.1.0 work is tracked in:

- [#6 Implement EDGAR extraction for comparable three-statement source data](https://github.com/DecisionNerd/waccy/issues/6)
- [#14 Decide and implement EDGAR pattern-learning scope for v0.1.0](https://github.com/DecisionNerd/waccy/issues/14)
- [v0.1.0 milestone](https://github.com/DecisionNerd/waccy/milestone/1)

## Installation

```bash
uv pip install waccy-edgar
```

Or install with the core platform:

```bash
uv pip install "waccy[edgar]"
```

## Current Usage

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("edgar")()
print(extractor.name)
```

The following target API is planned but not runnable yet:

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
