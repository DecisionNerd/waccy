use serde_json::{json, Value};
use std::sync::{Arc, Mutex, MutexGuard};
use waccy_core::query::QueryEngine;

pub struct ServerState {
    engine: Mutex<Option<QueryEngine>>,
    pub data_dir: std::path::PathBuf,
}

impl ServerState {
    pub fn new() -> Self {
        let data_dir = dirs_next::home_dir()
            .unwrap_or_else(|| std::path::PathBuf::from("."))
            .join(".waccy");
        Self {
            engine: Mutex::new(None),
            data_dir,
        }
    }

    /// Return a locked guard with an initialised engine, creating it if needed.
    /// Must be called inside `spawn_blocking` — std Mutex blocks the thread.
    pub fn ensure_engine(&self) -> Result<MutexGuard<'_, Option<QueryEngine>>, String> {
        let mut guard = self.engine.lock().map_err(|e| e.to_string())?;
        if guard.is_none() {
            let engine = QueryEngine::open(&self.data_dir).map_err(|e| e.to_string())?;
            *guard = Some(engine);
        }
        Ok(guard)
    }

    pub fn invalidate_engine(&self) {
        if let Ok(mut guard) = self.engine.lock() {
            *guard = None;
        }
    }
}

pub async fn handle(state: Arc<ServerState>, msg: Value) -> Option<Value> {
    msg.get("id")?;
    let id = msg["id"].clone();
    let method = msg.get("method")?.as_str()?;
    let params = msg.get("params").cloned().unwrap_or(json!({}));

    let result = match method {
        "initialize" => Ok(json!({
            "protocolVersion": "2024-11-05",
            "capabilities": { "tools": {} },
            "serverInfo": { "name": "waccy", "version": env!("CARGO_PKG_VERSION") }
        })),

        "tools/list" => Ok(json!({ "tools": crate::tools::list() })),

        "tools/call" => {
            let tool_name = params.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let args = params.get("arguments").cloned().unwrap_or(json!({}));
            crate::tools::call(state, &tool_name, args).await
        }

        _ => return Some(error_response(id, -32601, &format!("Method not found: {method}"))),
    };

    Some(match result {
        Ok(r) => json!({ "jsonrpc": "2.0", "id": id, "result": r }),
        Err(e) => error_response(id, -32603, &e),
    })
}

pub fn error_response(id: Value, code: i64, message: &str) -> Value {
    json!({
        "jsonrpc": "2.0",
        "id": id,
        "error": { "code": code, "message": message }
    })
}
