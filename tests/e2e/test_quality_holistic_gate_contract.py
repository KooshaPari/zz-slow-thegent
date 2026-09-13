"""Contract checks for holistic quality gates (security/perf/chaos/a11y)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKFILE = ROOT / "Taskfile.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_taskfile_declares_holistic_quality_tasks() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    for token in (
        "quality:security:sast:",
        "quality:perf:benchmark-gate:",
        "quality:chaos:smoke:",
        "quality:a11y:smoke:",
        "quality:providers:required-gate:",
    ):
        assert token in text


def test_ci_quality_job_invokes_holistic_quality_tasks() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    for token in (
        "task quality:providers:required-gate",
        "task quality:security:sast",
        "task quality:perf:benchmark-gate",
        "task quality:chaos:smoke",
        "task quality:a11y:smoke",
    ):
        assert token in text


def test_release_security_audits_are_blocking() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert "pip-audit --format=json --output dist/pip-audit.json || true" not in text
    assert "cargo audit --json > dist/cargo-audit.json || true" not in text
