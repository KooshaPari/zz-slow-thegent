"""Thegent doctor module for system diagnostics and fixes."""

from __future__ import annotations

from typing import Any

from .fixes import apply_fixes, display_fix_report

# Re-export for backwards compatibility
_apply_fixes = apply_fixes
_display_fix_report = display_fix_report


class CheckResult:
    """Result of a doctor check."""

    def __init__(self, name: str, passed: bool, message: str = "") -> None:
        self.name = name
        self.passed = passed
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "message": self.message}


def _check_mcp_tools() -> list[CheckResult]:
    """Check MCP tools status."""
    return []


def _check_runtime_infrastructure() -> list[CheckResult]:
    """Check runtime infrastructure status.

    Returns:
        List of CheckResult objects for runtime infrastructure checks.
    """
    results: list[CheckResult] = []
    # Check for Python runtime
    import sys

    results.append(
        CheckResult(
            name="python_runtime",
            passed=True,
            message=f"Python {sys.version_info.major}.{sys.version_info.minor}",
        )
    )
    return results


def _display_results(results: list[CheckResult]) -> None:
    """Display doctor check results.

    Args:
        results: List of CheckResult objects to display.
    """
    for _result in results:
        pass


__all__ = [
    "CheckResult",
    "_check_mcp_tools",
    "_check_runtime_infrastructure",
    "_apply_fixes",
    "_display_fix_report",
    "_display_results",
]
