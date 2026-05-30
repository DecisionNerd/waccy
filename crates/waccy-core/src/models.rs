use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const CONTRACT_SCHEMA_VERSION: &str = "1.0.0";

// ── Enums ─────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AccountType {
    Asset,
    Liability,
    Equity,
    Revenue,
    Expense,
    CashFlow,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PeriodType {
    Month,
    Quarter,
    Year,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MappingStatus {
    Mapped,
    Ambiguous,
    Overridden,
    Unmapped,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IssueSeverity {
    Info,
    Warning,
    Error,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StatementKind {
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
}

// ── Standard account ontology ─────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandardAccount {
    pub id: String,
    pub name: String,
    pub account_type: AccountType,
    pub statement: StatementKind,
    pub normal_balance: NormalBalance,
    pub cash_flow_section: Option<CashFlowSection>,
    pub sort_order: u32,
    pub aliases: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum NormalBalance {
    Debit,
    Credit,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CashFlowSection {
    Operating,
    Investing,
    Financing,
}

// ── Reporting periods ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportingPeriod {
    pub label: String,
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    pub period_type: PeriodType,
}

// ── Source identity ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceReference {
    pub source_system: String,
    pub source_id: String,
    pub source_label: String,
    pub metadata: HashMap<String, serde_json::Value>,
}

// ── Source records ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceRecord {
    pub source_account_id: String,
    pub source_account_name: String,
    pub amount: f64,
    pub period_label: String,
    pub source: SourceReference,
    pub unit: String,
    pub statement: Option<String>,
    pub source_account_type: Option<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NormalizedFinancialDataset {
    pub schema_version: String,
    pub entity_name: String,
    pub periods: Vec<ReportingPeriod>,
    pub records: Vec<SourceRecord>,
    pub metadata: HashMap<String, serde_json::Value>,
}

// ── Mapping ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MappingDiagnostic {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MappingOverride {
    pub account_id: String,
    pub note: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MappedFinancialRecord {
    pub source_record: SourceRecord,
    pub account_id: Option<String>,
    pub account_name: Option<String>,
    pub status: MappingStatus,
    pub confidence: f32,
    pub diagnostics: Vec<MappingDiagnostic>,
    pub override_note: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MappedFinancialDataset {
    pub schema_version: String,
    pub entity_name: String,
    pub periods: Vec<ReportingPeriod>,
    pub records: Vec<MappedFinancialRecord>,
    pub metadata: HashMap<String, serde_json::Value>,
}

// ── Validation ────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationIssue {
    pub code: String,
    pub message: String,
    pub severity: IssueSeverity,
    pub period_label: Option<String>,
    pub account_id: Option<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidatedFinancialDataset {
    pub schema_version: String,
    pub mapped_dataset: MappedFinancialDataset,
    pub issues: Vec<ValidationIssue>,
}

impl ValidatedFinancialDataset {
    pub fn is_valid(&self) -> bool {
        !self.issues.iter().any(|i| i.severity == IssueSeverity::Error)
    }
}

// ── Extractor input ───────────────────────────────────────────────────────────

/// Raw data from an extractor — source records are the primary path; the
/// `transactions` vec is a legacy fallback retained for compatibility.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExtractedData {
    pub entity_name: String,
    pub periods: Vec<ReportingPeriod>,
    pub source_records: Vec<SourceRecord>,
    pub metadata: HashMap<String, serde_json::Value>,
}

// ── Financial statements ──────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatementLine {
    pub label: String,
    pub account_id: Option<String>,
    /// Amount keyed by period label.
    pub values: HashMap<String, f64>,
    pub is_subtotal: bool,
    pub is_check: bool,
    pub source_account_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialStatement {
    pub name: String,
    pub periods: Vec<ReportingPeriod>,
    pub lines: Vec<StatementLine>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreeStatementModel {
    pub schema_version: String,
    pub entity_name: String,
    pub periods: Vec<ReportingPeriod>,
    pub income_statement: FinancialStatement,
    pub balance_sheet: FinancialStatement,
    pub cash_flow_statement: FinancialStatement,
    pub validation_issues: Vec<ValidationIssue>,
    pub metadata: HashMap<String, serde_json::Value>,
}
