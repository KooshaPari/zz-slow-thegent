"""Tests for JsonlParser (BKM-10).

Exercises the pure-Python fallback path so tests pass regardless of whether
the thegent-jsonl Rust binary is compiled.

FR-JSONL-001  @trace FR-JSONL-001
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import orjson as json

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from thegent.native.jsonl_parser import (
    JsonlParser,
    _find_binary,
    _py_count,
    _py_filter,
    _py_sample,
    _py_stream,
    _run_binary_count,
    _run_binary_lines,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(lines: list[dict | str], tmp_dir: Path) -> Path:
    """Write a JSONL file to *tmp_dir* and return its path."""
    p = tmp_dir / "test.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for line in lines:
            if isinstance(line, dict):
                fh.write(json.dumps(line).decode() + "\n")
            else:
                fh.write(line + "\n")  # raw/invalid line
    return p


# ---------------------------------------------------------------------------
# Unit: pure-Python helpers
# ---------------------------------------------------------------------------


class TestPyStream:
    """@trace FR-JSONL-001"""

    def test_stream_valid_records(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"a": 1}, {"b": 2}], tmp_path)
        records = list(_py_stream(p))
        assert len(records) == 2
        assert records[0] == {"a": 1}
        assert records[1] == {"b": 2}

    def test_stream_skips_blank_lines(self, tmp_path: Path) -> None:
        p = tmp_path / "f.jsonl"
        p.write_text('\n{"x":1}\n\n{"y":2}\n', encoding="utf-8")
        records = list(_py_stream(p))
        assert len(records) == 2

    def test_stream_skips_invalid_json(self, tmp_path: Path) -> None:
        p = _write_jsonl(["not_json", {"ok": True}], tmp_path)
        records = list(_py_stream(p))
        # invalid line is skipped; only the valid dict is yielded
        assert len(records) == 1
        assert records[0] == {"ok": True}

    def test_stream_skips_non_dict_json(self, tmp_path: Path) -> None:
        # JSON arrays and scalars at top-level are not dicts — skip them
        p = tmp_path / "f.jsonl"
        p.write_text('[1,2,3]\n{"k":"v"}\n42\n', encoding="utf-8")
        records = list(_py_stream(p))
        assert len(records) == 1
        assert records[0] == {"k": "v"}

    def test_stream_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        records = list(_py_stream(p))
        assert records == []

    def test_stream_unicode_values(self, tmp_path: Path) -> None:
        data = {"emoji": "\U0001f600", "text": "日本語"}
        p = _write_jsonl([data], tmp_path)
        records = list(_py_stream(p))
        assert records[0] == data


class TestPyCount:
    """@trace FR-JSONL-001"""

    def test_count_valid_file(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"a": 1}, {"b": 2}, {"c": 3}], tmp_path)
        assert _py_count(p) == 3

    def test_count_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        assert _py_count(p) == 0

    def test_count_with_blank_lines(self, tmp_path: Path) -> None:
        p = tmp_path / "f.jsonl"
        p.write_text('\n{"a":1}\n\n{"b":2}\n\n', encoding="utf-8")
        assert _py_count(p) == 2

    def test_count_includes_invalid_json_lines(self, tmp_path: Path) -> None:
        # count counts non-blank lines regardless of validity
        p = _write_jsonl(["bad_json", {"ok": True}], tmp_path)
        assert _py_count(p) == 2


class TestPyFilter:
    """@trace FR-JSONL-001"""

    def test_filter_matches_key_value(self, tmp_path: Path) -> None:
        p = _write_jsonl(
            [{"type": "error", "msg": "oops"}, {"type": "info", "msg": "ok"}],
            tmp_path,
        )
        results = list(_py_filter(p, "type", "error"))
        assert len(results) == 1
        assert results[0]["type"] == "error"

    def test_filter_no_match(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"type": "info"}, {"type": "debug"}], tmp_path)
        results = list(_py_filter(p, "type", "error"))
        assert results == []

    def test_filter_multiple_matches(self, tmp_path: Path) -> None:
        p = _write_jsonl(
            [
                {"level": "warn", "n": 1},
                {"level": "info", "n": 2},
                {"level": "warn", "n": 3},
            ],
            tmp_path,
        )
        results = list(_py_filter(p, "level", "warn"))
        assert len(results) == 2
        assert all(r["level"] == "warn" for r in results)

    def test_filter_missing_key_skipped(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"x": 1}, {"y": 2}], tmp_path)
        results = list(_py_filter(p, "type", "error"))
        assert results == []


class TestPySample:
    """@trace FR-JSONL-001"""

    def test_sample_returns_n_records(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"n": i} for i in range(10)], tmp_path)
        sample = _py_sample(p, 3)
        assert len(sample) == 3
        assert sample[0] == {"n": 0}
        assert sample[2] == {"n": 2}

    def test_sample_fewer_than_n(self, tmp_path: Path) -> None:
        p = _write_jsonl([{"n": 1}], tmp_path)
        sample = _py_sample(p, 100)
        assert len(sample) == 1

    def test_sample_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        sample = _py_sample(p, 5)
        assert sample == []


# ---------------------------------------------------------------------------
# Unit: JsonlParser public API (Python fallback forced via mock)
# ---------------------------------------------------------------------------


class TestJsonlParserFallback:
    """Verify JsonlParser works with binary absent.

    @trace FR-JSONL-001
    """

    @pytest.fixture
    def parser(self) -> JsonlParser:
        return JsonlParser()

    @pytest.fixture
    def no_binary(self):
        """Force Python fallback by patching binary discovery to None."""
        with patch("thegent.native.jsonl_parser._find_binary", return_value=None):
            yield

    def test_stream_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"a": 1}, {"b": 2}], tmp_path)
        records = list(parser.stream(p))
        assert len(records) == 2

    def test_count_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"a": 1}, {"b": 2}, {"c": 3}], tmp_path)
        assert parser.count(p) == 3

    def test_filter_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"t": "a"}, {"t": "b"}, {"t": "a"}], tmp_path)
        results = list(parser.filter(p, "t", "a"))
        assert len(results) == 2

    def test_sample_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"n": i} for i in range(5)], tmp_path)
        sample = parser.sample(p, 2)
        assert len(sample) == 2

    def test_stream_empty_file_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        records = list(parser.stream(p))
        assert records == []

    def test_count_empty_file_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        assert parser.count(p) == 0

    def test_sample_returns_list(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"k": "v"}], tmp_path)
        result = parser.sample(p, 10)
        assert isinstance(result, list)

    def test_filter_no_matches_via_fallback(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"type": "info"}], tmp_path)
        results = list(parser.filter(p, "type", "error"))
        assert results == []

    def test_stream_invalid_lines_skipped(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl(["INVALID", {"valid": True}], tmp_path)
        records = list(parser.stream(p))
        assert len(records) == 1
        assert records[0]["valid"] is True

    def test_count_handles_invalid_lines(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        # count counts lines regardless of JSON validity
        p = _write_jsonl(["INVALID", {"valid": True}], tmp_path)
        assert parser.count(p) == 2

    def test_stream_accepts_str_path(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"x": 1}], tmp_path)
        records = list(parser.stream(str(p)))
        assert len(records) == 1

    def test_count_accepts_str_path(self, parser: JsonlParser, no_binary, tmp_path: Path) -> None:
        p = _write_jsonl([{"x": 1}], tmp_path)
        assert parser.count(str(p)) == 1


# ---------------------------------------------------------------------------
# Integration: binary lookup (no binary expected in CI)
# ---------------------------------------------------------------------------


class TestBinaryDiscovery:
    """@trace FR-JSONL-001"""

    def test_find_binary_returns_str_or_none(self) -> None:
        result = _find_binary()
        assert result is None or isinstance(result, str)

    def test_run_binary_count_returns_none_when_no_binary(self, tmp_path: Path) -> None:
        with patch("thegent.native.jsonl_parser._find_binary", return_value=None):
            result = _run_binary_count(tmp_path / "nonexistent.jsonl")
        assert result is None

    def test_run_binary_lines_returns_none_when_no_binary(self) -> None:
        with patch("thegent.native.jsonl_parser._find_binary", return_value=None):
            result = _run_binary_lines(["count", "/tmp/f.jsonl"])
        assert result is None
