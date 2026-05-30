// ── Row types ─────────────────────────────────────────────────────────────────

/**
 * One row in a financial statement — one (line, period) pair.
 *
 * Schema mirrors `waccy-core::query::statement_to_dataframe`:
 * label | account_id | period_label | amount | is_subtotal | is_check | source_account_ids
 */
export interface StatementRow {
  /** Human-readable line label, e.g. "Revenue", "Net Income", "Balance Check" */
  label: string
  /** Canonical account ID, e.g. "revenue", "cash". Null for computed subtotals. */
  account_id: string | null
  /** Reporting period label, e.g. "2024", "2024Q1", "FY2023" */
  period_label: string
  /** Monetary value for this (line, period) cell */
  amount: number
  /** True for computed subtotals (Gross Profit, Total Assets, etc.) */
  is_subtotal: boolean
  /** True for reconciliation checks (Balance Check, Cash Flow Tie-Out) */
  is_check: boolean
  /** Comma-separated source account IDs that roll into this line */
  source_account_ids: string
}

/**
 * Three-statement model returned by `buildModel` — one `StatementRow[]` per statement.
 *
 * Each array is in tidy long format: one row per (line, period) combination.
 * This is the natural shape for charting, pivoting, or loading into nodejs-polars:
 *
 * ```ts
 * import pl from 'nodejs-polars'
 * const { income_statement } = buildModel(dataJson)
 * const df = pl.from_records(income_statement)
 * ```
 */
export interface ModelStatements {
  income_statement: StatementRow[]
  balance_sheet: StatementRow[]
  cash_flow_statement: StatementRow[]
}

// ── Extraction ────────────────────────────────────────────────────────────────

/**
 * Normalise an SEC EDGAR companyfacts JSON payload into WACCY ExtractedData.
 * Pass the result directly to `buildModel`.
 */
export declare function extractEdgar(companyfactsJson: string, periods?: number | null, taxonomy?: string | null): Promise<string>

/**
 * Normalise a raw QuickBooks Online report payload into WACCY ExtractedData.
 * Pass the result directly to `buildModel`.
 */
export declare function extractQbo(payloadJson: string): Promise<string>

// ── Modelling ─────────────────────────────────────────────────────────────────

/**
 * Build a three-statement financial model from JSON-encoded ExtractedData.
 *
 * Returns `{ income_statement, balance_sheet, cash_flow_statement }` where each
 * value is a `StatementRow[]` — one row per (line, period) pair.
 *
 * For the full model object including validation issues use `buildModelJson`.
 */
export declare function buildModel(extractedJson: string): ModelStatements

/**
 * Build a three-statement model and return the full `ThreeStatementModel` as a
 * JSON string, including `validation_issues`, `entity_name`, and metadata.
 *
 * Parse with `JSON.parse()`. Use `buildModel` for row-oriented access.
 */
export declare function buildModelJson(extractedJson: string): string

// ── Query ─────────────────────────────────────────────────────────────────────

/**
 * Execute arbitrary SQL against the financial dataset.
 * The primary table is `records`.
 *
 * @example
 * ```ts
 * const rows = await query(
 *   "SELECT period_label, SUM(amount) AS revenue FROM records WHERE account_id = 'revenue' GROUP BY 1"
 * )
 * ```
 */
export declare function query(sql: string, dataDir?: string | null): Promise<Record<string, unknown>[]>

/**
 * Income statement rows for the modelled periods.
 * Returns `StatementRow[]` — one row per (line, period) pair.
 */
export declare function incomeStatement(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>

/**
 * Balance sheet rows for the modelled periods.
 * Returns `StatementRow[]` — one row per (line, period) pair.
 */
export declare function balanceSheet(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>

/**
 * Cash flow statement rows for the modelled periods.
 * Returns `StatementRow[]` — one row per (line, period) pair.
 */
export declare function cashFlow(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>
