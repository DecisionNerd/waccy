mod server;
mod tools;

use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::WARN.into()),
        )
        .init();

    let mut stdin = BufReader::new(tokio::io::stdin());
    let mut stdout = tokio::io::stdout();

    let state = std::sync::Arc::new(server::ServerState::new());

    let mut line = String::new();
    loop {
        line.clear();
        match stdin.read_line(&mut line).await {
            Ok(0) => break,
            Err(e) => {
                tracing::error!("stdin read error: {e}");
                break;
            }
            Ok(_) => {}
        }

        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let response = match serde_json::from_str::<serde_json::Value>(trimmed) {
            Ok(msg) => server::handle(state.clone(), msg).await,
            Err(e) => Some(server::error_response(
                serde_json::Value::Null,
                -32700,
                &format!("Parse error: {e}"),
            )),
        };

        if let Some(resp) = response {
            let mut bytes = serde_json::to_vec(&resp).unwrap();
            bytes.push(b'\n');
            if let Err(e) = stdout.write_all(&bytes).await {
                tracing::error!("stdout write error: {e}");
                break;
            }
            let _ = stdout.flush().await;
        }
    }
}
