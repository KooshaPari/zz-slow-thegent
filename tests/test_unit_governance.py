"""Unit tests for governance modules (G-GP)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.cost.aggregator import CostAggregator, CostEstimator
from thegent.execution import PolicyEngine, RunMeta
from thegent.governance.input_guardrails import (
    InputGuardrails,
    guardrails_from_settings,
)


@pytest.mark.unit
class TestCostEstimator:
    """CostEstimator (G-GP-06)."""

    def test_estimate_with_pricing_table(self) -> None:
        # @trace FR-GOV-001
        """Uses pricing table when model matches."""
        est = CostEstimator()
        cost = est.estimate(model="claude-sonnet-4", tokens_in=1000, tokens_out=500)
        assert cost > 0
        assert cost < 0.1

    def test_estimate_fallback_heuristic(self) -> None:
        # @trace FR-GOV-001
        """Uses heuristic when model unknown."""
        est = CostEstimator()
        cost = est.estimate(prompt_length=500)
        assert cost >= 0


@pytest.mark.unit
class TestInputGuardrails:
    """InputGuardrails (G-GP-02)."""

    def test_check_passes_by_default(self) -> None:
        # @trace FR-GOV-003
        """Empty config passes all."""
        g = InputGuardrails()
        r = g.check(prompt="hello", agent="gemini", cwd="/tmp")
        assert r.passed is True

    def test_check_prompt_length_fails(self) -> None:
        # @trace FR-GOV-003
        """Exceeding prompt_max_chars fails."""
        g = InputGuardrails(prompt_max_chars=10)
        r = g.check(prompt="x" * 20)
        assert r.passed is False
        assert r.rail_id == "prompt_length"

    def test_check_agent_allowlist_fails(self) -> None:
        # @trace FR-GOV-005
        """Agent not in allowlist fails."""
        g = InputGuardrails(agent_allowlist=["gemini", "claude"])
        r = g.check(agent="unknown-agent")
        assert r.passed is False
        assert r.rail_id == "agent_allowlist"

    def test_check_agent_allowlist_empty_allows_all(self) -> None:
        # @trace FR-GOV-005
        """Empty allowlist allows any agent."""
        g = InputGuardrails(agent_allowlist=[])
        r = g.check(agent="anything")
        assert r.passed is True

    def test_check_cwd_restriction_fails(self) -> None:
        # @trace FR-GOV-006
        """CWD not under allowed prefix fails."""
        g = InputGuardrails(cwd_allowed_prefixes=["/home", "/workspace"])
        r = g.check(cwd="/tmp/other")
        assert r.passed is False
        assert r.rail_id == "cwd_restriction"

    def test_check_cwd_restriction_passes(self, tmp_path: Path) -> None:
        # @trace FR-GOV-006
        """CWD under prefix passes."""
        allowed = str(tmp_path)
        g = InputGuardrails(cwd_allowed_prefixes=[allowed])
        r = g.check(cwd=tmp_path / "subdir")
        assert r.passed is True

    def testguardrails_from_settings(self) -> None:
        # @trace FR-GOV-007
        """guardrails_from_settings reads THGENT_PROMPT_MAX_CHARS."""
        with patch.dict(os.environ, {"THGENT_PROMPT_MAX_CHARS": "100"}, clear=False):
            g = guardrails_from_settings()
            assert g.prompt_max_chars == 100


@pytest.mark.unit
class TestPolicyEngineOPA:
    """G-GP-01: OPA optional client stub."""

    def test_evaluate_without_opa_uses_python_logic(self, tmp_path: Path) -> None:
        # @trace FR-GOV-001
        """When OPA not configured, PolicyEngine uses Python logic."""
        settings = MagicMock()
        settings.opa_url = ""
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.cost_tracking_enabled = False
        settings.session_dir = tmp_path
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")
        result, reason = engine.evaluate(run)
        assert result in ("allow", "deny", "warn")
        assert isinstance(reason, str)

    def test_evaluate_with_opa_allow_delegates(self, tmp_path: Path) -> None:
        # @trace FR-GOV-001
        """When OPA returns allow, PolicyEngine returns allow."""
        settings = MagicMock()
        settings.opa_url = "http://localhost:8181"
        settings.opa_timeout_ms = 500
        settings.opa_fallback_allow = False
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.cost_tracking_enabled = False
        settings.session_dir = tmp_path
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"allow": True, "reason": "OPA allowed"}}
        mock_resp.raise_for_status.return_value = None
        with patch("thegent.execution.httpx.post", return_value=mock_resp):
            result, reason = engine.evaluate(run)
        assert result == "allow"
        assert "OPA" in reason or "allowed" in reason

    def test_evaluate_with_opa_deny_delegates(self, tmp_path: Path) -> None:
        # @trace FR-GOV-001
        """When OPA returns deny, PolicyEngine returns deny."""
        settings = MagicMock()
        settings.opa_url = "http://localhost:8181"
        settings.opa_timeout_ms = 500
        settings.opa_fallback_allow = False
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.cost_tracking_enabled = False
        settings.session_dir = tmp_path
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"allow": False, "reason": "OPA denied"}}
        mock_resp.raise_for_status.return_value = None
        with patch("thegent.execution.httpx.post", return_value=mock_resp):
            result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "OPA" in reason or "denied" in reason

    def test_evaluate_opa_unreachable_fallback_deny(self, tmp_path: Path) -> None:
        # @trace FR-GOV-001
        """When OPA unreachable and fallback_allow=False, returns deny."""
        settings = MagicMock()
        settings.opa_url = "http://localhost:8181"
        settings.opa_timeout_ms = 500
        settings.opa_fallback_allow = False
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.cost_tracking_enabled = False
        settings.session_dir = tmp_path
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")

        with patch("thegent.execution.httpx.post", side_effect=OSError("connection refused")):
            result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "OPA" in reason or "deny" in reason.lower()

    def test_evaluate_opa_unreachable_fallback_allow(self, tmp_path: Path) -> None:
        # @trace FR-GOV-001
        """When OPA unreachable and fallback_allow=True, returns allow."""
        settings = MagicMock()
        settings.opa_url = "http://localhost:8181"
        settings.opa_timeout_ms = 500
        settings.opa_fallback_allow = True
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.cost_tracking_enabled = False
        settings.session_dir = tmp_path
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")

        with patch("thegent.execution.httpx.post", side_effect=OSError("connection refused")):
            result, reason = engine.evaluate(run)
        assert result == "allow"
        assert "fallback" in reason.lower()

    def test_evaluate_cost_budget_exceeded(self) -> None:
        # @trace FR-GOV-002
        """PolicyEngine blocks execution when cost budget is exceeded."""
        settings = MagicMock()
        settings.opa_url = ""
        settings.environment = "development"
        settings.cost_tracking_enabled = True
        settings.cost_budget_mtd = 10.0
        settings.session_dir = Path("/tmp/fake")

        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="user", lane="standard")

        with patch("thegent.cost.aggregator.CostAggregator.get_mtd_total", return_value=15.0):
            result, reason = engine.evaluate(run)

        assert result == "deny"
        assert "Monthly budget exceeded" in reason

    def test_evaluate_input_guardrail_fails(self) -> None:
        # @trace FR-GOV-003
        """PolicyEngine blocks execution when input guardrail fails."""
        settings = MagicMock()
        settings.opa_url = ""
        settings.environment = "development"
        settings.input_guardrails_enabled = True
        settings.cost_tracking_enabled = False

        engine = PolicyEngine(settings)
        # prompt too long (>65k by default, but let's use a small one via env mock)
        run = RunMeta(agent="gemini", prompt="too_long_prompt", cwd="/tmp", owner="user", lane="standard")

        with patch("thegent.governance.input_guardrails.InputGuardrails.check") as mock_check:
            from thegent.governance.input_guardrails import GuardrailResult

            mock_check.return_value = GuardrailResult(passed=False, rail_id="prompt_length", reason="too long")
            result, reason = engine.evaluate(run)

        assert result == "deny"
        assert "Input guardrail 'prompt_length' failed" in reason


@pytest.mark.unit
class TestCostAggregatorDailyTotal:
    """Tests for CostAggregator.daily_total()."""

    def test_daily_total_no_registry_file(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total returns 0.0 when no registry file exists."""
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == 0.0

    def test_daily_total_empty_registry(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total returns 0.0 for empty registry file."""
        reg_path = tmp_path / "run_registry.jsonl"
        reg_path.write_text("", encoding="utf-8")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == 0.0

    def test_daily_total_sums_today_costs(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total sums cost_usd from today's finish events."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        today = datetime.now(UTC).date().isoformat()
        events = [
            {"event": "finish", "run_id": "r1", "cost_usd": 1.50, "ended_at_utc": f"{today}T10:00:00Z"},
            {"event": "finish", "run_id": "r2", "cost_usd": 2.25, "ended_at_utc": f"{today}T11:00:00Z"},
            {"event": "finish", "run_id": "r3", "cost_usd": 0.75, "ended_at_utc": "2020-01-01T00:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        total = agg.daily_total("user1")
        assert total == pytest.approx(3.75)

    def test_daily_total_ignores_non_finish_events(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total ignores events that are not 'finish'."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        today = datetime.now(UTC).date().isoformat()
        events = [
            {"event": "start", "run_id": "r1", "cost_usd": 99.0, "ended_at_utc": f"{today}T10:00:00Z"},
            {"event": "feedback", "run_id": "r1", "cost_usd": 99.0, "ended_at_utc": f"{today}T10:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == 0.0

    def test_daily_total_ignores_finish_without_cost(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total ignores finish events without cost_usd."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        today = datetime.now(UTC).date().isoformat()
        events = [
            {"event": "finish", "run_id": "r1", "ended_at_utc": f"{today}T10:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == 0.0


@pytest.mark.unit
class TestBlocklistPatternMatching:
    """Tests for InputGuardrails prompt blocklist pattern matching."""

    def test_blocklist_simple_pattern_blocks(self) -> None:
        # @trace FR-GOV-004
        """Simple blocklist pattern blocks matching prompt."""
        g = InputGuardrails(prompt_blocklist_patterns=[r"SECRET_KEY"])
        r = g.check(prompt="Please use SECRET_KEY=abc123")
        assert r.passed is False
        assert r.rail_id == "prompt_blocklist"

    def test_blocklist_regex_pattern_blocks(self) -> None:
        # @trace FR-GOV-004
        """Regex blocklist pattern blocks matching prompt."""
        g = InputGuardrails(prompt_blocklist_patterns=[r"password\s*=\s*\S+"])
        r = g.check(prompt="set password = hunter2")
        assert r.passed is False
        assert r.rail_id == "prompt_blocklist"

    def test_blocklist_no_match_passes(self) -> None:
        # @trace FR-GOV-004
        """Non-matching blocklist patterns pass."""
        g = InputGuardrails(prompt_blocklist_patterns=[r"rm\s+-rf\s+/"])
        r = g.check(prompt="list files in directory")
        assert r.passed is True

    def test_blocklist_invalid_regex_skipped(self) -> None:
        # @trace FR-GOV-004
        """Invalid regex patterns are silently skipped."""
        g = InputGuardrails(prompt_blocklist_patterns=[r"[invalid"])
        r = g.check(prompt="anything")
        assert r.passed is True

    def test_model_allowlist_blocks_unlisted_model(self) -> None:
        # @trace FR-GOV-005
        """Model not in allowlist is blocked."""
        g = InputGuardrails(model_allowlist=["gemini-3-flash", "claude-haiku-4.5"])
        r = g.check(model="gpt-4")
        assert r.passed is False
        assert r.rail_id == "model_allowlist"


@pytest.mark.unit
class TestCostAggregatorMtdTotal:
    """Tests for CostAggregator.get_mtd_total month-to-date calculation."""

    def test_get_mtd_total_no_registry(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total returns 0.0 when no registry file exists."""
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == 0.0

    def test_get_mtd_total_sums_current_month(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total sums cost_usd from current month's finish events."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        events = [
            {"event": "finish", "run_id": "r1", "cost_usd": 2.50, "ended_at_utc": f"{current_month}-01T10:00:00Z"},
            {"event": "finish", "run_id": "r2", "cost_usd": 3.25, "ended_at_utc": f"{current_month}-15T11:00:00Z"},
            {"event": "finish", "run_id": "r3", "cost_usd": 1.00, "ended_at_utc": "2020-01-01T00:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        total = agg.get_mtd_total()
        assert total == pytest.approx(5.75)

    def test_get_mtd_total_ignores_non_finish(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total ignores non-finish events."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        events = [
            {"event": "start", "run_id": "r1", "cost_usd": 99.0, "ended_at_utc": f"{current_month}-01T10:00:00Z"},
            {"event": "feedback", "run_id": "r1", "cost_usd": 99.0, "ended_at_utc": f"{current_month}-01T10:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == 0.0

    def test_get_mtd_total_ignores_finish_without_cost(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total ignores finish events lacking cost_usd."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        events = [
            {"event": "finish", "run_id": "r1", "ended_at_utc": f"{current_month}-01T10:00:00Z"},
        ]
        with reg_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev).decode() + "\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == 0.0

    def test_get_mtd_total_corrupted_lines_skipped(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total skips corrupted JSON lines."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        with reg_path.open("w", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write(
                json.dumps(
                    {
                        "event": "finish",
                        "run_id": "r1",
                        "cost_usd": 1.0,
                        "ended_at_utc": f"{current_month}-01T10:00:00Z",
                    }
                )
                + "\n"
            )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == pytest.approx(1.0)


@pytest.mark.unit
class TestCostEstimatorBranches:
    """Extended tests for CostEstimator branch coverage."""

    def test_estimate_with_tokens_only_known_model(self) -> None:
        # @trace FR-GOV-001
        """Uses pricing table for known model with explicit token counts."""
        est = CostEstimator()
        cost = est.estimate(model="gemini-3-flash", tokens_in=5000, tokens_out=1000)
        expected = (5000 / 1000.0) * 0.0001 + (1000 / 1000.0) * 0.0004
        assert cost == pytest.approx(expected)

    def test_estimate_fallback_with_no_model(self) -> None:
        # @trace FR-GOV-001
        """Uses heuristic fallback when no model provided."""
        est = CostEstimator()
        cost = est.estimate()
        assert cost >= 0

    def test_estimate_fallback_with_unknown_model(self) -> None:
        # @trace FR-GOV-001
        """Uses heuristic fallback when model is unknown."""
        est = CostEstimator()
        cost = est.estimate(model="totally-unknown-model")
        assert cost >= 0

    def test_estimate_custom_pricing(self) -> None:
        # @trace FR-GOV-001
        """Uses custom pricing when overridden."""
        custom_pricing = {"my-model": (0.01, 0.05)}
        est = CostEstimator(pricing=custom_pricing)
        cost = est.estimate(model="my-model", tokens_in=1000, tokens_out=500)
        expected = (1000 / 1000.0) * 0.01 + (500 / 1000.0) * 0.05
        assert cost == pytest.approx(expected)


@pytest.mark.unit
class TestCostAggregatorBlankAndCorruptedLines:
    """Tests for blank/corrupted lines in daily_total and get_mtd_total (lines 65, 72-75, 91, 100-101)."""

    def test_daily_total_skips_blank_lines(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total skips blank lines in registry (line 65)."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        today = datetime.now(UTC).date().isoformat()
        with reg_path.open("w", encoding="utf-8") as f:
            f.write("\n")
            f.write("\n")
            f.write(
                json.dumps(
                    {"event": "finish", "run_id": "r1", "cost_usd": 1.0, "ended_at_utc": f"{today}T10:00:00Z"}
                ).decode()
                + "\n"
            )
            f.write("\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == pytest.approx(1.0)

    def test_daily_total_skips_corrupted_json(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total skips corrupted JSON lines (lines 72-73)."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        today = datetime.now(UTC).date().isoformat()
        with reg_path.open("w", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write("{broken json\n")
            f.write(
                json.dumps(
                    {"event": "finish", "run_id": "r1", "cost_usd": 2.0, "ended_at_utc": f"{today}T10:00:00Z"}
                ).decode()
                + "\n"
            )
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.daily_total("user1") == pytest.approx(2.0)

    def test_daily_total_file_read_error(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """daily_total handles file read errors gracefully (lines 74-75)."""
        reg_path = tmp_path / "run_registry.jsonl"
        reg_path.write_text("valid start\n", encoding="utf-8")
        agg = CostAggregator(session_dir=tmp_path)
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            result = agg.daily_total("user1")
        assert result == 0.0

    def test_get_mtd_total_skips_blank_lines(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total skips blank lines (line 91)."""
        from datetime import UTC, datetime

        reg_path = tmp_path / "run_registry.jsonl"
        now = datetime.now(UTC)
        current_month = f"{now.year}-{now.month:02d}"
        with reg_path.open("w", encoding="utf-8") as f:
            f.write("\n")
            f.write(
                json.dumps(
                    {
                        "event": "finish",
                        "run_id": "r1",
                        "cost_usd": 3.0,
                        "ended_at_utc": f"{current_month}-05T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )
            f.write("\n")
        agg = CostAggregator(session_dir=tmp_path)
        assert agg.get_mtd_total() == pytest.approx(3.0)

    def test_get_mtd_total_file_read_error(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """get_mtd_total handles file read errors (lines 100-101)."""
        reg_path = tmp_path / "run_registry.jsonl"
        reg_path.write_text("valid\n", encoding="utf-8")
        agg = CostAggregator(session_dir=tmp_path)
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            result = agg.get_mtd_total()
        assert result == 0.0


@pytest.mark.unit
class TestGuardrailsFromEnvBranches:
    """Tests for guardrails_from_settings env var branches (lines 105-106, 111, 116, 121)."""

    def test_invalid_prompt_max_chars_uses_default(self) -> None:
        # @trace FR-GOV-007
        """Invalid THGENT_PROMPT_MAX_CHARS falls back to default (lines 105-106)."""
        with patch.dict(os.environ, {"THGENT_PROMPT_MAX_CHARS": "not_a_number"}, clear=False):
            g = guardrails_from_settings()
        assert g.prompt_max_chars == 65536

    def test_blocklist_from_env(self) -> None:
        # @trace FR-GOV-007
        """THGENT_PROMPT_BLOCKLIST_PATTERNS parsed from env (line 111)."""
        with patch.dict(os.environ, {"THGENT_PROMPT_BLOCKLIST_PATTERNS": "SECRET,PASSWORD"}, clear=False):
            g = guardrails_from_settings()
        assert "SECRET" in g.prompt_blocklist_patterns
        assert "PASSWORD" in g.prompt_blocklist_patterns

    def test_agent_allowlist_from_env(self) -> None:
        # @trace FR-GOV-007
        """THGENT_AGENT_ALLOWLIST parsed from env (line 116)."""
        with patch.dict(os.environ, {"THGENT_AGENT_ALLOWLIST": "gemini,claude"}, clear=False):
            g = guardrails_from_settings()
        assert "gemini" in g.agent_allowlist
        assert "claude" in g.agent_allowlist

    def test_cwd_prefixes_from_env(self) -> None:
        # @trace FR-GOV-007
        """THGENT_CWD_ALLOWED_PREFIXES parsed from env (line 121)."""
        with patch.dict(os.environ, {"THGENT_CWD_ALLOWED_PREFIXES": "/home,/workspace"}, clear=False):
            g = guardrails_from_settings()
        assert "/home" in g.cwd_allowed_prefixes
        assert "/workspace" in g.cwd_allowed_prefixes
