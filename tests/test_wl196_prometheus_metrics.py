"""Tests for WL-196: Prometheus Metrics Export.

Verifies metrics collection, export formatting, and retrieval.

# @trace WL-196
"""

from __future__ import annotations

import pytest

from thegent.integrations.prometheus_metrics import (
    MetricSample,
    PrometheusMetricsExporter,
)


@pytest.mark.requirement("WL-196")
class TestMetricSample:
    """WL-196: MetricSample dataclass."""

    def test_metric_sample_creation(self):
        """Create a metric sample."""
        sample = MetricSample(
            name="requests_total", value=42.0, labels={"method": "GET"}
        )

        assert sample.name == "requests_total"
        assert sample.value == 42.0
        assert sample.labels == {"method": "GET"}

    def test_metric_sample_empty_labels(self):
        """Create a metric sample with empty labels."""
        sample = MetricSample(name="uptime", value=100.5, labels={})

        assert sample.name == "uptime"
        assert sample.value == 100.5
        assert sample.labels == {}


@pytest.mark.requirement("WL-196")
class TestPrometheusMetricsExporterRecord:
    """WL-196: Recording metrics."""

    def test_record_simple_metric(self):
        """Record a metric without labels."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 10.0)

        samples = exporter.get_samples("requests")
        assert len(samples) == 1
        assert samples[0].value == 10.0
        assert samples[0].labels == {}

    def test_record_metric_with_labels(self):
        """Record a metric with labels."""
        exporter = PrometheusMetricsExporter()

        exporter.record(
            "response_time", 150.5, labels={"endpoint": "/api/v1", "status": "200"}
        )

        samples = exporter.get_samples("response_time")
        assert len(samples) == 1
        assert samples[0].value == 150.5
        assert samples[0].labels == {"endpoint": "/api/v1", "status": "200"}

    def test_record_multiple_metrics(self):
        """Record multiple metrics."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)
        exporter.record("errors", 5.0)
        exporter.record("requests", 50.0)

        assert len(exporter.get_samples("requests")) == 2
        assert len(exporter.get_samples("errors")) == 1

    def test_record_empty_name_raises(self):
        """Reject empty metric name."""
        exporter = PrometheusMetricsExporter()

        with pytest.raises(ValueError, match="metric name cannot be empty"):
            exporter.record("", 42.0)

    def test_record_none_labels_defaults_to_empty(self):
        """None labels defaults to empty dict."""
        exporter = PrometheusMetricsExporter()

        exporter.record("metric", 1.0, labels=None)

        samples = exporter.get_samples("metric")
        assert samples[0].labels == {}

    def test_record_copies_labels_to_prevent_external_mutation(self):
        """Recorded labels are isolated from caller-side dict mutation."""
        exporter = PrometheusMetricsExporter()
        labels = {"region": "us-east-1"}

        exporter.record("requests", 1.0, labels=labels)
        labels["region"] = "mutated"

        samples = exporter.get_samples("requests")
        assert samples[0].labels == {"region": "us-east-1"}


@pytest.mark.requirement("WL-196")
class TestPrometheusMetricsExporterExport:
    """WL-196: Exporting metrics in Prometheus format."""

    def test_export_empty(self):
        """Export with no recorded metrics."""
        exporter = PrometheusMetricsExporter()

        result = exporter.export()

        assert result == ""

    def test_export_single_metric_no_labels(self):
        """Export single metric without labels."""
        exporter = PrometheusMetricsExporter()

        exporter.record("uptime", 3600.0)

        result = exporter.export()

        assert result == "uptime 3600.0"

    def test_export_single_metric_with_labels(self):
        """Export single metric with labels."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0, labels={"method": "GET"})

        result = exporter.export()

        assert result == 'requests{method="GET"} 100.0'

    def test_export_single_metric_multiple_labels(self):
        """Export single metric with multiple labels."""
        exporter = PrometheusMetricsExporter()

        exporter.record("response", 200.5, labels={"endpoint": "/api", "status": "200"})

        result = exporter.export()

        # Labels should be sorted
        assert result == 'response{endpoint="/api",status="200"} 200.5'

    def test_export_multiple_metrics(self):
        """Export multiple metrics."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)
        exporter.record("errors", 5.0)

        result = exporter.export()
        lines = result.split("\n")

        assert len(lines) == 2
        assert "requests 100.0" in result
        assert "errors 5.0" in result

    def test_export_format_compliance(self):
        """Verify export format matches Prometheus text format."""
        exporter = PrometheusMetricsExporter()

        exporter.record(
            "http_requests_total", 1027.0, labels={"method": "POST", "code": "200"}
        )
        exporter.record(
            "http_requests_total", 3.0, labels={"method": "POST", "code": "400"}
        )

        result = exporter.export()

        lines = result.split("\n")
        assert len(lines) == 2

        # Verify both lines contain proper format
        for line in lines:
            assert "http_requests_total" in line
            assert "{" in line
            assert "}" in line
            assert " " in line  # Space before value


@pytest.mark.requirement("WL-196")
class TestPrometheusMetricsExporterGetSamples:
    """WL-196: Retrieving samples by metric name."""

    def test_get_samples_matching_name(self):
        """Get samples by metric name."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)
        exporter.record("errors", 5.0)
        exporter.record("requests", 50.0)

        samples = exporter.get_samples("requests")

        assert len(samples) == 2
        assert samples[0].value == 100.0
        assert samples[1].value == 50.0

    def test_get_samples_no_match(self):
        """Get samples for non-existent metric."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)

        samples = exporter.get_samples("nonexistent")

        assert len(samples) == 0

    def test_get_samples_returns_copy(self):
        """Get samples returns correct data (order preserved)."""
        exporter = PrometheusMetricsExporter()

        exporter.record("metric", 1.0)
        exporter.record("metric", 2.0)
        exporter.record("metric", 3.0)

        samples = exporter.get_samples("metric")

        assert len(samples) == 3
        assert [s.value for s in samples] == [1.0, 2.0, 3.0]


@pytest.mark.requirement("WL-196")
class TestPrometheusMetricsExporterClear:
    """WL-196: Clearing metrics."""

    def test_clear_removes_all_metrics(self):
        """Clear removes all recorded metrics."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)
        exporter.record("errors", 5.0)

        exporter.clear()

        assert exporter.export() == ""
        assert exporter.get_samples("requests") == []
        assert exporter.get_samples("errors") == []

    def test_clear_allows_rerecording(self):
        """Can record metrics again after clear."""
        exporter = PrometheusMetricsExporter()

        exporter.record("requests", 100.0)
        exporter.clear()
        exporter.record("requests", 50.0)

        samples = exporter.get_samples("requests")
        assert len(samples) == 1
        assert samples[0].value == 50.0
