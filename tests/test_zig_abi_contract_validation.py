"""Tests for Zig ABI contract validation scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest

# @trace FR-RUNTIME-001


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _valid_contract_payload() -> dict[str, object]:
    return {
        "contract_id": "runtime.zig_abi.v1",
        "version": "1.0.0",
        "abi": {
            "calling_convention": "C",
            "symbols": [
                {
                    "name": "tg_zig_kernel_version",
                    "kind": "function",
                    "signature": "const char* tg_zig_kernel_version(void)",
                    "stability": "required",
                },
                {
                    "name": "tg_zig_init",
                    "kind": "function",
                    "signature": "int32_t tg_zig_init(const char* config_json, char** err_json_out)",
                    "stability": "required",
                },
            ],
        },
        "wire_protocol": {
            "request_encoding": "utf-8-json",
            "response_encoding": "utf-8-json",
        },
        "error_contract": {
            "error_envelope": {
                "required_fields": ["code", "message", "stage"],
                "optional_fields": ["details"],
            },
            "codes": ["ZIG_BAD_REQUEST"],
        },
        "validation": {
            "required_tests": [
                "abi_symbol_presence",
                "ffi_roundtrip_smoke",
                "error_envelope_conformance",
                "memory_free_safety",
                "wasm_target_build",
            ],
        },
    }


@pytest.mark.unit
def test_validate_zig_abi_contract_passes_repo_contract() -> None:
    script = _repo_root() / "scripts" / "validate_zig_abi_contract.py"
    contract = _repo_root() / "contracts" / "runtime" / "zig_abi_contract_v1.json"

    result = subprocess.run(
        [sys.executable, str(script), "--contract", str(contract)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation passed" in result.stdout


@pytest.mark.unit
def test_validate_zig_abi_contract_fails_on_missing_required_field(tmp_path: Path) -> None:
    script = _repo_root() / "scripts" / "validate_zig_abi_contract.py"
    bad_contract = tmp_path / "zig_abi_contract_invalid.json"

    bad_contract.write_text(
        json.dumps(
            {
                **_valid_contract_payload(),
                "error_contract": {
                    "error_envelope": {
                        "required_fields": ["code", "message"],
                        "optional_fields": ["details"],
                    },
                    "codes": ["ZIG_BAD_REQUEST"],
                },
            }
        ).decode("utf-8"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(script), "--contract", str(bad_contract)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "required_fields missing required keys" in (result.stdout + result.stderr)


@pytest.mark.unit
def test_validate_zig_abi_contract_fails_on_missing_readiness_gates(tmp_path: Path) -> None:
    script = _repo_root() / "scripts" / "validate_zig_abi_contract.py"
    bad_contract = tmp_path / "zig_abi_contract_missing_readiness.json"
    contract_payload = _valid_contract_payload()
    contract_payload["validation"] = {"required_tests": ["abi_symbol_presence"]}
    bad_contract.write_text(json.dumps(contract_payload).decode("utf-8"), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--contract", str(bad_contract)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "missing readiness gates" in (result.stdout + result.stderr)


@pytest.mark.unit
def test_validate_zig_abi_contract_fails_on_duplicate_required_tests(tmp_path: Path) -> None:
    script = _repo_root() / "scripts" / "validate_zig_abi_contract.py"
    bad_contract = tmp_path / "zig_abi_contract_duplicate_tests.json"
    contract_payload = _valid_contract_payload()
    contract_payload["validation"] = {
        "required_tests": [
            "abi_symbol_presence",
            "ffi_roundtrip_smoke",
            "error_envelope_conformance",
            "memory_free_safety",
            "wasm_target_build",
            "wasm_target_build",
        ]
    }
    bad_contract.write_text(json.dumps(contract_payload).decode("utf-8"), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--contract", str(bad_contract)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "must not contain duplicates" in (result.stdout + result.stderr)


@pytest.mark.unit
def test_check_zig_abi_artifact_detects_missing_required_symbols(tmp_path: Path) -> None:
    script = _repo_root() / "scripts" / "check_zig_abi_artifact.py"
    contract = _repo_root() / "contracts" / "runtime" / "zig_abi_contract_v1.json"
    symbols_fixture = tmp_path / "symbols.txt"
    symbols_fixture.write_text("tg_zig_init\ntg_zig_execute\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--contract",
            str(contract),
            "--symbols-file",
            str(symbols_fixture),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 4
    assert "missing required symbols" in (result.stdout + result.stderr)


@pytest.mark.unit
def test_check_zig_abi_artifact_passes_with_symbols_and_error_envelope(tmp_path: Path) -> None:
    script = _repo_root() / "scripts" / "check_zig_abi_artifact.py"
    contract = _repo_root() / "contracts" / "runtime" / "zig_abi_contract_v1.json"

    symbols_fixture = tmp_path / "symbols.txt"
    symbols_fixture.write_text(
        "\n".join(
            [
                "tg_zig_kernel_version",
                "tg_zig_init",
                "tg_zig_execute",
                "tg_zig_free",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    envelope_fixture = tmp_path / "error.json"
    envelope_fixture.write_text(
        json.dumps(
            {
                "code": "ZIG_BAD_REQUEST",
                "message": "invalid request",
                "stage": "execute",
                "details": {"field": "input"},
            }
        ).decode("utf-8"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--contract",
            str(contract),
            "--symbols-file",
            str(symbols_fixture),
            "--error-envelope-json",
            str(envelope_fixture),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "contract checks passed" in result.stdout
