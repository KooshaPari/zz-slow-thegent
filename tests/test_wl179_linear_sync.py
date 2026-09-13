"""Tests for WL-179: Linear Sync Integration Tests.

@pytest.mark.requirement("WL-179")
"""

from __future__ import annotations

import pytest

from thegent.integrations.linear_sync_integration import (
    LinearSyncIntegrationSuite,
    LinearSyncTestResult,
)


class TestLinearSyncTestResult:
    """Test the LinearSyncTestResult dataclass."""

    @pytest.mark.requirement("WL-179")
    def test_linear_sync_test_result_creation(self) -> None:
        """Test creating a LinearSyncTestResult."""
        result = LinearSyncTestResult(test_name="test_cycle", passed=True)
        assert result.test_name == "test_cycle"
        assert result.passed is True
        assert result.details == ""

    @pytest.mark.requirement("WL-179")
    def test_linear_sync_test_result_with_details(self) -> None:
        """Test creating a LinearSyncTestResult with details."""
        result = LinearSyncTestResult(
            test_name="test_cycle", passed=False, details="GraphQL query failed"
        )
        assert result.test_name == "test_cycle"
        assert result.passed is False
        assert result.details == "GraphQL query failed"

    @pytest.mark.requirement("WL-179")
    def test_linear_sync_test_result_all_fields(self) -> None:
        """Test all fields of LinearSyncTestResult."""
        result = LinearSyncTestResult(
            test_name="test_graphql",
            passed=True,
            details="Fixture validated",
        )
        assert result.test_name == "test_graphql"
        assert result.passed is True
        assert result.details == "Fixture validated"


class TestLinearSyncIntegrationSuite:
    """Test the LinearSyncIntegrationSuite."""

    @pytest.mark.requirement("WL-179")
    def test_suite_initialization(self) -> None:
        """Test suite initialization."""
        suite = LinearSyncIntegrationSuite()
        assert suite is not None

    @pytest.mark.requirement("WL-179")
    def test_add_single_test(self) -> None:
        """Test adding a single test."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_cycle", lambda: True)
        # Verify internal state (indirectly through run_all)
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].test_name == "test_cycle"
        assert results[0].passed is True

    @pytest.mark.requirement("WL-179")
    def test_add_multiple_tests(self) -> None:
        """Test adding multiple tests."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_query", lambda: True)
        suite.add_test("test_mutation", lambda: True)
        suite.add_test("test_subscription", lambda: False)

        results = suite.run_all()
        assert len(results) == 3
        assert results[0].test_name == "test_query"
        assert results[1].test_name == "test_mutation"
        assert results[2].test_name == "test_subscription"

    @pytest.mark.requirement("WL-179")
    def test_add_test_with_details(self) -> None:
        """Test adding a test with details."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test(
            "test_cycle_status",
            lambda: True,
            details="Tests mock Linear GraphQL cycle responses",
        )
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].details == "Tests mock Linear GraphQL cycle responses"

    @pytest.mark.requirement("WL-179")
    def test_run_all_with_passing_tests(self) -> None:
        """Test running all tests where all pass."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: True)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        assert len(results) == 3
        assert all(r.passed for r in results)

    @pytest.mark.requirement("WL-179")
    def test_run_all_with_failing_tests(self) -> None:
        """Test running all tests where some fail."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        assert len(results) == 3
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[2].passed is True

    @pytest.mark.requirement("WL-179")
    def test_run_all_with_exception_in_test(self) -> None:
        """Test handling of exceptions in test functions."""

        def failing_test() -> bool:
            raise RuntimeError("GraphQL error")

        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_error", failing_test)
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].passed is False
        assert "Exception" in results[0].details
        assert "GraphQL error" in results[0].details

    @pytest.mark.requirement("WL-179")
    def test_run_all_preserves_order(self) -> None:
        """Test that run_all preserves test order."""
        suite = LinearSyncIntegrationSuite()
        for i in range(5):
            suite.add_test(f"test_{i}", lambda: True)

        results = suite.run_all()
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.test_name == f"test_{i}"

    @pytest.mark.requirement("WL-179")
    def test_summary_all_passed(self) -> None:
        """Test summary with all passing tests."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: True)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        summary = LinearSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 3
        assert summary["failed"] == 0

    @pytest.mark.requirement("WL-179")
    def test_summary_all_failed(self) -> None:
        """Test summary with all failing tests."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", lambda: False)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: False)

        results = suite.run_all()
        summary = LinearSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 0
        assert summary["failed"] == 3

    @pytest.mark.requirement("WL-179")
    def test_summary_mixed(self) -> None:
        """Test summary with mixed results."""
        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: True)
        suite.add_test("test_4", lambda: False)
        suite.add_test("test_5", lambda: True)

        results = suite.run_all()
        summary = LinearSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 3
        assert summary["failed"] == 2

    @pytest.mark.requirement("WL-179")
    def test_summary_empty(self) -> None:
        """Test summary with no tests."""
        suite = LinearSyncIntegrationSuite()
        results = suite.run_all()
        summary = LinearSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 0
        assert summary["failed"] == 0

    @pytest.mark.requirement("WL-179")
    def test_run_all_empty(self) -> None:
        """Test run_all with no tests registered."""
        suite = LinearSyncIntegrationSuite()
        results = suite.run_all()
        assert len(results) == 0
        assert results == []

    @pytest.mark.requirement("WL-179")
    def test_stateful_test_function(self) -> None:
        """Test that test functions can be stateful."""
        state = {"count": 0}

        def stateful_test() -> bool:
            state["count"] += 1
            return state["count"] <= 2

        suite = LinearSyncIntegrationSuite()
        suite.add_test("test_1", stateful_test)
        suite.add_test("test_2", stateful_test)
        suite.add_test("test_3", stateful_test)

        results = suite.run_all()
        assert results[0].passed is True
        assert results[1].passed is True
        assert results[2].passed is False
