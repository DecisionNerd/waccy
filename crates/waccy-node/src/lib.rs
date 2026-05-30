#![deny(clippy::all)]

use napi_derive::napi;
use waccy_core::{
    extraction::normalize_map_validate,
    modeling::{ModelBuilder, ModelInput},
    models::ExtractedData,
    query::{dataframe_to_json_rows, statement_to_dataframe, QueryEngine},
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

fn df_to_json_value(
    df: &polars::prelude::DataFrame,
    limit: Option<usize>,
) -> serde_json::Value {
    let rows = dataframe_to_json_rows(df, limit);
    serde_json::Value::Array(rows.into_iter().map(serde_json::Value::Object).collect())
}

// ── Query ─────────────────────────────────────────────────────────────────────

/// Execute arbitrary SQL against the financial dataset.
/// Returns an array of row objects. The primary table is `records`.
#[napi]
pub async fn query(sql: String, data_dir: Option<String>) -> napi::Result<serde_json::Value> {
    let dir = data_dir_path(data_dir);
    let rows = tokio::task::spawn_blocking(move || {
        let mut engine = QueryEngine::open(&dir)
            .map_err(|e| napi::Error::from_reason(e.to_string()))?;
        let df = engine
            .execute(&sql)
            .map_err(|e| napi::Error::from_reason(e.to_string()))?;
        Ok::<_, napi::Error>(df_to_json_value(&df, None))
    })
    .await
    .map_err(|e| napi::Error::from_reason(e.to_string()))??;
    Ok(rows)
}

/// Income statement rows for the modelled periods.
/// Returns `StatementRow[]` — one row per (line, period) pair.
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

/// Balance sheet rows for the modelled periods.
/// Returns `StatementRow[]` — one row per (line, period) pair.
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

/// Cash flow statement rows for the modelled periods.
/// Returns `StatementRow[]` — one row per (line, period) pair.
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
///
/// Returns `{ income_statement, balance_sheet, cash_flow_statement }` where each
/// value is a `StatementRow[]` — one row per (line, period) pair.
/// This is the natural shape for charting, pivoting, or passing to nodejs-polars:
///
/// ```ts
/// import pl from 'nodejs-polars'
/// const { income_statement } = await buildModel(dataJson)
/// const df = pl.from_records(income_statement)
/// ```
///
/// For the full model object including validation issues and metadata,
/// use `buildModelJson`.
#[napi]
pub fn build_model(extracted_json: String) -> napi::Result<serde_json::Value> {
    let data: ExtractedData = serde_json::from_str(&extracted_json)
        .map_err(|e| napi::Error::from_reason(format!("invalid input: {e}")))?;

    let validated = normalize_map_validate(&data, &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    let model = ModelBuilder
        .build(ModelInput::Validated(validated), &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    let income_df = statement_to_dataframe(&model.income_statement)
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;
    let balance_df = statement_to_dataframe(&model.balance_sheet)
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;
    let cashflow_df = statement_to_dataframe(&model.cash_flow_statement)
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    Ok(serde_json::json!({
        "income_statement":    df_to_json_value(&income_df, None),
        "balance_sheet":       df_to_json_value(&balance_df, None),
        "cash_flow_statement": df_to_json_value(&cashflow_df, None),
    }))
}

/// Build a three-statement model and return the full ThreeStatementModel as a
/// JSON string, including validation issues and metadata.
///
/// Use this when you need `validation_issues`, `entity_name`, or the raw model
/// structure. For row-oriented access use `buildModel`.
#[napi]
pub fn build_model_json(extracted_json: String) -> napi::Result<String> {
    let data: ExtractedData = serde_json::from_str(&extracted_json)
        .map_err(|e| napi::Error::from_reason(format!("invalid input: {e}")))?;

    let validated = normalize_map_validate(&data, &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    let model = ModelBuilder
        .build(ModelInput::Validated(validated), &Default::default())
        .map_err(|e| napi::Error::from_reason(e.to_string()))?;

    serde_json::to_string(&model).map_err(|e| napi::Error::from_reason(e.to_string()))
}
