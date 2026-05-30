#![deny(clippy::all)]

use napi_derive::napi;
use waccy_core::{
    extraction::normalize_map_validate,
    modeling::{ModelBuilder, ModelInput},
    models::ExtractedData,
    query::{dataframe_to_json_rows, QueryEngine},
};

fn data_dir_path(data_dir: Option<String>) -> std::path::PathBuf {
    data_dir
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|| {
            dirs_next::home_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join(".waccy")
        })
}

fn period_filter(period: Option<&str>) -> String {
    match period {
        Some(p) => format!(" AND period_label = '{}'", p.replace('\'', "''")),
        None => String::new(),
    }
}

// ── Query ─────────────────────────────────────────────────────────────────────

/// Execute arbitrary SQL against the financial dataset.
/// Returns an array of row objects.
#[napi]
pub async fn query(sql: String, data_dir: Option<String>) -> napi::Result<serde_json::Value> {
    let dir = data_dir_path(data_dir);
    let rows = tokio::task::spawn_blocking(move || {
        let mut engine = QueryEngine::open(&dir)
            .map_err(|e| napi::Error::from_reason(e.to_string()))?;
        let df = engine
            .execute(&sql)
            .map_err(|e| napi::Error::from_reason(e.to_string()))?;
        Ok::<_, napi::Error>(dataframe_to_json_rows(&df, None))
    })
    .await
    .map_err(|e| napi::Error::from_reason(e.to_string()))??;

    Ok(serde_json::Value::Array(
        rows.into_iter().map(serde_json::Value::Object).collect(),
    ))
}

/// Income statement for the modelled periods.
/// Returns an array of row objects.
#[napi]
pub async fn income_statement(
    period: Option<String>,
    data_dir: Option<String>,
) -> napi::Result<serde_json::Value> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'income_statement'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    query(sql, data_dir).await
}

/// Balance sheet for the modelled periods.
/// Returns an array of row objects.
#[napi]
pub async fn balance_sheet(
    period: Option<String>,
    data_dir: Option<String>,
) -> napi::Result<serde_json::Value> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'balance_sheet'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    query(sql, data_dir).await
}

/// Cash flow statement for the modelled periods.
/// Returns an array of row objects.
#[napi]
pub async fn cash_flow(
    period: Option<String>,
    data_dir: Option<String>,
) -> napi::Result<serde_json::Value> {
    let sql = format!(
        "SELECT * FROM records WHERE statement_kind = 'cash_flow_statement'{} ORDER BY account_id",
        period_filter(period.as_deref())
    );
    query(sql, data_dir).await
}

// ── Modelling ─────────────────────────────────────────────────────────────────

/// Build a three-statement model from JSON-serialised ExtractedData.
/// Returns the full ThreeStatementModel as a plain object.
#[napi]
pub fn build_model(extracted_json: String) -> napi::Result<serde_json::Value> {
    let data: ExtractedData = serde_json::from_str(&extracted_json)
        .map_err(|e| napi::Error::from_reason(format!("invalid input: {e}")))?;

    let validated = normalize_map_validate(&data, &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    let model = ModelBuilder
        .build(ModelInput::Validated(validated), &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    serde_json::to_value(&model).map_err(|e| napi::Error::from_reason(e.to_string()))
}
