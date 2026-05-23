# WACCY Requirements

WACCY is evolving from a Python-first proof of concept into a multi-language
financial modeling platform. The product requirement is not "a spreadsheet
generator in one language." The requirement is a reliable financial data and
modeling engine that can be embedded from Python, called from Node, and run as a
Rust-backed service.

The durable contract remains:

```text
source data
  -> normalized financial dataset
  -> mapped financial dataset
  -> validated financial dataset
  -> model and metric outputs
  -> exports and downstream APIs
```

The language surfaces must share this contract instead of inventing separate
data shapes.

## Product Scope

WACCY should help developers and analysts turn messy accounting, filing, and
operational data into auditable financial datasets and model outputs. The first
release proved a three-statement vertical slice. The next architecture should
support many model types, multiple runtimes, and a more durable backend.

Required product outcomes:

- load source data from accounting systems, filings, fixtures, and future
  operational sources
- preserve source provenance from extraction through output
- normalize source records into a stable financial dataset contract
- map source accounts and concepts into a canonical WACCY ontology
- validate completeness, balance checks, cash-flow tie-outs, and mapping quality
- build source-agnostic financial models and metrics
- export to XLSX, pandas, JSON, and API-friendly structures
- support Python and Node developers without duplicating modeling logic
- run deterministic, performance-sensitive logic in Rust

## API Surface Requirements

WACCY should expose the same platform through multiple API surfaces.

### Python API

The Python API is for analysts, data scientists, notebooks, backend workers, and
existing Python finance/data ecosystems.

Requirements:

- idiomatic Python package install and imports
- typed models or schema-generated classes for financial datasets
- pandas handoff for downstream modeling and analysis
- XLSX export support
- fixture-first and file-based workflows
- compatibility path for the current `waccy`, `waccy-edgar`, and
  `waccy-quickbooks` users

The Python API should become a thin orchestration and ergonomics layer over the
shared contract and Rust-backed core logic where practical.

### Node API

The Node API is for web apps, SaaS backends, agent tools, serverless workflows,
and JavaScript/TypeScript product teams.

Requirements:

- published npm package with TypeScript types
- JSON-serializable request and response contracts
- model-building, validation, and export APIs equivalent to Python where
  applicable
- browser-safe or server-only boundaries documented clearly
- streaming or async-friendly interfaces for larger jobs
- compatibility with web application frameworks without requiring Python

The Node API should not reimplement financial logic independently. It should call
the same Rust backend or generated bindings/contracts.

### Rust Backend

Rust is the canonical backend for deterministic computation, validation,
mapping, and performance-sensitive model assembly.

Requirements:

- shared financial dataset schema and ontology types
- deterministic mapping and validation engine
- model builders for three-statement models and future model families
- stable serialization format for Python, Node, and service APIs
- test coverage for core financial invariants
- clear FFI, WebAssembly, or service boundary depending on deployment mode

Rust should own the parts where correctness, speed, and cross-language reuse
matter most. Source-specific API clients may remain in Python or Node if that is
where the ecosystem is strongest.

## Data Contract Requirements

All APIs must support the same conceptual data layers.

### Source Data

Source data is source-shaped and provenance-rich. It may come from QBO, EDGAR,
spreadsheets, PDFs, customer uploads, or future operational systems.

Requirements:

- source system and source record identifiers
- source labels, account names, concepts, and metadata
- period labels, dates, units, currency, and statement hints
- raw payload references where safe
- diagnostics for missing, empty, or partial source reports

### Normalized Financial Dataset

The normalized dataset is the shared cross-language input to mapping and
validation.

Requirements:

- entity metadata
- reporting periods
- normalized records with source provenance
- amounts, units, currency, and statement hints
- JSON Schema generated from the Python/Pydantic reference models for the first
  polyglot version
- stable versioning so Python and Node clients can detect compatibility

### Mapped Financial Dataset

The mapped dataset connects normalized records to WACCY canonical accounts.

Requirements:

- canonical account identifiers
- mapping status: mapped, ambiguous, overridden, unmapped
- confidence score and diagnostics
- override metadata
- source provenance preserved

### Validated Financial Dataset

The validated dataset is the required input to source-agnostic model builders.

Requirements:

- validation issues with severity, period, account, and source references
- reconciliation checks
- completeness diagnostics
- machine-readable status for API consumers
- human-readable diagnostics for review workflows

## Ontology Requirements

The WACCY ontology is the canonical financial vocabulary across languages.

Requirements:

- account type and hierarchy
- statement placement
- normal balance and sign convention
- cash-flow classification
- QBO aliases and EDGAR/XBRL aliases
- industry extension points
- versioned schema and migration path

The ontology should be generated or shared across Python, Node, and Rust so
there is one source of truth.

## Model Requirements

Model builders should consume validated datasets and produce source-agnostic
outputs.

Required model families:

- three-statement operating model
- DCF valuation model
- trading comparables
- transaction comparables
- M&A and pro forma model
- LBO model
- credit and covenant model
- SaaS cohort and unit economics model
- FP&A budget vs actual model

The three-statement model remains the foundation. Future models should reuse its
validated data, period handling, sign conventions, and export infrastructure.

## Export And Downstream Requirements

WACCY must support both human review and programmatic handoff.

Required outputs:

- XLSX workbooks with visible checks
- pandas DataFrames for Python workflows
- JSON responses for APIs and Node workflows
- stable model objects for service consumers
- diagnostics suitable for UI display

Optional future outputs:

- Google Sheets
- Arrow/Parquet
- DuckDB-compatible tables
- BI/dashboard payloads

## Quality Requirements

Financial correctness must be measurable and testable.

Requirements:

- source records trace to model lines
- unmapped and ambiguous records are visible
- required periods are detected and validated
- duplicate or malformed periods are rejected
- balance-sheet imbalances are reported
- cash-flow tie-outs are reported
- generated outputs include check rows or equivalent diagnostics
- Python, Node, and Rust tests share fixture expectations where possible

Quality reporting should prioritize actions a user or developer can take.

## Source Requirements

### QBO / QuickBooks

QBO remains the primary small-business accounting source.

Requirements:

- raw report JSON normalization
- chart of accounts metadata
- ProfitAndLoss, BalanceSheet, and CashFlow handling
- empty or partial report diagnostics
- deterministic aliases for common sandbox and live account names
- live pull tooling outside the core modeling engine

### SEC EDGAR

EDGAR remains the primary public-company filing source and pattern corpus.

Requirements:

- company facts ingestion
- XBRL concept mapping
- period selection and date handling
- deterministic pattern learning for classification support
- diagnostics for partial filings or incomplete statement coverage

### Future Sources

Future source packages should be able to target any supported API surface as long
as they emit the shared normalized dataset.

Likely sources:

- Xero, Sage, NetSuite, and other accounting systems
- banking, payments, and payroll systems
- spreadsheets and uploaded workbooks
- PDFs and financial documents
- market data providers
- CRM and sales systems

## Runtime Requirements

The platform should support multiple deployment modes:

- local Python package workflows
- Node server workflows
- Rust CLI or service workflows
- hosted API service
- batch jobs for large filings or portfolios

The same model and validation logic should be reusable across these modes.

## Versioning Requirements

WACCY should version contracts deliberately.

Requirements:

- package versions for Python and Node clients
- crate versions for Rust packages
- schema versions for financial datasets
- root dataset and model outputs include a `schema_version` field
- ontology versions
- migration notes when contracts change
- compatibility tests across Python, Node, and Rust surfaces

## Roadmap Requirements

### Phase One: Multi-Language Contract Foundation

- freeze and version the financial dataset schema
- define Rust core crate boundaries
- generate schemas from the Python/Pydantic reference models for Node and Rust
  consumers
- preserve current Python v0.1.0 behavior during migration
- add cross-language fixture conformance tests

### Phase Two: Rust Core Parity

- port deterministic ontology, mapping, validation, and period logic to Rust
- expose Rust through Python bindings and Node bindings or a service API
- prove parity against existing QBO and EDGAR fixtures
- keep XLSX and pandas handoff available from Python

### Phase Three: Service And Node API

- publish TypeScript package
- expose model-building and validation APIs for web backends
- support async job execution for larger datasets
- add JSON-first diagnostics for product UIs

### Phase Four: Advanced Models

- DCF
- comparables
- transaction and M&A models
- LBO
- credit/covenant
- SaaS and FP&A models

### Phase Five: Decision Support

- scenario management
- sensitivity analysis
- model comparison
- document and source synthesis
- confidence-aware review workflows
