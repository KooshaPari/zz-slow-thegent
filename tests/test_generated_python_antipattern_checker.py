from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def test_generated_python_antipattern_checker_fails_on_error(tmp_path: Path) -> None:
    src = tmp_path / "bad.py"
    src.write_text(
        "value = eval('1 + 1')\ntry:\n    pass\nexcept:\n    pass\n",
        encoding="utf-8",
    )
    json_out = tmp_path / "report.json"
    sarif_out = tmp_path / "report.sarif"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_generated_python_antipatterns.py",
            str(src),
            "--json-out",
            str(json_out),
            "--sarif-out",
            str(sarif_out),
            "--fail-on",
            "error",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    report = json.loads(json_out.read_text(encoding="utf-8"))
    ids = {finding["rule_id"] for finding in report["findings"]}
    assert "GENPY001" in ids
    assert "GENPY003" in ids
    sarif = json.loads(sarif_out.read_text(encoding="utf-8"))
    assert sarif["version"] == "2.1.0"


def test_generated_python_antipattern_checker_passes_clean_file(tmp_path: Path) -> None:
    src = tmp_path / "ok.py"
    src.write_text("print('ok')\n", encoding="utf-8")
    json_out = tmp_path / "report.json"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_generated_python_antipatterns.py",
            str(src),
            "--json-out",
            str(json_out),
            "--fail-on",
            "error",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    report = json.loads(json_out.read_text(encoding="utf-8"))
    assert report["summary"]["total_findings"] == 0
