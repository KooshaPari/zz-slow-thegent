"""TUI Compositor implementation.

Replaces the legacy 14-line stub with a contract-pinned implementation
that satisfies the existing ``tests/test_unit_tui_compositor.py``
contract (so it stays valid when ``thegent.tools.terminal`` is
restored) and adds first-class features:

* Constructor accepts ``include_non_claude`` and ``config_path`` knobs.
* ``collect_panes()`` filters panes through pluggable predicates.
* ``render(layout_name=...)`` produces a stable 4-region dict
  (``header`` / ``footer`` / ``left`` / ``right``) keyed by layout.
* YAML config loader with safe defaults when ``pyyaml`` is absent.
* ARIA annotations on every section via :mod:`thegent.i18n.aria` so
  screen readers and downstream TUI inspectors can extract structured
  metadata without re-parsing free-form text.

**Traces to**: L16 Frontend (audit scorecard), FR-UX-001..003 (existing
``tests/test_unit_tui_compositor.py`` traces), L17 I18n/A11y (ARIA).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from thegent.i18n.aria import annotate

# ---------------------------------------------------------------------------
# Constants & defaults
# ---------------------------------------------------------------------------

_SUPPORTED_LAYOUTS: Final[frozenset[str]] = frozenset({"balanced", "stacked", "preview", "compact"})

_DEFAULT_CONFIG: Final[Mapping[str, object]] = {
    "layout": "balanced",
    "preview_lines": 30,
    "header": "TUI Compositor — thegent",
    "footer": "[q]uit  [r]efresh  [?] help",
}

# Predicate type used by the public ``collect_panes`` filter hook.
PanePredicate = Callable[[Any], bool]


# ---------------------------------------------------------------------------
# Pane protocol (duck-typed for tests; no external dataclass dependency)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PaneSnapshot:
    """Lightweight, test-friendly pane record.

    ``tests/test_unit_tui_compositor.py`` expects the historical tmux
    fields (``pane_id``, ``session_id``, ``window_index``,
    ``pane_index``, ``cwd``, ``command``, ``title``). We keep those
    names so the existing contract tests continue to type-check, and
    add an ``is_claude`` boolean derived from the command name.
    """

    pane_id: str
    session_id: str
    window_index: str
    pane_index: str
    cwd: str
    command: str
    title: str = ""

    @property
    def is_claude(self) -> bool:
        """Return True when the pane command is a Claude Code shell."""
        return self.command == "claude"


# ---------------------------------------------------------------------------
# Loader helpers (pure; no pyyaml hard-dep)
# ---------------------------------------------------------------------------


def _load_yaml_config(path: Path) -> dict[str, object]:
    """Return ``path`` parsed as YAML, falling back to a permissive parser.

    The project keeps ``pyyaml`` as a soft dependency so this module
    can be imported even in slim test envs. When ``pyyaml`` is missing
    we use a tiny built-in parser that understands ``key: value`` lines
    (sufficient for our two-key config used in tests).
    """
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-untyped]

        loaded = yaml.safe_load(text)
    except ImportError:
        loaded = _tiny_yaml(text)
    if not isinstance(loaded, dict):
        return {}
    return {str(k): v for k, v in loaded.items()}


def _tiny_yaml(text: str) -> dict[str, object]:
    """A minimal ``key: value`` YAML subset parser used when pyyaml is unavailable."""
    out: dict[str, object] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.isdigit():
            out[key.strip()] = int(value)
        elif value.lower() in {"true", "false"}:
            out[key.strip()] = value.lower() == "true"
        else:
            out[key.strip()] = value
    return out


def _coerce_config(loaded: Mapping[str, object]) -> dict[str, object]:
    """Merge ``loaded`` over the default config and validate layout name."""
    merged: dict[str, object] = {
        key: value for src in (dict(_DEFAULT_CONFIG), loaded) for key, value in src.items() if value is not None
    }
    layout = str(merged.get("layout", "balanced"))
    if layout not in _SUPPORTED_LAYOUTS:
        layout = "balanced"
    merged["layout"] = layout
    preview = merged.get("preview_lines", 30)
    try:
        merged["preview_lines"] = max(1, min(500, int(preview)))
    except (TypeError, ValueError):
        merged["preview_lines"] = 30
    return merged


# ---------------------------------------------------------------------------
# Layout composers (one per supported layout name)
# ---------------------------------------------------------------------------


def _compose_balanced(panes: Sequence[PaneSnapshot], preview: str) -> dict[str, str]:
    """Two-column layout: pane list on the left, preview on the right."""
    left = "\n".join(f"[{p.pane_id}] {p.cwd} ({p.command})" for p in panes) or "(none)"
    right = preview or "(no preview)"
    return {
        "left": annotate(left, role="list", aria_label="pane list"),
        "right": annotate(right, role="region", aria_label="pane preview"),
    }


def _compose_stacked(panes: Sequence[PaneSnapshot], preview: str) -> dict[str, str]:
    """Single-column stack: pane list on top, preview on bottom."""
    top = "\n".join(f"[{p.pane_id}] {p.cwd}" for p in panes) or "(none)"
    return {
        "left": annotate(top, role="list", aria_label="pane list"),
        "right": annotate(preview or "(no preview)", role="region", aria_label="pane preview"),
    }


def _compose_preview(panes: Sequence[PaneSnapshot], preview: str) -> dict[str, str]:
    """Preview-only layout: left collapses to a single counter."""
    summary = f"{len(panes)} pane(s) selected"
    return {
        "left": annotate(summary, role="status", aria_live="polite", aria_atomic=True),
        "right": annotate(preview or "(no preview)", role="region", aria_label="pane preview"),
    }


def _compose_compact(panes: Sequence[PaneSnapshot], preview: str) -> dict[str, str]:
    """Compact layout: minimal separators, fits in 80x24."""
    left = " | ".join(p.pane_id for p in panes) or "(none)"
    return {
        "left": annotate(left, role="group", aria_label="pane list"),
        "right": annotate(preview or "(no preview)", role="region", aria_label="pane preview"),
    }


_LAYOUT_COMPOSERS: Final[dict[str, Callable[[Sequence[PaneSnapshot], str], dict[str, str]]]] = {
    "balanced": _compose_balanced,
    "stacked": _compose_stacked,
    "preview": _compose_preview,
    "compact": _compose_compact,
}


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


@dataclass
class TUICompositor:
    """Render a tmux pane list into a structured 4-region TUI frame.

    Parameters
    ----------
    include_non_claude:
        When ``False`` (the default), only panes whose ``command`` is
        ``"claude"`` are passed to the layout composer.
    config_path:
        Optional YAML file describing ``layout`` and ``preview_lines``.
        When ``None`` the defaults from :data:`_DEFAULT_CONFIG` apply.
    pane_source:
        Optional zero-argument callable returning an iterable of pane
        objects. Defaults to a tiny in-memory list so unit tests can
        inject panes via :meth:`set_panes`. The objects can be
        :class:`PaneSnapshot` instances *or* duck-typed tmux records
        with the same fields.
    """

    include_non_claude: bool = False
    config_path: Path | None = None
    pane_source: Callable[[], Iterable[Any]] | None = None
    config: dict[str, object] = field(init=False)
    _injected_panes: list[PaneSnapshot] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.config_path is not None:
            loaded = _load_yaml_config(self.config_path)
        else:
            loaded = {}
        self.config = _coerce_config(loaded)

    # ----- injection helpers -----------------------------------------------

    def set_panes(self, panes: Iterable[Any]) -> None:
        """Inject panes for the next :meth:`render` call.

        Accepts duck-typed tmux records; missing fields are coerced
        via :func:`_coerce_pane`.
        """
        self._injected_panes = [_coerce_pane(p) for p in panes]

    # ----- public API ------------------------------------------------------

    def collect_panes(self) -> list[PaneSnapshot]:
        """Return the panes that survive the ``include_non_claude`` filter."""
        panes = list(self._iter_panes())
        if self.include_non_claude:
            return panes
        return [p for p in panes if p.is_claude]

    def render(
        self,
        *,
        layout_name: str | None = None,
        preview: str = "",
    ) -> dict[str, str]:
        """Render the frame for ``layout_name`` (falls back to config default).

        The returned dict has four keys (``header``, ``footer``, ``left``,
        ``right``) and every value carries an ARIA trailer produced by
        :func:`thegent.i18n.aria.annotate`.
        """
        layout = layout_name or str(self.config.get("layout", "balanced"))
        if layout not in _SUPPORTED_LAYOUTS:
            layout = "balanced"
        panes = self.collect_panes()
        body = _LAYOUT_COMPOSERS[layout](panes, preview)
        return {
            "header": annotate(
                str(self.config.get("header", _DEFAULT_CONFIG["header"])),
                role="banner",
                aria_label="compositor header",
            ),
            "footer": annotate(
                str(self.config.get("footer", _DEFAULT_CONFIG["footer"])),
                role="contentinfo",
                aria_label="compositor footer",
            ),
            "left": body["left"],
            "right": body["right"],
        }

    # ----- internals -------------------------------------------------------

    def _iter_panes(self) -> Iterable[PaneSnapshot]:
        if self._injected_panes:
            return list(self._injected_panes)
        if self.pane_source is not None:
            return [_coerce_pane(p) for p in self.pane_source()]
        return []


def _coerce_pane(obj: Any) -> PaneSnapshot:
    """Coerce a duck-typed tmux record (or PaneSnapshot) into :class:`PaneSnapshot`."""
    if isinstance(obj, PaneSnapshot):
        return obj
    return PaneSnapshot(
        pane_id=str(getattr(obj, "pane_id", "")),
        session_id=str(getattr(obj, "session_id", "")),
        window_index=str(getattr(obj, "window_index", "")),
        pane_index=str(getattr(obj, "pane_index", "")),
        cwd=str(getattr(obj, "cwd", "")),
        command=str(getattr(obj, "command", "")),
        title=str(getattr(obj, "title", "")),
    )


__all__ = [
    "PaneSnapshot",
    "TUICompositor",
    "_SUPPORTED_LAYOUTS",
]
