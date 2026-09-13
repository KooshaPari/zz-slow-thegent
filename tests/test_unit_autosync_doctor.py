"""Unit tests for autosync GA doctor checks.

# @trace WL-240
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.commands.doctor import DoctorRunner


@pytest.mark.requirement("WL-240")
def test_autosync_ga_readiness_warns_when_checks_missing(tmp_path):
    runner = DoctorRunner()
    with patch.object(Path, "cwd", return_value=tmp_path):
        check = runner._check_autosync_ga_readiness()
    assert check.status == "warn"
    assert "missing checks" in check.message


@pytest.mark.requirement("WL-240")
def test_autosync_ga_readiness_ok_when_all_checks_present(tmp_path, monkeypatch):
    docs_ref = tmp_path / "docs" / "reference"
    docs_ref.mkdir(parents=True)
    (docs_ref / "AUTOSYNC_GA_READINESS_CRITERIA.md").write_text("ok\n", encoding="utf-8")
    (docs_ref / "autosync_status.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("THGENT_WORKSTREAM_AUTOSYNC_ENABLED", "true")

    runner = DoctorRunner()
    with patch.object(Path, "cwd", return_value=tmp_path):
        check = runner._check_autosync_ga_readiness()
    assert check.status == "ok"


@pytest.mark.requirement("WL-240")
def test_run_checks_includes_autosync_ga_readiness(tmp_path):
    runner = DoctorRunner()
    with (
        patch("pathlib.Path.home", return_value=tmp_path),
        patch("pathlib.Path.cwd", return_value=tmp_path),
    ):
        checks = runner.run_checks()
    assert any(check.name == "autosync_ga_readiness" for check in checks)
