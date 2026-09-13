"""Tests for WL-117 VS Code extension dependency check (WL-104 gate).

# @trace WL-117 B90-W2-E5
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
WORK_STREAM = ROOT / "docs" / "reference" / "WORK_STREAM.md"
VSCODE_EXT_DIR = ROOT / "extensions" / "vscode"
SCAFFOLD_PLAN = ROOT / "docs" / "plans" / "WL-117-VSCODE-EXTENSION-SCAFFOLD.md"


def _get_wl104_status() -> str:
    """Extract WL-104 status from WORK_STREAM.md."""
    content = WORK_STREAM.read_text(encoding="utf-8")
    lines = content.splitlines()
    in_wl104 = False
    for line in lines:
        if "[WL-104]" in line:
            in_wl104 = True
        if in_wl104 and "**Status:**" in line:
            return line.strip()
    return "NOT_FOUND"


def test_wl104_status_is_completed() -> None:
    """WL-104 (embedding protocol) must be COMPLETED before WL-117 can proceed."""
    status_line = _get_wl104_status()
    assert "COMPLETED" in status_line, f"WL-104 must be COMPLETED to unblock WL-117, but got: {status_line}"


def test_vscode_extension_directory_exists() -> None:
    """VS Code extension directory must exist at extensions/vscode/."""
    assert VSCODE_EXT_DIR.exists() and VSCODE_EXT_DIR.is_dir(), (
        "extensions/vscode/ must exist; WL-117 extension should be scaffolded"
    )


def test_vscode_package_json_exists() -> None:
    """extensions/vscode/package.json must exist."""
    pkg = VSCODE_EXT_DIR / "package.json"
    assert pkg.exists(), "extensions/vscode/package.json must exist"


def test_vscode_package_json_has_correct_name() -> None:
    """extensions/vscode/package.json must name the extension 'thegent-vscode'."""
    import json

    pkg = VSCODE_EXT_DIR / "package.json"
    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data.get("name") == "thegent-vscode", f"Extension name must be 'thegent-vscode', got: {data.get('name')}"


def test_scaffold_plan_exists() -> None:
    """WL-117 scaffold plan document must exist."""
    assert SCAFFOLD_PLAN.exists(), f"Expected scaffold plan at {SCAFFOLD_PLAN}"


def test_scaffold_plan_references_wl104_unblock() -> None:
    """Scaffold plan must reference WL-104 as the unblock condition."""
    content = SCAFFOLD_PLAN.read_text(encoding="utf-8")
    assert "WL-104" in content, "Scaffold plan must reference WL-104 as unblock condition"


# noqa: PT018
