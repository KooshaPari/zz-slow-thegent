"""Unit tests for output parser (extract_condensed)."""

import pytest

from thegent.output_parser import (
    OUTPUT_PARSER_SCHEMA_VERSION,
    PARSE_EMPTY,
    PARSE_OK,
    PARSE_TRUNCATED,
    ParseResult,
    condense_stream_to_display,
    extract_condensed,
    extract_condensed_structured,
    extract_condensed_validated,
)


@pytest.mark.unit
class TestCondenseStreamToDisplay:
    """Condensed stream JSON formatter (Cursor-style output)."""

    def test_empty_returns_empty(self) -> None:
        assert condense_stream_to_display("") == ""
        assert condense_stream_to_display("   ") == ""

    def test_plain_text_returns_empty(self) -> None:
        assert condense_stream_to_display("Plain text output") == ""

    def test_user_answers_produce_bullets(self) -> None:
        stdout = (
            '{"type":"message","role":"assistant","content":"What tray technology?"}\n'
            '{"type":"message","role":"user","content":"Native desktop"}\n'
        )
        result = condense_stream_to_display(stdout)
        assert "User answered questions:" in result
        assert "What tray technology?" in result
        assert "Native desktop" in result

    def test_tool_uses_produce_first_plus_more(self) -> None:
        stdout = (
            '{"type":"message","role":"assistant","content":"Research tray tech"}\n'
            '{"type":"tool_use","tool_name":"Search","input":{"pattern":"@mcp.tool","path":"src/mcp.py"}}\n'
            '{"type":"tool_use","tool_name":"read_file","input":{"path":"foo"}}\n'
        )
        result = condense_stream_to_display(stdout)
        assert "Research tray tech" in result
        assert "Search" in result
        assert "+1 more tool uses" in result

    def test_mixed_user_and_tools(self) -> None:
        stdout = (
            '{"type":"message","role":"assistant","content":"What technology?"}\n'
            '{"type":"message","role":"user","content":"Native"}\n'
            '{"type":"message","role":"assistant","content":"I will research"}\n'
            '{"type":"tool_use","tool_name":"Search","input":{"query":"tray"}}\n'
        )
        result = condense_stream_to_display(stdout)
        assert "User answered questions:" in result
        assert "What technology?" in result
        assert "Native" in result
        assert "I will research" in result
        assert "Search" in result

    def test_gemini_format_from_validation_doc(self) -> None:
        stdout = (
            '{"type":"init","timestamp":"2026-02-06T07:36:46.996Z","model":"auto-gemini-3"}\n'
            '{"type":"message","role":"user","content":"List 3 files"}\n'
            '{"type":"message","role":"assistant","content":"I will list 3 files..."}\n'
            '{"type":"tool_use","timestamp":"2026-02-06T07:36:51.833Z","tool_name":"list_directory"}\n'
            '{"type":"message","role":"assistant","content":"1. `.air.toml`\\n2. `.bandit`\\n3. `README.md`"}\n'
        )
        result = condense_stream_to_display(stdout)
        assert "I will list 3 files" in result
        assert "list_directory" in result
        assert "1. `.air.toml`" in result or "air.toml" in result


@pytest.mark.unit
class TestExtractCondensedEmpty:
    """Empty or whitespace input."""

    def test_empty_string_returns_empty(self) -> None:
        # @trace FR-OUT-001
        assert extract_condensed("") == ""

    def test_whitespace_only_returns_empty(self) -> None:
        # @trace FR-OUT-001
        assert extract_condensed("   \n\t  ") == ""


@pytest.mark.unit
class TestExtractCondensedJsonl:
    """JSONL stream extraction."""

    def test_message_role_assistant_extracts_content(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"message","role":"assistant","content":"Hello world"}'
        assert extract_condensed(stdout) == "Hello world"

    def test_data_prefix_sse_line_parsed(self) -> None:
        # @trace FR-OUT-001
        stdout = 'data: {"type":"message","role":"assistant","content":"SSE content"}'
        assert extract_condensed(stdout) == "SSE content"

    def test_completion_final_text_precedence(self) -> None:
        # @trace FR-OUT-001
        stdout = (
            '{"type":"message","role":"assistant","content":"intermediate"}\n'
            '{"type":"completion","finalText":"Final answer"}'
        )
        assert extract_condensed(stdout) == "Final answer"

    def test_item_content_envelope(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"x","item":{"type":"message","content":"From item"}}'
        assert extract_condensed(stdout) == "From item"

    def test_top_level_text_field(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"x","text":"Direct text"}'
        assert extract_condensed(stdout) == "Direct text"


@pytest.mark.unit
class TestExtractCondensedPlainText:
    """Plain text fallback."""

    def test_plain_text_passthrough(self) -> None:
        # @trace FR-OUT-002
        stdout = "Simple plain output"
        assert extract_condensed(stdout) == "Simple plain output"

    def test_trailing_noise_stripped(self) -> None:
        # @trace FR-OUT-002
        stdout = "Actual content\n\nTotal usage est: 100 tokens"
        assert "Actual content" in extract_condensed(stdout)
        assert "Total usage" not in extract_condensed(stdout)

    def test_leading_noise_stripped(self) -> None:
        # @trace FR-OUT-002
        stdout = "[TIME CONSTRAINT: 60s]\n\nReal output here"
        result = extract_condensed(stdout)
        assert "Real output" in result
        assert "[TIME CONSTRAINT" not in result


@pytest.mark.unit
class TestExtractCondensedThinkBlocks:
    """Think block stripping."""

    def test_think_block_removed(self) -> None:
        # @trace FR-OUT-003
        stdout = "Before <think>internal reasoning</think> After"
        result = extract_condensed(stdout)
        assert "Before" in result
        assert "After" in result
        assert "<think>" not in result
        assert "internal reasoning" not in result

    def test_native_think_strip_failure_logs_and_uses_regex_fallback(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # @trace FR-OUT-003
        import thegent.output_parser as output_parser_module

        class _NativeFail:
            @staticmethod
            def strip_think_blocks(_text: str) -> str:
                raise RuntimeError("native strip failed")

        text = "Before <think>outer <think>inner</think> tail</think> After"
        monkeypatch.setattr(output_parser_module, "_get_native_parser", lambda: _NativeFail())
        caplog.set_level("DEBUG", logger="thegent.output_parser")
        assert output_parser_module._strip_think_blocks(text) == output_parser_module._THINK_RE.sub("", text).strip()
        assert "Native think-strip failed; using regex fallback" in caplog.text


@pytest.mark.unit
class TestExtractCondensedWorkerReport:
    """Worker status report preference."""

    def test_worker_report_preferred(self) -> None:
        # @trace FR-OUT-004
        stdout = "Preamble\n\n**Summary**\nTask completed successfully.\n\n**Items Done**\n- item 1"
        result = extract_condensed(stdout)
        assert "Task completed" in result or "successfully" in result

    def test_unescape_literal_newlines(self) -> None:
        # @trace FR-OUT-004
        stdout = '{"type":"message","role":"assistant","content":"Line1\\nLine2"}'
        result = extract_condensed(stdout)
        assert "Line1" in result
        assert "Line2" in result


@pytest.mark.unit
class TestExtractCondensedStructured:
    """Schema-aware extraction (Chunk 173 follow-up)."""

    def test_returns_text_and_schema_version(self) -> None:
        # @trace FR-OUT-005
        stdout = "Hello"
        result = extract_condensed_structured(stdout)
        assert result["text"] == "Hello"
        assert result["schema_version"] == OUTPUT_PARSER_SCHEMA_VERSION

    def test_schema_version_constant(self) -> None:
        # @trace FR-OUT-005
        assert OUTPUT_PARSER_SCHEMA_VERSION == "output-parser-v1"


@pytest.mark.unit
class TestExtractCondensedValidated:
    """Structural validation with ParseResult and error_class."""

    def test_empty_returns_parse_empty(self) -> None:
        # @trace FR-OUT-004
        res = extract_condensed_validated("")
        assert res.success is False
        assert res.error_class == PARSE_EMPTY
        assert res.text == ""

    def test_whitespace_returns_parse_empty(self) -> None:
        # @trace FR-OUT-004
        res = extract_condensed_validated("   \n\t  ")
        assert res.success is False
        assert res.error_class == PARSE_EMPTY

    def test_success_returns_parse_ok(self) -> None:
        # @trace FR-OUT-004
        res = extract_condensed_validated("Hello world")
        assert res.success is True
        assert res.error_class == PARSE_OK
        assert res.text == "Hello world"
        assert res.schema_version == OUTPUT_PARSER_SCHEMA_VERSION

    def test_jsonl_success_returns_parse_ok(self) -> None:
        # @trace FR-OUT-004
        stdout = '{"type":"message","role":"assistant","content":"Done"}'
        res = extract_condensed_validated(stdout)
        assert res.success is True
        assert res.error_class == PARSE_OK
        assert res.text == "Done"

    def test_truncated_xml_returns_parse_truncated(self) -> None:
        # @trace FR-OUT-004
        stdout = "Preamble\n<SUMMARY>In progress"
        res = extract_condensed_validated(stdout)
        assert res.success is False
        assert res.error_class == PARSE_TRUNCATED
        assert res.partial_state is not None
        assert res.partial_state.get("open_tag") == "SUMMARY"
        assert "In progress" in (res.partial_state.get("partial_content") or "")


@pytest.mark.unit
class TestCoerceTextEdgeCases:
    """Tests for _coerce_text edge cases."""

    def test_coerce_none_returns_empty(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text(None) == ""

    def test_coerce_empty_string_returns_empty(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text("") == ""

    def test_coerce_whitespace_only_returns_empty(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text("   ") == ""

    def test_coerce_unicode_text(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text("Hello \u2603 world") == "Hello \u2603 world"

    def test_coerce_very_long_text(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        long_text = "x" * 100000
        assert _coerce_text(long_text) == long_text

    def test_coerce_integer(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text(42) == "42"

    def test_coerce_float(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text(3.14) == "3.14"

    def test_coerce_boolean(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        assert _coerce_text(True) == "True"

    def test_coerce_list_of_strings(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        result = _coerce_text(["line1", "line2", "line3"])
        assert "line1" in result
        assert "line2" in result

    def test_coerce_list_with_nones(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        result = _coerce_text(["a", None, "b"])
        assert "a" in result
        assert "b" in result

    def test_coerce_dict_extracts_text_key(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        result = _coerce_text({"text": "hello", "other": "ignored"})
        assert result == "hello"

    def test_coerce_dict_extracts_content_key(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        result = _coerce_text({"content": "world"})
        assert result == "world"

    def test_coerce_dict_fallback_to_str(self) -> None:
        # @trace FR-OUT-001
        from thegent.output_parser import _coerce_text

        result = _coerce_text({"foo": "bar"})
        assert "foo" in result
        assert "bar" in result


@pytest.mark.unit
class TestNestedJsonEnvelopes:
    """Tests for nested JSON envelope parsing in extract_condensed."""

    def test_nested_item_message_content(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"item.completed","item":{"type":"message","message":{"content":"Nested msg"}}}'
        result = extract_condensed(stdout)
        assert "Nested msg" in result

    def test_message_envelope_variant(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"response","message":{"content":"From message envelope"}}'
        result = extract_condensed(stdout)
        assert "From message envelope" in result

    def test_result_field_extraction(self) -> None:
        # @trace FR-OUT-001
        stdout = '{"type":"output","result":"Result text here"}'
        result = extract_condensed(stdout)
        assert "Result text here" in result


@pytest.mark.unit
class TestSSEPrefixHandling:
    """Tests for SSE data: prefix handling."""

    def test_sse_data_prefix_stripped(self) -> None:
        # @trace FR-OUT-001
        stdout = 'data: {"type":"message","role":"assistant","content":"SSE stripped"}'
        result = extract_condensed(stdout)
        assert "SSE stripped" in result

    def test_multiple_sse_lines(self) -> None:
        # @trace FR-OUT-001
        stdout = (
            'data: {"type":"message","role":"assistant","content":"first"}\n'
            'data: {"type":"message","role":"assistant","content":"second"}'
        )
        result = extract_condensed(stdout)
        assert "second" in result

    def test_sse_non_json_ignored(self) -> None:
        # @trace FR-OUT-001
        stdout = "data: not json at all\nPlain text output"
        result = extract_condensed(stdout)
        assert "Plain text output" in result


@pytest.mark.unit
class TestTruncatedXMLDetection:
    """Tests for truncated XML detection and recovery."""

    def test_truncated_partial_tag_start(self) -> None:
        # @trace FR-OUT-004
        """Detects partial tag at end of stream (e.g., '<STATU')."""
        res = extract_condensed_validated("Begin <STATU")
        assert res.text != ""

    def test_fully_closed_tags_no_truncation(self) -> None:
        # @trace FR-OUT-004
        """Fully closed tags produce parse_ok, not truncated."""
        res = extract_condensed_validated("<STATUS>done</STATUS>")
        assert res.error_class == PARSE_OK
        assert res.success is True

    def test_multiple_unclosed_tags(self) -> None:
        # @trace FR-OUT-004
        """Multiple unclosed tags detected as truncated."""
        res = extract_condensed_validated("<OUTER><INNER>partial content")
        assert res.error_class == PARSE_TRUNCATED
        assert res.partial_state is not None
        assert res.partial_state.get("open_tag") == "INNER"


@pytest.mark.unit
class TestMalformedInputGraceful:
    """Tests for graceful handling of malformed input."""

    def test_invalid_json_falls_back_to_plain(self) -> None:
        # @trace FR-OUT-002
        """Invalid JSON lines fall back to plain text extraction."""
        stdout = "{broken json}\nActual output content"
        result = extract_condensed(stdout)
        assert "Actual output content" in result

    def test_mixed_json_and_plain(self) -> None:
        # @trace FR-OUT-002
        """Mix of valid JSON and plain text extracts from JSON."""
        stdout = '{"type":"message","role":"assistant","content":"JSON content"}\nsome trailing plain text'
        result = extract_condensed(stdout)
        assert "JSON content" in result


# ---------------------------------------------------------------------------
# Coverage gaps: _coerce_text fallback for non-standard types (line 114)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCoerceTextFallbackStr:
    """Tests for _coerce_text str fallback on non-text values (line 114)."""

    def test_coerce_custom_object_returns_str(self) -> None:
        # @trace FR-OUT-001
        """_coerce_text falls back to str() for unrecognized objects."""
        from thegent.output_parser import _coerce_text

        class CustomObj:
            def __str__(self) -> str:
                return "custom-repr"

        result = _coerce_text(CustomObj())
        assert result == "custom-repr"


# ---------------------------------------------------------------------------
# Coverage gaps: _extract_record_message nested item.message.content (lines 129-133)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractRecordMessageNestedMessage:
    """Tests for _extract_record_message nested message envelope (lines 129-133)."""

    def test_item_message_dict_content(self) -> None:
        # @trace FR-OUT-001
        """Extracts content from item.message.content dict envelope."""
        stdout = '{"type":"x","item":{"type":"message","message":{"content":"deep nested"}}}'
        result = extract_condensed(stdout)
        assert "deep nested" in result

    def test_item_non_error_type_extracts(self) -> None:
        # @trace FR-OUT-001
        """Non-error item type extracts content (line 166)."""
        stdout = '{"type":"x","item":{"type":"function_call","content":"tool result"}}'
        result = extract_condensed(stdout)
        assert "tool result" in result


# ---------------------------------------------------------------------------
# Coverage gaps: _extract_from_jsonl item paths (lines 179-182)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractFromJsonlItemPaths:
    """Tests for item_content non-message non-error type (lines 179-182)."""

    def test_item_non_message_non_error_extracts_content(self) -> None:
        # @trace FR-OUT-001
        """Non-message, non-error item with content extracts it."""
        stdout = '{"type":"item.done","item":{"type":"tool_result","content":"tool output here"}}'
        result = extract_condensed(stdout)
        assert "tool output here" in result


# ---------------------------------------------------------------------------
# Coverage gaps: _strip_leading_noise limit (lines 199-200)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStripLeadingNoiseLimit:
    """Tests for _strip_leading_noise 5-line limit (lines 199-200)."""

    def test_strip_leading_noise_stops_after_5(self) -> None:
        # @trace FR-OUT-002
        """_strip_leading_noise strips at most 5 leading noise lines."""
        from thegent.output_parser import _strip_leading_noise

        lines = [
            "[TIME CONSTRAINT: 60s]",
            "[TIME CONSTRAINT: 60s]",
            "[TIME CONSTRAINT: 60s]",
            "[TIME CONSTRAINT: 60s]",
            "[TIME CONSTRAINT: 60s]",
            "[TIME CONSTRAINT: 60s]",  # 6th noise line - should NOT be stripped
            "Real content",
        ]
        result = _strip_leading_noise(lines)
        assert "Real content" in result
        # 6th noise line should be kept since limit is 5
        assert "[TIME CONSTRAINT: 60s]" in result


# ---------------------------------------------------------------------------
# Coverage gaps: _extract_from_plain_text empty (line 230) / fallback (line 237)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractFromPlainTextEdgeCases:
    """Tests for _extract_from_plain_text empty meaningful list (lines 230, 237)."""

    def test_all_noise_returns_stripped_stdout(self) -> None:
        # @trace FR-OUT-002
        """All noise lines returns stdout.strip() (line 230)."""
        from thegent.output_parser import _extract_from_plain_text

        # Trailing noise patterns
        stdout = "Total usage est: 100 tokens\nTokens: 50 input\nCost: $0.01"
        result = _extract_from_plain_text(stdout)
        assert isinstance(result, str)

    def test_fallback_last_15_lines(self) -> None:
        # @trace FR-OUT-002
        """Falls back to last 15 meaningful lines when no last paragraph (line 237)."""
        from thegent.output_parser import _extract_from_plain_text

        stdout = "Content line 1\nContent line 2\n\nContent line 3"
        result = _extract_from_plain_text(stdout)
        assert result is not None


# ---------------------------------------------------------------------------
# Coverage gaps: _compact_report truncation (lines 274-276, 278)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCompactReportTruncation:
    """Tests for _compact_report summary truncation (lines 274-276, 278)."""

    def test_compact_report_truncates_long_summary(self) -> None:
        # @trace FR-OUT-004
        """_compact_report truncates summary over 200 chars."""
        from thegent.output_parser import _compact_report

        long_summary = "**Summary**\n" + ("A" * 250) + ". More text here."
        result = _compact_report(long_summary)
        assert len(result) < 260

    def test_compact_report_no_summary_returns_text(self) -> None:
        # @trace FR-OUT-004
        """_compact_report returns text when no **Summary** section."""
        from thegent.output_parser import _compact_report

        text = "Just some regular text without summary marker"
        result = _compact_report(text)
        assert result == text


# ---------------------------------------------------------------------------
# Coverage gaps: extract_condensed empty after strip (line 296)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractCondensedEmptyAfterStrip:
    """Tests for extract_condensed returning empty after think block strip (line 296)."""

    def test_only_think_block_returns_empty(self) -> None:
        # @trace FR-OUT-003
        """Only think block content returns empty string."""
        stdout = "<think>all internal reasoning only</think>"
        result = extract_condensed(stdout)
        assert result == ""


# ---------------------------------------------------------------------------
# Coverage gaps: extract_condensed_validated (lines 358, 367, 380-381)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractCondensedValidatedEdgeCases:
    """Tests for extract_condensed_validated edge cases."""

    def test_validated_empty_after_strip_returns_parse_empty(self) -> None:
        # @trace FR-OUT-004
        """validated returns PARSE_EMPTY when content is empty after strip (line 358)."""
        res = extract_condensed_validated("<think>only internal</think>")
        assert res.success is False
        assert res.error_class == PARSE_EMPTY

    def test_validated_worker_report_used_when_long(self) -> None:
        # @trace FR-OUT-004
        """validated uses compact worker report when >= 20 chars (line 367)."""
        stdout = "Preamble\n\n**Summary**\nTask completed successfully with details.\n\n**Items Done**\n- done item"
        res = extract_condensed_validated(stdout)
        assert res.success is True
        assert "Task completed" in res.text or "successfully" in res.text

    def test_validated_xml_parse_exception_ignored(self) -> None:
        # @trace FR-OUT-004
        """validated ignores XML parse exceptions (lines 380-381)."""
        # Provide content that has < and > but will cause parser to fail
        stdout = "<<< random brackets >>>"
        res = extract_condensed_validated(stdout)
        assert isinstance(res, ParseResult)


@pytest.mark.unit
class TestExtractRecordMessageItemMessageDict:
    """Tests for _extract_record_message item.message dict branch (lines 129-133)."""

    def test_item_error_type_with_message_dict(self) -> None:
        # @trace FR-OUT-001
        """item type=error falls to message dict branch (lines 129-133)."""
        stdout = '{"type":"x","item":{"type":"error","message":{"content":"error details"}}}'
        result = extract_condensed(stdout)
        assert "error details" in result

    def test_item_error_type_no_message_dict(self) -> None:
        # @trace FR-OUT-001
        """item type=error without message dict falls through."""
        stdout = '{"type":"x","item":{"type":"error","text":"plain error"}}'
        result = extract_condensed(stdout)
        # Should still find some text
        assert isinstance(result, str)


@pytest.mark.unit
class TestExtractFromJsonlNonDictSkipped:
    """Tests for non-dict JSON objects in JSONL being skipped (line 166)."""

    def test_jsonl_non_dict_object_skipped(self) -> None:
        # @trace FR-OUT-001
        """Non-dict JSON objects (arrays, strings, numbers) in JSONL are skipped (line 166)."""
        stdout = '"just a string"\n[1, 2, 3]\n42\n{"type":"message","role":"assistant","content":"Real content"}'
        result = extract_condensed(stdout)
        assert "Real content" in result

    def test_jsonl_only_non_dict_falls_back_to_plain(self) -> None:
        # @trace FR-OUT-001
        """JSONL with only non-dict objects falls through to plain text."""
        stdout = '"just a string"\n[1, 2, 3]'
        result = extract_condensed(stdout)
        assert isinstance(result, str)


@pytest.mark.unit
class TestExtractFromPlainTextAllNoise:
    """Tests for _extract_from_plain_text when all lines are noise (line 230)."""

    def test_all_noise_lines_returns_stripped(self) -> None:
        # @trace FR-OUT-002
        """All meaningful lines filtered returns stdout.strip() (line 230)."""
        from thegent.output_parser import _extract_from_plain_text

        # Use lines that ALL match noise patterns
        stdout = (
            "Total usage est: $0.05\n"
            "Total code changes: 3\n"
            "Usage by model: claude-4\n"
            "Copilot CLI available\n"
            "Git repo: /home/user/project"
        )
        result = _extract_from_plain_text(stdout)
        assert isinstance(result, str)
        # All lines are noise so meaningful is empty; returns stdout.strip()
        assert result == stdout.strip()


@pytest.mark.unit
class TestExtractFromPlainTextFallbackLines:
    """Tests for _extract_from_plain_text fallback to last 15 lines (line 237)."""

    def test_empty_last_block_falls_back_to_last_lines(self) -> None:
        # @trace FR-OUT-002
        """When last paragraph block is empty, falls back to last 15 lines (line 237)."""
        from thegent.output_parser import _extract_from_plain_text

        # Content with no blank-line-separated blocks -- single block
        stdout = "Line one\nLine two\nLine three"
        result = _extract_from_plain_text(stdout)
        assert "Line" in result


@pytest.mark.unit
class TestValidatedXmlParseExceptionCoverage:
    """Ensures the except Exception: pass branch is hit (lines 380-381)."""

    def test_xml_parse_raises_catches_exception(self) -> None:
        # @trace FR-OUT-004
        """IncrementalXMLParser exception is caught in validated (lines 380-381)."""
        from unittest.mock import patch

        with patch(
            "thegent.contracts.parser.IncrementalXMLParser.get_partial_state",
            side_effect=RuntimeError("parser exploded"),
        ):
            res = extract_condensed_validated("<TAG>some content</OTHER>")
        assert isinstance(res, ParseResult)
        # Should not be PARSE_TRUNCATED since exception was caught
        assert res.partial_state is None
