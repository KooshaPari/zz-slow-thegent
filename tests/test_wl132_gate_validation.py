# @trace WL-132 B90-W3-D3
"""Tests that validate the Zig gate validation report exists and is well-formed.

B90-W3-D3: Validate Zig gate behavior on macOS/Linux lanes.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

ZIG_GATE_REPORT = REPO_ROOT / "docs" / "reports" / "2026-02-21-B90-W3-D3-zig-gate-validation.md"


def test_zig_gate_validation_report_exists() -> None:
    """The Zig gate validation report must exist."""
    assert ZIG_GATE_REPORT.exists(), f"Zig gate validation report not found at {ZIG_GATE_REPORT}"


def test_zig_gate_report_mentions_platform() -> None:
    """The report must mention the platform (macOS, darwin, or 'platform')."""
    content = ZIG_GATE_REPORT.read_text()
    assert any(keyword in content.lower() for keyword in ("macos", "darwin", "platform")), (
        "Zig gate validation report must mention platform information"
    )


def test_zig_gate_report_mentions_abi_or_contract() -> None:
    """The report must mention ABI or contract validation."""
    content = ZIG_GATE_REPORT.read_text()
    assert any(keyword in content.upper() for keyword in ("ABI", "CONTRACT")), (
        "Zig gate validation report must mention ABI or contract"
    )


def test_zig_gate_report_is_non_empty() -> None:
    """The Zig gate validation report must be non-empty."""
    content = ZIG_GATE_REPORT.read_text()
    assert len(content.strip()) > 100, "Zig gate validation report appears empty"
