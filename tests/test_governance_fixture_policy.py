"""Policy tests for governance fixture versioning and signed digests."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _validate_schema_changelog_contract(doc: dict, label: str) -> None:
    schema_version = doc.get("schema_version")
    changelog = doc.get("changelog")
    assert isinstance(schema_version, int) and schema_version >= 1, f"{label}: invalid schema_version"
    assert isinstance(changelog, list) and changelog, f"{label}: changelog is required"

    versions = [entry.get("version") for entry in changelog]
    assert all(isinstance(v, int) and v >= 1 for v in versions), f"{label}: changelog versions must be positive ints"
    assert versions == sorted(versions), f"{label}: changelog versions must be monotonic non-decreasing"
    assert len(set(versions)) == len(versions), f"{label}: changelog versions must be unique"
    assert versions[-1] == schema_version, (
        f"{label}: latest changelog version ({versions[-1]}) must equal schema_version ({schema_version})"
    )

    for entry in changelog:
        assert isinstance(entry.get("note"), str) and entry["note"].strip(), f"{label}: changelog note is required"
        date = entry.get("date")
        assert isinstance(date, str) and _DATE_RE.match(date), f"{label}: changelog date must be YYYY-MM-DD"


@pytest.mark.unit
def test_governance_fixtures_require_versioned_changelog() -> None:
    root = _repo_root() / "tests" / "fixtures" / "governance"
    for file_name in (
        "spiral_selector_contract_snapshot.json",
        "spiral_trend_replay_manifest.json",
        "fixture_digests.json",
    ):
        doc = json.loads((root / file_name).read_text(encoding="utf-8"))
        _validate_schema_changelog_contract(doc, file_name)


@pytest.mark.unit
def test_governance_fixture_signed_digests_verify() -> None:
    script = _repo_root() / "scripts" / "verify_governance_fixture_digests.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "verification passed" in proc.stdout


@pytest.mark.unit
def test_governance_fixture_regeneration_check_passes() -> None:
    script = _repo_root() / "scripts" / "regenerate_governance_fixtures.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "canonical" in proc.stdout


# noqa: PT018
