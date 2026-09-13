"""Unit tests for WP-27003: Formal Verification of Schema Evolution."""

from thegent.verification.schema_formal import SchemaEvolutionVerifier


def test_schema_evolution_compatible_addition():
    verifier = SchemaEvolutionVerifier()
    old = {"a": 1, "b": "test"}
    new = {"a": 1, "b": "test", "c": [1, 2, 3]}

    result = verifier.verify_compatibility(old, new)
    assert result["compatible"] is True
    assert "c" in result["added"]
    assert not result["errors"]
    assert "Evolution: New fields added: c" in result["warnings"][0]


def test_schema_evolution_breaking_removal():
    verifier = SchemaEvolutionVerifier()
    old = {"a": 1, "b": "test"}
    new = {"a": 1}

    result = verifier.verify_compatibility(old, new)
    assert result["compatible"] is False
    assert "b" in result["removed"]
    assert any("Breaking change" in e for e in result["errors"])


def test_schema_evolution_breaking_type_change():
    verifier = SchemaEvolutionVerifier()
    old = {"a": 1}
    new = {"a": "1"}  # Changed from int to str

    result = verifier.verify_compatibility(old, new)
    assert result["compatible"] is False
    assert any("type changed from int to str" in e for e in result["errors"])


def test_nested_schema_evolution():
    verifier = SchemaEvolutionVerifier()
    old = {"meta": {"version": 1}}
    new = {"meta": {"version": 1, "author": "agent"}}

    result = verifier.verify_compatibility(old, new)
    assert result["compatible"] is True
    assert not result["errors"]


def test_nested_schema_breaking():
    verifier = SchemaEvolutionVerifier()
    old = {"meta": {"version": 1}}
    new = {"meta": {"version": "1"}}  # type change in nested dict

    result = verifier.verify_compatibility(old, new)
    assert result["compatible"] is False
    assert any("In field 'meta'" in e for e in result["errors"])


def test_tag_evolution_compatible():
    verifier = SchemaEvolutionVerifier()
    old = ["STATUS", "SUMMARY"]
    new = ["STATUS", "SUMMARY", "PROGRESS"]

    result = verifier.verify_tag_evolution(old, new)
    assert result["compatible"] is True
    assert "PROGRESS" in result["added"]


def test_tag_evolution_breaking():
    verifier = SchemaEvolutionVerifier()
    old = ["STATUS", "SUMMARY"]
    new = ["STATUS"]  # Removed SUMMARY

    result = verifier.verify_tag_evolution(old, new)
    assert result["compatible"] is False
    assert "SUMMARY" in result["removed"]


def test_liveness_impact():
    verifier = SchemaEvolutionVerifier()

    # OK evolution
    report_ok = verifier.verify_tag_evolution(["STATUS", "SUMMARY"], ["STATUS", "SUMMARY", "LOG"])
    assert verifier.check_liveness_impact(report_ok) is True

    # Impactful evolution (removing STATUS)
    report_bad = verifier.verify_tag_evolution(["STATUS", "SUMMARY"], ["SUMMARY", "LOG"])
    assert verifier.check_liveness_impact(report_bad) is False
