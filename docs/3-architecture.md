# WACCY Architecture

## Overview

WACCY is a Rust-centered polyglot financial modeling platform. The Rust core owns all deterministic financial logic — ontology, mapping, validation, model assembly, storage, and query. Python and Node are first-class distribution surfaces backed by the same core via native bindings.

```
┌─────────────────────────────────────────────────┐
│              Distribution surfaces               │
│  CLI (waccy)  MCP (waccy-mcp)  Python   Node    │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  waccy-core                      │
│  models · ontology · extraction · classification │
│  validation · modeling · storage · query         │
└──────────────────────┬──────────────────────────┘
                       │
            Arrow + Parquet (storage)
            Polars (query / analysis)
```

## Repository Layout

```
waccy/
├── crates/
│   ├── waccy-core/          # Rust library — all financial logic
│   ├── waccy-cli/           # Binary: waccy CLI (clap)
│   ├── waccy-mcp/           # Binary: waccy-mcp MCP server (JSON-RPC 2.0 / stdio)
│   ├── waccy-python/        # PyO3 cdylib (maturin) — Python bindings
│   └── waccy-node/          # napi-rs cdylib — Node.js native addon
├── docs/
│   └── adr/                 # Architecture decision records
├── tests/                   # Rust integration tests + conformance fixtures
├── Formula/waccy.rb         # Homebrew formula (reference copy)
├── scripts/install.sh       # Universal install + MCP registration script
├── .agents/skills/          # Agent skills for npx skills add
├── justfile                 # Development recipes
├── Cargo.toml               # Workspace root
└── legacy/                  # Python v0.1.0 (archived reference)
```

## waccy-core Modules

```
waccy-core/src/
├── models.rs            # All shared types (CONTRACT_SCHEMA_VERSION = "1.0.0")
├── error.rs             # WaccyError enum
├── extraction/
│   ├── mod.rs           # Extractor trait, registry, normalize(), normalize_map_validate()
│   ├── edgar.rs         # normalize_companyfacts() — SEC EDGAR → ExtractedData
│   └── qbo.rs           # normalize_qbo_reports() — QBO raw reports → ExtractedData
├── classification/
│   ├── mod.rs           # DataMapper — map NormalizedFinancialDataset → MappedFinancialDataset
│   └── ontology.rs      # StandardChartOfAccounts (21 accounts, full alias tables)
├── validation.rs        # validate_mapped_dataset() — issues, severity, period checks
├── modeling/
│   └── mod.rs           # ModelBuilder, ModelInput — three-statement model assembly
├── query/
│   └── mod.rs           # QueryEngine — Polars LazyFrame over stored Parquet
├── storage/             # (TODO) Parquet read/write, ETL metadata
└── utils/
    └── dates.rs         # infer_reporting_period() — "2024", "2024Q1", "FY2024", "2024-06"
```

## Pipeline

```
source payload (JSON)
        │
        ▼
  extract_edgar()         extract_qbo()
  normalize_companyfacts()  normalize_qbo_reports()
        │                        │
        └──────────┬─────────────┘
                   ▼
            ExtractedData
                   │
                   ▼
             normalize()              ← infers periods from record labels
                   │
                   ▼
     NormalizedFinancialDataset
                   │
                   ▼
          DataMapper::map()           ← alias lookup, statement-hint narrowing, overrides
                   │
                   ▼
      MappedFinancialDataset
                   │
                   ▼
     validate_mapped_dataset()        ← period checks, unmapped/ambiguous issues
                   │
                   ▼
     ValidatedFinancialDataset
                   │
                   ▼
        ModelBuilder::build()         ← income stmt, balance sheet, cash flow
                   │                    balance check, cash-flow tie-out
                   ▼
       ThreeStatementModel
                   │
          ┌────────┴────────┐
          ▼                 ▼
      storage           export
  (Arrow/Parquet)    (XLSX, JSON, DataFrame)
```

## Storage and Query

See [ADR-001](engineering/adr/001-polars-over-datafusion.md) for the decision to use Polars + Arrow over DataFusion.

**Storage:** Arrow + Parquet via the `arrow` and `parquet` crates. The default data directory is `~/.waccy/`. One Parquet file per dataset type. ETL metadata written as JSON.

**Query:** Polars `LazyFrame` is the primary query surface. It handles filter, pivot, groupby, and period comparison natively without a SQL engine overhead.

**Async boundary:** Polars operations are synchronous CPU-bound work. In async contexts (MCP server, Node napi, Python with async callers) they run inside `tokio::task::spawn_blocking` so the executor is never blocked.

```rust
// Pattern used throughout async contexts
let result = tokio::task::spawn_blocking(move || {
    polars_query(data_dir, filter)
}).await??;
```

## Ontology

The standard chart of accounts has 21 canonical accounts:

| ID | Statement | Type |
|---|---|---|
| `revenue` | Income Statement | Revenue |
| `cogs` | Income Statement | Expense |
| `operating_expenses` | Income Statement | Expense |
| `depreciation_amortization` | Income Statement | Expense |
| `interest_expense` | Income Statement | Expense |
| `tax_expense` | Income Statement | Expense |
| `cash` | Balance Sheet | Asset |
| `accounts_receivable` | Balance Sheet | Asset |
| `inventory` | Balance Sheet | Asset |
| `ppe` | Balance Sheet | Asset |
| `accumulated_depreciation` | Balance Sheet | Asset |
| `accounts_payable` | Balance Sheet | Liability |
| `accrued_expenses` | Balance Sheet | Liability |
| `debt` | Balance Sheet | Liability |
| `equity` | Balance Sheet | Equity |
| `retained_earnings` | Balance Sheet | Equity |
| `net_income` | Cash Flow | CashFlow (Operating) |
| `depreciation_addback` | Cash Flow | CashFlow (Operating) |
| `working_capital_movement` | Cash Flow | CashFlow (Operating) |
| `capex` | Cash Flow | CashFlow (Investing) |
| `financing_movement` | Cash Flow | CashFlow (Financing) |

Each account carries QBO aliases (common account names and sandbox labels) and EDGAR/XBRL aliases (us-gaap concept names). Matching normalizes to an alphanumeric key — case-insensitive, punctuation-stripped — before lookup.

## Architectural Principles

- **One engine, many surfaces** — Python and Node call the same Rust core. Financial rules are never duplicated.
- **Rust owns correctness** — ontology, mapping, validation, reconciliation, and model assembly live in `waccy-core`.
- **Source adapters stay pragmatic** — QBO and EDGAR normalizers are in Rust now; future adapters can live in the language with the best ecosystem as long as they emit `ExtractedData`.
- **Deterministic first** — explicit rules before any LLM-assisted classification.
- **Audit trail always** — source provenance is preserved from extraction through model output.
- **Async at the boundary, sync in the core** — I/O and network calls are async; Polars and model computation are synchronous behind `spawn_blocking`.

## Distribution

| Artifact | Registry | Build |
|---|---|---|
| `waccy` + `waccy-mcp` binaries | GitHub Releases + Homebrew tap | `cargo build --release` |
| `waccy` Python wheel | PyPI | `maturin build --release` |
| `@waccy/core` Node addon | npm | `napi build --platform --release` |
| Agent skills | `npx skills add DecisionNerd/waccy` | `.agents/skills/` SKILL.md files |

Release workflow: git tag → `release.yml` → builds binaries, creates GitHub Release, opens Homebrew PR, triggers Python wheel builds, publishes to PyPI and npm.
