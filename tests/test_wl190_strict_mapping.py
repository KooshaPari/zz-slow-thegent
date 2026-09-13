"""Tests for WL-190: Strict mapping mode for connector state and field validation.

# @trace WL-190
"""

from __future__ import annotations

import pytest

from thegent.integrations.strict_mapping import (
    StrictMappingConfig,
    StrictMappingError,
    StrictMappingValidator,
)


class TestStrictMappingConfig:
    """Tests for StrictMappingConfig dataclass."""

    @pytest.mark.requirement("WL-190")
    def test_default_config_is_enabled(self):
        """# @trace WL-190 — default config has enabled=True."""
        config = StrictMappingConfig()
        assert config.enabled is True

    @pytest.mark.requirement("WL-190")
    def test_default_unknown_state_action_is_fail(self):
        """# @trace WL-190 — default unknown_state_action is 'fail'."""
        config = StrictMappingConfig()
        assert config.unknown_state_action == "fail"

    @pytest.mark.requirement("WL-190")
    def test_config_can_be_disabled(self):
        """# @trace WL-190 — config.enabled can be set to False."""
        config = StrictMappingConfig(enabled=False)
        assert config.enabled is False

    @pytest.mark.requirement("WL-190")
    def test_invalid_unknown_state_action_raises(self):
        """# @trace WL-190 — invalid unknown_state_action raises ValueError."""
        with pytest.raises(ValueError, match="must be 'fail', 'warn', or 'skip'"):
            StrictMappingConfig(unknown_state_action="invalid")

    @pytest.mark.requirement("WL-190")
    def test_valid_unknown_state_actions(self):
        """# @trace WL-190 — valid actions 'fail', 'warn', 'skip' are accepted."""
        for action in ("fail", "warn", "skip"):
            config = StrictMappingConfig(unknown_state_action=action)
            assert config.unknown_state_action == action


class TestStrictMappingValidator:
    """Tests for StrictMappingValidator class."""

    @pytest.mark.requirement("WL-190")
    def test_validator_with_default_config(self):
        """# @trace WL-190 — validator initializes with default config."""
        validator = StrictMappingValidator()
        assert validator.config.enabled is True
        assert validator.config.unknown_state_action == "fail"

    @pytest.mark.requirement("WL-190")
    def test_validator_accepts_custom_config(self):
        """# @trace WL-190 — validator accepts custom StrictMappingConfig."""
        config = StrictMappingConfig(enabled=False)
        validator = StrictMappingValidator(config)
        assert validator.config.enabled is False

    @pytest.mark.requirement("WL-190")
    def test_validate_remote_state_known_state_passes(self):
        """# @trace WL-190 — known state passes validation."""
        validator = StrictMappingValidator()
        is_valid, error = validator.validate_remote_state(
            "active", ["active", "inactive"]
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.requirement("WL-190")
    def test_validate_remote_state_unknown_state_fails_when_enabled(self):
        """# @trace WL-190 — unknown state raises StrictMappingError when enabled and action='fail'."""
        validator = StrictMappingValidator()
        with pytest.raises(StrictMappingError):
            validator.validate_remote_state("unknown", ["active", "inactive"])

    @pytest.mark.requirement("WL-190")
    def test_validate_remote_state_unknown_state_warn_mode(self):
        """# @trace WL-190 — unknown state returns (False, error_msg) when action='warn'."""
        config = StrictMappingConfig(unknown_state_action="warn")
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_remote_state(
            "unknown", ["active", "inactive"]
        )
        assert is_valid is False
        assert error is not None
        assert "Unknown state" in error

    @pytest.mark.requirement("WL-190")
    def test_validate_remote_state_unknown_state_skip_mode(self):
        """# @trace WL-190 — unknown state returns (False, None) when action='skip'."""
        config = StrictMappingConfig(unknown_state_action="skip")
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_remote_state(
            "unknown", ["active", "inactive"]
        )
        assert is_valid is False
        assert error is None

    @pytest.mark.requirement("WL-190")
    def test_validate_remote_state_disabled_accepts_unknown(self):
        """# @trace WL-190 — disabled strict mapping accepts unknown states."""
        config = StrictMappingConfig(enabled=False)
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_remote_state(
            "unknown", ["active", "inactive"]
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.requirement("WL-190")
    def test_validate_field_value_allowed_passes(self):
        """# @trace WL-190 — allowed field value passes validation."""
        validator = StrictMappingValidator()
        is_valid, error = validator.validate_field_value(
            "status", "pending", ["pending", "done"]
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.requirement("WL-190")
    def test_validate_field_value_not_allowed_fails(self):
        """# @trace WL-190 — disallowed field value raises StrictMappingError when enabled."""
        validator = StrictMappingValidator()
        with pytest.raises(StrictMappingError):
            validator.validate_field_value("status", "invalid", ["pending", "done"])

    @pytest.mark.requirement("WL-190")
    def test_validate_field_value_not_allowed_warn_mode(self):
        """# @trace WL-190 — disallowed field value returns (False, error_msg) when action='warn'."""
        config = StrictMappingConfig(unknown_state_action="warn")
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_field_value(
            "status", "invalid", ["pending", "done"]
        )
        assert is_valid is False
        assert error is not None
        assert "invalid value" in error

    @pytest.mark.requirement("WL-190")
    def test_validate_field_value_not_allowed_skip_mode(self):
        """# @trace WL-190 — disallowed field value returns (False, None) when action='skip'."""
        config = StrictMappingConfig(unknown_state_action="skip")
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_field_value(
            "status", "invalid", ["pending", "done"]
        )
        assert is_valid is False
        assert error is None

    @pytest.mark.requirement("WL-190")
    def test_validate_field_value_disabled_accepts_disallowed(self):
        """# @trace WL-190 — disabled strict mapping accepts disallowed field values."""
        config = StrictMappingConfig(enabled=False)
        validator = StrictMappingValidator(config)
        is_valid, error = validator.validate_field_value(
            "status", "invalid", ["pending", "done"]
        )
        assert is_valid is True
        assert error is None
