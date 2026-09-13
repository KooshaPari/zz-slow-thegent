"""Performance benchmarks for critical code paths.

Measures wall time for core governance, orchestration, and registry
operations to catch regressions and establish baselines.

# @trace PERF-CRITICAL-001
"""

from __future__ import annotations

import time

import pytest

from thegent.contracts.capability_registry import Capability, CapabilityRegistry
from thegent.governance.costs import CostTracker
from thegent.governance.policy import LearningSession, PolicyManager
from thegent.governance.redaction import PIIRedactor
from thegent.governance.semantic_firewall import SemanticFirewall
from thegent.governance.tee_check import TEEChecker
from thegent.orchestration.plan import OrchestrationPlan
from thegent.orchestration.sub_agent_dispatcher.dispatch_result import DispatchResult
from thegent.orchestration.sub_agent_dispatcher.topological_sort import (
    topological_order,
)

pytestmark = pytest.mark.performance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _benchmark(name: str, iterations: int, func, threshold_ms: float) -> dict:
    """Run *func* for *iterations* and return timing stats."""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    elapsed = time.perf_counter() - start
    per_iter_us = (elapsed / iterations) * 1_000_000
    result = {
        "name": name,
        "iterations": iterations,
        "elapsed_s": elapsed,
        "per_iter_us": per_iter_us,
        "threshold_ms": threshold_ms,
    }
    print(f"  {name}: {elapsed * 1000:.2f}ms total, {per_iter_us:.1f}us/iter ({iterations} iterations)")
    return result


def _assert_within_threshold(name: str, elapsed_s: float, threshold_ms: float) -> None:
    elapsed_ms = elapsed_s * 1000
    assert elapsed_ms < threshold_ms, f"{name} exceeded threshold: {elapsed_ms:.2f}ms > {threshold_ms}ms"


# ---------------------------------------------------------------------------
# 1. DispatchResult construction
# ---------------------------------------------------------------------------


class TestBenchmarkDispatchResult:
    """Benchmark DispatchResult construction."""

    def test_dispatch_result_1000_iterations(self) -> None:
        iterations = 1000

        def build():
            DispatchResult(node_id="node_1", output="result data", success=True, error="")

        result = _benchmark("DispatchResult construction", iterations, build, threshold_ms=100)
        _assert_within_threshold(result["name"], result["elapsed_s"], 100)


# ---------------------------------------------------------------------------
# 2. topological_order on a 50-node DAG
# ---------------------------------------------------------------------------


class TestBenchmarkTopologicalSort:
    """Benchmark topological_order on a 50-node DAG."""

    @pytest.fixture()
    def plan_50_nodes(self) -> OrchestrationPlan:
        plan = OrchestrationPlan(goal="benchmark 50-node DAG")
        for i in range(50):
            deps = [plan.nodes[i // 2].id] if i > 0 else []
            plan.add_task(f"task_{i}", depends_on=deps)
        return plan

    def test_topological_order_50_nodes(self, plan_50_nodes: OrchestrationPlan) -> None:
        iterations = 200

        def sort_plan():
            topological_order(plan_50_nodes)

        result = _benchmark("topological_order (50-node DAG)", iterations, sort_plan, threshold_ms=500)
        _assert_within_threshold(result["name"], result["elapsed_s"], 500)


# ---------------------------------------------------------------------------
# 3. CapabilityRegistry.get_capability (1000 lookups)
# ---------------------------------------------------------------------------


class TestBenchmarkCapabilityRegistry:
    """Benchmark CapabilityRegistry.get_capability lookups."""

    @pytest.fixture()
    def registry(self) -> CapabilityRegistry:
        reg = CapabilityRegistry()
        for i in range(20):
            reg.register(Capability(id=f"bench.cap.{i}", version="1.0", trust_level=3))
        return reg

    def test_get_capability_1000_lookups(self, registry: CapabilityRegistry) -> None:
        iterations = 1000

        def lookup():
            registry.get_capability("bench.cap.15")

        result = _benchmark("CapabilityRegistry.get_capability", iterations, lookup, threshold_ms=50)
        _assert_within_threshold(result["name"], result["elapsed_s"], 50)


# ---------------------------------------------------------------------------
# 4. PolicyManager + LearningSession cycle
# ---------------------------------------------------------------------------


class TestBenchmarkPolicyLearningCycle:
    """Benchmark PolicyManager and LearningSession lifecycle."""

    def test_policy_learning_cycle(self) -> None:
        iterations = 1000

        def cycle():
            pm = PolicyManager({"cost_cap": 5.0, "max_tokens": 4096})
            session = LearningSession(pm)
            session.start()
            assert session.is_valid() is True
            pm.update({"cost_cap": 10.0})
            assert session.is_valid() is True

        result = _benchmark("PolicyManager + LearningSession cycle", iterations, cycle, threshold_ms=100)
        _assert_within_threshold(result["name"], result["elapsed_s"], 100)


# ---------------------------------------------------------------------------
# 5. PIIRedactor.redact on 1KB text
# ---------------------------------------------------------------------------


class TestBenchmarkPIIRedactor:
    """Benchmark PIIRedactor.redact on 1KB text."""

    @pytest.fixture()
    def redactor(self) -> PIIRedactor:
        return PIIRedactor()

    @pytest.fixture()
    def text_1kb(self) -> str:
        base = (
            "Contact alice@example.com or call 555-123-4567. "
            "SSN: 123-45-6789. Token: sk-abcdefghijklmnopqrstuvwxyz1234567890. "
            "Auth: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9. "
            "Send to bob@example.com and carol@example.com. "
        )
        return base * 8  # ~1KB

    def test_redact_1000_iterations(self, redactor: PIIRedactor, text_1kb: str) -> None:
        iterations = 1000

        def redact():
            redactor.redact(text_1kb)

        result = _benchmark("PIIRedactor.redact (1KB)", iterations, redact, threshold_ms=5000)
        _assert_within_threshold(result["name"], result["elapsed_s"], 5000)


# ---------------------------------------------------------------------------
# 6. SemanticFirewall.inspect_output
# ---------------------------------------------------------------------------


class TestBenchmarkSemanticFirewall:
    """Benchmark SemanticFirewall.inspect_output."""

    @pytest.fixture()
    def firewall(self) -> SemanticFirewall:
        return SemanticFirewall()

    def test_inspect_output_clean(self, firewall: SemanticFirewall) -> None:
        output = "The agent completed the task successfully. No issues found."
        iterations = 1000

        def inspect():
            firewall.inspect_output(output)

        result = _benchmark("SemanticFirewall.inspect_output (clean)", iterations, inspect, threshold_ms=500)
        _assert_within_threshold(result["name"], result["elapsed_s"], 500)

    def test_inspect_output_with_redact_match(self, firewall: SemanticFirewall) -> None:
        output = "password = 'hunter2' and the system is ready."
        iterations = 1000

        def inspect():
            firewall.inspect_output(output)

        result = _benchmark("SemanticFirewall.inspect_output (redact match)", iterations, inspect, threshold_ms=1000)
        _assert_within_threshold(result["name"], result["elapsed_s"], 1000)


# ---------------------------------------------------------------------------
# 7. CostTracker lifecycle (start + record + query)
# ---------------------------------------------------------------------------


class TestBenchmarkCostTracker:
    """Benchmark CostTracker full lifecycle."""

    def test_cost_tracker_lifecycle(self) -> None:
        iterations = 1000

        def lifecycle():
            tracker = CostTracker()
            tracker.start_session("bench_session")
            tracker.record_cost("bench_session", 1.5)
            tracker.record_cost("bench_session", 2.3)
            total = tracker.get_session_cost("bench_session")
            assert total == 3.8
            assert tracker.is_within_budget("bench_session", 10.0)

        result = _benchmark("CostTracker lifecycle", iterations, lifecycle, threshold_ms=100)
        _assert_within_threshold(result["name"], result["elapsed_s"], 100)

    def test_cost_tracker_heavy_recording(self) -> None:
        iterations = 100

        def heavy():
            tracker = CostTracker()
            tracker.start_session("heavy")
            for i in range(100):
                tracker.record_cost("heavy", 0.01 * i)
            total = tracker.get_session_cost("heavy")
            assert total > 0

        result = _benchmark("CostTracker (100 records)", iterations, heavy, threshold_ms=200)
        _assert_within_threshold(result["name"], result["elapsed_s"], 200)


# ---------------------------------------------------------------------------
# 8. TEEChecker.check in mock mode
# ---------------------------------------------------------------------------


class TestBenchmarkTEEChecker:
    """Benchmark TEEChecker.check in mock mode."""

    def test_tee_check_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THEGENT_TEE_MOCK", "true")
        iterations = 100

        def check():
            checker = TEEChecker(mock_mode=True)
            att = checker.check()
            assert att.is_attested is True

        result = _benchmark("TEEChecker.check (mock)", iterations, check, threshold_ms=5000)
        _assert_within_threshold(result["name"], result["elapsed_s"], 5000)
