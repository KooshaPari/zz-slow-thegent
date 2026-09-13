"""Unit tests for thegent.contracts.parser -- IncrementalXMLParser and helpers."""

import pytest

import thegent.contracts.parser as parser_module
from thegent.contracts.parser import (
    IncrementalXMLParser,
    extract_tags,
)


@pytest.mark.unit
class TestIncrementalXMLParserParse:
    """Tests for IncrementalXMLParser.parse()."""

    def test_single_balanced_tag(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        result = parser.parse("<STATUS>completed</STATUS>")
        assert result == {"STATUS": "completed"}

    def test_multiple_balanced_tags(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>completed</STATUS><SUMMARY>All done</SUMMARY>"
        result = parser.parse(text)
        assert result == {"STATUS": "completed", "SUMMARY": "All done"}

    def test_multiline_content(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<SUMMARY>Line 1\nLine 2\nLine 3</SUMMARY>"
        result = parser.parse(text)
        assert result["SUMMARY"] == "Line 1\nLine 2\nLine 3"

    def test_content_is_stripped(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>  completed  </STATUS>"
        result = parser.parse(text)
        assert result["STATUS"] == "completed"

    def test_case_insensitive_default(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        result = parser.parse("<status>ok</status>")
        assert "STATUS" in result
        assert result["STATUS"] == "ok"

    def test_case_sensitive_mode(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser(case_sensitive=True)
        # The regex matches [A-Z0-9_]+ with IGNORECASE disabled in case_sensitive mode,
        # but the character class is uppercase-only, so only uppercase tags match.
        result = parser.parse("<STATUS>ok</STATUS>")
        assert "STATUS" in result
        assert result["STATUS"] == "ok"

    def test_duplicate_tags_last_wins(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>first</STATUS><STATUS>second</STATUS>"
        result = parser.parse(text)
        assert result["STATUS"] == "second"

    def test_allowed_tags_filtering(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser(allowed_tags=["STATUS"])
        text = "<STATUS>ok</STATUS><SUMMARY>text</SUMMARY>"
        result = parser.parse(text)
        assert "STATUS" in result
        assert "SUMMARY" not in result

    def test_allowed_tags_case_insensitive(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser(allowed_tags=["status"])
        text = "<STATUS>ok</STATUS>"
        result = parser.parse(text)
        assert result == {"STATUS": "ok"}

    def test_empty_input(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        result = parser.parse("")
        assert result == {}

    def test_no_tags_in_input(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        result = parser.parse("just some plain text without tags")
        assert result == {}

    def test_nested_text_between_tags(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "Before <STATUS>ok</STATUS> middle <SUMMARY>done</SUMMARY> after"
        result = parser.parse(text)
        assert result == {"STATUS": "ok", "SUMMARY": "done"}

    def test_tag_with_underscores(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<TASK_ID>abc-123</TASK_ID>"
        result = parser.parse(text)
        assert result == {"TASK_ID": "abc-123"}

    def test_tag_with_numeric_suffix(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STEP1>first step</STEP1>"
        result = parser.parse(text)
        assert result == {"STEP1": "first step"}

    def test_empty_tag_content(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS></STATUS>"
        result = parser.parse(text)
        assert result == {"STATUS": ""}

    def test_malformed_unclosed_tag_ignored(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>pending"
        result = parser.parse(text)
        assert result == {}

    def test_mismatched_tags_ignored(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>ok</SUMMARY>"
        result = parser.parse(text)
        assert result == {}


@pytest.mark.unit
class TestIncrementalXMLParserPartialState:
    """Tests for IncrementalXMLParser.get_partial_state()."""

    def test_no_tags_returns_no_truncation(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("plain text")
        assert state["is_truncated"] is False
        assert state["open_tag"] is None

    def test_trailing_incomplete_tag_detected(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("some text <STATU")
        assert state["is_truncated"] is True
        assert state["incomplete_tag"] is not None

    def test_balanced_tags_not_truncated(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>ok</STATUS>")
        assert state["is_truncated"] is False

    def test_unclosed_tag_detected(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>working on it")
        assert state["is_truncated"] is True
        assert state["open_tag"] == "STATUS"

    def test_partial_content_captured(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>partial content here")
        assert state["is_truncated"] is True
        assert "partial content here" in state["partial_content"]

    def test_empty_input(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("")
        assert state["is_truncated"] is False

    def test_nested_complete_and_one_open(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        text = "<STATUS>done</STATUS><SUMMARY>still writing"
        state = parser.get_partial_state(text)
        assert state["is_truncated"] is True
        assert state["open_tag"] == "SUMMARY"

    def test_trailing_angle_bracket_only(self) -> None:
        # @trace FR-CTR-002
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("text <")
        assert state["is_truncated"] is True


@pytest.mark.unit
class TestExtractTags:
    """Tests for the extract_tags helper function."""

    def test_extract_all_tags(self) -> None:
        # @trace FR-CTR-002
        text = "<STATUS>ok</STATUS><SUMMARY>done</SUMMARY>"
        result = extract_tags(text)
        assert result == {"STATUS": "ok", "SUMMARY": "done"}

    def test_extract_specific_tags(self) -> None:
        # @trace FR-CTR-002
        text = "<STATUS>ok</STATUS><SUMMARY>done</SUMMARY>"
        result = extract_tags(text, tags=["STATUS"])
        assert "STATUS" in result
        assert "SUMMARY" not in result

    def test_extract_from_empty_string(self) -> None:
        # @trace FR-CTR-002
        assert extract_tags("") == {}

    def test_extract_tags_prefers_native_parser_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CTR-002
        class _Native:
            @staticmethod
            def extract_xml_tags(text: str, allowed_tags=None, case_sensitive=False):  # noqa: ANN001
                assert text == "<STATUS>ok</STATUS>"
                return {"STATUS": "native-ok"}

        monkeypatch.setattr(parser_module, "_get_native_parser", lambda: _Native())
        assert extract_tags("<STATUS>ok</STATUS>") == {"STATUS": "native-ok"}

    def test_extract_tags_falls_back_when_native_parser_raises(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # @trace FR-CTR-002
        class _NativeFail:
            @staticmethod
            def extract_xml_tags(_text: str, allowed_tags=None, case_sensitive=False):  # noqa: ANN001
                raise RuntimeError("native failure")

        monkeypatch.setattr(parser_module, "_get_native_parser", lambda: _NativeFail())
        caplog.set_level("DEBUG", logger="thegent.contracts.parser")
        text = "<STATUS>ok</STATUS><SUMMARY>done</SUMMARY>"
        assert extract_tags(text) == {"STATUS": "ok", "SUMMARY": "done"}
        assert "Native XML parser failed; falling back to Python parser" in caplog.text


@pytest.mark.unit
class TestPartialStateCaseSensitiveBranch:
    """Tests for get_partial_state case_sensitive=True branch (lines 127-130)."""

    def test_case_sensitive_unclosed_tag_detected(self) -> None:
        # @trace FR-CTR-002
        """case_sensitive=True uses rfind branch for unclosed tag (lines 127-130)."""
        parser = IncrementalXMLParser(case_sensitive=True)
        state = parser.get_partial_state("<STATUS>working on it")
        assert state["is_truncated"] is True
        assert state["open_tag"] == "STATUS"
        assert "working on it" in state["partial_content"]

    def test_case_sensitive_balanced_tags_not_truncated(self) -> None:
        # @trace FR-CTR-002
        """case_sensitive=True balanced tags are not truncated."""
        parser = IncrementalXMLParser(case_sensitive=True)
        state = parser.get_partial_state("<STATUS>done</STATUS>")
        assert state["is_truncated"] is False

    def test_case_sensitive_multiple_tags_last_open(self) -> None:
        # @trace FR-CTR-002
        """case_sensitive=True detects last open tag when multiple present."""
        parser = IncrementalXMLParser(case_sensitive=True)
        state = parser.get_partial_state("<STATUS>done</STATUS><SUMMARY>partial")
        assert state["is_truncated"] is True
        assert state["open_tag"] == "SUMMARY"
        assert "partial" in state["partial_content"]
