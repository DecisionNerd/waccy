# WACCY Testing and Quality

WACCY's testing strategy protects financial correctness across all surfaces. The goal is not just green tests — it is provable behavioral parity between Rust, Python, and Node against the same fixture expectations.

## Quality Standard

Every meaningful change should answer three questions before it merges:

- Does it satisfy the user-visible outcome described by the issue?
- Do the financial calculations, mappings, validations, and model outputs remain correct?
- Can a reviewer trust the checks without manually reconstructing the pipeline?

## Test Layers

```
Rust unit tests        — deterministic logic in models, ontology, mapping, validation, dates
Rust integration tests — full pipeline: ExtractedData → ThreeStatementModel
Conformance fixtures   — shared JSON expectations, consumed by Rust, Python, and Node
Python wheel tests     — maturin build + import + smoke test
Node addon tests       — napi build + import + smoke test
CI checks              — fmt, clippy, cargo test, wheel build, addon build
```

## Local Development

```bash
# Rust
cargo test --all           # all unit and integration tests
cargo clippy --all-targets -- -D warnings
cargo fmt --check

# Full setup via justfile
just test
just lint

# Python wheel (requires maturin)
cd crates/waccy-python && maturin develop && python -c "import waccy; print(waccy.__version__)"

# Node addon (requires @napi-rs/cli)
cd crates/waccy-node && npx napi build --platform && node -e "const w = require('.'); console.log(Object.keys(w))"
```

## Conformance Fixtures

Cross-language conformance fixtures live under `tests/conformance/`. Each source case contains expected pipeline outputs that all three language surfaces must match.

```
tests/conformance/
├── qbo/
│   ├── source-fixture.json        # raw QBO report payload
│   ├── expected-extracted.json    # ExtractedData
│   ├── expected-normalized.json   # NormalizedFinancialDataset
│   ├── expected-mapped.json       # MappedFinancialDataset
│   ├── expected-validated.json    # ValidatedFinancialDataset
│   └── expected-model.json        # ThreeStatementModel
└── edgar/
    ├── source-fixture.json        # companyfacts payload
    ├── expected-extracted.json
    ├── expected-normalized.json
    ├── expected-mapped.json
    ├── expected-validated.json
    └── expected-model.json
```

Conformance fixture changes must be reviewed carefully — they represent a change in the cross-language contract, not just a test update.

## Key Financial Invariants

Integration tests should assert these invariants on the conformance fixtures:

- three statements produced (income, balance sheet, cash flow)
- balance sheet check = 0 (or WARNING with EDGAR partial extraction flag)
- cash-flow tie-out = 0 for periods after the first
- no ERROR-severity validation issues on clean fixtures
- all source account IDs traceable via `source_account_ids` on statement lines
- known QBO account names map to expected canonical account IDs
- known EDGAR XBRL concepts map to expected canonical account IDs

## CI

GitHub Actions runs three jobs on every push and PR:

**test** (macos-14):
- `cargo fmt --all -- --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test --all`

**python** (macos-14):
- `maturin build --release` (wheel build check)

**node** (macos-14):
- `napi build --platform --release` (addon build check)

## Release Smoke Tests

The release workflow runs smoke tests before publishing:

```bash
# Python
python -c "import waccy; assert waccy.__version__ == '0.x.x'"

# Node
node -e "const w = require('@waccy/core'); ['query','buildModel','extractEdgar'].forEach(f => { if (!w[f]) throw new Error(f + ' missing') })"

# CLI
waccy --version
waccy-mcp --version
```

## Financial Correctness Focus

Coverage numbers are a guardrail, not the quality signal. Tests should exercise behavior that matters:

- ambiguous account names resolve correctly after statement-hint narrowing
- parenthesized negatives in QBO amounts parse correctly
- EDGAR `latest-by-fiscal-year` selection chooses the most recent filing
- `infer_reporting_period` handles "2024", "2024Q1", "FY2024", "2024-06"
- balance check fires on an unbalanced fixture
- cash-flow tie-out fires when cash change doesn't match
- overrides by all four keys (id, name, system:id, system:name) work
- `is_summary_check` metadata suppresses ERROR to INFO for QBO net-change row

Avoid superficial tests that only execute lines without protecting an outcome.
