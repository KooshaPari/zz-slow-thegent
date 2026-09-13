"""Unit tests for conformance test suite (contracts/conformance.py)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from thegent.contracts.conformance import (
    ConformanceTest,
    _build_conformance_tests,
    run_conformance_suite,
)
from thegent.contracts.csm import CSMStatus


@pytest.mark.unit
class TestConformanceTest:
    """Tests for ConformanceTest dataclass."""

    def test_create_with_defaults(self) -> None:
        # @trace FR-CON-060
        ct = ConformanceTest(
            name="Basic Test",
            provider="gemini",
            raw_output="some output",
            expected_status=CSMStatus.COMPLETED,
        )
        assert ct.name == "Basic Test"
        assert ct.provider == "gemini"
        assert ct.min_confidence == 0.5
        assert ct.check_summary is True

    def test_create_with_custom_values(self) -> None:
        # @trace FR-CON-060
        ct = ConformanceTest(
            name="Custom Test",
            provider="claude",
            raw_output={"status": "done"},
            expected_status=CSMStatus.IN_PROGRESS,
            min_confidence=0.9,
            check_summary=False,
        )
        assert ct.min_confidence == 0.9
        assert ct.check_summary is False
        assert ct.expected_status == CSMStatus.IN_PROGRESS


@pytest.mark.unit
class TestBuildConformanceTests:
    """Tests for _build_conformance_tests."""

    def test_returns_non_empty_list(self) -> None:
        # @trace FR-CON-061
        tests = _build_conformance_tests()
        assert len(tests) > 0

    def test_all_entries_are_conformance_tests(self) -> None:
        # @trace FR-CON-061
        tests = _build_conformance_tests()
        for t in tests:
            assert isinstance(t, ConformanceTest)

    def test_covers_multiple_providers(self) -> None:
        # @trace FR-CON-062
        tests = _build_conformance_tests()
        providers = {t.provider for t in tests}
        assert len(providers) >= 3

    def test_includes_xml_and_plaintext_tests(self) -> None:
        # @trace FR-CON-062
        tests = _build_conformance_tests()
        names = [t.name for t in tests]
        has_xml = any("XML" in n for n in names)
        has_plain = any("Plain" in n or "Generic" in n for n in names)
        assert has_xml, "Suite should include XML-based tests"
        assert has_plain, "Suite should include plain text or generic tests"

    def test_includes_malformed_test(self) -> None:
        # @trace FR-CON-063
        tests = _build_conformance_tests()
        malformed = [t for t in tests if "Malformed" in t.name or "truncated" in t.name]
        assert len(malformed) >= 1, "Suite should include a malformed input test"


@pytest.mark.unit
class TestRunConformanceSuite:
    """Tests for run_conformance_suite."""

    def _mock_adapter_result(self, status: CSMStatus, confidence: float, summary: str = "Done") -> MagicMock:
        """Build a mock AdapterResult."""
        csm = MagicMock()
        csm.status = status
        csm.summary = summary
        result = MagicMock()
        result.csm = csm
        result.confidence = confidence
        return result

    @patch("thegent.contracts.conformance.normalize_output")
    def test_all_pass(self, mock_normalize: MagicMock) -> None:
        # @trace FR-CON-064
        # Return COMPLETED with high confidence and non-empty summary for all tests
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Summary text")
        # Override behavior: for IN_PROGRESS expected tests, return IN_PROGRESS
        tests = _build_conformance_tests()

        def side_effect(provider: str, raw: Any) -> MagicMock:
            for t in tests:
                if t.provider == provider and t.raw_output == raw:
                    return self._mock_adapter_result(
                        t.expected_status,
                        max(t.min_confidence, 0.5),
                        "Summary" if t.check_summary else "",
                    )
            return self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Summary")

        mock_normalize.side_effect = side_effect

        report = run_conformance_suite()
        assert report["total"] == len(tests)
        assert report["passed"] == report["total"]
        assert report["failed"] == 0

    @patch("thegent.contracts.conformance.normalize_output")
    def test_status_mismatch_counted_as_failure(self, mock_normalize: MagicMock) -> None:
        # @trace FR-CON-065
        # Return FAILED for everything, so status mismatch for COMPLETED-expected tests
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.FAILED, 1.0, "Summary")
        report = run_conformance_suite()
        assert report["failed"] > 0
        # Check issues contain "Status mismatch"
        failed_results = [r for r in report["results"] if not r["success"]]
        assert any("Status mismatch" in issue for r in failed_results for issue in r["issues"])

    @patch("thegent.contracts.conformance.normalize_output")
    def test_low_confidence_counted_as_failure(self, mock_normalize: MagicMock) -> None:
        # @trace FR-CON-066
        # Return correct status but very low confidence
        tests = _build_conformance_tests()

        def side_effect(provider: str, raw: Any) -> MagicMock:
            for t in tests:
                if t.provider == provider and t.raw_output == raw:
                    return self._mock_adapter_result(
                        t.expected_status,
                        0.0,  # zero confidence -- below all min_confidence thresholds > 0
                        "Summary" if t.check_summary else "",
                    )
            return self._mock_adapter_result(CSMStatus.COMPLETED, 0.0, "Summary")

        mock_normalize.side_effect = side_effect
        report = run_conformance_suite()
        # Tests with min_confidence > 0 should fail
        high_conf_tests = [t for t in tests if t.min_confidence > 0.0]
        assert report["failed"] >= len(high_conf_tests)

    @patch("thegent.contracts.conformance.normalize_output")
    def test_report_structure(self, mock_normalize: MagicMock) -> None:
        # @trace FR-CON-067
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Ok")
        report = run_conformance_suite()
        assert "total" in report
        assert "passed" in report
        assert "failed" in report
        assert "results" in report
        assert "drift_issues" in report
        assert "drift_checked" in report
        assert report["drift_checked"] is False

    @patch("thegent.contracts.conformance.normalize_output")
    def test_without_session_dir_no_drift(self, mock_normalize: MagicMock) -> None:
        # @trace FR-CON-068
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Ok")
        report = run_conformance_suite(session_dir=None)
        assert report["drift_checked"] is False
        assert report["drift_issues"] == []

    @patch("thegent.contracts.telemetry.ContractTelemetry")
    @patch("thegent.contracts.conformance.normalize_output")
    def test_with_session_dir_runs_drift_detection(
        self, mock_normalize: MagicMock, mock_telemetry_cls: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-CON-069
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Ok")
        mock_ct_instance = MagicMock()
        mock_ct_instance.detect_drift.return_value = []
        mock_ct_instance.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "structural_budget_pct": 5.0,
            "semantic_rate_pct": 2.0,
            "semantic_budget_pct": 10.0,
        }
        mock_telemetry_cls.return_value = mock_ct_instance

        report = run_conformance_suite(session_dir=tmp_path, drift_window=25)
        assert report["drift_checked"] is True
        assert report["drift_issues"] == []
        mock_ct_instance.detect_drift.assert_called_once_with(window_size=25)

    @patch("thegent.contracts.telemetry.ContractTelemetry")
    @patch("thegent.contracts.conformance.normalize_output")
    def test_drift_budget_exceeded_appended_to_issues(
        self, mock_normalize: MagicMock, mock_telemetry_cls: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-CON-070
        mock_normalize.return_value = self._mock_adapter_result(CSMStatus.COMPLETED, 1.0, "Ok")
        mock_ct_instance = MagicMock()
        mock_ct_instance.detect_drift.return_value = ["drift issue 1"]
        mock_ct_instance.get_drift_budget_status.return_value = {
            "within_budget": False,
            "structural_rate_pct": 8.0,
            "structural_budget_pct": 5.0,
            "semantic_rate_pct": 15.0,
            "semantic_budget_pct": 10.0,
        }
        mock_telemetry_cls.return_value = mock_ct_instance

        report = run_conformance_suite(session_dir=tmp_path)
        assert report["drift_checked"] is True
        assert len(report["drift_issues"]) >= 2  # original issue + budget exceeded
        assert any("Drift budget exceeded" in i for i in report["drift_issues"])
