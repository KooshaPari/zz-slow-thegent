"""Governance gate selector mode tests."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _assert_report_schema(report: dict) -> None:
    required_keys = {
        "contract_version",
        "generated_at",
        "metrics",
        "thresholds",
        "violations",
        "streak",
        "interrupt",
        "pressure_score",
        "policy_band",
        "enforcement_path",
        "remediation_directive",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
    }
    assert required_keys.issubset(report.keys())
    assert report["contract_version"] == "v1"
    assert isinstance(report["generated_at"], str)
    assert isinstance(report["metrics"], dict)
    assert isinstance(report["thresholds"], dict)
    assert isinstance(report["violations"], int)
    assert isinstance(report["streak"], int)
    assert isinstance(report["interrupt"], bool)
    assert isinstance(report["pressure_score"], (int, float))
    assert report["policy_band"] in {"green", "yellow", "red"}
    assert isinstance(report["enforcement_path"], str)
    assert isinstance(report["remediation_directive"], str)
    assert isinstance(report["band_retry_count"], int)
    assert report["cooldown_until"] is None or isinstance(report["cooldown_until"], int)
    assert isinstance(report["escalation_stage"], str)


def _assert_metric_schema(metric: dict) -> None:
    required_keys = {
        "contract_version",
        "generated_at",
        "session_id",
        "status",
        "severity",
        "reason",
        "metrics",
        "violations",
        "streak",
        "interrupt",
        "pressure_score",
        "policy_band",
        "remediation_directive",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
    }
    assert required_keys.issubset(metric.keys())
    assert metric["contract_version"] == "v1"
    assert isinstance(metric["generated_at"], str)
    assert isinstance(metric["session_id"], str)
    assert isinstance(metric["status"], str)
    assert isinstance(metric["severity"], str)
    assert isinstance(metric["reason"], str)
    assert isinstance(metric["metrics"], dict)
    assert isinstance(metric["violations"], int)
    assert isinstance(metric["streak"], int)
    assert isinstance(metric["interrupt"], bool)
    assert isinstance(metric["pressure_score"], (int, float))
    assert metric["policy_band"] in {"green", "yellow", "red"}
    assert isinstance(metric["remediation_directive"], str)
    assert isinstance(metric["band_retry_count"], int)
    assert metric["cooldown_until"] is None or isinstance(metric["cooldown_until"], int)
    assert isinstance(metric["escalation_stage"], str)


def _assert_state_schema(state: dict) -> None:
    required_keys = {
        "contract_version",
        "generated_at",
        "streak",
        "violations",
        "prev_violations",
        "band_retry_counts",
        "cooldown_until",
        "escalation_stage",
        "last_policy_band",
        "last_directive",
    }
    assert required_keys.issubset(state.keys())
    assert state["contract_version"] == "v1"
    assert isinstance(state["generated_at"], str)
    assert isinstance(state["streak"], int)
    assert isinstance(state["violations"], int)
    assert isinstance(state["prev_violations"], int)
    assert isinstance(state["band_retry_counts"], dict)
    assert set(state["band_retry_counts"].keys()) == {"green", "yellow", "red"}
    assert all(isinstance(v, int) for v in state["band_retry_counts"].values())
    assert state["cooldown_until"] is None or isinstance(state["cooldown_until"], int)
    assert isinstance(state["escalation_stage"], str)
    assert state["last_policy_band"] in {"green", "yellow", "red"}
    assert isinstance(state["last_directive"], str)


def _assert_alert_schema(alert: dict) -> None:
    required_keys = {
        "contract_version",
        "generated_at",
        "severity",
        "reason",
        "session_id",
        "project_dir",
        "policy_band",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
        "remediation_directive",
    }
    assert required_keys.issubset(alert.keys())
    assert alert["contract_version"] == "v1"
    assert isinstance(alert["generated_at"], str)
    assert alert["severity"] in {"warning", "critical"}
    assert isinstance(alert["reason"], str)
    assert isinstance(alert["session_id"], str)
    assert isinstance(alert["project_dir"], str)
    assert alert["policy_band"] in {"green", "yellow", "red"}
    assert isinstance(alert["band_retry_count"], int)
    assert alert["cooldown_until"] is None or isinstance(alert["cooldown_until"], int)
    assert isinstance(alert["escalation_stage"], str)
    assert isinstance(alert["remediation_directive"], str)


def _read_governance_gate_execution(project_dir: Path) -> list[dict]:
    verify_dir = project_dir / ".claude" / "verification"
    metrics_path = verify_dir / "quality-metrics.json"
    if not metrics_path.exists():
        return []
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    entries = payload.get("governance_gate_execution", [])
    assert isinstance(entries, list)
    return entries


def _run_governance_selected(
    tmp_path: Path,
    *,
    selected: str,
    async_results_payload: dict | None = None,
    qa_state_present: bool = True,
    qa_attestation_present: bool = True,
    max_failed: int = 5,
    max_flaky: int = 5,
    require_e2e_first: bool = False,
    require_env_ready_first: bool = False,
    prev_streak: int = 0,
    prev_violations: int = 0,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    project = tmp_path / "project"
    verify_dir = project / ".claude" / "verification"
    hooks_dir = project / "hooks"
    home_dir = tmp_path / "home"
    temp_dir = tmp_path / ".tmp"
    cache_dir = tmp_path / ".hook-cache"

    verify_dir.mkdir(parents=True, exist_ok=True)
    # Create test directories for tier-enforcer to pass
    (project / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (project / "tests" / "integration").mkdir(parents=True, exist_ok=True)
    (project / "tests" / "e2e").mkdir(parents=True, exist_ok=True)
    (project / "tests" / "security").mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (home_dir / ".claude").mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_cfg = _repo_root() / "hooks" / "hook-config.yaml"
    (hooks_dir / "hook-config.yaml").write_text(source_cfg.read_text(encoding="utf-8"), encoding="utf-8")
    (project / ".claude" / "quality.json").write_text("{}", encoding="utf-8")
    (verify_dir / "regression-spiral-state.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-01-01T00:00:00Z",
                "streak": prev_streak,
                "violations": prev_violations,
                "prev_violations": prev_violations,
                "band_retry_counts": {"green": 0, "yellow": 0, "red": 0},
                "cooldown_until": 0,
                "escalation_stage": "seed",
                "last_policy_band": "green",
                "last_directive": "seed_directive",
            }
        ).decode()
        + "\n",
        encoding="utf-8",
    )

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
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=project, check=True)

    gate_script = _repo_root() / "hooks" / "governance-gates.sh"
    env = {
        **os.environ,
        "_HOOK_DISPATCHED": "1",
        "JQ_CMD": "jq",
        "QUALITY_MAX_ATTEMPTS": "999",
        "TMPDIR": str(temp_dir),
        "THEGENT_CACHE_DIR": str(cache_dir),
        "QA_GATES_ONLY": selected,
        "PROJECT_DIR": str(project),
        "VERIFY_DIR": str(verify_dir),
        "QUALITY_CONFIG": str(project / ".claude" / "quality.json"),
        "HOME": str(home_dir),
        "SESSION_ID": "selector-tests",
        "QA_SPIRAL_MAX_FAILED_TESTS": str(max_failed),
        "QA_SPIRAL_MAX_FLAKY_TESTS": str(max_flaky),
        "QA_SPIRAL_STREAK_TRIGGER": "99",
        "QA_REQUIRE_E2E_FIRST": "true" if require_e2e_first else "false",
        "QA_REQUIRE_ENV_READY_FIRST": "true" if require_env_ready_first else "false",
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(gate_script)],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _extract_selected_mode_line(stdout: str) -> str:
    match = re.search(r"GOVERNANCE-GATES: selected mode gates=([^\n]+)", stdout)
    return match.group(1).strip() if match else ""


@pytest.mark.unit
def test_selector_single_gate_runs_only_regression_spiral(tmp_path: Path) -> None:
    proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )

    assert proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard" in proc.stdout
    assert "tier-enforcer" not in proc.stdout

    report = json.loads(
        (tmp_path / "project/.claude/verification/regression-spiral-guard.json").read_text(encoding="utf-8")
    )
    assert report["policy_band"] == "green"


@pytest.mark.unit
def test_selector_multi_gate_runs_list_without_unselected_gates(tmp_path: Path) -> None:
    proc = _run_governance_selected(
        tmp_path,
        selected="reliability,regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )

    assert proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard,reliability" in proc.stdout
    assert "reliability" in proc.stdout
    assert "regression-spiral-guard" in proc.stdout
    assert "tier-enforcer" not in proc.stdout


@pytest.mark.unit
def test_selector_unknown_gate_is_fail_closed(tmp_path: Path) -> None:
    proc = _run_governance_selected(tmp_path, selected="nope_gate")

    assert proc.returncode == 2
    assert "unknown gate label: nope_gate" in proc.stdout
    assert "GOVERNANCE-GATES: 1 fail-closed gate(s) failed" in proc.stdout


@pytest.mark.unit
def test_selector_malformed_token_is_fail_closed(tmp_path: Path) -> None:
    proc = _run_governance_selected(tmp_path, selected="regression_spiral_guard;rm -rf /")

    assert proc.returncode == 2
    assert "unknown gate label:" in proc.stdout
    assert "GOVERNANCE-GATES: 1 fail-closed gate(s) failed" in proc.stdout


@pytest.mark.unit
def test_selector_empty_entries_fail_closed_with_explicit_reason(tmp_path: Path) -> None:
    proc = _run_governance_selected(tmp_path, selected=" , , ")

    assert proc.returncode == 2
    assert "no valid gate labels in QA_GATES_ONLY=,," in proc.stdout
    assert "GOVERNANCE-GATES: 1 fail-closed gate(s) failed" in proc.stdout


@pytest.mark.unit
def test_cache_scope_selected_then_full_do_not_collide(tmp_path: Path) -> None:
    selected_proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    assert selected_proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard" in selected_proc.stdout

    full_proc = _run_governance_selected(
        tmp_path,
        selected="",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    assert full_proc.returncode == 0
    assert "selected mode gates=" not in full_proc.stdout
    assert "tier-enforcer" in full_proc.stdout


@pytest.mark.unit
def test_cache_scope_full_then_selected_do_not_collide(tmp_path: Path) -> None:
    full_proc = _run_governance_selected(
        tmp_path,
        selected="",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    assert full_proc.returncode == 0
    assert "selected mode gates=" not in full_proc.stdout
    assert "tier-enforcer" in full_proc.stdout

    selected_proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    assert selected_proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard" in selected_proc.stdout
    assert "tier-enforcer" not in selected_proc.stdout


@pytest.mark.unit
def test_selector_is_canonicalized_for_display_and_execution(tmp_path: Path) -> None:
    proc = _run_governance_selected(
        tmp_path,
        selected=" regression_spiral_guard , reliability , regression_spiral_guard ",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )

    assert proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard,reliability" in proc.stdout
    assert "tier-enforcer" not in proc.stdout


@pytest.mark.unit
def test_selector_records_per_gate_execution_metrics(tmp_path: Path) -> None:
    proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    assert proc.returncode == 0

    entries = _read_governance_gate_execution(tmp_path / "project")
    assert entries, "missing governance_gate_execution entries"

    regression_entries = [
        entry for entry in entries if entry.get("name") in {"regression_spiral_guard", "regression-spiral-guard"}
    ]
    assert regression_entries, "missing regression_spiral_guard metric entry"
    entry = regression_entries[-1]

    assert entry["result"] == "pass"
    assert entry["cache_hit"] is False
    assert entry["scope"] == "selected"
    assert entry["profile"] == "auto"
    assert isinstance(entry["duration_ms"], int)
    assert entry["duration_ms"] >= 0


@pytest.mark.unit
def test_equivalent_selector_sets_share_cache_scope(tmp_path: Path) -> None:
    first_proc = _run_governance_selected(
        tmp_path,
        selected="reliability,regression_spiral_guard",
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
        max_failed=5,
        max_flaky=5,
        require_e2e_first=False,
        require_env_ready_first=False,
        prev_streak=0,
    )
    assert first_proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard,reliability" in first_proc.stdout

    second_proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard,reliability",
        async_results_payload=None,
        qa_state_present=False,
        qa_attestation_present=False,
        max_failed=0,
        max_flaky=0,
        require_e2e_first=True,
        require_env_ready_first=True,
        prev_streak=2,
    )
    # If canonical selector scope is shared, this run returns cached result (rc=0).
    # Without canonicalization, this configuration would execute and fail closed (rc=2).
    assert second_proc.returncode == 0
    assert "selected mode gates=regression_spiral_guard,reliability" in second_proc.stdout
    assert "policy_band=red" not in second_proc.stdout


@pytest.mark.unit
def test_selector_native_dispatcher_parity_with_shell_fallback(tmp_path: Path) -> None:
    native_bin = _repo_root() / "hooks/hook-dispatcher/target/debug/hook-dispatcher"
    if not native_bin.exists():
        pytest.skip("native hook-dispatcher binary not built")

    selector = " regression_spiral_guard , reliability , regression_spiral_guard "
    fallback_proc = _run_governance_selected(
        tmp_path / "fallback",
        selected=selector,
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
    )
    native_proc = subprocess.run(
        [str(native_bin), "governance", "spiral-selector", "--format", "csv", selector],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert fallback_proc.returncode == 0
    assert native_proc.returncode == 0
    assert _extract_selected_mode_line(fallback_proc.stdout) == "regression_spiral_guard,reliability"
    assert native_proc.stdout.strip() == "regression_spiral_guard,reliability"


@pytest.mark.unit
def test_selector_native_dispatcher_parity_for_malformed_token_fail_closed(tmp_path: Path) -> None:
    native_bin = _repo_root() / "hooks/hook-dispatcher/target/debug/hook-dispatcher"
    if not native_bin.exists():
        pytest.skip("native hook-dispatcher binary not built")

    selector = "regression_spiral_guard;rm -rf /"
    fallback_proc = _run_governance_selected(tmp_path / "fallback", selected=selector)
    native_proc = subprocess.run(
        [str(native_bin), "governance", "spiral-selector", "--format", "csv", selector],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert fallback_proc.returncode == 2
    assert native_proc.returncode == 0
    assert "unknown gate label: regression_spiral_guard;rm-rf/" in fallback_proc.stdout
    assert native_proc.stdout.strip() == "regression_spiral_guard;rm-rf/"


@pytest.mark.unit
def test_selector_artifact_schema_drift_sentinel_exact_keys(tmp_path: Path) -> None:
    proc = _run_governance_selected(
        tmp_path,
        selected="regression_spiral_guard",
        async_results_payload=None,
        qa_state_present=False,
        qa_attestation_present=False,
        max_failed=0,
        max_flaky=0,
        require_e2e_first=True,
        require_env_ready_first=True,
        prev_streak=2,
    )
    assert proc.returncode == 2

    verify_dir = tmp_path / "project/.claude/verification"
    report = json.loads((verify_dir / "regression-spiral-guard.json").read_text(encoding="utf-8"))
    metric = json.loads((verify_dir / "regression-spiral-metrics.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    state = json.loads((verify_dir / "regression-spiral-state.json").read_text(encoding="utf-8"))
    alert = json.loads((verify_dir / "regression-spiral-alert.json").read_text(encoding="utf-8"))

    assert set(report.keys()) == {
        "contract_version",
        "generated_at",
        "metrics",
        "thresholds",
        "violations",
        "streak",
        "interrupt",
        "pressure_score",
        "policy_band",
        "enforcement_path",
        "remediation_directive",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
    }
    assert set(metric.keys()) == {
        "contract_version",
        "generated_at",
        "session_id",
        "status",
        "severity",
        "reason",
        "metrics",
        "violations",
        "streak",
        "interrupt",
        "pressure_score",
        "policy_band",
        "remediation_directive",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
    }
    assert set(state.keys()) == {
        "contract_version",
        "generated_at",
        "streak",
        "violations",
        "prev_violations",
        "band_retry_counts",
        "cooldown_until",
        "escalation_stage",
        "last_policy_band",
        "last_directive",
    }
    assert set(alert.keys()) == {
        "contract_version",
        "generated_at",
        "severity",
        "reason",
        "session_id",
        "project_dir",
        "policy_band",
        "band_retry_count",
        "cooldown_until",
        "escalation_stage",
        "remediation_directive",
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("scenario", "kwargs", "expected_returncode", "expected_band", "expect_alert", "expected_alert_severity"),
    [
        (
            "green",
            {
                "async_results_payload": {"total": 10, "failed": 0, "flaky": 0},
                "qa_state_present": True,
                "qa_attestation_present": True,
                "max_failed": 5,
                "max_flaky": 5,
                "require_e2e_first": False,
                "require_env_ready_first": False,
            },
            0,
            "green",
            False,
            None,
        ),
        (
            "yellow",
            {
                "async_results_payload": {"total": 10, "failed": 1, "flaky": 0},
                "qa_state_present": True,
                "qa_attestation_present": True,
                "max_failed": 0,
                "max_flaky": 5,
                "require_e2e_first": False,
                "require_env_ready_first": False,
            },
            0,
            "yellow",
            True,
            "warning",
        ),
        (
            "red",
            {
                "async_results_payload": None,
                "qa_state_present": False,
                "qa_attestation_present": False,
                "max_failed": 0,
                "max_flaky": 0,
                "require_e2e_first": True,
                "require_env_ready_first": True,
                "prev_streak": 2,
            },
            2,
            "red",
            True,
            "critical",
        ),
    ],
)
def test_selector_artifact_contract_by_policy_band(
    tmp_path: Path,
    scenario: str,
    kwargs: dict,
    expected_returncode: int,
    expected_band: str,
    expect_alert: bool,
    expected_alert_severity: str | None,
) -> None:
    proc = _run_governance_selected(tmp_path, selected="regression_spiral_guard", **kwargs)
    assert proc.returncode == expected_returncode, f"{scenario} stdout={proc.stdout!r} stderr={proc.stderr!r}"

    verify_dir = tmp_path / "project/.claude/verification"
    report_path = verify_dir / "regression-spiral-guard.json"
    metrics_path = verify_dir / "regression-spiral-metrics.jsonl"
    state_path = verify_dir / "regression-spiral-state.json"
    alert_path = verify_dir / "regression-spiral-alert.json"

    assert report_path.exists(), f"missing report for {scenario}"
    assert metrics_path.exists(), f"missing metrics for {scenario}"
    assert state_path.exists(), f"missing state for {scenario}"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    metric = json.loads(metrics_path.read_text(encoding="utf-8").splitlines()[-1])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    _assert_report_schema(report)
    _assert_metric_schema(metric)
    _assert_state_schema(state)

    assert report["policy_band"] == expected_band
    assert metric["policy_band"] == expected_band
    assert state["last_policy_band"] == expected_band
    assert metric["escalation_stage"] == report["escalation_stage"]
    assert metric["remediation_directive"] == report["remediation_directive"]

    if expect_alert:
        assert alert_path.exists(), f"expected alert for {scenario}"
        alert = json.loads(alert_path.read_text(encoding="utf-8"))
        _assert_alert_schema(alert)
        assert alert["policy_band"] == expected_band
        assert alert["severity"] == expected_alert_severity
    else:
        assert not alert_path.exists(), f"did not expect alert for {scenario}"
