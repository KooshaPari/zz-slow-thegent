"""Ensures specs.py uses dynamic paths, not hardcoded user paths.
@trace FR-SPECS-001
"""


import pytest


@pytest.mark.unit
def test_specs_no_hardcoded_user_path():
    """specs.py must not contain hardcoded /Users/ paths."""
    # We need to import the specs command module
    from pathlib import Path

    specs_path = Path(__file__).parent.parent.parent / "cli" / "commands" / "specs.py"
    with open(specs_path) as f:
        src_code = f.read()

    hardcoded = [
        line.strip()
        for i, line in enumerate(src_code.split("\n"), 1)
        if "/Users/" in line and not line.strip().startswith("#")
    ]
    assert hardcoded == [], f"Hardcoded paths found: {hardcoded}"
