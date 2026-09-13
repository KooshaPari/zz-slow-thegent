"""Tests for PR-targeted lanes, anti-flake profile, contributor guidance, and traceability contracts.

Covers tasks 87-100 from the pytest optimization wave plan.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import orjson as json

# scripts.test_pytest_wave_artifacts module was removed.
import pytest

pytest.importorskip(
    "scripts.test_pytest_wave_artifacts",
    reason=("scripts.test_pytest_wave_artifacts module removed; pr mode and flake lane tests skipped"),
)
from scripts.test_pytest_wave_artifacts import (  # noqa: E402
    _parse_collect_metrics,
)

ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TASKFILE = ROOT / "Taskfile.yml"
SCRIPT = ROOT / "scripts" / "test_pytest_wave_artifacts.py"
FR_TRACE_EXTRACTOR_SCRIPT = ROOT / "scripts" / "fr_trace_extractor.py"
PR_GUIDE = ROOT / "docs" / "guides" / "PR_TEST_IMPACT_REDUCTION.md"
PR_INI = ROOT / "pytest-pr.ini"
PR_FLAKE_INI = ROOT / "pytest-pr-flake.ini"
PR_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
BENCHMARK_WORKFLOW = ROOT / ".github" / "workflows" / "benchmark.yml"
TRACE_MIGRATION_SCRIPT = ROOT / "scripts" / "list_untagged_heavy_tests.py"


def test_pyproject_has_lane_markers() -> None:
    """pyproject should include PR and flake lane marker expressions."""
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "pr_lane_marker" in text
    assert "flake_lane_marker" in text


def test_pr_lane_ini_files_exist() -> None:
    """Fast PR lane + anti-flake lane profiles should be present."""
    assert PR_INI.is_file(), "pytest-pr.ini missing"
    assert PR_FLAKE_INI.is_file(), "pytest-pr-flake.ini missing"
    assert "--maxfail" in PR_FLAKE_INI.read_text(encoding="utf-8")
    pr_ini_text = PR_INI.read_text(encoding="utf-8")
    assert "--strict-config" in pr_ini_text
    assert "xfail_strict = true" in pr_ini_text


def test_taskfile_pr_aliases_exist() -> None:
    """Taskfile should expose PR run, targets and anti-flake helpers."""
    text = TASKFILE.read_text(encoding="utf-8")
    assert "  test:pr:" in text
    assert "  test:pr:targets:" in text
    assert "  test:anti-flake:" in text
    assert "  test:flake-lane:" in text


def test_taskfile_pr_command_documents_targeting(tmp_path: Path) -> None:
    """`task test:pr:targets` should write selected targets artifact."""
    target_output = tmp_path / "targets.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "pr-targets",
            "--changed-file",
            "src/thegent/cli/commands/impl.py",
            "--changed-file",
            "tests/test_unit_cli_commands_a.py",
            "--output",
            str(target_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(target_output.read_text(encoding="utf-8"))
    assert payload["fallback_to_fast_lane"] is False
    assert "tests/test_unit_cli_commands_a.py" in payload["targets"]


def test_pr_targets_fallback_to_fast_marker(tmp_path: Path) -> None:
    """Files without known suite mapping must mark fallback-to-fast-lane."""
    target_output = tmp_path / "fallback.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "pr-targets",
            "--changed-file",
            "README.md",
            "--output",
            str(target_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(target_output.read_text(encoding="utf-8"))
    assert payload["fallback_to_fast_lane"] is True
    assert payload["targets"] == []


def test_pr_impact_guide_exists_and_mentions_anti_flake() -> None:
    """Minimal PR impact guide should exist and include anti-flake command guidance."""
    text = PR_GUIDE.read_text(encoding="utf-8")
    assert "test:anti-flake" in text
    assert "@pytest.mark.fast" in text
    assert "@pytest.mark.deep" in text


def test_collect_metrics_parser_supports_pytest_count_formats() -> None:
    """Collect parser should extract node counts from common pytest summary formats."""
    selected, _ = _parse_collect_metrics("3/10 tests collected (7 deselected) in 0.01s", "")
    assert selected == 3
    selected, _ = _parse_collect_metrics("collected 128 items in 0.01s", "")
    assert selected == 128
    selected, _ = _parse_collect_metrics("no tests collected (10 deselected) in 0.01s", "")
    assert selected == 0


def _build_minimal_pytest_tree(root: Path) -> tuple[Path, Path]:
    tests_dir = root / "tests"
    src_dir = root / "src"
    tests_dir.mkdir()
    src_dir.mkdir()

    (src_dir / "api.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    (tests_dir / "test_api.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.requirement("FR-TEST-001")\n'
        "def test_with_requirement():\n    assert True\n\n"
        "def test_without_requirement():\n    assert True\n",
        encoding="utf-8",
    )

    return tests_dir, src_dir / "api.py"


def test_requirements_gate_fails_on_unmarked_pr_target(tmp_path: Path) -> None:
    """Changes mapped to tests should fail gate when a test lacks requirement marker."""
    tests_dir, changed = _build_minimal_pytest_tree(tmp_path)
    changed_list = tmp_path / "changed.txt"
    changed_list.write_text(f"{changed}\n", encoding="utf-8")
    output = tmp_path / "gate.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-gate",
            "--input-dir",
            str(tests_dir),
            "--changed-file-list",
            str(changed_list),
            "--output",
            str(output),
            "--strict",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert payload["blocked_count"] == 1
    assert payload["blocked"][0]["reason"] == "missing_requirement_marker"


def test_requirements_gate_respects_explicit_exemption(tmp_path: Path) -> None:
    """A matching entry in the exception file should allow an unmarked test."""
    tests_dir, changed = _build_minimal_pytest_tree(tmp_path)
    changed_list = tmp_path / "changed.txt"
    changed_list.write_text(f"{changed}\n", encoding="utf-8")
    exceptions = tmp_path / "exceptions.json"
    exceptions.write_text(
        json.dumps(
            {
                "exemptions": [
                    {
                        "file": f"{tests_dir / 'test_api.py'}",
                        "test": "test_without_requirement",
                        "reason": "legacy coverage debt",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "gate.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-gate",
            "--input-dir",
            str(tests_dir),
            "--changed-file-list",
            str(changed_list),
            "--exceptions",
            str(exceptions),
            "--output",
            str(output),
            "--strict",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["blocked_count"] == 0


def test_pr_targets_accepts_changed_file_list_input(tmp_path: Path) -> None:
    """`pr-targets` should map changed files from list file input."""
    known_test_file = ROOT / "tests" / "test_unit_cli_commands_a.py"
    changed_list = tmp_path / "changed.txt"
    changed_list.write_text(f"{known_test_file}\n", encoding="utf-8")
    targets_output = tmp_path / "targets.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "pr-targets",
            "--changed-file-list",
            str(changed_list),
            "--output",
            str(targets_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(targets_output.read_text(encoding="utf-8"))
    assert payload["fallback_to_fast_lane"] is False
    assert any("test_unit_cli_commands_a.py" in item for item in payload["targets"])


def test_requirements_map_includes_uncovered_requirements(tmp_path: Path) -> None:
    """Mapping output should include uncovered requirement IDs from the FR tracker."""
    tests_dir, _ = _build_minimal_pytest_tree(tmp_path)
    tracker = tmp_path / "FR_TRACKER.md"
    tracker.write_text(
        "| FR-TEST-001 |\n| FR-TEST-002 |\n",
        encoding="utf-8",
    )
    output = tmp_path / "requirements-map.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-map",
            "--input-dir",
            str(tests_dir),
            "--fr-tracker",
            str(tracker),
            "--output",
            str(output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "FR-TEST-001" in payload["requirement_to_tests"]
    assert "FR-TEST-002" in payload["requirement_coverage"]["uncovered_requirements"]


def test_fr_trace_extractor_generates_requirements_map_artifact(tmp_path: Path) -> None:
    """Dedicated FR extractor entrypoint should emit requirements-map/v1 output."""
    tests_dir, _ = _build_minimal_pytest_tree(tmp_path)
    tracker = tmp_path / "FR_TRACKER.md"
    tracker.write_text("| FR-TEST-001 |\n| FR-TEST-002 |\n", encoding="utf-8")
    output = tmp_path / "requirements-map.json"
    csv_output = tmp_path / "requirements-map.csv"
    summary = tmp_path / "requirements-map.md"

    result = subprocess.run(
        [
            sys.executable,
            str(FR_TRACE_EXTRACTOR_SCRIPT),
            "--input-dir",
            str(tests_dir),
            "--fr-tracker",
            str(tracker),
            "--output",
            str(output),
            "--csv-output",
            str(csv_output),
            "--summary",
            str(summary),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "requirements-map/v1"
    assert "FR-TEST-001" in payload["requirement_to_tests"]
    assert payload["requirement_coverage"]["uncovered_requirements"] == ["FR-TEST-002"]
    assert csv_output.exists()
    assert summary.exists()


def test_requirements_map_treats_trace_comments_as_secondary_evidence(
    tmp_path: Path,
) -> None:
    """Trace references without @pytest.mark.requirement are counted in secondary evidence."""
    tests_dir, _ = _build_minimal_pytest_tree(tmp_path)
    tracked_file = tests_dir / "test_trace_secondary.py"
    tracked_file.write_text(
        "from __future__ import annotations\n\n"
        "import pytest\n\n"
        '@pytest.mark.requirement("FR-TRACE-MAIN")\n'
        "def test_marked_trace():\n"
        "    assert True\n\n"
        "# @trace FR-TRACE-ONLY\n"
        "def test_trace_only():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    tracker = tmp_path / "FR_TRACKER.md"
    tracker.write_text(
        "| FR-TRACE-MAIN |\n| FR-TRACE-ONLY |\n",
        encoding="utf-8",
    )

    requirements_output = tmp_path / "requirements-map.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-map",
            "--input-dir",
            str(tests_dir),
            "--fr-tracker",
            str(tracker),
            "--output",
            str(requirements_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(requirements_output.read_text(encoding="utf-8"))
    assert "FR-TRACE-MAIN" in payload["requirement_to_tests"]
    assert "FR-TRACE-ONLY" not in payload["secondary_evidence_coverage"]["uncovered_requirements"]
    assert "FR-TRACE-ONLY" in payload["trace_to_tests"]
    assert any("test_trace_only" in nodeid for nodeid in payload["trace_to_tests"]["FR-TRACE-ONLY"])


def test_untagged_heavy_migration_script_filters_by_loc(tmp_path: Path) -> None:
    """Migration helper should export only tests above the requested source_loc threshold."""
    artifact = tmp_path / "untagged-heavy-tests.json"
    artifact.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "min_loc": 80,
                "count": 2,
                "tests": [
                    {
                        "file": "tests/test_a.py",
                        "nodeid": "tests/test_a.py::test_a",
                        "line": 10,
                        "markers": ["integration"],
                        "source_loc": 120,
                    },
                    {
                        "file": "tests/test_b.py",
                        "nodeid": "tests/test_b.py::test_b",
                        "line": 20,
                        "markers": [],
                        "source_loc": 70,
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "migration.json"

    result = subprocess.run(
        [
            sys.executable,
            str(TRACE_MIGRATION_SCRIPT),
            "--input",
            str(artifact),
            "--output",
            str(output),
            "--min-source-loc",
            "100",
            "--max-count",
            "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["tests"][0]["source_loc"] == 120


def test_pr_template_requires_artifact_links_and_fr_mapping_evidence() -> None:
    """PR template must request artifact links and FR mapping evidence."""
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    assert "## Artifact Links" in text
    assert "## Functional Requirements Mapping" in text
    assert "requirements-map" in text
    assert "FR mapping evidence provided" in text


def test_ci_has_nightly_template_collect_job() -> None:
    """CI workflow should include a nightly template-tree collect-only job."""
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "template-collect-nightly" in text
    assert "task test:collect:templates" in text


def test_benchmark_workflow_has_routing_and_heavy_e2e_jobs() -> None:
    """Benchmark workflow should have routing + heavy e2e jobs with and without xdist."""
    text = BENCHMARK_WORKFLOW.read_text(encoding="utf-8")
    assert "benchmark-routing" in text
    assert "benchmark-routing-xdist" in text
    assert "benchmark-e2e-heavy" in text
    assert "benchmark-e2e-heavy-xdist" in text
    assert "task bench:pytest:routing" in text
    assert "task bench:pytest:routing-xdist" in text
    assert "task bench:pytest:e2e-heavy" in text
    assert "task bench:pytest:e2e-heavy-xdist" in text


def test_taskfile_has_traceability_contract_maintenance_tasks() -> None:
    """Taskfile should expose extraction, promotion, diagram, and cleanup maintenance commands."""
    text = TASKFILE.read_text(encoding="utf-8")
    assert "  test:requirements:map:" in text
    assert "  test:requirements:promotion-criteria:" in text
    assert "  test:requirements:diagram:" in text
    assert "  test:traceability:quarterly-cleanup:" in text


def test_requirements_map_schema_contract_is_stable(tmp_path: Path) -> None:
    """Extractor schema version and core fields should remain stable for consumer contracts."""
    tests_dir, _ = _build_minimal_pytest_tree(tmp_path)
    tracker = tmp_path / "FR_TRACKER.md"
    tracker.write_text("| FR-TEST-001 |\n| FR-TEST-002 |\n", encoding="utf-8")
    requirements_output = tmp_path / "requirements-map.json"
    requirements_diagram = tmp_path / "requirements-map.mdown"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-map",
            "--input-dir",
            str(tests_dir),
            "--fr-tracker",
            str(tracker),
            "--output",
            str(requirements_output),
            "--diagram-output",
            str(requirements_diagram),
            "--diagram-max-nodes",
            "1",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(requirements_output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "requirements-map/v1"
    assert payload["generated_at"]
    assert payload["requirement_to_tests"]
    assert payload["test_to_requirements"]
    assert payload["trace_to_tests"] == {}
    assert payload["test_to_trace_requirements"]
    assert payload["requirement_coverage"]["coverage_ratio"] == 0.5
    assert payload["secondary_evidence_coverage"]["uncovered_requirements"] == [
        "FR-TEST-002",
    ]
    assert requirements_diagram.exists()
    diagram = requirements_diagram.read_text(encoding="utf-8")
    assert "Requirement DAG" in diagram
    assert "flowchart TD" in diagram
    assert "Visible requirements: `1`" in diagram


def test_requirements_promotion_criteria_contract_includes_optional_lane_readiness_fields(
    tmp_path: Path,
) -> None:
    """Promotion criteria payload should include stability, flake, and required optional-run constraints."""
    requirements_map = tmp_path / "requirements-map.json"
    requirements_map.write_text(
        json.dumps(
            {
                "schema_version": "requirements-map/v1",
                "requirement_coverage": {"coverage_ratio": 0.95},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    requirements_gate = tmp_path / "requirements-gate.json"
    requirements_gate.write_text(
        json.dumps({"blocked_count": 0}, indent=2).decode(),
        encoding="utf-8",
    )
    health = tmp_path / "health.json"
    health.write_text(json.dumps({"overall_health_score": 93}, indent=2).decode(), encoding="utf-8")

    run_1 = tmp_path / "run-1.json"
    run_1.write_text(json.dumps({"status": "passed"}, indent=2).decode(), encoding="utf-8")
    run_2 = tmp_path / "run-2.json"
    run_2.write_text(json.dumps({"status": "passed"}, indent=2).decode(), encoding="utf-8")

    criteria_output = tmp_path / "requirements-promotion-criteria.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-promotion-criteria",
            "--requirements-map",
            str(requirements_map),
            "--requirements-gate",
            str(requirements_gate),
            "--health",
            str(health),
            "--min-runs",
            "2",
            "--min-coverage-ratio",
            "0.90",
            "--max-flake-ratio",
            "0.10",
            "--acceptable-fail-budget",
            "0",
            "--run-artifact",
            str(run_1),
            "--run-artifact",
            str(run_2),
            "--output",
            str(criteria_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(criteria_output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "lane-promotion-criteria/v1"
    criteria = payload["criteria"]
    assert criteria["required_stability_ratio"] == 0.9
    assert criteria["required_stable_runs_required"] == 2
    actual = payload["actual"]
    assert actual["coverage_threshold_met"] is True
    assert actual["requirements_gate_blocked"] is True
    assert actual["health_score_threshold_met"] is True
    assert actual["flake_ratio_threshold_met"] is True
    assert payload["recommendation"]["ready_for_lane_promotion"] is True
    assert payload["recommendation"]["make_optional_lanes_required"] is True
    assert payload["flake_gate"]["required_optional_run_count"] == 2

    lane_output = tmp_path / "lane-promotion.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "lane-promotion",
            "--lane",
            "pr",
            "--requirements-map",
            str(requirements_map),
            "--requirements-gate",
            str(requirements_gate),
            "--health",
            str(health),
            "--min-runs",
            "2",
            "--min-coverage-ratio",
            "0.90",
            "--max-flake-ratio",
            "0.10",
            "--acceptable-fail-budget",
            "0",
            "--run-artifact",
            str(run_1),
            "--run-artifact",
            str(run_2),
            "--output",
            str(lane_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    lane_payload = json.loads(lane_output.read_text(encoding="utf-8"))
    assert lane_payload["schema_version"] == "lane-promotion/v1"
    assert lane_payload["recommendation"]["ready_to_require_optional_lanes"] is True
    assert lane_payload["promotion_plan"]["action"] == "promote_optional_lane_to_required"
    assert lane_payload["promotion_plan"]["required"] is True


def test_requirements_diagram_output_respects_max_nodes_and_truncation(
    tmp_path: Path,
) -> None:
    """Diagram command should cap visible FR rows and emit truncation metadata."""
    payload_path = tmp_path / "requirements-map.json"
    payload_path.write_text(
        json.dumps(
            {
                "schema_version": "requirements-map/v1",
                "requirement_to_tests": {
                    f"FR-TEST-{index:03d}": [f"tests/test_{index}.py::test_{index}"] for index in range(1, 7).decode()
                },
                "requirement_coverage": {"coverage_ratio": 1.0},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    diagram_output = tmp_path / "requirements-map.mermaid.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "requirements-diagram",
            "--requirements-map",
            str(payload_path),
            "--output",
            str(diagram_output),
            "--max-nodes",
            "3",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    text = diagram_output.read_text(encoding="utf-8")
    assert "Visible requirements: `3`" in text
    assert "Truncated requirements: `True`" in text
    assert "This diagram is truncated for readability." in text


def test_traceability_quarterly_cleanup_task_creates_issue_contract(
    tmp_path: Path,
) -> None:
    """Quarterly traceability cleanup should emit both debt and cleanup-issue contract payloads."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    stale_test = tests_dir / "test_cleanup.py"
    stale_test.write_text(
        "# @trace FR-OLD-001\ndef test_old_trace_only():\n    assert True\n",
        encoding="utf-8",
    )
    stale_time = datetime.now(UTC).timestamp() - (4 * 24 * 60 * 60)
    os.utime(stale_test, (stale_time, stale_time))

    debt_output = tmp_path / "requirements-cleanup.json"
    issue_output = tmp_path / "requirements-cleanup-issue.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "traceability-cleanup",
            "--input-dir",
            str(tests_dir),
            "--stale-window-days",
            "1",
            "--issue-threshold",
            "0",
            "--issue-output",
            str(issue_output),
            "--output",
            str(debt_output),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    issue_payload = json.loads(issue_output.read_text(encoding="utf-8"))
    assert issue_payload["schema_version"] == "traceability-cleanup-issue/v1"
    assert issue_payload["status"] == "open"
    assert issue_payload["recommended_action"] == "open"
    assert issue_payload["artifact"] == str(debt_output)
    assert issue_payload["stale_window_breach"] is True
    assert issue_payload["deprecated_marker_breach"] is False

    debt_payload = json.loads(debt_output.read_text(encoding="utf-8"))
    assert debt_payload["schema_version"] == "traceability-cleanup/v1"
    assert debt_payload["stale_debt_count"] == 1
    assert debt_payload["quarterly_cleanup_issue"] == "open"
