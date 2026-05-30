# ADR-001: Polars over DataFusion for storage and query

**Status:** Accepted  
**Date:** 2026-05-30

## Context

The initial Rust scaffold copied DataFusion from `imessage-analysis` as the query layer. That project's use case — arbitrary SQL aggregations over a large, append-only, flat message log — is a natural fit for a SQL engine. WACCY's use case is different.

WACCY works with a small, structured, typed dataset: approximately 21 canonical accounts × N reporting periods. The "query" patterns at every surface are:

- filter by `statement_kind`
- filter by `period_label`
- pivot values by period for display or export
- groupby account type for subtotals

These are DataFrame operations, not SQL engine problems.

Two additional concerns:

1. **Cross-language story.** DataFusion has no official Python or Node bindings that data practitioners actually use. Returning JSON strings from Python and Node was the only workable path, which added friction and destroyed type information.

2. **Binary size and compile time.** DataFusion pulls in a significant dependency tree. For a CLI and native addon that should install quickly and start fast, that cost is unjustifiable when simpler tools suffice.

## Decision

Replace DataFusion with Polars as the query and analysis layer, keeping Arrow + Parquet for storage.

**Storage:** Arrow + Parquet via the `arrow` and `parquet` crates (already in the dependency tree). Unchanged.

**Query:** Polars `LazyFrame` over stored Parquet files. Polars handles filter, select, pivot, groupby, and SQL-style expressions natively. A thin SQL escape hatch is available via `polars.sql()` for power users.

**Cross-language return types:**
- Python: `polars.DataFrame` or `pyarrow.Table` (zero-copy via Arrow FFI — no JSON round-trip)
- Node: `DataFrame` via `nodejs-polars` (the official maintained binding), or plain object arrays for simpler cases

**Async boundary:** Polars is synchronous CPU-bound work. All Polars calls in async contexts (MCP server, Node napi event loop, Python with async callers) are wrapped in `tokio::task::spawn_blocking`. This is the standard Rust pattern for sync/CPU-bound work in an async runtime — it does not sacrifice async throughput.

```rust
// Canonical pattern
let result = tokio::task::spawn_blocking(move || {
    polars_query(data_dir, filter_expr)
}).await??;
```

DataFusion is removed from all `Cargo.toml` files.

## Consequences

**Positive:**
- Python consumers get a real `polars.DataFrame` or `pyarrow.Table` — no `json.loads()` call needed
- Node consumers get a real `DataFrame` via `nodejs-polars`
- Polars is the DataFrame library data practitioners actually use in 2025–2026; it extends the platform naturally into notebooks and data pipelines
- Smaller binary, faster compile
- `spawn_blocking` is idiomatic, well-understood, and has no hidden cost for our workload sizes

**Negative:**
- Polars is a heavier dependency than raw Arrow; acceptable given the cross-language payoff
- The SQL escape hatch (`polars.sql()`) is less capable than DataFusion's full SQL engine; acceptable because WACCY's dataset is small and well-typed

**Neutral:**
- The async boundary is preserved — callers see `async fn` throughout. Only the internals change.
- Storage format (Arrow + Parquet) is unchanged; existing Parquet files remain readable.

## Alternatives Considered

**Keep DataFusion.** Rejected. The cross-language story was broken (JSON strings), the binary weight was unjustified, and DataFusion's strength (large-dataset SQL) does not match WACCY's workload.

**Raw Arrow without a DataFrame library.** Rejected. Manual filter/pivot over Arrow arrays would duplicate what Polars already does well and lose the cross-language return-type benefit.

**DuckDB.** Strong SQL story, good Python bindings. Rejected because the Rust DuckDB crate is less mature than Polars, and DuckDB's primary value (in-process SQL over large files) is again not WACCY's workload.
