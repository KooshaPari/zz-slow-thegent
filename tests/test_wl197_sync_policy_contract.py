"""Tests for WL-197: Sync Policy File Contract.

Verifies contract creation and validation rules.

# @trace WL-197
"""

from __future__ import annotations

import pytest

from thegent.integrations.sync_policy_contract import (
    SyncPolicyContract,
    SyncPolicyValidator,
)


@pytest.mark.requirement("WL-197")
class TestSyncPolicyContractCreation:
    """WL-197: SyncPolicyContract dataclass creation."""

    def test_create_with_required_fields(self):
        """Create contract with required fields."""
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["stripe", "paypal"],
        )

        assert policy.version == "1.0"
        assert policy.allowed_connectors == ["stripe", "paypal"]
        assert policy.max_batch_size == 100
        assert policy.dry_run is False

    def test_create_with_all_fields(self):
        """Create contract with all fields specified."""
        policy = SyncPolicyContract(
            version="2.0",
            allowed_connectors=["slack", "teams"],
            max_batch_size=500,
            dry_run=True,
        )

        assert policy.version == "2.0"
        assert policy.allowed_connectors == ["slack", "teams"]
        assert policy.max_batch_size == 500
        assert policy.dry_run is True

    def test_create_with_single_connector(self):
        """Create contract with single connector."""
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["github"],
        )

        assert policy.allowed_connectors == ["github"]

    def test_create_with_many_connectors(self):
        """Create contract with many connectors."""
        connectors = ["stripe", "paypal", "square", "adyen", "braintree"]
        policy = SyncPolicyContract(version="1.0", allowed_connectors=connectors)

        assert len(policy.allowed_connectors) == 5
        assert policy.allowed_connectors == connectors


@pytest.mark.requirement("WL-197")
class TestSyncPolicyValidatorValid:
    """WL-197: Validation of valid policies."""

    def test_validate_valid_minimal_policy(self):
        """Validate minimal valid policy."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(version="1.0", allowed_connectors=["connector"])

        errors = validator.validate(policy)

        assert errors == []

    def test_validate_valid_full_policy(self):
        """Validate full valid policy."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="2.0",
            allowed_connectors=["a", "b", "c"],
            max_batch_size=200,
            dry_run=True,
        )

        errors = validator.validate(policy)

        assert errors == []

    def test_validate_version_with_semver(self):
        """Validate policy with semantic version."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(version="1.2.3", allowed_connectors=["stripe"])

        errors = validator.validate(policy)

        assert errors == []

    def test_validate_large_batch_size(self):
        """Validate policy with large batch size."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["api"],
            max_batch_size=10000,
        )

        errors = validator.validate(policy)

        assert errors == []


@pytest.mark.requirement("WL-197")
class TestSyncPolicyValidatorInvalid:
    """WL-197: Validation of invalid policies."""

    def test_validate_empty_version(self):
        """Reject policy with empty version."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(version="", allowed_connectors=["connector"])

        errors = validator.validate(policy)

        assert "version must be non-empty" in errors

    def test_validate_whitespace_only_version(self):
        """Reject policy with whitespace-only version."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(version="   ", allowed_connectors=["connector"])

        errors = validator.validate(policy)

        assert "version must be non-empty" in errors

    def test_validate_empty_connectors_list(self):
        """Reject policy with empty connectors list."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(version="1.0", allowed_connectors=[])

        errors = validator.validate(policy)

        assert "allowed_connectors must be non-empty" in errors

    def test_validate_zero_batch_size(self):
        """Reject policy with zero batch size."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["connector"],
            max_batch_size=0,
        )

        errors = validator.validate(policy)

        assert "max_batch_size must be > 0" in errors

    def test_validate_negative_batch_size(self):
        """Reject policy with negative batch size."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["connector"],
            max_batch_size=-100,
        )

        errors = validator.validate(policy)

        assert "max_batch_size must be > 0" in errors

    def test_validate_multiple_errors(self):
        """Report multiple validation errors."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="",
            allowed_connectors=[],
            max_batch_size=-1,
        )

        errors = validator.validate(policy)

        assert len(errors) == 3
        assert "version must be non-empty" in errors
        assert "allowed_connectors must be non-empty" in errors
        assert "max_batch_size must be > 0" in errors

    def test_validate_only_batch_size_error(self):
        """Validate correctly even with partial errors."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["ok"],
            max_batch_size=-5,
        )

        errors = validator.validate(policy)

        assert len(errors) == 1
        assert errors[0] == "max_batch_size must be > 0"


@pytest.mark.requirement("WL-197")
class TestSyncPolicyValidatorBoundary:
    """WL-197: Boundary and edge cases."""

    def test_validate_batch_size_one(self):
        """Valid policy with batch size of 1."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="1.0",
            allowed_connectors=["connector"],
            max_batch_size=1,
        )

        errors = validator.validate(policy)

        assert errors == []

    def test_validate_very_long_version_string(self):
        """Valid policy with very long version string."""
        validator = SyncPolicyValidator()
        policy = SyncPolicyContract(
            version="v1.2.3-alpha+build.12345.12345.12345",
            allowed_connectors=["connector"],
        )

        errors = validator.validate(policy)

        assert errors == []

    def test_validate_many_connectors(self):
        """Valid policy with many allowed connectors."""
        validator = SyncPolicyValidator()
        connectors = [f"connector_{i}" for i in range(100)]
        policy = SyncPolicyContract(version="1.0", allowed_connectors=connectors)

        errors = validator.validate(policy)

        assert errors == []
