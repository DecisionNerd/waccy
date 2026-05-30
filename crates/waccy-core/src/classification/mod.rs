pub mod ontology;

pub use ontology::CHART;

use crate::{
    error::WaccyError,
    models::{
        MappedFinancialDataset, MappedFinancialRecord, MappingDiagnostic, MappingOverride,
        MappingStatus, NormalizedFinancialDataset, CONTRACT_SCHEMA_VERSION,
    },
};
use std::collections::HashMap;

pub struct DataMapper;

impl DataMapper {
    pub fn map(
        &self,
        dataset: &NormalizedFinancialDataset,
        overrides: &HashMap<String, MappingOverride>,
    ) -> Result<MappedFinancialDataset, WaccyError> {
        let chart = &*CHART;
        let mut records = Vec::new();

        for record in &dataset.records {
            // Check overrides (4 keys: id, name, system:id, system:name)
            let override_key = [
                record.source_account_id.as_str(),
                record.source_account_name.as_str(),
                &format!("{}:{}", record.source.source_system, record.source_account_id),
                &format!("{}:{}", record.source.source_system, record.source_account_name),
            ]
            .iter()
            .find_map(|k| overrides.get(*k));

            if let Some(ov) = override_key {
                records.push(apply_override(record.clone(), ov, chart));
                continue;
            }

            let mut candidates = chart.map_candidates(&record.source_account_name);

            // Narrow by statement hint if ambiguous
            if candidates.len() > 1 {
                if let Some(stmt) = &record.statement {
                    let stmt_key = stmt.as_str();
                    let narrowed: Vec<_> = candidates
                        .iter()
                        .filter(|a| {
                            let sk = match a.statement {
                                crate::models::StatementKind::IncomeStatement => "income_statement",
                                crate::models::StatementKind::BalanceSheet => "balance_sheet",
                                crate::models::StatementKind::CashFlowStatement => "cash_flow_statement",
                            };
                            sk == stmt_key
                        })
                        .copied()
                        .collect();
                    if !narrowed.is_empty() {
                        candidates = narrowed;
                    }
                }
            }

            let mapped = match candidates.len() {
                1 => MappedFinancialRecord {
                    source_record: record.clone(),
                    account_id: Some(candidates[0].id.clone()),
                    account_name: Some(candidates[0].name.clone()),
                    status: MappingStatus::Mapped,
                    confidence: 0.95,
                    diagnostics: vec![],
                    override_note: None,
                },
                0 => MappedFinancialRecord {
                    source_record: record.clone(),
                    account_id: None,
                    account_name: None,
                    status: MappingStatus::Unmapped,
                    confidence: 0.0,
                    diagnostics: vec![MappingDiagnostic {
                        code: "unmapped_account".to_string(),
                        message: format!(
                            "No WACCY account mapping for {:?}.",
                            record.source_account_name
                        ),
                    }],
                    override_note: None,
                },
                _ => MappedFinancialRecord {
                    source_record: record.clone(),
                    account_id: None,
                    account_name: None,
                    status: MappingStatus::Ambiguous,
                    confidence: 0.4,
                    diagnostics: vec![MappingDiagnostic {
                        code: "ambiguous_mapping".to_string(),
                        message: format!(
                            "Source account matched multiple WACCY accounts: {}",
                            candidates.iter().map(|a| a.id.as_str()).collect::<Vec<_>>().join(", ")
                        ),
                    }],
                    override_note: None,
                },
            };
            records.push(mapped);
        }

        Ok(MappedFinancialDataset {
            schema_version: CONTRACT_SCHEMA_VERSION.to_string(),
            entity_name: dataset.entity_name.clone(),
            periods: dataset.periods.clone(),
            records,
            metadata: dataset.metadata.clone(),
        })
    }
}

fn apply_override(
    record: crate::models::SourceRecord,
    ov: &MappingOverride,
    chart: &ontology::StandardChartOfAccounts,
) -> MappedFinancialRecord {
    let account = chart.get(&ov.account_id);
    let mut diagnostics = vec![];
    if account.is_none() {
        diagnostics.push(MappingDiagnostic {
            code: "invalid_override".to_string(),
            message: format!("Override account {:?} is not in the ontology.", ov.account_id),
        });
    }
    MappedFinancialRecord {
        source_record: record,
        account_id: Some(account.map(|a| a.id.clone()).unwrap_or_else(|| ov.account_id.clone())),
        account_name: account.map(|a| a.name.clone()),
        status: MappingStatus::Overridden,
        confidence: if account.is_some() { 1.0 } else { 0.0 },
        diagnostics,
        override_note: if ov.note.is_empty() { None } else { Some(ov.note.clone()) },
    }
}
