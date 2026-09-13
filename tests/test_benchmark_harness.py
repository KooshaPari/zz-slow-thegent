from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import orjson as json

HARNESS_PATH = Path("scripts/benchmark-comprehensive.sh")


def _write_exec(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_harness_writes_report_summary_and_manifest(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()

    _write_exec(
        fake_bin / "hyperfine",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "out=''\n"
        'args=("$@")\n'
        "for ((i=0; i<${#args[@]}; i++)); do\n"
        "  if [[ \"${args[$i]}\" == '--export-json' ]]; then\n"
        '    out="${args[$((i+1))]}"\n'
        "  fi\n"
        "done\n"
        'if [[ -z "$out" ]]; then\n'
        "  echo 'missing --export-json' >&2\n"
        "  exit 1\n"
        "fi\n"
        'mkdir -p "$(dirname "$out")"\n'
        "cat > \"$out\" <<'JSON'\n"
        '{"results":[{"command":"fake","mean":0.01,"stddev":0.001,"min":0.009,"max":0.012,"times":[0.01]}]}\n'
        "JSON\n",
    )

    _write_exec(fake_bin / "thegent-tool-detect", "#!/usr/bin/env bash\necho '{}'\n")
    _write_exec(fake_bin / "thegent-path-resolve", "#!/usr/bin/env bash\necho '/usr/bin/codex'\n")

    result_root = tmp_path / "results"
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["THEGENT_BENCH_RESULTS_DIR"] = str(result_root)
    env["BENCH_RUN_ID"] = "test-run"

    subprocess.run([str(HARNESS_PATH)], check=True, env=env, capture_output=True, text=True)

    run_dir = result_root / "test-run"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "summary.json").exists()

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "test-run"
    assert manifest["warmup_runs"] == 3
    assert manifest["measure_runs"] == 20

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "Rust Hook Benchmark Comparison" in report
    assert "tool_detection" in report

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert any(item["scenario"] == "tool_detection" for item in summary["scenarios"])
