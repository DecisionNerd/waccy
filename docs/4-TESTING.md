# WACCY Testing And Quality

WACCY's testing strategy should protect the financial correctness of the platform, not only the mechanics of individual functions. The quality loop is designed around issue-sized changes, local pre-push checks, GitHub CI, Codecov coverage gates, CodeRabbit review, and outcome-oriented BDD specs.

## Quality Standard

Every meaningful change should answer three questions before it merges:

- Does the code satisfy the user-visible outcome described by the issue?
- Do the financial calculations, mappings, validations, and exports remain correct?
- Can a reviewer trust the checks without manually reconstructing the whole model path?

For WACCY, "correct" means more than green unit tests. A change should preserve source provenance, mapping status, validation diagnostics, reconciliation checks, and workbook outputs.

## Local Pre-Push Workflow

The default development loop is:

1. Work one GitHub issue at a time.
2. Add or update outcome expectations when product behavior changes.
3. Run local checks before pushing.
4. Push the branch.
5. Open a ready-for-review PR, not a draft PR.
6. Let GitHub CI, Codecov, and CodeRabbit verify the same branch.

Run:

```bash
make pre-push
```

`make pre-push` is intentionally aligned with CI. It runs:

```bash
uv run ruff check
uv run mypy src/waccy
uv run pytest tests/bdd -q -m "bdd or outcome"
uv run pytest --cov=src/waccy --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

The Makefile also exposes smaller targets for faster iteration:

```bash
make lint
make typecheck
make bdd
make test
make test-cov
```

## Coverage Target

The project coverage target is 90%.

This target is enforced in two places:

- local and CI pytest coverage with `--cov-fail-under=90`
- Codecov project and patch gates set to `90%`

Coverage should be meaningful. Tests should exercise behavior, edge cases, validation branches, source-specific mapping, and exported artifacts. Avoid adding superficial tests that only execute lines without protecting a user or financial outcome.

Low-coverage scaffolding should either gain useful tests or remain clearly marked as placeholder behavior. As the codebase matures, placeholder modules should be replaced by real behavior and real tests rather than excluded from coverage by default.

## Test Layers

WACCY uses layered tests that mirror the architecture:

- **Unit tests** cover deterministic behavior in models, ontology, mapping, validation, utilities, and exporters.
- **Fixture-driven tests** cover QBO and EDGAR source-shaped inputs without live API dependencies.
- **Integration-style pipeline tests** cover the path from extracted records to normalized datasets, mapped records, validated datasets, three-statement models, and XLSX workbooks.
- **BDD outcome specs** cover user-visible expectations in business language.
- **CI checks** verify the complete branch before merge.

The core v0.1.0 outcome path is:

```text
source extractor
  -> raw extracted data
  -> normalized financial dataset
  -> mapped financial dataset
  -> validated financial dataset
  -> model builders
  -> XLSX exporter
```

Tests should preserve that contract.

## BDD Outcome Specs

BDD specs live under:

```text
tests/bdd/features/
tests/bdd/test_*_outcomes.py
```

Feature files should describe outcomes in user-facing terms. They should focus on what must be true, not how the code happens to implement it.

Good BDD scenarios answer questions like:

- Can a balanced QBO fixture produce exactly the expected three statements?
- Can EDGAR/XBRL concepts map into the same canonical model as QBO?
- Does the model surface unmapped accounts, ambiguous mappings, balance-sheet failures, or cash-flow tie-out failures?
- Does a workbook export contain the expected sheets, periods, line items, and check rows?

BDD specs should not replace unit tests. They define the acceptance contract. Unit and integration tests then protect the implementation details behind that contract.

## GitHub CI

GitHub Actions runs two jobs:

- **Quality Gates**: ruff, mypy, full pytest coverage, Codecov upload.
- **BDD Outcome Specs**: focused behavior checks so outcome regressions are visible in the PR.

CI should remain fast enough to support issue-by-issue work. If a future test category becomes slow, split it into an explicit job rather than hiding it inside a broad command.

## Codecov

Codecov checks both project coverage and patch coverage. The target is 90%, with small thresholds to avoid noise from harmless rounding or incidental line shifts.

Codecov is a guardrail, not the sole quality signal. A PR can have high coverage and still be wrong if it lacks outcome coverage, bad financial assumptions, or weak validation checks.

## CodeRabbit

CodeRabbit is configured through `.coderabbit.yaml` and should review ready PRs. It is expected to provide an additional code-review pass, especially on:

- financial calculation mistakes
- unclear abstractions
- missing tests
- API contract breaks
- documentation drift
- CI or workflow mistakes

CodeRabbit comments should be triaged like normal review feedback. Fix actionable issues, explain intentional tradeoffs, and keep the PR moving through the same checks.

## Issue-To-PR Discipline

The preferred workflow is one issue, one focused branch, one ready PR.

Each issue should include:

- the intended user-visible outcome
- feature expectations that can become BDD scenarios when behavior changes
- implementation notes for likely modules or APIs
- done criteria for BDD coverage, unit/integration coverage, and passing CI

Each PR should include:

- the linked issue
- the outcome delivered
- tests added or updated
- local `make pre-push` result
- any known gaps or follow-up issues

Draft PRs are not the default workflow because they interrupt the expected review and CI process. If a branch needs exploratory feedback, say so explicitly; otherwise PRs should be opened ready for review after `make pre-push` passes.
