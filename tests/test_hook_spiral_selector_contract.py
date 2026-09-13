"""Contract tests for hook-dispatcher governance spiral-selector JSON output."""

from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _dispatcher_bin() -> Path:
    return _repo_root() / "hooks" / "hook-dispatcher" / "target" / "debug" / "hook-dispatcher"


def _run_selector_json(selector_input: str) -> dict:
    dispatcher = _dispatcher_bin()
    assert dispatcher.exists(), f"Missing dispatcher binary: {dispatcher}"
    proc = subprocess.run(
        [str(dispatcher), "governance", "spiral-selector", "--format", "json", selector_input],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _run_selector_raw(args: list[str]) -> subprocess.CompletedProcess[str]:
    dispatcher = _dispatcher_bin()
    assert dispatcher.exists(), f"Missing dispatcher binary: {dispatcher}"
    return subprocess.run(
        [str(dispatcher), "governance", "spiral-selector", *args],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.unit
def test_spiral_selector_json_contract_keys_and_types() -> None:
    payload = _run_selector_json(" regression_spiral_guard , reliability , regression_spiral_guard ")
    assert set(payload.keys()) == {"raw", "cleaned_raw", "canonical", "selected_mode"}
    assert isinstance(payload["raw"], str)
    assert isinstance(payload["cleaned_raw"], str)
    assert isinstance(payload["canonical"], str)
    assert isinstance(payload["selected_mode"], bool)
    assert payload["canonical"] == "regression_spiral_guard,reliability"


@pytest.mark.unit
def test_spiral_selector_json_snapshot_contract() -> None:
    fixture = _repo_root() / "tests" / "fixtures" / "governance" / "spiral_selector_contract_snapshot.json"
    snapshot = json.loads(fixture.read_text(encoding="utf-8"))
    assert snapshot["schema_version"] >= 1
    assert snapshot["changelog"], "selector snapshot changelog is required"
    for case in snapshot["cases"]:
        got = _run_selector_json(case["input"])
        assert got == case["expected"], (
            "selector JSON contract drift detected. "
            "If intentional, bump schema_version and append changelog entry in "
            "tests/fixtures/governance/spiral_selector_contract_snapshot.json."
        )


@pytest.mark.unit
def test_spiral_selector_rejects_unknown_flag() -> None:
    proc = _run_selector_raw(["--unknown"])
    assert proc.returncode != 0
    assert "unknown flag" in proc.stderr


@pytest.mark.unit
def test_spiral_selector_rejects_missing_format_value() -> None:
    proc = _run_selector_raw(["--format"])
    assert proc.returncode != 0
    assert "--format requires a value" in proc.stderr


@pytest.mark.unit
def test_spiral_selector_rejects_invalid_format_value() -> None:
    proc = _run_selector_raw(["--format", "yaml", "reliability"])
    assert proc.returncode != 0
    assert "invalid --format value" in proc.stderr


@pytest.mark.unit
def test_spiral_selector_rejects_too_many_positionals() -> None:
    proc = _run_selector_raw(["one", "two"])
    assert proc.returncode != 0
    assert "too many positional arguments" in proc.stderr


@pytest.mark.unit
def test_spiral_selector_rejects_control_characters() -> None:
    proc = _run_selector_raw(["reliability\tregression_spiral_guard"])
    assert proc.returncode != 0
    assert "control characters are not allowed" in proc.stderr
