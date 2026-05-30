# WACCY Requirements

WACCY is a polyglot financial modeling platform with a Rust core. The durable pipeline contract is:

```
source data
  → ExtractedData
  → NormalizedFinancialDataset
  → MappedFinancialDataset
  → ValidatedFinancialDataset
  → ThreeStatementModel (and future model families)
  → exports and downstream APIs
```

All language surfaces must share this contract rather than inventing separate data shapes.

## API Surface Requirements

### Rust Core (`waccy-core`)

- shared financial dataset types and ontology
- deterministic mapping and validation engine
- three-statement model builder (and future model families)
- EDGAR and QBO source normalizers
- Parquet storage via Arrow
- Polars DataFrame integration for query and analysis
- stable JSON serialization for cross-language use

### CLI (`waccy`)

- `waccy extract <source>` — normalize source data to `~/.waccy/`
- `waccy model` — build three-statement model, write results
- `waccy status` — dataset metadata and freshness
- `waccy query <sql>` — Polars SQL over the dataset
- `--format table|json|csv` — output format control
- shell completions via `waccy completions`

### MCP Server (`waccy-mcp`)

- JSON-RPC 2.0 over stdio
- tools: `extract`, `model`, `query`, `income_statement`, `balance_sheet`, `cash_flow`, `status`, `schema`
- stateful `QueryEngine` held across requests (no re-parse per call)
- works with Claude Code, Claude Desktop, Cursor, Codex

### Python Package (`waccy` on PyPI)

- `extract_edgar(companyfacts_json)` → JSON string
- `extract_qbo(payload_json)` → JSON string
- `build_model(extracted_json)` → JSON string
- `query(sql)` → `pyarrow.Table`
- `income_statement(period)` → `pyarrow.Table`
- `balance_sheet(period)` → `pyarrow.Table`
- `cash_flow(period)` → `pyarrow.Table`
- built with maturin, returns `pyarrow.Table` (zero-copy Arrow FFI)
- Python 3.11+, macOS and Linux wheels

### Node Package (`@waccy/core` on npm)

- `extractEdgar(json)` → `Promise<object>`
- `extractQbo(json)` → `Promise<object>`
- `buildModel(json)` → `object`
- `query(sql)` → `Promise<object[]>` (Polars DataFrame as plain objects)
- `incomeStatement(period?)` → `Promise<object[]>`
- `balanceSheet(period?)` → `Promise<object[]>`
- `cashFlow(period?)` → `Promise<object[]>`
- built with napi-rs v3, async via `spawn_blocking` over sync Polars
- TypeScript types generated from Rust structs
- Node 18+

## Data Contract Requirements

### ExtractedData

- entity name
- reporting periods (label, start, end, period type)
- source records with full provenance (source system, source ID, account name, account ID, amount, period, statement hint, metadata)
- metadata map for source-specific issues

### NormalizedFinancialDataset

- schema version
- entity name
- periods (inferred from record labels where not explicit)
- records with source provenance preserved
- metadata

### MappedFinancialDataset

- mapped records with canonical account IDs
- mapping status: `mapped`, `ambiguous`, `overridden`, `unmapped`
- confidence score (0.0–1.0)
- mapping diagnostics
- override metadata

### ValidatedFinancialDataset

- all mapped dataset content
- `ValidationIssue[]` with code, message, severity, period, account
- `is_valid()` — no ERROR-severity issues

### ThreeStatementModel

- schema version
- entity name, periods
- income statement, balance sheet, cash flow statement
- each statement: ordered `StatementLine[]` with `values` by period, `is_subtotal`, `is_check`, `source_account_ids`
- `validation_issues[]` including balance check and cash-flow tie-out results

## Ontology Requirements

- 21 canonical accounts across income statement, balance sheet, cash flow statement
- account type, normal balance, cash-flow section
- QBO aliases (common account names, sandbox labels)
- EDGAR/XBRL aliases (us-gaap concept names)
- normalized alphanumeric key matching (case-insensitive, punctuation-stripped)
- statement-hint narrowing for ambiguous candidates
- override mechanism by 4 keys per record (id, name, system:id, system:name)

## Storage Requirements

- Arrow + Parquet for all serialized datasets
- `~/.waccy/` as the default data directory
- one Parquet file per dataset type (records, model lines, metadata)
- ETL metadata JSON for status and incremental support
- Polars `LazyFrame` as the primary query surface over stored data
- `spawn_blocking` wrapping all synchronous Polars operations in the async context

## Quality Requirements

- source records trace to model lines via `source_account_ids`
- unmapped and ambiguous records are surfaced as validation issues
- balance-sheet imbalance reported as ERROR (or WARNING for partial EDGAR extractions)
- cash-flow tie-out mismatch reported as WARNING
- duplicate periods and invalid period ranges reported as ERROR
- all issue codes machine-readable

## Roadmap

### Phase 1 — Foundation (current)

- Rust workspace: `waccy-core`, `waccy-cli`, `waccy-mcp`, `waccy-python`, `waccy-node`
- full pipeline: extract → normalize → map → validate → model
- EDGAR and QBO normalizers
- 21-account ontology
- three-statement model builder
- Arrow + Parquet + Polars storage and query
- Python and Node bindings wired to core
- CLI and MCP tools wired to core
- conformance fixtures and integration tests
- CI, Homebrew, PyPI, npm release automation

### Phase 2 — Live Sources

- QBO OAuth flow and live report pull
- EDGAR live HTTP fetch
- incremental extraction (only new periods)

### Phase 3 — Advanced Models

- DCF valuation
- trading comparables
- M&A / pro forma
- LBO
- credit and covenant
- SaaS unit economics
- FP&A budget vs actual

### Phase 4 — Decision Support

- scenario management and sensitivity analysis
- confidence-aware mapping review UI
- document and source synthesis (LLM-assisted classification for unmapped accounts)
