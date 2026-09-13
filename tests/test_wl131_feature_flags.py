# @trace WL-131 B90-W3-D2
"""Tests for the Rust feature flags contract file.

B90-W3-D2: Finalize Rust-backed feature flag defaults.
"""

from __future__ import annotations

from pathlib import Path

import orjson as json

REPO_ROOT = Path(__file__).parent.parent

FLAGS_PATH = REPO_ROOT / "contracts" / "runtime" / "rust-feature-flags.json"

REQUIRED_FLAG_FIELDS = {"name", "crate", "value", "promotion_gate"}


def test_rust_feature_flags_file_exists() -> None:
    """contracts/runtime/rust-feature-flags.json must exist."""
    assert FLAGS_PATH.exists(), f"Feature flags file not found at {FLAGS_PATH}"


def test_rust_feature_flags_is_valid_json() -> None:
    """The feature flags file must be valid JSON."""
    content = FLAGS_PATH.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict), "Feature flags file must be a JSON object"


def test_rust_feature_flags_has_flags_array() -> None:
    """Feature flags file must have a 'flags' array with at least 2 entries."""
    data = json.loads(FLAGS_PATH.read_text())
    assert "flags" in data, "Feature flags file must have a 'flags' key"
    flags = data["flags"]
    assert isinstance(flags, list), "'flags' must be an array"
    assert len(flags) >= 2, f"'flags' must have at least 2 entries; got {len(flags)}"


def test_rust_feature_flags_has_schema_version() -> None:
    """Feature flags file must declare a schema_version."""
    data = json.loads(FLAGS_PATH.read_text())
    assert "schema_version" in data, "Feature flags file must have 'schema_version'"
    assert data["schema_version"], "'schema_version' must be non-empty"


def test_each_flag_has_required_fields() -> None:
    """Each flag entry must have name, crate, value, and promotion_gate."""
    data = json.loads(FLAGS_PATH.read_text())
    for flag in data["flags"]:
        missing = REQUIRED_FLAG_FIELDS - flag.keys()
        assert not missing, f"Flag '{flag.get('name', '?')}' is missing required fields: {missing}"


def test_zmx_abi_contract_version_flag_present() -> None:
    """zmx_abi_contract_version flag must be present."""
    data = json.loads(FLAGS_PATH.read_text())
    names = {f["name"] for f in data["flags"]}
    assert "zmx_abi_contract_version" in names, "zmx_abi_contract_version flag must be present in feature flags"


def test_parse_model_suffixes_flag_present() -> None:
    """parse_model_suffixes_enabled flag must be present."""
    data = json.loads(FLAGS_PATH.read_text())
    names = {f["name"] for f in data["flags"]}
    assert "parse_model_suffixes_enabled" in names, "parse_model_suffixes_enabled flag must be present in feature flags"


def test_each_flag_crate_is_non_empty_string() -> None:
    """Each flag must reference a non-empty crate name."""
    data = json.loads(FLAGS_PATH.read_text())
    for flag in data["flags"]:
        assert isinstance(flag.get("crate"), str) and flag["crate"].strip(), (
            f"Flag '{flag.get('name', '?')}' must have a non-empty 'crate' string"
        )


def test_each_flag_promotion_gate_references_test_file() -> None:
    """Each flag's promotion_gate must reference a test file path."""
    data = json.loads(FLAGS_PATH.read_text())
    for flag in data["flags"]:
        gate = flag.get("promotion_gate", "")
        assert "test" in gate.lower() or "tests" in gate.lower(), (
            f"Flag '{flag.get('name', '?')}' promotion_gate '{gate}' should reference a test file"
        )


# noqa: PT018
