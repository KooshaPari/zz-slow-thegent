# @trace WL-131 B90-W2-B2
"""Python-side parity tests for the model suffix parser.

These tests exercise the same 10+ input cases covered by the Rust unit tests
in crates/thegent-parser/src/lib.rs (model_suffix_tests module).

The tests import from the existing Python implementation
(thegent.routing.model_suffix_parser) and verify expected behavior.
When the Rust extension is available via PyO3, the thegent_parser.parse_model_suffixes
wrapper is exercised to confirm cross-language output parity.
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.model_suffix_parser import parse_model_suffixes

# ---------------------------------------------------------------------------
# Parity test cases — mirrors the Rust model_suffix_tests module
# ---------------------------------------------------------------------------

PARITY_CASES: list[tuple[str, str, list[str]]] = [
    # (input, expected_base, expected_suffix_values)
    ("gpt-4o", "gpt-4o", []),
    ("gpt-4o:nitro", "gpt-4o", ["nitro"]),
    ("gpt-4o:floor", "gpt-4o", ["floor"]),
    ("openai/gpt-4o:free", "openai/gpt-4o", ["free"]),
    ("claude-sonnet-4-5:thinking", "claude-sonnet-4-5", ["thinking"]),
    ("gpt-4o:online", "gpt-4o", ["online"]),
    ("claude-opus-4:extended", "claude-opus-4", ["extended"]),
    (
        "anthropic/claude-sonnet-4-5:thinking:online",
        "anthropic/claude-sonnet-4-5",
        ["thinking", "online"],
    ),
    ("model:unknown", "model", []),
    ("anthropic/claude-opus-4", "anthropic/claude-opus-4", []),
    ("gpt-4o:nitro:thinking", "gpt-4o", ["nitro", "thinking"]),
]


@pytest.mark.parametrize(("model_str", "expected_base", "expected_suffixes"), PARITY_CASES)
def test_parse_model_suffixes_base_model(model_str: str, expected_base: str, expected_suffixes: list[str]) -> None:
    """Base model is extracted correctly for all parity cases."""
    del expected_suffixes
    result = parse_model_suffixes(model_str)
    assert result.base_model == expected_base, (
        f"input={model_str!r}: expected base={expected_base!r}, got {result.base_model!r}"
    )


@pytest.mark.parametrize(("model_str", "expected_base", "expected_suffixes"), PARITY_CASES)
def test_parse_model_suffixes_suffix_values(model_str: str, expected_base: str, expected_suffixes: list[str]) -> None:
    """Suffix values are extracted correctly for all parity cases."""
    del expected_base
    result = parse_model_suffixes(model_str)
    actual = [s.value for s in result.suffixes]
    assert actual == expected_suffixes, f"input={model_str!r}: expected suffixes={expected_suffixes!r}, got {actual!r}"


@pytest.mark.parametrize(("model_str", "expected_base", "expected_suffixes"), PARITY_CASES)
def test_parse_model_suffixes_raw_preserved(model_str: str, expected_base: str, expected_suffixes: list[str]) -> None:
    """Raw input string is preserved unchanged."""
    del expected_base, expected_suffixes
    result = parse_model_suffixes(model_str)
    assert result.raw == model_str, f"input={model_str!r}: raw not preserved, got {result.raw!r}"


def test_unknown_suffix_does_not_raise() -> None:
    """An unknown suffix token must not raise — it is silently ignored."""
    result = parse_model_suffixes("model:completelyunknownsuffix")
    assert result.base_model == "model"
    assert result.suffixes == []


def test_has_suffix_false_for_bare_model() -> None:
    result = parse_model_suffixes("gpt-4o")
    assert result.has_suffix is False


def test_has_suffix_true_for_suffixed_model() -> None:
    result = parse_model_suffixes("gpt-4o:nitro")
    assert result.has_suffix is True


def test_is_thinking_property() -> None:
    result = parse_model_suffixes("claude:thinking")
    assert result.is_thinking is True
    result2 = parse_model_suffixes("claude:nitro")
    assert result2.is_thinking is False


def test_is_free_tier_property() -> None:
    result = parse_model_suffixes("openai/gpt-4o:free")
    assert result.is_free_tier is True


def test_is_performance_tier_property() -> None:
    result = parse_model_suffixes("gpt-4o:nitro")
    assert result.is_performance_tier is True


def test_is_economy_tier_property() -> None:
    result = parse_model_suffixes("gpt-4o:floor")
    assert result.is_economy_tier is True


def test_needs_web_search_property() -> None:
    result = parse_model_suffixes("gpt-4o:online")
    assert result.needs_web_search is True


# ---------------------------------------------------------------------------
# Rust extension parity (best-effort — skipped when extension not built)
# ---------------------------------------------------------------------------


def test_rust_extension_parity_if_available() -> None:
    """When the Rust PyO3 extension is available, verify output parity."""
    try:
        import thegent_parser  # type: ignore[import]
    except ImportError:
        pytest.skip("thegent_parser Rust extension not built; skipping cross-language parity")

    if not hasattr(thegent_parser, "parse_model_suffixes"):
        pytest.skip("parse_model_suffixes not exported from Rust extension")

    for model_str, expected_base, expected_suffixes in PARITY_CASES:
        rust_result = thegent_parser.parse_model_suffixes(model_str)
        assert rust_result["base_model"] == expected_base, (
            f"Rust/Python base_model mismatch for {model_str!r}: "
            f"Rust={rust_result['base_model']!r}, Python={expected_base!r}"
        )
        assert rust_result["suffixes"] == expected_suffixes, (
            f"Rust/Python suffixes mismatch for {model_str!r}: "
            f"Rust={rust_result['suffixes']!r}, Python={expected_suffixes!r}"
        )
        assert rust_result["raw"] == model_str, f"Rust raw not preserved for {model_str!r}"
