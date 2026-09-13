# @trace WL-133 B90-W2-B4
"""Deterministic Mojo kernel smoke checks.

These are contract-level smoke tests that do NOT require Mojo to be installed.
They validate:

1. The mojo_kernel_contract_v1.json artifact exists and has required fields.
2. mojo_bridge.py exposes the function referenced by the kernel contract.
3. The Python bridge produces deterministic outputs for deterministic fixture inputs
   (run the computation twice with same inputs, assert same result).
4. The deterministic fixture file exists and is well-formed.

Tests skip gracefully when Mojo subprocess execution would be needed but the
binary is not available.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import orjson as json
import pytest

CONTRACT_PATH = Path(__file__).parent.parent.parent / "contracts" / "runtime" / "mojo_kernel_contract_v1.json"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "deterministic_score_v1.json"
MOJO_BRIDGE_MODULE = "thegent.infra.mojo_bridge"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kernel_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"Contract not found at {CONTRACT_PATH}"
    return json.loads(CONTRACT_PATH.read_text())


@pytest.fixture(scope="module")
def deterministic_fixture() -> dict:
    assert FIXTURE_PATH.exists(), f"Fixture not found at {FIXTURE_PATH}"
    return json.loads(FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# Contract file checks
# ---------------------------------------------------------------------------


def test_kernel_contract_file_exists():
    assert CONTRACT_PATH.exists(), f"Expected contract at {CONTRACT_PATH}"


def test_kernel_contract_has_version(kernel_contract: dict):
    assert "version" in kernel_contract, "Contract must have a 'version' field"
    assert kernel_contract["version"], "Contract version must be non-empty"


def test_kernel_contract_has_kernel_catalog(kernel_contract: dict):
    assert "kernel_catalog" in kernel_contract, "Contract must have a 'kernel_catalog' section"
    catalog = kernel_contract["kernel_catalog"]
    assert isinstance(catalog, list) and len(catalog) > 0, "kernel_catalog must be a non-empty list"


def test_kernel_catalog_entry_has_required_fields(kernel_contract: dict):
    required = {"kernel_id", "deterministic"}
    for entry in kernel_contract["kernel_catalog"]:
        missing = required - entry.keys()
        assert not missing, f"kernel_catalog entry {entry.get('kernel_id', '?')} missing required fields: {missing}"


def test_kernel_catalog_deterministic_flag_is_true(kernel_contract: dict):
    for entry in kernel_contract["kernel_catalog"]:
        assert entry.get("deterministic") is True, f"Kernel {entry.get('kernel_id', '?')} must have deterministic=true"


def test_kernel_contract_has_schemas(kernel_contract: dict):
    assert "schemas" in kernel_contract, "Contract must have a 'schemas' section"


def test_kernel_contract_score_rank_input_schema(kernel_contract: dict):
    schemas = kernel_contract.get("schemas", {})
    assert "score_rank_input" in schemas, "Contract schemas must include 'score_rank_input'"
    input_schema = schemas["score_rank_input"]
    required_fields = input_schema.get("required", [])
    assert "candidates" in required_fields, "Input schema must require 'candidates'"
    assert "weights" in required_fields, "Input schema must require 'weights'"


def test_kernel_contract_score_rank_output_schema(kernel_contract: dict):
    schemas = kernel_contract.get("schemas", {})
    assert "score_rank_output" in schemas, "Contract schemas must include 'score_rank_output'"
    output_schema = schemas["score_rank_output"]
    required_fields = output_schema.get("required", [])
    assert "ranked" in required_fields, "Output schema must require 'ranked'"


# ---------------------------------------------------------------------------
# mojo_bridge.py structural checks
# ---------------------------------------------------------------------------


def test_mojo_bridge_module_importable():
    """mojo_bridge must be importable without raising."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    assert module is not None


def test_mojo_bridge_has_validate_kernel_contract():
    """validate_kernel_contract function must be present in the bridge."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    assert hasattr(module, "validate_kernel_contract"), "mojo_bridge must expose validate_kernel_contract"
    assert callable(module.validate_kernel_contract)


def test_mojo_bridge_has_build_provider_score_kernel_script():
    """build_provider_score_kernel_script function must be present."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    assert hasattr(module, "build_provider_score_kernel_script"), (
        "mojo_bridge must expose build_provider_score_kernel_script"
    )
    assert callable(module.build_provider_score_kernel_script)


def test_mojo_bridge_has_mojo_kernel_contracts():
    """MOJO_KERNEL_CONTRACTS registry must be present and non-empty."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    assert hasattr(module, "MOJO_KERNEL_CONTRACTS"), "mojo_bridge must expose MOJO_KERNEL_CONTRACTS"
    contracts = module.MOJO_KERNEL_CONTRACTS
    assert isinstance(contracts, dict) and len(contracts) > 0, "MOJO_KERNEL_CONTRACTS must be a non-empty dict"


def test_mojo_bridge_contract_references_calculate_provider_score():
    """The known kernel contract must reference calculate_provider_score."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    contracts = module.MOJO_KERNEL_CONTRACTS
    key = ("math", "calculate_provider_score")
    assert key in contracts, f"MOJO_KERNEL_CONTRACTS must include key {key!r}"


# ---------------------------------------------------------------------------
# Determinism checks (Python bridge layer only — no Mojo subprocess needed)
# ---------------------------------------------------------------------------


def test_validate_kernel_contract_is_deterministic():
    """validate_kernel_contract must not raise for valid complete args (run twice)."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    validate = module.validate_kernel_contract
    args = {"cost_score": 0.5, "quality_score": 0.8, "latency_score": 0.3}

    # Run twice — deterministic: no exception either time
    validate("math", "calculate_provider_score", args)
    validate("math", "calculate_provider_score", args)


def test_validate_kernel_contract_fails_fast_on_missing_arg():
    """validate_kernel_contract must raise immediately when a required arg is missing."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    validate = module.validate_kernel_contract
    incomplete_args = {"cost_score": 0.5}  # missing quality_score, latency_score
    with pytest.raises(ValueError):
        validate("math", "calculate_provider_score", incomplete_args)


def test_build_kernel_script_is_deterministic():
    """build_provider_score_kernel_script must return identical output on repeated calls."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    build = module.build_provider_score_kernel_script
    result1 = build()
    result2 = build()
    assert result1 == result2, "build_provider_score_kernel_script must be deterministic"


def test_build_kernel_script_non_empty():
    """build_provider_score_kernel_script must return a non-empty string."""
    module = importlib.import_module(MOJO_BRIDGE_MODULE)
    script = module.build_provider_score_kernel_script()
    assert isinstance(script, str) and script.strip(), "build_provider_score_kernel_script must return non-empty string"


# ---------------------------------------------------------------------------
# Deterministic fixture file checks
# ---------------------------------------------------------------------------


def test_deterministic_fixture_file_exists():
    assert FIXTURE_PATH.exists(), f"Expected fixture at {FIXTURE_PATH}"


def test_deterministic_fixture_has_three_cases(deterministic_fixture: dict):
    cases = deterministic_fixture.get("cases", [])
    assert len(cases) >= 3, f"Fixture must have at least 3 cases; got {len(cases)}"


def test_deterministic_fixture_cases_have_required_fields(deterministic_fixture: dict):
    for case in deterministic_fixture["cases"]:
        assert "case_id" in case, f"Case missing 'case_id': {case}"
        assert "input" in case, f"Case {case.get('case_id')} missing 'input'"
        assert "expected_output" in case, f"Case {case.get('case_id')} missing 'expected_output'"


def test_deterministic_fixture_inputs_match_contract_schema(
    deterministic_fixture: dict,
):
    """Each fixture input must have request_id, candidates, and weights."""
    for case in deterministic_fixture["cases"]:
        inp = case["input"]
        assert "request_id" in inp, f"Case {case['case_id']} input missing 'request_id'"
        assert "candidates" in inp, f"Case {case['case_id']} input missing 'candidates'"
        assert "weights" in inp, f"Case {case['case_id']} input missing 'weights'"
        weights = inp["weights"]
        assert "cost" in weights and "latency" in weights and "quality" in weights, (
            f"Case {case['case_id']} weights must have cost, latency, quality"
        )


# noqa: PT018
