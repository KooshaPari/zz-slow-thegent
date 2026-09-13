"""Tests for WL-178: GitHub Sync Integration Tests.

@pytest.mark.requirement("WL-178")
"""

from __future__ import annotations

import pytest

from thegent.integrations.github_sync_integration import (
    GitHubSyncIntegrationSuite,
    SyncTestResult,
)


class TestSyncTestResult:
    """Test the SyncTestResult dataclass."""

    @pytest.mark.requirement("WL-178")
    def test_sync_test_result_creation(self) -> None:
        """Test creating a SyncTestResult."""
        result = SyncTestResult(test_name="test_pull", passed=True)
        assert result.test_name == "test_pull"
        assert result.passed is True
        assert result.details == ""

    @pytest.mark.requirement("WL-178")
    def test_sync_test_result_with_details(self) -> None:
        """Test creating a SyncTestResult with details."""
        result = SyncTestResult(
            test_name="test_pull", passed=False, details="Connection timeout"
        )
        assert result.test_name == "test_pull"
        assert result.passed is False
        assert result.details == "Connection timeout"

    @pytest.mark.requirement("WL-178")
    def test_sync_test_result_all_fields(self) -> None:
        """Test all fields of SyncTestResult."""
        result = SyncTestResult(
            test_name="test_integration",
            passed=True,
            details="Mocked response validated",
        )
        assert result.test_name == "test_integration"
        assert result.passed is True
        assert result.details == "Mocked response validated"


class TestGitHubSyncIntegrationSuite:
    """Test the GitHubSyncIntegrationSuite."""

    @pytest.mark.requirement("WL-178")
    def test_suite_initialization(self) -> None:
        """Test suite initialization."""
        suite = GitHubSyncIntegrationSuite()
        assert suite is not None

    @pytest.mark.requirement("WL-178")
    def test_add_single_test(self) -> None:
        """Test adding a single test."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_pull", lambda: True)
        # Verify internal state (indirectly through run_all)
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].test_name == "test_pull"
        assert results[0].passed is True

    @pytest.mark.requirement("WL-178")
    def test_add_multiple_tests(self) -> None:
        """Test adding multiple tests."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_pull", lambda: True)
        suite.add_test("test_push", lambda: True)
        suite.add_test("test_merge", lambda: False)

        results = suite.run_all()
        assert len(results) == 3
        assert results[0].test_name == "test_pull"
        assert results[1].test_name == "test_push"
        assert results[2].test_name == "test_merge"

    @pytest.mark.requirement("WL-178")
    def test_add_test_with_details(self) -> None:
        """Test adding a test with details."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test(
            "test_pr",
            lambda: True,
            details="Tests mock GitHub pull request responses",
        )
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].details == "Tests mock GitHub pull request responses"

    @pytest.mark.requirement("WL-178")
    def test_run_all_with_passing_tests(self) -> None:
        """Test running all tests where all pass."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: True)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        assert len(results) == 3
        assert all(r.passed for r in results)

    @pytest.mark.requirement("WL-178")
    def test_run_all_with_failing_tests(self) -> None:
        """Test running all tests where some fail."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        assert len(results) == 3
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[2].passed is True

    @pytest.mark.requirement("WL-178")
    def test_run_all_with_exception_in_test(self) -> None:
        """Test handling of exceptions in test functions."""

        def failing_test() -> bool:
            raise ValueError("Mock error")

        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_error", failing_test)
        results = suite.run_all()
        assert len(results) == 1
        assert results[0].passed is False
        assert "Exception" in results[0].details
        assert "Mock error" in results[0].details

    @pytest.mark.requirement("WL-178")
    def test_run_all_preserves_order(self) -> None:
        """Test that run_all preserves test order."""
        suite = GitHubSyncIntegrationSuite()
        for i in range(5):
            suite.add_test(f"test_{i}", lambda: True)

        results = suite.run_all()
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.test_name == f"test_{i}"

    @pytest.mark.requirement("WL-178")
    def test_summary_all_passed(self) -> None:
        """Test summary with all passing tests."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: True)
        suite.add_test("test_3", lambda: True)

        results = suite.run_all()
        summary = GitHubSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 3
        assert summary["failed"] == 0

    @pytest.mark.requirement("WL-178")
    def test_summary_all_failed(self) -> None:
        """Test summary with all failing tests."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", lambda: False)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: False)

        results = suite.run_all()
        summary = GitHubSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 0
        assert summary["failed"] == 3

    @pytest.mark.requirement("WL-178")
    def test_summary_mixed(self) -> None:
        """Test summary with mixed results."""
        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", lambda: True)
        suite.add_test("test_2", lambda: False)
        suite.add_test("test_3", lambda: True)
        suite.add_test("test_4", lambda: False)
        suite.add_test("test_5", lambda: True)

        results = suite.run_all()
        summary = GitHubSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 3
        assert summary["failed"] == 2

    @pytest.mark.requirement("WL-178")
    def test_summary_empty(self) -> None:
        """Test summary with no tests."""
        suite = GitHubSyncIntegrationSuite()
        results = suite.run_all()
        summary = GitHubSyncIntegrationSuite.summary(results)
        assert summary["passed"] == 0
        assert summary["failed"] == 0

    @pytest.mark.requirement("WL-178")
    def test_run_all_empty(self) -> None:
        """Test run_all with no tests registered."""
        suite = GitHubSyncIntegrationSuite()
        results = suite.run_all()
        assert len(results) == 0
        assert results == []

    @pytest.mark.requirement("WL-178")
    def test_stateful_test_function(self) -> None:
        """Test that test functions can be stateful."""
        state = {"count": 0}

        def stateful_test() -> bool:
            state["count"] += 1
            return state["count"] <= 2

        suite = GitHubSyncIntegrationSuite()
        suite.add_test("test_1", stateful_test)
        suite.add_test("test_2", stateful_test)
        suite.add_test("test_3", stateful_test)

        results = suite.run_all()
        assert results[0].passed is True
        assert results[1].passed is True
        assert results[2].passed is False
