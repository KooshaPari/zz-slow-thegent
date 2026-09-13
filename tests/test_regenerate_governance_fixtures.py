"""Tests for deterministic governance fixture regeneration tooling."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _fixture_root() -> Path:
    return _repo_root() / "tests" / "fixtures" / "governance"


@pytest.mark.unit
def test_regenerate_governance_fixtures_check_passes_on_canonical_tree() -> None:
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


@pytest.mark.unit
def test_regenerate_governance_fixtures_requires_bump_when_manifest_drifted(tmp_path: Path) -> None:
    src = _fixture_root()
    dst = tmp_path / "governance"
    shutil.copytree(src, dst)

    manifest_path = dst / "spiral_trend_replay_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["cases"] = list(reversed(manifest["cases"]))
    manifest_path.write_text(json.dumps(manifest, indent=2).decode() + "\n", encoding="utf-8")

    script = _repo_root() / "scripts" / "regenerate_governance_fixtures.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--root", str(dst), "--check"],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "bump-version" in (proc.stdout + proc.stderr)
