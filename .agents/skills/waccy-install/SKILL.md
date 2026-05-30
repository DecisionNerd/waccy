---
name: waccy-install
description: Check whether waccy is installed and the MCP server is registered, and fix anything that's missing.
---

# WACCY Install

Verify the installation is complete and working. Install or register anything that's missing.

## When to Use

- After running `npx skills add DecisionNerd/waccy` for the first time
- "Set up waccy"
- "Install waccy"
- "Is waccy set up?"
- "Register the MCP server"
- On first use if the MCP tools aren't responding

## Steps

### 1 — Check the binary

```bash
which waccy && waccy --version
```

**If missing**, install via Homebrew (recommended):

```bash
brew tap DecisionNerd/tap && brew install waccy
```

**If Homebrew isn't available**, install from source:

```bash
cargo install --git https://github.com/DecisionNerd/waccy --bins
```

### 2 — Check the MCP server binary

```bash
which waccy-mcp
```

If missing, re-run the install step — `waccy-mcp` is installed alongside `waccy`.

### 3 — Check MCP registration

```bash
claude mcp list   # Claude Code
codex mcp list    # Codex
```

Look for `waccy` in the output. If it's not listed, register it:

**Claude Code:**
```bash
claude mcp add waccy $(which waccy-mcp)
```

**Codex:**
```bash
codex mcp add waccy -- $(which waccy-mcp)
```

### 4 — Check dataset status

```bash
waccy status
```

If no dataset is found, run the first extraction:

```bash
waccy extract quickbooks
# or
waccy extract edgar --option cik=0001234567
```

### 5 — Report status

Summarise what was found and what (if anything) was fixed:

- Binary: installed at `<path>` ✓ / installed now ✓ / not found ✗
- MCP server: registered ✓ / registered now ✓
- Dataset: present ✓ / needs first extraction

If everything is good, offer to run `/model` to build a three-statement model.
