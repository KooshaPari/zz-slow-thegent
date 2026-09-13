"""Unit tests for ``thegent.mcp.server.mcp_perf_gates`` (SOTA audit).

Audit findings (Lane 3 — comprehensive surface audit across Phase 3/4 modules):

+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| Module                      | Docstring | Types| Thread   | Error     | __all__ | Defensive       |
|                             |           |      | Safety   | Handling  |         | Checks          |
+=============================+===========+======+==========+===========+=========+=================+
| mcp_audit_trail.py          | ✓         | ✓    | ✓        | ✓         | ✗ miss  | ⚠ max_entries   |
|                             |           |      |          |           |         |   not validated  |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| mcp_server_contracts.py     | ✓         | ✓    | N/A      | ✓         | ✗ miss  | ✓               |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| decision_audit.py           | ✓         | ✗¹   | ✓        | ✓         | ⚠²     | ✓               |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| cockpit.py                  | ✓         | ✓    | ✓        | ✓         | ✓       | ✓               |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| policy_engine.py            | ✓         | ✓    | ✓        | ✓         | ✓       | ✓               |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+
| federated_policy.py         | ✓         | ✓    | ✓        | ✓         | ✗ miss  | ⚠ load_from_   |
|                             |           |      |          |           |         |   file shallow  |
+-----------------------------+-----------+------+----------+-----------+---------+-----------------+

¹ ``flush()`` returned ``bool`` at runtime but was annotated ``-> None`` — fixed.
² ``__all__`` omits ``DEFAULT_MAX_BYTES``, ``DEFAULT_MAX_LINES``, ``DEFAULT_MAX_BACKUPS`` constants.
"""

from __future__ import annotations

import threading
import time

import pytest

from thegent.mcp.server.mcp_perf_gates import (
    MCP_PERF_BUDGETS,
    MCPBudgetExceeded,
    check_mcp_budget,
    mcp_budget_context,
)

# ------------------------------------------------------------------
# MCPBudgetExceeded contract
# ------------------------------------------------------------------


class TestMCPBudgetExceededContract:
    """Verify the exception's shape and message."""

    def test_fields_attached(self) -> None:
        exc = MCPBudgetExceeded("tool_invoke_ms", 120.0, 100.0)
        assert exc.operation == "tool_invoke_ms"
        assert exc.elapsed_ms == 120.0
        assert exc.budget_ms == 100.0

    def test_message_contains_operation(self) -> None:
        exc = MCPBudgetExceeded("resource_read_ms", 80.0, 50.0)
        assert "resource_read_ms" in str(exc)
        assert "80.0ms" in str(exc)
        assert "50.0ms" in str(exc)

    def test_is_exception_subclass(self) -> None:
        assert issubclass(MCPBudgetExceeded, Exception)


# ------------------------------------------------------------------
# check_mcp_budget
# ------------------------------------------------------------------


class TestCheckMCPBudget:
    """Validate the budget check helper."""

    def test_within_budget_passes(self) -> None:
        check_mcp_budget("tool_invoke_ms", 99.9)

    def test_exact_budget_passes(self) -> None:
        check_mcp_budget("gate_check_ms", 20.0)

    def test_exceeds_budget_raises(self) -> None:
        with pytest.raises(MCPBudgetExceeded) as exc_info:
            check_mcp_budget("gate_check_ms", 21.0)
        assert exc_info.value.operation == "gate_check_ms"

    def test_unknown_operation_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            check_mcp_budget("nonexistent_operation_ms", 1.0)


# ------------------------------------------------------------------
# mcp_budget_context
# ------------------------------------------------------------------


class TestMCPBudgetContext:
    """Validate the context-manager timing path."""

    def test_fast_block_passes(self) -> None:
        with mcp_budget_context("gate_check_ms"):
            pass

    def test_slow_block_raises(self) -> None:
        with pytest.raises(MCPBudgetExceeded):
            with mcp_budget_context("gate_check_ms"):
                time.sleep(0.05)

    def test_custom_budget_overrides_named(self) -> None:
        # 0.001ms budget — almost certainly exceeded by sleep
        with pytest.raises(MCPBudgetExceeded):
            with mcp_budget_context("gate_check_ms", budget_ms=0.001):
                time.sleep(0.01)

    def test_custom_budget_within(self) -> None:
        # Generous budget — should pass
        with mcp_budget_context("gate_check_ms", budget_ms=5000.0):
            pass


# ------------------------------------------------------------------
# MCP_PERF_BUDGETS dict shape
# ------------------------------------------------------------------


class TestMCPPerfBudgets:
    """Validate the budget dictionary."""

    def test_is_dict(self) -> None:
        assert isinstance(MCP_PERF_BUDGETS, dict)

    def test_all_values_positive_float(self) -> None:
        for key, val in MCP_PERF_BUDGETS.items():
            assert isinstance(val, float), f"{key} is not float"
            assert val > 0, f"{key} is not positive"

    def test_known_keys_present(self) -> None:
        required = {"tool_invoke_ms", "resource_read_ms", "gate_check_ms"}
        assert required.issubset(MCP_PERF_BUDGETS.keys())

    def test_string_keys(self) -> None:
        for key in MCP_PERF_BUDGETS:
            assert isinstance(key, str)


# ------------------------------------------------------------------
# Thread-safety
# ------------------------------------------------------------------


class TestMCPPerfGatesThreadSafety:
    """Concurrent check_mcp_budget calls should not race."""

    def test_concurrent_checks_dont_raise_spurious(self) -> None:
        """Many threads checking within-budget values must all pass."""
        errors: list[BaseException] = []

        def _check() -> None:
            try:
                for _ in range(100):
                    check_mcp_budget("tool_invoke_ms", 50.0)
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_check) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
        assert errors == []

    def test_concurrent_budget_exceeded(self) -> None:
        """Over-budget calls from multiple threads must raise."""
        raised = threading.Event()
        lock = threading.Lock()
        count = 0

        def _check() -> None:
            nonlocal count
            try:
                for _ in range(50):
                    check_mcp_budget("gate_check_ms", 999.0)
            except MCPBudgetExceeded:
                with lock:
                    count += 1
                    raised.set()

        threads = [threading.Thread(target=_check) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
        assert raised.is_set()
        assert count == 6
