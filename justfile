BINARY := `which waccy 2>/dev/null || echo ~/.local/bin/waccy`
MCP_BINARY := `which waccy-mcp 2>/dev/null || echo ~/.local/bin/waccy-mcp`

# Build, install, and register waccy
setup: install register
    @echo ""
    @echo "✓ Ready. Run: waccy extract quickbooks"

# Build, and install both binaries
install: build copy
    @echo "✓ Installed waccy and waccy-mcp"

# Build release binaries
build:
    cargo build --release --bin waccy --bin waccy-mcp

# Copy binaries to install location
copy:
    #!/usr/bin/env bash
    set -euo pipefail
    DEST=$(dirname {{BINARY}})
    mkdir -p "$DEST"
    cp target/release/waccy "$DEST/waccy"
    cp target/release/waccy-mcp "$DEST/waccy-mcp"
    echo "  → $DEST/waccy"
    echo "  → $DEST/waccy-mcp"

# Register the MCP server with Claude Code
register:
    claude mcp add waccy {{MCP_BINARY}}
    @echo "✓ Registered waccy MCP server"

# Run tests
test:
    cargo test --all

# Lint
lint:
    cargo clippy --all-targets -- -D warnings
    cargo fmt --check
