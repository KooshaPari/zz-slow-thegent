from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _wl138_command() -> list[str]:
    return [
        "cargo",
        "run",
        "-q",
        "--manifest-path",
        "crates/Cargo.toml",
        "-p",
        "thegent-utils",
        "--bin",
        "wl138-decomposition-progress",
        "--",
    ]


def test_wl138_progress_script_emits_json(tmp_path: Path) -> None:
    repo_root = _repo_root()
    output = tmp_path / "progress.json"

    result = subprocess.run(
        [
            *_wl138_command(),
            "--output",
            str(output),
            "--skip-execution-gates",
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["workstream_id"] == "WL-138"
    assert payload["artifact_id"] == "wl138.decomposition_progress.v1"
    assert payload["total_checkpoints"] >= 5
    assert payload["complete_checkpoints"] <= payload["total_checkpoints"]
    assert payload["execution_gates"]["skipped"] is True

    runtime_matrix_checkpoint = next(
        item for item in payload["checkpoints"] if item["checkpoint_id"] == "runtime-matrix-artifacts"
    )
    matrix_paths = [check["path"] for check in runtime_matrix_checkpoint["checks"]]
    assert "contracts/runtime/runtime-modularization-matrix.json" in matrix_paths

    rust_checkpoint = next(item for item in payload["checkpoints"] if item["checkpoint_id"] == "rust-hook-splits")
    assert rust_checkpoint["evaluation"]["total_execution_gates"] >= 1
    assert rust_checkpoint["execution_gates"][0]["status"] == "skipped"


def test_build_progress_fails_checkpoint_when_execution_gate_fails(tmp_path: Path) -> None:
    repo_root = _repo_root()
    single_checkpoint = tmp_path / "checkpoint.json"
    output = tmp_path / "single_checkpoint_result.json"
    python_bin = sys.executable

    single_checkpoint.write_text(
        json.dumps(
            {
                "checkpoint_id": "fake-checkpoint",
                "description": "fake",
                "paths": ["README.md"],
                "execution_gates": [
                    {
                        "gate_id": "failing-gate",
                        "description": "fails",
                        "command": [
                            python_bin,
                            "-c",
                            "raise SystemExit(7).decode()",
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            *_wl138_command(),
            "--checkpoint",
            str(single_checkpoint),
            "--output",
            str(output),
            "--repo-root",
            str(repo_root),
            "--python-bin",
            python_bin,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    result_payload = json.loads(output.read_text(encoding="utf-8"))
    assert result_payload["evaluation"]["paths_complete"] is True
    assert result_payload["evaluation"]["execution_gates_complete"] is False
    assert result_payload["complete"] is False
    assert result_payload["execution_gates"][0]["status"] == "fail"
    assert result_payload["execution_gates"][0]["exit_code"] == 7
