"""WL-079: Offline-safe assertions for Rust audit benchmark wiring."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_router_cargo_declares_audit_bench_target() -> None:
    cargo_toml = REPO_ROOT / "crates" / "thegent-router" / "Cargo.toml"
    data = tomllib.loads(cargo_toml.read_text(encoding="utf-8"))
    benches = data.get("bench", [])
    audit_entries = [entry for entry in benches if entry.get("name") == "audit_bench"]
    assert len(audit_entries) == 1
    assert audit_entries[0].get("harness") is False


def test_workspace_declares_criterion_dependency() -> None:
    workspace_toml = REPO_ROOT / "crates" / "Cargo.toml"
    data = tomllib.loads(workspace_toml.read_text(encoding="utf-8"))
    workspace_deps = data.get("workspace", {}).get("dependencies", {})
    assert "criterion" in workspace_deps


def test_taskfile_bench_rust_audit_is_offline_and_locked() -> None:
    taskfile = (REPO_ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    assert "bench:rust:audit:" in taskfile
    assert "CARGO_NET_OFFLINE=true cargo bench --locked" in taskfile
    assert "-p thegent-router --bench audit_bench" in taskfile


def test_router_readme_documents_offline_benchmark_run() -> None:
    readme = (REPO_ROOT / "crates" / "thegent-router" / "README.md").read_text(encoding="utf-8")
    assert "Deterministic No-Network Verification" in readme
    assert "CARGO_NET_OFFLINE=true cargo bench --locked" in readme
    assert "tests/test_wl079_audit_bench.py" in readme


def test_quality_guide_includes_benchmark_smoke_checklist_entry() -> None:
    quality_guide = (REPO_ROOT / "docs" / "guides" / "QUALITY_ASSURANCE.md").read_text(encoding="utf-8")
    assert "Deterministic benchmark smoke passed (`task bench:smoke:ci`)" in quality_guide
    assert 'CI benchmark smoke step present in PR checks ("Deterministic benchmark smoke")' in quality_guide
    assert "CI benchmark smoke command snippet (WL-079)" in quality_guide
    assert "uv run pytest -q tests/test_wl079_audit_bench.py" in quality_guide
    assert "CARGO_NET_OFFLINE=true cargo bench --locked --manifest-path crates/Cargo.toml" in quality_guide
    assert "wraps CARGO_NET_OFFLINE=true cargo bench --locked -p thegent-router --bench audit_bench" in quality_guide


def test_governance_summary_includes_benchmark_smoke_policy() -> None:
    governance_summary = (REPO_ROOT / "docs" / "governance" / "GOVERNANCE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Deterministic Benchmark Governance (WL-079)" in governance_summary
    assert "task bench:smoke:ci" in governance_summary
    assert "CARGO_NET_OFFLINE=true cargo bench --locked --manifest-path crates/Cargo.toml" in governance_summary
    assert "Deterministic benchmark smoke" in governance_summary


def test_ci_quality_job_runs_benchmark_smoke() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "Deterministic benchmark smoke" in ci_workflow
    assert "task bench:smoke:ci" in ci_workflow


def test_ci_benchmark_smoke_step_uses_task_wrapper_not_inline_cargo() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    step_block = ci_workflow.split("- name: Deterministic benchmark smoke", 1)[1]
    step_block = step_block.split("\n      - name:", 1)[0]
    assert "task bench:smoke:ci" in step_block
    assert "cargo bench" not in step_block


def test_taskfile_bench_smoke_ci_remains_test_wrapper_gate() -> None:
    taskfile = (REPO_ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    smoke_block = taskfile.split("  bench:smoke:ci:", 1)[1].split("\n  bench:", 1)[0]
    assert "uv run pytest -q tests/test_wl079_audit_bench.py" in smoke_block
    assert "cargo bench" not in smoke_block


def test_taskfile_bench_smoke_ci_has_single_wrapper_command() -> None:
    taskfile = (REPO_ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    smoke_block = taskfile.split("  bench:smoke:ci:", 1)[1].split("\n  bench:", 1)[0]
    assert smoke_block.count("uv run pytest -q tests/test_wl079_audit_bench.py") == 1
