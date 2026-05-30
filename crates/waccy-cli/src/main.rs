use clap::{Parser, Subcommand};
use clap_complete::Shell;

#[derive(Parser)]
#[command(
    name = "waccy",
    about = "Intelligent financial modelling for small businesses",
    version
)]
struct Cli {
    /// Output format: table, json, csv
    #[arg(long, global = true, default_value = "table")]
    format: String,

    /// Suppress progress indicators
    #[arg(short, long, global = true, default_value_t = false)]
    quiet: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Extract financial data from a source (quickbooks, edgar)
    Extract {
        source: String,
        /// Source-specific connection options as key=value pairs
        #[arg(long)]
        option: Vec<String>,
    },
    /// Build a three-statement financial model from extracted data
    Model {
        /// Path to extracted data file (JSON)
        #[arg(long)]
        data: Option<String>,
    },
    /// Show dataset status
    Status,
    /// Execute arbitrary SQL against the financial dataset
    Query {
        sql: String,
        #[arg(long, default_value_t = 50)]
        limit: usize,
    },
    /// Generate shell completions
    Completions { shell: Shell },
}

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::WARN.into()),
        )
        .init();

    let cli = Cli::parse();

    let result: Result<(), String> = match cli.command {
        Commands::Extract { source, option } => {
            let opts: std::collections::HashMap<String, String> = option
                .iter()
                .filter_map(|kv| {
                    let mut parts = kv.splitn(2, '=');
                    Some((parts.next()?.to_string(), parts.next()?.to_string()))
                })
                .collect();
            run_extract(&source, &opts)
        }
        Commands::Model { data } => run_model(data.as_deref()),
        Commands::Status => run_status(),
        Commands::Query { sql, limit } => run_query(&sql, limit),
        Commands::Completions { shell } => {
            use clap::CommandFactory;
            clap_complete::generate(shell, &mut Cli::command(), "waccy", &mut std::io::stdout());
            Ok(())
        }
    };

    if let Err(e) = result {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

fn run_extract(source: &str, opts: &std::collections::HashMap<String, String>) -> Result<(), String> {
    println!("Extracting from {source}…");
    let _ = opts;
    // TODO: wire extractor registry
    println!("Done.");
    Ok(())
}

fn run_model(data: Option<&str>) -> Result<(), String> {
    let _ = data;
    println!("Building three-statement model…");
    // TODO: wire ModelBuilder
    println!("Done.");
    Ok(())
}

fn run_status() -> Result<(), String> {
    println!("No dataset found. Run `waccy extract <source>` first.");
    Ok(())
}

fn run_query(sql: &str, limit: usize) -> Result<(), String> {
    let _ = (sql, limit);
    println!("No dataset found. Run `waccy extract <source>` first.");
    Ok(())
}
