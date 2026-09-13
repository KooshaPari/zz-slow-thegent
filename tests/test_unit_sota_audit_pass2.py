"""SOTA Audit Pass 2 — Phase 3/4 hardening surface validation.

Validates the expanded hardening surface introduced during the Phase 3/4
SOTA audit, covering:

1. MCP performance gates module exports
2. Infra performance budget module exports
3. Governance policy-engine thread-safety
4. Cockpit clock injection
5. Decision audit trail (thread-safe flush)
6. UX explanations (exit-code / exception mappings)
7. MCP server contract functions
"""

from __future__ import annotations

import inspect
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from thegent.infra.perf_budget import (
    BudgetResult,
    PerformanceBudgetError,
    budget_context,
    check_memory_budget,
    check_module_load_budget,
    get_perf_summary,
)
from thegent.mcp.server import (
    thegent_observe_summary,
    thegent_session_contract_health_gate,
)
from thegent.mcp.server.mcp_perf_gates import (
    MCP_PERF_BUDGETS,
    MCPBudgetExceeded,
    check_mcp_budget,
    mcp_budget_context,
)
from thegent.ux.cockpit import OperatorCockpit
from thegent.ux.decision_audit import DecisionAuditAppender
from thegent.ux.explanations import (
    EXPLANATION_MAP,
    explain_exception,
    explain_exit_code,
)

# =====================================================================
# 1. mcp_perf_gates module exports
# =====================================================================


class TestMCPPerfGatesExports:
    """Verify the four public symbols from mcp_perf_gates are importable."""

    @pytest.mark.parametrize(
        "symbol_name",
        ["MCP_PERF_BUDGETS", "MCPBudgetExceeded", "check_mcp_budget", "mcp_budget_context"],
        ids=["budgets_dict", "exception", "check_fn", "context_mgr"],
    )
    def test_symbol_importable(self, symbol_name: str) -> None:
        import thegent.mcp.server.mcp_perf_gates as mod

        assert hasattr(mod, symbol_name), f"{symbol_name} missing from mcp_perf_gates"

    def test_budgets_dict_non_empty(self) -> None:
        assert len(MCP_PERF_BUDGETS) > 0

    def test_exception_is_exception(self) -> None:
        assert issubclass(MCPBudgetExceeded, Exception)

    def test_check_fn_is_callable(self) -> None:
        assert callable(check_mcp_budget)

    def test_context_mgr_is_callable(self) -> None:
        assert callable(mcp_budget_context)


# =====================================================================
# 2. perf_budget module exports
# =====================================================================


class TestPerfBudgetExports:
    """Verify the six public symbols from infra.perf_budget are importable."""

    @pytest.mark.parametrize(
        "symbol_name",
        [
            "check_module_load_budget",
            "check_memory_budget",
            "budget_context",
            "get_perf_summary",
            "PerformanceBudgetError",
            "BudgetResult",
        ],
        ids=[
            "module_load_gate",
            "memory_gate",
            "budget_ctx",
            "perf_summary",
            "error_cls",
            "result_cls",
        ],
    )
    def test_symbol_importable(self, symbol_name: str) -> None:
        import thegent.infra.perf_budget as mod

        assert hasattr(mod, symbol_name), f"{symbol_name} missing from perf_budget"

    def test_error_is_exception(self) -> None:
        assert issubclass(PerformanceBudgetError, Exception)

    def test_budget_result_is_dataclass(self) -> None:
        assert hasattr(BudgetResult, "__dataclass_fields__")

    def test_perf_summary_returns_dict(self) -> None:
        summary = get_perf_summary()
        assert isinstance(summary, dict)
        assert "checked_modules" in summary
        assert "peak_memory_bytes" in summary
        assert "violations" in summary

    def test_memory_budget_within_limit(self) -> None:
        """A generous memory budget should pass on any CI/dev machine."""
        rss = check_memory_budget("sota_pass2_test", max_bytes=2**40)  # 1 TiB
        assert isinstance(rss, int)
        assert rss > 0

    def test_module_load_budget_stdlib(self) -> None:
        """Standard library 'json' should load within 50ms."""
        elapsed = check_module_load_budget("json", max_load_ms=50.0)
        assert isinstance(elapsed, float)
        assert elapsed >= 0.0

    def test_budget_context_yields_result(self) -> None:
        with budget_context("sota_pass2_ctx") as result:
            x = sum(range(100))
        assert isinstance(result, BudgetResult)
        assert result.label == "sota_pass2_ctx"
        assert result.elapsed_ms >= 0.0
        assert result.peak_memory_bytes > 0
        assert x >= 0  # ensure block executed


# =====================================================================
# 3. Governance policy-engine thread-safety
# =====================================================================


class TestGovernanceThreadSafety:
    """PolicyEngine and FederatedPolicyEngine must expose a _lock attribute."""

    @pytest.mark.parametrize(
        "cls_path",
        [
            "thegent.governance.policy_engine.PolicyEngine",
            "thegent.governance.federated_policy.FederatedPolicyEngine",
        ],
        ids=["PolicyEngine", "FederatedPolicyEngine"],
    )
    def test_has_lock_attribute(self, cls_path: str) -> None:
        import importlib

        module_path, class_name = cls_path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        obj = cls()
        assert hasattr(obj, "_lock"), f"{class_name} missing _lock attribute"

    @pytest.mark.parametrize(
        "cls_path",
        [
            "thegent.governance.policy_engine.PolicyEngine",
            "thegent.governance.federated_policy.FederatedPolicyEngine",
        ],
        ids=["PolicyEngine", "FederatedPolicyEngine"],
    )
    def test_lock_is_reentrant(self, cls_path: str) -> None:
        import importlib

        module_path, class_name = cls_path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        obj = cls()
        assert isinstance(obj._lock, type(threading.RLock())), f"{class_name}._lock is not an RLock instance"


# =====================================================================
# 4. Cockpit clock injection
# =====================================================================


class TestCockpitClockInjection:
    """OperatorCockpit must accept and use a clock parameter."""

    def test_clock_parameter_accepted(self) -> None:
        import inspect

        sig = inspect.signature(OperatorCockpit.__init__)
        assert "clock" in sig.parameters, "OperatorCockpit.__init__ missing clock param"

    def test_injected_clock_is_used(self) -> None:
        """A deterministic clock should produce predictable tick_at values."""
        fixed_now = 1_700_000_000.0

        def clock() -> float:
            return fixed_now

        cockpit = OperatorCockpit(clock=clock)
        cockpit.tick()
        snap = cockpit.snapshot()
        assert snap["tick_at"] == fixed_now

    def test_default_clock_falls_back_to_time(self) -> None:
        """Without an explicit clock the cockpit should still tick."""
        cockpit = OperatorCockpit()
        before = time.time()
        cockpit.tick()
        after = time.time()
        snap = cockpit.snapshot()
        assert before <= snap["tick_at"] <= after


# =====================================================================
# 5. Decision audit trail — thread-safe flush
# =====================================================================


class TestDecisionAuditTrail:
    """DecisionAuditAppender.flush must be thread-safe."""

    def test_flush_returns_bool(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(
            audit_path=tmp_path / "audit.jsonl",
            fsync=False,
        )
        result = appender.flush()
        assert isinstance(result, bool)

    def test_flush_no_fsync_returns_false(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(
            audit_path=tmp_path / "audit.jsonl",
            fsync=False,
        )
        assert appender.flush() is False

    def test_concurrent_flush_no_raise(self, tmp_path: Path) -> None:
        """Multiple threads flushing simultaneously must not raise."""
        appender = DecisionAuditAppender(
            audit_path=tmp_path / "audit.jsonl",
            fsync=False,
        )
        errors: list[BaseException] = []

        def _flush_worker() -> None:
            try:
                for _ in range(50):
                    appender.flush()
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_flush_worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
        assert errors == [], f"Concurrent flush raised: {errors}"

    def test_record_and_flush(self, tmp_path: Path) -> None:
        from thegent.ux.cockpit import DecisionNotice

        appender = DecisionAuditAppender(
            audit_path=tmp_path / "audit.jsonl",
            fsync=True,
            fsync_every_n=1,
        )
        notice = DecisionNotice(
            verdict="deny",
            reason_code="test_code",
            rule_id="test.rule",
            agent="sota_audit",
            lane="standard",
            evaluated_at=time.time(),
            reason="pass2 test",
        )
        appender.record(notice)
        flushed = appender.flush()
        # With fsync=True and fsync_every_n=1, flush should be a no-op
        # because the single record already triggered fsync.
        assert isinstance(flushed, bool)


# =====================================================================
# 6. UX explanations
# =====================================================================


class TestUXExplanations:
    """explain_exit_code, explain_exception, and EXPLANATION_MAP contracts."""

    @pytest.mark.parametrize(
        ("code", "expected_substring"),
        [
            (0, "success"),
            (1, "general error"),
            (2, "misuse"),
            (3, "policy deny"),
            (4, "replay mismatch"),
            (127, "command not found"),
            (130, "interrupted"),
        ],
        ids=["exit_0", "exit_1", "exit_2", "exit_3", "exit_4", "exit_127", "exit_130"],
    )
    def test_explain_exit_code_known(self, code: int, expected_substring: str) -> None:
        result = explain_exit_code(code)
        assert isinstance(result, str)
        assert expected_substring in result.lower()

    def test_explain_exit_code_unknown(self) -> None:
        result = explain_exit_code(999)
        assert "999" in result
        assert isinstance(result, str)

    def test_explanation_map_keys_are_ints(self) -> None:
        for key in EXPLANATION_MAP:
            assert isinstance(key, int), f"EXPLANATION_MAP key {key!r} is not int"

    def test_explanation_map_values_are_strings(self) -> None:
        for val in EXPLANATION_MAP.values():
            assert isinstance(val, str), f"EXPLANATION_MAP value {val!r} is not str"

    @pytest.mark.parametrize(
        ("exc", "expected_substring"),
        [
            (TimeoutError("timed out"), "timeout"),
            (PermissionError("denied"), "permission denied"),
            (ConnectionError("failed"), "connection failed"),
            (FileNotFoundError("missing"), "file not found"),
            (ValueError("bad input"), "validation error"),
            (KeyError("missing_key"), "missing key"),
        ],
        ids=[
            "timeout",
            "permission",
            "connection",
            "file_not_found",
            "value_error",
            "key_error",
        ],
    )
    def test_explain_exception_known_types(self, exc: Exception, expected_substring: str) -> None:
        result = explain_exception(exc)
        assert isinstance(result, str)
        assert expected_substring in result.lower()

    def test_explain_exception_unknown_type(self) -> None:
        class CustomError(Exception):
            pass

        result = explain_exception(CustomError("something broke"))
        assert "CustomError" in result
        assert isinstance(result, str)


# =====================================================================
# 7. MCP server contract functions exist
# =====================================================================


class TestMCPServerContractFunctions:
    """thegent_observe_summary and thegent_session_contract_health_gate
    must be importable and callable."""

    @pytest.mark.parametrize(
        "fn",
        [thegent_observe_summary, thegent_session_contract_health_gate],
        ids=["observe_summary", "contract_health_gate"],
    )
    def test_function_is_callable(self, fn: Any) -> None:
        assert callable(fn)

    @pytest.mark.parametrize(
        "fn",
        [thegent_observe_summary, thegent_session_contract_health_gate],
        ids=["observe_summary", "contract_health_gate"],
    )
    def test_function_has_expected_signature(self, fn: Any) -> None:
        sig = inspect.signature(fn)
        params = sig.parameters
        # Both functions accept keyword arguments at minimum;
        # observe_summary expects at least 'limit', 'drift_window'
        assert len(params) >= 2, f"{fn.__name__} has fewer than 2 parameters"
