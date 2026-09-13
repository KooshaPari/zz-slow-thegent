"""Tests for governance contract report attestation generation and verification."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_governance_contract_attestation_roundtrip(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"total": 1, "passed": 1, "failed": 0}).decode() + "\n", encoding="utf-8")
    attestation = tmp_path / "attestation.json"

    gen_script = _repo_root() / "scripts" / "attest_governance_contract_report.py"
    verify_script = _repo_root() / "scripts" / "verify_governance_contract_attestation.py"

    gen = subprocess.run(
        [sys.executable, str(gen_script), "--report-json", str(report), "--attestation-out", str(attestation)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert gen.returncode == 0, gen.stderr
    assert attestation.exists()

    ver = subprocess.run(
        [sys.executable, str(verify_script), "--report-json", str(report), "--attestation-json", str(attestation)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ver.returncode == 0, ver.stdout + ver.stderr
    assert "verification passed" in ver.stdout


@pytest.mark.unit
def test_governance_contract_attestation_detects_tampered_report(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"total": 1, "passed": 1, "failed": 0}).decode() + "\n", encoding="utf-8")
    attestation = tmp_path / "attestation.json"

    gen_script = _repo_root() / "scripts" / "attest_governance_contract_report.py"
    verify_script = _repo_root() / "scripts" / "verify_governance_contract_attestation.py"

    subprocess.run(
        [sys.executable, str(gen_script), "--report-json", str(report), "--attestation-out", str(attestation)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=True,
    )

    report.write_text(json.dumps({"total": 1, "passed": 0, "failed": 1}).decode() + "\n", encoding="utf-8")
    ver = subprocess.run(
        [sys.executable, str(verify_script), "--report-json", str(report), "--attestation-json", str(attestation)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ver.returncode != 0
    assert "digest mismatch" in (ver.stdout + ver.stderr)
