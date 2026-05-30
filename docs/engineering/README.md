# Engineering

This directory holds deep-dive technical documentation: architecture decision records, implementation guides, data model specifications, and anything that would make the core docs too long.

The five core docs (`0-mission` through `4-testing`) stay pithy and navigable. When a topic needs more depth — a decision with tradeoffs, a data format spec, a module design — it lives here and is linked from the core doc that references it.

## Contents

### Architecture Decision Records

ADRs record significant technical decisions: what was decided, why, what was rejected, and what consequences are expected. They are append-only — superseded decisions get a new ADR, not an edit.

| ADR | Decision |
|---|---|
| [ADR-001](adr/001-polars-over-datafusion.md) | Use Polars + Arrow over DataFusion for storage and query |

### Deep-Dive Docs

_(Add files here as topics outgrow the core docs.)_

---

## ADR Format

Each ADR uses this structure:

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Superseded by ADR-NNN
**Date:** YYYY-MM-DD

## Context
What problem or situation prompted this decision.

## Decision
What was decided, in plain terms.

## Consequences
What gets better, what gets worse, what is neutral.

## Alternatives Considered
What else was evaluated and why it was rejected.
```

New ADRs get the next sequential number. Link them from the relevant core doc when they relate to something a reader would expect to find there.
