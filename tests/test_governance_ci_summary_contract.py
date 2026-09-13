"""Contract tests for governance selector CI summary wiring."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ci_workflow() -> dict:
    workflow = _repo_root() / ".github/workflows/ci.yml"
    return yaml.safe_load(workflow.read_text(encoding="utf-8"))


def _job_steps(job_name: str) -> list[dict]:
    jobs = _ci_workflow().get("jobs", {})
    assert job_name in jobs, f"missing workflow job: {job_name}"
    return jobs[job_name].get("steps", [])


def _find_step_by_name(steps: list[dict], expected_name: str) -> dict:
    for step in steps:
        if step.get("name") == expected_name:
            return step
    pytest.fail(f"missing step: {expected_name}")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("job_name", "log_path", "title", "summary_step_name"),
    [
        (
            "governance-selector-fast",
            ".quality/governance-selector-fast.log",
            "Governance Selector Fast Summary",
            "Summarize selector fast governance signals",
        ),
        (
            "governance-selector-strict",
            ".quality/governance-selector-strict.log",
            "Governance Selector Strict Summary",
            "Summarize selector strict governance signals",
        ),
    ],
)
def test_governance_selector_jobs_use_summary_script_contract(
    job_name: str, log_path: str, title: str, summary_step_name: str
) -> None:
    steps = _job_steps(job_name)
    step = _find_step_by_name(steps, summary_step_name)
    run = step.get("run", "")

    assert "uv run python scripts/governance_alert_summary.py" in run
    assert f"--log {log_path}" in run
    assert f'--title "{title}"' in run
    assert '>> "$GITHUB_STEP_SUMMARY"' in run


@pytest.mark.unit
@pytest.mark.parametrize(
    ("job_name", "run_step_name", "log_path"),
    [
        (
            "governance-selector-fast",
            "Run selector fast lane with fail-closed reporting",
            ".quality/governance-selector-fast.log",
        ),
        (
            "governance-selector-strict",
            "Run selector strict lane with fail-closed reporting",
            ".quality/governance-selector-strict.log",
        ),
    ],
)
def test_governance_selector_jobs_keep_fail_closed_signal_grep_contract(
    job_name: str, run_step_name: str, log_path: str
) -> None:
    steps = _job_steps(job_name)
    step = _find_step_by_name(steps, run_step_name)
    run = step.get("run", "")

    assert f"tee {log_path}" in run
    assert "grep -E" in run
    assert "fail-closed|GOVERNANCE-GATES FAIL|policy_band=red|critical_interrupt" in run


@pytest.mark.unit
def test_governance_alert_summary_script_renders_markdown_contract(tmp_path: Path) -> None:
    log_file = tmp_path / "selector.log"
    log_file.write_text(
        "\n".join(
            [
                "noise",
                "GOVERNANCE-GATES ALERT [critical]: regression-spiral-guard policy_band=red escalation_stage=red_hard_interrupt remediation_directive=interrupt_red",
                "GOVERNANCE-GATES FAIL: [regression-spiral-guard]: policy_band=red pressure_score=0.95",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    script = _repo_root() / "scripts/governance_alert_summary.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--log", str(log_file), "--title", "Governance Summary Contract"],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "### Governance Summary Contract" in proc.stdout
    assert "| Field | Value |" in proc.stdout
    assert "| policy_band | red |" in proc.stdout
    assert "Governance fail-closed signals detected." in proc.stdout
    assert "GOVERNANCE-GATES FAIL" in proc.stdout
