from __future__ import annotations

from pathlib import Path

import pytest

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_python_suite.py"
MODULE = _load_script_module("benchmark_python_suite", SCRIPT_PATH)


def test_wl078_main_refuses_overwrite_without_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "baseline.json"
    out.write_text('{"old": true}', encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "benchmark_python_suite.py",
            "--iterations",
            "5",
            "--output",
            str(out),
        ],
    )

    with pytest.raises(FileExistsError, match="Refusing to overwrite existing benchmark output"):
        MODULE.main()


def test_wl078_main_allows_overwrite_with_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "baseline.json"
    out.write_text('{"old": true}', encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "benchmark_python_suite.py",
            "--iterations",
            "5",
            "--output",
            str(out),
            "--overwrite",
        ],
    )

    rc = MODULE.main()
    assert rc == 0
    payload = out.read_text(encoding="utf-8")
    assert '"suite": "python-benchmark-suite-v1"' in payload


# noqa: PT018
