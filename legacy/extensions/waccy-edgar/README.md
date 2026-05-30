# waccy-edgar

WACCY extension for SEC EDGAR filing parsing and pattern learning.

## Status

This package provides fixture-first EDGAR/XBRL-shaped extraction, deterministic SEC companyfacts normalization, and the entry point for `ExtractorRegistry` discovery. Live SEC fetching is still kept separate from fixture normalization. The v0.1.0 work is tracked in:

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

Companyfacts JSON can be normalized into WACCY fixture records before extraction:

```python
from waccy_edgar import EdgarCompanyFactsNormalizer, EdgarExtractor

fixture = EdgarCompanyFactsNormalizer().to_fixture(companyfacts_json)
extracted = EdgarExtractor().extract({"fixture": fixture})
```

The normalizer selects annual 10-K facts, preserves fiscal-year and instant-fact provenance, emits `FYyyyy` periods, and carries partial-extraction diagnostics in fixture metadata.

## Development

This package is part of the WACCY monorepo. See the main [README](../README.md) for development setup.
