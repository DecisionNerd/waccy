use std::collections::{HashMap, HashSet};

use crate::{
    error::WaccyError,
    extraction::normalize_map_validate,
    models::{
        ExtractedData, FinancialStatement, IssueSeverity, MappedFinancialDataset,
        MappedFinancialRecord, MappingOverride, StatementLine, ThreeStatementModel,
        ValidatedFinancialDataset, ValidationIssue, CONTRACT_SCHEMA_VERSION,
    },
    validation::validate_mapped_dataset,
};

pub struct ModelBuilder;

impl ModelBuilder {
    /// Build a three-statement model from any pipeline stage.
    pub fn build(
        &self,
        input: ModelInput,
        overrides: &HashMap<String, MappingOverride>,
    ) -> Result<ThreeStatementModel, WaccyError> {
        let validated = match input {
            ModelInput::Extracted(data) => normalize_map_validate(&data, overrides)?,
            ModelInput::Mapped(dataset) => validate_mapped_dataset(dataset),
            ModelInput::Validated(v) => v,
        };

        let dataset = &validated.mapped_dataset;
        let periods = dataset.periods.clone();
        let period_labels: Vec<String> = periods.iter().map(|p| p.label.clone()).collect();
        let records = &dataset.records;

        let mut issues = validated.issues.clone();
        issues.extend(source_completeness_issues(&dataset.metadata));

        let income_lines = build_income_lines(records, &period_labels);
        let balance_lines = build_balance_lines(records, &period_labels);
        let cf_lines = build_cf_lines(records, &income_lines, &balance_lines, &period_labels);

        issues.extend(statement_issues(&balance_lines, &cf_lines, &period_labels, &dataset.metadata));

        Ok(ThreeStatementModel {
            schema_version: CONTRACT_SCHEMA_VERSION.to_string(),
            entity_name: dataset.entity_name.clone(),
            periods: periods.clone(),
            income_statement: FinancialStatement {
                name: "Income Statement".to_string(),
                periods: periods.clone(),
                lines: income_lines,
            },
            balance_sheet: FinancialStatement {
                name: "Balance Sheet".to_string(),
                periods: periods.clone(),
                lines: balance_lines,
            },
            cash_flow_statement: FinancialStatement {
                name: "Cash Flow Statement".to_string(),
                periods: periods.clone(),
                lines: cf_lines,
            },
            validation_issues: issues,
            metadata: dataset.metadata.clone(),
        })
    }
}

pub enum ModelInput {
    Extracted(ExtractedData),
    Mapped(MappedFinancialDataset),
    Validated(ValidatedFinancialDataset),
}

// ── Line builders ─────────────────────────────────────────────────────────────

fn build_income_lines(
    records: &[MappedFinancialRecord],
    periods: &[String],
) -> Vec<StatementLine> {
    let revenue = source_line("Revenue", "revenue", records, periods);
    let cogs = source_line("Cost of Goods Sold", "cogs", records, periods);
    let opex = source_line("Operating Expenses", "operating_expenses", records, periods);
    let da = source_line("Depreciation & Amortization", "depreciation_amortization", records, periods);
    let interest = source_line("Interest Expense", "interest_expense", records, periods);
    let taxes = source_line("Tax Expense", "tax_expense", records, periods);

    let gross_profit = computed("Gross Profit", periods, |p| {
        get(&revenue, p) - get(&cogs, p)
    });
    let operating_income = computed("Operating Income", periods, |p| {
        get(&gross_profit, p) - get(&opex, p) - get(&da, p)
    });
    let pretax = computed("Pre-Tax Income", periods, |p| {
        get(&operating_income, p) - get(&interest, p)
    });
    let net_income = computed("Net Income", periods, |p| get(&pretax, p) - get(&taxes, p));

    vec![revenue, cogs, gross_profit, opex, da, operating_income, interest, pretax, taxes, net_income]
}

fn build_balance_lines(
    records: &[MappedFinancialRecord],
    periods: &[String],
) -> Vec<StatementLine> {
    let cash = source_line("Cash", "cash", records, periods);
    let ar = source_line("Accounts Receivable", "accounts_receivable", records, periods);
    let inv = source_line("Inventory", "inventory", records, periods);
    let ppe = source_line("Property, Plant & Equipment", "ppe", records, periods);
    let acc_dep = source_line("Accumulated Depreciation", "accumulated_depreciation", records, periods);
    let ap = source_line("Accounts Payable", "accounts_payable", records, periods);
    let accrued = source_line("Accrued Expenses", "accrued_expenses", records, periods);
    let debt = source_line("Debt", "debt", records, periods);
    let equity = source_line("Equity", "equity", records, periods);
    let retained = source_line("Retained Earnings", "retained_earnings", records, periods);

    let total_assets = computed("Total Assets", periods, |p| {
        get(&cash, p) + get(&ar, p) + get(&inv, p) + get(&ppe, p) - get(&acc_dep, p)
    });
    let total_liab = computed("Total Liabilities", periods, |p| {
        get(&ap, p) + get(&accrued, p) + get(&debt, p)
    });
    let total_equity = computed("Total Equity", periods, |p| {
        get(&equity, p) + get(&retained, p)
    });
    let balance_check = computed_check("Balance Check", periods, |p| {
        get(&total_assets, p) - get(&total_liab, p) - get(&total_equity, p)
    });

    vec![cash, ar, inv, ppe, acc_dep, total_assets, ap, accrued, debt, total_liab, equity, retained, total_equity, balance_check]
}

fn build_cf_lines(
    records: &[MappedFinancialRecord],
    income_lines: &[StatementLine],
    balance_lines: &[StatementLine],
    periods: &[String],
) -> Vec<StatementLine> {
    let bs_cash = find_line(balance_lines, "Cash");

    // Net income: prefer CF-specific account, fall back to IS net income
    let mut net_income = source_line("Net Income", "net_income", records, periods);
    if net_income.values.values().all(|v| *v == 0.0) {
        if let Some(is_ni) = income_lines.iter().find(|l| l.label == "Net Income") {
            net_income.values = is_ni.values.clone();
        }
    }

    // D&A addback: prefer CF-specific, fall back to IS D&A
    let mut da = source_line("Depreciation Add-back", "depreciation_addback", records, periods);
    if da.values.values().all(|v| *v == 0.0) {
        da = source_line("Depreciation Add-back", "depreciation_amortization", records, periods);
    }

    let wc = source_line("Working Capital Movement", "working_capital_movement", records, periods);
    let capex = source_line("Capital Expenditures", "capex", records, periods);
    let financing = source_line("Financing Movement", "financing_movement", records, periods);

    let net_change = computed_subtotal("Net Change In Cash", periods, |p| {
        get(&net_income, p) + get(&da, p) + get(&wc, p) + get(&capex, p) + get(&financing, p)
    });

    let cash_tieout = computed_check("Cash Flow Tie-Out", periods, |p| {
        let idx = periods.iter().position(|x| x == p).unwrap_or(0);
        if idx == 0 {
            return 0.0;
        }
        let prev = &periods[idx - 1];
        let cash_change = bs_cash.map(|c| get(c, p) - get(c, prev)).unwrap_or(0.0);
        cash_change - get(&net_change, p)
    });

    vec![net_income, da, wc, capex, financing, net_change, cash_tieout]
}

// ── Statement-level validation ────────────────────────────────────────────────

fn statement_issues(
    balance_lines: &[StatementLine],
    cf_lines: &[StatementLine],
    periods: &[String],
    metadata: &HashMap<String, serde_json::Value>,
) -> Vec<ValidationIssue> {
    let mut issues = Vec::new();
    let balance_check = find_line(balance_lines, "Balance Check");
    let cf_tieout = find_line(cf_lines, "Cash Flow Tie-Out");

    for (idx, period) in periods.iter().enumerate() {
        let partial = has_partial_edgar_extraction(metadata, period);

        if let Some(bc) = balance_check {
            let delta = get(bc, period);
            if delta.abs() > f64::EPSILON {
                issues.push(ValidationIssue {
                    code: "balance_sheet_imbalance".to_string(),
                    message: format!("Balance sheet does not balance for {period}."),
                    severity: if partial { IssueSeverity::Warning } else { IssueSeverity::Error },
                    period_label: Some(period.clone()),
                    account_id: None,
                    metadata: {
                        let mut m = HashMap::new();
                        m.insert("difference".to_string(), serde_json::Value::String(delta.to_string()));
                        m.insert("partial_source_extraction".to_string(), serde_json::Value::Bool(partial));
                        m
                    },
                });
            }
        }

        if idx > 0 {
            if let Some(cf) = cf_tieout {
                let delta = get(cf, period);
                if delta.abs() > f64::EPSILON {
                    issues.push(ValidationIssue {
                        code: "cash_flow_tie_out_failure".to_string(),
                        message: format!("Cash flow does not tie to cash movement for {period}."),
                        severity: IssueSeverity::Warning,
                        period_label: Some(period.clone()),
                        account_id: None,
                        metadata: {
                            let mut m = HashMap::new();
                            m.insert("difference".to_string(), serde_json::Value::String(delta.to_string()));
                            m
                        },
                    });
                }
            }
        }
    }
    issues
}

fn has_partial_edgar_extraction(
    metadata: &HashMap<String, serde_json::Value>,
    period: &str,
) -> bool {
    let partial_codes: HashSet<&str> = ["edgar_missing_expected_concept", "edgar_partial_extraction"].into();
    let partial_types: HashSet<&str> = ["partial_extraction", "balance_sheet_partial"].into();

    if let Some(issues) = metadata.get("edgar_source_issues").and_then(|v| v.as_array()) {
        for issue in issues {
            let code = issue.get("code").and_then(|v| v.as_str()).unwrap_or("");
            let itype = issue.get("issue_type").and_then(|v| v.as_str()).unwrap_or("");
            if !partial_codes.contains(code) && !partial_types.contains(itype) {
                continue;
            }
            if let Some(pl) = issue.get("period_label").and_then(|v| v.as_str()) {
                if pl == period { return true; }
                continue;
            }
            if let Some(pls) = issue.get("period_labels").and_then(|v| v.as_array()) {
                if pls.iter().any(|v| v.as_str() == Some(period)) {
                    return true;
                }
            }
        }
    }
    false
}

fn source_completeness_issues(
    metadata: &HashMap<String, serde_json::Value>,
) -> Vec<ValidationIssue> {
    let mut raw_issues = Vec::new();
    for key in ["qbo_source_issues", "edgar_source_issues", "source_issues"] {
        if let Some(arr) = metadata.get(key).and_then(|v| v.as_array()) {
            raw_issues.extend(arr.iter().cloned());
        }
    }

    raw_issues
        .iter()
        .filter_map(|issue| {
            let obj = issue.as_object()?;
            let code = obj.get("code").and_then(|v| v.as_str()).unwrap_or("source_data_issue").to_string();
            let severity = obj
                .get("severity")
                .and_then(|v| v.as_str())
                .and_then(|s| match s {
                    "info" => Some(IssueSeverity::Info),
                    "warning" => Some(IssueSeverity::Warning),
                    "error" => Some(IssueSeverity::Error),
                    _ => None,
                })
                .unwrap_or(IssueSeverity::Error);
            let message = obj.get("message").and_then(|v| v.as_str()).unwrap_or(&code).to_string();
            let period_label = obj.get("period_label").and_then(|v| v.as_str()).map(str::to_string);
            let extra: HashMap<String, serde_json::Value> = obj
                .iter()
                .filter(|(k, _)| !["code", "message", "severity", "period_label"].contains(&k.as_str()))
                .map(|(k, v)| (k.clone(), v.clone()))
                .collect();
            Some(ValidationIssue {
                code,
                message,
                severity,
                period_label,
                account_id: None,
                metadata: extra,
            })
        })
        .collect()
}

// ── Line constructors ─────────────────────────────────────────────────────────

fn source_line(
    label: &str,
    account_id: &str,
    records: &[MappedFinancialRecord],
    periods: &[String],
) -> StatementLine {
    let mut values: HashMap<String, f64> = periods.iter().map(|p| (p.clone(), 0.0)).collect();
    let mut source_ids: HashSet<String> = HashSet::new();

    for record in records {
        if record.account_id.as_deref() != Some(account_id) {
            continue;
        }
        let p = &record.source_record.period_label;
        if values.contains_key(p) {
            *values.get_mut(p).unwrap() += record.source_record.amount;
            source_ids.insert(record.source_record.source_account_id.clone());
        }
    }

    let mut sorted_ids: Vec<_> = source_ids.into_iter().collect();
    sorted_ids.sort();

    StatementLine {
        label: label.to_string(),
        account_id: Some(account_id.to_string()),
        values,
        is_subtotal: false,
        is_check: false,
        source_account_ids: sorted_ids,
    }
}

fn computed(label: &str, periods: &[String], f: impl Fn(&str) -> f64) -> StatementLine {
    StatementLine {
        label: label.to_string(),
        account_id: None,
        values: periods.iter().map(|p| (p.clone(), f(p))).collect(),
        is_subtotal: true,
        is_check: false,
        source_account_ids: vec![],
    }
}

fn computed_subtotal(label: &str, periods: &[String], f: impl Fn(&str) -> f64) -> StatementLine {
    computed(label, periods, f)
}

fn computed_check(label: &str, periods: &[String], f: impl Fn(&str) -> f64) -> StatementLine {
    StatementLine {
        label: label.to_string(),
        account_id: None,
        values: periods.iter().map(|p| (p.clone(), f(p))).collect(),
        is_subtotal: false,
        is_check: true,
        source_account_ids: vec![],
    }
}

fn get(line: &StatementLine, period: &str) -> f64 {
    *line.values.get(period).unwrap_or(&0.0)
}

fn find_line<'a>(lines: &'a [StatementLine], label: &str) -> Option<&'a StatementLine> {
    lines.iter().find(|l| l.label == label)
}
