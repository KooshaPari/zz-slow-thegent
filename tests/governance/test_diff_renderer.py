"""Tests for DiffPayload, DiffRenderer, and HITLDiffPayload.

@trace FR-HITL-100
"""

from __future__ import annotations

import re

import orjson as json
import pytest

from thegent.governance.diff_renderer import (
    DiffPayload,
    DiffRenderer,
    HITLDiffPayload,
)

# ---------------------------------------------------------------------------
# DiffPayload tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-HITL-100")
class TestDiffPayload:
    """Tests for DiffPayload pydantic model. @trace FR-HITL-100"""

    def test_from_strings_computes_unified_diff(self) -> None:
        before = "line1\nline2\nline3\n"
        after = "line1\nmodified\nline3\n"
        payload = DiffPayload.from_strings(before, after, path="test.py")
        assert "modified" in payload.unified_diff
        assert "-line2" in payload.unified_diff
        assert "+modified" in payload.unified_diff

    def test_from_strings_empty_before(self) -> None:
        payload = DiffPayload.from_strings("", "new content\n", path="new.py")
        assert "+new content" in payload.unified_diff
        assert payload.before == ""
        assert payload.after == "new content\n"

    def test_from_strings_empty_after(self) -> None:
        payload = DiffPayload.from_strings("old content\n", "", path="del.py")
        assert "-old content" in payload.unified_diff
        assert payload.after == ""

    def test_from_strings_identical_no_diff(self) -> None:
        content = "same\ncontent\n"
        payload = DiffPayload.from_strings(content, content, path="same.py")
        assert payload.unified_diff == ""

    def test_from_strings_path_in_diff_header(self) -> None:
        payload = DiffPayload.from_strings("a\n", "b\n", path="src/foo.py")
        assert "src/foo.py" in payload.unified_diff

    def test_diff_payload_is_frozen(self) -> None:
        payload = DiffPayload.from_strings("a\n", "b\n")
        with pytest.raises(Exception):
            payload.before = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DiffRenderer tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-HITL-100")
class TestDiffRenderer:
    """Tests for DiffRenderer static methods. @trace FR-HITL-100"""

    def _make_payload(self) -> DiffPayload:
        before = "alpha\nbeta\ngamma\n"
        after = "alpha\nBETA\ngamma\ndelta\n"
        return DiffPayload.from_strings(before, after, path="render.py")

    def test_render_ansi_additions_green(self) -> None:
        payload = self._make_payload()
        ansi = DiffRenderer.render_ansi(payload)
        # Lines with additions should be rendered in green (\033[32m)
        green_lines = [line for line in ansi.splitlines() if line.startswith("\033[32m")]
        assert len(green_lines) > 0

    def test_render_ansi_deletions_red(self) -> None:
        payload = self._make_payload()
        ansi = DiffRenderer.render_ansi(payload)
        assert "\033[31m" in ansi

    def test_render_ansi_hunk_header_cyan(self) -> None:
        payload = self._make_payload()
        ansi = DiffRenderer.render_ansi(payload)
        assert "\033[36m" in ansi

    def test_render_ansi_unchanged_no_color(self) -> None:
        payload = self._make_payload()
        ansi = DiffRenderer.render_ansi(payload)
        lines = ansi.splitlines()
        # Context lines (starting with space) should not have ANSI escapes
        for line in lines:
            if line.startswith(" "):
                assert "\033[" not in line

    def test_render_ansi_ends_with_reset(self) -> None:
        payload = self._make_payload()
        ansi = DiffRenderer.render_ansi(payload)
        assert ansi.endswith("\033[0m")

    def test_render_plain_no_ansi_codes(self) -> None:
        payload = self._make_payload()
        plain = DiffRenderer.render_plain(payload)
        assert "\033[" not in plain
        assert "---" in plain or "+BETA" in plain

    def test_render_summary_format(self) -> None:
        payload = self._make_payload()
        summary = DiffRenderer.render_summary(payload)
        assert "render.py" in summary
        assert re.search(r"\+\d+", summary)
        assert re.search(r"-\d+", summary)

    def test_render_summary_counts_additions(self) -> None:
        payload = DiffPayload.from_strings("", "a\nb\nc\n", path="add.py")
        summary = DiffRenderer.render_summary(payload)
        assert "+3" in summary

    def test_render_summary_counts_deletions(self) -> None:
        payload = DiffPayload.from_strings("a\nb\n", "", path="del.py")
        summary = DiffRenderer.render_summary(payload)
        assert "-2" in summary


# ---------------------------------------------------------------------------
# HITLDiffPayload tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-HITL-100")
class TestHITLDiffPayload:
    """Tests for HITLDiffPayload pydantic model. @trace FR-HITL-100"""

    def _make_hitl_payload(self) -> HITLDiffPayload:
        diff = DiffPayload.from_strings("old\n", "new\n", path="file.py")
        return HITLDiffPayload(
            approval_id="hitl_abc123",
            diff=diff,
            context={"agent": "test-agent"},
            requested_at_utc="2026-02-20T12:00:00+00:00",
        )

    def test_hitl_diff_payload_fields(self) -> None:
        payload = self._make_hitl_payload()
        assert payload.approval_id == "hitl_abc123"
        assert payload.diff.path == "file.py"
        assert payload.context == {"agent": "test-agent"}
        assert payload.requested_at_utc == "2026-02-20T12:00:00+00:00"

    def test_hitl_diff_payload_is_frozen(self) -> None:
        payload = self._make_hitl_payload()
        with pytest.raises(Exception):
            payload.approval_id = "changed"  # type: ignore[misc]

    def test_hitl_diff_payload_serializable(self) -> None:
        payload = self._make_hitl_payload()
        data = payload.model_dump(mode="json")
        serialized = json.dumps(data).decode()
        assert "hitl_abc123" in serialized
        assert "file.py" in serialized
        # Round-trip
        deserialized = json.loads(serialized)
        restored = HITLDiffPayload(**deserialized)
        assert restored.approval_id == payload.approval_id
        assert restored.diff.path == payload.diff.path
