# Product

This directory holds market context, positioning, competitive landscape, and ecosystem fit — the "why this exists and where it sits" layer. It informs prioritization and helps new contributors understand what WACCY is competing with, complementing, and building toward.

## Contents

| File | Topic |
|---|---|
| [positioning.md](positioning.md) | Market positioning and competitive landscape |
| [ecosystem.md](ecosystem.md) | How WACCY fits into the financial data and tooling ecosystem |

---

## Market Context

Small-business financial modeling sits in an underserved gap. Enterprise finance has Bloomberg, Refinitiv, and dedicated FP&A platforms. Consumer finance has Mint and Personal Capital. But the small-business middle — the companies that need rigorous analysis but lack the infrastructure to support it — has mostly spreadsheets and one-off engagements.

The closest adjacent tools:

**Accounting systems** (QuickBooks, Xero, Sage) — excellent at transaction recording, weak at modeling. They produce reports but not models, and their account classification is source-specific rather than standardized.

**Financial modeling tools** (Mosaic, Jirav, Causal) — cloud FP&A platforms aimed at Series A+ startups with clean data and finance teams. Assume well-structured inputs. Not designed for extraction from messy source data.

**Data extraction tools** (Apify, Plaid, Codat) — API aggregators that normalize data schemas but stop at extraction. They don't classify accounts, build models, or produce auditable outputs.

**Analyst workflows** — advisors and accountants still build models in Excel by hand, normalizing accounts themselves. Slow, error-prone, not reproducible.

WACCY's position: a deterministic financial modeling engine that starts from messy source data, normalizes it to a standard ontology, and produces auditable three-statement models and downstream analysis — embeddable from Python, Node, or Rust, and callable from AI agents via MCP.

## Ecosystem Fit

WACCY is designed to sit at the center of a financial data workflow, not to be the whole thing:

```
Accounting system (QBO, Xero, EDGAR)
        │
        ▼
  WACCY extraction + normalization + modeling
        │
   ┌────┴──────────────────────┐
   ▼                           ▼
Python notebook            Next.js app
(analyst workflow)         (SaaS product)
        │                      │
      XLSX                  JSON API
   (human review)          (AI agent)
```

It is explicitly not:
- a bookkeeping or accounting system
- a payments or banking integration
- a BI/dashboarding tool
- a general-purpose data pipeline

It is a focused financial modeling core that other tools and workflows plug into.

## Distribution Strategy

WACCY reaches different audiences through different surfaces:

- **CLI + Homebrew** — analysts and developers who prefer the terminal
- **MCP server** — AI agent workflows in Claude, Cursor, and similar tools
- **PyPI wheel** — data scientists and finance engineers in Python ecosystems
- **npm package** — product teams building SaaS applications on Node/Next.js
- **Agent skills** — one-command setup for Claude Code and compatible agents

The goal is broad embeddability without requiring users to adopt a new primary tool.
