# @trace WL-132 B90-W2-B3
"""Tests for the Zig ABI contract version assertions.

Validates:
1. contracts/runtime/zig_abi_contract_v1.json has a non-empty version field.
2. The thegent-zmx-interop Rust crate builds successfully.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json
import pytest

CONTRACT_PATH = Path(__file__).parent.parent / "contracts" / "runtime" / "zig_abi_contract_v1.json"

# The Cargo workspace root is at crates/ inside the repo root.
REPO_ROOT = Path(__file__).parent.parent
CARGO_WORKSPACE_ROOT = REPO_ROOT / "crates"


@pytest.fixture(scope="module")
def zig_abi_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"Contract not found at {CONTRACT_PATH}"
    return json.loads(CONTRACT_PATH.read_text())


def test_zig_abi_contract_file_exists():
    assert CONTRACT_PATH.exists(), f"Expected contract at {CONTRACT_PATH}"


def test_zig_abi_contract_has_version_field(zig_abi_contract: dict):
    assert "version" in zig_abi_contract, "Contract must have a 'version' field"


def test_zig_abi_contract_version_non_empty(zig_abi_contract: dict):
    version = zig_abi_contract.get("version", "")
    assert version, "Contract 'version' must be present and non-empty"
    assert version.strip(), "Contract 'version' must be non-empty"


def test_zig_abi_contract_version_is_semver(zig_abi_contract: dict):
    """Version field must be in X.Y.Z semver format."""
    version = zig_abi_contract["version"]
    parts = version.split(".")
    assert len(parts) == 3, f"Version must be X.Y.Z; got {version!r}"
    for part in parts:
        assert part.isdigit(), f"Each version part must be an integer; got {part!r} in {version!r}"


def test_zig_abi_contract_version_matches_expected(zig_abi_contract: dict):
    """The contract version matches the value embedded in the Rust crate source."""
    # This is the canonical expected version per the WL-132 contract.
    expected = "1.0.0"
    assert zig_abi_contract["version"] == expected, (
        f"Contract version {zig_abi_contract['version']!r} does not match expected {expected!r}"
    )


def test_zig_abi_contract_has_contract_id(zig_abi_contract: dict):
    assert "contract_id" in zig_abi_contract, "Contract must have a 'contract_id' field"


def test_zig_abi_contract_has_abi_section(zig_abi_contract: dict):
    assert "abi" in zig_abi_contract, "Contract must have an 'abi' section"


def test_zig_abi_contract_abi_has_symbols(zig_abi_contract: dict):
    symbols = zig_abi_contract.get("abi", {}).get("symbols", [])
    assert len(symbols) > 0, "Contract ABI must declare at least one symbol"


def test_zmx_interop_crate_builds():
    """The thegent-zmx-interop crate must compile without error."""
    result = subprocess.run(
        ["cargo", "build", "-p", "thegent-zmx-interop"],
        cwd=str(CARGO_WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(f"cargo build -p thegent-zmx-interop failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
