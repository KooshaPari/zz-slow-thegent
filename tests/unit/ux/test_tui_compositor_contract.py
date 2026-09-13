"""TUI Compositor contract tests.

Pins the contract the existing ``tests/test_unit_tui_compositor.py``
expects from :class:`thegent.ux.compositor.TUICompositor` (constructor
kwargs, ``collect_panes`` filter, ``render`` 4-region dict, YAML
config loading) and adds new contract tests for the L16 Frontend
hardening (ARIA trailers, supported layouts, fallback when pyyaml is
missing, predicate injection).

These tests are unit tests and intentionally do not depend on
``thegent.tools.terminal`` (which was removed during the WL-130
restructuring). The legacy contract test suite in
``tests/test_unit_tui_compositor.py`` uses ``pytest.importorskip`` to
silently skip when ``thegent.tools.terminal`` is unavailable; this
suite verifies the compositor itself works without it.

# @trace FR-UX-CONTRACT
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from thegent.ux.compositor import PaneSnapshot, TUICompositor

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def claude_pane() -> PaneSnapshot:
    return PaneSnapshot(
        pane_id="%1",
        session_id="s1",
        window_index="0",
        pane_index="0",
        cwd="/repo/a",
        command="claude",
        title="title-a",
    )


@pytest.fixture
def zsh_pane() -> PaneSnapshot:
    return PaneSnapshot(
        pane_id="%2",
        session_id="s2",
        window_index="0",
        pane_index="1",
        cwd="/repo/b",
        command="zsh",
        title="title-b",
    )


# ---------------------------------------------------------------------------
# Constructor + config
# ---------------------------------------------------------------------------


class TestConstructorAndConfig:
    def test_default_config_when_no_path(self) -> None:
        comp = TUICompositor()
        assert comp.config["layout"] == "balanced"
        assert comp.config["preview_lines"] == 30

    def test_loads_yaml_config_from_path(self, tmp_path: Path) -> None:
        config_path = tmp_path / "tui-config.yaml"
        config_path.write_text(
            "layout: stacked\npreview_lines: 12\n",
            encoding="utf-8",
        )
        comp = TUICompositor(config_path=config_path)
        assert comp.config["layout"] == "stacked"
        assert comp.config["preview_lines"] == 12

    def test_unknown_layout_falls_back_to_balanced(self, tmp_path: Path) -> None:
        config_path = tmp_path / "tui-config.yaml"
        config_path.write_text("layout: totally-bogus\n", encoding="utf-8")
        comp = TUICompositor(config_path=config_path)
        assert comp.config["layout"] == "balanced"

    def test_tiny_yaml_fallback_works_without_pyyaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When pyyaml is missing, the built-in parser still works."""
        import builtins

        real_import = builtins.__import__

        def _import_block(name: str, *args: object, **kwargs: object):  # noqa: ANN401
            if name == "yaml" or name.startswith("yaml."):
                raise ImportError("simulated pyyaml absence")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _import_block)

        config_path = tmp_path / "tui-config.yaml"
        config_path.write_text(
            "layout: preview\npreview_lines: 7\n",
            encoding="utf-8",
        )
        comp = TUICompositor(config_path=config_path)
        assert comp.config["layout"] == "preview"
        assert comp.config["preview_lines"] == 7


# ---------------------------------------------------------------------------
# collect_panes — the include_non_claude filter
# ---------------------------------------------------------------------------


class TestCollectPanes:
    def test_filters_non_claude_by_default(self, claude_pane: PaneSnapshot, zsh_pane: PaneSnapshot) -> None:
        comp = TUICompositor()
        comp.set_panes([claude_pane, zsh_pane])
        selected = comp.collect_panes()
        assert [p.pane_id for p in selected] == ["%1"]

    def test_includes_non_claude_when_requested(self, claude_pane: PaneSnapshot, zsh_pane: PaneSnapshot) -> None:
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([claude_pane, zsh_pane])
        selected = comp.collect_panes()
        assert {p.pane_id for p in selected} == {"%1", "%2"}

    def test_accepts_duck_typed_tmux_records(self) -> None:
        """Real tmux-style objects with field-style access are coerced."""
        raw_pane = SimpleNamespace(
            pane_id="%9",
            session_id="s9",
            window_index="0",
            pane_index="0",
            cwd="/repo/c",
            command="claude",
            title="title-c",
        )
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([raw_pane])
        assert [p.pane_id for p in comp.collect_panes()] == ["%9"]

    def test_empty_when_no_panes(self) -> None:
        comp = TUICompositor()
        assert comp.collect_panes() == []


# ---------------------------------------------------------------------------
# render — the 4-region output contract
# ---------------------------------------------------------------------------


class TestRender:
    def test_renders_balanced_layout_with_preview(self, claude_pane: PaneSnapshot) -> None:
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([claude_pane])
        layout = comp.render(layout_name="balanced", preview="hello world")
        for key in ("header", "footer", "left", "right"):
            assert layout[key], f"region '{key}' was empty"
        assert "hello world" in layout["right"]
        assert "%1" in layout["left"]

    def test_renders_all_supported_layouts(self, claude_pane: PaneSnapshot) -> None:
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([claude_pane])
        for layout_name in ("balanced", "stacked", "preview", "compact"):
            layout = comp.render(layout_name=layout_name, preview="x")
            assert set(layout) == {"header", "footer", "left", "right"}

    def test_unknown_layout_falls_back_to_balanced(self, claude_pane: PaneSnapshot) -> None:
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([claude_pane])
        layout = comp.render(layout_name="totally-bogus", preview="")
        assert "header" in layout
        assert "%1" in layout["left"]

    def test_render_without_panes_still_has_header_footer(self) -> None:
        comp = TUICompositor()
        layout = comp.render()
        assert layout["header"]
        assert layout["footer"]
        assert layout["left"]
        assert layout["right"]


# ---------------------------------------------------------------------------
# ARIA annotations — L17 cross-cut, all rendered regions must have trailers
# ---------------------------------------------------------------------------


class TestARIAOnAllRegions:
    def test_every_region_has_role_attribute(self, claude_pane: PaneSnapshot) -> None:
        comp = TUICompositor(include_non_claude=True)
        comp.set_panes([claude_pane])
        layout = comp.render(layout_name="balanced", preview="preview-text")
        for region, value in layout.items():
            assert "[role=" in value, f"region '{region}' missing ARIA role trailer: {value!r}"


# ---------------------------------------------------------------------------
# Public surface — module-level exports
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_compat_alias_compositor_compose(self) -> None:
        from thegent.ux.compositor import compositor_compose

        assert compositor_compose(["a", None, "b"]) == "a\nb"

    def test_legacy_stub_class_is_real(self) -> None:
        """The previously-stubbed ``TUICompositor`` is now a real dataclass."""
        comp = TUICompositor()
        assert hasattr(comp, "collect_panes")
        assert hasattr(comp, "render")
        assert hasattr(comp, "config")
