from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path("scripts/mojo_score_rank_harness.py")


def _run_harness(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _write_exec(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_generate_fixtures_is_deterministic(tmp_path: Path) -> None:
    out_a = tmp_path / "fixtures-a"
    out_b = tmp_path / "fixtures-b"
    common_args = [
        "--seed",
        "98765",
        "--small-cases",
        "7",
        "--medium-cases",
        "9",
        "--large-cases",
        "11",
    ]

    first = _run_harness(["generate-fixtures", "--output-root", str(out_a), *common_args])
    second = _run_harness(["generate-fixtures", "--output-root", str(out_b), *common_args])
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    for name in ["small_128.json", "medium_1024.json", "large_8192.json"]:
        assert (out_a / name).read_text(encoding="utf-8") == (out_b / name).read_text(encoding="utf-8")

    fixture = json.loads((out_a / "small_128.json").read_text(encoding="utf-8"))
    assert fixture["dataset_id"] == "small-128"
    assert len(fixture["cases"]) == 7
    assert "input" in fixture["cases"][0]
    assert "expected_output" in fixture["cases"][0]


def test_run_fails_loudly_without_mojo(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures"
    generated = _run_harness(
        [
            "generate-fixtures",
            "--output-root",
            str(fixture_root),
            "--small-cases",
            "2",
            "--medium-cases",
            "2",
            "--large-cases",
            "2",
        ]
    )
    assert generated.returncode == 0, generated.stderr

    result = _run_harness(
        [
            "run",
            "--fixture-root",
            str(fixture_root),
            "--datasets",
            "small-128",
            "--mojo-bin",
            "this-mojo-does-not-exist",
            "--mojo-kernel",
            str(tmp_path / "score_rank.mojo"),
        ]
    )
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Mojo executable not found on PATH" in combined
    assert "Install Mojo" in combined
    assert "python3 scripts/mojo_score_rank_harness.py run --mojo-kernel <path/to/score_rank.mojo>" in combined


def test_run_smoke_with_fake_mojo(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures"
    generated = _run_harness(
        [
            "generate-fixtures",
            "--output-root",
            str(fixture_root),
            "--small-cases",
            "6",
            "--medium-cases",
            "2",
            "--large-cases",
            "2",
        ]
    )
    assert generated.returncode == 0, generated.stderr

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_mojo = fake_bin / "mojo"
    _write_exec(
        fake_mojo,
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
if len(args) < 4 or args[0] != "run" or args[2] != "--input-json":
    raise SystemExit("unexpected args")
payload = json.loads(Path(args[3]).read_text(encoding="utf-8"))
w = payload["weights"]
ranked = []
for cand in payload["candidates"]:
    score = (w["quality"] * cand["quality"]) - (w["cost"] * cand["cost"]) - (w["latency"] * cand["latency"])
    ranked.append({"id": cand["id"], "score": score})
ranked.sort(key=lambda item: (-item["score"], item["id"]))
print(json.dumps({
    "request_id": payload["request_id"],
    "ranked": [{"id": r["id"], "score": r["score"], "rank": idx + 1} for idx, r in enumerate(ranked)],
}))
""",
    )

    kernel_file = tmp_path / "score_rank.mojo"
    kernel_file.write_text("// fake kernel path for harness smoke\n", encoding="utf-8")
    output_path = tmp_path / "result.json"

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    result = _run_harness(
        [
            "run",
            "--fixture-root",
            str(fixture_root),
            "--datasets",
            "small-128",
            "--mojo-kernel",
            str(kernel_file),
            "--output",
            str(output_path),
            "--no-enforce-gates",
        ],
        env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["correctness_failures_total"] == 0
    assert payload["datasets"][0]["dataset_id"] == "small-128"
    assert payload["datasets"][0]["case_count"] == 6
    assert payload["promotion_gate"]["enforced"] is False
    assert isinstance(payload["promotion_gate"]["violations"], list)


def test_run_enforces_promotion_gate_by_default(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures"
    generated = _run_harness(
        [
            "generate-fixtures",
            "--output-root",
            str(fixture_root),
            "--small-cases",
            "6",
            "--medium-cases",
            "2",
            "--large-cases",
            "2",
        ]
    )
    assert generated.returncode == 0, generated.stderr

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_mojo = fake_bin / "mojo"
    _write_exec(
        fake_mojo,
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
if len(args) < 4 or args[0] != "run" or args[2] != "--input-json":
    raise SystemExit("unexpected args")
payload = json.loads(Path(args[3]).read_text(encoding="utf-8"))
w = payload["weights"]
ranked = []
for cand in payload["candidates"]:
    score = (w["quality"] * cand["quality"]) - (w["cost"] * cand["cost"]) - (w["latency"] * cand["latency"])
    ranked.append({"id": cand["id"], "score": score})
ranked.sort(key=lambda item: (-item["score"], item["id"]))
print(json.dumps({
    "request_id": payload["request_id"],
    "ranked": [{"id": r["id"], "score": r["score"], "rank": idx + 1} for idx, r in enumerate(ranked)],
}))
""",
    )

    kernel_file = tmp_path / "score_rank.mojo"
    kernel_file.write_text("// fake kernel path for harness smoke\n", encoding="utf-8")
    output_path = tmp_path / "result_enforced.json"

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    result = _run_harness(
        [
            "run",
            "--fixture-root",
            str(fixture_root),
            "--datasets",
            "small-128",
            "--mojo-kernel",
            str(kernel_file),
            "--output",
            str(output_path),
        ],
        env=env,
    )
    assert result.returncode != 0
    assert "Mojo promotion gate failed" in f"{result.stdout}\n{result.stderr}"

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["correctness_failures_total"] == 0
    assert payload["promotion_gate"]["enforced"] is True
    assert len(payload["promotion_gate"]["violations"]) >= 1
