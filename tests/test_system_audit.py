"""Tests for src/thegent/audit/system_audit.py.

Traces to: FR-AUDIT-001 through FR-AUDIT-020
"""

from __future__ import annotations

import os
import textwrap
from typing import TYPE_CHECKING

import orjson as json
import pytest

from thegent.audit.system_audit import (
    AuditReport,
    AuditResult,
    AuditStatus,
    SystemAuditor,
    _extract_pkg_name,
    _normalize_pkg_name,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Set up a minimal project layout under tmp_path."""
    (tmp_path / "hooks").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"

            [project]
            name = "myproject"
            version = "0.1.0"
            dependencies = [
                "httpx>=0.28.0",
                "pyyaml>=6.0",
            ]
        """),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def auditor(tmp_project: Path) -> SystemAuditor:
    """SystemAuditor pointing at tmp_project."""
    return SystemAuditor(project_root=tmp_project)


# ---------------------------------------------------------------------------
# AuditResult unit tests (FR-AUDIT-001, FR-AUDIT-002)
# ---------------------------------------------------------------------------


def test_audit_result_is_ok_when_ok() -> None:
    """Traces to: FR-AUDIT-001 -- AuditResult.is_ok() returns True for OK status."""
    r = AuditResult(
        category="hooks",
        item="my-hook",
        status=AuditStatus.OK,
        expected="hooks/my-hook.sh",
        actual="hooks/my-hook.sh",
    )
    assert r.is_ok() is True


def test_audit_result_not_ok_for_non_ok_statuses() -> None:
    """Traces to: FR-AUDIT-001 -- AuditResult.is_ok() returns False for all non-OK statuses."""
    for status in AuditStatus:
        if status == AuditStatus.OK:
            continue
        r = AuditResult(
            category="test",
            item="item",
            status=status,
            expected="x",
            actual="y",
        )
        assert r.is_ok() is False, f"Expected False for {status}"


def test_audit_result_to_dict_fields() -> None:
    """Traces to: FR-AUDIT-002 -- AuditResult.to_dict() serializes all fields."""
    r = AuditResult(
        category="config",
        item="debug",
        status=AuditStatus.DRIFT,
        expected="default(False)",
        actual="True",
        fix_suggestion="Unset THGENT_DEBUG",
    )
    d = r.to_dict()
    assert d["category"] == "config"
    assert d["item"] == "debug"
    assert d["status"] == "drift"
    assert d["expected"] == "default(False)"
    assert d["actual"] == "True"
    assert d["fix_suggestion"] == "Unset THGENT_DEBUG"


# ---------------------------------------------------------------------------
# AuditReport unit tests (FR-AUDIT-003, FR-AUDIT-004)
# ---------------------------------------------------------------------------


def test_audit_report_summary_counts() -> None:
    """Traces to: FR-AUDIT-003 -- AuditReport.summary counts per-status."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results(
        [
            AuditResult("hooks", "a", AuditStatus.OK, "x", "x"),
            AuditResult("hooks", "b", AuditStatus.MISSING, "x", "y"),
            AuditResult("config", "c", AuditStatus.DRIFT, "1", "2"),
        ]
    )
    assert report.summary["total"] == 3
    assert report.summary["ok"] == 1
    assert report.summary["missing"] == 1
    assert report.summary["drift"] == 1


def test_audit_report_has_drift_false_when_all_ok() -> None:
    """Traces to: FR-AUDIT-004 -- AuditReport.has_drift is False when all results are OK."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results(
        [
            AuditResult("hooks", "a", AuditStatus.OK, "x", "x"),
            AuditResult("agents", "b", AuditStatus.OK, "y", "y"),
        ]
    )
    assert report.has_drift is False


def test_audit_report_has_drift_true_when_any_issue() -> None:
    """Traces to: FR-AUDIT-004 -- AuditReport.has_drift is True when any non-OK result exists."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results(
        [
            AuditResult("hooks", "a", AuditStatus.OK, "x", "x"),
            AuditResult("hooks", "b", AuditStatus.MISSING, "x", "y"),
        ]
    )
    assert report.has_drift is True


def test_audit_report_to_dict_structure() -> None:
    """Traces to: FR-AUDIT-003 -- AuditReport.to_dict() contains timestamp, summary, results."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results([AuditResult("hooks", "a", AuditStatus.OK, "x", "x")])
    d = report.to_dict()
    assert "timestamp" in d
    assert "summary" in d
    assert "results" in d
    assert isinstance(d["results"], list)


# ---------------------------------------------------------------------------
# audit_hooks tests (FR-AUDIT-005, FR-AUDIT-006, FR-AUDIT-007)
# ---------------------------------------------------------------------------


def test_audit_hooks_missing_config_file(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-005 -- MISSING result when hook-config.yaml absent."""
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_hooks()
    assert len(results) == 1
    assert results[0].status == AuditStatus.MISSING
    assert results[0].item == "hook-config.yaml"


def test_audit_hooks_ok_when_script_present(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-006 -- OK result when declared hook has matching .sh file."""
    hook_cfg = tmp_project / "hooks" / "hook-config.yaml"
    hook_cfg.write_text(
        "hooks:\n  quality-gate:\n    scope: changed\n    timeout: 300\n",
        encoding="utf-8",
    )
    (tmp_project / "hooks" / "quality-gate.sh").write_text("#!/bin/bash\necho ok\n")

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_hooks()
    ok_results = [r for r in results if r.item == "quality-gate"]
    assert len(ok_results) == 1
    assert ok_results[0].status == AuditStatus.OK


def test_audit_hooks_missing_when_script_absent(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-006 -- MISSING result when declared hook has no .sh file."""
    hook_cfg = tmp_project / "hooks" / "hook-config.yaml"
    hook_cfg.write_text(
        "hooks:\n  my-hook:\n    scope: changed\n    timeout: 60\n",
        encoding="utf-8",
    )

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_hooks()
    missing = [r for r in results if r.status == AuditStatus.MISSING]
    assert any(r.item == "my-hook" for r in missing)


def test_audit_hooks_unexpected_unregistered_script(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-007 -- UNEXPECTED result for .sh not in hook-config.yaml."""
    hook_cfg = tmp_project / "hooks" / "hook-config.yaml"
    hook_cfg.write_text("hooks: {}\n", encoding="utf-8")
    (tmp_project / "hooks" / "orphan-hook.sh").write_text("#!/bin/bash\n")

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_hooks()
    unexpected = [r for r in results if r.status == AuditStatus.UNEXPECTED]
    assert any(r.item == "orphan-hook" for r in unexpected)


def test_audit_hooks_fix_suggestion_populated_for_missing(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-006 -- fix_suggestion is non-empty for MISSING hook."""
    hook_cfg = tmp_project / "hooks" / "hook-config.yaml"
    hook_cfg.write_text("hooks:\n  missing-hook:\n    timeout: 30\n", encoding="utf-8")

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_hooks()
    missing = next(r for r in results if r.status == AuditStatus.MISSING and r.item == "missing-hook")
    assert missing.fix_suggestion != ""


# ---------------------------------------------------------------------------
# audit_agents tests (FR-AUDIT-008, FR-AUDIT-009, FR-AUDIT-010)
# ---------------------------------------------------------------------------


def test_audit_agents_missing_agents_dir(tmp_path: Path) -> None:
    """Traces to: FR-AUDIT-008 -- MISSING result when agents/ directory absent."""
    auditor = SystemAuditor(project_root=tmp_path)
    results = auditor.audit_agents()
    assert len(results) == 1
    assert results[0].status == AuditStatus.MISSING
    assert results[0].item == "agents/"


def test_audit_agents_ok_for_nonempty_md_file(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-009 -- OK result for a non-empty agent .md file."""
    (tmp_project / "agents" / "my-agent.md").write_text("# My Agent\nA capable persona.\n", encoding="utf-8")
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_agents()
    ok_results = [r for r in results if r.item == "my-agent" and r.status == AuditStatus.OK]
    assert len(ok_results) == 1


def test_audit_agents_warn_for_empty_md_file(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-009 -- WARN result for empty agent .md file."""
    (tmp_project / "agents" / "empty-agent.md").write_text("", encoding="utf-8")
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_agents()
    warn = [r for r in results if r.status == AuditStatus.WARN]
    assert any(r.item == "empty-agent" for r in warn)


def test_audit_agents_missing_when_referenced_in_bounded_contexts(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-010 -- MISSING when bounded-contexts.yaml references absent agent."""
    # Need at least one real .md file so the function doesn't exit early with WARN
    (tmp_project / "agents" / "real-agent.md").write_text("# Real Agent\nA working persona.\n", encoding="utf-8")
    (tmp_project / "agents" / "bounded-contexts.yaml").write_text("agents:\n  - nonexistent-agent\n", encoding="utf-8")
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_agents()
    missing = [r for r in results if r.status == AuditStatus.MISSING]
    assert any(r.item == "nonexistent-agent" for r in missing)


def test_audit_agents_warn_when_empty_directory(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-008 -- WARN when agents/ dir exists but has no .md files."""
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_agents()
    assert any(r.status == AuditStatus.WARN for r in results)


# ---------------------------------------------------------------------------
# audit_config tests (FR-AUDIT-011, FR-AUDIT-012)
# ---------------------------------------------------------------------------


def test_audit_config_returns_results_for_all_fields(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Traces to: FR-AUDIT-011 -- audit_config returns at least one result per known field."""
    # Ensure no stray THGENT_ vars from test env bleed in
    for key in list(os.environ.keys()):
        if key.startswith("THGENT_"):
            monkeypatch.delenv(key, raising=False)

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_config()
    # ThegentSettings has many fields; we expect a substantial list
    assert len(results) >= 10


def test_audit_config_ok_for_set_env_var(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Traces to: FR-AUDIT-012 -- OK result when a THGENT_* env var is explicitly set."""
    monkeypatch.setenv("THGENT_DEBUG", "0")
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_config()
    debug_results = [r for r in results if r.item == "debug"]
    assert len(debug_results) == 1
    assert debug_results[0].status == AuditStatus.OK
    assert "THGENT_DEBUG" in debug_results[0].expected or "THGENT_DEBUG" in debug_results[0].actual


def test_audit_config_unexpected_unknown_env_var(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Traces to: FR-AUDIT-012 -- UNEXPECTED result for unknown THGENT_* env var."""
    monkeypatch.setenv("THGENT_TOTALLY_UNKNOWN_XYZ", "value")
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_config()
    unexpected = [r for r in results if r.status == AuditStatus.UNEXPECTED]
    assert any(r.item == "THGENT_TOTALLY_UNKNOWN_XYZ" for r in unexpected)


# ---------------------------------------------------------------------------
# audit_dependencies tests (FR-AUDIT-013, FR-AUDIT-014, FR-AUDIT-015)
# ---------------------------------------------------------------------------


def test_audit_dependencies_missing_pyproject(tmp_path: Path) -> None:
    """Traces to: FR-AUDIT-013 -- MISSING result when pyproject.toml absent."""
    auditor = SystemAuditor(project_root=tmp_path)
    results = auditor.audit_dependencies()
    assert len(results) == 1
    assert results[0].status == AuditStatus.MISSING
    assert results[0].item == "pyproject.toml"


def test_audit_dependencies_ok_for_installed_package(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-014 -- OK result for a package that is actually installed.

    httpx and pyyaml are project dependencies guaranteed to be installed.
    """
    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_dependencies()
    # httpx and pyyaml should be installed in this env
    items = {r.item: r for r in results}
    assert "httpx" in items, "httpx should be in audit results"
    assert items["httpx"].status == AuditStatus.OK


def test_audit_dependencies_missing_for_uninstalled_package(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-015 -- MISSING result for package not installed."""
    # Add a fake package that certainly is not installed
    pyproject = tmp_project / "pyproject.toml"
    content = pyproject.read_text()
    content = content.replace(
        '"pyyaml>=6.0",',
        '"pyyaml>=6.0",\n    "thegent-fake-package-xyz>=99.0",',
    )
    pyproject.write_text(content, encoding="utf-8")

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_dependencies()
    missing = [r for r in results if r.status == AuditStatus.MISSING]
    assert any(r.item == "thegent-fake-package-xyz" for r in missing)


def test_audit_dependencies_fix_suggestion_for_missing(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-015 -- fix_suggestion populated for MISSING dependency."""
    pyproject = tmp_project / "pyproject.toml"
    content = pyproject.read_text()
    content = content.replace(
        '"httpx>=0.28.0",',
        '"thegent-not-real-pkg>=1.0",',
    )
    pyproject.write_text(content, encoding="utf-8")

    auditor = SystemAuditor(project_root=tmp_project)
    results = auditor.audit_dependencies()
    missing = next(r for r in results if r.item == "thegent-not-real-pkg")
    assert "pip install" in missing.fix_suggestion


# ---------------------------------------------------------------------------
# run_full_audit tests (FR-AUDIT-016, FR-AUDIT-017)
# ---------------------------------------------------------------------------


def test_run_full_audit_returns_report_with_all_categories(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-016 -- run_full_audit returns results covering all 4 categories."""
    # Add a hook entry so hooks category produces at least one result
    hook_cfg = tmp_project / "hooks" / "hook-config.yaml"
    hook_cfg.write_text(
        "hooks:\n  quality-gate:\n    scope: changed\n    timeout: 300\n",
        encoding="utf-8",
    )
    # quality-gate.sh is absent intentionally so we get a MISSING hooks result

    auditor = SystemAuditor(project_root=tmp_project)
    report = auditor.run_full_audit()

    categories = {r.category for r in report.results}
    assert "hooks" in categories
    assert "agents" in categories
    assert "config" in categories
    assert "dependencies" in categories


def test_run_full_audit_summary_total_matches_results(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-017 -- summary['total'] matches len(results)."""
    auditor = SystemAuditor(project_root=tmp_project)
    report = auditor.run_full_audit()
    assert report.summary["total"] == len(report.results)


def test_run_full_audit_timestamp_is_iso_string(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-016 -- AuditReport timestamp is a non-empty ISO 8601 string."""
    auditor = SystemAuditor(project_root=tmp_project)
    report = auditor.run_full_audit()
    assert report.timestamp
    assert "T" in report.timestamp  # basic ISO 8601 marker


# ---------------------------------------------------------------------------
# format_report tests (FR-AUDIT-018)
# ---------------------------------------------------------------------------


def test_format_report_contains_category_headers(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-018 -- format_report output contains category headers."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results(
        [
            AuditResult("hooks", "a", AuditStatus.OK, "x", "x"),
            AuditResult("agents", "b", AuditStatus.MISSING, "y", "z", "fix it"),
        ]
    )
    auditor = SystemAuditor(project_root=tmp_project)
    text = auditor.format_report(report)
    assert "[HOOKS]" in text
    assert "[AGENTS]" in text


def test_format_report_shows_fix_suggestion_for_issues(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-018 -- format_report includes fix_suggestion for non-OK results."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results(
        [
            AuditResult("hooks", "missing-hook", AuditStatus.MISSING, "x", "y", "Create hooks/missing-hook.sh"),
        ]
    )
    auditor = SystemAuditor(project_root=tmp_project)
    text = auditor.format_report(report)
    assert "Create hooks/missing-hook.sh" in text


def test_format_report_summary_line_present(tmp_project: Path) -> None:
    """Traces to: FR-AUDIT-018 -- format_report includes Total/OK/Issues summary line."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results([AuditResult("config", "x", AuditStatus.OK, "a", "a")])
    auditor = SystemAuditor(project_root=tmp_project)
    text = auditor.format_report(report)
    assert "Total:" in text
    assert "OK:" in text


# ---------------------------------------------------------------------------
# export_json tests (FR-AUDIT-019)
# ---------------------------------------------------------------------------


def test_export_json_writes_valid_json(tmp_project: Path, tmp_path: Path) -> None:
    """Traces to: FR-AUDIT-019 -- export_json writes valid, parseable JSON."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    report.add_results([AuditResult("hooks", "a", AuditStatus.OK, "x", "x")])

    auditor = SystemAuditor(project_root=tmp_project)
    out_path = tmp_path / "report.json"
    auditor.export_json(report, out_path)

    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert "timestamp" in data
    assert "results" in data
    assert "summary" in data


def test_export_json_creates_parent_directories(tmp_project: Path, tmp_path: Path) -> None:
    """Traces to: FR-AUDIT-019 -- export_json creates missing parent directories."""
    report = AuditReport(timestamp="2026-01-01T00:00:00+00:00")
    out_path = tmp_path / "nested" / "deep" / "report.json"
    auditor = SystemAuditor(project_root=tmp_project)
    auditor.export_json(report, out_path)
    assert out_path.exists()


# ---------------------------------------------------------------------------
# Internal utility tests (FR-AUDIT-020)
# ---------------------------------------------------------------------------


def test_normalize_pkg_name_lowercases_and_normalizes() -> None:
    """Traces to: FR-AUDIT-020 -- _normalize_pkg_name applies PEP 503 normalization."""
    assert _normalize_pkg_name("PyYAML") == "pyyaml"
    assert _normalize_pkg_name("Pillow") == "pillow"
    assert _normalize_pkg_name("my_package") == "my-package"
    assert _normalize_pkg_name("my.package") == "my-package"
    assert _normalize_pkg_name("my--package") == "my-package"


def test_extract_pkg_name_strips_specifiers() -> None:
    """Traces to: FR-AUDIT-020 -- _extract_pkg_name strips version specifiers and extras."""
    assert _extract_pkg_name("httpx>=0.28.1") == "httpx"
    assert _extract_pkg_name("pydantic[email]>=2.0") == "pydantic"
    assert _extract_pkg_name("orjson; implementation_name == 'cpython'") == "orjson"
    assert _extract_pkg_name("rich") == "rich"
    assert _extract_pkg_name("tenacity==9.0.0") == "tenacity"
    assert _extract_pkg_name("ujson; implementation_name == 'pypy'") == "ujson"
