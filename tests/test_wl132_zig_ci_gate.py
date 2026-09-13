# @trace WL-132 B90-W2-D4
"""Tests for the WL-132 B90-W2-D4 Zig ABI readiness CI gate.

Verifies that .github/workflows/ci.yml contains the zig-readiness job
and the required thegent-zmx-interop references.
"""

from __future__ import annotations

from pathlib import Path

import pytest

CI_YML_PATH = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"


def _read_ci_yml() -> str:
    """Read the CI YAML file, skipping if not present."""
    if not CI_YML_PATH.exists():
        pytest.skip(f"ci.yml not found at {CI_YML_PATH}")
    return CI_YML_PATH.read_text()


# ---------------------------------------------------------------------------
# D4-1: zig-readiness job exists in ci.yml
# ---------------------------------------------------------------------------


def test_ci_yml_contains_zig_readiness_job() -> None:
    """ci.yml must define the zig-readiness job."""
    text = _read_ci_yml()
    assert "zig-readiness:" in text, "ci.yml missing 'zig-readiness:' job block (WL-132 B90-W2-D4)"


def test_ci_yml_zig_job_references_zmx_interop() -> None:
    """zig-readiness job must reference thegent-zmx-interop."""
    text = _read_ci_yml()
    assert "thegent-zmx-interop" in text, "ci.yml zig-readiness job must reference 'thegent-zmx-interop'"


def test_ci_yml_zig_job_is_blocking_required_gate() -> None:
    """zig-readiness job must be blocking after promotion to required gate."""
    text = _read_ci_yml()
    assert "continue-on-error: true" not in text, "zig-readiness must not be non-blocking"


def test_ci_yml_zig_job_has_wl132_comment() -> None:
    """ci.yml must include WL-132 trace comment for the zig-readiness job."""
    text = _read_ci_yml()
    assert "WL-132" in text, "ci.yml must include WL-132 reference comment in zig-readiness job"


# ---------------------------------------------------------------------------
# D4-2: cargo build and cargo test commands are present
# ---------------------------------------------------------------------------


def test_ci_yml_zig_job_has_cargo_build() -> None:
    """zig-readiness job must include a cargo build step for zmx-interop."""
    text = _read_ci_yml()
    assert "cargo build --locked -p thegent-zmx-interop" in text, (
        "zig-readiness job must run 'cargo build --locked -p thegent-zmx-interop'"
    )


def test_ci_yml_zig_job_has_cargo_test() -> None:
    """zig-readiness job must include a cargo test step for zmx-interop."""
    text = _read_ci_yml()
    assert "cargo test --locked -p thegent-zmx-interop" in text, (
        "zig-readiness job must run 'cargo test --locked -p thegent-zmx-interop'"
    )


def test_ci_yml_zig_job_has_explicit_criteria_step() -> None:
    """zig-readiness job must verify explicit criteria inputs before build/test."""
    text = _read_ci_yml()
    assert "Verify Zig gate criteria inputs" in text
    assert 'name = "thegent-zmx-interop"' in text


# ---------------------------------------------------------------------------
# D4-3: Rust toolchain is set up in zig-readiness job
# ---------------------------------------------------------------------------


def test_ci_yml_zig_job_installs_rust() -> None:
    """zig-readiness job must set up a Rust toolchain."""
    text = _read_ci_yml()
    assert "dtolnay/rust-toolchain" in text, "zig-readiness job must use dtolnay/rust-toolchain to set up Rust"


# ---------------------------------------------------------------------------
# D4-4: ci.yml is valid YAML
# ---------------------------------------------------------------------------


def test_ci_yml_is_valid_yaml() -> None:
    """ci.yml must parse as valid YAML."""
    try:
        import yaml
    except ImportError:
        pytest.skip("pyyaml not installed; skipping YAML validation")

    text = _read_ci_yml()
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict), "ci.yml must parse to a dict"
    assert "jobs" in parsed, "ci.yml must have a 'jobs' key"
    assert "zig-readiness" in parsed["jobs"], "ci.yml jobs must include 'zig-readiness'"
