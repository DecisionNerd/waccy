use crate::{error::WaccyError, models::FinancialStatement};
use polars::polars_utils::pl_path::PlRefPath;
use polars::prelude::*;
use polars_sql::SQLContext;
use std::path::Path;

/// Reads stored Parquet files and executes SQL or filter queries via Polars.
///
/// `open` is synchronous and cheap — `scan_parquet` reads only file metadata.
/// `execute` is also synchronous; wrap in `tokio::task::spawn_blocking` when
/// calling from an async context (MCP server, Node addon).
pub struct QueryEngine {
    ctx: SQLContext,
}

impl QueryEngine {
    /// Scan all `.parquet` files in `data_dir`, registering each as a SQL table
    /// named after its file stem (e.g. `records.parquet` → table `records`).
    pub fn open(data_dir: &Path) -> Result<Self, WaccyError> {
        let ctx = SQLContext::new();

        if data_dir.exists() {
            for entry in std::fs::read_dir(data_dir)? {
                let entry = entry?;
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) == Some("parquet") {
                    let table_name = path
                        .file_stem()
                        .and_then(|s| s.to_str())
                        .unwrap_or("records")
                        .to_string();
                    let pl_path = PlRefPath::try_from_path(&path)?;
                    let lf = LazyFrame::scan_parquet(pl_path, ScanArgsParquet::default())?;
                    ctx.register(&table_name, lf);
                }
            }
        }

        Ok(Self { ctx })
    }

    /// Execute a SQL query and collect results into a `DataFrame`.
    pub fn execute(&mut self, sql: &str) -> Result<DataFrame, WaccyError> {
        let lf = self.ctx.execute(sql)?;
        Ok(lf.collect()?)
    }

    /// Return the schema of the `records` table without materialising data.
    pub fn schema(&mut self) -> Result<Schema, WaccyError> {
        let mut lf = self.ctx.execute("SELECT * FROM records LIMIT 0")?;
        let schema = lf.collect_schema()?;
        Ok((*schema).clone())
    }
}

/// Serialise a `DataFrame` to a `Vec` of JSON row objects.
///
/// This is the canonical output format for MCP tools and the Node addon.
/// `limit` caps the number of rows; pass `None` for no cap.
pub fn dataframe_to_json_rows(
    df: &DataFrame,
    limit: Option<usize>,
) -> Vec<serde_json::Map<String, serde_json::Value>> {
    let height = match limit {
        Some(n) => df.height().min(n),
        None => df.height(),
    };
    let columns = df.columns();
    let mut rows = Vec::with_capacity(height);

    for i in 0..height {
        let mut map = serde_json::Map::new();
        for col in columns {
            let val = anyvalue_to_json(col.get(i).unwrap_or(AnyValue::Null));
            map.insert(col.name().to_string(), val);
        }
        rows.push(map);
    }

    rows
}

/// Convert a `FinancialStatement` to a tidy long-format `DataFrame`.
///
/// Schema: `label | account_id | period_label | amount | is_subtotal | is_check | source_account_ids`
///
/// Each row is one (line, period) pair. This is the natural Polars shape for
/// pivoting, plotting, and further analysis.
pub fn statement_to_dataframe(stmt: &FinancialStatement) -> Result<DataFrame, WaccyError> {
    let mut labels: Vec<Option<String>> = Vec::new();
    let mut account_ids: Vec<Option<String>> = Vec::new();
    let mut period_labels: Vec<String> = Vec::new();
    let mut amounts: Vec<f64> = Vec::new();
    let mut is_subtotal: Vec<bool> = Vec::new();
    let mut is_check: Vec<bool> = Vec::new();
    let mut source_ids: Vec<String> = Vec::new();

    let periods: Vec<&str> = stmt.periods.iter().map(|p| p.label.as_str()).collect();

    for line in &stmt.lines {
        for &period in &periods {
            labels.push(Some(line.label.clone()));
            account_ids.push(line.account_id.clone());
            period_labels.push(period.to_string());
            amounts.push(*line.values.get(period).unwrap_or(&0.0));
            is_subtotal.push(line.is_subtotal);
            is_check.push(line.is_check);
            source_ids.push(line.source_account_ids.join(","));
        }
    }

    let df = DataFrame::new_infer_height(vec![
        Column::new("label".into(), labels),
        Column::new("account_id".into(), account_ids),
        Column::new("period_label".into(), period_labels),
        Column::new("amount".into(), amounts),
        Column::new("is_subtotal".into(), is_subtotal),
        Column::new("is_check".into(), is_check),
        Column::new("source_account_ids".into(), source_ids),
    ])?;

    Ok(df)
}

fn anyvalue_to_json(v: AnyValue<'_>) -> serde_json::Value {
    match v {
        AnyValue::Null => serde_json::Value::Null,
        AnyValue::Boolean(b) => serde_json::Value::Bool(b),
        AnyValue::Int8(n) => (n as i64).into(),
        AnyValue::Int16(n) => (n as i64).into(),
        AnyValue::Int32(n) => (n as i64).into(),
        AnyValue::Int64(n) => n.into(),
        AnyValue::UInt8(n) => (n as u64).into(),
        AnyValue::UInt16(n) => (n as u64).into(),
        AnyValue::UInt32(n) => (n as u64).into(),
        AnyValue::UInt64(n) => n.into(),
        AnyValue::Float32(f) => serde_json::Number::from_f64(f as f64)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null),
        AnyValue::Float64(f) => serde_json::Number::from_f64(f)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null),
        AnyValue::String(s) => serde_json::Value::String(s.to_string()),
        AnyValue::StringOwned(s) => serde_json::Value::String(s.to_string()),
        other => serde_json::Value::String(format!("{other}")),
    }
}
