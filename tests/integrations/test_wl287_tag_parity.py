"""Tests for thegent.integrations.tag_parity — Label/Tag Parity Checker.

@trace WL-287
"""

from __future__ import annotations

import pytest

from thegent.integrations.tag_parity import (
    TagParityChecker,
    TagParityResult,
)


class TestTagParityResultCreation:
    """Test TagParityResult dataclass creation."""

    @pytest.mark.requirement("WL-287")
    def test_create_parity_result(self) -> None:
        """Can create a TagParityResult with required fields."""
        result = TagParityResult(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag2", "tag3"],
            missing_remote=["tag1"],
            missing_local=["tag3"],
        )

        assert result.wl_id == "WL-001"
        assert result.local_tags == ["tag1", "tag2"]
        assert result.remote_tags == ["tag2", "tag3"]
        assert result.missing_remote == ["tag1"]
        assert result.missing_local == ["tag3"]


class TestTagParityCheckerCheck:
    """Test TagParityChecker.check operations."""

    @pytest.fixture
    def checker(self) -> TagParityChecker:
        """Provide a TagParityChecker instance."""
        return TagParityChecker()

    @pytest.mark.requirement("WL-287")
    def test_check_identical_tags(self, checker: TagParityChecker) -> None:
        """check returns empty missing lists when tags are identical."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag1", "tag2"],
        )

        assert result.wl_id == "WL-001"
        assert result.missing_remote == []
        assert result.missing_local == []

    @pytest.mark.requirement("WL-287")
    def test_check_local_only_tag(self, checker: TagParityChecker) -> None:
        """check detects tags in local but not remote."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag1"],
        )

        assert result.missing_remote == ["tag2"]
        assert result.missing_local == []

    @pytest.mark.requirement("WL-287")
    def test_check_remote_only_tag(self, checker: TagParityChecker) -> None:
        """check detects tags in remote but not local."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=["tag1"],
            remote_tags=["tag1", "tag2"],
        )

        assert result.missing_remote == []
        assert result.missing_local == ["tag2"]

    @pytest.mark.requirement("WL-287")
    def test_check_both_missing(self, checker: TagParityChecker) -> None:
        """check detects tags missing in both directions."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag3", "tag4"],
        )

        assert result.missing_remote == ["tag1", "tag2"]
        assert result.missing_local == ["tag3", "tag4"]

    @pytest.mark.requirement("WL-287")
    def test_check_empty_tags(self, checker: TagParityChecker) -> None:
        """check handles empty tag lists."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=[],
            remote_tags=[],
        )

        assert result.missing_remote == []
        assert result.missing_local == []

    @pytest.mark.requirement("WL-287")
    def test_check_sorted_output(self, checker: TagParityChecker) -> None:
        """check returns sorted tag lists."""
        result = checker.check(
            wl_id="WL-001",
            local_tags=["zebra", "apple", "banana"],
            remote_tags=["zebra", "cherry"],
        )

        assert result.local_tags == ["apple", "banana", "zebra"]
        assert result.remote_tags == ["cherry", "zebra"]
        assert result.missing_remote == ["apple", "banana"]

    @pytest.mark.requirement("WL-287")
    def test_check_empty_wl_id_raises_error(self, checker: TagParityChecker) -> None:
        """check raises ValueError for empty wl_id."""
        with pytest.raises(ValueError, match="wl_id cannot be empty"):
            checker.check("", ["tag1"], ["tag1"])

    @pytest.mark.requirement("WL-287")
    def test_check_invalid_local_tags_type(self, checker: TagParityChecker) -> None:
        """check raises ValueError if local_tags is not a list."""
        with pytest.raises(ValueError, match="must be lists"):
            checker.check("WL-001", "tag1", ["tag1"])  # type: ignore

    @pytest.mark.requirement("WL-287")
    def test_check_invalid_remote_tags_type(self, checker: TagParityChecker) -> None:
        """check raises ValueError if remote_tags is not a list."""
        with pytest.raises(ValueError, match="must be lists"):
            checker.check("WL-001", ["tag1"], "tag1")  # type: ignore


class TestTagParityCheckerIsInParity:
    """Test TagParityChecker.is_in_parity operations."""

    @pytest.fixture
    def checker(self) -> TagParityChecker:
        """Provide a TagParityChecker instance."""
        return TagParityChecker()

    @pytest.mark.requirement("WL-287")
    def test_is_in_parity_true_when_empty(self, checker: TagParityChecker) -> None:
        """is_in_parity returns True when no missing tags."""
        result = TagParityResult(
            wl_id="WL-001",
            local_tags=["tag1"],
            remote_tags=["tag1"],
            missing_remote=[],
            missing_local=[],
        )

        assert checker.is_in_parity(result) is True

    @pytest.mark.requirement("WL-287")
    def test_is_in_parity_false_when_missing_remote(
        self, checker: TagParityChecker
    ) -> None:
        """is_in_parity returns False when tags missing in remote."""
        result = TagParityResult(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag1"],
            missing_remote=["tag2"],
            missing_local=[],
        )

        assert checker.is_in_parity(result) is False

    @pytest.mark.requirement("WL-287")
    def test_is_in_parity_false_when_missing_local(
        self, checker: TagParityChecker
    ) -> None:
        """is_in_parity returns False when tags missing in local."""
        result = TagParityResult(
            wl_id="WL-001",
            local_tags=["tag1"],
            remote_tags=["tag1", "tag2"],
            missing_remote=[],
            missing_local=["tag2"],
        )

        assert checker.is_in_parity(result) is False

    @pytest.mark.requirement("WL-287")
    def test_is_in_parity_false_when_both_missing(
        self, checker: TagParityChecker
    ) -> None:
        """is_in_parity returns False when tags missing in both."""
        result = TagParityResult(
            wl_id="WL-001",
            local_tags=["tag1", "tag2"],
            remote_tags=["tag3", "tag4"],
            missing_remote=["tag1", "tag2"],
            missing_local=["tag3", "tag4"],
        )

        assert checker.is_in_parity(result) is False


class TestTagParityCheckerCheckBatch:
    """Test TagParityChecker.check_batch operations."""

    @pytest.fixture
    def checker(self) -> TagParityChecker:
        """Provide a TagParityChecker instance."""
        return TagParityChecker()

    @pytest.mark.requirement("WL-287")
    def test_check_batch_single_item(self, checker: TagParityChecker) -> None:
        """check_batch processes single item."""
        items = [
            {
                "wl_id": "WL-001",
                "local_tags": ["tag1"],
                "remote_tags": ["tag1"],
            }
        ]

        results = checker.check_batch(items)

        assert len(results) == 1
        assert results[0].wl_id == "WL-001"
        assert results[0].missing_remote == []
        assert results[0].missing_local == []

    @pytest.mark.requirement("WL-287")
    def test_check_batch_multiple_items(self, checker: TagParityChecker) -> None:
        """check_batch processes multiple items."""
        items = [
            {
                "wl_id": "WL-001",
                "local_tags": ["tag1", "tag2"],
                "remote_tags": ["tag1"],
            },
            {
                "wl_id": "WL-002",
                "local_tags": ["tag3"],
                "remote_tags": ["tag3", "tag4"],
            },
        ]

        results = checker.check_batch(items)

        assert len(results) == 2
        assert results[0].wl_id == "WL-001"
        assert results[0].missing_remote == ["tag2"]
        assert results[1].wl_id == "WL-002"
        assert results[1].missing_local == ["tag4"]

    @pytest.mark.requirement("WL-287")
    def test_check_batch_missing_wl_id(self, checker: TagParityChecker) -> None:
        """check_batch raises ValueError if item missing wl_id."""
        items = [
            {
                "local_tags": ["tag1"],
                "remote_tags": ["tag1"],
            }
        ]

        with pytest.raises(ValueError, match="missing required keys"):
            checker.check_batch(items)

    @pytest.mark.requirement("WL-287")
    def test_check_batch_missing_local_tags(self, checker: TagParityChecker) -> None:
        """check_batch raises ValueError if item missing local_tags."""
        items = [
            {
                "wl_id": "WL-001",
                "remote_tags": ["tag1"],
            }
        ]

        with pytest.raises(ValueError, match="missing required keys"):
            checker.check_batch(items)

    @pytest.mark.requirement("WL-287")
    def test_check_batch_empty_list(self, checker: TagParityChecker) -> None:
        """check_batch returns empty list for empty input."""
        results = checker.check_batch([])

        assert results == []

    @pytest.mark.requirement("WL-287")
    def test_check_batch_complex_scenario(self, checker: TagParityChecker) -> None:
        """check_batch handles complex multi-item scenario."""
        items = [
            {
                "wl_id": "WL-001",
                "local_tags": ["feature", "bug", "urgent"],
                "remote_tags": ["feature", "urgent"],
            },
            {
                "wl_id": "WL-002",
                "local_tags": ["documentation"],
                "remote_tags": ["documentation", "review"],
            },
            {
                "wl_id": "WL-003",
                "local_tags": [],
                "remote_tags": ["archived"],
            },
        ]

        results = checker.check_batch(items)

        assert len(results) == 3

        # WL-001: missing "bug" in remote
        assert results[0].missing_remote == ["bug"]
        assert results[0].missing_local == []

        # WL-002: missing "review" in local
        assert results[1].missing_remote == []
        assert results[1].missing_local == ["review"]

        # WL-003: missing "archived" in local
        assert results[2].missing_remote == []
        assert results[2].missing_local == ["archived"]
