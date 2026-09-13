"""Tests for thegent.integrations.policy_checksum — Policy checksum drift detection.

@trace WL-312
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.policy_checksum import (
    PolicyChecksum,
    PolicyChecksumDriftDetector,
)


class TestPolicyChecksum:
    """Test PolicyChecksum dataclass. @trace WL-312"""

    @pytest.mark.requirement("WL-312")
    @pytest.mark.requirement("WL-226")
    def test_create_policy_checksum(self) -> None:
        """Can create a PolicyChecksum with all fields."""
        now = datetime.now(UTC)
        checksum = PolicyChecksum(
            policy_id="policy-auth-001",
            checksum="abc123def456",
            cycle_id="cycle-42",
            timestamp=now,
        )

        assert checksum.policy_id == "policy-auth-001"
        assert checksum.checksum == "abc123def456"
        assert checksum.cycle_id == "cycle-42"
        assert checksum.timestamp == now


class TestPolicyChecksumDriftDetector:
    """Test PolicyChecksumDriftDetector operations. @trace WL-312"""

    @pytest.fixture
    def detector(self) -> PolicyChecksumDriftDetector:
        """Provide a PolicyChecksumDriftDetector instance."""
        return PolicyChecksumDriftDetector()

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_simple(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can compute checksum of simple dict."""
        data = {"role": "admin", "permission": "read"}
        checksum = detector.compute_checksum(data)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex is 64 chars

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_deterministic(self, detector: PolicyChecksumDriftDetector) -> None:
        """Checksum computation is deterministic."""
        data = {"role": "admin", "permission": "read"}

        checksum1 = detector.compute_checksum(data)
        checksum2 = detector.compute_checksum(data)

        assert checksum1 == checksum2

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_order_independent(self, detector: PolicyChecksumDriftDetector) -> None:
        """Checksum is independent of dict key order."""
        data1 = {"role": "admin", "permission": "read"}
        data2 = {"permission": "read", "role": "admin"}

        checksum1 = detector.compute_checksum(data1)
        checksum2 = detector.compute_checksum(data2)

        assert checksum1 == checksum2

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_value_changes(self, detector: PolicyChecksumDriftDetector) -> None:
        """Different data produces different checksum."""
        data1 = {"role": "admin"}
        data2 = {"role": "user"}

        checksum1 = detector.compute_checksum(data1)
        checksum2 = detector.compute_checksum(data2)

        assert checksum1 != checksum2

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_empty_dict(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can compute checksum of empty dict."""
        checksum = detector.compute_checksum({})
        assert isinstance(checksum, str)
        assert len(checksum) == 64

    @pytest.mark.requirement("WL-312")
    def test_compute_checksum_nested_dict(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can compute checksum of nested dict."""
        data = {"policy": {"role": "admin", "permissions": ["read", "write"]}}
        checksum = detector.compute_checksum(data)
        assert isinstance(checksum, str)
        assert len(checksum) == 64

    @pytest.mark.requirement("WL-312")
    def test_record_baseline(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can record a baseline for a policy."""
        data = {"role": "admin", "permission": "read"}
        baseline = detector.record_baseline("policy-001", data, "cycle-1")

        assert baseline.policy_id == "policy-001"
        assert baseline.cycle_id == "cycle-1"
        assert baseline.checksum == detector.compute_checksum(data)

    @pytest.mark.requirement("WL-312")
    def test_record_baseline_overwrites_previous(self, detector: PolicyChecksumDriftDetector) -> None:
        """Recording baseline twice overwrites the previous one."""
        data1 = {"role": "admin"}
        data2 = {"role": "user"}

        baseline1 = detector.record_baseline("policy-001", data1, "cycle-1")
        baseline2 = detector.record_baseline("policy-001", data2, "cycle-2")

        assert baseline1.checksum != baseline2.checksum
        assert detector.get_baseline("policy-001").checksum == baseline2.checksum

    @pytest.mark.requirement("WL-312")
    def test_check_drift_no_baseline_raises_error(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift raises KeyError if no baseline exists."""
        data = {"role": "admin"}

        with pytest.raises(KeyError, match="No baseline"):
            detector.check_drift("nonexistent", data)

    @pytest.mark.requirement("WL-312")
    def test_check_drift_no_drift(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift returns False if data matches baseline."""
        data = {"role": "admin", "permission": "read"}

        detector.record_baseline("policy-001", data, "cycle-1")
        has_drift = detector.check_drift("policy-001", data)

        assert has_drift is False

    @pytest.mark.requirement("WL-312")
    def test_check_drift_with_drift(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift returns True if data differs from baseline."""
        baseline_data = {"role": "admin", "permission": "read"}
        current_data = {"role": "admin", "permission": "write"}

        detector.record_baseline("policy-001", baseline_data, "cycle-1")
        has_drift = detector.check_drift("policy-001", current_data)

        assert has_drift is True

    @pytest.mark.requirement("WL-312")
    def test_check_drift_detects_field_addition(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift detects when fields are added."""
        baseline_data = {"role": "admin"}
        current_data = {"role": "admin", "permission": "read"}

        detector.record_baseline("policy-001", baseline_data, "cycle-1")
        has_drift = detector.check_drift("policy-001", current_data)

        assert has_drift is True

    @pytest.mark.requirement("WL-312")
    def test_check_drift_detects_field_removal(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift detects when fields are removed."""
        baseline_data = {"role": "admin", "permission": "read"}
        current_data = {"role": "admin"}

        detector.record_baseline("policy-001", baseline_data, "cycle-1")
        has_drift = detector.check_drift("policy-001", current_data)

        assert has_drift is True

    @pytest.mark.requirement("WL-312")
    def test_check_drift_order_independent(self, detector: PolicyChecksumDriftDetector) -> None:
        """check_drift returns False regardless of dict order."""
        baseline_data = {"role": "admin", "permission": "read"}
        current_data = {"permission": "read", "role": "admin"}

        detector.record_baseline("policy-001", baseline_data, "cycle-1")
        has_drift = detector.check_drift("policy-001", current_data)

        assert has_drift is False

    @pytest.mark.requirement("WL-312")
    def test_get_baseline_exists(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can retrieve baseline for existing policy."""
        data = {"role": "admin"}
        recorded = detector.record_baseline("policy-001", data, "cycle-1")

        retrieved = detector.get_baseline("policy-001")

        assert retrieved.policy_id == recorded.policy_id
        assert retrieved.checksum == recorded.checksum

    @pytest.mark.requirement("WL-312")
    def test_get_baseline_nonexistent_raises_error(self, detector: PolicyChecksumDriftDetector) -> None:
        """get_baseline raises KeyError for nonexistent policy."""
        with pytest.raises(KeyError, match="No baseline"):
            detector.get_baseline("nonexistent")

    @pytest.mark.requirement("WL-312")
    @pytest.mark.requirement("WL-226")
    def test_workflow_baseline_and_check(self, detector: PolicyChecksumDriftDetector) -> None:
        """Typical workflow: record baseline, then check for drift."""
        policy_id = "policy-rbac-001"
        cycle_id = "cycle-001"

        # Record initial policy state
        initial_policy = {"role": "admin", "permissions": ["read", "write", "delete"]}
        detector.record_baseline(policy_id, initial_policy, cycle_id)

        # Check if unchanged policy has drift
        assert detector.check_drift(policy_id, initial_policy) is False

        # Check if modified policy has drift
        modified_policy = {"role": "admin", "permissions": ["read", "write"]}
        assert detector.check_drift(policy_id, modified_policy) is True

    @pytest.mark.requirement("WL-312")
    def test_multiple_policies(self, detector: PolicyChecksumDriftDetector) -> None:
        """Can track multiple policies independently."""
        policy1_data = {"role": "admin"}
        policy2_data = {"role": "user"}

        detector.record_baseline("policy-001", policy1_data, "cycle-1")
        detector.record_baseline("policy-002", policy2_data, "cycle-1")

        # Drift in policy-002 should not affect policy-001
        assert detector.check_drift("policy-001", policy1_data) is False
        assert detector.check_drift("policy-002", {"role": "guest"}) is True
        assert detector.check_drift("policy-001", policy1_data) is False
