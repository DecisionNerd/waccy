#!/usr/bin/env bash
# install.sh — install waccy and register the MCP server
# Usage: curl -fsSL https://raw.githubusercontent.com/DecisionNerd/waccy/main/scripts/install.sh | bash
set -euo pipefail

REPO="DecisionNerd/waccy"
BIN_DIR="${WACCY_BIN_DIR:-$HOME/.local/bin}"

# ── colours ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; RESET="\033[0m"
else
  BOLD=""; GREEN=""; YELLOW=""; RED=""; RESET=""
fi

ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
err()  { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }
step() { echo -e "\n${BOLD}$*${RESET}"; }

# ── 1. install binary ──────────────────────────────────────────────────────────
step "Installing waccy…"

if command -v brew &>/dev/null; then
  if brew list waccy &>/dev/null 2>&1; then
    ok "waccy already installed via Homebrew"
  else
    echo "  Installing via Homebrew…"
    brew tap DecisionNerd/tap &>/dev/null
    brew install waccy
    ok "Installed via Homebrew"
  fi
  WACCY_BIN="$(brew --prefix)/bin/waccy"
  WACCY_MCP_BIN="$(brew --prefix)/bin/waccy-mcp"
else
  if command -v waccy &>/dev/null; then
    ok "waccy already installed at $(which waccy)"
    WACCY_BIN="$(which waccy)"
    _mcp="$(which waccy-mcp 2>/dev/null || true)"
    WACCY_MCP_BIN="${_mcp:-$BIN_DIR/waccy-mcp}"
  else
    echo "  Homebrew not found — building from source (requires Rust)…"
    command -v cargo &>/dev/null || err "Rust/cargo not found. Install from https://rustup.rs or install Homebrew first."
    mkdir -p "$BIN_DIR"
    TMP_DIR="$(mktemp -d)"
    git clone --depth 1 "https://github.com/$REPO.git" "$TMP_DIR" &>/dev/null
    pushd "$TMP_DIR" &>/dev/null
    cargo build --release --locked --bin waccy --bin waccy-mcp 2>&1 | tail -3
    cp target/release/waccy "$BIN_DIR/"
    cp target/release/waccy-mcp "$BIN_DIR/"
    popd &>/dev/null
    rm -rf "$TMP_DIR"
    WACCY_BIN="$BIN_DIR/waccy"
    WACCY_MCP_BIN="$BIN_DIR/waccy-mcp"
    ok "Built and installed to $BIN_DIR"
  fi
fi

# ── 2. register MCP server ─────────────────────────────────────────────────────
step "Registering MCP server…"

REGISTERED=0

# Claude Code
if command -v claude &>/dev/null; then
  if claude mcp list 2>/dev/null | grep -q "waccy"; then
    ok "Claude Code: already registered"
  else
    claude mcp add waccy "$WACCY_MCP_BIN"
    ok "Claude Code: registered"
  fi
  REGISTERED=1
fi

# Codex
if command -v codex &>/dev/null; then
  if codex mcp list 2>/dev/null | grep -q "waccy"; then
    ok "Codex: already registered"
  else
    codex mcp add waccy -- "$WACCY_MCP_BIN"
    ok "Codex: registered"
  fi
  REGISTERED=1
fi

# Claude Desktop
CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -d "$HOME/Library/Application Support/Claude" ]; then
  if [ -f "$CLAUDE_DESKTOP_CONFIG" ] && grep -q "waccy" "$CLAUDE_DESKTOP_CONFIG" 2>/dev/null; then
    ok "Claude Desktop: already registered"
  else
    if [ ! -f "$CLAUDE_DESKTOP_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_DESKTOP_CONFIG"
    fi
    python3 - "$CLAUDE_DESKTOP_CONFIG" "$WACCY_MCP_BIN" << 'PYEOF'
import json, sys
path, mcp_bin = sys.argv[1], sys.argv[2]
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault("mcpServers", {})["waccy"] = {"command": mcp_bin}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF
    ok "Claude Desktop: registered (restart the app to apply)"
  fi
  REGISTERED=1
fi

# Cursor — global config
CURSOR_CONFIG="$HOME/.cursor/mcp.json"
if [ -d "$HOME/.cursor" ]; then
  if [ -f "$CURSOR_CONFIG" ] && grep -q "waccy" "$CURSOR_CONFIG" 2>/dev/null; then
    ok "Cursor: already registered"
  else
    if [ ! -f "$CURSOR_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CURSOR_CONFIG"
    fi
    python3 - "$CURSOR_CONFIG" "$WACCY_MCP_BIN" << 'PYEOF'
import json, sys
path, mcp_bin = sys.argv[1], sys.argv[2]
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault("mcpServers", {})["waccy"] = {"command": mcp_bin}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF
    ok "Cursor: registered (restart Cursor to apply)"
  fi
  REGISTERED=1
fi

if [ "$REGISTERED" -eq 0 ]; then
  warn "No supported AI client detected. Add this to your client's MCP config manually:"
  echo ""
  echo '  { "mcpServers": { "waccy": { "command": "'"$WACCY_MCP_BIN"'" } } }'
  echo ""
fi

# ── done ───────────────────────────────────────────────────────────────────────
echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]] && ! command -v waccy &>/dev/null; then
  warn "$BIN_DIR is not on your PATH. Add it to your shell profile:"
  echo "  export PATH=\"\$PATH:$BIN_DIR\""
  echo ""
fi

ok "Done. Ask your AI agent: \"Build a three-statement model from my QuickBooks data.\""
