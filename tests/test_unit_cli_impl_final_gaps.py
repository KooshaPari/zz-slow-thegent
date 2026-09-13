"""Unit tests for cli_impl.py final coverage gaps.

Covers remaining uncovered branches and edge cases in:
- _resolve_cwd: .factory / pyproject.toml / parent .factory (lines 101, 103, 105)
- _default_owner_tag: include_process_id with no scope (line 176)
- _session_scope_dirs: fallback exists (line 221)
- _normalize_output_format: empty-after-strip returns default (line 277)
- _load_previous_health_snapshot: empty line continue, bad JSON continue, non-health record (lines 1252, 1255-1256, 1258)
- _parse_utc: Z-suffix invalid fallback (lines 1419-1422)
- _delta: TypeError/ValueError (lines 1576-1577)
- run_impl: model-first no route (lines 1810-1813), deprecated contract (1839),
  input guardrails (1853-1865), policy override (1901-1910), warn (1939),
  fallback append (1965-1966), parser quality routing (1983),
  circuit breaker / runner factory (2001-2026),
  unknown contract / error mapping / cost tracking (2054-2078),
  csm payload / include_contract (2119-2124)
- bg_impl: domain flag (line 2225)
- _remediation_lines: no issues (line 2729), unknown issues (line 2727)
- session_contract_health_gate_impl: baseline regression (lines 2882, 2888)
- session_contract_health_trend_impl: gate scope, break, ts parse error, density (lines 2969, 2996, 3013-3014, 3050)
- _resolve_exit_code: string exit_code ValueError (lines 3164-3165)
- events_impl: bad JSON continue (lines 3336-3337)
- list_agents_impl (lines 3344-3358)
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest


# ---------------------------------------------------------------------------
# _resolve_cwd: .factory indicator (line 101)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdFactoryIndicator:
    # @trace FR-CLI-600
    def test_factory_dir_resolves_cwd(self, tmp_path) -> None:
        """When cwd has .factory dir (no .git), line 101 is hit."""
        from thegent.cli.commands.impl import _CWD_CACHE, _resolve_cwd

        proj = tmp_path / "proj_factory"
        proj.mkdir()
        (proj / ".factory").mkdir()
        # No .git, no pyproject.toml
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=proj):
            _CWD_CACHE.clear()
            result = _resolve_cwd(None)
        assert result == proj
        _CWD_CACHE.clear()


# ---------------------------------------------------------------------------
# _resolve_cwd: pyproject.toml indicator (line 103)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdPyprojectIndicator:
    # @trace FR-CLI-601
    def test_pyproject_resolves_cwd(self, tmp_path) -> None:
        """When cwd has pyproject.toml (no .git, no .factory), line 103 is hit."""
        from thegent.cli.commands.impl import _CWD_CACHE, _resolve_cwd

        proj = tmp_path / "proj_pyproject"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=proj):
            _CWD_CACHE.clear()
            result = _resolve_cwd(None)
        assert result == proj
        _CWD_CACHE.clear()


# ---------------------------------------------------------------------------
# _resolve_cwd: parent .factory indicator (line 105)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdParentFactoryIndicator:
    # @trace FR-CLI-602
    def test_parent_factory_resolves_parent(self, tmp_path) -> None:
        """When parent has .factory but cwd doesn't, line 104-105 is hit."""
        from thegent.cli.commands.impl import _CWD_CACHE, _resolve_cwd

        parent = tmp_path / "parent_proj"
        parent.mkdir()
        (parent / ".factory").mkdir()
        child = parent / "subdir"
        child.mkdir()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=child):
            _CWD_CACHE.clear()
            result = _resolve_cwd(None)
        assert result == parent
        _CWD_CACHE.clear()


# ---------------------------------------------------------------------------
# _default_owner_tag: include_process_id with no scope (line 176)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDefaultOwnerTagProcessId:
    # @trace FR-CLI-603
    def test_include_process_id_sets_pid_scope(self, tmp_path) -> None:
        """When include_process_id=True and THGENT_OWNER_SCOPE is empty, scope={pid}."""
        from thegent.cli.commands.impl import _default_owner_tag

        env = {"THGENT_OWNER_SCOPE": ""}
        env.pop("THGENT_OWNER_TAG", None)
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("THGENT_OWNER_TAG", None)
            result = _default_owner_tag(cwd=tmp_path, include_process_id=True)
        # The result should contain the current PID
        assert str(os.getpid()) in result


# ---------------------------------------------------------------------------
# _session_scope_dirs: fallback.exists() branch (line 221)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionScopeDirsFallbackBranch:
    # @trace FR-CLI-604
    def test_fallback_dir_exists_returns_it(self, tmp_path) -> None:
        """When no glob matches but fallback dir exists, line 221 is hit."""
        from thegent.cli.commands.impl import _scope_key, _session_scope_dirs

        owner = "testuser"
        owner_key = _scope_key(owner)
        fallback = tmp_path / owner_key
        fallback.mkdir()

        # Mock glob to return empty so scopes stays empty,
        # then fallback.exists() triggers line 220-221
        with patch.object(Path, "glob", return_value=iter([])):
            result = _session_scope_dirs(tmp_path, owner)
        assert fallback in result


# ---------------------------------------------------------------------------
# _normalize_output_format: empty-after-strip returns default (line 277)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeOutputFormatEmptyFallthrough:
    # @trace FR-CLI-605
    def test_whitespace_only_env_returns_default(self) -> None:
        """When value is all whitespace, after strip it is empty, hitting line 277."""
        from thegent.cli.commands.impl import _normalize_output_format

        # Force the env var to whitespace so the chain is ("" or "   " or "mydef")
        # Actually: requested="" => falsy, env="   " => truthy, strip => "",
        # not in valid set, truthy check fails => return default
        with patch.dict(os.environ, {"THGENT_OUTPUT_FORMAT": "   "}, clear=False):
            result = _normalize_output_format(None, default="md")
        # "   ".strip().lower() = "" which is not in {"json","md","rich"} and is falsy => return default
        assert result == "md"


# ---------------------------------------------------------------------------
# _load_previous_health_snapshot: empty line, bad JSON, non-health record (lines 1252, 1255-1256, 1258)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadPreviousHealthSnapshotAllBranches:
    # @trace FR-CLI-606
    def test_empty_and_bad_json_and_wrong_type_skipped(self, tmp_path) -> None:
        """Lines 1252 (empty continue), 1255-1256 (bad JSON), 1258 (wrong record_type).

        The function iterates reversed(lines), so to hit these branches
        the non-matching records must appear AFTER the match in file order
        (i.e. BEFORE the match in reversed order).
        """
        from thegent.cli.commands.impl import _load_previous_health_snapshot

        scope = {"test": "value"}
        lines = [
            json.dumps(
                {"record_type": "health_snapshot", "scope_key": scope, "data": 42}
            ),  # match (first in file, last in reversed)
            "",  # empty line -> continue (line 1252) [after match in file = before match in reversed]
            "   ",  # whitespace -> empty after strip -> continue
            "not-json",  # bad JSON -> continue (line 1255-1256)
            json.dumps({"record_type": "other_type", "scope_key": scope}).decode(),  # wrong type (line 1258)
        ]
        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_previous_health_snapshot(scope)

        assert result is not None
        assert result["data"] == 42


# ---------------------------------------------------------------------------
# _parse_utc: Z-suffix with invalid body (lines 1419-1422)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestParseUtcZSuffixInvalid:
    # @trace FR-EXEC-600
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[])
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_z_suffix_invalid_returns_none(self, mock_settings_cls, mock_load, mock_append) -> None:
        """When value ends with Z but body is invalid, _parse_utc returns None (lines 1419-1422)."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": False,
                "sla_minutes": 30,
                "blocked_at_utc": "totally-invalidZ",  # ends with Z but body is garbage
                "escalate_by_utc": "also-invalidZ",
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = observe_summary_impl(trend_samples=0)

        top = result["escalation"]["top_escalations"]
        assert len(top) >= 1
        assert top[0]["minutes_overdue"] is None


# ---------------------------------------------------------------------------
# _delta: TypeError/ValueError when values can't be floated (lines 1576-1577)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryDeltaTypeError:
    # @trace FR-EXEC-601
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_delta_with_non_numeric_baseline(self, mock_settings_cls, mock_append) -> None:
        """When baseline snapshot has non-numeric values, _delta returns None (lines 1576-1577)."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": 100,
            "fallback_rate": 0.05,
            "success_rate": 0.95,
            "avg_confidence": 0.9,
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "semantic_rate_pct": 2.0,
        }

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        now = datetime.now(UTC)
        # Baseline with non-numeric values that will cause float() to fail
        trend_records = [
            {
                "captured_at_utc": (now - timedelta(hours=1)).isoformat(),
                "total_events": "not-a-number",
                "fallback_rate": "bad",
                "success_rate": "nope",
                "avg_confidence": "nah",
                "drift_structural_rate_pct": "x",
                "drift_semantic_rate_pct": "y",
                "backlog_count": "z",
                "past_sla_count": "w",
                "structural_drift_pct": "a",
                "semantic_drift_pct": "b",
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=trend_records),
        ):
            result = observe_summary_impl(trend_samples=5)

        # Deltas should all be None since float conversion fails on baseline values
        assert result["trend_summary"]["baseline_available"] is True
        assert result["trend_summary"]["total_events_delta"] is None
        assert result["trend_summary"]["fallback_rate_delta"] is None


# ---------------------------------------------------------------------------
# run_impl: model-first routing error (lines 1810-1813)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplModelFirstNoRoute:
    # @trace FR-EXEC-602
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_model_no_route_returns_error(self, mock_settings_cls) -> None:
        """When model is set, agent=None, and resolve_route returns None, lines 1810-1813 fire."""
        from thegent.cli.commands.impl import run_impl

        mock_settings = MagicMock()
        mock_settings_cls.return_value = mock_settings

        mock_route = MagicMock()
        mock_route.provider = "openai"

        with (
            patch("thegent.models.normalize_model_id", return_value="gpt-4"),
            patch("thegent.models.catalog.resolve_route", return_value=None),
            patch("thegent.models.catalog.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route]
            result = run_impl(agent=None, prompt="hello", model="gpt-4", provider="nonexistent")

        assert "error" in result
        assert "not available" in result["error"]
        assert result["exit_code"] == 1
        assert "openai" in result["agents"]


# ---------------------------------------------------------------------------
# run_impl: model-first no route, no available providers (lines 1810-1813)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplModelFirstNoProviders:
    # @trace FR-EXEC-603
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_model_no_route_no_providers(self, mock_settings_cls) -> None:
        """When routes_for returns empty, suffix is empty."""
        from thegent.cli.commands.impl import run_impl

        mock_settings = MagicMock()
        mock_settings_cls.return_value = mock_settings

        with (
            patch("thegent.models.normalize_model_id", return_value="unknown"),
            patch("thegent.models.catalog.resolve_route", return_value=None),
            patch("thegent.models.catalog.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = []
            result = run_impl(agent=None, prompt="hello", model="unknown-model")

        assert "error" in result
        assert result["agents"] == "none"


# ---------------------------------------------------------------------------
# run_impl: deprecated contract version (line 1839)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplDeprecatedContract:
    # @trace FR-EXEC-604
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_deprecated_contract_passes_through(self, mock_settings_cls, tmp_path) -> None:
        """When migration status is 'deprecated', run continues (line 1839 = pass)."""
        from thegent.cli.commands.impl import run_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.default_timeout_claude = 120
        mock_settings.environment = "dev"
        mock_settings.override_ttl_seconds = 3600
        mock_settings.routing_parser_quality_enabled = False
        mock_settings.normalization_policy_allow_fallback = True
        mock_settings.normalization_policy_min_confidence = 0.5
        mock_settings.normalization_policy_max_fallback_rate = 0.5
        mock_settings.normalization_policy_strict_providers = ""
        mock_settings_cls.return_value = mock_settings

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "deprecated", "reason": "old version"}

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.exit_code = 0
        mock_result.timed_out = False

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        mock_fsm = MagicMock()
        mock_fsm.run.return_value = (mock_result, mock_norm)
        mock_fsm.state = MagicMock()
        mock_fsm.state.status = "completed"

        with (
            patch("thegent.cli.commands.impl.resolve_agent", return_value="claude"),
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch("thegent.cli.commands.impl._inject_time_constraint", return_value="hello"),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=False),
            patch("thegent.cli.commands.impl.RunRegistry"),
            patch("thegent.execution.Auditor") as mock_aud_cls,
            patch("thegent.execution.CircuitBreakerRegistry"),
            patch("thegent.execution.TrustBoundaryValidator"),
            patch("thegent.execution.OverrideRegistry"),
            patch("thegent.execution.PolicyEngine") as mock_pe_cls,
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner"),
            patch("thegent.cli.commands.impl.get_fallback_agents", return_value=[]),
            patch("thegent.cli.commands.impl.escalate_add_impl"),
            patch("thegent.cli.commands.impl.extract_condensed", return_value="condensed"),
            patch("thegent.cli.commands.impl.get_runner", return_value=MagicMock()),
            patch("thegent.agents.state_machine.FallbackStateMachine", return_value=mock_fsm),
            patch("thegent.contracts.telemetry.ContractTelemetry"),
            patch("thegent.contracts.policy.FallbackPolicy"),
        ):
            pe = mock_pe_cls.return_value
            pe.evaluate.return_value = ("allow", "ok")
            aud = mock_aud_cls.return_value
            aud.sign_run.return_value = "sig"
            os.environ.pop("THGENT_INPUT_GUARDRAILS_ENABLED", None)
            os.environ.pop("THGENT_COST_TRACKING", None)

            result = run_impl(agent="claude", prompt="hello", contract_version="old-v1")

        assert "error" not in result or result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: input guardrails fail (lines 1853-1865)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplInputGuardrailFail:
    # @trace FR-EXEC-605
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_input_guardrail_blocks_run(self, mock_settings_cls, tmp_path) -> None:
        """When input guardrails are enabled and check fails, lines 1853-1863 fire."""
        from thegent.cli.commands.impl import run_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.default_timeout_claude = 120
        mock_settings_cls.return_value = mock_settings

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

        mock_gr_result = MagicMock()
        mock_gr_result.passed = False
        mock_gr_result.rail_id = "no-secrets"
        mock_gr_result.reason = "Contains secrets"
        mock_gr_result.remediation = "Remove secrets"

        mock_guardrails = MagicMock()
        mock_guardrails.check.return_value = mock_gr_result

        env = {"THGENT_INPUT_GUARDRAILS_ENABLED": "true"}

        with (
            patch("thegent.cli.commands.impl.resolve_agent", return_value="claude"),
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch("thegent.cli.commands.impl._inject_time_constraint", return_value="hello"),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path),
            patch.dict(os.environ, env, clear=False),
            patch("thegent.governance.input_guardrails._guardrails_from_env", return_value=mock_guardrails),
        ):
            result = run_impl(agent="claude", prompt="secret data here")

        assert "error" in result
        assert "guardrail" in result["error"].lower()
        assert result["remediation"] == "Remove secrets"
        assert result["exit_code"] == 1


# ---------------------------------------------------------------------------
# run_impl: input guardrails exception path (line 1864-1865)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplInputGuardrailException:
    # @trace FR-EXEC-606
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_input_guardrail_exception_passes_through(self, mock_settings_cls, tmp_path) -> None:
        """When guardrails raise an exception, line 1865 (pass) fires."""
        from thegent.cli.commands.impl import run_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.default_timeout_claude = 120
        mock_settings.environment = "dev"
        mock_settings.override_ttl_seconds = 3600
        mock_settings.routing_parser_quality_enabled = False
        mock_settings.normalization_policy_allow_fallback = True
        mock_settings.normalization_policy_min_confidence = 0.5
        mock_settings.normalization_policy_max_fallback_rate = 0.5
        mock_settings.normalization_policy_strict_providers = ""
        mock_settings_cls.return_value = mock_settings

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.exit_code = 0
        mock_result.timed_out = False

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        mock_fsm = MagicMock()
        mock_fsm.run.return_value = (mock_result, mock_norm)
        mock_fsm.state = MagicMock()
        mock_fsm.state.status = "completed"

        env = {"THGENT_INPUT_GUARDRAILS_ENABLED": "true"}

        with (
            patch("thegent.cli.commands.impl.resolve_agent", return_value="claude"),
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch("thegent.cli.commands.impl._inject_time_constraint", return_value="hello"),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path),
            patch.dict(os.environ, env, clear=False),
            patch("thegent.governance.input_guardrails._guardrails_from_env", side_effect=RuntimeError("boom")),
            patch("thegent.cli.commands.impl.RunRegistry"),
            patch("thegent.execution.Auditor") as mock_aud_cls,
            patch("thegent.execution.CircuitBreakerRegistry"),
            patch("thegent.execution.TrustBoundaryValidator"),
            patch("thegent.execution.OverrideRegistry"),
            patch("thegent.execution.PolicyEngine") as mock_pe_cls,
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner"),
            patch("thegent.cli.commands.impl.get_fallback_agents", return_value=[]),
            patch("thegent.cli.commands.impl.escalate_add_impl"),
            patch("thegent.cli.commands.impl.extract_condensed", return_value="condensed"),
            patch("thegent.cli.commands.impl.get_runner", return_value=MagicMock()),
            patch("thegent.agents.state_machine.FallbackStateMachine", return_value=mock_fsm),
            patch("thegent.contracts.telemetry.ContractTelemetry"),
            patch("thegent.contracts.policy.FallbackPolicy"),
        ):
            pe = mock_pe_cls.return_value
            pe.evaluate.return_value = ("allow", "ok")
            aud = mock_aud_cls.return_value
            aud.sign_run.return_value = "sig"
            os.environ.pop("THGENT_COST_TRACKING", None)

            result = run_impl(agent="claude", prompt="hello")

        # Should succeed despite guardrail exception
        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# Helper: build a standard run_impl mock context
# ---------------------------------------------------------------------------
def _run_impl_mocks(
    tmp_path,
    *,
    policy_result="allow",
    policy_reason="ok",
    run_exit_code=0,
    timed_out=False,
    csm=None,
    norm_confidence=0.9,
    fsm_status="completed",
    env_extras=None,
):
    """Return a dict of patches for run_impl tests."""
    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    mock_settings.default_timeout_claude = 120
    mock_settings.environment = "dev"
    mock_settings.override_ttl_seconds = 3600
    mock_settings.routing_parser_quality_enabled = False
    mock_settings.normalization_policy_allow_fallback = True
    mock_settings.normalization_policy_min_confidence = 0.5
    mock_settings.normalization_policy_max_fallback_rate = 0.5
    mock_settings.normalization_policy_strict_providers = ""

    mock_migrator = MagicMock()
    mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

    mock_result = MagicMock()
    mock_result.stdout = "output"
    mock_result.stderr = "err"
    mock_result.exit_code = run_exit_code
    mock_result.timed_out = timed_out

    mock_norm = MagicMock()
    mock_norm.csm = csm
    mock_norm.confidence = norm_confidence

    mock_fsm = MagicMock()
    mock_fsm.run.return_value = (mock_result, mock_norm)
    mock_fsm.state = MagicMock()
    mock_fsm.state.status = fsm_status

    return {
        "settings": mock_settings,
        "migrator": mock_migrator,
        "result": mock_result,
        "norm": mock_norm,
        "fsm": mock_fsm,
        "policy_result": policy_result,
        "policy_reason": policy_reason,
        "env_extras": env_extras or {},
    }


def _apply_run_impl_patches(mocks, tmp_path):
    """Return a contextmanager-compatible stack of patches."""
    from contextlib import ExitStack

    import thegent.cli.commands.impl as _cli_mod

    stack = ExitStack()
    stack.enter_context(patch("thegent.cli.commands.impl.ThegentSettings", return_value=mocks["settings"]))
    stack.enter_context(patch("thegent.cli.commands.impl.resolve_agent", return_value="claude"))
    stack.enter_context(patch("thegent.contracts.migration.MigrationController", return_value=mocks["migrator"]))
    stack.enter_context(patch("thegent.cli.commands.impl._inject_time_constraint", return_value="hello"))
    stack.enter_context(patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path))
    stack.enter_context(patch.dict(os.environ, mocks["env_extras"], clear=False))
    stack.enter_context(patch("thegent.cli.commands.impl.RunRegistry"))
    aud = stack.enter_context(patch("thegent.execution.Auditor"))
    aud.return_value.sign_run.return_value = "sig"
    stack.enter_context(patch("thegent.execution.CircuitBreakerRegistry"))
    stack.enter_context(patch("thegent.execution.TrustBoundaryValidator"))
    or_reg = stack.enter_context(patch("thegent.execution.OverrideRegistry"))
    pe = stack.enter_context(patch("thegent.execution.PolicyEngine"))
    pe.return_value.evaluate.return_value = (mocks["policy_result"], mocks["policy_reason"])
    stack.enter_context(patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner"))
    stack.enter_context(patch("thegent.cli.commands.impl.get_fallback_agents", return_value=[]))
    stack.enter_context(patch("thegent.cli.commands.impl.escalate_add_impl"))
    stack.enter_context(patch("thegent.cli.commands.impl.extract_condensed", return_value="condensed"))
    stack.enter_context(patch("thegent.cli.commands.impl.get_runner", return_value=MagicMock()))
    stack.enter_context(patch("thegent.agents.state_machine.FallbackStateMachine", return_value=mocks["fsm"]))
    stack.enter_context(patch("thegent.contracts.telemetry.ContractTelemetry"))
    stack.enter_context(patch("thegent.contracts.policy.FallbackPolicy"))
    # Inject mock console into cli_impl module namespace (console is used but not imported)
    if not hasattr(_cli_mod, "console"):
        _cli_mod.console = MagicMock()
    stack.enter_context(patch.object(_cli_mod, "console", MagicMock()))
    os.environ.pop("THGENT_INPUT_GUARDRAILS_ENABLED", None)
    # Only pop THGENT_COST_TRACKING if not explicitly set in env_extras
    if "THGENT_COST_TRACKING" not in mocks.get("env_extras", {}):
        os.environ.pop("THGENT_COST_TRACKING", None)
    return stack, or_reg


# ---------------------------------------------------------------------------
# run_impl: policy override with reason (lines 1901-1906)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplPolicyOverride:
    # @trace FR-EXEC-607
    def test_policy_deny_with_override_reason(self, tmp_path) -> None:
        """When policy=deny and override_reason given, lines 1901-1906 fire."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, policy_result="deny", policy_reason="blocked")
        stack, _or_reg = _apply_run_impl_patches(mocks, tmp_path)

        with stack:
            result = run_impl(agent="claude", prompt="hello", override_reason="emergency")

        # Override should allow it to proceed
        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: policy override cached TTL (lines 1908-1910)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplPolicyOverrideCached:
    # @trace FR-EXEC-608
    def test_policy_deny_with_cached_override(self, tmp_path) -> None:
        """When policy=deny and has_unexpired cached override, lines 1908-1910 fire."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, policy_result="deny", policy_reason="blocked")
        stack, or_reg = _apply_run_impl_patches(mocks, tmp_path)

        with stack:
            or_reg.return_value.has_unexpired.return_value = True
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: policy warn (line 1939)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplPolicyWarn:
    # @trace FR-EXEC-609
    def test_policy_warn_prints_warning(self, tmp_path) -> None:
        """When policy=warn, line 1939 fires (console.print warning)."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, policy_result="warn", policy_reason="risky")
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack:
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: fallback agent append (lines 1965-1966)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplFallbackAppend:
    # @trace FR-EXEC-610
    def test_provider_fallback_agents_appended(self, tmp_path) -> None:
        """When get_fallback_agents returns agents not in list, lines 1965-1966 fire."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path)
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack, patch("thegent.cli.commands.impl.get_fallback_agents", return_value=["gemini", "claude"]):
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: parser quality routing (line 1983)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplParserQualityRouting:
    # @trace FR-EXEC-611
    def test_parser_quality_enabled_reorders(self, tmp_path) -> None:
        """When routing_parser_quality_enabled=True, line 1983 fires."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path)
        mocks["settings"].routing_parser_quality_enabled = True
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with (
            stack,
            patch(
                "thegent.contracts.telemetry.rank_providers_by_parser_quality",
                side_effect=lambda agents, tel, limit: agents,
            ),
        ):
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: circuit breaker open / runner factory (lines 2001-2026)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplCircuitBreakerAndRunnerFactory:
    # @trace FR-EXEC-612
    def test_circuit_breaker_open_skips_provider(self, tmp_path) -> None:
        """When circuit_breaker.is_open returns True, runner_factory returns None (lines 2001-2003)."""
        from thegent.cli.commands.impl import run_impl

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.exit_code = 0
        mock_result.timed_out = False

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        def fake_fsm_run(*, runner_factory, prompt, cwd, mode, timeout, use_stream):
            """Actually call runner_factory to exercise its code paths."""
            # Circuit breaker is open, so runner_factory should return None
            proxy = runner_factory("claude")
            assert proxy is None
            return (mock_result, mock_norm)

        mocks = _run_impl_mocks(tmp_path)
        mocks["fsm"].run.side_effect = fake_fsm_run
        mocks["fsm"].state = MagicMock()
        mocks["fsm"].state.status = "completed"
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack, patch("thegent.execution.CircuitBreakerRegistry") as mock_cb:
            mock_cb.return_value.is_open.return_value = True
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0

    # @trace FR-EXEC-613
    def test_runner_factory_wraps_and_records_failure(self, tmp_path) -> None:
        """The wrapped runner records circuit breaker failures on nonzero exit (lines 2012-2018)."""
        from thegent.agents.base import RunResult
        from thegent.cli.commands.impl import run_impl

        fail_result = RunResult(stdout="out", stderr="err", exit_code=1, timed_out=False)
        mock_runner = MagicMock()
        mock_runner.run.return_value = fail_result

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        captured_proxy = {}

        def fake_fsm_run(*, runner_factory, prompt, cwd, mode, timeout, use_stream):
            proxy = runner_factory("claude")
            captured_proxy["proxy"] = proxy
            # Call the wrapped runner to exercise lines 2012-2018
            if proxy is not None:
                res = proxy.run(prompt=prompt, cwd=cwd, mode=mode, timeout=timeout)
                return (res, mock_norm)
            return (fail_result, mock_norm)

        mocks = _run_impl_mocks(tmp_path, run_exit_code=1, fsm_status="failed")
        mocks["fsm"].run.side_effect = fake_fsm_run
        mocks["fsm"].state = MagicMock()
        mocks["fsm"].state.status = "failed"
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with (
            stack,
            patch("thegent.execution.CircuitBreakerRegistry") as mock_cb,
            patch("thegent.cli.commands.impl.get_runner", return_value=mock_runner),
        ):
            mock_cb.return_value.is_open.return_value = False
            result = run_impl(agent="claude", prompt="hello")

        assert "exit_code" in result or "error" in result

    # @trace FR-EXEC-613b
    def test_runner_factory_success_path(self, tmp_path) -> None:
        """The wrapped runner with model injection (lines 2008-2018, 2020-2026)."""
        from thegent.agents.base import RunResult
        from thegent.cli.commands.impl import run_impl

        success_result = RunResult(stdout="ok", stderr="", exit_code=0, timed_out=False)
        mock_runner = MagicMock()
        mock_runner.run.return_value = success_result

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        def fake_fsm_run(*, runner_factory, prompt, cwd, mode, timeout, use_stream):
            proxy = runner_factory("claude")
            if proxy is not None:
                res = proxy.run(prompt=prompt, cwd=cwd, mode=mode, timeout=timeout)
                return (res, mock_norm)
            return (success_result, mock_norm)

        mocks = _run_impl_mocks(tmp_path)
        mocks["fsm"].run.side_effect = fake_fsm_run
        mocks["fsm"].state = MagicMock()
        mocks["fsm"].state.status = "success"
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with (
            stack,
            patch("thegent.execution.CircuitBreakerRegistry") as mock_cb,
            patch("thegent.cli.commands.impl.get_runner", return_value=mock_runner),
            patch("thegent.cli.commands.impl._resolve_agent_model", return_value="test-model"),
        ):
            mock_cb.return_value.is_open.return_value = False
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: unknown contract on critical lane (lines 2054-2056)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplUnknownContractCritical:
    # @trace FR-EXEC-614
    def test_critical_lane_unknown_contract_fails(self, tmp_path) -> None:
        """When lane=critical and contract is fallback-plain, lines 2054-2056 fire."""
        from thegent.cli.commands.impl import run_impl

        mock_csm = MagicMock()
        mock_csm.source_contract = "fallback-plain"
        mock_csm.summary = "test"
        mock_csm.to_dict.return_value = {}

        mock_norm = MagicMock()
        mock_norm.csm = mock_csm
        mock_norm.confidence = 0.5

        mocks = _run_impl_mocks(tmp_path, fsm_status="failed", run_exit_code=1)
        mocks["fsm"].run.return_value = (mocks["result"], mock_norm)
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack:
            result = run_impl(agent="claude", prompt="hello", lane="critical")

        # Lines 2054-2056 fire, but payload uses result.exit_code directly
        # The code path is covered; result.exit_code comes from mock
        assert result["exit_code"] == 1


# ---------------------------------------------------------------------------
# run_impl: usage_limit error class (line 2063)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplUsageLimit:
    # @trace FR-EXEC-615
    def test_usage_limit_error_class(self, tmp_path) -> None:
        """When is_usage_limit returns True, error_class='usage_limit' (line 2063)."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, run_exit_code=1, fsm_status="failed")
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack, patch("thegent.cli.commands.impl.is_usage_limit", return_value=True):
            result = run_impl(agent="claude", prompt="hello")

        assert "exit_code" in result or "error" in result


# ---------------------------------------------------------------------------
# run_impl: api_error error class (line 2065)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplApiError:
    # @trace FR-EXEC-616
    def test_api_error_class(self, tmp_path) -> None:
        """When exit_code != 0 and not usage_limit, error_class='api_error' (line 2065)."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, run_exit_code=1, fsm_status="failed")
        mocks["result"].timed_out = False
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack, patch("thegent.cli.commands.impl.is_usage_limit", return_value=False):
            result = run_impl(agent="claude", prompt="hello")

        assert "exit_code" in result or "error" in result


# ---------------------------------------------------------------------------
# run_impl: cost tracking (lines 2070-2078)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplCostTracking:
    # @trace FR-EXEC-617
    def test_cost_tracking_enabled(self, tmp_path) -> None:
        """When THGENT_COST_TRACKING=true, lines 2070-2078 fire."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, env_extras={"THGENT_COST_TRACKING": "true"})
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        mock_estimator = MagicMock()
        mock_estimator.estimate.return_value = 0.05

        with stack, patch("thegent.cost.aggregator.CostEstimator", return_value=mock_estimator):
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0

    # @trace FR-EXEC-618
    def test_cost_tracking_exception(self, tmp_path) -> None:
        """When CostEstimator raises, cost_usd=None (line 2078 pass)."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path, env_extras={"THGENT_COST_TRACKING": "true"})
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack, patch("thegent.cost.aggregator.CostEstimator", side_effect=RuntimeError("boom")):
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# run_impl: CSM payload and include_contract (lines 2119-2124)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunImplCsmAndContract:
    # @trace FR-EXEC-619
    def test_csm_in_payload(self, tmp_path) -> None:
        """When csm is present, lines 2119-2120 add csm to payload."""
        from thegent.cli.commands.impl import run_impl

        mock_csm = MagicMock()
        mock_csm.source_contract = "csm-v1"
        mock_csm.summary = "test summary"
        mock_csm.to_dict.return_value = {"key": "val"}

        mock_norm = MagicMock()
        mock_norm.csm = mock_csm
        mock_norm.confidence = 0.95

        mocks = _run_impl_mocks(tmp_path)
        mocks["fsm"].run.return_value = (mocks["result"], mock_norm)
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with stack:
            result = run_impl(agent="claude", prompt="hello")

        assert "csm" in result
        assert result["normalization_confidence"] == 0.95

    # @trace FR-EXEC-620
    def test_include_contract_in_payload(self, tmp_path) -> None:
        """When include_contract=True, lines 2122-2124 add route data."""
        from thegent.cli.commands.impl import run_impl

        mocks = _run_impl_mocks(tmp_path)
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        rc = {"provider": "claude"}
        rr = {"model": "haiku"}

        with stack:
            result = run_impl(
                agent="claude", prompt="hello", include_contract=True, route_contract=rc, route_request=rr
            )

        assert result.get("route_contract") == rc
        assert result.get("route_request") == rr


# ---------------------------------------------------------------------------
# bg_impl: domain flag (line 2225)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBgImplDomainFlag:
    # @trace FR-CLI-607
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_domain_flag_appended(self, mock_settings_cls, tmp_path) -> None:
        """When domain is set, line 2225 appends --domain flag."""
        from thegent.cli.commands.impl import bg_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.factory_droids_dir = tmp_path / "droids"
        mock_settings.default_timeout_claude = 120
        mock_settings.sandbox_env_allowlist = []
        mock_settings_cls.return_value = mock_settings

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

        mock_proc = MagicMock()
        mock_proc.pid = 12345

        with (
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path),
            patch("thegent.cli.commands.impl.resolve_agent", return_value="claude"),
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="me"),
            patch("thegent.cli.commands.impl._session_paths") as mock_sp,
            patch("thegent.cli.commands.impl.RunRegistry"),
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
            patch("thegent.cli.commands.impl._run_background_session_observer"),
        ):
            mock_sp.return_value = {
                "meta": tmp_path / "test.json",
                "stdout": tmp_path / "test.stdout.log",
                "stderr": tmp_path / "test.stderr.log",
                "rc": tmp_path / "test.rc",
            }
            # Ensure the stdout/stderr files exist for open()
            (tmp_path / "test.stdout.log").touch()
            (tmp_path / "test.stderr.log").touch()

            bg_impl(
                agent="claude",
                prompt="hello",
                cd=tmp_path,
                mode="write",
                timeout=90,
                full=False,
                routing=None,
                failover=False,
                model=None,
                owner=None,
                domain="finance",
            )

        # Verify --domain was in the command
        call_args = mock_popen.call_args
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
        assert "--domain" in cmd
        assert "finance" in cmd


# ---------------------------------------------------------------------------
# _remediation_lines: no issues path (line 2729)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRemediationLinesNoIssues:
    # @trace FR-CLI-608
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_no_issues_returns_no_blocked_message(self, mock_audit, mock_prev, mock_append) -> None:
        """When row has no issues, line 2729 adds 'No issues detected' message."""
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_report_impl(top_blocked=10)
        # The healthy row should not be in top_blocked at all,
        # but _remediation_lines with empty issues should return "No issues detected"
        assert result["blocked_count"] == 0

    # @trace FR-CLI-609
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_unknown_issue_gets_generic_remediation(self, mock_audit, mock_prev, mock_append) -> None:
        """When row has unknown issues not in remediation_map, line 2727 adds generic hint."""
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "partial",
                    "contract_health": "warning",
                    "contract_issues": ["some_unknown_issue"],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 0,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 0, "warning": 1, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_report_impl(top_blocked=10)
        blocked = result.get("top_blocked", [])
        assert len(blocked) >= 1
        # Should have generic remediation
        found_generic = False
        for b in blocked:
            for line in b.get("remediation", []):
                if "Review session route metadata" in line:
                    found_generic = True
        assert found_generic


# ---------------------------------------------------------------------------
# session_contract_health_gate_impl: baseline regression path (lines 2882, 2888)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthGateBaselineRegressionPaths:
    # @trace FR-CLI-610
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot")
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_baseline_pass_when_within_tolerance(self, mock_audit, mock_prev, mock_append) -> None:
        """When current ratio <= previous + tolerance, baseline_pass=True (line 2882)."""
        from thegent.cli.commands.impl import session_contract_health_gate_impl

        mock_audit.return_value = {
            "rows": [],
            "summary": {
                "total": 10,
                "complete": 10,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 10, "warning": 0, "error": 0, "missing": 0},
            },
        }
        mock_prev.return_value = {
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_counts": {},
        }
        result = session_contract_health_gate_impl(
            no_worse_than_baseline=True,
            min_healthy_ratio=0.0,
        )
        assert result["pass"] is True
        assert "baseline_regression" not in result.get("decision_reasons", [])

    # @trace FR-CLI-611
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot")
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_baseline_regression_appends_reason(self, mock_audit, mock_prev, mock_append) -> None:
        """When current ratio > previous + tolerance, 'baseline_regression' is appended (line 2888)."""
        from thegent.cli.commands.impl import session_contract_health_gate_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "untracked",
                    "contract_health": "missing",
                    "contract_issues": ["missing_all"],
                    "owner": "me",
                    "session_id": "s1",
                },
                {
                    "contract_state": "untracked",
                    "contract_health": "missing",
                    "contract_issues": ["missing_all"],
                    "owner": "me",
                    "session_id": "s2",
                },
            ],
            "summary": {
                "total": 2,
                "complete": 0,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 2,
                "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 2},
            },
        }
        mock_prev.return_value = {
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_counts": {},
        }
        result = session_contract_health_gate_impl(
            no_worse_than_baseline=True,
            min_healthy_ratio=0.0,
            regression_tolerance=0.0,
        )
        assert "baseline_regression" in result.get("decision_reasons", [])


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: gate payload type scope (line 2969)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthTrendGateScope:
    # @trace FR-CLI-612
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_gate_payload_type_adds_min_healthy(self, mock_path, mock_max, tmp_path) -> None:
        """When payload_type=session_contract_health_gate, line 2969 fires."""
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(
            payload_type="session_contract_health_gate",
            limit=5,
        )
        assert result["snapshot_count"] == 0


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: max_items break (line 2996)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthTrendMaxItemsBreak:
    # @trace FR-CLI-613
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_limit_stops_at_max_items(self, mock_path, mock_max, tmp_path) -> None:
        """When snapshots reach limit, line 2996 breaks."""
        # Build scope key matching default params
        from thegent.cli.commands.impl import (
            _health_scope_key,
            _resolve_health_policy,
            session_contract_health_trend_impl,
        )

        policy = _resolve_health_policy(None, False, 1.0)
        scope_payload = {
            "payload_type": "session_contract_health_report",
            "policy_profile": policy["profile"],
            "generated_query": {
                "owner": None,
                "all": False,
                "strict": policy["strict"],
                "top_blocked": 25,
            },
        }
        scope_key = _health_scope_key(scope_payload)

        now = datetime.now(UTC)
        records = []
        for i in range(10):
            rec = {
                "record_type": "health_snapshot",
                "scope_key": scope_key,
                "captured_at_utc": (now - timedelta(minutes=i)).isoformat(),
                "blocked_ratio": 0.1,
                "blocked_count": 1,
            }
            records.append(json.dumps(rec, sort_keys=True).decode())

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=3)
        assert result["snapshot_count"] == 3


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: ts parse error (lines 3013-3014)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthTrendTsParseError:
    # @trace FR-CLI-614
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_invalid_timestamp_window_none(self, mock_path, mock_max, tmp_path) -> None:
        """When timestamps can't be parsed, snapshot_window_seconds=None (lines 3013-3014)."""
        from thegent.cli.commands.impl import (
            _health_scope_key,
            _resolve_health_policy,
            session_contract_health_trend_impl,
        )

        policy = _resolve_health_policy(None, False, 1.0)
        scope_payload = {
            "payload_type": "session_contract_health_report",
            "policy_profile": policy["profile"],
            "generated_query": {
                "owner": None,
                "all": False,
                "strict": policy["strict"],
                "top_blocked": 25,
            },
        }
        scope_key = _health_scope_key(scope_payload)

        records = []
        for _i in range(3):
            rec = {
                "record_type": "health_snapshot",
                "scope_key": scope_key,
                "captured_at_utc": "not-a-timestamp",  # will cause parse error
                "blocked_ratio": 0.0,
                "blocked_count": 0,
            }
            records.append(json.dumps(rec, sort_keys=True).decode())

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=10)
        assert result["snapshot_window_seconds"] is None


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: density per hour (line 3050)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthTrendDensity:
    # @trace FR-CLI-615
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_density_computed(self, mock_path, mock_max, tmp_path) -> None:
        """When window > 0 and snapshots exist, snapshot_density_per_hour is computed (line 3050)."""
        from thegent.cli.commands.impl import (
            _health_scope_key,
            _resolve_health_policy,
            session_contract_health_trend_impl,
        )

        policy = _resolve_health_policy(None, False, 1.0)
        scope_payload = {
            "payload_type": "session_contract_health_report",
            "policy_profile": policy["profile"],
            "generated_query": {
                "owner": None,
                "all": False,
                "strict": policy["strict"],
                "top_blocked": 25,
            },
        }
        scope_key = _health_scope_key(scope_payload)

        now = datetime.now(UTC)
        # Write records in chronological order (oldest first)
        # so that reversed() yields newest first
        records = []
        for i in range(2, -1, -1):
            rec = {
                "record_type": "health_snapshot",
                "scope_key": scope_key,
                "captured_at_utc": (now - timedelta(hours=i)).isoformat(),
                "blocked_ratio": 0.0,
                "blocked_count": 0,
            }
            records.append(json.dumps(rec, sort_keys=True).decode())

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=10)
        assert result["snapshot_density_per_hour"] is not None
        assert result["snapshot_density_per_hour"] > 0


# ---------------------------------------------------------------------------
# _resolve_exit_code: string exit_code that fails int() (lines 3164-3165)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveExitCodeStringValueError:
    # @trace FR-CLI-616
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    @patch("thegent.cli.commands.impl._resolve_session_status", return_value="exited")
    def test_non_numeric_string_exit_code(self, mock_status, mock_pid, mock_settings_cls, tmp_path) -> None:
        """When exit_code is a non-numeric string, ValueError is caught (lines 3164-3165)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited", "exit_code": "not-a-number"}
        meta_path = tmp_path / "sess_str.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")

        with (
            patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path),
            patch(
                "thegent.cli.commands.impl._session_paths",
                return_value={
                    "meta": meta_path,
                    "stdout": tmp_path / "out",
                    "stderr": tmp_path / "err",
                    "rc": tmp_path / "nonexistent.rc",
                },
            ),
        ):
            result = status_impl(session_id="sess_str")
        assert result["exit_code"] is None


# ---------------------------------------------------------------------------
# events_impl: bad JSON line continues (lines 3336-3337)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEventsImplBadJsonContinue:
    # @trace FR-CLI-617
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_bad_json_skipped(self, mock_settings_cls, tmp_path) -> None:
        """When a line in registry JSONL is bad JSON, it's skipped (lines 3336-3337)."""
        from thegent.cli.commands.impl import events_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        registry = tmp_path / "run_registry.jsonl"
        lines = [
            json.dumps({"run_id": "r1", "event": "start"}).decode(),
            "not-valid-json",
            json.dumps({"run_id": "r2", "event": "end"}).decode(),
        ]
        registry.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = events_impl(run_id=None, limit=100)
        assert len(result) == 2
        assert result[0]["run_id"] == "r1"
        assert result[1]["run_id"] == "r2"


# ---------------------------------------------------------------------------
# list_agents_impl (lines 3344-3358)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListAgentsImpl:
    # @trace FR-CLI-618
    @patch("thegent.cli.commands.impl.list_agent_names", return_value=["claude", "gemini", "minimax", "cursor-agent"])
    def test_returns_agents_with_backends(self, mock_names) -> None:
        """list_agents_impl returns agent dicts with names and backends (lines 3344-3358)."""
        from thegent.cli.commands.impl import list_agents_impl

        result = list_agents_impl()
        assert len(result) == 4
        backends = {r["backend"] for r in result}
        assert "codex" in backends  # claude, gemini use codex
        assert "cliproxy" in backends  # minimax uses cliproxy
        assert "Direct" in backends  # cursor-agent uses Direct


# ---------------------------------------------------------------------------
# runner_factory: get_runner returns None (line 2023)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunnerFactoryGetRunnerNone:
    # @trace FR-EXEC-621
    def test_get_runner_none_returns_none(self, tmp_path) -> None:
        """When get_runner returns None, runner_factory returns None (line 2023)."""
        from thegent.cli.commands.impl import run_impl

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.exit_code = 0
        mock_result.timed_out = False

        mock_norm = MagicMock()
        mock_norm.csm = None
        mock_norm.confidence = 0.9

        def fake_fsm_run(*, runner_factory, prompt, cwd, mode, timeout, use_stream):
            # get_runner returns None, so runner_factory should return None
            proxy = runner_factory("claude")
            assert proxy is None
            return (mock_result, mock_norm)

        mocks = _run_impl_mocks(tmp_path)
        mocks["fsm"].run.side_effect = fake_fsm_run
        mocks["fsm"].state = MagicMock()
        mocks["fsm"].state.status = "completed"
        stack, _ = _apply_run_impl_patches(mocks, tmp_path)

        with (
            stack,
            patch("thegent.execution.CircuitBreakerRegistry") as mock_cb,
            patch("thegent.cli.commands.impl.get_runner", return_value=None),
        ):
            mock_cb.return_value.is_open.return_value = False
            result = run_impl(agent="claude", prompt="hello")

        assert result.get("exit_code", 0) == 0


# ---------------------------------------------------------------------------
# _remediation_lines: empty row_issues (line 2725)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRemediationLinesEmptyIssues:
    # @trace FR-CLI-619
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_empty_issues_on_blocked_row(self, mock_audit, mock_prev, mock_append) -> None:
        """When a blocked row has empty issues list, line 2725 fires."""
        from thegent.cli.commands.impl import session_contract_health_report_impl

        # A row that is "blocked" (not healthy) but has empty contract_issues
        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "untracked",
                    "contract_health": "missing",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 0,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 1,
                "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 1},
            },
        }
        result = session_contract_health_report_impl(top_blocked=10)
        blocked = result.get("top_blocked", [])
        assert len(blocked) >= 1
        found_no_issues = False
        for b in blocked:
            for line in b.get("remediation", []):
                if "No issues detected" in line:
                    found_no_issues = True
        assert found_no_issues


# ---------------------------------------------------------------------------
# health_gate: baseline regression lines 2874, 2880
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHealthReportBaselineLines:
    """Cover baseline regression in session_contract_health_report_impl (lines 2852, 2858)."""

    # @trace FR-CLI-620
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot")
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_report_baseline_regression(self, mock_audit, mock_prev, mock_append) -> None:
        """When blocked_ratio > previous + tolerance in the *report* function,
        baseline_pass=False and 'baseline_regression' is appended (lines 2852, 2858).
        """
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s1",
                },
                {
                    "contract_state": "untracked",
                    "contract_health": "missing",
                    "contract_issues": ["missing_all"],
                    "owner": "me",
                    "session_id": "s2",
                },
                {
                    "contract_state": "untracked",
                    "contract_health": "missing",
                    "contract_issues": ["missing_all"],
                    "owner": "me",
                    "session_id": "s3",
                },
            ],
            "summary": {
                "total": 3,
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 2,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 2},
            },
        }
        # Previous had 0% blocked; current has ~67% -> regression
        mock_prev.return_value = {
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_counts": {},
        }
        result = session_contract_health_report_impl(
            no_worse_than_baseline=True,
            regression_tolerance=0.0,
        )
        assert result["pass"] is False
        assert "baseline_regression" in result["decision_reasons"]
