# WACCY Experience

This document describes the target user experience for WACCY. The current package is still an early scaffold; the first useful workflow is tracked in the [v0.1.0 milestone](https://github.com/DecisionNerd/waccy/milestone/1).

## Primary Users

WACCY should serve people who need professional financial analysis but start from imperfect records:

- advisors and accountants cleaning up small-business financials
- investors, lenders, and buyers evaluating small companies
- operators and founders trying to understand performance and cash flow
- developers building automated finance workflows

The product should assume the user is capable and busy. It should avoid magic, expose uncertainty, and make review efficient.

## v0.1.0 Target Workflow

The first usable release should make one narrow path feel solid:

1. Install WACCY with the QBO and EDGAR extensions.
2. Load QBO/QuickBooks or EDGAR fixture data.
3. Normalize source accounts into the WACCY chart of accounts.
4. Build a three-statement model.
5. Export an `.xlsx` workbook with:
   - Income Statement
   - Balance Sheet
   - Cash Flow Statement
6. Review validation and reconciliation checks.

## Target End-To-End Experience

In the long run, WACCY should guide users through a repeatable workflow:

1. **Connect or load sources**: accounting data, public filings, documents, or other business systems.
2. **Inspect extracted data**: source accounts, periods, amounts, and provenance.
3. **Review mappings**: see how source accounts map to WACCY standard accounts.
4. **Resolve ambiguity**: accept, override, or flag uncertain classifications.
5. **Build models**: generate financial statements and model outputs from normalized data.
6. **Validate outputs**: review balance checks, cash-flow tie-outs, missing data, and confidence scores.
7. **Export and iterate**: produce workbook outputs that remain auditable and editable.

The experience should make the quality of the data visible before the user relies on the model.

## User Expectations

The v0.1.0 experience should be explicit about data quality. If source accounts cannot be mapped, periods are missing, or the balance sheet does not balance, WACCY should return actionable diagnostics rather than quietly producing a bad model.

Users should be able to answer:

- Which source records produced this line item?
- Which accounts were mapped automatically?
- Which accounts were ambiguous or unmapped?
- Which periods are incomplete?
- Does the balance sheet balance?
- Does cash flow tie to the change in cash?
- What assumptions or defaults did WACCY use?

## Data Quality Experience

WACCY should treat messy records as normal, not exceptional. When input data is incomplete or ambiguous, the user experience should:

- identify the issue clearly
- show the source data involved
- explain the likely impact on the model
- provide an override or review path where appropriate
- preserve the audit trail after correction

Confidence scoring should help prioritize review. It should not imply false precision.

## Non-Goals For v0.1.0

The following are important to the broader mission but should not block the first vertical slice:

- A full live QuickBooks product workflow beyond the typed OAuth/report-pull helper
- Full EDGAR pattern-learning system
- DCF, LBO, M&A, SaaS cohort, or other advanced model types
- Google Sheets API export
- LLM-dependent classification as a required path
