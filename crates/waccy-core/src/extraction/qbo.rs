/// Normalize raw QuickBooks Online report payloads into WACCY `ExtractedData`.
///
/// Mirrors `QuickBooksReportNormalizer.to_fixture()` from the legacy Python.
use std::collections::HashMap;

use chrono::{Datelike, NaiveDate};
use serde_json::Value;

use crate::{
    error::WaccyError,
    models::{ExtractedData, PeriodType, ReportingPeriod, SourceRecord, SourceReference},
};

const REPORT_STATEMENTS: &[(&str, &str)] = &[
    ("ProfitAndLoss", "income_statement"),
    ("BalanceSheet", "balance_sheet"),
    ("CashFlow", "cash_flow_statement"),
];
const REQUIRED_REPORTS: &[&str] = &["ProfitAndLoss", "BalanceSheet", "CashFlow"];

/// Convert a raw QBO report payload into `ExtractedData`.
///
/// `payload` should be the dictionary produced by `QuickBooksApiClient.pull_financial_reports()`,
/// with keys: `entity_name`, `reports` (dict), `accounts` (list), `end_date`.
pub fn normalize_qbo_reports(payload: &Value) -> Result<ExtractedData, WaccyError> {
    let data = payload.as_object().ok_or_else(|| {
        WaccyError::Extraction("QBO normalization requires a JSON object payload.".to_string())
    })?;

    let reports_raw = data.get("reports").and_then(|r| r.as_object()).ok_or_else(|| {
        WaccyError::Extraction("QBO normalization requires a 'reports' object.".to_string())
    })?;

    // Build accounts index
    let accounts_by_id = build_accounts_by_id(data.get("accounts"));

    // Determine reports-by-period structure
    let reports_by_period = reports_by_period(data, reports_raw)?;

    let mut source_records: Vec<SourceRecord> = Vec::new();
    let mut period_map: HashMap<String, ReportingPeriod> = HashMap::new();
    let mut source_issues: Vec<Value> = Vec::new();
    let mut seen_issue_keys: std::collections::HashSet<(String, String, String)> = Default::default();
    let mut report_record_counts: HashMap<String, usize> = HashMap::new();

    for (period_label, reports) in &reports_by_period {
        let present: std::collections::HashSet<String> = reports
            .keys()
            .map(|k| report_name(k, reports.get(k).and_then(|v| v.as_object()).unwrap_or(&Default::default())))
            .collect();

        for required in REQUIRED_REPORTS {
            if !present.contains(*required) {
                push_issue(
                    &mut source_issues,
                    &mut seen_issue_keys,
                    make_issue(
                        "missing_required_source_statement",
                        &format!("Missing required QBO report {required:?} for {period_label}."),
                        required,
                        period_label,
                    ),
                );
            }
        }

        for (report_key, report_val) in reports {
            let report_obj = match report_val.as_object() {
                Some(o) => o,
                None => continue,
            };
            let rname = report_name(report_key, report_obj);
            let stmt = match REPORT_STATEMENTS.iter().find(|(k, _)| *k == rname) {
                Some((_, s)) => *s,
                None => continue,
            };

            let period = period_from_report(period_label, report_obj)?;
            period_map.entry(period.label.clone()).or_insert(period.clone());

            if has_no_report_data(report_obj) {
                push_issue(
                    &mut source_issues,
                    &mut seen_issue_keys,
                    make_issue(
                        "qbo_report_no_data",
                        &format!("QBO report {rname:?} has NoReportData=true for {}.", period.label),
                        &rname,
                        &period.label,
                    ),
                );
            }

            let before = source_records.len();
            collect_records(
                report_obj,
                &rname,
                stmt,
                &period.label,
                &accounts_by_id,
                &mut source_records,
            );
            let count = source_records.len() - before;
            report_record_counts.insert(format!("{}:{rname}", period.label), count);
        }
    }

    // Check for zero-record required reports
    for period_label in period_map.keys() {
        for required in REQUIRED_REPORTS {
            let count = report_record_counts
                .get(&format!("{period_label}:{required}"))
                .copied()
                .unwrap_or(0);
            if count == 0 {
                push_issue(
                    &mut source_issues,
                    &mut seen_issue_keys,
                    make_issue(
                        "missing_required_source_statement",
                        &format!("Required QBO report {required:?} produced no source records for {period_label}."),
                        required,
                        period_label,
                    ),
                );
            }
        }
    }

    let mut periods: Vec<ReportingPeriod> = period_map.into_values().collect();
    periods.sort_by_key(|p| p.start_date);

    let entity_name = data
        .get("entity_name")
        .and_then(|v| v.as_str())
        .unwrap_or("QuickBooks Entity")
        .to_string();

    let mut metadata = HashMap::new();
    metadata.insert("source".to_string(), Value::String("qbo".to_string()));
    metadata.insert("mode".to_string(), Value::String("raw_report_normalized".to_string()));
    metadata.insert("qbo_source_issues".to_string(), Value::Array(source_issues));

    Ok(ExtractedData {
        entity_name,
        periods,
        source_records,
        metadata,
    })
}

// ── Helpers ───────────────────────────────────────────────────────────────────

fn build_accounts_by_id(raw: Option<&Value>) -> HashMap<String, Value> {
    let mut map = HashMap::new();
    if let Some(arr) = raw.and_then(|v| v.as_array()) {
        for account in arr {
            if let Some(obj) = account.as_object() {
                let id = obj
                    .get("Id")
                    .or_else(|| obj.get("id"))
                    .and_then(|v| v.as_str())
                    .map(str::to_string);
                if let Some(id) = id {
                    map.insert(id, account.clone());
                }
            }
        }
    }
    map
}

/// Returns a HashMap<period_label, HashMap<report_key, report_value>>.
fn reports_by_period(
    data: &serde_json::Map<String, Value>,
    reports_raw: &serde_json::Map<String, Value>,
) -> Result<HashMap<String, HashMap<String, Value>>, WaccyError> {
    // Check if values have "Header" — single-period flat structure
    let is_flat = reports_raw
        .values()
        .all(|r| r.as_object().map(|o| o.contains_key("Header")).unwrap_or(false));

    if is_flat {
        // Single period: use end_date as key
        let fallback = data
            .get("end_date")
            .and_then(|v| v.as_str())
            .unwrap_or("report_period")
            .to_string();
        let first = reports_raw.values().next().unwrap();
        let period = period_from_report(&fallback, first.as_object().unwrap_or(&Default::default()))?;
        let inner: HashMap<String, Value> = reports_raw
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        Ok(HashMap::from([(period.label, inner)]))
    } else {
        // Multi-period: keys are period labels
        let mut out = HashMap::new();
        for (label, reports) in reports_raw {
            if let Some(obj) = reports.as_object() {
                out.insert(
                    label.clone(),
                    obj.iter().map(|(k, v)| (k.clone(), v.clone())).collect(),
                );
            }
        }
        Ok(out)
    }
}

fn report_name(key: &str, obj: &serde_json::Map<String, Value>) -> String {
    obj.get("Header")
        .and_then(|h| h.get("ReportName"))
        .and_then(|v| v.as_str())
        .unwrap_or(key)
        .to_string()
}

fn period_from_report(
    fallback_label: &str,
    report: &serde_json::Map<String, Value>,
) -> Result<ReportingPeriod, WaccyError> {
    let header = report.get("Header").and_then(|h| h.as_object());
    let end = header
        .and_then(|h| h.get("EndPeriod"))
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if end.is_empty() {
        return Err(WaccyError::Extraction(
            "QBO report Header.EndPeriod is required.".to_string(),
        ));
    }
    let end_date = NaiveDate::parse_from_str(end, "%Y-%m-%d")
        .map_err(|_| WaccyError::Extraction(format!("Invalid EndPeriod date {end:?}.")))?;
    let start_str = header
        .and_then(|h| h.get("StartPeriod"))
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let start_date = if start_str.is_empty() {
        NaiveDate::from_ymd_opt(end_date.year(), 1, 1).unwrap()
    } else {
        NaiveDate::parse_from_str(start_str, "%Y-%m-%d").unwrap_or(
            NaiveDate::from_ymd_opt(end_date.year(), 1, 1).unwrap(),
        )
    };

    let label = if fallback_label == "report_period"
        || fallback_label.ends_with("-12-31")
        || fallback_label.ends_with("-06-30")
    {
        end_date.format("%Y").to_string()
    } else {
        fallback_label.to_string()
    };

    Ok(ReportingPeriod {
        label,
        start_date,
        end_date,
        period_type: PeriodType::Year,
    })
}

fn has_no_report_data(report: &serde_json::Map<String, Value>) -> bool {
    report
        .get("Header")
        .and_then(|h| h.get("Option"))
        .and_then(|o| o.as_array())
        .map(|opts| {
            opts.iter().any(|opt| {
                opt.get("Name").and_then(|v| v.as_str()) == Some("NoReportData")
                    && opt
                        .get("Value")
                        .and_then(|v| v.as_str())
                        .map(|s| s.to_ascii_lowercase() == "true")
                        .unwrap_or(false)
            })
        })
        .unwrap_or(false)
}

fn collect_records(
    report: &serde_json::Map<String, Value>,
    report_name: &str,
    statement: &str,
    period_label: &str,
    accounts_by_id: &HashMap<String, Value>,
    records: &mut Vec<SourceRecord>,
) {
    let rows = report
        .get("Rows")
        .and_then(|r| r.get("Row"))
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default();

    walk_rows(
        &rows,
        &[],
        report_name,
        statement,
        period_label,
        report
            .get("Header")
            .and_then(|h| h.get("Currency"))
            .and_then(|v| v.as_str())
            .unwrap_or("USD"),
        accounts_by_id,
        records,
    );
}

#[allow(clippy::too_many_arguments)]
fn walk_rows(
    rows: &[Value],
    path: &[String],
    report_name: &str,
    statement: &str,
    period_label: &str,
    unit: &str,
    accounts_by_id: &HashMap<String, Value>,
    records: &mut Vec<SourceRecord>,
) {
    for row in rows {
        let obj = match row.as_object() {
            Some(o) => o,
            None => continue,
        };

        let label = row_label(obj);
        let mut next_path = path.to_vec();
        if !label.is_empty() {
            next_path.push(label);
        }

        // Recurse into child rows
        if let Some(child_rows) = obj.get("Rows").and_then(|r| r.get("Row")).and_then(|r| r.as_array()) {
            walk_rows(
                child_rows,
                &next_path,
                report_name,
                statement,
                period_label,
                unit,
                accounts_by_id,
                records,
            );
        }

        let row_type = obj.get("type").and_then(|v| v.as_str()).unwrap_or("");

        if row_type == "Data" {
            if let Some(record) = record_from_row(
                obj, &next_path, report_name, statement, period_label, unit, accounts_by_id,
            ) {
                records.push(record);
            }
        } else if report_name == "CashFlow" {
            if let Some(record) =
                cash_flow_summary_record(obj, &next_path, report_name, statement, period_label, unit)
            {
                records.push(record);
            }
        }
    }
}

fn record_from_row(
    row: &serde_json::Map<String, Value>,
    path: &[String],
    report_name: &str,
    statement: &str,
    period_label: &str,
    unit: &str,
    accounts_by_id: &HashMap<String, Value>,
) -> Option<SourceRecord> {
    let columns = row.get("ColData")?.as_array()?;
    if columns.len() < 2 {
        return None;
    }
    let account_col = columns[0].as_object()?;
    let amount_col = columns.last()?.as_object()?;

    let account_name = account_col.get("value")?.as_str()?.trim().to_string();
    if account_name.is_empty() {
        return None;
    }
    let amount = parse_decimal(amount_col.get("value"))?;
    let account_id = account_col
        .get("id")
        .and_then(|v| v.as_str())
        .unwrap_or(&account_name)
        .to_string();

    let account = accounts_by_id.get(&account_id);
    let account_type = account
        .and_then(|a| a.get("AccountType").or_else(|| a.get("Classification")))
        .and_then(|v| v.as_str())
        .map(str::to_string);

    let mut meta = HashMap::new();
    meta.insert("report_name".to_string(), Value::String(report_name.to_string()));
    meta.insert(
        "row_path".to_string(),
        Value::Array(path.iter().map(|s| Value::String(s.clone())).collect()),
    );
    if let Some(acc) = account {
        meta.insert("qbo_account".to_string(), acc.clone());
    }

    Some(SourceRecord {
        source_account_id: account_id.clone(),
        source_account_name: account_name.clone(),
        amount,
        period_label: period_label.to_string(),
        unit: unit.to_string(),
        statement: Some(statement.to_string()),
        source_account_type: account_type,
        source: SourceReference {
            source_system: "qbo".to_string(),
            source_id: account_id,
            source_label: account_name,
            metadata: meta.clone(),
        },
        metadata: meta,
    })
}

fn cash_flow_summary_record(
    row: &serde_json::Map<String, Value>,
    path: &[String],
    report_name: &str,
    statement: &str,
    period_label: &str,
    unit: &str,
) -> Option<SourceRecord> {
    let summary = row.get("Summary")?.get("ColData")?.as_array()?;
    if summary.len() < 2 {
        return None;
    }
    let label = summary[0].get("value")?.as_str()?.trim().to_string();
    if label != "Net Change In Cash" {
        return None;
    }
    let amount = parse_decimal(summary.last()?.get("value"))?;

    let mut meta = HashMap::new();
    meta.insert("report_name".to_string(), Value::String(report_name.to_string()));
    meta.insert(
        "row_path".to_string(),
        Value::Array(path.iter().map(|s| Value::String(s.clone())).collect()),
    );
    meta.insert("is_summary_check".to_string(), Value::Bool(true));

    Some(SourceRecord {
        source_account_id: label.clone(),
        source_account_name: label.clone(),
        amount,
        period_label: period_label.to_string(),
        unit: unit.to_string(),
        statement: Some(statement.to_string()),
        source_account_type: None,
        source: SourceReference {
            source_system: "qbo".to_string(),
            source_id: label.clone(),
            source_label: label,
            metadata: meta.clone(),
        },
        metadata: meta,
    })
}

fn row_label(row: &serde_json::Map<String, Value>) -> String {
    for key in ["Header", "Summary", "ColData"] {
        if let Some(val) = row.get(key) {
            let cols = if key == "ColData" {
                val.as_array().cloned().unwrap_or_default()
            } else {
                val.get("ColData")
                    .and_then(|c| c.as_array())
                    .cloned()
                    .unwrap_or_default()
            };
            if let Some(first) = cols.first() {
                if let Some(s) = first.get("value").and_then(|v| v.as_str()) {
                    let trimmed = s.trim();
                    if !trimmed.is_empty() {
                        return trimmed.to_string();
                    }
                }
            }
        }
    }
    String::new()
}

/// Parse an amount string, handling parenthesized negatives: "(1000)" → -1000.
fn parse_decimal(val: Option<&Value>) -> Option<f64> {
    let s = val?.as_str()?.trim().replace(',', "");
    if s.is_empty() {
        return None;
    }
    if s.starts_with('(') && s.ends_with(')') {
        let inner = &s[1..s.len() - 1];
        return inner.parse::<f64>().ok().map(|v| -v);
    }
    s.parse().ok()
}

fn make_issue(code: &str, message: &str, report_name: &str, period_label: &str) -> Value {
    serde_json::json!({
        "code": code,
        "message": message,
        "severity": "error",
        "source": "qbo",
        "report_name": report_name,
        "period_label": period_label,
    })
}

fn push_issue(
    issues: &mut Vec<Value>,
    seen: &mut std::collections::HashSet<(String, String, String)>,
    issue: Value,
) {
    let key = (
        issue["code"].as_str().unwrap_or("").to_string(),
        issue["report_name"].as_str().unwrap_or("").to_string(),
        issue["period_label"].as_str().unwrap_or("").to_string(),
    );
    if seen.insert(key) {
        issues.push(issue);
    }
}
