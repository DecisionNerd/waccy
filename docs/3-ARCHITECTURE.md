# WACCY Architecture

## Overview

WACCY is moving toward a polyglot architecture:

- **Rust backend**: canonical deterministic engine for schemas, ontology,
  mapping, validation, and model construction.
- **Python API**: analyst and data-science surface, pandas/XLSX integration, and
  compatibility path for the existing Python package.
- **Node API**: TypeScript surface for web apps, SaaS products, agent tools, and
  server-side JavaScript workflows.

The architectural goal is one financial modeling contract with multiple
language-native entry points.

```text
Python API         Node API          Hosted/API clients
    \                |                 /
     \               |                /
      -> shared schema and transport ->
                    |
              Rust backend
                    |
      ontology, mapping, validation, models
                    |
       exports, diagnostics, model outputs
```

## Current Implementation Status

The published v0.1.0 release is Python-first:

- `waccy` is `0.1.0`
- `waccy-edgar` is `0.1.0`
- `waccy-quickbooks` is `0.1.1`

The current Python implementation is the reference behavior for the first
vertical slice: QBO and EDGAR inputs, canonical mapping, validation,
three-statement model output, XLSX export, and pandas handoff.

The next architecture should treat that Python implementation as a working
reference, not as the final core boundary. Rust should become the canonical
engine as parity is established.

## Architectural Principles

- **One contract, many APIs**: Python and Node should expose the same financial
  dataset and model concepts.
- **Rust owns deterministic logic**: schema validation, ontology mapping,
  reconciliation, and model assembly should converge in Rust.
- **Source adapters stay pragmatic**: QBO, EDGAR, and future source clients can
  live in the language with the best ecosystem, as long as they emit the shared
  normalized dataset.
- **No duplicated financial rules**: Python and Node wrappers should not drift
  into separate financial engines.
- **API-first diagnostics**: validation and mapping issues should be structured
  enough for CLIs, notebooks, web UIs, and hosted APIs.
- **Migration without breakage**: current Python users should keep a coherent
  path while internals move toward Rust.

## Layered Data Contract

The durable WACCY pipeline remains:

```text
source extractor
  -> raw extracted data
  -> normalized financial dataset
  -> mapped financial dataset
  -> validated financial dataset
  -> model and metric builders
  -> exporters and API responses
```

### Source Extractor

Extractors are source-specific. They read QBO, EDGAR, or another source and
return source records with provenance. Extractors should not build financial
models.

### Raw Extracted Data

Raw extracted data preserves source-native concepts: account names, account IDs,
statement labels, transaction IDs, dates, periods, units, and metadata. This is
the audit and debugging layer.

### Normalized Financial Dataset

The normalized dataset is the cross-language contract between extraction and
downstream analysis. It should be serializable and versioned so Python, Node, and
Rust all agree on its shape.

### Mapped Financial Dataset

The mapped dataset connects normalized records to the WACCY ontology. It adds
canonical account IDs, confidence, review status, ambiguity diagnostics, and
optional user overrides.

### Validated Financial Dataset

The validated dataset adds quality and reconciliation results. Model and metric
builders should consume this layer rather than raw source data.

### Model And Metric Builders

Builders are source-agnostic. Three-statement, DCF, comparables, SaaS metrics,
covenants, and LBO builders should consume validated datasets and ontology
metadata.

### Exporters And API Responses

Exporters render model or metric outputs into files or external systems. The
same output object should support XLSX, pandas, JSON, and future API formats
where practical.

## Target Repository Shape

The current repository is Python-first. A Rust and Node architecture should grow
into a monorepo shape like this:

```text
waccy/
├── crates/
│   ├── waccy-core/              # Rust schemas, ontology, validation, models
│   ├── waccy-ffi/               # Optional FFI boundary for Python/Node
│   └── waccy-service/           # Optional HTTP/job service
├── python/
│   ├── waccy/                   # Python API package
│   ├── waccy-edgar/             # Python EDGAR adapter, if retained
│   └── waccy-quickbooks/        # Python QBO adapter, if retained
├── packages/
│   └── waccy/                   # Node/TypeScript API package
├── schemas/
│   ├── financial-dataset.json   # Shared schema contract
│   ├── model-output.json
│   └── diagnostics.json
├── docs/
├── tests/
│   ├── fixtures/
│   ├── conformance/
│   ├── python/
│   ├── node/
│   └── rust/
└── examples/
```

This is a target shape, not an immediate requirement to move every file. The
first migration should avoid churn until Rust and Node boundaries are clear.

## Rust Backend

Rust should become the canonical engine for financial correctness and
performance-sensitive computation.

### Crate Responsibilities

`waccy-core` should own:

- shared data model types
- ontology structures
- period and date logic
- deterministic mapping support
- validation and reconciliation
- model assembly
- serialization and diagnostics

`waccy-ffi` may own:

- Python binding functions
- Node native binding functions
- WebAssembly bindings if browser or edge use becomes important

`waccy-service` may own:

- HTTP/JSON API
- async job execution
- artifact storage hooks
- service diagnostics

These crates should be separated only when the boundary has a reason. The first
Rust milestone can start with a single `waccy-core` crate.

### Rust Data Boundary

Rust should accept and emit versioned structures:

- `NormalizedFinancialDataset`
- `MappedFinancialDataset`
- `ValidatedFinancialDataset`
- `ThreeStatementModel`
- `ValidationIssue`
- `ModelDiagnostic`

Serialization should be stable enough for Python and Node wrappers to rely on.
JSON Schema is the most practical contract format for cross-language alignment;
Arrow or binary formats can be added for large datasets later.

## Python API

The Python API should remain comfortable for analysts and data engineers.

Responsibilities:

- package ergonomics and public imports
- pandas DataFrame export
- XLSX export
- notebook-friendly workflows
- compatibility adapters for the existing `waccy` API
- optional Python source clients where Python ecosystems are strongest

As Rust parity grows, Python should delegate deterministic logic to Rust via
bindings or service calls. Python should not maintain a separate model engine
once Rust reaches parity.

## Node API

The Node API should expose WACCY to TypeScript and web product teams.

Responsibilities:

- npm package distribution
- TypeScript types generated from shared schemas
- JSON-first validation and model-building APIs
- async-friendly calls for larger jobs
- server-side integration with web apps and agent tools
- optional client helpers for hosted WACCY services

The Node package can be implemented through native bindings, WebAssembly, or a
thin service client. The decision should be driven by deployment needs:

- **Native binding**: best for server-side speed and direct embedding.
- **WebAssembly**: best for portability and edge/browser possibilities.
- **HTTP client**: best for hosted service and job orchestration.

## Hosted Service Option

A hosted service is not required for every deployment, but the architecture
should allow it.

Service responsibilities:

- receive normalized datasets or source payloads
- run validation and model jobs
- store artifacts and diagnostics
- return model outputs and export links
- support long-running jobs for large filings or portfolios

The hosted API should use the same schemas as the local Python and Node APIs.

## Source Adapter Strategy

Source adapters should stay outside the Rust core unless there is a clear reason
to move them.

### QBO / QuickBooks

QBO remains a first-party adapter. The current Python `waccy-quickbooks` package
can continue to own OAuth, report pulling, token cache behavior, and raw report
normalization. Its long-term responsibility is to emit the shared normalized
dataset.

### SEC EDGAR

EDGAR remains a first-party adapter and public-company corpus. The current
Python `waccy-edgar` package can continue to own company-facts normalization and
filing-specific extraction until Rust or a service boundary has a strong reason
to absorb pieces of it.

### Future Sources

Future adapters can be written in Python, Node, Rust, or another language if
they emit the shared contract. The core should not depend on source-specific
payload structures.

## Ontology Architecture

The ontology should be stored and versioned as shared data, then loaded by Rust
and surfaced through Python and Node.

Requirements:

- canonical account IDs and names
- account type and hierarchy
- statement placement
- normal balance and sign convention
- cash-flow section and treatment
- source aliases
- industry extensions
- ontology version

The ontology should be testable independently from source adapters and model
builders.

## Model Builder Architecture

Model builders should be organized around validated data, not source systems.

Initial builder:

- three-statement model

Future builders:

- DCF
- comparables
- M&A/pro forma
- LBO
- credit/covenant
- SaaS metrics
- FP&A forecast

Each builder should define:

- input accounts or metrics required by the builder
- optional input accounts
- output lines
- subtotal and check logic
- diagnostics
- export representation

## Testing Architecture

Cross-language conformance is the key testing requirement.

Test layers:

- Rust unit tests for deterministic financial logic
- Python API tests for compatibility and pandas/XLSX workflows
- Node API tests for TypeScript contracts and JSON workflows
- shared fixture conformance tests across Python, Node, and Rust
- outcome tests for QBO and EDGAR release fixtures
- package build and smoke tests for every published artifact

Conformance fixtures should describe expected normalized, mapped, validated, and
model-output results. Each language surface should prove it can produce or
consume those fixtures.

## Packaging And Release Architecture

Current published packages:

- PyPI: `waccy`
- PyPI: `waccy-edgar`
- PyPI: `waccy-quickbooks`

Future packages:

- crates.io: `waccy-core` or equivalent Rust crates
- npm: `@waccy/waccy` or equivalent TypeScript package

Release requirements:

- package artifacts build from source without local workspace leakage
- PyPI publishing uses trusted publishers
- npm publishing should use provenance and trusted CI publishing where possible
- Rust crates should use reproducible cargo builds
- schema versions should be included in release notes
- GitHub releases should summarize all language package versions

## Migration Path

This migration path follows the canonical roadmap in
[2-REQUIREMENTS.md](2-REQUIREMENTS.md#roadmap-requirements). Architecture work
should use these phase names so planning does not split into competing
sequences.

### Phase One: Multi-Language Contract Foundation

- define shared schemas for datasets, diagnostics, and model outputs
- align current Python models to the schema
- add conformance fixtures
- document compatibility expectations
- decide which current Python APIs are compatibility commitments

### Phase Two: Rust Core Parity

- create `waccy-core`
- port ontology and period/date primitives
- port validation primitives
- expose JSON serialization
- prove parity on small fixtures
- evaluate Python native binding vs service call
- evaluate Node native binding vs WebAssembly vs service client
- choose based on deployment and maintenance costs
- port three-statement builder
- port diagnostics and reconciliation
- compare outputs against Python v0.1.0 fixtures
- keep Python API stable

### Phase Three: Service And Node API

- publish TypeScript package
- support validation and model-building calls
- include generated types and examples
- add Node conformance tests
- define hosted service boundaries if local bindings are not enough

### Phase Four: Advanced Models

- add DCF and advanced model families on top of the validated dataset contract
- keep Python and Node API parity where appropriate

### Phase Five: Decision Support

- add scenario management and sensitivity analysis
- add model comparison workflows
- add document and source synthesis workflows
- expose confidence-aware review APIs for product UIs

## Open Architecture Decisions

- Should Python and Node call Rust through native bindings, WebAssembly, or a
  hosted service first?
- Should source adapters remain in Python packages or move toward language-
  specific SDKs?
- Should schemas be generated from Rust types or maintained as independent JSON
  Schema files?
- What package names should be reserved for npm and crates.io?
- How much of XLSX export should stay in Python versus move to Rust or Node?
