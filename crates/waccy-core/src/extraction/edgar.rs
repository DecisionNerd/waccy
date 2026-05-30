/// Normalize SEC companyfacts JSON into WACCY `ExtractedData`.
///
/// Mirrors `EdgarCompanyFactsNormalizer.to_fixture()` from the legacy Python.
use std::collections::HashMap;

use chrono::NaiveDate;
use serde_json::Value;

use crate::{
    error::WaccyError,
    models::{ExtractedData, PeriodType, ReportingPeriod, SourceRecord, SourceReference},
};

/// (statement, us-gaap concept names in priority order)
const CONCEPT_SPECS: &[(&str, &str, &[&str])] = &[
    ("revenue", "income_statement", &["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"]),
    ("cogs", "income_statement", &["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization"]),
    ("operating_expenses", "income_statement", &["OperatingExpenses", "SellingGeneralAndAdministrativeExpense"]),
    ("depreciation_amortization", "income_statement", &["DepreciationDepletionAndAmortizationExpense", "DepreciationDepletionAndAmortization"]),
    ("interest_expense", "income_statement", &["InterestExpense", "InterestExpenseNonOperating"]),
    ("tax_expense", "income_statement", &["IncomeTaxExpenseBenefit"]),
    ("cash", "balance_sheet", &["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    ("accounts_receivable", "balance_sheet", &["AccountsReceivableNetCurrent"]),
    ("inventory", "balance_sheet", &["InventoryNet"]),
    ("ppe", "balance_sheet", &["PropertyPlantAndEquipmentNet"]),
    ("accumulated_depreciation", "balance_sheet", &["AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment"]),
    ("accounts_payable", "balance_sheet", &["AccountsPayableCurrent"]),
    ("accrued_expenses", "balance_sheet", &["AccruedLiabilitiesCurrent", "AccruedIncomeTaxesCurrent"]),
    ("debt", "balance_sheet", &["LongTermDebtCurrent", "LongTermDebtNoncurrent", "LongTermDebtAndFinanceLeaseObligationsCurrent", "LongTermDebtAndFinanceLeaseObligationsNoncurrent"]),
    ("equity", "balance_sheet", &["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    ("retained_earnings", "balance_sheet", &["RetainedEarningsAccumulatedDeficit"]),
    ("net_income", "cash_flow_statement", &["NetIncomeLoss"]),
    ("depreciation_addback", "cash_flow_statement", &["DepreciationDepletionAndAmortizationExpense", "DepreciationDepletionAndAmortization"]),
    ("working_capital_movement", "cash_flow_statement", &["IncreaseDecreaseInOperatingAssetsAndLiabilitiesNetOfAcquisitions", "NetCashProvidedByUsedInOperatingActivities"]),
    ("capex", "cash_flow_statement", &["PaymentsToAcquirePropertyPlantAndEquipment"]),
    ("financing_movement", "cash_flow_statement", &["ProceedsFromIssuanceOfDebt", "ProceedsFromIssuanceOfLongTermDebt", "RepaymentsOfDebt"]),
];

/// Convert an SEC companyfacts JSON payload into `ExtractedData`.
///
/// `periods` controls how many trailing fiscal years to include (default 4).
pub fn normalize_companyfacts(
    companyfacts: &Value,
    periods: usize,
    taxonomy: &str,
) -> Result<ExtractedData, WaccyError> {
    if periods == 0 {
        return Err(WaccyError::Extraction(
            "EDGAR companyfacts periods must be a positive integer.".to_string(),
        ));
    }

    let facts = companyfacts
        .get("facts")
        .and_then(|f| f.get(taxonomy))
        .and_then(|f| f.as_object())
        .ok_or_else(|| {
            WaccyError::Extraction(format!(
                "Companyfacts payload is missing facts.{taxonomy}."
            ))
        })?;

    let target_years = target_fiscal_years(facts, periods);
    let mut source_records: Vec<SourceRecord> = Vec::new();
    let mut period_map: HashMap<String, ReportingPeriod> = HashMap::new();
    let mut source_issues: Vec<Value> = Vec::new();
    let target_period_labels: Vec<String> =
        target_years.iter().map(|y| format!("FY{y}")).collect();

    for (canonical, statement, concepts) in CONCEPT_SPECS {
        match select_fact(facts, concepts, &target_years) {
            None => {
                source_issues.push(serde_json::json!({
                    "code": "edgar_missing_expected_concept",
                    "message": format!("No annual 10-K companyfacts concept found for {canonical}."),
                    "severity": "warning",
                    "source": "edgar",
                    "issue_type": "partial_extraction",
                    "account_id": canonical,
                    "period_labels": target_period_labels,
                }));
            }
            Some(facts_by_year) => {
                for (concept, fact) in &facts_by_year {
                    let fy = fact["fy"].as_i64().unwrap_or(0);
                    let period_label = format!("FY{fy}");
                    let val = fact["val"].as_f64().unwrap_or(0.0);
                    let end_str = fact["end"].as_str().unwrap_or("");
                    let start_str = fact.get("start").and_then(|v| v.as_str());

                    let end_date = NaiveDate::parse_from_str(end_str, "%Y-%m-%d")
                        .unwrap_or_else(|_| NaiveDate::from_ymd_opt(fy as i32, 12, 31).unwrap());
                    let start_date = start_str
                        .and_then(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d").ok())
                        .unwrap_or(end_date);

                    // Update period map (expand dates on collision)
                    period_map
                        .entry(period_label.clone())
                        .and_modify(|p| {
                            if start_date < p.start_date { p.start_date = start_date; }
                            if end_date > p.end_date { p.end_date = end_date; }
                        })
                        .or_insert(ReportingPeriod {
                            label: period_label.clone(),
                            start_date,
                            end_date,
                            period_type: PeriodType::Year,
                        });

                    let mut meta = HashMap::new();
                    meta.insert("canonical_account_hint".to_string(), Value::String(canonical.to_string()));
                    meta.insert("concept".to_string(), Value::String(concept.to_string()));
                    if let Some(v) = fact.get("accn") { meta.insert("accession".to_string(), v.clone()); }
                    if let Some(v) = fact.get("filed") { meta.insert("filed".to_string(), v.clone()); }
                    if let Some(v) = fact.get("form") { meta.insert("form".to_string(), v.clone()); }
                    if let Some(v) = fact.get("fp") { meta.insert("fp".to_string(), v.clone()); }
                    if let Some(v) = fact.get("fy") { meta.insert("fy".to_string(), v.clone()); }
                    meta.insert("is_instant".to_string(), Value::Bool(start_str.is_none()));

                    let full_concept = format!("us-gaap:{concept}");
                    source_records.push(SourceRecord {
                        source_account_id: full_concept.clone(),
                        source_account_name: full_concept.clone(),
                        amount: val,
                        period_label: period_label.clone(),
                        unit: "USD".to_string(),
                        statement: Some(statement.to_string()),
                        source_account_type: None,
                        source: SourceReference {
                            source_system: "edgar".to_string(),
                            source_id: full_concept.clone(),
                            source_label: full_concept.clone(),
                            metadata: meta.clone(),
                        },
                        metadata: meta,
                    });
                }
            }
        }
    }

    let mut periods: Vec<ReportingPeriod> = period_map.into_values().collect();
    periods.sort_by_key(|p| p.start_date);

    let entity_name = companyfacts
        .get("entityName")
        .and_then(|v| v.as_str())
        .unwrap_or("EDGAR Entity")
        .to_string();

    let mut metadata = HashMap::new();
    metadata.insert("source".to_string(), Value::String("edgar".to_string()));
    metadata.insert("mode".to_string(), Value::String("companyfacts_normalized".to_string()));
    metadata.insert("taxonomy".to_string(), Value::String(taxonomy.to_string()));
    metadata.insert("edgar_source_issues".to_string(), Value::Array(source_issues));
    if let Some(cik) = companyfacts.get("cik") {
        metadata.insert("cik".to_string(), cik.clone());
    }

    Ok(ExtractedData {
        entity_name,
        periods,
        source_records,
        metadata,
    })
}

// ── Helpers ───────────────────────────────────────────────────────────────────

fn target_fiscal_years(facts: &serde_json::Map<String, Value>, periods: usize) -> Vec<i64> {
    let mut years = std::collections::BTreeSet::new();
    for concept_data in facts.values() {
        if let Some(units) = concept_data.get("units").and_then(|u| u.as_object()) {
            for unit_facts in units.values() {
                if let Some(arr) = unit_facts.as_array() {
                    for fact in arr {
                        if fact.get("form").and_then(|v| v.as_str()) == Some("10-K")
                            && fact.get("fp").and_then(|v| v.as_str()) == Some("FY")
                        {
                            if let Some(fy) = fact.get("fy").and_then(|v| v.as_i64()) {
                                years.insert(fy);
                            }
                        }
                    }
                }
            }
        }
    }
    let all: Vec<i64> = years.into_iter().collect();
    let n = all.len().min(periods);
    all[all.len().saturating_sub(n)..].to_vec()
}

/// Returns `Some(vec[(concept_name, fact_value)])` indexed by fiscal year,
/// choosing the latest filing per year across the candidate concepts.
fn select_fact(
    facts: &serde_json::Map<String, Value>,
    concepts: &[&str],
    target_years: &[i64],
) -> Option<Vec<(String, Value)>> {
    let target_set: std::collections::HashSet<i64> = target_years.iter().copied().collect();
    // year → (concept, fact)
    let mut by_year: HashMap<i64, (String, Value)> = HashMap::new();

    for concept in concepts {
        let annual_facts: Vec<&Value> = facts
            .get(*concept)
            .and_then(|c| c.get("units"))
            .and_then(|u| u.get("USD"))
            .and_then(|u| u.as_array())
            .map(|arr| {
                arr.iter()
                    .filter(|f| {
                        f.get("form").and_then(|v| v.as_str()) == Some("10-K")
                            && f.get("fp").and_then(|v| v.as_str()) == Some("FY")
                            && f.get("fy").and_then(|v| v.as_i64()).is_some()
                            && f.get("end").and_then(|v| v.as_str()).is_some()
                            && f.get("val").is_some()
                    })
                    .filter(|f| {
                        target_set.contains(&f["fy"].as_i64().unwrap_or(0))
                    })
                    .collect()
            })
            .unwrap_or_default();

        // latest-by-fiscal-year within this concept
        let mut latest: HashMap<i64, &Value> = HashMap::new();
        for fact in &annual_facts {
            let fy = fact["fy"].as_i64().unwrap_or(0);
            let entry = latest.entry(fy).or_insert(fact);
            let filed_new = fact.get("filed").and_then(|v| v.as_str()).unwrap_or("");
            let filed_old = entry.get("filed").and_then(|v| v.as_str()).unwrap_or("");
            if filed_new > filed_old {
                *entry = fact;
            }
        }

        for (fy, fact) in latest {
            by_year.entry(fy).or_insert((concept.to_string(), (*fact).clone()));
        }
    }

    if by_year.is_empty() {
        return None;
    }
    let mut result: Vec<(String, Value)> = by_year
        .into_iter()
        .map(|(_fy, pair)| pair)
        .collect();
    result.sort_by_key(|(_, f)| f["fy"].as_i64().unwrap_or(0));
    Some(result)
}
