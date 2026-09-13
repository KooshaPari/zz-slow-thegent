"""E2E lifecycle coverage for regression spiral governance artifacts."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _init_project(tmp_path: Path) -> dict[str, Path]:
    project = tmp_path / "project"
    verify_dir = project / ".claude" / "verification"
    hooks_dir = project / "hooks"
    home_dir = tmp_path / "home"

    verify_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (home_dir / ".claude").mkdir(parents=True, exist_ok=True)

    source_cfg = _repo_root() / "hooks" / "hook-config.yaml"
    (hooks_dir / "hook-config.yaml").write_text(source_cfg.read_text(encoding="utf-8"), encoding="utf-8")
    (project / ".claude" / "quality.json").write_text("{}", encoding="utf-8")
    (verify_dir / "regression-spiral-state.json").write_text(
        json.dumps(
            {
                "contract_version": "v1",
                "generated_at": "2026-01-01T00:00:00Z",
                "streak": 0,
                "violations": 0,
                "prev_violations": 0,
                "band_retry_counts": {"green": 0, "yellow": 0, "red": 0},
                "cooldown_until": 0,
                "escalation_stage": "seed",
                "last_policy_band": "green",
                "last_directive": "seed_directive",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    (project / "README").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=project, check=True)

    return {
        "project": project,
        "verify_dir": verify_dir,
        "home_dir": home_dir,
        "gate_script": _repo_root() / "hooks" / "governance-gates.sh",
    }


def _write_attestation(path: Path) -> None:
    attestation = {
        "summary": {"fr_total": 0, "fr_covered": 0, "orphan_tests": 0},
        "methodology": {
            "test_first": {"missing_test_pairs": []},
            "missing_required_test_types": [],
            "detected_test_types": {},
        },
        "security": {"signed_attestation_present": True, "slsa_provenance_present": True},
    }
    path.write_text(json.dumps(attestation).decode() + "\n", encoding="utf-8")


def _run_once(
    paths: dict[str, Path],
    *,
    run_id: int,
    async_results_payload: dict | None,
    qa_state_present: bool,
    qa_attestation_present: bool,
    require_e2e_first: bool,
    require_env_ready_first: bool,
    max_failed: int,
    max_flaky: int,
    max_yellow_retries: int = 2,
    max_red_retries: int = 2,
) -> subprocess.CompletedProcess[str]:
    verify_dir = paths["verify_dir"]
    home_dir = paths["home_dir"]
    project = paths["project"]

    async_path = home_dir / ".claude" / ".async-test-results.json"
    qa_state_path = verify_dir / "qa-state.json"
    qa_attestation_path = verify_dir / "qa-attestation.json"

    if async_results_payload is None:
        async_path.unlink(missing_ok=True)
    else:
        async_path.write_text(json.dumps(async_results_payload).decode() + "\n", encoding="utf-8")

    if qa_state_present:
        qa_state_path.write_text("{}", encoding="utf-8")
    else:
        qa_state_path.unlink(missing_ok=True)

    if qa_attestation_present:
        _write_attestation(qa_attestation_path)
    else:
        qa_attestation_path.unlink(missing_ok=True)

    temp_dir = paths["project"].parent / f".tmp-run-{run_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = paths["project"].parent / f".hook-cache-run-{run_id}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "_HOOK_DISPATCHED": "1",
        "JQ_CMD": "jq",
        "QUALITY_MAX_ATTEMPTS": "999",
        "TMPDIR": str(temp_dir),
        "THEGENT_CACHE_DIR": str(cache_dir),
        "HOOK_CACHE_TTL": "0",
        "QA_GATES_ONLY": "regression_spiral_guard",
        "PROJECT_DIR": str(project),
        "VERIFY_DIR": str(verify_dir),
        "QUALITY_CONFIG": str(project / ".claude" / "quality.json"),
        "HOME": str(home_dir),
        "SESSION_ID": f"spiral-lifecycle-{run_id}",
        "QA_SPIRAL_MAX_FAILED_TESTS": str(max_failed),
        "QA_SPIRAL_MAX_FLAKY_TESTS": str(max_flaky),
        "QA_SPIRAL_STREAK_TRIGGER": "99",
        "QA_REQUIRE_E2E_FIRST": "true" if require_e2e_first else "false",
        "QA_REQUIRE_ENV_READY_FIRST": "true" if require_env_ready_first else "false",
        "QA_SPIRAL_MAX_YELLOW_RETRIES": str(max_yellow_retries),
        "QA_SPIRAL_MAX_RED_RETRIES": str(max_red_retries),
    }
    return subprocess.run(
        [str(paths["gate_script"])],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_artifacts(verify_dir: Path) -> tuple[dict, dict, dict, dict | None, list[dict]]:
    report = json.loads((verify_dir / "regression-spiral-guard.json").read_text(encoding="utf-8"))
    metric_lines = [
        line
        for line in (verify_dir / "regression-spiral-metrics.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    metric = json.loads(metric_lines[-1])
    all_metrics = [json.loads(line) for line in metric_lines]
    state = json.loads((verify_dir / "regression-spiral-state.json").read_text(encoding="utf-8"))
    alert_path = verify_dir / "regression-spiral-alert.json"
    alert = json.loads(alert_path.read_text(encoding="utf-8")) if alert_path.exists() else None
    return report, metric, state, alert, all_metrics


def _assert_contract_versions(report: dict, metric: dict, state: dict, alert: dict | None) -> None:
    assert report["contract_version"] == "v1"
    assert metric["contract_version"] == "v1"
    assert state["contract_version"] == "v1"
    if alert is not None:
        assert alert["contract_version"] == "v1"


@pytest.mark.unit
def test_spiral_lifecycle_green_yellow_red_then_cooldown_recovery(tmp_path: Path) -> None:
    paths = _init_project(tmp_path)
    verify_dir = paths["verify_dir"]

    run1 = _run_once(
        paths,
        run_id=1,
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
        qa_state_present=True,
        qa_attestation_present=True,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=5,
        max_flaky=5,
    )
    assert run1.returncode == 0, f"{run1.stdout}\n{run1.stderr}"
    report1, metric1, state1, alert1, _ = _load_artifacts(verify_dir)
    _assert_contract_versions(report1, metric1, state1, alert1)
    assert report1["policy_band"] == "green"
    assert alert1 is None

    run2 = _run_once(
        paths,
        run_id=2,
        async_results_payload={"total": 10, "failed": 1, "flaky": 0},
        qa_state_present=True,
        qa_attestation_present=True,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=0,
        max_flaky=10,
        max_yellow_retries=10,
        max_red_retries=10,
    )
    assert run2.returncode == 0, f"{run2.stdout}\n{run2.stderr}"
    report2, metric2, state2, alert2, _ = _load_artifacts(verify_dir)
    _assert_contract_versions(report2, metric2, state2, alert2)
    assert report2["policy_band"] == "yellow"
    assert alert2 is not None
    assert alert2["severity"] == "warning"

    run3 = _run_once(
        paths,
        run_id=3,
        async_results_payload=None,
        qa_state_present=False,
        qa_attestation_present=False,
        require_e2e_first=True,
        require_env_ready_first=True,
        max_failed=0,
        max_flaky=0,
    )
    assert run3.returncode == 2, f"{run3.stdout}\n{run3.stderr}"
    report3, metric3, state3, alert3, _ = _load_artifacts(verify_dir)
    _assert_contract_versions(report3, metric3, state3, alert3)
    assert report3["policy_band"] == "red"
    assert report3["interrupt"] is True
    assert alert3 is not None
    assert alert3["severity"] == "critical"

    state3["cooldown_until"] = int(time.time()) - 1
    state3["band_retry_counts"]["yellow"] = 5
    state3["band_retry_counts"]["red"] = 4
    (verify_dir / "regression-spiral-state.json").write_text(json.dumps(state3).decode() + "\n", encoding="utf-8")

    run4 = _run_once(
        paths,
        run_id=4,
        async_results_payload={"total": 10, "failed": 0, "flaky": 0},
        qa_state_present=True,
        qa_attestation_present=True,
        require_e2e_first=False,
        require_env_ready_first=False,
        max_failed=5,
        max_flaky=5,
    )
    assert run4.returncode == 0, f"{run4.stdout}\n{run4.stderr}"
    report4, metric4, state4, alert4, all_metrics = _load_artifacts(verify_dir)
    _assert_contract_versions(report4, metric4, state4, alert4)
    assert report4["policy_band"] == "green"
    assert state4["band_retry_counts"]["green"] == 0
    assert state4["band_retry_counts"]["yellow"] == 0
    assert state4["band_retry_counts"]["red"] == 0
    assert state4["cooldown_until"] is None
    assert alert4 is None

    assert len(all_metrics) == 4
    assert [item["policy_band"] for item in all_metrics] == ["green", "yellow", "red", "green"]
    assert all(item["contract_version"] == "v1" for item in all_metrics)
