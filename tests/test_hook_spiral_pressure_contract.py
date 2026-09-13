"""Shell-level regression tests for spiral pressure contract enforcement."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json_artifact(path: Path, *, proc: subprocess.CompletedProcess[str], verify_dir: Path) -> dict:
    if not path.exists():
        files = sorted(p.name for p in verify_dir.glob("*"))
        pytest.fail(
            "\n".join(
                [
                    f"missing governance artifact: {path}",
                    f"returncode={proc.returncode}",
                    f"stdout={proc.stdout!r}",
                    f"stderr={proc.stderr!r}",
                    f"verification_files={files}",
                ]
            )
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _run_governance(
    tmp_path: Path,
    *,
    async_results_payload: dict | None,
    qa_state_present: bool,
    qa_attestation_present: bool,
    prev_streak: int,
    prev_violations: int,
    require_e2e_first: bool,
    require_env_ready_first: bool,
    max_failed: int,
    max_flaky: int,
    streak_trigger: int,
    max_yellow_retries: int = 2,
    max_red_retries: int = 2,
    yellow_cooldown_minutes: int = 30,
    red_cooldown_minutes: int = 60,
    directive_green: str = "continue_green",
    directive_yellow: str = "remediate_yellow",
    directive_red: str = "interrupt_red",
    initial_band_retry_counts: tuple[int, int, int] = (0, 0, 0),
    initial_cooldown_until: int = 0,
) -> tuple[int, dict, dict, dict, dict | None]:
    project = tmp_path / "project"
    verify_dir = project / ".claude" / "verification"
    hooks_dir = project / "hooks"
    home_dir = tmp_path / "home"
    verify_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (home_dir / ".claude").mkdir(parents=True, exist_ok=True)
    temp_dir = tmp_path / ".tmp"
    cache_dir = tmp_path / ".hook-cache"
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_cfg = _repo_root() / "hooks" / "hook-config.yaml"
    (hooks_dir / "hook-config.yaml").write_text(source_cfg.read_text(encoding="utf-8"), encoding="utf-8")
    (project / ".claude" / "quality.json").write_text("{}", encoding="utf-8")

    state = {
        "generated_at": "2026-01-01T00:00:00Z",
        "streak": prev_streak,
        "violations": prev_violations,
        "prev_violations": prev_violations,
        "band_retry_counts": {
            "green": initial_band_retry_counts[0],
            "yellow": initial_band_retry_counts[1],
            "red": initial_band_retry_counts[2],
        },
        "cooldown_until": initial_cooldown_until,
        "escalation_stage": "seed",
        "last_policy_band": "green",
        "last_directive": "seed_directive",
    }
    (verify_dir / "regression-spiral-state.json").write_text(json.dumps(state).decode() + "\n", encoding="utf-8")

    if async_results_payload is not None:
        (home_dir / ".claude" / ".async-test-results.json").write_text(
            json.dumps(async_results_payload).decode() + "\n",
            encoding="utf-8",
        )

    if qa_state_present:
        (verify_dir / "qa-state.json").write_text("{}", encoding="utf-8")

    if qa_attestation_present:
        attestation = {
            "summary": {"fr_total": 0, "fr_covered": 0, "orphan_tests": 0},
            "methodology": {
                "test_first": {"missing_test_pairs": []},
                "missing_required_test_types": [],
                "detected_test_types": {},
            },
            "security": {"signed_attestation_present": True, "slsa_provenance_present": True},
        }
        (verify_dir / "qa-attestation.json").write_text(json.dumps(attestation).decode() + "\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    (project / "README").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)

    gate_script = _repo_root() / "hooks" / "governance-gates.sh"
    env = {
        **os.environ,
        "_HOOK_DISPATCHED": "1",
        "JQ_CMD": "jq",
        "QUALITY_MAX_ATTEMPTS": "999",
        "TMPDIR": str(temp_dir),
        "THEGENT_CACHE_DIR": str(cache_dir),
        "QA_GATES_ONLY": "regression_spiral_guard",
        "PROJECT_DIR": str(project),
        "VERIFY_DIR": str(verify_dir),
        "QUALITY_CONFIG": str(project / ".claude" / "quality.json"),
        "HOME": str(home_dir),
        "SESSION_ID": "testsess",
        "QA_SPIRAL_MAX_FAILED_TESTS": str(max_failed),
        "QA_SPIRAL_MAX_FLAKY_TESTS": str(max_flaky),
        "QA_SPIRAL_STREAK_TRIGGER": str(streak_trigger),
        "QA_REQUIRE_E2E_FIRST": "true" if require_e2e_first else "false",
        "QA_REQUIRE_ENV_READY_FIRST": "true" if require_env_ready_first else "false",
        "QA_SPIRAL_MAX_YELLOW_RETRIES": str(max_yellow_retries),
        "QA_SPIRAL_MAX_RED_RETRIES": str(max_red_retries),
        "QA_SPIRAL_YELLOW_COOLDOWN_MINUTES": str(yellow_cooldown_minutes),
        "QA_SPIRAL_RED_COOLDOWN_MINUTES": str(red_cooldown_minutes),
        "QA_SPIRAL_DIRECTIVE_GREEN": directive_green,
        "QA_SPIRAL_DIRECTIVE_YELLOW": directive_yellow,
        "QA_SPIRAL_DIRECTIVE_RED": directive_red,
    }
    proc = subprocess.run(
        [str(gate_script)],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    report = _load_json_artifact(verify_dir / "regression-spiral-guard.json", proc=proc, verify_dir=verify_dir)

    metrics_path = verify_dir / "regression-spiral-metrics.jsonl"
    if not metrics_path.exists():
        pytest.fail(
            "\n".join(
                [
                    f"missing governance artifact: {metrics_path}",
                    f"returncode={proc.returncode}",
                    f"stdout={proc.stdout!r}",
                    f"stderr={proc.stderr!r}",
                ]
            )
        )
    metric_lines = [line for line in metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not metric_lines:
        pytest.fail(
            "\n".join(
                [
                    f"empty governance artifact: {metrics_path}",
                    f"returncode={proc.returncode}",
                    f"stdout={proc.stdout!r}",
                    f"stderr={proc.stderr!r}",
                ]
            )
        )
    metric = json.loads(metric_lines[-1])

    state_after = _load_json_artifact(verify_dir / "regression-spiral-state.json", proc=proc, verify_dir=verify_dir)
    alert_path = verify_dir / "regression-spiral-alert.json"
    alert = json.loads(alert_path.read_text(encoding="utf-8")) if alert_path.exists() else None
    return proc.returncode, report, metric, state_after, alert


@pytest.mark.unit
def test_spiral_gate_report_and_metric_include_pressure_fields(tmp_path: Path) -> None:
    rc, report, metric, state, alert = _run_governance(
        tmp_path,
        async_results_payload={"total": 10, "failed": 9, "flaky": 9},
        qa_state_present=True,
        qa_attestation_present=True,
        prev_streak=0,
        prev_violations=0,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=0,
        max_flaky=0,
        streak_trigger=1,
    )
    assert rc == 2
    assert "pressure_score" in report
    assert "policy_band" in report
    assert report["policy_band"] in {"green", "yellow", "red"}
    assert "pressure_score" in metric
    assert "policy_band" in metric
    assert metric["policy_band"] == report["policy_band"]
    assert "remediation_directive" in report
    assert "band_retry_count" in report
    assert "cooldown_until" in report
    assert "escalation_stage" in report
    assert metric["remediation_directive"] == report["remediation_directive"]
    assert metric["band_retry_count"] == report["band_retry_count"]
    assert metric["cooldown_until"] == report["cooldown_until"]
    assert metric["escalation_stage"] == report["escalation_stage"]
    assert state["last_policy_band"] == report["policy_band"]
    assert state["last_directive"] == report["remediation_directive"]
    assert alert is not None
    assert alert["policy_band"] == report["policy_band"]
    assert alert["remediation_directive"] == report["remediation_directive"]


@pytest.mark.unit
def test_red_policy_band_forces_interrupt_and_fail_closed(tmp_path: Path) -> None:
    rc, report, metric, _, alert = _run_governance(
        tmp_path,
        async_results_payload=None,
        qa_state_present=False,
        qa_attestation_present=False,
        prev_streak=2,
        prev_violations=0,
        require_e2e_first=True,
        require_env_ready_first=True,
        max_failed=0,
        max_flaky=0,
        streak_trigger=99,
    )
    assert rc == 2
    assert report["policy_band"] == "red"
    assert report["interrupt"] is True
    assert report["enforcement_path"] == "fail_closed"
    assert float(report["pressure_score"]) >= 0.75
    assert metric["policy_band"] == "red"
    assert metric["interrupt"] is True
    assert report["remediation_directive"] == "interrupt_red"
    assert alert is not None
    assert alert["policy_band"] == "red"
    assert alert["remediation_directive"] == "interrupt_red"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("scenario", "expected_band", "expected_directive", "kwargs"),
    [
        (
            "green",
            "green",
            "continue_green",
            {
                "async_results_payload": {"total": 10, "failed": 0, "flaky": 0},
                "qa_state_present": True,
                "qa_attestation_present": True,
                "prev_streak": 0,
                "prev_violations": 0,
                "require_e2e_first": False,
                "require_env_ready_first": False,
                "max_failed": 5,
                "max_flaky": 5,
                "streak_trigger": 99,
            },
        ),
        (
            "yellow",
            "yellow",
            "remediate_yellow",
            {
                "async_results_payload": {"total": 10, "failed": 1, "flaky": 0},
                "qa_state_present": True,
                "qa_attestation_present": True,
                "prev_streak": 2,
                "prev_violations": 0,
                "require_e2e_first": False,
                "require_env_ready_first": False,
                "max_failed": 0,
                "max_flaky": 10,
                "streak_trigger": 99,
                "max_yellow_retries": 10,
            },
        ),
        (
            "red",
            "red",
            "interrupt_red",
            {
                "async_results_payload": None,
                "qa_state_present": False,
                "qa_attestation_present": False,
                "prev_streak": 2,
                "prev_violations": 0,
                "require_e2e_first": True,
                "require_env_ready_first": True,
                "max_failed": 0,
                "max_flaky": 0,
                "streak_trigger": 99,
            },
        ),
    ],
)
def test_spiral_directive_parity_by_band(
    tmp_path: Path, scenario: str, expected_band: str, expected_directive: str, kwargs: dict
) -> None:
    _, report, metric, state, alert = _run_governance(tmp_path, **kwargs)
    assert report["policy_band"] == expected_band
    assert report["remediation_directive"] == expected_directive
    assert "band_retry_count" in report
    assert "cooldown_until" in report
    assert "escalation_stage" in report
    assert metric["remediation_directive"] == expected_directive
    assert metric["policy_band"] == expected_band
    assert "band_retry_counts" in state
    assert set(state["band_retry_counts"]) == {"green", "yellow", "red"}
    assert state["last_policy_band"] == expected_band
    assert state["last_directive"] == expected_directive
    if scenario in {"yellow", "red"}:
        assert alert is not None
        assert alert["policy_band"] == expected_band
        assert alert["remediation_directive"] == expected_directive
    else:
        assert alert is None


@pytest.mark.unit
def test_yellow_retries_escalate_to_red_interrupt_after_threshold(tmp_path: Path) -> None:
    now_epoch = int(time.time())
    rc, report, metric, state, alert = _run_governance(
        tmp_path,
        async_results_payload={"total": 10, "failed": 1, "flaky": 0},
        qa_state_present=True,
        qa_attestation_present=True,
        prev_streak=2,
        prev_violations=0,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=0,
        max_flaky=10,
        streak_trigger=99,
        max_yellow_retries=1,
        max_red_retries=10,
        initial_band_retry_counts=(0, 1, 0),
        initial_cooldown_until=now_epoch + 1800,
    )
    assert rc == 2
    assert report["policy_band"] == "red"
    assert report["interrupt"] is True
    assert report["enforcement_path"] == "fail_closed"
    assert report["escalation_stage"] == "yellow_retry_limit_exceeded"
    assert report["remediation_directive"] == "interrupt_red"
    assert report["band_retry_count"] == 2
    assert isinstance(report["cooldown_until"], int)
    assert report["cooldown_until"] > now_epoch
    assert metric["policy_band"] == "red"
    assert metric["escalation_stage"] == "yellow_retry_limit_exceeded"
    assert state["last_policy_band"] == "red"
    assert state["band_retry_counts"]["yellow"] == 2
    assert alert is not None
    assert alert["policy_band"] == "red"


@pytest.mark.unit
def test_cooldown_expiry_resets_band_retry_counters(tmp_path: Path) -> None:
    now_epoch = int(time.time())
    _, report, _, state, _ = _run_governance(
        tmp_path,
        async_results_payload={"total": 10, "failed": 1, "flaky": 0},
        qa_state_present=True,
        qa_attestation_present=True,
        prev_streak=2,
        prev_violations=0,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=0,
        max_flaky=10,
        streak_trigger=99,
        max_yellow_retries=10,
        initial_band_retry_counts=(0, 4, 1),
        initial_cooldown_until=now_epoch - 60,
    )
    assert report["policy_band"] == "yellow"
    assert report["band_retry_count"] == 1
    assert state["band_retry_counts"]["yellow"] == 1
    assert state["band_retry_counts"]["red"] == 0
