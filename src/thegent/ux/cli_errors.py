"""Shared UX helpers for CLI surfaces.

Phase 3/4 hardening lane — AUDIT-9 + F-15 extension: error envelope
parity across all Typer sub-apps (cockpit, sota, govern, phench, etc.).

The two public helpers (:func:`exc_text` and :func:`print_exc`) are
the Rich-markup escape shims that every CLI error envelope in the
repository routes through. This guarantees that user-influenced
data — exception messages, exception values, ``Path`` objects,
arbitrary ``str`` payloads — can never inject Rich markup
(``[red]...[/red]``, ``[bold]...[/bold]``) into an operator terminal.

History:

* AUDIT-9 (Phase 3/4 third-pass): the helper was first introduced as
  ``_exc_text`` inside ``thegent.ux.cli_cockpit`` so the cockpit +
  sota error paths could neutralise bracket markup in user-supplied
  exception messages.
* F-15 (SOTA fifth-pass): the signature was widened from
  ``BaseException`` to ``object`` so non-exception values (``Path``,
  ``str``, ``int``) could route through the same helper without
  requiring a separate ``_escape(str(...))`` wrapper at every
  call site.
* GOV-1 (Phase 3/4 sixteenth+1 lane): the helper is extracted into
  a dedicated module so it can be safely imported from
  ``thegent.cli.apps.govern`` and any future CLI sub-app without
  dragging the full cockpit dependency surface into the root
  ``thegent`` import graph. :func:`print_exc` is added so the
  envelope render path is **safe end-to-end** — pre-escaping the
  string and then routing it through ``Console.print(markup=True)``
  would otherwise let Rich re-interpret the escape sequence and
  re-apply the malicious markup.
* AUDIT-N+3 (Phase 3/4 sweep lane): :func:`safe_echo` is added as
  the typer-echo counterpart to :func:`print_exc`. The helper
  combines ``typer.echo``'s stderr-routing with
  :func:`rich.markup.escape` applied to every interpolated value,
  closing the unsafe ``typer.echo(f"… {untrusted_var}")`` pattern
  in the ``cli/commands/`` + ``cli/apps/run_app.py`` surface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape as _rich_escape

if TYPE_CHECKING:
    from rich.console import Console


def exc_text(value: object) -> str:
    """Return ``value`` as a string with Rich markup escaped.

    AUDIT-9 contract: every CLI error / warning string that
    interpolates user-influenced data MUST route through this
    helper so an attacker cannot inject Rich markup (e.g.
    ``[red]injected[/red]``) into stderr.

    The signature was widened from ``BaseException`` to ``object``
    in F-15 so non-exception values (paths, arbitrary strings,
    format names, etc.) can route through the same helper without
    the dual ``_escape(str(...))`` wrapper at every call site.

    Caveat — callers that route the result through
    ``rich.console.Console.print(markup=True)`` (the default) MUST
    wrap the result in a :class:`rich.text.Text` object first or
    use :func:`print_exc`; otherwise Rich's parser will re-interpret
    the backslash-escape sequence (``\\[red]`` → ``[red]``) and
    re-apply the malicious markup. The cockpit + sota envelopes
    have historically relied on the string-level escape only, but
    :func:`print_exc` now provides the correct end-to-end render
    path for any new envelope site.

    Parameters
    ----------
    value:
        Any Python object. Non-``str`` values are coerced via
        ``str(value)`` before the Rich escape is applied.

    Returns
    -------
    str
        The escaped string, safe to interpolate into a
        ``rich.text.Text.append(...)`` call without re-interpretation.
    """
    return _rich_escape(str(value))


def print_exc(
    console: Console,
    prefix: str,
    value: object,
    *,
    style: str = "red",
) -> None:
    """Render a CLI error envelope safely end-to-end.

    This is the canonical render helper for every ``[red]X
    failed:[/red] <detail>`` envelope in the repository. The
    envelope is assembled as a :class:`rich.text.Text` object so the
    user-influenced ``value`` is treated as **literal text** rather
    than as Rich markup — preventing an attacker from injecting
    colour tags (e.g. ``[red]pwned[/red]``) into an operator
    terminal.

    Why not just ``console.print(f"[red]{prefix}[/red]
    {exc_text(exc)}")``? Because ``rich.markup.escape`` returns
    ``\\[red]boom\\[/red]``, and ``Console.print(markup=True)`` (the
    default) will re-interpret the ``\\`` as an escape for ``[`` and
    re-apply the markup — undoing the escape. The
    :class:`rich.text.Text` assembly path bypasses the parser
    entirely for the user-data section, so the escape is effective
    end-to-end.

    Parameters
    ----------
    console:
        The Rich ``Console`` (typically ``err_console`` for stderr)
        to render the envelope onto.
    prefix:
        The prefix label (e.g. ``"govern approve failed:"``) — this
        is rendered as a styled segment so legitimate markup is
        applied.
    value:
        The user-influenced detail. Any Python object is coerced
        via ``str(value)`` and Rich-markup-escaped before render.
    style:
        The Rich style applied to ``prefix`` (defaults to ``"red"``).
        The user-data section is appended as literal text without
        any styling.
    """
    from rich.text import Text

    line = Text()
    line.append(prefix, style=style)
    line.append(" ")
    line.append(exc_text(value))
    console.print(line)


def safe_echo(*values: object, err: bool = False, **kwargs: object) -> None:
    """AUDIT-N+3 — echo through typer/click with Rich-markup-safe coercion.

    Combines ``typer.echo``'s ``err=True`` (stderr) routing with
    :func:`rich.markup.escape` applied to every interpolated value so a
    malicious or buggy payload containing Rich markup (``[red]…[/red]``,
    ``[bold]…[/bold]``, etc.) cannot inject colour tags into the
    operator's terminal.

    Parameters
    ----------
    *values:
        Positional values to render. Each value is coerced to ``str``
        and Rich-markup-escaped via :func:`exc_text`. No legitimate
        Rich markup passes through — this helper is for error/warning
        envelopes, not styled success output.
    err:
        When ``True``, route through ``typer.echo(..., err=True)`` so
        the envelope appears on stderr (the conventional destination
        for CLI error/warning surfaces).
    **kwargs:
        Forwarded to ``typer.echo``. The ``color`` kwarg is pinned
        to ``False`` so the rendered output is plain text.

    Notes
    -----
    Why pin ``color=False``? ``typer.echo`` uses click's styler
    which can re-introduce ANSI sequences on operator terminals
    that enable colour. By pinning ``color=False`` we force the
    literal-escaped string to reach the terminal unchanged — the
    same end-to-end render-safety contract :func:`print_exc`
    provides through :class:`rich.text.Text` assembly.
    """
    import typer

    kwargs.setdefault("color", False)
    kwargs["err"] = err
    rendered = " ".join(exc_text(v) for v in values)
    typer.echo(rendered, **kwargs)


__all__ = ["exc_text", "print_exc", "safe_echo"]
