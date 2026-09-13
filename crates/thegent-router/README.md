# Thegent Router

Pareto-efficient routing engine in Rust.

## Audit Benchmark

Run the Criterion suite for audit hash-chain structures:

`CARGO_NET_OFFLINE=true cargo bench --locked --manifest-path ../../crates/Cargo.toml -p thegent-router --bench audit_bench`

### Deterministic No-Network Verification

- Use `CARGO_NET_OFFLINE=true` and `--locked` so the run cannot hit the network or mutate lock resolution.
- Keep bench inputs fixed (100/1000/10000 records) to ensure deterministic workload shape across runs.
- Run static verification with `uv run pytest tests/test_wl079_audit_bench.py -q`.
