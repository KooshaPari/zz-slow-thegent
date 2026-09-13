# @trace WL-131 B90-W3-B2
"""Tests for the WL-131 parity gap report and import-time sanity checks.

Validates:
1. The parity gap report document exists at the expected path.
2. The report mentions 'parity' (confirms it is the right document).
3. The report mentions 'maturin' or 'PyO3' (confirms it addresses the Rust build gap).
4. The existing parity test files can be imported without errors (import-time only).
"""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent / "docs" / "reports" / "2026-02-21-B90-W3-B2-parity-gap-report.md"

PARITY_FILE_1 = Path(__file__).parent / "routing" / "test_wl131_parser_parity.py"

PARITY_FILE_2 = Path(__file__).parent / "routing" / "test_wl131_rust_python_parity.py"


def test_parity_gap_report_exists() -> None:
    """The B90-W3-B2 parity gap report must exist at the expected path."""
    assert REPORT_PATH.exists(), f"Expected parity gap report at {REPORT_PATH}"


def test_parity_gap_report_mentions_parity() -> None:
    """The report must mention 'parity' to confirm it is the right document."""
    content = REPORT_PATH.read_text()
    assert "parity" in content.lower(), "Parity gap report must contain the word 'parity'"


def test_parity_gap_report_mentions_maturin_or_pyo3() -> None:
    """The report must mention 'maturin' or 'PyO3' to address the Rust build gap."""
    content = REPORT_PATH.read_text()
    assert "maturin" in content.lower() or "pyo3" in content.lower(), (
        "Parity gap report must mention 'maturin' or 'PyO3'"
    )


def test_parity_file_1_exists() -> None:
    """The Wave-2 parser parity test file must exist."""
    assert PARITY_FILE_1.exists(), f"Expected parity test file at {PARITY_FILE_1}"


def test_parity_file_2_exists() -> None:
    """The Wave-2 Rust/Python parity test file must exist."""
    assert PARITY_FILE_2.exists(), f"Expected parity test file at {PARITY_FILE_2}"


def test_parity_file_1_importable() -> None:
    """test_wl131_parser_parity.py must be importable without raising at import time."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("test_wl131_parser_parity", str(PARITY_FILE_1))
    assert spec is not None and spec.loader is not None, f"Could not create module spec for {PARITY_FILE_1}"
    module = importlib.util.module_from_spec(spec)
    # Import the module — this must not raise at the module level
    spec.loader.exec_module(module)  # type: ignore[union-attr]


def test_parity_file_2_importable() -> None:
    """test_wl131_rust_python_parity.py must be importable without raising at import time."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("test_wl131_rust_python_parity", str(PARITY_FILE_2))
    assert spec is not None and spec.loader is not None, f"Could not create module spec for {PARITY_FILE_2}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]


# noqa: PT018
