# Headless LSP Quick Start Guide

**Date**: 2026-02-18
**Purpose**: Quick guide for using headless LSP infrastructure

---

## What is Headless LSP?

**Headless LSP** provides Language Server Protocol (LSP) servers running without a GUI, perfect for:

- Agent-driven development
- CI/CD pipelines
- Automated code analysis
- Batch formatting/inspection

**Supported Languages**: Python, TypeScript, Rust, Go, Java, C++, Bash, YAML, JSON

---

## Quick Start

### 1. Start LSP Server

```bash
# Start Python LSP
thegent lsp start python

# Start TypeScript LSP
thegent lsp start typescript

# Start Rust LSP
thegent lsp start rust
```

### 2. List Running Servers

```bash
# Show all running LSP servers
thegent lsp list
```

Output:

```
┌─────────────────────────────────────────┐
│      Running LSP Servers                │
├──────────┬──────┬───────────┬──────────┤
│ Language │ PID  │ Status    │ Uptime   │
├──────────┼──────┼───────────┼──────────┤
│ python   │ 1234 │ ✅ Running│ 45s      │
│ typescript│ 5678│ ✅ Running│ 120s     │
└──────────┴──────┴───────────┴──────────┘
```

### 3. Stop LSP Server

```bash
# Stop Python LSP
thegent lsp stop python
```

---

## JetBrains Integration

### Prerequisites

- IntelliJ IDEA Ultimate installed
- `idea` command in PATH (or auto-detected)

### Format Files

```bash
# Format Python files
thegent lsp format src/**/*.py --project /path/to/project

# Format TypeScript files
thegent lsp format src/**/*.ts --project /path/to/project
```

### Run Inspections

```bash
# Run code inspections
thegent lsp inspect /path/to/project

# With custom profile
thegent lsp inspect /path/to/project --profile "Default"
```

---

## Installation

### Install LSP Servers

If LSP servers are missing, install them:

**Python**:

```bash
npm install -g pyright
```

**TypeScript**:

```bash
npm install -g typescript-language-server typescript
```

**Rust**:

```bash
rustup component add rust-analyzer
```

**Go**:

```bash
go install golang.org/x/tools/gopls@latest
```

**C++**:

```bash
# macOS
brew install llvm

# Linux
apt-get install clangd
```

---

## Troubleshooting

### Issue: "LSP server 'X' not found"

**Solution**: Install the missing LSP server (see Installation section above).

### Issue: "IntelliJ IDEA not found"

**Solution**:

1. Ensure IntelliJ IDEA Ultimate is installed
2. Add `idea` to PATH, or
3. Specify path: `JetBrainsCLI(ide_path=Path("/path/to/idea"))`

### Issue: LSP server crashes

**Solution**: Check logs:

```bash
# Check process status
thegent lsp list

# Restart server
thegent lsp stop python
thegent lsp start python
```

---

## Advanced Usage

### Programmatic Usage

```python
from thegent.lsp.headless_manager import HeadlessLSPManager
from thegent.lsp.jetbrains_cli import JetBrainsCLI
from pathlib import Path

# Start LSP server
manager = HeadlessLSPManager()
server = manager.ensure_server("python")

# Format files
cli = JetBrainsCLI()
result = cli.format([Path("src/main.py"), Path("src/utils.py")], project_root=Path("/path/to/project"))

if result["success"]:
    print("Files formatted!")
```

---

## Related Documentation

- **Full Design**: `docs/research/HEADLESS_LSP_JETBRAINS_DESIGN_2026-02-18.md`
- **Implementation Summary**: `docs/research/HEADLESS_LSP_IMPLEMENTATION_SUMMARY_2026-02-18.md`
- **JetBrains CLI Docs**: https://www.jetbrains.com/help/idea/working-with-the-ide-features-from-command-line.html

---

## Status

**Current Status**: Core implementation complete, testing pending

**Known Limitations**:

- JetBrains Gateway not yet implemented
- Multi-client LSP proxy not yet implemented
- Remote LSP support not yet implemented

**Roadmap**: See design document for full roadmap.
