from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def test_mutation_perf_pilot_emits_artifact(tmp_path: Path) -> None:
    output = tmp_path / "pilot.json"
    perf_output = tmp_path / "perf.json"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/mutation_perf_pilot.py",
            "--output",
            str(output),
            "--perf-output",
            str(perf_output),
            "--perf-iterations",
            "20",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "mutation-perf-pilot/v1"
    assert isinstance(payload["phases"], list)
    assert any(phase["name"] == "perf_smoke" for phase in payload["phases"])
