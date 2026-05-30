# Journeys

This directory holds personas, user journeys, and the narrative origins of BDD scenarios. The core docs stay pithy; this is where the detail lives.

Each journey file describes what a specific type of user needs, what they do step by step, what can go wrong, and what a good outcome looks like. These feed directly into BDD feature files in `tests/` — a journey step that matters becomes a `Scenario` that matters.

## Contents

| File | Persona |
|---|---|
| [advisor.md](advisor.md) | Financial advisor cleaning up small-business records for a transaction or valuation |
| [developer.md](developer.md) | Developer embedding WACCY into a Python or Node workflow |
| [operator.md](operator.md) | Business owner or CFO using WACCY directly for financial visibility |
| [agent.md](agent.md) | AI agent using WACCY via MCP to answer financial questions |

---

## How Journeys Connect to BDD

A journey describes the goal, the steps, and the expected outcome in human terms. When a step matters enough to protect — because it's financial-correctness-critical or user-visible — it becomes a Gherkin scenario:

```
Journey step:
  "The advisor reviews which accounts couldn't be mapped automatically
   so they can decide whether to override or accept the gap."

BDD scenario:
  Given a QBO fixture with one unmapped account
  When the model is built
  Then the validation issues include an unmapped_account error
  And the issue identifies the source account name
  And the issue has period_label set
```

Journeys are the source of truth for what scenarios should exist. If a scenario can't be traced to a journey step that matters to a real user, it probably shouldn't be a BDD scenario.

## Persona Summary

### Financial Advisor / Accountant

Starts from a client's QBO export or EDGAR filing. Needs to know: which accounts mapped cleanly, which are ambiguous, whether the balance sheet balances, and what the model says about revenue, margins, and cash flow. Exports to XLSX for review and client delivery. Values auditability over automation.

### Developer

Embedding WACCY into a data pipeline or product. Needs a clean API, predictable JSON contracts, and errors that explain what went wrong. May call from Python (notebook, backend worker) or Node (Next.js API route, server action). Values composability and type safety.

### Operator / Owner

Using WACCY or a product built on WACCY to understand their own business. Needs clear answers to: "are we profitable?", "where is cash going?", "how do we compare to last year?". Less interested in data provenance, more interested in actionable insight. Values simplicity and directness.

### AI Agent

Calling WACCY via MCP in response to a user question. Needs structured tool responses it can interpret and relay. Needs to know when data is missing or a model couldn't be built, and why. Values machine-readable diagnostics, not prose.
