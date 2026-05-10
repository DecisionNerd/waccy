# waccy-quickbooks

WACCY extension for QuickBooks Online integration.

## Status

This package provides fixture-first QuickBooks/QBO-shaped extraction, the entry point for `ExtractorRegistry` discovery, and a small typed live-pull helper for OAuth-backed QBO reports. The live helper intentionally returns raw QBO JSON; WACCY's model-building contract still begins after source data is normalized into WACCY records. The v0.1.0 work is tracked in:

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

## Fixture Usage

```python
from waccy.extraction import ExtractorRegistry

registry = ExtractorRegistry()
extractor = registry.get_extractor("qbo")()
print(extractor.name)
```

## Live QBO Report Pull

Use Intuit OAuth to create or refresh a token, then pull raw company info, chart of accounts, and reports. Store the token cache in a caller-owned path; do not commit it.

```python
from datetime import date

from waccy_quickbooks import (
    FileTokenCache,
    QuickBooksApiClient,
    QuickBooksOAuthConfig,
)

config = QuickBooksOAuthConfig(
    client_id="...",
    client_secret="...",
    redirect_uri="http://localhost:8765/callback",
    environment="sandbox",
)
cache = FileTokenCache("~/.waccy/qbo-token.json")
client = QuickBooksApiClient.from_token_cache(cache, config)

pull = client.pull_financial_reports(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
)
```

The returned `QuickBooksReportPull` carries raw `CompanyInfo`, `Account`, `ProfitAndLoss`, `BalanceSheet`, and `CashFlow` payloads. Convert that raw pull into WACCY source records with the report normalizer:

```python
from waccy_quickbooks import QuickBooksExtractor, QuickBooksReportNormalizer

fixture = QuickBooksReportNormalizer().to_fixture(pull)
extracted = QuickBooksExtractor().extract({"fixture": fixture})
```

The normalizer preserves QBO report provenance in record metadata, detects `NoReportData` reports, and emits source-completeness diagnostics for missing required statements. Keep live pull artifacts and token caches out of git. Use sanitized raw fixtures for repeatable CI/local smoke tests.

## Development

This package is part of the WACCY monorepo. See the main [README](../README.md) for development setup.
