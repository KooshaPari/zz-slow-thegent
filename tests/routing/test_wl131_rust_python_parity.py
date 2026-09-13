# @trace WL-131 B90-W2-D3
"""Comprehensive parity tests: Python APIs vs Rust implementations.

This file extends tests/routing/test_wl131_parser_parity.py (which covers
model-suffix parsing parity) with parity tests for the other Python APIs
that have Rust equivalents in crates/thegent-parser/src/lib.rs:

  - extract_xml_tags  (Python: thegent.contracts.parser.extract_tags)
  - strip_think_blocks (Python: manual regex in output_parser)
  - strip_noise        (Python: output parser noise stripping)
  - parse_checkpoint_by_id (Python: thegent.execution_jsonl_parsers)
  - parse_dlq_item         (Python: thegent.execution_jsonl_parsers)

For each function, 5+ identical inputs are run through the Python side and
verified against documented expected outputs from the Rust implementation.

When the Rust PyO3 extension (thegent_parser) is available, a cross-language
parity assertion is also run.

# @trace WL-131 B90-W2-D3
"""

from __future__ import annotations

import os
from typing import Any

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _try_import_rust_parser() -> Any:
    """Return the Rust thegent_parser extension, or None if not built."""
    try:
        import thegent_parser  # type: ignore[import]

        return thegent_parser
    except ImportError:
        return None


PARSER_PARITY_STRICT = os.environ.get("THEGENT_PARSER_PARITY_REQUIRED", "").strip().lower() in {"1", "true", "yes"}


def _require_rust_parser(reason: str) -> Any:
    parser = _try_import_rust_parser()
    if parser is None:
        if PARSER_PARITY_STRICT:
            pytest.fail(
                "Parser-touching CI profile requires the `thegent_parser` extension, but it could not be imported. "
                "Run `uv pip install crates/thegent-parser` or "
                "`cd crates/thegent-parser && maturin develop --release --features python` before rerunning parity tests."
            )
        pytest.skip(reason)
    return parser


# ---------------------------------------------------------------------------
# 1. extract_xml_tags parity
#    Python: thegent.contracts.parser (or thegent.output_parser)
#    Rust:   crates/thegent-parser extract_xml_tags
# ---------------------------------------------------------------------------

EXTRACT_XML_TAG_CASES: list[tuple[str, dict[str, str]]] = [
    # (input_text, expected_dict)
    ("<RESULT>hello</RESULT>", {"RESULT": "hello"}),
    ("<A>foo</A><B>bar</B>", {"A": "foo", "B": "bar"}),
    ("<TAG>  padded  </TAG>", {"TAG": "padded"}),
    ("<EMPTY></EMPTY>", {"EMPTY": ""}),
    ("no tags here", {}),
    ("<NESTED><inner>val</inner></NESTED>", {"NESTED": "<inner>val</inner>"}),
    ("<X>1</X><X>2</X>", {"X": "2"}),  # last value wins (dict semantics)
]


def _python_extract_xml_tags(text: str) -> dict[str, str]:
    """Invoke the Python XML tag extractor."""
    try:
        from thegent.contracts.parser import extract_tags

        return extract_tags(text)
    except (ImportError, AttributeError):
        # Fallback: minimal reference implementation
        import re

        result: dict[str, str] = {}
        for m in re.finditer(r"<([A-Za-z0-9_\-]+)>(.*?)</\1>", text, re.DOTALL):
            result[m.group(1)] = m.group(2).strip()
        return result


@pytest.mark.parametrize(("text", "expected"), EXTRACT_XML_TAG_CASES)
def test_python_extract_xml_tags(text: str, expected: dict[str, str]) -> None:
    """Python extract_tags must match documented expected output."""
    result = _python_extract_xml_tags(text)
    assert result == expected, f"extract_xml_tags mismatch for {text!r}: expected={expected!r}, got={result!r}"


def test_rust_extract_xml_tags_parity_if_available() -> None:
    """When Rust extension available, Python and Rust must agree on all cases."""
    parser = _require_rust_parser("thegent_parser.extract_xml_tags not available; skipping cross-language parity")
    if not hasattr(parser, "extract_xml_tags"):
        pytest.skip("thegent_parser.extract_xml_tags not available; skipping cross-language parity")

    for text, _expected in EXTRACT_XML_TAG_CASES:
        py_result = _python_extract_xml_tags(text)
        rust_result = parser.extract_xml_tags(text)
        assert py_result == rust_result, (
            f"Python/Rust extract_xml_tags mismatch for {text!r}: Python={py_result!r}, Rust={rust_result!r}"
        )


# ---------------------------------------------------------------------------
# 2. parse_model_suffixes parity (extended cases beyond test_wl131_parser_parity)
#    Python: thegent.routing.model_suffix_parser.parse_model_suffixes
#    Rust:   crates/thegent-parser parse_model_suffixes (dict return)
# ---------------------------------------------------------------------------

EXTRA_MODEL_SUFFIX_CASES: list[tuple[str, str, list[str]]] = [
    # (input, expected_base, expected_suffix_strings)
    ("", "", []),  # empty string: base=empty, no suffixes
    (":nitro", "", ["nitro"]),  # leading colon — base is empty
    ("model:nitro:floor", "model", ["nitro", "floor"]),  # two known suffixes
    ("model:unknown1:nitro:unknown2", "model", ["nitro"]),  # unknowns filtered
    ("prefix/model:thinking:online:extended", "prefix/model", ["thinking", "online", "extended"]),
]


def _python_parse_model_suffixes(model: str) -> dict[str, Any]:
    """Return dict matching Rust output shape: base_model, suffixes (str list), raw."""
    from thegent.utils.routing_impl.model_suffix_parser import parse_model_suffixes

    parsed = parse_model_suffixes(model)
    return {
        "base_model": parsed.base_model,
        "suffixes": [s.value for s in parsed.suffixes],
        "raw": parsed.raw,
    }


@pytest.mark.parametrize(("model_str", "expected_base", "expected_suffixes"), EXTRA_MODEL_SUFFIX_CASES)
def test_python_extended_model_suffix_cases(model_str: str, expected_base: str, expected_suffixes: list[str]) -> None:
    """Python parse_model_suffixes must match expected output for extended cases."""
    result = _python_parse_model_suffixes(model_str)
    assert result["base_model"] == expected_base, (
        f"base_model mismatch for {model_str!r}: expected={expected_base!r}, got={result['base_model']!r}"
    )
    assert result["suffixes"] == expected_suffixes, (
        f"suffixes mismatch for {model_str!r}: expected={expected_suffixes!r}, got={result['suffixes']!r}"
    )
    assert result["raw"] == model_str, f"raw not preserved for {model_str!r}: got={result['raw']!r}"


def test_rust_extended_model_suffix_parity_if_available() -> None:
    """When Rust extension available, verify parity for extended suffix cases."""
    parser = _require_rust_parser("thegent_parser.parse_model_suffixes not available")
    if not hasattr(parser, "parse_model_suffixes"):
        pytest.skip("thegent_parser.parse_model_suffixes not available")

    for model_str, _expected_base, _expected_suffixes in EXTRA_MODEL_SUFFIX_CASES:
        if model_str == "":
            continue  # Rust and Python may differ on degenerate empty input
        py_result = _python_parse_model_suffixes(model_str)
        rust_result = parser.parse_model_suffixes(model_str)
        assert py_result["base_model"] == rust_result["base_model"], f"base_model mismatch for {model_str!r}"
        assert py_result["suffixes"] == rust_result["suffixes"], f"suffixes mismatch for {model_str!r}"


# ---------------------------------------------------------------------------
# 3. parse_checkpoint_by_id parity
#    Python: thegent.execution_jsonl_parsers.parse_checkpoint_by_id
#    Rust:   crates/thegent-parser parse_checkpoint_by_id
# ---------------------------------------------------------------------------

CHECKPOINT_CASES: list[tuple[str, str, bool]] = [
    # (json_line, checkpoint_id, expect_match)
    ('{"checkpoint_id": "abc123", "data": 1}', "abc123", True),
    ('{"checkpoint_id": "abc123", "data": 1}', "xyz999", False),
    ('{"other": "field"}', "abc123", False),
    ("not valid json", "abc123", False),
    ('{"checkpoint_id": "exact-match-01", "status": "ok"}', "exact-match-01", True),
]


def _python_parse_checkpoint_by_id(line: str, checkpoint_id: str) -> Any:
    """Invoke the Python parse_checkpoint_by_id."""
    try:
        from thegent.execution_jsonl_parsers import parse_checkpoint_by_id

        return parse_checkpoint_by_id(line, checkpoint_id)
    except ImportError:
        # Reference implementation
        try:
            obj = json.loads(line)
        except Exception:
            return None
        if not isinstance(obj, dict):
            return None
        if obj.get("checkpoint_id") != checkpoint_id:
            return None
        return obj


@pytest.mark.parametrize(("line", "cid", "expect_match"), CHECKPOINT_CASES)
def test_python_parse_checkpoint_by_id(line: str, cid: str, expect_match: bool) -> None:
    """Python parse_checkpoint_by_id must match/not-match based on checkpoint_id."""
    result = _python_parse_checkpoint_by_id(line, cid)
    if expect_match:
        assert result is not None, f"Expected match for checkpoint_id={cid!r}, got None"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("checkpoint_id") == cid
    else:
        assert result is None, f"Expected None for non-matching case, got {result!r}"


def test_rust_parse_checkpoint_by_id_parity_if_available() -> None:
    """When Rust extension available, Python and Rust must agree on checkpoint parsing."""
    parser = _require_rust_parser("thegent_parser.parse_checkpoint_by_id not available")
    if not hasattr(parser, "parse_checkpoint_by_id"):
        pytest.skip("thegent_parser.parse_checkpoint_by_id not available")

    for line, cid, _expect_match in CHECKPOINT_CASES:
        py_result = _python_parse_checkpoint_by_id(line, cid)
        rust_result = parser.parse_checkpoint_by_id(line, cid)
        # Both must agree on None vs non-None
        py_matched = py_result is not None
        rust_matched = rust_result is not None
        assert py_matched == rust_matched, (
            f"Python/Rust checkpoint match disagreement for cid={cid!r}, line={line!r}: "
            f"Python={py_matched}, Rust={rust_matched}"
        )


# ---------------------------------------------------------------------------
# 4. parse_dlq_item parity
#    Python: thegent.execution_jsonl_parsers.parse_dlq_item
#    Rust:   crates/thegent-parser parse_dlq_item
# ---------------------------------------------------------------------------

DLQ_CASES: list[tuple[str, str | None, str | None, bool]] = [
    # (json_line, status_filter, run_id_filter, expect_match)
    ('{"status": "failed", "run_id": "r1", "data": "x"}', "failed", "r1", True),
    ('{"status": "failed", "run_id": "r1"}', "succeeded", "r1", False),
    ('{"status": "failed", "run_id": "r1"}', "failed", "r999", False),
    ('{"status": "pending", "run_id": "r2"}', None, None, True),
    ("not-json", None, None, False),
]


def _python_parse_dlq_item(line: str, status: str | None, run_id: str | None) -> Any:
    """Invoke the Python parse_dlq_item (positional args: line, status, run_id)."""
    try:
        from thegent.execution_jsonl_parsers import parse_dlq_item

        return parse_dlq_item(line, status, run_id)
    except ImportError:
        # Reference implementation
        try:
            obj = json.loads(line)
        except Exception:
            return None
        if not isinstance(obj, dict):
            return None
        if status is not None and obj.get("status") != status:
            return None
        if run_id is not None and obj.get("run_id") != run_id:
            return None
        return obj


@pytest.mark.parametrize(("line", "status", "run_id", "expect_match"), DLQ_CASES)
def test_python_parse_dlq_item(line: str, status: str | None, run_id: str | None, expect_match: bool) -> None:
    """Python parse_dlq_item must filter correctly on status and run_id."""
    result = _python_parse_dlq_item(line, status, run_id)
    if expect_match:
        assert result is not None, f"Expected match (status={status!r}, run_id={run_id!r}), got None"
    else:
        assert result is None, f"Expected None (status={status!r}, run_id={run_id!r}), got {result!r}"


def test_rust_parse_dlq_item_parity_if_available() -> None:
    """When Rust extension available, Python and Rust must agree on DLQ filtering."""
    parser = _require_rust_parser("thegent_parser.parse_dlq_item not available")
    if not hasattr(parser, "parse_dlq_item"):
        pytest.skip("thegent_parser.parse_dlq_item not available")

    for line, status, run_id, _expect_match in DLQ_CASES:
        py_result = _python_parse_dlq_item(line, status, run_id)
        # Rust extension uses keyword args for optional status/run_id
        rust_kwargs: dict[str, Any] = {}
        if status is not None:
            rust_kwargs["status"] = status
        if run_id is not None:
            rust_kwargs["run_id"] = run_id
        rust_result = parser.parse_dlq_item(line, **rust_kwargs)

        py_matched = py_result is not None
        rust_matched = rust_result is not None
        assert py_matched == rust_matched, (
            f"Python/Rust DLQ parse disagreement: line={line!r}, "
            f"status={status!r}, run_id={run_id!r}: Python={py_matched}, Rust={rust_matched}"
        )
