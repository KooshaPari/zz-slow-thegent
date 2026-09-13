from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from thegent.cli.commands import impl


def test_wrapper_parse_work_stream_md_delegates(tmp_path: Path) -> None:
    work_stream_path = tmp_path / "WORK_STREAM.md"
    expected = {"backlog": [{"id": "WS-1"}], "claimed": {"WS-2"}, "completed": {"WS-3"}}

    with patch(
        "thegent.cli.services.run_workstream_helpers.parse_work_stream_md",
        return_value=expected,
    ) as mock_fn:
        result = impl._parse_work_stream_md(work_stream_path)

    mock_fn.assert_called_once_with(work_stream_path)
    assert result is expected


def test_wrapper_collect_work_stream_items_delegates(tmp_path: Path) -> None:
    work_stream_path = tmp_path / "WORK_STREAM.md"
    expected_items = [{"id": "WS-1", "description": "Do WS-1", "_sort_order": 4}]
    expected_sources = ["WORK_STREAM.md"]

    with patch(
        "thegent.cli.services.run_workstream_helpers.collect_work_stream_items",
        return_value=(expected_items, expected_sources),
    ) as mock_fn:
        result = impl._collect_work_stream_items(work_stream_path, 5)

    mock_fn.assert_called_once_with(work_stream_path, 5)
    assert result == (expected_items, expected_sources)


def test_parse_and_sort_functional_case(tmp_path: Path) -> None:
    work_stream_path = tmp_path / "WORK_STREAM.md"
    work_stream_path.write_text(
        (
            "## BACKLOG\n"
            "| ID | Title | Type | Depends | Notes | Status |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| WS-2 | Implement B | feature | WS-1 | - | PENDING |\n"
            "| WS-1 | Implement A | feature | - | - | PENDING |\n"
            "| WS-3 | Implement C | feature | WS-9 | - | PENDING |\n\n"
            "## COMPLETED\n"
            "| ID | Title | Type | Depends | Notes | Status |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| WS-9 | Foundation | feature | - | - | COMPLETED |\n"
        ),
        encoding="utf-8",
    )

    parsed = impl._parse_work_stream_md(work_stream_path)
    assert [item["id"] for item in parsed["backlog"]] == ["WS-2", "WS-1", "WS-3"]
    assert "WS-9" in parsed["completed"]

    # Functional sort check using parsed rows as input.
    priority_by_id = {"WS-2": "P3", "WS-1": "P1", "WS-3": "P2"}
    ordered = sorted(
        parsed["backlog"],
        key=lambda item: impl._priority_sort_key(priority_by_id[item["id"]]),
    )
    assert [item["id"] for item in ordered] == ["WS-1", "WS-3", "WS-2"]
