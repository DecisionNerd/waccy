use std::collections::HashSet;

use crate::models::{
    IssueSeverity, MappedFinancialDataset, MappingStatus, ValidatedFinancialDataset,
    ValidationIssue, CONTRACT_SCHEMA_VERSION,
};

pub fn validate_mapped_dataset(dataset: MappedFinancialDataset) -> ValidatedFinancialDataset {
    let mut issues = Vec::new();

    // Period checks
    let mut seen_labels = HashSet::new();
    for period in &dataset.periods {
        if !seen_labels.insert(period.label.clone()) {
            issues.push(ValidationIssue {
                code: "duplicate_period".to_string(),
                message: format!("Duplicate reporting period {:?}.", period.label),
                severity: IssueSeverity::Error,
                period_label: Some(period.label.clone()),
                account_id: None,
                metadata: Default::default(),
            });
        }
        if period.start_date > period.end_date {
            issues.push(ValidationIssue {
                code: "invalid_period_range".to_string(),
                message: format!("Period {:?} starts after it ends.", period.label),
                severity: IssueSeverity::Error,
                period_label: Some(period.label.clone()),
                account_id: None,
                metadata: Default::default(),
            });
        }
    }

    let period_labels: HashSet<String> =
        dataset.periods.iter().map(|p| p.label.clone()).collect();

    // Record checks
    for record in &dataset.records {
        let pl = &record.source_record.period_label;
        if !period_labels.contains(pl) {
            issues.push(ValidationIssue {
                code: "missing_period".to_string(),
                message: format!(
                    "Record {:?} references missing period {:?}.",
                    record.source_record.source.source_id, pl
                ),
                severity: IssueSeverity::Error,
                period_label: Some(pl.clone()),
                account_id: record.account_id.clone(),
                metadata: Default::default(),
            });
        }

        match record.status {
            MappingStatus::Mapped | MappingStatus::Overridden if record.account_id.is_none() => {
                issues.push(ValidationIssue {
                    code: "missing_mapped_account_id".to_string(),
                    message: format!(
                        "Record {:?} is {:?} but has no account_id.",
                        record.source_record.source.source_id, record.status
                    ),
                    severity: IssueSeverity::Error,
                    period_label: Some(pl.clone()),
                    account_id: None,
                    metadata: Default::default(),
                });
            }
            MappingStatus::Unmapped => {
                let is_summary_check = record
                    .source_record
                    .metadata
                    .get("is_summary_check")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                if is_summary_check {
                    issues.push(ValidationIssue {
                        code: "unmapped_source_check".to_string(),
                        message: format!(
                            "Unmapped source check {:?}.",
                            record.source_record.source_account_name
                        ),
                        severity: IssueSeverity::Info,
                        period_label: Some(pl.clone()),
                        account_id: None,
                        metadata: Default::default(),
                    });
                } else {
                    issues.push(ValidationIssue {
                        code: "unmapped_account".to_string(),
                        message: format!(
                            "Unmapped account {:?}.",
                            record.source_record.source_account_name
                        ),
                        severity: IssueSeverity::Error,
                        period_label: Some(pl.clone()),
                        account_id: None,
                        metadata: Default::default(),
                    });
                }
            }
            MappingStatus::Ambiguous => {
                issues.push(ValidationIssue {
                    code: "ambiguous_mapping".to_string(),
                    message: format!(
                        "Ambiguous account {:?}.",
                        record.source_record.source_account_name
                    ),
                    severity: IssueSeverity::Warning,
                    period_label: Some(pl.clone()),
                    account_id: None,
                    metadata: Default::default(),
                });
            }
            MappingStatus::Overridden if record.account_id.is_some() => {
                issues.push(ValidationIssue {
                    code: "mapping_overridden".to_string(),
                    message: format!(
                        "Mapping overridden for {:?}.",
                        record.source_record.source_account_name
                    ),
                    severity: IssueSeverity::Info,
                    period_label: Some(pl.clone()),
                    account_id: record.account_id.clone(),
                    metadata: Default::default(),
                });
            }
            _ => {}
        }
    }

    if dataset.records.is_empty() {
        issues.push(ValidationIssue {
            code: "empty_dataset".to_string(),
            message: "No financial records are available for validation.".to_string(),
            severity: IssueSeverity::Error,
            period_label: None,
            account_id: None,
            metadata: Default::default(),
        });
    }

    ValidatedFinancialDataset {
        schema_version: CONTRACT_SCHEMA_VERSION.to_string(),
        mapped_dataset: dataset,
        issues,
    }
}
