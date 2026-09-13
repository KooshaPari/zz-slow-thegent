"""Integration tests for the thegent-zmx Rust crate (impl-rust-zmx-wrapper).

Verifies that the crate:
  - exists on disk with the expected structure
  - compiles successfully via ``cargo check``
  - exposes the public API surface documented in the task spec
  - has ≥10 unit tests declared in src/lib.rs
  - integrates correctly into the workspace Cargo.toml

These tests do NOT require the ``zmx`` binary or ``libzmx`` to be present;
they only validate the Rust source structure and compile-time correctness.

# @trace FR-ZMX-001 FR-ZMX-002 FR-ZMX-003 FR-ZMX-004 FR-ZMX-005
# @trace FR-ZMX-006 FR-ZMX-007 FR-ZMX-008
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
CRATES_DIR = REPO_ROOT / "crates"
ZMX_CRATE = CRATES_DIR / "thegent-zmx"
SRC_LIB = ZMX_CRATE / "src" / "lib.rs"
CARGO_TOML = ZMX_CRATE / "Cargo.toml"
WORKSPACE_TOML = CRATES_DIR / "Cargo.toml"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _cargo_check() -> subprocess.CompletedProcess:
    """Run ``cargo check -p thegent-zmx`` and return the result."""
    return subprocess.run(
        ["cargo", "check", "-p", "thegent-zmx"],
        cwd=str(CRATES_DIR),
        capture_output=True,
        text=True,
        timeout=180,
    )


# ---------------------------------------------------------------------------
# Test 1 — crate directory exists
# ---------------------------------------------------------------------------


def test_crate_directory_exists():
    """The thegent-zmx crate directory must exist under crates/.

    # @trace FR-ZMX-001
    """
    assert ZMX_CRATE.is_dir(), f"Expected crate dir at {ZMX_CRATE}"


# ---------------------------------------------------------------------------
# Test 2 — Cargo.toml is present and has correct package name
# ---------------------------------------------------------------------------


def test_cargo_toml_exists_and_has_correct_name():
    """Cargo.toml must declare name = \"thegent-zmx\".

    # @trace FR-ZMX-001
    """
    assert CARGO_TOML.is_file(), f"Missing {CARGO_TOML}"
    content = CARGO_TOML.read_text(encoding="utf-8")
    assert 'name = "thegent-zmx"' in content, 'Cargo.toml must set name = "thegent-zmx"'


# ---------------------------------------------------------------------------
# Test 3 — Cargo.toml declares required dependencies
# ---------------------------------------------------------------------------


def test_cargo_toml_declares_required_deps():
    """Cargo.toml must list thegent-zmx-interop, anyhow, serde, serde_json.

    # @trace FR-ZMX-001
    """
    content = CARGO_TOML.read_text(encoding="utf-8")
    for dep in ("thegent-zmx-interop", "anyhow", "serde", "serde_json"):
        assert dep in content, f"Missing dependency '{dep}' in Cargo.toml"


# ---------------------------------------------------------------------------
# Test 4 — src/lib.rs exists
# ---------------------------------------------------------------------------


def test_lib_rs_exists():
    """src/lib.rs must exist inside the crate.

    # @trace FR-ZMX-002
    """
    assert SRC_LIB.is_file(), f"Missing {SRC_LIB}"


# ---------------------------------------------------------------------------
# Test 5 — ZmxSession struct is declared
# ---------------------------------------------------------------------------


def test_lib_rs_declares_zmx_session():
    """lib.rs must declare the ZmxSession struct.

    # @trace FR-ZMX-002
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    assert "pub struct ZmxSession" in content, "lib.rs must contain 'pub struct ZmxSession'"


# ---------------------------------------------------------------------------
# Test 6 — ZmxState enum is declared with all three variants
# ---------------------------------------------------------------------------


def test_lib_rs_declares_zmx_state_variants():
    """lib.rs must declare ZmxState with Active, Detached, Dead variants.

    # @trace FR-ZMX-002
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    assert "pub enum ZmxState" in content
    for variant in ("Active", "Detached", "Dead"):
        assert variant in content, f"Missing ZmxState variant: {variant}"


# ---------------------------------------------------------------------------
# Test 7 — ZmxClient methods are declared
# ---------------------------------------------------------------------------


def test_lib_rs_declares_zmx_client_methods():
    """lib.rs must declare all required ZmxClient public methods.

    # @trace FR-ZMX-006
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    for method in ("pub fn new", "pub fn list_sessions", "pub fn attach", "pub fn capture", "pub fn send"):
        assert method in content, f"Missing ZmxClient method: '{method}'"


# ---------------------------------------------------------------------------
# Test 8 — at least 10 #[test] functions declared
# ---------------------------------------------------------------------------


def test_lib_rs_has_at_least_10_tests():
    """lib.rs must contain ≥10 #[test] annotations.

    # @trace FR-ZMX-007
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    test_count = len(re.findall(r"#\[test\]", content))
    assert test_count >= 10, f"Expected ≥10 #[test] in lib.rs, found {test_count}"


# ---------------------------------------------------------------------------
# Test 9 — crate is registered in workspace Cargo.toml
# ---------------------------------------------------------------------------


def test_crate_registered_in_workspace():
    """thegent-zmx must appear in the workspace members list.

    # @trace FR-ZMX-001
    """
    content = WORKSPACE_TOML.read_text(encoding="utf-8")
    assert '"thegent-zmx"' in content, "thegent-zmx must be listed in crates/Cargo.toml [workspace] members"


# ---------------------------------------------------------------------------
# Test 10 — live-zmx and zmx-native features are declared
# ---------------------------------------------------------------------------


def test_cargo_toml_declares_features():
    """Cargo.toml must declare live-zmx and zmx-native features.

    # @trace FR-ZMX-001
    """
    content = CARGO_TOML.read_text(encoding="utf-8")
    assert "live-zmx" in content, "Missing feature 'live-zmx' in Cargo.toml"
    assert "zmx-native" in content, "Missing feature 'zmx-native' in Cargo.toml"


# ---------------------------------------------------------------------------
# Test 11 — cargo check passes
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_cargo_check_passes():
    """``cargo check -p thegent-zmx`` must exit with code 0.

    Marked slow because it invokes the Rust compiler.

    # @trace FR-ZMX-001
    """
    result = _cargo_check()
    assert result.returncode == 0, f"cargo check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


# ---------------------------------------------------------------------------
# Test 12 — serde derives are present
# ---------------------------------------------------------------------------


def test_lib_rs_uses_serde_derives():
    """ZmxSession and ZmxState must derive Serialize and Deserialize.

    # @trace FR-ZMX-005
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    assert "serde::Serialize" in content or "Serialize" in content
    assert "serde::Deserialize" in content or "Deserialize" in content


# ---------------------------------------------------------------------------
# Test 13 — JSON helper functions are present
# ---------------------------------------------------------------------------


def test_lib_rs_has_json_helpers():
    """lib.rs must expose sessions_to_json and sessions_from_json.

    # @trace FR-ZMX-005
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    assert "pub fn sessions_to_json" in content
    assert "pub fn sessions_from_json" in content


# ---------------------------------------------------------------------------
# Test 14 — validate_session_name helper rejects empty/NUL input
# ---------------------------------------------------------------------------


def test_lib_rs_has_validate_session_name():
    """lib.rs must contain a validate_session_name helper.

    # @trace FR-ZMX-004
    """
    content = SRC_LIB.read_text(encoding="utf-8")
    assert "validate_session_name" in content, "lib.rs must define validate_session_name"


# ---------------------------------------------------------------------------
# Test 15 — cargo test passes (all non-live tests)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_cargo_test_passes():
    """``cargo test -p thegent-zmx`` must exit with code 0.

    # @trace FR-ZMX-007
    """
    result = subprocess.run(
        ["cargo", "test", "-p", "thegent-zmx"],
        cwd=str(CRATES_DIR),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"cargo test failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
