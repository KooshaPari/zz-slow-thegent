"""Unit tests for remaining uncovered lines in cli.py.

Targets specific branches, error paths, serialization helpers, and display
formatting code that tests_a and tests_b do not exercise.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import click.exceptions
import orjson as json
import pytest
import typer

from thegent.cli.commands.impl import DagDocument

_EXIT = (SystemExit, click.exceptions.Exit)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_settings(**overrides):
    defaults = {
        "session_dir": Path("/tmp/thegent-test-sessions"),
        "environment": "development",
        "trust_score_threshold": 0.7,
        "override_ttl_seconds": 300,
        "output_format": "rich",
        "default_routing": "prefer_direct",
        "default_antigravity_model": "gemini-3-pro-high",
        "cursor_api_url": "http://localhost:8080",
        "retention_days_sessions": 30,
    }
    defaults.update(overrides)
    s = MagicMock()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_dag_doc(tasks=None, headers=None):
    return DagDocument(
        frontmatter={"version": "1", "project": "test", "owner": "ci"},
        tasks=tasks or [],
        before_table="# DAG Session\n\n## Tasks\n\n",
        after_table="",
        table_headers=headers or ["id", "agent", "prompt", "depends_on", "status"],
    )


def _health_gate_result(**overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_gate",
        "status": "pass",
        "pass": True,
        "healthy_ratio": 1.0,
        "threshold": 1.0,
        "healthy_count": 5,
        "unhealthy_count": 0,
        "blocked_count": 0,
        "total": 5,
        "total_sessions": 5,
        "healthy_sessions": 5,
        "unhealthy_sessions": 0,
        "blocked_sessions": [],
        "blocked_sessions_count": 0,
        "blocked_ratio": 0.0,
        "top_blocked_count": 0,
        "blocked_sessions_cap": 25,
        "strict_checks_enabled": False,
        "generated_at_utc": "2025-01-01T00:00:00Z",
        "generated_query": {
            "owner": "ci",
            "all": False,
            "strict": False,
            "min_healthy_ratio": 1.0,
        },
        "summary": {"health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0}},
        "decision_reasons": [],
    }
    base.update(overrides)
    return base


def _health_report_result(**overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_report",
        "status": "pass",
        "pass": True,
        "total": 5,
        "total_sessions": 5,
        "healthy_sessions": 5,
        "unhealthy_sessions": 0,
        "blocked_sessions": 0,
        "blocked_sessions_count": 0,
        "blocked_count": 0,
        "blocked_ratio": 0.0,
        "top_blocked_count": 0,
        "health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0},
        "strict_checks_enabled": False,
        "issue_breakdown": [],
        "owner_breakdown": {},
        "top_blocked": [],
        "healthy_count": 5,
        "unhealthy_count": 0,
    }
    base.update(overrides)
    return base


def _health_trend_result(**overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_trend",
        "trend_payload_type": "session_contract_health_trend",
        "snapshot_count": 2,
        "limit": 20,
        "scope_key": {"owner": "ci", "payload_type": "session_contract_health_report"},
        "delta_summary": {"blocked_ratio_delta": 0.0, "blocked_count_delta": 0},
        "latest": {
            "status": "pass",
            "pass": True,
            "captured_at_utc": "2025-01-01T00:00:00Z",
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_types": [],
        },
        "snapshots": [],
        "generated_at_utc": "2025-01-01T00:00:00Z",
    }
    base.update(overrides)
    return base


# ============================================================================
# sweep_cmd  (lines 496, 513)
# ============================================================================


@pytest.mark.unit
class TestSweepCmdBranches:
    """Cover audit-present and audit-status branches in sweep_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="json")
    @patch("thegent.cli.commands.impl.sweep_impl")
    def test_sweep_json_with_audit(self, mock_impl, mock_fmt, mock_console) -> None:
        # @trace FR-GOV-001
        mock_impl.return_value = {
            "pass": True,
            "drift_issues": [],
            "past_sla_count": 0,
            "audit": {"status": "passed", "details": "ok"},
        }
        from thegent.cli import sweep_cmd

        sweep_cmd(drift_window=50, include_audit=True, format="json")

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli.commands.impl.sweep_impl")
    def test_sweep_rich_audit_failed_status(
        self, mock_impl, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-002
        mock_impl.return_value = {
            "pass": False,
            "drift_issues": ["drift1"],
            "past_sla_count": 1,
            "audit": {"status": "failed"},
        }
        from thegent.cli import sweep_cmd

        with pytest.raises(_EXIT):
            sweep_cmd(drift_window=50, include_audit=True, format=None)
        # A Panel is printed when there are parts (drift_issues + audit)
        mock_console.print.assert_called()


# ============================================================================
# contracts_registry_cmd  (lines 576-588)
# ============================================================================


@pytest.mark.unit
class TestContractsRegistryCmdRich:
    """Cover the rich table branch for contracts_registry_cmd."""

    def test_registry_rich_format(self) -> None:
        # @trace FR-CLI-400
        mock_version = MagicMock()
        mock_version.contract_id = "c1"
        mock_version.version = "1.0"
        mock_version.description = "Test contract"
        mock_version.deprecated = False
        mock_version.migration_window_end = "2025-12-31"
        mock_registry = MagicMock()
        mock_registry.list_versions.return_value = [mock_version]
        mock_local_console = MagicMock()
        with (
            patch(
                "thegent.contracts.registry.get_registry", return_value=mock_registry
            ),
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            from thegent.cli import contracts_registry_cmd

            contracts_registry_cmd(format=None)
        mock_local_console.print.assert_called()

    def test_registry_deprecated(self) -> None:
        # @trace FR-CLI-401
        mock_version = MagicMock()
        mock_version.contract_id = "c1"
        mock_version.version = "0.9"
        mock_version.description = "Old"
        mock_version.deprecated = True
        mock_version.migration_window_end = None
        mock_registry = MagicMock()
        mock_registry.list_versions.return_value = [mock_version]
        mock_local_console = MagicMock()
        with (
            patch(
                "thegent.contracts.registry.get_registry", return_value=mock_registry
            ),
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            from thegent.cli import contracts_registry_cmd

            contracts_registry_cmd(format=None)


# ============================================================================
# migration_cmd  (lines 606-618)
# ============================================================================


@pytest.mark.unit
class TestMigrationCmdRich:
    """Cover the rich panel branch of migration_cmd."""

    def test_migration_allowed(self) -> None:
        # @trace FR-CLI-402
        mock_local_console = MagicMock()
        with (
            patch("thegent.contracts.migration.MigrationController") as MockMC,
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            mc = MockMC.return_value
            mc.evaluate_version.return_value = {
                "allowed": True,
                "status": "active",
                "reason": "ok",
                "migration_days_left": 90,
            }
            from thegent.cli import migration_cmd

            migration_cmd(contract_id="c1", version="1.0", format=None)
        mock_local_console.print.assert_called()

    def test_migration_deprecated(self) -> None:
        # @trace FR-CLI-403
        mock_local_console = MagicMock()
        with (
            patch("thegent.contracts.migration.MigrationController") as MockMC,
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            mc = MockMC.return_value
            mc.evaluate_version.return_value = {
                "allowed": False,
                "status": "deprecated",
                "reason": "too old",
            }
            from thegent.cli import migration_cmd

            migration_cmd(contract_id="c1", version="0.5", format=None)


# ============================================================================
# drift_cmd  (lines 651-669)
# ============================================================================


@pytest.mark.unit
class TestDriftCmdBranches:
    """Cover the drift-issues and budget-exceeded panel branch."""

    def test_drift_issues_and_budget_exceeded(self) -> None:
        # @trace FR-GOV-003
        import sys

        mock_list_mod = MagicMock()
        sys.modules["rich.list"] = mock_list_mod
        try:
            mock_local_console = MagicMock()
            mock_ct = MagicMock()
            mock_ct.detect_drift.return_value = ["issue1"]
            mock_ct.get_drift_budget_status.return_value = {
                "within_budget": False,
                "structural_rate_pct": 10.0,
                "structural_budget_pct": 5.0,
                "semantic_rate_pct": 8.0,
                "semantic_budget_pct": 5.0,
            }
            with (
                patch("thegent.cli.ThegentSettings", return_value=_mock_settings()),
                patch(
                    "thegent.contracts.telemetry.ContractTelemetry",
                    return_value=mock_ct,
                ),
                patch("rich.console.Console", return_value=mock_local_console),
            ):
                from thegent.cli import drift_cmd

                drift_cmd(
                    window=50, format=None, structural_budget=5.0, semantic_budget=5.0
                )
            mock_local_console.print.assert_called()
        finally:
            sys.modules.pop("rich.list", None)


# ============================================================================
# observe_summary_cmd  (lines 700-755)
# ============================================================================


@pytest.mark.unit
class TestObserveSummaryCmdRich:
    """Cover the rich panel rendering branch of observe_summary_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_observe_summary_rich_full(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-CLI-404
        result = {
            "kpis": {
                "total_events": 100,
                "fallback_rate": 0.05,
                "success_rate": 0.95,
                "avg_confidence": 0.9,
            },
            "drift": {
                "structural_rate_pct": 2.0,
                "structural_budget_pct": 5.0,
                "semantic_rate_pct": 1.0,
                "semantic_budget_pct": 5.0,
                "within_budget": True,
                "issues": ["minor drift"],
            },
            "escalation": {
                "backlog_count": 2,
                "past_sla_count": 1,
                "top_escalations": [
                    {
                        "run_id": "r1",
                        "owner": "alice",
                        "agent": "claude",
                        "lane": "standard",
                        "past_sla": True,
                        "minutes_overdue": 10,
                        "minutes_remaining": None,
                        "priority": 3,
                    },
                    {
                        "run_id": "r2",
                        "owner": None,
                        "agent": "gemini",
                        "lane": "fast",
                        "past_sla": False,
                        "minutes_remaining": 5,
                        "priority": 1,
                    },
                    {
                        "run_id": "r3",
                        "owner": "bob",
                        "agent": "codex",
                        "lane": "slow",
                        "past_sla": False,
                        "minutes_remaining": None,
                        "priority": 0,
                    },
                ],
            },
            "alerts": ["high fallback rate"],
            "status": "critical",
            "trend_summary": {
                "enabled": True,
                "trend_samples_requested": 5,
                "trend_effective_samples": 3,
                "history_sample_count": 10,
                "baseline_available": True,
                "trend_snapshot_health": "healthy",
            },
            "generated_query": {"owner": "ci"},
        }
        with patch(
            "thegent.cli.commands.observability_impl.observe_summary_impl",
            return_value=result,
        ):
            from thegent.cli import observe_summary_cmd

            observe_summary_cmd(limit=100, drift_window=50, format=None, provider=None)
        assert mock_console.print.called


# ============================================================================
# contracts_conformance_cmd  (lines 764-805)
# ============================================================================


@pytest.mark.unit
class TestContractsConformanceCmdRich:
    """Cover rich table + drift alarm branches of conformance cmd."""

    def test_conformance_rich_with_drift(self) -> None:
        # @trace FR-CLI-405
        report = {
            "passed": 3,
            "failed": 1,
            "total": 4,
            "results": [
                {
                    "name": "test1",
                    "provider": "claude",
                    "success": True,
                    "confidence": 0.95,
                    "issues": [],
                },
                {
                    "name": "test2",
                    "provider": "gemini",
                    "success": False,
                    "confidence": 0.5,
                    "issues": ["timeout"],
                },
            ],
            "drift_checked": True,
            "drift_issues": ["structural drift detected"],
        }
        mock_local_console = MagicMock()
        with (
            patch(
                "thegent.contracts.conformance.run_conformance_suite",
                return_value=report,
            ),
            patch("thegent.cli.ThegentSettings", return_value=_mock_settings()),
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            from thegent.cli import contracts_conformance_cmd

            with pytest.raises(_EXIT):
                contracts_conformance_cmd(
                    format=None, check_drift=True, drift_window=50
                )

    def test_conformance_json_with_failures(self) -> None:
        # @trace FR-CLI-406
        report = {
            "passed": 2,
            "failed": 1,
            "total": 3,
            "results": [],
            "drift_issues": [],
        }
        mock_local_console = MagicMock()
        with (
            patch(
                "thegent.contracts.conformance.run_conformance_suite",
                return_value=report,
            ),
            patch("thegent.cli.ThegentSettings", return_value=_mock_settings()),
            patch("rich.console.Console", return_value=mock_local_console),
        ):
            from thegent.cli import contracts_conformance_cmd

            with pytest.raises(_EXIT):
                contracts_conformance_cmd(
                    format="json", check_drift=False, drift_window=50
                )


# ============================================================================
# cockpit_cmd  (lines 858-862)
# ============================================================================


@pytest.mark.unit
class TestCockpitCmdBranches:
    """Cover the recent_errors display branch in cockpit_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.Columns")
    @patch("thegent.cli.Panel")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_cockpit_with_recent_errors(
        self, mock_settings, mock_panel, mock_cols, mock_console
    ) -> None:
        # @trace FR-CLI-407
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [
            {"status": "failed", "run_id": "r1", "policy_reason": "blocked"},
            {"status": "failed", "run_id": "r2", "error_class": "TimeoutError"},
        ]
        mock_cb = MagicMock()
        mock_cb.is_open.return_value = False
        mock_ckpt = MagicMock()
        mock_ckpt.list_checkpoints.return_value = []
        with (
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
            patch("thegent.execution.CircuitBreakerRegistry", return_value=mock_cb),
            patch("thegent.execution.CheckpointRegistry", return_value=mock_ckpt),
            patch("thegent.cli.commands.impl.ps_impl", return_value=[]),
        ):
            from thegent.cli import cockpit_cmd

            cockpit_cmd()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "r1" in printed


# ============================================================================
# ps_cmd  (lines 896-898, 907-910, 990)
# ============================================================================


@pytest.mark.unit
class TestPsCmdBranches:
    """Cover md format with include_contract and missing_only branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_ps_md_with_contract(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-CLI-408
        rows = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "ci",
                "pid": 1234,
                "status": "running",
                "prompt_preview": "hello",
                "route_request": {"model": "claude-sonnet"},
                "route_contract": {"provider": "claude"},
            },
        ]
        with patch("thegent.cli.commands.impl.ps_impl", return_value=rows):
            from thegent.cli import ps_cmd

            ps_cmd(all_sessions=False, owner=None, format="md", include_contract=True)
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "route_request" in printed or "claude" in printed


# ============================================================================
# session_contracts_cmd  (lines 990, 997-1034, 1046-1082)
# ============================================================================


@pytest.mark.unit
class TestSessionContractAuditCmdBranches:
    """Cover md format, rich table, missing_only, and summary_only branches."""

    def _audit_result(self, rows=None, summary=None):
        return {
            "rows": rows or [],
            "summary": summary
            or {
                "complete": 3,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 1,
                "total": 5,
                "health": {"healthy": 3, "warning": 1, "error": 0, "missing": 1},
                "strict_checks_enabled": False,
            },
        }

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_no_rows_missing_only(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-004
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl",
            return_value=self._audit_result(),
        ):
            from thegent.cli import session_contracts_cmd

            session_contracts_cmd(
                all_sessions=False,
                owner=None,
                format=None,
                missing_only=True,
                summary_only=False,
                strict=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "No contract gaps" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_md_summary_only(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-005
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl",
            return_value=self._audit_result(),
        ):
            from thegent.cli import session_contracts_cmd

            session_contracts_cmd(
                all_sessions=False,
                owner=None,
                format="md",
                missing_only=False,
                summary_only=True,
                strict=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "summary" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_md_with_rows(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-006
        rows = [
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "ci",
                "status": "running",
                "contract_state": "complete",
                "contract_health": "healthy",
                "requested_model": "claude-sonnet",
                "requested_provider_hint": "claude",
                "resolved_model_alias": "sonnet",
                "policy": "prefer_direct",
                "contract_issues": [],
            },
        ]
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl",
            return_value=self._audit_result(rows=rows),
        ):
            from thegent.cli import session_contracts_cmd

            session_contracts_cmd(
                all_sessions=False,
                owner=None,
                format="md",
                missing_only=False,
                summary_only=False,
                strict=False,
            )

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_rich_table_with_rows(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-007
        rows = [
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "ci",
                "status": "running",
                "contract_state": "complete",
                "contract_health": "healthy",
                "requested_model": "claude-sonnet",
                "requested_provider_hint": "claude",
                "resolved_model_alias": "sonnet",
                "policy": "prefer_direct",
                "contract_issues": ["stale_contract"],
            },
        ]
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl",
            return_value=self._audit_result(rows=rows),
        ):
            from thegent.cli import session_contracts_cmd

            session_contracts_cmd(
                all_sessions=False,
                owner=None,
                format=None,
                missing_only=False,
                summary_only=False,
                strict=False,
            )


# ============================================================================
# session_contract_health_gate_cmd  (lines 1112-1125, 1131, 1134-1135, 1141, 1156-1157)
# ============================================================================


@pytest.mark.unit
class TestHealthGateCmdBranches:
    """Cover md format, payload_signature, decision_reasons, trend_summary."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_gate_md_format(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-008
        result = _health_gate_result()
        with patch(
            "thegent.cli.commands.impl.session_contract_health_gate_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_gate_cmd

            session_contract_health_gate_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                format="md",
                min_healthy_ratio=1.0,
                policy_profile=None,
                output=None,
                export_format=None,
                overwrite=False,
            )

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_gate_rich_with_signature_and_trend(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-009
        result = _health_gate_result(
            payload_signature={"algorithm": "sha256", "value": "abc123"},
            decision_reasons=["healthy_ratio_above_threshold"],
            trend_summary={
                "baseline_available": True,
                "blocked_ratio_delta": -0.1,
                "blocked_count_delta": -2,
            },
        )
        with patch(
            "thegent.cli.commands.impl.session_contract_health_gate_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_gate_cmd

            session_contract_health_gate_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                format=None,
                min_healthy_ratio=1.0,
                policy_profile=None,
                output=None,
                export_format=None,
                overwrite=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "payload_signature" in printed
        assert "trend" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_gate_with_export(
        self, mock_settings, mock_owner, mock_fmt, mock_console, tmp_path
    ) -> None:
        # @trace FR-GOV-010
        result = _health_gate_result()
        out_file = tmp_path / "gate.json"
        with (
            patch(
                "thegent.cli.commands.impl.session_contract_health_gate_impl",
                return_value=result,
            ),
            patch(
                "thegent.cli._write_health_gate_export", return_value="json"
            ) as mock_export,
        ):
            from thegent.cli import session_contract_health_gate_cmd

            session_contract_health_gate_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                format=None,
                min_healthy_ratio=1.0,
                policy_profile=None,
                output=out_file,
                export_format="json",
                overwrite=False,
            )
        mock_export.assert_called_once()


# ============================================================================
# _write_report_export  (lines 1688-1706)
# ============================================================================


@pytest.mark.unit
class TestWriteReportExport:
    """Cover md, csv, jsonl branches + cleanup in _write_report_export."""

    def test_md_format(self, tmp_path) -> None:
        # @trace FR-CLI-409
        from thegent.cli import _write_report_export

        result = _health_report_result(
            generated_at_utc="2025-01-01T00:00:00Z",
            generated_query={"owner": "ci"},
        )
        out = tmp_path / "report.md"
        fmt = _write_report_export(out, result, "md", overwrite=False)
        assert fmt == "md"
        assert out.exists()

    def test_csv_format(self, tmp_path) -> None:
        # @trace FR-CLI-410
        from thegent.cli import _write_report_export

        result = _health_report_result(
            generated_at_utc="2025-01-01T00:00:00Z",
            generated_query={"owner": "ci"},
        )
        out = tmp_path / "report.csv"
        fmt = _write_report_export(out, result, "csv", overwrite=False)
        assert fmt == "csv"

    def test_jsonl_format(self, tmp_path) -> None:
        # @trace FR-CLI-411
        from thegent.cli import _write_report_export

        result = _health_report_result(
            generated_at_utc="2025-01-01T00:00:00Z",
            generated_query={"owner": "ci"},
        )
        out = tmp_path / "report.jsonl"
        fmt = _write_report_export(out, result, "jsonl", overwrite=False)
        assert fmt == "jsonl"

    def test_existing_dir_error(self, tmp_path) -> None:
        # @trace FR-CLI-412
        from thegent.cli import _write_report_export

        out = tmp_path / "dir_output"
        out.mkdir()
        with pytest.raises(typer.BadParameter, match="directory"):
            _write_report_export(out, {}, "json", overwrite=False)

    def test_existing_file_no_overwrite(self, tmp_path) -> None:
        # @trace FR-CLI-413
        from thegent.cli import _write_report_export

        out = tmp_path / "report.json"
        out.write_text("{}")
        with pytest.raises(typer.BadParameter, match="already exists"):
            _write_report_export(out, {}, "json", overwrite=False)


# ============================================================================
# _write_health_gate_export  (lines 1725, 1727, 1733-1734, 1736, 1738, 1748)
# ============================================================================


@pytest.mark.unit
class TestWriteHealthGateExport:
    """Cover all format branches in _write_health_gate_export."""

    def test_md_format(self, tmp_path) -> None:
        # @trace FR-CLI-414
        from thegent.cli import _write_health_gate_export

        result = _health_gate_result()
        out = tmp_path / "gate.md"
        fmt = _write_health_gate_export(out, result, "md", overwrite=False)
        assert fmt == "md"
        assert out.exists()

    def test_csv_format(self, tmp_path) -> None:
        # @trace FR-CLI-415
        from thegent.cli import _write_health_gate_export

        result = _health_gate_result()
        out = tmp_path / "gate.csv"
        fmt = _write_health_gate_export(out, result, "csv", overwrite=False)
        assert fmt == "csv"

    def test_jsonl_format(self, tmp_path) -> None:
        # @trace FR-CLI-416
        from thegent.cli import _write_health_gate_export

        result = _health_gate_result()
        out = tmp_path / "gate.jsonl"
        fmt = _write_health_gate_export(out, result, "jsonl", overwrite=False)
        assert fmt == "jsonl"

    def test_existing_dir_error(self, tmp_path) -> None:
        # @trace FR-CLI-417
        from thegent.cli import _write_health_gate_export

        out = tmp_path / "dir_output"
        out.mkdir()
        with pytest.raises(typer.BadParameter, match="directory"):
            _write_health_gate_export(out, {}, "json", overwrite=False)

    def test_existing_file_no_overwrite(self, tmp_path) -> None:
        # @trace FR-CLI-418
        from thegent.cli import _write_health_gate_export

        out = tmp_path / "gate.json"
        out.write_text("{}")
        with pytest.raises(typer.BadParameter, match="already exists"):
            _write_health_gate_export(out, {}, "json", overwrite=False)


# ============================================================================
# _write_health_trend_export  (lines 2422-2437)
# ============================================================================


@pytest.mark.unit
class TestWriteHealthTrendExport:
    """Cover all format branches in _write_health_trend_export."""

    def test_md_format(self, tmp_path) -> None:
        # @trace FR-CLI-419
        from thegent.cli import _write_health_trend_export

        result = _health_trend_result()
        out = tmp_path / "trend.md"
        fmt = _write_health_trend_export(out, result, "md", overwrite=False)
        assert fmt == "md"
        assert out.exists()

    def test_csv_format(self, tmp_path) -> None:
        # @trace FR-CLI-420
        from thegent.cli import _write_health_trend_export

        result = _health_trend_result()
        out = tmp_path / "trend.csv"
        fmt = _write_health_trend_export(out, result, "csv", overwrite=False)
        assert fmt == "csv"

    def test_jsonl_format(self, tmp_path) -> None:
        # @trace FR-CLI-421
        from thegent.cli import _write_health_trend_export

        result = _health_trend_result()
        out = tmp_path / "trend.jsonl"
        fmt = _write_health_trend_export(out, result, "jsonl", overwrite=False)
        assert fmt == "jsonl"

    def test_json_default(self, tmp_path) -> None:
        # @trace FR-CLI-422
        from thegent.cli import _write_health_trend_export

        result = _health_trend_result()
        out = tmp_path / "trend.json"
        fmt = _write_health_trend_export(out, result, "json", overwrite=False)
        assert fmt == "json"
        content = json.loads(out.read_text())
        assert content["schema_version"] == "3.0"


# ============================================================================
# session_contract_health_report_cmd  (lines 2471, 2487, 2492-2513, 2525-2529)
# ============================================================================


@pytest.mark.unit
class TestHealthReportCmdBranches:
    """Cover md format, signature, decision_reasons, trend_summary, top_blocked."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_report_md_format(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-011
        result = _health_report_result()
        with patch(
            "thegent.cli.commands.impl.session_contract_health_report_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                top_blocked=25,
                policy_profile=None,
                no_worse_than_baseline=False,
                regression_tolerance=0.0,
                format="md",
                output=None,
                export_format=None,
                overwrite=False,
            )

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_report_rich_with_signature_trend_blocked(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-012
        result = _health_report_result(
            payload_signature={"algorithm": "sha256", "value": "abc"},
            decision_reasons=["some_reason"],
            generated_at_utc="2025-01-01T00:00:00Z",
            generated_query={"owner": "ci"},
            trend_summary={
                "baseline_available": True,
                "blocked_ratio_delta": 0.0,
                "blocked_count_delta": 0,
            },
            top_blocked=[
                {
                    "session_id": "s1",
                    "owner": "ci",
                    "health": "error",
                    "issues": ["stale_contract"],
                    "remediation": ["refresh"],
                },
            ],
        )
        with patch(
            "thegent.cli.commands.impl.session_contract_health_report_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                top_blocked=25,
                policy_profile=None,
                no_worse_than_baseline=False,
                regression_tolerance=0.0,
                format=None,
                output=None,
                export_format=None,
                overwrite=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "payload_signature" in printed
        assert "trend" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_report_unrecognized_export_suffix(
        self, mock_settings, mock_owner, mock_fmt, mock_console, tmp_path
    ) -> None:
        # @trace FR-GOV-013
        result = _health_report_result()
        out_file = tmp_path / "report.xyz"
        with (
            patch(
                "thegent.cli.commands.impl.session_contract_health_report_impl",
                return_value=result,
            ),
            patch("thegent.cli._write_report_export", return_value="json"),
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(
                all_sessions=False,
                owner=None,
                strict=False,
                top_blocked=25,
                policy_profile=None,
                no_worse_than_baseline=False,
                regression_tolerance=0.0,
                format=None,
                output=out_file,
                export_format=None,
                overwrite=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "not recognized" in printed


# ============================================================================
# session_contract_health_trend_cmd  (lines 2564-2577, 2582)
# ============================================================================


@pytest.mark.unit
class TestHealthTrendCmdBranches:
    """Cover export, md, and unrecognized suffix branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_trend_md_format(
        self, mock_settings, mock_owner, mock_fmt, mock_console
    ) -> None:
        # @trace FR-GOV-014
        result = _health_trend_result()
        with patch(
            "thegent.cli.commands.impl.session_contract_health_trend_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_trend_cmd

            session_contract_health_trend_cmd(
                payload_type="session_contract_health_report",
                all_sessions=False,
                owner=None,
                strict=False,
                policy_profile=None,
                min_healthy_ratio=1.0,
                top_blocked=25,
                limit=20,
                format="md",
                output=None,
                export_format=None,
                overwrite=False,
            )

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._default_owner_tag", return_value="ci:proj")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_trend_with_export_and_unrecognized_suffix(
        self, mock_settings, mock_owner, mock_fmt, mock_console, tmp_path
    ) -> None:
        # @trace FR-GOV-015
        result = _health_trend_result()
        out_file = tmp_path / "trend.xyz"
        with (
            patch(
                "thegent.cli.commands.impl.session_contract_health_trend_impl",
                return_value=result,
            ),
            patch("thegent.cli._write_health_trend_export", return_value="json"),
        ):
            from thegent.cli import session_contract_health_trend_cmd

            session_contract_health_trend_cmd(
                payload_type="session_contract_health_report",
                all_sessions=False,
                owner=None,
                strict=False,
                policy_profile=None,
                min_healthy_ratio=1.0,
                top_blocked=25,
                limit=20,
                format=None,
                output=out_file,
                export_format=None,
                overwrite=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "not recognized" in printed


# ============================================================================
# dag_validate_cmd freshness check (lines 2639-2646)
# ============================================================================


@pytest.mark.unit
class TestDagValidateFreshness:
    """Cover the state freshness warning branch in dag_validate_cmd."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._validate_dag", return_value=[])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_freshness_warning(
        self, mock_console, mock_cwd, mock_parse, mock_validate, mock_settings, tmp_path
    ) -> None:
        # @trace FR-GOV-016
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.write_text("# DAG")
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")
        mock_ckpt_registry = MagicMock()
        mock_ckpt_registry.list_checkpoints.return_value = [
            {"checkpoint_id": "ckpt-1", "created_at_utc": "2020-01-01T00:00:00+00:00"},
        ]
        with patch(
            "thegent.execution.CheckpointRegistry", return_value=mock_ckpt_registry
        ):
            from thegent.cli import dag_validate_cmd

            dag_validate_cmd(cd=None)
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "modified since last checkpoint" in printed


# ============================================================================
# dag_list_cmd  (lines 2671, 2679-2687) - json with tasks, rich table
# ============================================================================


@pytest.mark.unit
class TestDagListCmdRichTable:
    """Cover the rich Table branch in dag_list_cmd."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_list_rich_table(
        self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-423
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [
            {
                "id": "T1",
                "agent": "claude",
                "prompt": "hello",
                "depends_on": "-",
                "status": "pending",
            },
        ]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_list_cmd

        dag_list_cmd(cd=None, format="rich")
        assert mock_console.print.called

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_list_json_with_tasks(
        self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-424
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [
            {
                "id": "T1",
                "agent": "claude",
                "prompt": "hello",
                "depends_on": "-",
                "status": "done",
            }
        ]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "json"

        from thegent.cli import dag_list_cmd

        dag_list_cmd(cd=None, format="json")


# ============================================================================
# dag_add_cmd  (lines 2743-2755, 2748-2749) - depends_on validation + contract_version + cycles
# ============================================================================


@pytest.mark.unit
class TestDagAddCmdDepsBranch:
    """Cover depends_on not-found, contract_version, and cycle detection."""

    @patch("thegent.cli._ensure_dag_file")
    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_depends_on_not_found(
        self, mock_console, mock_cwd, mock_vtid, mock_vagent, mock_ensure, tmp_path
    ) -> None:
        # @trace FR-CLI-425
        dag_dir = tmp_path / ".factory"
        dag_dir.mkdir(parents=True)
        mock_cwd.return_value = tmp_path
        mock_ensure.return_value = _make_dag_doc()

        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(
                task_id="T1", agent="claude", prompt="test", depends_on="NONEXIST"
            )

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="ser")
    @patch("thegent.cli._check_dag_cycles", return_value=["Cycle: T1 -> T2 -> T1"])
    @patch("thegent.cli._ensure_dag_file")
    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_cycle_detected(
        self,
        mock_console,
        mock_cwd,
        mock_vtid,
        mock_vagent,
        mock_ensure,
        mock_cycles,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-426
        dag_dir = tmp_path / ".factory"
        dag_dir.mkdir(parents=True)
        mock_cwd.return_value = tmp_path
        mock_ensure.return_value = _make_dag_doc()

        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="T2", agent="claude", prompt="test")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="ser")
    @patch("thegent.cli._check_dag_cycles", return_value=[])
    @patch("thegent.cli._ensure_contract_version_header")
    @patch("thegent.cli._ensure_dag_file")
    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_contract_version_header(
        self,
        mock_console,
        mock_cwd,
        mock_vtid,
        mock_vagent,
        mock_ensure,
        mock_cv_header,
        mock_cycles,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-427
        dag_dir = tmp_path / ".factory"
        dag_dir.mkdir(parents=True)
        mock_cwd.return_value = tmp_path
        mock_ensure.return_value = _make_dag_doc()

        from thegent.cli import dag_add_cmd

        dag_add_cmd(task_id="T1", agent="claude", prompt="test", contract_version="2.0")
        mock_cv_header.assert_called_once()


# ============================================================================
# dag_remove_cmd  (lines 2767-2768) - DAG not found
# ============================================================================


@pytest.mark.unit
class TestDagRemoveCmdNotFound:
    """Cover DAG file not found branch."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-428
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_remove_cmd

        with pytest.raises(_EXIT):
            dag_remove_cmd(task_id="T1")


# ============================================================================
# dag_status_cmd  (lines 2796-2797, 2818-2831) - DAG not found + md/rich
# ============================================================================


@pytest.mark.unit
class TestDagStatusCmdBranches:
    """Cover DAG not found, md format, and rich table branches."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-429
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_status_cmd

        with pytest.raises(_EXIT):
            dag_status_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._session_status_for", return_value="running")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_md_format(
        self, mock_console, mock_cwd, mock_parse, mock_status, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-430
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [{"id": "T1", "status": "running", "session_id": "sess-1"}]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_status_cmd

        dag_status_cmd(cd=None, format="md")
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "T1" in printed

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._session_status_for", return_value="exited:0")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rich_table(
        self, mock_console, mock_cwd, mock_parse, mock_status, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-431
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [{"id": "T1", "status": "running", "session_id": "sess-1"}]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_status_cmd

        dag_status_cmd(cd=None, format="rich")


# ============================================================================
# dag_update_cmd  (lines 2852-2881) - invalid agent, depends_on, cycle, _dag_update_task false
# ============================================================================


@pytest.mark.unit
class TestDagUpdateCmdBranches:
    """Cover error branches: invalid agent, depends_on not found, cycle, update fails."""

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_invalid_agent(self, mock_console, mock_cwd, mock_parse, tmp_path) -> None:
        # @trace FR-CLI-432
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        with patch("thegent.cli._validate_agent", return_value="invalid agent chars"):
            from thegent.cli import dag_update_cmd

            with pytest.raises(_EXIT):
                dag_update_cmd(task_id="T1", agent="@bad@")

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_depends_on_not_found(
        self, mock_console, mock_cwd, mock_parse, tmp_path
    ) -> None:
        # @trace FR-CLI-433
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1", depends_on="NONEXIST")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="ser")
    @patch("thegent.cli._check_dag_cycles", return_value=["Cycle detected"])
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_cycle_detected_on_update(
        self,
        mock_console,
        mock_cwd,
        mock_parse,
        mock_upd,
        mock_cycles,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-434
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1", status="done")

    @patch("thegent.cli._dag_update_task", return_value=False)
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_update_task_returns_false(
        self, mock_console, mock_cwd, mock_parse, mock_upd, tmp_path
    ) -> None:
        # @trace FR-CLI-435
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1", session_id="s1")


# ============================================================================
# _parse_depends_on  (line 2890)
# ============================================================================


@pytest.mark.unit
class TestParseDependsOn:
    """Cover the _parse_depends_on helper."""

    def test_empty_string(self) -> None:
        # @trace FR-CLI-436
        from thegent.cli import _parse_depends_on

        assert _parse_depends_on("") == []
        assert _parse_depends_on("—") == []
        assert _parse_depends_on("-") == []

    def test_multiple_deps(self) -> None:
        # @trace FR-CLI-437
        from thegent.cli import _parse_depends_on

        result = _parse_depends_on("T1, T2, T3")
        assert result == ["T1", "T2", "T3"]

    def test_mixed_with_dash(self) -> None:
        # @trace FR-CLI-438
        from thegent.cli import _parse_depends_on

        result = _parse_depends_on("T1, —, T2")
        assert result == ["T1", "T2"]


# ============================================================================
# dag_ready_cmd  (lines 2904-2905, 2917-2937)
# ============================================================================


@pytest.mark.unit
class TestDagReadyCmdBranches:
    """Cover DAG not found, md format, and rich table branches."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-439
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_ready_cmd

        with pytest.raises(_EXIT):
            dag_ready_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_md_format(
        self, mock_console, mock_cwd, mock_parse, mock_ready, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-440
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [
            {
                "id": "T1",
                "agent": "claude",
                "prompt": "hello world this is a long prompt",
            }
        ]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_ready_cmd

        dag_ready_cmd(cd=None, format="md")
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "T1" in printed

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rich_table(
        self, mock_console, mock_cwd, mock_parse, mock_ready, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-441
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [{"id": "T1", "agent": "claude", "prompt": "hello"}]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_ready_cmd

        dag_ready_cmd(cd=None, format="rich")


# ============================================================================
# dag_reconcile_cmd  (lines 2948-2949, 2972-2975)
# ============================================================================


@pytest.mark.unit
class TestDagReconcileCmdBranches:
    """Cover DAG not found and exception-in-status branches."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-442
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_reconcile_cmd

        with pytest.raises(_EXIT):
            dag_reconcile_cmd(cd=None)

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="ser")
    @patch("thegent.cli._session_status_for", side_effect=Exception("not found"))
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_exception_in_session_status(
        self,
        mock_console,
        mock_cwd,
        mock_settings,
        mock_parse,
        mock_status,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-443
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")
        mock_parse.return_value = _make_dag_doc(
            tasks=[{"id": "T1", "status": "running", "session_id": "sess-1"}],
        )
        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=None)


# ============================================================================
# plan_analyze_cmd  (lines 3011-3012, 3024, 3071-3089)
# ============================================================================


@pytest.mark.unit
class TestPlanAnalyzeCmdBranches:
    """Cover DAG not found, empty task id skip, and rich output branches."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-444
        mock_cwd.return_value = tmp_path
        from thegent.cli import plan_analyze_cmd

        with pytest.raises(_EXIT):
            plan_analyze_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rich_pert_and_continuity(
        self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-445
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {"id": "T1", "depends_on": "-", "status": "pending"},
                {"id": "", "depends_on": "-", "status": "pending"},
            ],
        )
        mock_pert_result = MagicMock()
        mock_pert_result.expected_duration = 1.0
        mock_pert_result.variance = 0.1
        mock_pert_result.confidence_p50 = 1.0
        mock_pert_result.confidence_p90 = 1.5
        mock_continuity = MagicMock()
        mock_continuity.risk_score = 0.3
        mock_continuity.factors = ["factor1"]
        mock_continuity.recommendations = ["rec1"]
        mock_continuity.high_risk_tasks = []
        with (
            patch(
                "thegent.planning.simulation.pert_forward_pass",
                return_value={"T1": mock_pert_result},
            ),
            patch("thegent.planning.simulation.simulate_resource_contention"),
            patch(
                "thegent.planning.simulation.score_continuity_risk",
                return_value=mock_continuity,
            ),
        ):
            from thegent.cli import plan_analyze_cmd

            plan_analyze_cmd(
                cd=None, pert=True, resources=False, continuity=True, format=None
            )


# ============================================================================
# archive_cmd  (lines 3116-3121, 3133-3138)
# ============================================================================


@pytest.mark.unit
class TestArchiveCmdBranches:
    """Cover cold tier and domain-filter branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings")
    def test_cold_tier(self, mock_settings, mock_console, tmp_path) -> None:
        # @trace FR-CLI-446
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        archive_dir = session_dir / "archive"
        archive_dir.mkdir()
        old_dir = archive_dir / "old-session"
        old_dir.mkdir()
        import os
        import time as _time

        old_ts = _time.time() - (400 * 86400)
        os.utime(old_dir, (old_ts, old_ts))
        mock_settings.return_value.session_dir = str(session_dir)
        mock_settings.return_value.retention_days_sessions = 30

        from thegent.cli import archive_cmd

        archive_cmd(days=365, domain=None, tier="cold")
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "cold storage" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings")
    def test_hot_tier_with_domain_filter(
        self, mock_settings, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-447
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        old_dir = session_dir / "project-alpha-sess1"
        old_dir.mkdir()
        import os
        import time as _time

        old_ts = _time.time() - (60 * 86400)
        os.utime(old_dir, (old_ts, old_ts))
        mock_settings.return_value.session_dir = str(session_dir)
        mock_settings.return_value.retention_days_sessions = 30

        from thegent.cli import archive_cmd

        archive_cmd(days=30, domain="project-alpha", tier=None)
        assert (session_dir / "archive" / "project-alpha-sess1").exists()


# ============================================================================
# operations_cmd  (lines 3150-3180)
# ============================================================================


@pytest.mark.unit
class TestOperationsCmdBranches:
    """Cover unknown operation and rich table branches."""

    @patch("thegent.cli.console")
    def test_unknown_operation(self, mock_console) -> None:
        # @trace FR-CLI-448
        from thegent.cli import operations_cmd

        with pytest.raises(_EXIT):
            operations_cmd(format=None, operation="nonexistent_op")

    @patch("thegent.cli.console")
    def test_rich_table(self, mock_console) -> None:
        # @trace FR-CLI-449
        mock_entry = MagicMock()
        mock_entry.command = "thegent run"
        mock_entry.description = "Run a task"
        mock_entry.mcp_tool = "run"
        with patch(
            "thegent.operations.list_operations",
            return_value={
                "orchestrate": [
                    {"command": "thegent run", "description": "Run", "mcp_tool": "run"}
                ]
            },
        ):
            from thegent.cli import operations_cmd

            operations_cmd(format=None, operation=None)


# ============================================================================
# modes_cmd  (lines 3188-3215)
# ============================================================================


@pytest.mark.unit
class TestModesCmdBranches:
    """Cover unknown mode and rich table branches."""

    @patch("thegent.cli.console")
    def test_unknown_mode(self, mock_console) -> None:
        # @trace FR-CLI-450
        with patch("thegent.orchestration_modes.get_mode", return_value=None):
            from thegent.cli import modes_cmd

            with pytest.raises(_EXIT):
                modes_cmd(format=None, mode="nonexistent_mode")

    @patch("thegent.cli.console")
    def test_rich_table_all_modes(self, mock_console) -> None:
        # @trace FR-CLI-451
        modes_data = [
            {
                "mode": "sequential_delegation",
                "description": "Sequential delegation of tasks to agents",
                "phases": ["plan", "execute", "review"],
                "use_case": "Simple tasks",
                "risk_profile": "low",
                "selection_hint": "default",
            },
        ]
        with patch("thegent.orchestration_modes.list_modes", return_value=modes_data):
            from thegent.cli import modes_cmd

            modes_cmd(format=None, mode=None)


# ============================================================================
# benchmark_cmd  (lines 3261-3274)
# ============================================================================


@pytest.mark.unit
class TestBenchmarkCmdBranches:
    """Cover contract telemetry branch in benchmark_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_benchmark_with_telemetry(self, mock_settings, mock_console) -> None:
        # @trace FR-CLI-452
        runs = [
            {"status": "completed", "duration_seconds": 10},
            {"status": "failed", "error_class": "TimeoutError"},
        ]
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = runs
        mock_tel = MagicMock()
        mock_tel.get_stats.return_value = {
            "total": 50,
            "success_rate": 0.9,
            "fallback_rate": 0.05,
            "by_provider": {"claude": 0.95},
        }
        with (
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
            patch(
                "thegent.contracts.telemetry.ContractTelemetry", return_value=mock_tel
            ),
            patch(
                "thegent.contracts.telemetry.detect_drift", return_value=["drift issue"]
            ),
        ):
            from thegent.cli import benchmark_cmd

            benchmark_cmd()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "DRIFT DETECTED" in printed


# ============================================================================
# closure_pack_cmd  (lines 3285-3286)
# ============================================================================


@pytest.mark.unit
class TestClosurePackCmdBranches:
    """Cover DAG not found branch."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-453
        mock_cwd.return_value = tmp_path
        from thegent.cli import closure_pack_cmd

        with pytest.raises(_EXIT):
            closure_pack_cmd(cd=None)


# ============================================================================
# dag_run_cmd  (lines 3397-3428, 3457-3462, 3475, 3508, 3511-3512, 3528-3529)
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdBranches:
    """Cover DAG not found, task not ready, max_parallel, low confidence, missing agent."""

    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(
        self, mock_console, mock_cwd, mock_reconcile, tmp_path
    ) -> None:
        # @trace FR-CLI-454
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_run_cmd

        with pytest.raises(_EXIT):
            dag_run_cmd(cd=tmp_path, dry_run=False)

    @patch("thegent.cli._get_ready_task_ids", return_value=["T2"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_task_not_ready(
        self, mock_console, mock_cwd, mock_reconcile, mock_parse, mock_ready, tmp_path
    ) -> None:
        # @trace FR-CLI-455
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                }
            ],
        )
        from thegent.cli import dag_run_cmd

        with pytest.raises(_EXIT):
            dag_run_cmd(cd=tmp_path, task="T1", dry_run=False)

    @patch("thegent.cli._get_ready_task_ids", return_value=["T1", "T2"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_max_parallel_reached(
        self, mock_console, mock_cwd, mock_reconcile, mock_parse, mock_ready, tmp_path
    ) -> None:
        # @trace FR-CLI-456
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T0",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                },
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "y",
                    "depends_on": "-",
                    "status": "pending",
                },
                {
                    "id": "T2",
                    "agent": "claude",
                    "prompt": "z",
                    "depends_on": "-",
                    "status": "pending",
                },
            ],
        )
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, max_parallel=1, dry_run=False)
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "Max parallel" in printed


# ============================================================================
# dag_sync_cmd  (lines 3548-3549, 3555-3558, 3565, 3592-3593)
# ============================================================================


@pytest.mark.unit
class TestDagSyncCmdBranches:
    """Cover DAG not found and quorum logic branches."""

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-457
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_sync_cmd

        with pytest.raises(_EXIT):
            dag_sync_cmd(cd=None)


# ============================================================================
# dag_recover_cmd  (lines 3690-3701, 3709)
# ============================================================================


@pytest.mark.unit
class TestDagRecoverCmdBranches:
    """Cover fallback and no-changes branches."""

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="ser")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_fallback_action(
        self, mock_console, mock_cwd, mock_parse, mock_ser, mock_write, tmp_path
    ) -> None:
        # @trace FR-CLI-458
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "failed",
                }
            ],
        )
        with patch(
            "thegent.agents.registry.get_fallback_agents", return_value=["gemini"]
        ):
            from thegent.cli import dag_recover_cmd

            dag_recover_cmd(cd=None, action="fallback")
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "gemini" in printed

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_fallback_no_fallbacks(
        self, mock_console, mock_cwd, mock_parse, tmp_path
    ) -> None:
        # @trace FR-CLI-459
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "failed",
                }
            ],
        )
        with patch("thegent.agents.registry.get_fallback_agents", return_value=[]):
            from thegent.cli import dag_recover_cmd

            dag_recover_cmd(cd=None, action="fallback")
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "No failed tasks" in printed or "No changes" in printed


# ============================================================================
# dag_probe_cmd  (lines 3732-3733)
# ============================================================================


@pytest.mark.unit
class TestDagProbeCmdBranches:
    """Cover baseline not found branch."""

    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_baseline_not_found(
        self, mock_console, mock_cwd, mock_settings, tmp_path
    ) -> None:
        # @trace FR-CLI-460
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = [{"checkpoint_id": "ckpt-1"}]
        mock_registry.get_checkpoint.return_value = None
        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_probe_cmd

            with pytest.raises(_EXIT):
                dag_probe_cmd(cd=None, baseline_id=None)


# ============================================================================
# status_cmd  (lines 3788-3789, 3791)
# ============================================================================


@pytest.mark.unit
class TestStatusCmdBranches:
    """Cover include_contract rich display branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli._resolve_session_status", return_value="running")
    @patch("thegent.cli._is_pid_running", return_value=True)
    @patch("thegent.cli._read_session_meta")
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_rich_with_contract(
        self,
        mock_settings,
        mock_find,
        mock_paths,
        mock_meta,
        mock_pid,
        mock_status,
        mock_fmt,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-461
        mock_find.return_value = tmp_path / "meta.json"
        mock_paths.return_value = {
            "rc": tmp_path / "rc",
            "stdout": tmp_path / "out",
            "stderr": tmp_path / "err",
        }
        mock_meta.return_value = {
            "pid": 1234,
            "owner": "ci",
            "host": "localhost",
            "agent": "claude",
            "mode": "write",
            "cwd": "/tmp",
            "started_at_utc": "2025-01-01",
            "ended_at_utc": None,
            "duration_seconds": None,
            "timed_out": False,
            "paths": {},
            "route_contract": {"provider": "claude"},
            "route_request": {"model": "sonnet"},
        }
        from thegent.cli import status_cmd

        status_cmd(session_id="s1", format="rich", include_contract=True)
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "route_contract" in printed


# ============================================================================
# inspect_cmd  (lines 3824, 3831-3832)
# ============================================================================


@pytest.mark.unit
class TestInspectCmdBranches:
    """Cover rich status display and logs error branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    def test_rich_status_and_logs_error(self, mock_fmt, mock_console) -> None:
        # @trace FR-CLI-462
        with (
            patch(
                "thegent.cli.commands.impl.status_impl",
                return_value={"status": "running"},
            ),
            patch(
                "thegent.cli.commands.impl.logs_impl", side_effect=Exception("no log")
            ),
            patch("thegent.cli.commands.impl.ps_impl"),
        ):
            from thegent.cli import inspect_cmd

            inspect_cmd(
                session_ids=["s1"],
                owner=None,
                tail=50,
                stderr=False,
                format="rich",
                include_contract=False,
            )
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "running" in printed
        assert "logs error" in printed


# ============================================================================
# logs_cmd  (lines 3861, 3867-3876, 3879, 3882-3892)
# ============================================================================


@pytest.mark.unit
class TestLogsCmdBranches:
    """Cover follow mode branches: timeout, file disappear, truncated, idle exit."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._is_pid_running", return_value=False)
    @patch("thegent.cli._read_session_meta", return_value={"pid": 1234})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_follow_timeout_with_dead_process(
        self,
        mock_settings,
        mock_find,
        mock_paths,
        mock_meta,
        mock_pid,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-463
        log_file = tmp_path / "stdout.log"
        log_file.write_text("line1\nline2\n")
        mock_find.return_value = tmp_path / "meta.json"
        mock_paths.return_value = {
            "rc": tmp_path / "rc",
            "stdout": log_file,
            "stderr": tmp_path / "err",
        }

        # end_time = time.time() + timeout => 0 + 1 = 1
        # In the while loop: time.time() >= end_time => 100 >= 1 => True
        # not running => True; pos >= size => True => raises Exit
        with patch("thegent.cli.time") as mock_time:
            mock_time.time.side_effect = [0, 100]
            mock_time.sleep = MagicMock()
            with patch("thegent.cli.get_exit_message", return_value="timed out"):
                from thegent.cli import logs_cmd

                with pytest.raises(_EXIT):
                    logs_cmd(
                        session_id="s1", follow=True, stderr=False, tail=200, timeout=1
                    )

    @patch("thegent.cli.console")
    @patch("thegent.cli._read_session_meta", return_value={"pid": 1234})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_follow_no_timeout_process_dead(
        self, mock_settings, mock_find, mock_paths, mock_meta, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-464
        log_file = tmp_path / "stdout.log"
        log_file.write_text("line1\n")
        mock_find.return_value = tmp_path / "meta.json"
        mock_paths.return_value = {
            "rc": tmp_path / "rc",
            "stdout": log_file,
            "stderr": tmp_path / "err",
        }

        call_count = [0]

        def fake_is_pid_running(pid):
            call_count[0] += 1
            return call_count[0] < 2

        with (
            patch("thegent.cli._is_pid_running", side_effect=fake_is_pid_running),
            patch("thegent.cli.time") as mock_time,
        ):
            mock_time.time.return_value = 0
            mock_time.sleep = MagicMock()
            from thegent.cli import logs_cmd

            logs_cmd(session_id="s1", follow=True, stderr=False, tail=200, timeout=0)


# ============================================================================
# wait_cmd  (lines 3920, 3922)
# ============================================================================


@pytest.mark.unit
class TestWaitCmdBranches:
    """Cover timeout branch in wait_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._read_session_meta", return_value={"pid": 99999})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_wait_timeout(
        self, mock_settings, mock_find, mock_paths, mock_meta, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-465
        mock_find.return_value = tmp_path / "meta.json"
        rc_file = tmp_path / "rc"
        mock_paths.return_value = {
            "rc": rc_file,
            "stdout": tmp_path / "out",
            "stderr": tmp_path / "err",
        }

        import time as real_time

        call_count = [0]

        def fake_is_pid_running(pid) -> bool:
            call_count[0] += 1
            return True

        real_time.time()
        with (
            patch("thegent.cli._is_pid_running", side_effect=fake_is_pid_running),
            patch("thegent.cli.time") as mock_time,
            patch("thegent.cli.get_exit_message", return_value="timed out"),
        ):
            mock_time.time.side_effect = [0, 0, 100]
            mock_time.sleep = MagicMock()
            from thegent.cli import wait_cmd

            with pytest.raises(_EXIT):
                wait_cmd(session_id="s1", timeout=1)


# ============================================================================
# escalate_inspect_cmd  (lines 4003-4005)
# ============================================================================


@pytest.mark.unit
class TestResumeCmdBranches:
    """Cover the fallback run_id lookup from correlation_id in resume_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli._read_session_meta")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_run_id_from_correlation(
        self, mock_settings, mock_meta, mock_find, mock_console
    ) -> None:
        # @trace FR-GOV-017
        mock_find.return_value = Path("/tmp/meta.json")
        mock_meta.return_value = {"run_id": None}
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [
            {"run_id": "run-1", "correlation_id": "sess-1"},
        ]
        with patch("thegent.cli.RunRegistry", return_value=mock_registry):
            from thegent.cli import resume_cmd

            resume_cmd(session_id="sess-1")


# ============================================================================
# list_models_cmd  (lines 4053, 4072-4091)
# ============================================================================


@pytest.mark.unit
class TestListModelsCmdBranches:
    """Cover provider-specific model listing branches."""

    @patch("thegent.cli.console")
    def test_list_minimax_models(self, mock_console) -> None:
        # @trace FR-CLI-466
        with patch("thegent.cli._list_minimax_models") as mock_mm:
            from thegent.cli import list_models_cmd

            list_models_cmd(
                provider="minimax",
                refresh=False,
                include_contract=False,
                by_model=False,
            )
        mock_mm.assert_called_once()

    @patch("thegent.cli.console")
    def test_list_all_providers(self, mock_console) -> None:
        # @trace FR-CLI-467
        with (
            patch("thegent.cli._list_minimax_models") as m1,
            patch("thegent.cli._list_glm_models") as m2,
            patch("thegent.cli._list_cursor_models") as m3,
            patch("thegent.cli._list_cursor_api_models") as m4,
            patch("thegent.cli._list_gemini_models") as m5,
            patch("thegent.cli._list_copilot_models") as m6,
            patch("thegent.cli._list_claude_models") as m7,
            patch("thegent.cli._list_codex_models") as m8,
            patch("thegent.cli._list_antigravity_models") as m9,
        ):
            from thegent.cli import list_models_cmd

            list_models_cmd(
                provider=None, refresh=False, include_contract=False, by_model=False
            )
        for m in [m1, m2, m3, m4, m5, m6, m7, m8, m9]:
            m.assert_called_once()

    @patch("thegent.cli.console")
    def test_list_models_with_refresh(self, mock_console) -> None:
        # @trace FR-CLI-468
        with (
            patch("thegent.models.scrapers.get_scraped_catalog") as mock_scrape,
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.to_contract_view.return_value = {"models": []}
            from thegent.cli import list_models_cmd

            list_models_cmd(
                provider=None, refresh=True, include_contract=True, by_model=False
            )
        mock_scrape.assert_called_once_with(refresh=True)


# ============================================================================
# resolve_model_route_cmd  (lines 4100-4147)
# ============================================================================


@pytest.mark.unit
class TestResolveModelRouteCmdBranches:
    """Cover route found, no route, and invalid policy branches."""

    @patch("thegent.cli.console")
    def test_route_found(self, mock_console) -> None:
        # @trace FR-CLI-469
        mock_route = MagicMock()
        mock_route.provider = "claude"
        mock_route.model_alias = "sonnet"
        mock_route.backend_type = "direct"
        mock_route.priority = 1
        mock_route.schema_version = "3.0"
        with (
            patch(
                "thegent.models.normalize_route_policy", return_value="prefer_direct"
            ),
            patch(
                "thegent.models.normalize_model_id", return_value="claude-sonnet-4-5"
            ),
            patch("thegent.models.resolve_route_contract", return_value=mock_route),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route]
            from thegent.cli import resolve_model_route_cmd

            resolve_model_route_cmd(
                model="claude-sonnet-4-5", provider="claude", policy="prefer_direct"
            )

    @patch("thegent.cli.console")
    def test_no_route_with_available(self, mock_console) -> None:
        # @trace FR-CLI-470
        mock_route = MagicMock()
        mock_route.provider = "gemini"
        mock_route.backend_type = "proxy"
        mock_route.model_alias = "flash"
        mock_route.priority = 2
        with (
            patch(
                "thegent.models.normalize_route_policy", return_value="prefer_direct"
            ),
            patch("thegent.models.normalize_model_id", return_value="gemini-3-flash"),
            patch("thegent.models.resolve_route_contract", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route]
            from thegent.cli import resolve_model_route_cmd

            with pytest.raises(_EXIT):
                resolve_model_route_cmd(
                    model="gemini-3-flash", provider="claude", policy="prefer_direct"
                )

    @patch("thegent.cli.console")
    def test_invalid_policy(self, mock_console) -> None:
        # @trace FR-CLI-471
        with patch(
            "thegent.models.normalize_route_policy", side_effect=ValueError("bad")
        ):
            from thegent.cli import resolve_model_route_cmd

            with pytest.raises(_EXIT):
                resolve_model_route_cmd(
                    model="test", provider=None, policy="bad_policy"
                )


# ============================================================================
# list_model_contract_schema_cmd  (lines 4152-4154)
# ============================================================================


@pytest.mark.unit
class TestListModelContractSchemaCmd:
    """Cover the schema display command."""

    @patch("thegent.cli.console")
    def test_prints_schema(self, mock_console) -> None:
        # @trace FR-CLI-472
        with patch("thegent.models.route_contract", return_value={"version": "3.0"}):
            from thegent.cli import list_model_contract_schema_cmd

            list_model_contract_schema_cmd()
        mock_console.print_json.assert_called_once()


# ============================================================================
# _list_cursor_models  (line 4187)
# ============================================================================


@pytest.mark.unit
class TestListCursorModelsBranches:
    """Cover failure branch of _list_cursor_models."""

    @patch("thegent.cli.console")
    def test_cursor_failed(self, mock_console) -> None:
        # @trace FR-CLI-473
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        with patch("thegent.cli.subprocess.run", return_value=mock_proc):
            from thegent.cli import _list_cursor_models

            _list_cursor_models()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "failed" in printed


# ============================================================================
# _list_cursor_api_models  (lines 4194-4204)
# ============================================================================


@pytest.mark.unit
class TestListCursorApiModelsBranches:
    """Cover the cursor-api model listing."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_models_found(self, mock_settings, mock_console) -> None:
        # @trace FR-CLI-474
        with patch(
            "thegent.models.scrapers.scrape_cursor_api",
            return_value=["model-a", "model-b"],
        ):
            from thegent.cli import _list_cursor_api_models

            _list_cursor_api_models()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "model-a" in printed

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_no_models(self, mock_settings, mock_console) -> None:
        # @trace FR-CLI-475
        with patch("thegent.models.scrapers.scrape_cursor_api", return_value=[]):
            from thegent.cli import _list_cursor_api_models

            _list_cursor_api_models()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "not reachable" in printed


# ============================================================================
# _list_copilot_models  (lines 4218-4241)
# ============================================================================


@pytest.mark.unit
class TestListCopilotModelsBranches:
    """Cover copilot help parsing and fallback branches."""

    @patch("thegent.cli.console")
    def test_copilot_with_model_choices(self, mock_console) -> None:
        # @trace FR-CLI-476
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = (
            '--model choices: "claude-haiku-4.5" "gpt-4" "gemini-3-flash"'
        )
        with patch("thegent.cli.subprocess.run", return_value=mock_proc):
            from thegent.cli import _list_copilot_models

            _list_copilot_models()

    @patch("thegent.cli.console")
    def test_copilot_no_model_flag(self, mock_console) -> None:
        # @trace FR-CLI-477
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "No model flag here"
        with (
            patch("thegent.cli.subprocess.run", return_value=mock_proc),
            patch("thegent.cli._list_copilot_models_fallback"),
        ):
            from thegent.cli import _list_copilot_models

            _list_copilot_models()

    @patch("thegent.cli.console")
    def test_copilot_not_found(self, mock_console) -> None:
        # @trace FR-CLI-478
        with (
            patch("thegent.cli.subprocess.run", side_effect=FileNotFoundError),
            patch("thegent.cli._list_copilot_models_fallback"),
        ):
            from thegent.cli import _list_copilot_models

            _list_copilot_models()


# ============================================================================
# _list_codex_models  (lines 4262-4279)
# ============================================================================


@pytest.mark.unit
class TestListCodexModelsBranches:
    """Cover codex model parsing and fallback branches."""

    @patch("thegent.cli.console")
    def test_codex_with_models(self, mock_console) -> None:
        # @trace FR-CLI-479
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "gpt-5.3-codex-high\ngpt-5.3-codex-xhigh\nTip: use codex\n"
        with patch("thegent.cli.subprocess.run", return_value=mock_proc):
            from thegent.cli import _list_codex_models

            _list_codex_models()

    @patch("thegent.cli.console")
    def test_codex_no_codex_models(self, mock_console) -> None:
        # @trace FR-CLI-480
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "only-claude-models\n"
        with (
            patch("thegent.cli.subprocess.run", return_value=mock_proc),
            patch("thegent.cli._list_codex_models_fallback"),
        ):
            from thegent.cli import _list_codex_models

            _list_codex_models()

    @patch("thegent.cli.console")
    def test_codex_not_found(self, mock_console) -> None:
        # @trace FR-CLI-481
        with (
            patch("thegent.cli.subprocess.run", side_effect=FileNotFoundError),
            patch("thegent.cli._list_codex_models_fallback"),
        ):
            from thegent.cli import _list_codex_models

            _list_codex_models()


# ============================================================================
# _models_table  (lines 4299-4302)
# ============================================================================


@pytest.mark.unit
class TestModelsTableHelper:
    """Cover the _models_table helper."""

    def test_creates_table(self) -> None:
        # @trace FR-CLI-482
        from thegent.cli import _models_table

        t = _models_table("Test Models")
        assert t.title == "Test Models"
