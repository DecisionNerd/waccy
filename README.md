# WACCY

Intelligent financial modelling for small businesses — built in Rust.

Extracts, maps, and synthesises financial data from QuickBooks Online and SEC EDGAR into institutional-quality three-statement models.

## Install

```sh
# Homebrew (recommended)
brew tap DecisionNerd/tap && brew install waccy

# Cargo
cargo install --git https://github.com/DecisionNerd/waccy

# Python (query-only)
pip install waccy

# Claude Code / Cursor skills
npx skills add DecisionNerd/waccy

# Universal script (also registers MCP server)
curl -fsSL https://raw.githubusercontent.com/DecisionNerd/waccy/main/scripts/install.sh | bash
```

## Quick start

```sh
# Extract financial data
waccy extract quickbooks
waccy extract edgar --option cik=0001234567

# Build three-statement model
waccy model

# Query results
waccy query "SELECT * FROM records WHERE statement_kind = 'income_statement'"
```

## MCP server

Register the MCP server (`waccy-mcp`) with your AI client:

```sh
# Claude Code
claude mcp add waccy $(which waccy-mcp)
```

Then ask your AI agent: _"Build a three-statement model from my QuickBooks data."_

## Distribution surfaces

| Surface | Package | How |
|---------|---------|-----|
| CLI | `waccy` binary | Homebrew / `cargo install` |
| MCP server | `waccy-mcp` binary | Registered via `claude mcp add` |
| Python | `waccy` on PyPI | `pip install waccy` |
| Agent skills | 11 skills | `npx skills add DecisionNerd/waccy` |

## Architecture

```
crates/
  waccy-core/     # Shared library: models, extraction, classification, modeling, query
  waccy-cli/      # Binary: waccy CLI
  waccy-mcp/      # Binary: waccy-mcp MCP server (JSON-RPC 2.0 over stdio)
  waccy-python/   # PyO3 cdylib: Python bindings (built with maturin)
legacy/           # Original Python implementation (archived)
```

## Development

```sh
cargo build --release          # Build binaries
cargo test --all               # Run tests
cargo clippy --all-targets     # Lint
cargo fmt                      # Format

# Python wheel
cd crates/waccy-python && maturin develop

# Full setup
just setup
```

## License

MIT
