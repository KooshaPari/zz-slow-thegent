"""Tests for thegent.integrations.tag_taxonomy — Local Tag Taxonomy Validator.

@trace WL-288
"""

from __future__ import annotations

import pytest

from thegent.integrations.tag_taxonomy import (
    TagTaxonomyValidator,
    TaxonomyViolation,
)


class TestTaxonomyViolationCreation:
    """Test TaxonomyViolation dataclass creation."""

    @pytest.mark.requirement("WL-288")
    def test_create_violation(self) -> None:
        """Can create a TaxonomyViolation with required fields."""
        violation = TaxonomyViolation(
            tag="invalid-tag",
            wl_id="WL-001",
            reason="Tag not in allowed taxonomy",
        )

        assert violation.tag == "invalid-tag"
        assert violation.wl_id == "WL-001"
        assert violation.reason == "Tag not in allowed taxonomy"


class TestTagTaxonomyValidatorInit:
    """Test TagTaxonomyValidator initialization."""

    @pytest.mark.requirement("WL-288")
    def test_init_with_valid_tags(self) -> None:
        """Can create validator with valid tag list."""
        allowed = ["feature", "bug", "documentation"]
        validator = TagTaxonomyValidator(allowed)

        assert validator.list_allowed() == ["bug", "documentation", "feature"]

    @pytest.mark.requirement("WL-288")
    def test_init_with_non_list_raises_error(self) -> None:
        """Init raises ValueError if allowed_tags is not a list."""
        with pytest.raises(ValueError, match="allowed_tags must be a list"):
            TagTaxonomyValidator("feature")  # type: ignore

    @pytest.mark.requirement("WL-288")
    def test_init_with_empty_list_raises_error(self) -> None:
        """Init raises ValueError if allowed_tags is empty."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TagTaxonomyValidator([])


class TestTagTaxonomyValidatorValidate:
    """Test TagTaxonomyValidator.validate operations."""

    @pytest.fixture
    def validator(self) -> TagTaxonomyValidator:
        """Provide a TagTaxonomyValidator instance."""
        return TagTaxonomyValidator(["feature", "bug", "documentation", "wontfix"])

    @pytest.mark.requirement("WL-288")
    def test_validate_all_valid_tags(self, validator: TagTaxonomyValidator) -> None:
        """validate returns no violations when all tags are valid."""
        violations = validator.validate("WL-001", ["feature", "bug"])

        assert violations == []

    @pytest.mark.requirement("WL-288")
    def test_validate_single_invalid_tag(self, validator: TagTaxonomyValidator) -> None:
        """validate detects single invalid tag."""
        violations = validator.validate("WL-001", ["feature", "invalid"])

        assert len(violations) == 1
        assert violations[0].tag == "invalid"
        assert violations[0].wl_id == "WL-001"
        assert "not in the allowed taxonomy" in violations[0].reason

    @pytest.mark.requirement("WL-288")
    def test_validate_multiple_invalid_tags(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """validate detects multiple invalid tags."""
        violations = validator.validate("WL-001", ["feature", "invalid1", "invalid2"])

        assert len(violations) == 2
        tags = {v.tag for v in violations}
        assert tags == {"invalid1", "invalid2"}

    @pytest.mark.requirement("WL-288")
    def test_validate_empty_tags(self, validator: TagTaxonomyValidator) -> None:
        """validate returns no violations for empty tag list."""
        violations = validator.validate("WL-001", [])

        assert violations == []

    @pytest.mark.requirement("WL-288")
    def test_validate_empty_wl_id_raises_error(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """validate raises ValueError for empty wl_id."""
        with pytest.raises(ValueError, match="wl_id cannot be empty"):
            validator.validate("", ["feature"])

    @pytest.mark.requirement("WL-288")
    def test_validate_non_list_tags_raises_error(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """validate raises ValueError if tags is not a list."""
        with pytest.raises(ValueError, match="tags must be a list"):
            validator.validate("WL-001", "feature")  # type: ignore

    @pytest.mark.requirement("WL-288")
    def test_validate_all_invalid_tags(self, validator: TagTaxonomyValidator) -> None:
        """validate detects all invalid tags."""
        violations = validator.validate("WL-001", ["bad1", "bad2", "bad3"])

        assert len(violations) == 3


class TestTagTaxonomyValidatorIsValid:
    """Test TagTaxonomyValidator.is_valid operations."""

    @pytest.fixture
    def validator(self) -> TagTaxonomyValidator:
        """Provide a TagTaxonomyValidator instance."""
        return TagTaxonomyValidator(["feature", "bug", "documentation"])

    @pytest.mark.requirement("WL-288")
    def test_is_valid_true_for_valid_tags(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """is_valid returns True for valid tags."""
        assert validator.is_valid("WL-001", ["feature", "bug"]) is True

    @pytest.mark.requirement("WL-288")
    def test_is_valid_false_for_invalid_tags(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """is_valid returns False for invalid tags."""
        assert validator.is_valid("WL-001", ["feature", "invalid"]) is False

    @pytest.mark.requirement("WL-288")
    def test_is_valid_true_for_empty_tags(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """is_valid returns True for empty tag list."""
        assert validator.is_valid("WL-001", []) is True

    @pytest.mark.requirement("WL-288")
    def test_is_valid_single_valid_tag(self, validator: TagTaxonomyValidator) -> None:
        """is_valid works for single valid tag."""
        assert validator.is_valid("WL-001", ["feature"]) is True

    @pytest.mark.requirement("WL-288")
    def test_is_valid_single_invalid_tag(self, validator: TagTaxonomyValidator) -> None:
        """is_valid works for single invalid tag."""
        assert validator.is_valid("WL-001", ["invalid"]) is False


class TestTagTaxonomyValidatorAddAllowed:
    """Test TagTaxonomyValidator.add_allowed operations."""

    @pytest.fixture
    def validator(self) -> TagTaxonomyValidator:
        """Provide a TagTaxonomyValidator instance."""
        return TagTaxonomyValidator(["feature", "bug"])

    @pytest.mark.requirement("WL-288")
    def test_add_allowed_extends_taxonomy(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """add_allowed adds new tag to allowed set."""
        validator.add_allowed("documentation")

        assert validator.is_valid("WL-001", ["documentation"]) is True

    @pytest.mark.requirement("WL-288")
    def test_add_allowed_multiple_times(self, validator: TagTaxonomyValidator) -> None:
        """add_allowed can be called multiple times."""
        validator.add_allowed("documentation")
        validator.add_allowed("wontfix")

        assert validator.is_valid("WL-001", ["documentation", "wontfix"]) is True

    @pytest.mark.requirement("WL-288")
    def test_add_allowed_duplicate(self, validator: TagTaxonomyValidator) -> None:
        """add_allowed handles duplicate tags gracefully."""
        validator.add_allowed("feature")  # Already exists

        assert validator.is_valid("WL-001", ["feature"]) is True

    @pytest.mark.requirement("WL-288")
    def test_add_allowed_empty_raises_error(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """add_allowed raises ValueError for empty tag."""
        with pytest.raises(ValueError, match="tag cannot be empty"):
            validator.add_allowed("")

    @pytest.mark.requirement("WL-288")
    def test_add_allowed_reflects_in_list(
        self, validator: TagTaxonomyValidator
    ) -> None:
        """add_allowed updates list_allowed output."""
        original = validator.list_allowed()
        validator.add_allowed("newfeature")
        updated = validator.list_allowed()

        assert len(updated) == len(original) + 1
        assert "newfeature" in updated


class TestTagTaxonomyValidatorListAllowed:
    """Test TagTaxonomyValidator.list_allowed operations."""

    @pytest.mark.requirement("WL-288")
    def test_list_allowed_returns_sorted(self) -> None:
        """list_allowed returns sorted list."""
        validator = TagTaxonomyValidator(["zebra", "apple", "banana"])
        allowed = validator.list_allowed()

        assert allowed == ["apple", "banana", "zebra"]

    @pytest.mark.requirement("WL-288")
    def test_list_allowed_independent_copy(self) -> None:
        """list_allowed returns independent list."""
        validator = TagTaxonomyValidator(["feature", "bug"])
        allowed1 = validator.list_allowed()
        allowed2 = validator.list_allowed()

        assert allowed1 == allowed2
        # Modifying returned list doesn't affect validator
        allowed1.append("newfeature")
        assert validator.is_valid("WL-001", ["newfeature"]) is False

    @pytest.mark.requirement("WL-288")
    def test_list_allowed_complex_scenario(self) -> None:
        """list_allowed works with complex taxonomy."""
        tags = [
            "feature",
            "bug",
            "documentation",
            "test",
            "refactor",
            "security",
            "performance",
        ]
        validator = TagTaxonomyValidator(tags)
        allowed = validator.list_allowed()

        assert len(allowed) == len(tags)
        assert allowed == sorted(tags)

    @pytest.mark.requirement("WL-288")
    def test_list_allowed_after_add(self) -> None:
        """list_allowed reflects additions."""
        validator = TagTaxonomyValidator(["feature"])
        validator.add_allowed("bug")
        validator.add_allowed("documentation")

        allowed = validator.list_allowed()
        assert allowed == ["bug", "documentation", "feature"]


class TestTagTaxonomyValidatorIntegration:
    """Integration tests for TagTaxonomyValidator."""

    @pytest.mark.requirement("WL-288")
    def test_full_workflow(self) -> None:
        """Full workflow: init, validate, add, re-validate."""
        validator = TagTaxonomyValidator(["feature", "bug"])

        # Initial validation
        assert validator.is_valid("WL-001", ["feature", "bug"]) is True
        assert validator.is_valid("WL-001", ["documentation"]) is False

        # Add new tag
        validator.add_allowed("documentation")

        # Re-validate
        assert validator.is_valid("WL-001", ["documentation"]) is True
        assert validator.is_valid("WL-001", ["feature", "bug", "documentation"]) is True

    @pytest.mark.requirement("WL-288")
    def test_batch_validation_simulation(self) -> None:
        """Simulate batch validation of multiple items."""
        validator = TagTaxonomyValidator(["feature", "bug", "documentation"])

        items = [
            ("WL-001", ["feature"]),
            ("WL-002", ["bug", "documentation"]),
            ("WL-003", ["feature", "invalid"]),
            ("WL-004", []),
        ]

        for wl_id, tags in items:
            violations = validator.validate(wl_id, tags)
            if wl_id == "WL-003":
                assert len(violations) == 1
                assert violations[0].tag == "invalid"
            else:
                assert len(violations) == 0
