"""Unit tests for thegent.contracts.telemetry -- ContractTelemetry, drift detection."""

import orjson as json
import pytest

from thegent.contracts.telemetry import (
    EVENT_NORMALIZATION,
    EVENT_SCHEMA_DRIFT_SEMANTIC,
    EVENT_SCHEMA_DRIFT_STRUCTURAL,
    ContractTelemetry,
    detect_drift,
    rank_providers_by_parser_quality,
)


@pytest.mark.unit
class TestContractTelemetryRecording:
    """Tests for recording normalization events."""

    def test_record_creates_file(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        assert tel.telemetry_path.exists()

    def test_record_appends_jsonl(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "gemini", "xml-tags", 0.8, True)
        lines = tel.telemetry_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_record_event_fields(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization(
            "r1", "copilot", "xml-tags", 0.9, True, errors=["warn"]
        )
        event = json.loads(tel.telemetry_path.read_text().strip())
        assert event["run_id"] == "r1"
        assert event["provider"] == "copilot"
        assert event["contract"] == "xml-tags"
        assert event["confidence"] == 0.9
        assert event["success"] is True
        assert event["errors"] == ["warn"]
        assert event["event_type"] == EVENT_NORMALIZATION

    def test_record_creates_parent_dirs(self, tmp_path) -> None:
        # @trace FR-CTR-006
        deep = tmp_path / "a" / "b" / "c"
        tel = ContractTelemetry(deep)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        assert tel.telemetry_path.exists()

    def test_record_default_errors_empty(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        event = json.loads(tel.telemetry_path.read_text().strip())
        assert event["errors"] == []


@pytest.mark.unit
class TestContractTelemetryDriftEvents:
    """Tests for emit_drift_event and drift budget."""

    def test_emit_structural_drift(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.emit_drift_event(
            "r1", "copilot", "xml-tags", "structural", {"field": "status"}
        )
        event = json.loads(tel.telemetry_path.read_text().strip())
        assert event["event_type"] == EVENT_SCHEMA_DRIFT_STRUCTURAL
        assert event["drift_type"] == "structural"

    def test_emit_semantic_drift(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        tel.emit_drift_event("r1", "copilot", "xml-tags", "semantic")
        event = json.loads(tel.telemetry_path.read_text().strip())
        assert event["event_type"] == EVENT_SCHEMA_DRIFT_SEMANTIC

    def test_drift_budget_empty_file(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        budget = tel.get_drift_budget_status()
        assert budget["within_budget"] is True
        assert budget["structural_rate_pct"] == 0.0
        assert budget["semantic_rate_pct"] == 0.0

    def test_drift_budget_within(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        for i in range(100):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        tel.emit_drift_event("rd1", "copilot", "xml-tags", "structural")
        budget = tel.get_drift_budget_status()
        assert budget["within_budget"] is True
        assert budget["structural_rate_pct"] < 5.0

    def test_drift_budget_exceeded(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        for i in range(10):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        for i in range(10):
            tel.emit_drift_event(f"rd{i}", "copilot", "xml-tags", "structural")
        budget = tel.get_drift_budget_status()
        assert budget["within_budget"] is False
        assert budget["structural_rate_pct"] == 50.0


@pytest.mark.unit
class TestContractTelemetryStats:
    """Tests for get_stats()."""

    def test_stats_empty(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        stats = tel.get_stats()
        assert stats["total"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_all_success(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        for i in range(5):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        stats = tel.get_stats()
        assert stats["total"] == 5
        assert stats["success_rate"] == 1.0
        assert stats["fallback_rate"] == 0.0

    def test_stats_with_fallbacks(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "copilot", "fallback-plain", 0.3, True)
        stats = tel.get_stats()
        assert stats["fallback_rate"] == 0.5

    def test_stats_provider_filter(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "gemini", "xml-tags", 0.8, True)
        stats = tel.get_stats(provider="copilot")
        assert stats["total"] == 1

    def test_stats_avg_confidence(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "copilot", "xml-tags", 0.6, True)
        stats = tel.get_stats()
        assert stats["avg_confidence"] == pytest.approx(0.8)

    def test_stats_by_provider(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "gemini", "xml-tags", 0.6, True)
        stats = tel.get_stats()
        assert "copilot" in stats["by_provider"]
        assert "gemini" in stats["by_provider"]


@pytest.mark.unit
class TestFallbackKPIs:
    """Tests for get_fallback_kpis()."""

    def test_kpis_empty(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        kpis = tel.get_fallback_kpis()
        assert kpis["total"] == 0
        assert kpis["fallback_rate"] == 0.0

    def test_kpis_with_data(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "copilot", "fallback-plain", 0.3, True)
        kpis = tel.get_fallback_kpis()
        assert kpis["total"] == 2
        assert kpis["fallback_rate"] == 0.5
        assert "copilot" in kpis["by_provider"]

    def test_kpis_provider_filter(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "gemini", "xml-tags", 0.8, True)
        kpis = tel.get_fallback_kpis(provider="copilot")
        assert kpis["total"] == 1


@pytest.mark.unit
class TestDetectDrift:
    """Tests for drift detection."""

    def test_legacy_detect_drift_high_rate(self) -> None:
        # @trace FR-CTR-006
        stats = {"fallback_rate": 0.5}
        issues = detect_drift(stats, threshold=0.2)
        assert len(issues) == 1
        assert "fallback rate" in issues[0].lower()

    def test_legacy_detect_drift_ok(self) -> None:
        # @trace FR-CTR-006
        stats = {"fallback_rate": 0.1}
        issues = detect_drift(stats, threshold=0.2)
        assert issues == []

    def test_instance_detect_drift_insufficient_data(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        for i in range(10):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        issues = tel.detect_drift(window_size=50)
        assert issues == []

    def test_instance_detect_drift_no_file(self, tmp_path) -> None:
        # @trace FR-CTR-006
        tel = ContractTelemetry(tmp_path)
        assert tel.detect_drift() == []


@pytest.mark.unit
class TestRankProviders:
    """Tests for rank_providers_by_parser_quality."""

    def test_rank_empty_providers(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        assert rank_providers_by_parser_quality([], tel) == []

    def test_rank_no_telemetry_data(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        result = rank_providers_by_parser_quality(["copilot", "gemini"], tel)
        assert set(result) == {"copilot", "gemini"}


@pytest.mark.unit
class TestDetectDriftTimeSeries:
    """Tests for ContractTelemetry.detect_drift with time-series data."""

    def test_detect_drift_fallback_rate_increase(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """Detects significant increase in fallback rate between historical and recent."""
        tel = ContractTelemetry(tmp_path)
        # Historical: 100 events, 0% fallback
        for i in range(100):
            tel.record_normalization(f"h{i}", "copilot", "xml-tags", 1.0, True)
        # Recent: 50 events, 40% fallback (much higher than historical 0%)
        for i in range(30):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        for i in range(20):
            tel.record_normalization(f"rf{i}", "copilot", "fallback-plain", 0.3, True)
        issues = tel.detect_drift(window_size=50)
        assert len(issues) >= 1
        assert any("fallback" in i.lower() for i in issues)

    def test_detect_drift_confidence_drop(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """Detects significant drop in normalization confidence."""
        tel = ContractTelemetry(tmp_path)
        # Historical: 100 events, high confidence
        for i in range(100):
            tel.record_normalization(f"h{i}", "copilot", "xml-tags", 0.95, True)
        # Recent: 50 events, low confidence
        for i in range(50):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 0.3, True)
        issues = tel.detect_drift(window_size=50)
        assert len(issues) >= 1
        assert any("confidence" in i.lower() for i in issues)

    def test_detect_drift_no_drift_stable_data(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """Returns empty list when data is stable (no drift)."""
        tel = ContractTelemetry(tmp_path)
        for i in range(200):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 0.9, True)
        issues = tel.detect_drift(window_size=50)
        assert issues == []


@pytest.mark.unit
class TestDetectDriftProviderSpecific:
    """Tests for provider-specific drift detection."""

    def test_provider_specific_fallback_regression(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """Detects provider-specific fallback rate regression."""
        tel = ContractTelemetry(tmp_path)
        # Historical: copilot with 0% fallback, gemini with 0% fallback
        for i in range(50):
            tel.record_normalization(f"hc{i}", "copilot", "xml-tags", 0.9, True)
        for i in range(50):
            tel.record_normalization(f"hg{i}", "gemini", "xml-tags", 0.9, True)
        # Recent: copilot regresses to high fallback, gemini stays stable
        for i in range(25):
            tel.record_normalization(f"rc{i}", "copilot", "fallback-plain", 0.3, True)
        for i in range(25):
            tel.record_normalization(f"rg{i}", "gemini", "xml-tags", 0.9, True)
        issues = tel.detect_drift(window_size=50)
        provider_issues = [i for i in issues if "copilot" in i.lower()]
        assert len(provider_issues) >= 1

    def test_provider_specific_confidence_regression(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """Detects provider-specific confidence score regression."""
        tel = ContractTelemetry(tmp_path)
        # Historical: gemini with high confidence
        for i in range(60):
            tel.record_normalization(f"hg{i}", "gemini", "xml-tags", 0.95, True)
        # Padding to meet minimum data requirements
        for i in range(60):
            tel.record_normalization(f"hp{i}", "copilot", "xml-tags", 0.9, True)
        # Recent: gemini drops in confidence
        for i in range(25):
            tel.record_normalization(f"rg{i}", "gemini", "xml-tags", 0.2, True)
        for i in range(25):
            tel.record_normalization(f"rp{i}", "copilot", "xml-tags", 0.9, True)
        issues = tel.detect_drift(window_size=50)
        gemini_issues = [i for i in issues if "gemini" in i.lower()]
        assert len(gemini_issues) >= 1


@pytest.mark.unit
class TestRankProvidersByQuality:
    """Extended tests for rank_providers_by_parser_quality scoring."""

    def test_rank_higher_confidence_first(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """Provider with higher confidence ranked first."""
        tel = ContractTelemetry(tmp_path)
        for i in range(10):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 0.5, True)
        for i in range(10):
            tel.record_normalization(f"s{i}", "gemini", "xml-tags", 0.9, True)
        result = rank_providers_by_parser_quality(["copilot", "gemini"], tel)
        assert result[0] == "gemini"

    def test_rank_lower_fallback_preferred(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """Provider with lower fallback rate ranked higher."""
        tel = ContractTelemetry(tmp_path)
        for i in range(10):
            tel.record_normalization(f"c{i}", "copilot", "fallback-plain", 0.8, True)
        for i in range(10):
            tel.record_normalization(f"g{i}", "gemini", "xml-tags", 0.8, True)
        result = rank_providers_by_parser_quality(["copilot", "gemini"], tel)
        assert result[0] == "gemini"

    def test_rank_single_provider(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """Single provider returns that provider."""
        tel = ContractTelemetry(tmp_path)
        result = rank_providers_by_parser_quality(["copilot"], tel)
        assert result == ["copilot"]


@pytest.mark.unit
class TestContractTelemetryEdgeCases:
    """Edge case tests for ContractTelemetry."""

    def test_get_stats_empty_events_after_provider_filter(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """get_stats returns zero totals when provider filter matches nothing."""
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        stats = tel.get_stats(provider="nonexistent")
        assert stats["total"] == 0

    def test_get_fallback_kpis_provider_filter_case_insensitive(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """get_fallback_kpis provider filter is case-insensitive."""
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "Copilot", "xml-tags", 1.0, True)
        kpis = tel.get_fallback_kpis(provider="copilot")
        assert kpis["total"] == 1


@pytest.mark.unit
class TestTelemetryCorruptedLines:
    """Tests for corrupted/blank JSONL lines in telemetry methods (lines 98, 101-102, 138-139, 197-198, 259-260)."""

    def test_drift_budget_blank_and_corrupted_lines(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """get_drift_budget_status skips blank and malformed JSON lines (lines 98, 101-102)."""
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        # Manually inject blank and corrupted lines
        with tel.telemetry_path.open("a", encoding="utf-8") as f:
            f.write("\n")
            f.write("this is not json\n")
            f.write("{broken\n")
        budget = tel.get_drift_budget_status()
        assert budget["within_budget"] is True

    def test_get_stats_corrupted_lines(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """get_stats skips corrupted JSON lines (lines 138-139)."""
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        with tel.telemetry_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")
            f.write("{broken json too\n")
        stats = tel.get_stats()
        assert stats["total"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["parse_errors"] == 2

    def test_get_fallback_kpis_corrupted_lines(self, tmp_path) -> None:
        # @trace FR-CTR-007
        """get_fallback_kpis skips corrupted JSON lines (lines 197-198)."""
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        with tel.telemetry_path.open("a", encoding="utf-8") as f:
            f.write("corrupted line\n")
            f.write("{broken\n")
        kpis = tel.get_fallback_kpis()
        assert kpis["total"] == 1
        assert tel.malformed_line_count >= 2

    def test_get_stats_tracks_parse_errors_and_provider_skips(self, tmp_path) -> None:
        # @trace FR-CTR-007
        tel = ContractTelemetry(tmp_path)
        tel.record_normalization("r1", "copilot", "xml-tags", 1.0, True)
        tel.record_normalization("r2", "gemini", "xml-tags", 0.7, True)
        with tel.telemetry_path.open("a", encoding="utf-8") as f:
            f.write("not-json\n")
            f.write('{"provider":')
        stats = tel.get_stats(provider="copilot")
        assert stats["total"] == 1
        assert stats["provider_skips"] == 1
        assert stats["parse_errors"] == 2

    def test_detect_drift_corrupted_lines(self, tmp_path) -> None:
        # @trace FR-CTR-006
        """detect_drift skips corrupted JSON lines (lines 259-260)."""
        tel = ContractTelemetry(tmp_path)
        # Need enough data for drift detection (window_size * 2)
        for i in range(100):
            tel.record_normalization(f"h{i}", "copilot", "xml-tags", 1.0, True)
        for i in range(50):
            tel.record_normalization(f"r{i}", "copilot", "xml-tags", 1.0, True)
        # Inject corrupted lines
        with tel.telemetry_path.open("a", encoding="utf-8") as f:
            f.write("broken json here\n")
            f.write("{invalid\n")
        issues = tel.detect_drift(window_size=50)
        assert isinstance(issues, list)
