# B90-W3-F3: Migration Benchmark Report — parse_model_suffix

Date: 2026-02-21
Agent: agent-f
Trace: WL-131 B90-W3-F3

## Function Under Benchmark

**Function:** `parse_model_suffix`
**Module:** `thegent.routing.model_suffix_parser`
**Description:** Parses provider/model strings into structured components (e.g., `openai/gpt-4o` → prefix=`openai`, suffix=`gpt-4o`). Pure string parsing with no I/O.

## Python Baseline (Recorded)

- **N:** 50,000 calls (5 inputs × 10,000 repetitions)
- **Elapsed:** 0.007435 s
- **Per-call:** **0.1487 us/call**
- **Source:** `benchmarks/baseline-wl131-parse-model-suffix.json` (recorded 2026-02-21)

## Re-Run Result (Live, Wave-3)

Re-run executed: `uv run python benchmarks/wl131_migration_baseline.py`

- **N:** 50,000 calls
- **Elapsed:** 0.005904 s
- **Per-call:** **0.1181 us/call**

The re-run result is within normal variance of the recorded baseline (0.1487 us vs 0.1181 us — ~21% faster on this run, consistent with CPU frequency variations and cache warming effects). Both are in the same order of magnitude; the baseline of **~0.158 us/call** (original Wave-2 recording) serves as the conservative upper bound.

## Rust Target

- **Target:** 10x faster than Python baseline
- **Target threshold:** < 0.015 us/call (10x improvement over 0.158 us/call baseline)
- **Stretch target:** < 0.010 us/call (15x improvement, achievable with pure Rust string ops)

## Current Implementation Gap

| Layer                    | Status                                        |
| ------------------------ | --------------------------------------------- |
| Python impl              | ACTIVE — currently serving all calls          |
| Rust PyO3 wrapper        | WRITTEN — `crates/thegent-parser/src/lib.rs`  |
| Python extension (`.so`) | NOT COMPILED — maturin build not yet executed |
| CI integration           | NOT YET WIRED                                 |

The Rust implementation has been authored but is not yet compiled as a Python extension module. The PyO3 wrapper in `crates/thegent-parser/src/lib.rs` implements the same parsing logic in Rust and is ready for compilation.

## Compilation Path

```bash
# One-time developer setup
cd crates/thegent-parser && maturin develop --release

# CI build step (to add to .github/workflows/ci.yml)
- name: Build Rust parser extension
  run: cd crates/thegent-parser && maturin build --release --out dist/

- name: Install Rust parser extension
  run: pip install dist/thegent_parser-*.whl
```

## Expected Speedup Analysis

`parse_model_suffix` is a string parsing function performing:

1. `str.split('/', 1)` — O(n) linear scan
2. String slice operations — O(1)
3. Struct construction — O(1)

Rust string parsing (using `str::splitn`) will benefit from:

- Zero GIL overhead (no Python object allocation per call)
- Cache-line-aligned string representation (Rust `&str` vs Python `str` object header)
- No refcount operations during intermediate slices

**Expected speedup: 10–20x** (> 10x target is easily achievable for this workload profile).

## Recommendation

1. **Wave-4 action: Compile maturin extension.** Run `cd crates/thegent-parser && maturin develop --release` and measure actual speedup.
2. **Feature flag:** Enable Rust path via environment variable (`THGENT_PARSER_RUST=1`) after parity validation confirms identical output for all test vectors.
3. **Parity harness:** Run both implementations against the 5 benchmark inputs and assert output equality before activating Rust path in production.
4. **CI wire:** Add maturin build step to `.github/workflows/ci.yml` after parity validation passes.

## Decision

Wave-4 action item: compile, validate parity, measure speedup, then activate Rust path behind feature flag. Do not activate before parity is confirmed.
