"""Tests for WL-319: Symptom-to-Fix Docs Matrix."""

from __future__ import annotations

import pytest

from thegent.integrations.symptom_matrix import (
    SymptomEntry,
    find_by_keyword,
    get_symptom_matrix,
)


class TestSymptomEntry:
    """Tests for SymptomEntry dataclass."""

    @pytest.mark.requirement("WL-319")
    def test_creation(self) -> None:
        """Test SymptomEntry creation."""
        entry = SymptomEntry(
            symptom="Test symptom",
            cause="Test cause",
            diagnostic_cmd="test diag",
            fix_cmd="test fix",
            reference="test/ref.md",
        )
        assert entry.symptom == "Test symptom"
        assert entry.cause == "Test cause"
        assert entry.diagnostic_cmd == "test diag"
        assert entry.fix_cmd == "test fix"
        assert entry.reference == "test/ref.md"

    @pytest.mark.requirement("WL-319")
    def test_fields(self) -> None:
        """Test all required fields are present."""
        entry = SymptomEntry(
            symptom="s",
            cause="c",
            diagnostic_cmd="d",
            fix_cmd="f",
            reference="r",
        )
        assert hasattr(entry, "symptom")
        assert hasattr(entry, "cause")
        assert hasattr(entry, "diagnostic_cmd")
        assert hasattr(entry, "fix_cmd")
        assert hasattr(entry, "reference")


class TestGetSymptomMatrix:
    """Tests for get_symptom_matrix function."""

    @pytest.mark.requirement("WL-319")
    def test_returns_list(self) -> None:
        """Test get_symptom_matrix returns a list."""
        matrix = get_symptom_matrix()
        assert isinstance(matrix, list)

    @pytest.mark.requirement("WL-319")
    def test_returns_symptom_entries(self) -> None:
        """Test all items are SymptomEntry instances."""
        matrix = get_symptom_matrix()
        for entry in matrix:
            assert isinstance(entry, SymptomEntry)

    @pytest.mark.requirement("WL-319")
    def test_minimum_entries(self) -> None:
        """Test matrix has at least 10 entries."""
        matrix = get_symptom_matrix()
        assert len(matrix) >= 10, f"Expected at least 10 entries, got {len(matrix)}"

    @pytest.mark.requirement("WL-319")
    def test_entry_completeness(self) -> None:
        """Test all entries have non-empty fields."""
        matrix = get_symptom_matrix()
        for entry in matrix:
            assert entry.symptom, "symptom field is empty"
            assert entry.cause, "cause field is empty"
            assert entry.diagnostic_cmd, "diagnostic_cmd field is empty"
            assert entry.fix_cmd, "fix_cmd field is empty"
            assert entry.reference, "reference field is empty"

    @pytest.mark.requirement("WL-319")
    def test_contains_drift_symptom(self) -> None:
        """Test matrix contains drift detection entry."""
        matrix = get_symptom_matrix()
        symptoms = [e.symptom for e in matrix]
        assert any("drift" in s.lower() for s in symptoms)

    @pytest.mark.requirement("WL-319")
    def test_contains_conflict_symptom(self) -> None:
        """Test matrix contains conflict resolution entry."""
        matrix = get_symptom_matrix()
        symptoms = [e.symptom for e in matrix]
        assert any("conflict" in s.lower() for s in symptoms)

    @pytest.mark.requirement("WL-319")
    def test_contains_auth_symptom(self) -> None:
        """Test matrix contains authentication entry."""
        matrix = get_symptom_matrix()
        symptoms = [e.symptom for e in matrix]
        assert any("auth" in s.lower() for s in symptoms)

    @pytest.mark.requirement("WL-319")
    def test_contains_rate_limit_symptom(self) -> None:
        """Test matrix contains rate limit entry."""
        matrix = get_symptom_matrix()
        symptoms = [e.symptom for e in matrix]
        assert any("rate" in s.lower() for s in symptoms)

    @pytest.mark.requirement("WL-319")
    def test_contains_stuck_symptom(self) -> None:
        """Test matrix contains stuck sync entry."""
        matrix = get_symptom_matrix()
        symptoms = [e.symptom for e in matrix]
        assert any("stuck" in s.lower() for s in symptoms)


class TestFindByKeyword:
    """Tests for find_by_keyword function."""

    @pytest.mark.requirement("WL-319")
    def test_returns_list(self) -> None:
        """Test find_by_keyword returns a list."""
        result = find_by_keyword("drift")
        assert isinstance(result, list)

    @pytest.mark.requirement("WL-319")
    def test_case_insensitive_search(self) -> None:
        """Test keyword search is case-insensitive."""
        result_lower = find_by_keyword("drift")
        result_upper = find_by_keyword("DRIFT")
        assert len(result_lower) == len(result_upper)
        assert result_lower == result_upper

    @pytest.mark.requirement("WL-319")
    def test_finds_symptom_keyword(self) -> None:
        """Test finding by symptom keyword."""
        result = find_by_keyword("drift")
        assert len(result) > 0
        assert any("drift" in e.symptom.lower() for e in result)

    @pytest.mark.requirement("WL-319")
    def test_finds_cause_keyword(self) -> None:
        """Test finding by cause keyword."""
        result = find_by_keyword("expired")
        assert len(result) > 0
        assert any("expired" in e.cause.lower() for e in result)

    @pytest.mark.requirement("WL-319")
    def test_no_matches_returns_empty(self) -> None:
        """Test no matches returns empty list."""
        result = find_by_keyword("xyzabc_nonexistent")
        assert result == []

    @pytest.mark.requirement("WL-319")
    def test_find_auth_issues(self) -> None:
        """Test finding authentication-related issues."""
        result = find_by_keyword("auth")
        assert len(result) > 0

    @pytest.mark.requirement("WL-319")
    def test_find_conflict_issues(self) -> None:
        """Test finding conflict-related issues."""
        result = find_by_keyword("conflict")
        assert len(result) > 0

    @pytest.mark.requirement("WL-319")
    def test_find_rate_limit_issues(self) -> None:
        """Test finding rate limit issues."""
        result = find_by_keyword("rate")
        assert len(result) > 0

    @pytest.mark.requirement("WL-319")
    def test_search_results_contain_entries(self) -> None:
        """Test search results are SymptomEntry instances."""
        result = find_by_keyword("drift")
        for entry in result:
            assert isinstance(entry, SymptomEntry)
