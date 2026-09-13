# Hooks Deployment Guide

## Overview

The `thegent-hooks` crate provides 10 Rust binaries for governance and quality enforcement.

## Binaries

| Binary                     | Purpose                         |
| -------------------------- | ------------------------------- |
| `thegent-hooks`            | Main CLI entry point            |
| `quality-gate`             | Policy evaluation               |
| `security-pipeline`        | Security scanning               |
| `stop-reconcile`           | Git status & conflict detection |
| `spec-verifier`            | FR coverage scanning            |
| `pre-write-validator`      | File validation                 |
| `qa-policy-test`           | Policy tests                    |
| `task-completion-verifier` | Task verification               |
| `post-edit-checker`        | AI slop detection               |
| `complexity-ratchet`       | Complexity enforcement          |

## Building

```bash
cd crates
cargo build -p thegent-hooks --bins
```

Output binaries in `target/debug/`

## Installation

### Local

```bash
cargo install --path crates/thegent-hooks --bin thegent-hooks
```

### Via GitHub Releases

```bash
# Download from releases
curl -L https://github.com/kooshapari/thegent/releases/latest/download/thegent-hooks -o thegent-hooks
chmod +x thegent-hooks
```

## Usage

All hooks read JSON from stdin and output JSON to stdout.

### Exit Codes

- `0` - Success/pass
- `1` - Warning/failure
- `2` - Error

### Example: stop-reconcile

```bash
echo '{"project_dir": "/path/to/repo", "session_id": "abc123"}' | ./stop-reconcile
```

### Example: spec-verifier

```bash
echo '{"project_dir": ".", "threshold": 0.8}' | ./spec-verifier
```

## CI Integration

Add to `.github/workflows/hooks.yml`:

```yaml
name: Hooks CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test -p thegent-hooks --lib
      - run: cargo clippy -p thegent-hooks -- -D warnings
```

## Configuration

Hooks accept configuration via JSON input:

- `project_dir` - Project root (required)
- `session_id` - Current session identifier
- `dry_run` - Preview mode (boolean)
- `threshold` - Coverage/complexity thresholds (float)

## Troubleshooting

### Build fails

- Ensure Rust 1.70+ is installed
- Run `cargo update` to refresh dependencies

### Tests fail

- Git tests require git config: `git config --global user.email "test@test.com"`
- Some tests require clean git repo

### Binary not found

- Check `target/debug/` for built binaries
- Use `--bin <name>` to build specific binary
