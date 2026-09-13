"""Tests for WL-301: Cross-Connector Consistency Verifier.

# @trace WL-301
"""

from __future__ import annotations

import pytest

from thegent.integrations.cross_connector_verifier import (
    ConsistencyViolation,
    CrossConnectorVerifier,
    SplitBrainFinding,
)


class TestConsistencyViolation:
    """WL-301: ConsistencyViolation dataclass."""

    @pytest.mark.requirement("WL-301")
    def test_violation_creation(self):
        """# @trace WL-301 — ConsistencyViolation can be created."""
        violation = ConsistencyViolation(
            wl_id="WL-123",
            connector_a="github",
            connector_b="linear",
            field="status",
            value_a="open",
            value_b="closed",
        )

        assert violation.wl_id == "WL-123"
        assert violation.connector_a == "github"
        assert violation.connector_b == "linear"
        assert violation.field == "status"
        assert violation.value_a == "open"
        assert violation.value_b == "closed"


class TestCrossConnectorVerifier:
    """WL-301: CrossConnectorVerifier class."""

    @pytest.mark.requirement("WL-301")
    def test_verifier_initialization(self):
        """# @trace WL-301 — CrossConnectorVerifier initializes."""
        verifier = CrossConnectorVerifier()

        assert verifier is not None
        assert {"status", "priority"} == CrossConnectorVerifier.CRITICAL_FIELDS

    @pytest.mark.requirement("WL-301")
    def test_compare_identical_states(self):
        """# @trace WL-301 — compare returns empty list for identical states."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-100",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-100",
            "connector_name": "linear",
            "status": "open",
            "priority": "P1",
        }

        violations = verifier.compare(state_a, state_b)

        assert violations == []

    @pytest.mark.requirement("WL-301")
    def test_compare_status_mismatch(self):
        """# @trace WL-301 — compare detects status mismatches."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-101",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-101",
            "connector_name": "linear",
            "status": "closed",
            "priority": "P1",
        }

        violations = verifier.compare(state_a, state_b)

        assert len(violations) == 1
        assert violations[0].field == "status"
        assert violations[0].value_a == "open"
        assert violations[0].value_b == "closed"

    @pytest.mark.requirement("WL-301")
    def test_compare_priority_mismatch(self):
        """# @trace WL-301 — compare detects priority mismatches."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-102",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-102",
            "connector_name": "linear",
            "status": "open",
            "priority": "P2",
        }

        violations = verifier.compare(state_a, state_b)

        assert len(violations) == 1
        assert violations[0].field == "priority"
        assert violations[0].value_a == "P1"
        assert violations[0].value_b == "P2"

    @pytest.mark.requirement("WL-301")
    def test_compare_multiple_mismatches(self):
        """# @trace WL-301 — compare detects multiple mismatches."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-103",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-103",
            "connector_name": "linear",
            "status": "closed",
            "priority": "P3",
        }

        violations = verifier.compare(state_a, state_b)

        assert len(violations) == 2
        fields = {v.field for v in violations}
        assert fields == {"status", "priority"}

    @pytest.mark.requirement("WL-301")
    def test_compare_missing_required_keys_state_a(self):
        """# @trace WL-301 — compare raises ValueError for missing keys in state_a."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-104",
            # Missing connector_name
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-104",
            "connector_name": "linear",
            "status": "open",
            "priority": "P1",
        }

        with pytest.raises(ValueError, match="connector_a_state missing required keys"):
            verifier.compare(state_a, state_b)

    @pytest.mark.requirement("WL-301")
    def test_compare_missing_required_keys_state_b(self):
        """# @trace WL-301 — compare raises ValueError for missing keys in state_b."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-105",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
        }
        state_b = {
            "wl_id": "WL-105",
            # Missing connector_name
            "status": "open",
            "priority": "P1",
        }

        with pytest.raises(ValueError, match="connector_b_state missing required keys"):
            verifier.compare(state_a, state_b)

    @pytest.mark.requirement("WL-301")
    def test_compare_with_extra_fields(self):
        """# @trace WL-301 — compare ignores extra non-critical fields."""
        verifier = CrossConnectorVerifier()

        state_a = {
            "wl_id": "WL-106",
            "connector_name": "github",
            "status": "open",
            "priority": "P1",
            "extra_field": "value1",
            "another_field": 123,
        }
        state_b = {
            "wl_id": "WL-106",
            "connector_name": "linear",
            "status": "open",
            "priority": "P1",
            "extra_field": "value2",
            "another_field": 456,
        }

        # Should return empty list, ignoring extra_field and another_field differences
        violations = verifier.compare(state_a, state_b)

        assert violations == []

    @pytest.mark.requirement("WL-271")
    def test_detect_split_brain_finds_divergent_fingerprints(self):
        """# @trace WL-271 — split-brain detector reports divergent connector states."""
        verifier = CrossConnectorVerifier()
        states = [
            {
                "wl_id": "WL-500",
                "connector_name": "github",
                "status": "BACKLOG",
                "priority": "P1",
            },
            {
                "wl_id": "WL-500",
                "connector_name": "linear",
                "status": "COMPLETED",
                "priority": "P1",
            },
        ]
        findings = verifier.detect_split_brain(states)
        assert len(findings) == 1
        assert isinstance(findings[0], SplitBrainFinding)
        assert findings[0].wl_id == "WL-500"
        assert findings[0].connectors == ["github", "linear"]

    @pytest.mark.requirement("WL-271")
    def test_detect_split_brain_ignores_equal_fingerprints(self):
        """# @trace WL-271 — split-brain detector ignores equivalent states."""
        verifier = CrossConnectorVerifier()
        states = [
            {
                "wl_id": "WL-501",
                "connector_name": "github",
                "status": "BACKLOG",
                "priority": "P1",
            },
            {
                "wl_id": "WL-501",
                "connector_name": "linear",
                "status": "BACKLOG",
                "priority": "P1",
            },
        ]
        findings = verifier.detect_split_brain(states)
        assert findings == []
