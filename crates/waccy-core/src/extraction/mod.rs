pub mod edgar;
pub mod qbo;

use std::collections::HashMap;

use crate::{
    classification::DataMapper,
    error::WaccyError,
    models::{
        ExtractedData, MappingOverride, NormalizedFinancialDataset, SourceRecord, SourceReference,
        ValidatedFinancialDataset, CONTRACT_SCHEMA_VERSION,
    },
    utils::dates::infer_reporting_period,
    validation::validate_mapped_dataset,
};

/// Implemented by every data-source adapter.
pub trait Extractor: Send + Sync {
    fn name(&self) -> &str;
    fn source_id(&self) -> &str;
    fn extract(&self, config: &HashMap<String, String>) -> Result<ExtractedData, WaccyError>;
}

/// Registry of available extractors.
#[derive(Default)]
pub struct ExtractorRegistry {
    extractors: HashMap<String, Box<dyn Extractor>>,
}

impl ExtractorRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(&mut self, extractor: Box<dyn Extractor>) {
        self.extractors.insert(extractor.source_id().to_string(), extractor);
    }

    pub fn get(&self, source_id: &str) -> Option<&dyn Extractor> {
        self.extractors.get(source_id).map(AsRef::as_ref)
    }

    pub fn list(&self) -> Vec<&str> {
        self.extractors.keys().map(String::as_str).collect()
    }
}

// ── Normalize → Map → Validate pipeline ──────────────────────────────────────

/// Normalize raw `ExtractedData` into a source-agnostic dataset, inferring
/// periods from record labels where explicit periods are absent.
pub fn normalize(data: &ExtractedData) -> Result<NormalizedFinancialDataset, WaccyError> {
    let mut records: Vec<SourceRecord> = data.source_records.clone();

    // Build period index from explicit periods
    let mut periods_by_label: HashMap<String, crate::models::ReportingPeriod> = data
        .periods
        .iter()
        .map(|p| (p.label.clone(), p.clone()))
        .collect();

    // Infer periods from record labels not already covered
    let mut label_remaps: HashMap<String, String> = HashMap::new();
    for record in &records {
        if periods_by_label.contains_key(&record.period_label) {
            continue;
        }
        if let Ok(period) = infer_reporting_period(&record.period_label) {
            label_remaps
                .entry(record.period_label.clone())
                .or_insert_with(|| period.label.clone());
            periods_by_label.entry(period.label.clone()).or_insert(period);
        }
    }

    // Apply any label remaps
    if !label_remaps.is_empty() {
        for record in &mut records {
            if let Some(new_label) = label_remaps.get(&record.period_label) {
                record.period_label = new_label.clone();
            }
        }
    }

    let mut sorted_periods: Vec<_> = periods_by_label.into_values().collect();
    sorted_periods.sort_by_key(|p| p.start_date);

    Ok(NormalizedFinancialDataset {
        schema_version: CONTRACT_SCHEMA_VERSION.to_string(),
        entity_name: data.entity_name.clone(),
        periods: sorted_periods,
        records,
        metadata: data.metadata.clone(),
    })
}

/// Full pipeline: normalize → map → validate.
pub fn normalize_map_validate(
    data: &ExtractedData,
    overrides: &HashMap<String, MappingOverride>,
) -> Result<ValidatedFinancialDataset, WaccyError> {
    let normalized = normalize(data)?;
    let mapper = DataMapper;
    let mapped = mapper.map(&normalized, overrides)?;
    Ok(validate_mapped_dataset(mapped))
}

// ── Fixture loader (shared by EDGAR + QBO extractors) ────────────────────────

/// Build a `SourceRecord` from a flat fixture dictionary (as produced by the
/// EDGAR and QBO normalizers).
pub fn source_record_from_dict(
    data: &serde_json::Value,
    source_system: &str,
) -> Option<SourceRecord> {
    let obj = data.as_object()?;

    let source_account_id = obj
        .get("source_account_id")
        .or_else(|| obj.get("account_id"))
        .or_else(|| obj.get("name"))?
        .as_str()?
        .to_string();

    let source_account_name = obj
        .get("source_account_name")
        .or_else(|| obj.get("name"))
        .or_else(|| obj.get("account_id"))?
        .as_str()?
        .to_string();

    let amount: f64 = obj
        .get("amount")
        .and_then(|v| v.as_str())
        .and_then(|s| s.parse().ok())
        .or_else(|| obj.get("amount").and_then(|v| v.as_f64()))?;

    let period_label = obj
        .get("period")
        .and_then(|v| v.as_str())?
        .to_string();

    let source_id = obj
        .get("source_id")
        .or_else(|| obj.get("id"))
        .or_else(|| obj.get("account_id"))
        .or_else(|| obj.get("name"))
        .and_then(|v| v.as_str())
        .unwrap_or(&source_account_id)
        .to_string();

    let source_label = obj
        .get("source_label")
        .or_else(|| obj.get("name"))
        .or_else(|| obj.get("account_id"))
        .and_then(|v| v.as_str())
        .unwrap_or(&source_account_name)
        .to_string();

    let metadata: HashMap<String, serde_json::Value> = obj
        .get("metadata")
        .and_then(|v| v.as_object())
        .cloned()
        .map(|m| m.into_iter().collect())
        .unwrap_or_default();

    Some(SourceRecord {
        source_account_id,
        source_account_name,
        amount,
        period_label,
        unit: obj
            .get("unit")
            .and_then(|v| v.as_str())
            .unwrap_or("USD")
            .to_string(),
        statement: obj.get("statement").and_then(|v| v.as_str()).map(str::to_string),
        source_account_type: obj
            .get("source_account_type")
            .or_else(|| obj.get("account_type"))
            .and_then(|v| v.as_str())
            .map(str::to_string),
        source: SourceReference {
            source_system: source_system.to_string(),
            source_id,
            source_label,
            metadata: metadata.clone(),
        },
        metadata,
    })
}
