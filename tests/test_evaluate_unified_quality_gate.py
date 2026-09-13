from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def _write_policy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "fail_if_summary_missing": True,
                "modes": {
                    "pr": {
                        "fail_on_overall": ["fail"],
                        "warn_statuses": ["warn", "missing"],
                        "max_warn_components": 99,
                        "allowed_missing_components": ["hooks_sarif"],
                    },
                    "nightly": {
                        "fail_on_overall": ["fail", "warn"],
                        "warn_statuses": ["warn", "missing"],
                        "max_warn_components": 0,
                        "allowed_missing_components": [],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _run(summary: Path, policy: Path, mode: str = "pr", strict: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "scripts/evaluate_unified_quality_gate.py",
        "--summary",
        str(summary),
        "--policy",
        str(policy),
        "--mode",
        mode,
    ]
    if strict:
        cmd.append("--strict")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_gate_fails_on_fail_status(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    policy = tmp_path / "policy.json"
    _write_policy(policy)
    summary.write_text(
        json.dumps({"overall_status": "fail", "components": []}).decode(),
        encoding="utf-8",
    )
    proc = _run(summary, policy=policy, mode="pr")
    assert proc.returncode == 1


def test_gate_warn_policy_differs_between_modes(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    policy = tmp_path / "policy.json"
    _write_policy(policy)
    summary.write_text(
        json.dumps({"overall_status": "warn", "components": [{"name": "a"}]}).decode(),
        encoding="utf-8",
    )
    proc_pr = _run(summary, policy=policy, mode="pr")
    assert proc_pr.returncode == 0
    proc_nightly = _run(summary, policy=policy, mode="nightly")
    assert proc_nightly.returncode == 1


def test_gate_blocks_disallowed_missing_component(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    policy = tmp_path / "policy.json"
    _write_policy(policy)
    summary.write_text(
        json.dumps(
            {
                "overall_status": "ok",
                "components": [
                    {
                        "name": "generated_python_json",
                        "status": "warn",
                        "details": {"reason": "missing"},
                    }
                ],
            }
        ).decode(),
        encoding="utf-8",
    )
    proc = _run(summary, policy=policy, mode="pr")
    assert proc.returncode == 1
