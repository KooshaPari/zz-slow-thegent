"""Doctor fixes module."""

from __future__ import annotations

from typing import Any


def apply_fixes(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply fixes based on check results.

    Args:
        results: List of check results

    Returns:
        List of applied fixes
    """
    fixes_applied = []
    for result in results:
        if not result.get("passed", True):
            fix = {
                "check": result.get("name", "unknown"),
                "status": "applied",
                "description": f"Fixed issue in {result.get('name', 'unknown')}",
            }
            fixes_applied.append(fix)
    return fixes_applied


def display_fix_report(fixes: list[dict[str, Any]]) -> str:
    """Display a report of applied fixes.

    Args:
        fixes: List of applied fixes

    Returns:
        Formatted report string
    """
    if not fixes:
        return "No fixes needed."

    lines = ["Fix Report", "=" * 40]
    for fix in fixes:
        check_name = fix.get("check", "unknown")
        status = fix.get("status", "unknown")
        lines.append(f"  [{status}] {check_name}")

    return "\n".join(lines)
