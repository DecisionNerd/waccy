use serde_json::{json, Value};
use std::sync::Arc;
use waccy_core::query::dataframe_to_json_rows;

use crate::server::ServerState;

pub fn list() -> Value {
    json!([
        {
            "name": "extract",
            "description": "Extract financial data from a source and build the dataset.",
            "inputSchema": {
                "type": "object",
                "required": ["source"],
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["quickbooks", "edgar"],
                        "description": "Data source to extract from"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force a full rebuild even if a dataset already exists"
                    }
                }
            }
        },
        {
            "name": "model",
            "description": "Build a three-statement financial model from the current dataset.",
            "inputSchema": { "type": "object", "properties": {} }
        },
        {
            "name": "query",
            "description": "Execute arbitrary SQL against the financial dataset. The primary table is `records`.",
            "inputSchema": {
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql":   { "type": "string", "description": "SQL query to run" },
                    "limit": { "type": "integer", "description": "Max rows (default 100)" }
                }
            }
        },
        {
            "name": "income_statement",
            "description": "Income statement for the modelled periods.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": { "type": "string", "description": "Period label, e.g. 2024 or 2024-Q1" }
                }
            }
        },
        {
            "name": "balance_sheet",
            "description": "Balance sheet for the modelled periods.",
            "inputSchema": {
                "type": "object",
                "properties": { "period": { "type": "string" } }
            }
        },
        {
            "name": "cash_flow",
            "description": "Cash flow statement for the modelled periods.",
            "inputSchema": {
                "type": "object",
                "properties": { "period": { "type": "string" } }
            }
        },
        {
            "name": "status",
            "description": "Show dataset status — last extraction time, record count.",
            "inputSchema": { "type": "object", "properties": {} }
        },
        {
            "name": "schema",
            "description": "Return the dataset schema (column names and types).",
            "inputSchema": { "type": "object", "properties": {} }
        }
    ])
}

pub async fn call(state: Arc<ServerState>, name: &str, args: Value) -> Result<Value, String> {
    match name {
        "extract" => {
            let source = args.get("source").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
            state.invalidate_engine();
            Ok(json!({ "content": [{ "type": "text", "text": format!("Extract from {source} is not yet wired — call `waccy extract {source}` from the CLI.") }] }))
        }

        "model" => Ok(json!({ "content": [{ "type": "text", "text": "Model build is not yet wired — call `waccy model` from the CLI." }] })),

        "status" => {
            let data_dir = state.data_dir.clone();
            let synced = data_dir.exists()
                && std::fs::read_dir(&data_dir)
                    .map(|mut d| d.next().is_some())
                    .unwrap_or(false);
            let result = if synced {
                json!({ "synced": true, "data_dir": data_dir.to_string_lossy() })
            } else {
                json!({ "synced": false, "message": "No dataset found. Run `waccy extract <source>` first." })
            };
            Ok(json!({ "content": [{ "type": "text", "text": serde_json::to_string(&result).unwrap() }] }))
        }

        "schema" => {
            let state2 = Arc::clone(&state);
            tokio::task::spawn_blocking(move || {
                let mut guard = state2.ensure_engine()?;
                let engine = guard.as_mut().unwrap();
                let schema = engine.schema().map_err(|e| e.to_string())?;
                Ok(json!({ "content": [{ "type": "text", "text": format!("{schema:?}") }] }))
            })
            .await
            .map_err(|e| e.to_string())?
        }

        _ => {
            let sql = build_sql(name, &args)?;
            let limit = args.get("limit").and_then(|v| v.as_u64()).unwrap_or(100) as usize;
            let state2 = Arc::clone(&state);
            tokio::task::spawn_blocking(move || {
                let mut guard = state2.ensure_engine()?;
                let engine = guard.as_mut().unwrap();
                let df = engine.execute(&sql).map_err(|e| e.to_string())?;
                let rows = dataframe_to_json_rows(&df, Some(limit));
                Ok(json!({ "content": [{ "type": "text", "text": serde_json::to_string(&rows).unwrap() }] }))
            })
            .await
            .map_err(|e| e.to_string())?
        }
    }
}

fn build_sql(name: &str, args: &Value) -> Result<String, String> {
    let str_arg = |key: &str| -> Option<String> { args.get(key)?.as_str().map(str::to_string) };

    Ok(match name {
        "query" => str_arg("sql").ok_or("missing `sql` argument")?,
        "income_statement" => {
            let filter = period_filter(str_arg("period").as_deref());
            format!("SELECT * FROM records WHERE statement_kind = 'income_statement'{filter} ORDER BY account_id")
        }
        "balance_sheet" => {
            let filter = period_filter(str_arg("period").as_deref());
            format!("SELECT * FROM records WHERE statement_kind = 'balance_sheet'{filter} ORDER BY account_id")
        }
        "cash_flow" => {
            let filter = period_filter(str_arg("period").as_deref());
            format!("SELECT * FROM records WHERE statement_kind = 'cash_flow_statement'{filter} ORDER BY account_id")
        }
        _ => return Err(format!("Unknown tool: {name}")),
    })
}

fn period_filter(period: Option<&str>) -> String {
    match period {
        Some(p) => format!(" AND period_label = '{}'", p.replace('\'', "''")),
        None => String::new(),
    }
}
