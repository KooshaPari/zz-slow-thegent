from pathlib import Path

import pytest

# thegent.tools.terminal module was removed.
_terminal = pytest.importorskip(
    "thegent.tools.terminal",
    reason="thegent.tools.terminal module removed; tui compositor tests skipped",
)
from thegent.tools.terminal import (
    TmuxPane,  # noqa: E402  (importorskip may skip before this)
)

from thegent.ux.compositor import TUICompositor


@pytest.mark.unit
def test_compositor_filters_non_claude_panes(monkeypatch):
    # @trace FR-UX-001
    panes = [
        TmuxPane("%1", "s1", "0", "0", "/repo/a", "claude", "title-a"),
        TmuxPane("%2", "s2", "0", "1", "/repo/b", "zsh", "title-b"),
    ]

    monkeypatch.setattr("thegent.ux.compositor.list_tmux_panes", lambda: panes)
    monkeypatch.setattr("thegent.ux.compositor.is_claude_code_pane", lambda pane: pane.command == "claude")

    compositor = TUICompositor(include_non_claude=False)
    selected = compositor.collect_panes()

    assert [pane.pane_id for pane in selected] == ["%1"]


@pytest.mark.unit
def test_compositor_renders_layout_with_preview(monkeypatch):
    # @trace FR-UX-002
    panes = [TmuxPane("%7", "s1", "0", "0", "/repo", "claude", "title")]

    monkeypatch.setattr("thegent.ux.compositor.list_tmux_panes", lambda: panes)
    monkeypatch.setattr("thegent.ux.compositor.is_claude_code_pane", lambda _: True)
    monkeypatch.setattr("thegent.ux.compositor.capture_tmux_pane", lambda pane_id, last_lines=30: f"preview:{pane_id}")

    compositor = TUICompositor(include_non_claude=True)
    layout = compositor.render(layout_name="balanced")

    assert layout["header"] is not None
    assert layout["footer"] is not None
    assert layout["left"] is not None
    assert layout["right"] is not None


@pytest.mark.unit
def test_compositor_loads_yaml_config(tmp_path: Path):
    # @trace FR-UX-003
    config_path = tmp_path / "tui-config.yaml"
    config_path.write_text("layout: stacked\npreview_lines: 12\n", encoding="utf-8")

    compositor = TUICompositor(config_path=config_path)

    assert compositor.config["layout"] == "stacked"
    assert compositor.config["preview_lines"] == 12
