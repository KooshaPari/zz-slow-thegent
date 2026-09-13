"""Tests for WL-138 B90 Wave-2 risk register.

# @trace WL-138 B90-W2-E4
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
RISK_REGISTER = ROOT / "docs" / "reports" / "2026-02-21-B90-W2-risk-register.md"


def test_risk_register_file_exists() -> None:
    """Risk register file must exist at the expected path."""
    assert RISK_REGISTER.exists(), f"Expected {RISK_REGISTER} to exist"


def test_risk_register_has_main_heading() -> None:
    """Risk register must have the B90 Wave-2 Risk Register heading."""
    content = RISK_REGISTER.read_text(encoding="utf-8")
    assert "# B90 Wave-2 Risk Register" in content


def test_risk_register_has_active_risks_section() -> None:
    """Risk register must have an Active Risks section."""
    content = RISK_REGISTER.read_text(encoding="utf-8")
    assert "## Active Risks" in content


def test_risk_register_has_required_columns() -> None:
    """Active Risks table must have required column headers."""
    content = RISK_REGISTER.read_text(encoding="utf-8")
    assert "| ID |" in content
    assert "Risk" in content
    assert "Probability" in content
    assert "Impact" in content
    assert "Mitigation" in content
    assert "Owner" in content


def test_risk_register_has_required_baseline_risks() -> None:
    """Risk register must contain the four baseline risk IDs from the plan."""
    content = RISK_REGISTER.read_text(encoding="utf-8")
    for risk_id in ["R-W2-01", "R-W2-02", "R-W2-03", "R-W2-04"]:
        assert risk_id in content, f"Required risk {risk_id} must appear in risk register"


def test_risk_register_has_new_wave2_risks() -> None:
    """Risk register must include at least one new risk discovered during Wave-2."""
    content = RISK_REGISTER.read_text(encoding="utf-8")
    # R-W2-05 onwards are Wave-2-observed risks
    assert "R-W2-05" in content, "Risk register must include at least one new Wave-2 risk (R-W2-05)"
