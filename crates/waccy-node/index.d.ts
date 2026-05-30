/**
 * Execute arbitrary SQL against the financial dataset.
 * Returns an array of row objects.
 *
 * @example
 * ```ts
 * import { query } from '@waccy/core'
 *
 * const rows = await query(
 *   "SELECT period_label, SUM(amount) AS revenue FROM records WHERE account_id = 'revenue' GROUP BY 1"
 * )
 * ```
 */
export declare function query(sql: string, dataDir?: string | null): Promise<Record<string, string>[]>

/**
 * Income statement for the modelled periods.
 * @param period - Optional period label, e.g. "2024" or "2024-Q1"
 */
export declare function incomeStatement(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>

/** Balance sheet for the modelled periods. */
export declare function balanceSheet(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>

/** Cash flow statement for the modelled periods. */
export declare function cashFlow(period?: string | null, dataDir?: string | null): Promise<StatementRow[]>

/**
 * Build a three-statement model from JSON-serialised ExtractedData.
 * Use this when you've extracted data via the CLI and want to process it
 * in a Next.js API route or Server Action.
 */
export declare function buildModel(extractedJson: string): ThreeStatementModel

// ── Result types ──────────────────────────────────────────────────────────────

export interface StatementRow {
  account_id: string
  account_name: string
  account_type: string
  statement_kind: string
  period_label: string
  amount: string
}

export interface ThreeStatementModel {
  income_statement: FinancialStatement
  balance_sheet: FinancialStatement
  cash_flow_statement: FinancialStatement
  reconciliation_checks: ReconciliationCheck[]
}

export interface FinancialStatement {
  kind: 'income_statement' | 'balance_sheet' | 'cash_flow_statement'
  periods: ReportingPeriod[]
  lines: StatementLine[]
}

export interface StatementLine {
  account: StandardAccount
  values: Record<string, number>
  is_subtotal: boolean
}

export interface StandardAccount {
  id: string
  display_name: string
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'cash_flow'
  statement: 'income_statement' | 'balance_sheet' | 'cash_flow_statement'
}

export interface ReportingPeriod {
  label: string
  start: string
  end: string
  period_type: 'annual' | 'quarterly' | 'monthly' | 'ttm' | 'custom'
}

export interface ReconciliationCheck {
  name: string
  passed: boolean
  delta: number
}
