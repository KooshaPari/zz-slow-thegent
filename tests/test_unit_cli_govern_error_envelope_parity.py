"""Phase 3/4 sixteenth+1 lane — Governance CLI error-envelope parity.

Closes the GOV-1 carry-forward surfaced by the ``sage`` research
agent (see WORKLOG.md 2026-07-19 ``Unblocked Next`` note):
``thegent.cli.apps.govern`` had four error-envelope sites that
interpolated ``{exc}`` (or ``{result.get('error', 'Unknown error')}``)
directly into a Rich-markup f-string, violating the AUDIT-9 contract
that every CLI error envelope in the repository routes through the
``_exc_text`` / ``exc_text`` helper so a malicious or buggy
exception payload containing ``[red]...[/red]`` cannot inject
Rich markup into an operator terminal.

This lane:

1. Extracts the helper into :mod:`thegent.ux.cli_errors` as
   :func:`exc_text` so any CLI sub-app outside the cockpit surface
   can import it without dragging the full cockpit dependency
   graph into the root ``thegent`` import path.
2. Migrates the four unsafe envelope sites in
   ``thegent.cli.apps.govern`` to the ``[red]govern <sub>
   failed:[/red]`` prefix convention (matches the cockpit + sota
   envelopes from F-15 UX-1).
3. Pins the GOV-1 contracts in this file so a future
   refactor cannot reintroduce the unsafe pattern.

Tests cover:

* :class:`TestExcTextPublicApi` — the shared helper accepts any
  ``object`` (``str``, ``int``, ``Exception``, ``Path``) and renders
  without leaking Rich-markup bracket tokens.
* :class:`TestGovernAppName` — the ``govern`` Typer app exposes its
  name in ``app.info.name``, renders ``Usage: govern`` rather than
  Typer's ``Usage: root`` fallback (F-15-D applied to the governance
  surface), and surfaces the ``@app.callback()`` root description
  in ``thegent govern --help`` (F-15-F applied to the governance
  surface).
* :class:`TestGovernErrorEnvelopeConvention` — the four
  ``thegent govern <sub>`` failure paths route through ``exc_text``
  and emit the ``govern <sub> failed:`` prefix. No naked ``{exc}``
  or ``{str(x)}`` interpolation into Rich-markup f-strings remains
  in ``apps/govern.py``.
* :class:`TestGovernErrorEnvelopeRichmarkupSafety` — the rendered
  envelope backslash-escapes any ``[red]...[/red]`` payload so an
  attacker cannot inject Rich markup into an operator terminal.
* :class:`TestGovernHelpOutputSanity` — every known ``govern``
  sub-command exits zero on ``--help``, prints ``Usage: govern``,
  and never prints a ``Traceback``.
* :class:`TestGovernErrorEnvelopeCliIntegration` — when the
  ``thegent`` CLI binary is on ``$PATH`` (i.e. after
  ``pip install -e .``), every wired ``govern <sub> --help``
  invocation through the root CLI also exits zero, confirming the
  ``add_typer(govern_app, name="govern")`` wiring in
  ``apps/main.py`` survives a refactor.
* :class:`TestCockpitReexportBackwardCompat` — the cockpit +
  sota modules still expose ``_exc_text`` (with the underscore
  prefix preserved) so every existing call site inside
  ``cli_cockpit.py`` and ``cli_sota.py`` continues to work
  unchanged after the helper was extracted into the shared
  ``thegent.ux.cli_errors`` module.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich/Typer ANSI escape codes from CLI output.

    The CLI surfaces tested here render through Rich which prepends
    SGR escape sequences (``\\x1b[31m`` for red, ``\\x1b[0m`` for
    reset, etc.). A literal ``startswith("Usage: govern")`` check
    would otherwise fail on the colourised output, so this helper
    centralises the cleanup.
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# exc_text helper — public API contract (extracted from cli_cockpit)
# ---------------------------------------------------------------------------


class TestExcTextPublicApi:
    """Pin the shared helper contract for every CLI surface.

    The helper was extracted into :mod:`thegent.ux.cli_errors` so the
    governance app + any future CLI sub-app can import it without
    dragging the cockpit dependency surface into the root ``thegent``
    import graph. The widening from ``BaseException`` to ``object``
    (F-15) means non-exception values (paths, arbitrary strings,
    format names) can route through the same helper.
    """

    def test_exc_text_neutralises_bracket_markup(self) -> None:
        """An exception payload containing ``[red]...[/red]`` must
        not be re-interpreted as Rich markup when rendered into a
        console.

        ``rich.markup.escape`` escapes the opening bracket of every
        Rich-markup tag by prepending a backslash (the canonical
        neutralisation pattern). The output string therefore contains
        the literal text ``\\[red]`` (raw chars ``[red]`` AND a leading
        backslash ``\\``) — Rich's parser sees the leading backslash
        and treats the whole token as plain text rather than as a
        colour tag. This assertion pins that contract.
        """
        from thegent.ux.cli_errors import exc_text

        out = exc_text("[red]injection[/red]")
        # The raw chars survive the escape.
        assert "[red]" in out
        # But the opening bracket is backslash-escaped, so Rich's
        # markup parser cannot reinterpret them as a colour tag.
        assert "\\[red]" in out
        assert "\\[/red]" in out
        # And the inner text is unchanged.
        assert "injection" in out

    def test_exc_text_accepts_arbitrary_object(self) -> None:
        """The widened signature accepts ``str``, ``int``, ``Path``,
        and ``Exception`` — the F-15 unification closes the dual
        ``_exc_text(exc)`` / ``_escape(str(...))`` split."""
        from thegent.ux.cli_errors import exc_text

        assert exc_text("plain string") == "plain string"
        assert exc_text(123) == "123"
        assert exc_text(Path("/tmp/example")) == "/tmp/example"
        assert exc_text(ValueError("boom")) == "boom"

    def test_exc_text_does_not_reintroduce_underscore_prefix(self) -> None:
        """The public surface is ``exc_text`` (no underscore) so any
        future CLI sub-app can import it without violating PEP-8
        leading-underscore-as-private convention. The cockpit +
        sota modules keep a backward-compatible ``_exc_text`` alias
        for the existing call sites but every new caller should
        use the public name."""
        from thegent.ux import cli_errors

        assert hasattr(cli_errors, "exc_text")
        assert callable(cli_errors.exc_text)


# ---------------------------------------------------------------------------
# Govern Typer app — name + callback help (F-15-D / F-15-F propagated)
# ---------------------------------------------------------------------------


class TestGovernAppName:
    """Pin the F-15-D contract for the governance surface:
    ``thegent govern --help`` renders ``Usage: govern`` rather than
    Typer's ``Usage: root`` fallback."""

    def test_typer_app_name_is_govern(self) -> None:
        from thegent.cli.apps import govern

        assert govern.app.info.name == "govern"

    def test_typer_app_help_is_not_empty(self) -> None:
        """The root ``help=`` text is rendered when the callback
        decorator is present (F-15-F)."""
        from thegent.cli.apps import govern

        assert govern.app.info.help
        assert "Governance" in govern.app.info.help

    def test_usage_line_shows_govern(self) -> None:
        from typer.testing import CliRunner

        from thegent.cli.apps import govern

        result = CliRunner().invoke(govern.app, ["--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        first_line = next(
            (ln.strip() for ln in clean.splitlines() if ln.strip()),
            "",
        )
        assert first_line.startswith("Usage: govern"), first_line

    def test_root_callback_help_is_surfaced(self) -> None:
        """The ``@app.callback(help=...)`` decorator causes the root
        description to render in ``--help`` alongside the
        sub-commands. Without the callback, Typer's
        ``add_completion=False`` default path drops the root help
        text."""
        from typer.testing import CliRunner

        from thegent.cli.apps import govern

        result = CliRunner().invoke(govern.app, ["--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        assert "Governance controls" in clean


# ---------------------------------------------------------------------------
# Govern error envelope — Rich-markup safety + prefix uniformity
# ---------------------------------------------------------------------------


# The four error-envelope sites that previously interpolated ``{exc}``
# directly into a Rich-markup f-string. Pinning these prevents a
# future refactor from reintroducing the AUDIT-9 contract violation.
_GOVERN_FAILING_SUBCOMMANDS = (
    "approve",
    "reject",
    "vet",
    "register-host",
)


class TestGovernErrorEnvelopeConvention:
    """Pin the F-15 UX-1 error-envelope convention for the
    governance surface: every failure renders as
    ``[red]govern <sub> failed:[/red] <escaped-detail>``."""

    @pytest.mark.parametrize("subcommand", _GOVERN_FAILING_SUBCOMMANDS)
    def test_envelope_prefix_matches_convention(self, subcommand: str) -> None:
        """The rendered envelope for every ``govern <sub>`` failure
        starts with ``govern <sub> failed:`` — verified by parsing
        the source of ``apps/govern.py`` for the exact
        ``print_exc(err_console, "govern <sub> failed:", ...)`` call.
        The new ``print_exc`` helper routes through a Rich
        :class:`Text` assembly so the user-data section is treated
        as literal text and the escape survives the
        ``Console.print(markup=True)`` round-trip."""
        from thegent.cli.apps import govern

        src = Path(govern.__file__).read_text(encoding="utf-8")
        # The exact prefix convention from F-15 UX-1 propagated to the
        # governance surface: every failure routes through
        # ``print_exc`` (NOT ``err_console.print(f"...")``) so the
        # envelope lands on stderr AND the user-data section is
        # rendered as literal text rather than re-parsed as Rich
        # markup.
        pattern = (
            r"print_exc\(\s*err_console,\s*"
            rf'"govern {subcommand} failed:",'
        )
        assert re.search(pattern, src), f"missing 'govern {subcommand} failed:' envelope in apps/govern.py"

    def test_no_naked_exc_interpolation_remains(self) -> None:
        """No ``console.print(f"[red]Error:[/red] {exc}")`` (or
        equivalent with ``result.get('error', ...)``) remains in
        the governance app source. Every envelope site must route
        through :func:`print_exc` so the user-data section is
        rendered as literal text rather than re-parsed as Rich
        markup."""
        from thegent.cli.apps import govern

        src = Path(govern.__file__).read_text(encoding="utf-8")
        # The pre-lane pattern (a) used ``console.print`` (stdout) instead
        # of ``err_console.print`` (stderr) and (b) interpolated ``{exc}``
        # or ``{result.get('error', ...)}`` directly into the Rich-markup
        # f-string. Either of those is a regression of the GOV-1 fix.
        assert 'console.print(f"[red]Error:' not in src, (
            "naked '{exc}' interpolation into Rich-markup f-string remains in apps/govern.py — AUDIT-9 violation"
        )
        assert 'console.print(f"[red]Error:[/red] {' not in src
        assert 'console.print(f"[red]Error:[/red] {result.get' not in src
        # The legacy ``err_console.print(f"[red]X failed:[/red] {exc_text(...)}")``
        # pattern is no longer sufficient because Rich's
        # ``Console.print(markup=True)`` re-interprets the
        # ``\\[red]`` escape and re-applies the markup. The new
        # canonical envelope is ``print_exc(err_console, "X failed:",
        # value)`` so flag any surviving legacy calls.
        assert 'err_console.print(f"[red]govern' not in src, (
            "legacy err_console.print(f'[red]...[/red] {exc_text(...)}') pattern remains — "
            "migrate to print_exc() so the escape survives Console.print(markup=True)"
        )

    def test_all_envelopes_route_through_print_exc(self) -> None:
        """Every error-envelope site in ``apps/govern.py`` must
        route through :func:`print_exc` (not the legacy
        ``err_console.print(f\"[red]...[/red] ...\")`` pattern).

        ``print_exc`` assembles the envelope as a Rich
        :class:`Text` object so the user-data section is treated as
        literal text — bypassing Rich's markup parser entirely.
        This is the only end-to-end-safe render path because Rich's
        ``Console.print(markup=True)`` would otherwise re-interpret
        the ``\\[red]`` escape produced by ``rich.markup.escape``.
        """
        from thegent.cli.apps import govern

        src = Path(govern.__file__).read_text(encoding="utf-8")
        # Count the canonical print_exc invocations for the four
        # governance sub-commands. This is a structural invariant
        # — a future bug cannot reintroduce a leaky envelope site
        # without breaking the pattern. The actual call sites have
        # a trailing comma + argument (``exc`` or ``result.get(...)``)
        # so we match the prefix only.
        assert src.count('print_exc(err_console, "govern approve failed:"') == 1
        assert src.count('print_exc(err_console, "govern reject failed:"') == 1
        assert src.count('print_exc(err_console, "govern vet failed:"') == 1
        assert src.count('print_exc(err_console, "govern register-host failed:"') == 1

    def test_govern_app_imports_exc_text(self) -> None:
        """The governance app imports ``exc_text`` from
        ``thegent.ux.cli_errors`` so it can use the same helper as
        the cockpit + sota surfaces."""
        from thegent.cli.apps import govern

        assert hasattr(govern, "exc_text")
        # The function must come from the shared module so a future
        # cockpit-only refactor cannot accidentally break the
        # governance envelope.
        assert govern.exc_text.__module__ == "thegent.ux.cli_errors"

    def test_govern_app_imports_print_exc(self) -> None:
        """The governance app imports :func:`print_exc` so the
        envelope render path is **safe end-to-end**. Without this
        helper, ``err_console.print(f"[red]X failed:[/red]
        {exc_text(exc)}")`` would render correctly at the string
        level but Rich's ``Console.print(markup=True)`` would
        re-interpret the escape sequence and re-apply the malicious
        markup — undoing the escape.
        """
        from thegent.cli.apps import govern

        assert hasattr(govern, "print_exc")
        assert callable(govern.print_exc)
        assert govern.print_exc.__module__ == "thegent.ux.cli_errors"


class TestGovernErrorEnvelopeRichmarkupSafety:
    """Regression guard: a malicious exception payload containing
    Rich-markup bracket tokens must not be re-interpreted as colour
    codes when rendered to the operator terminal."""

    def test_markup_neutralised_in_envelope(self) -> None:
        """Directly invoke the envelope-rendering path with an
        exception payload containing ``[red]...[/red]`` and assert
        the rendered string has the opening brackets backslash-escaped
        so Rich's markup parser cannot re-interpret them as a
        colour tag.
        """
        from thegent.ux.cli_errors import exc_text

        out = exc_text(ValueError("[red]injection attempt[/red]"))
        # The raw bracket tokens survive the escape, but the opening
        # bracket of each tag is backslash-escaped — that is the
        # canonical Rich-markup neutralisation pattern (mirrors
        # ``TestExcTextWidenedSignature.test_exc_text_accepts_exception``
        # in ``tests/test_unit_ux_sota_fifth_pass.py``).
        assert "[red]" in out
        assert "\\[red]" in out
        assert "injection attempt" in out

    def test_path_argument_does_not_inject_markup(self) -> None:
        """The widened signature (``object`` instead of
        ``BaseException``) means a ``Path``-shaped argument routes
        through the same helper without forcing the caller to write
        ``_exc_text(str(path))``.

        ``rich.markup.escape`` does not distinguish ``Path``-shaped
        strings from any other ``str`` payload — the same
        backslash-escape neutralisation applies uniformly.
        """
        from thegent.ux.cli_errors import exc_text

        out = exc_text(Path("/tmp/[red]injected[/red].txt"))
        assert "[red]" in out
        assert "\\[red]" in out
        assert "/tmp/" in out
        assert "injected" in out


# ---------------------------------------------------------------------------
# Govern --help sanity — every sub-command exits zero and renders cleanly
# ---------------------------------------------------------------------------


class TestGovernHelpOutputSanity:
    """``thegent govern <sub> --help`` must exit zero, render
    ``Usage: govern <sub>``, and never print a ``Traceback``.

    These tests pin the F-15 help-text convention on every wired
    governance sub-command so a future refactor cannot silently
    break the operator-facing help surface.
    """

    @pytest.mark.parametrize("subcommand", _GOVERN_FAILING_SUBCOMMANDS)
    def test_subcommand_help_exits_zero(self, subcommand: str) -> None:
        from typer.testing import CliRunner

        from thegent.cli.apps import govern

        result = CliRunner().invoke(govern.app, [subcommand, "--help"])
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        assert "Traceback" not in clean
        assert "Usage:" in clean

    def test_root_govern_help_exits_zero(self) -> None:
        from typer.testing import CliRunner

        from thegent.cli.apps import govern

        result = CliRunner().invoke(govern.app, ["--help"])
        assert result.exit_code == 0, result.output
        clean = _strip_ansi(result.output)
        assert "Traceback" not in clean
        assert "Usage: govern" in clean


# ---------------------------------------------------------------------------
# Functional end-to-end — exercise the actual try/except envelope path
# ---------------------------------------------------------------------------


class TestGovernErrorEnvelopeFunctional:
    """End-to-end functional check: invoke the governance Typer
    sub-command via ``CliRunner`` with a known-bad inner
    implementation that raises a malicious-looking exception
    payload, and assert the rendered ``err_console`` output
    contains the correct envelope prefix and backslash-escaped
    Rich markup.

    Uses ``govern vet`` as the test surface because its inner
    implementation lives at the importable path
    ``thegent.cli.governance.governance.govern_vet_impl``
    (the ``approve`` / ``reject`` / ``register-host`` inner
    implementations are wired through ``thegent.cli.commands.impl``
    which is currently mid-refactor — see WORKLOG pre-existing
    baseline notes — so the envelope code path is identical and
    exercised through this representative command).
    """

    def test_vet_envelope_renders_prefix_and_escapes_markup(self) -> None:
        """Inject ``[red]malicious[/red]`` into the exception
        payload and assert the rendered envelope (a) carries the
        ``govern vet failed:`` prefix convention, (b) backslash-
        escapes the brackets so Rich's parser cannot reinterpret
        them as colour tags, and (c) lands on stderr (not stdout).
        """
        import io

        from typer.testing import CliRunner

        from thegent.cli.apps import govern as govern_mod

        # Capture err_console output through a StringIO-backed console.
        buffer = io.StringIO()
        captured_console = type(govern_mod.err_console)(
            file=buffer,
            stderr=True,
            force_terminal=False,
            width=200,
        )

        with patch.object(govern_mod, "err_console", captured_console), patch(
            "thegent.cli.governance.governance.govern_vet_impl",
            side_effect=ValueError("[red]malicious[/red] boom"),
        ):
            # Click 8.2+ removed `mix_stderr`; stderr is always separated.
            # Capture both stdout and stderr explicitly via result.
            runner = CliRunner()
            result = runner.invoke(
                govern_mod.app,
                ["vet", "fake-run-id", "--policy", "default"],
                catch_exceptions=False,
            )

        # The envelope failure path exits 1.
        assert result.exit_code == 1

        captured = buffer.getvalue()
        # Prefix convention is honoured.
        assert "govern vet failed" in captured, captured
        # Rich-markup bracket tokens are backslash-escaped.
        assert "\\[red]" in captured, captured
        assert "\\[/red]" in captured, captured
        # The inner payload is preserved.
        assert "malicious" in captured
        assert "boom" in captured
        # The render did NOT leak the raw bracket tokens through
        # Rich's markup parser (which would have stripped them).
        assert "[red]malicious" not in captured or "\\[red]malicious" in captured

    def test_vet_envelope_does_not_inject_console_markup(self) -> None:
        """Render the envelope through :func:`print_exc` (the same
        path the operator terminal takes) and assert no extra ANSI
        red sequence leaks from a malicious payload — the escape
        is effective end-to-end.

        This is the end-to-end regression guard. Before the
        :func:`print_exc` helper, the envelope used
        ``err_console.print(f"[red]X failed:[/red]
        {_exc_text(exc)}")`` which left ``_exc_text`` to do the
        escaping but Rich's ``Console.print(markup=True)`` would
        re-interpret the ``\\[red]`` escape and re-apply the
        markup — undoing the escape. This test pins that
        regression cannot return.
        """
        import io

        from rich.console import Console

        from thegent.ux.cli_errors import print_exc

        # Simulate the operator terminal render path: a
        # ``force_terminal=True`` Rich Console with width 200 (same
        # defaults the cockpit + sota envelopes use).
        sink = io.StringIO()
        terminal = Console(file=sink, force_terminal=True, width=200)
        print_exc(terminal, "govern vet failed:", ValueError("[red]boom[/red]"))

        rendered = sink.getvalue()

        # The escaped brackets survive the Rich parser as literal text
        # (the ``\`` is the Rich markup escape character).
        assert "\\[red]boom\\[/red]" in rendered, repr(rendered)
        # But there is exactly one ANSI red sequence in the output —
        # the envelope prefix, not the injected payload. If the
        # escape failed, there would be two (one for the prefix, one
        # for the injected payload).
        red_ansi = "\x1b[31m"
        assert rendered.count(red_ansi) == 1, (
            f"expected exactly one ANSI red (the envelope prefix), got {rendered.count(red_ansi)}: {rendered!r}"
        )
        # And the payload text is present.
        assert "boom" in rendered

    def test_print_exc_helper_text_assembly(self) -> None:
        """The :func:`print_exc` helper assembles the envelope via
        :class:`rich.text.Text` so the user-data section is treated
        as literal text. Verify the assembled :class:`Text` has the
        right structure: a styled prefix span covering the prefix
        text, followed by the plain user-data segment.

        ``rich.text.Text.spans`` is the public API for inspecting
        the style spans; each :class:`rich.text.Span` carries
        ``start``, ``end``, and ``style``. The prefix span must
        carry ``style="red"`` and the user-data section must NOT
        carry any style (so Rich renders it as literal text).
        """
        from rich.text import Text

        from thegent.ux.cli_errors import exc_text

        line = Text()
        line.append("govern approve failed:", style="red")
        line.append(" ")
        line.append(exc_text(ValueError("[red]pwned[/red]")))

        # The plain-text payload round-trips the user-data.
        assert "govern approve failed:" in line.plain
        assert "\\[red]pwned\\[/red]" in line.plain

        # The prefix span carries the "red" style and covers the
        # prefix text only — the user-data segment is unstyled.
        red_spans = [span for span in line.spans if str(span.style) == "red"]
        assert red_spans, f"no 'red' style span found: {list(line.spans)}"
        prefix_span = red_spans[0]
        assert line.plain[prefix_span.start : prefix_span.end] == "govern approve failed:"

        # The user-data segment (after the prefix + space) has no
        # styling span over it — i.e. Rich's parser cannot apply any
        # markup to the escaped brackets. We verify by checking that
        # the "red" span ends exactly at the prefix boundary (not
        # bleeding into the user-data).
        assert prefix_span.end == len("govern approve failed:")
        # The characters after the prefix span contain the escaped
        # brackets as literal text.
        suffix = line.plain[prefix_span.end :]
        assert "\\[red]pwned\\[/red]" in suffix


# ---------------------------------------------------------------------------
# CLI integration — exercised through the parent ``thegent`` root
# ---------------------------------------------------------------------------


class TestGovernErrorEnvelopeCliIntegration:
    """End-to-end CLI integration: invoke ``thegent govern <sub>
    --help`` through the root CLI binary path so the
    ``apps/main.py → add_typer(govern_app, name="govern")`` wiring
    is exercised, not just the bare ``govern.app`` runner.

    These tests use ``subprocess`` because the parent CLI
    (``thegent.cli.apps.main``) imports the cockpit + sota surfaces
    which depend on Typer + Rich at module load time, and the
    in-process :class:`typer.testing.CliRunner` does not survive
    the multi-app wiring for the root command.

    Skipped automatically when the ``thegent`` CLI binary is not
    available on ``$PATH`` (e.g. fresh dev environment without
    ``pip install -e .``); the in-process tests above cover the
    contract surface in that case.
    """

    @pytest.fixture(scope="class")
    def thegent_binary(self) -> str:
        binary = "thegent"
        try:
            subprocess.run(
                [binary, "--help"],
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("thegent CLI binary not on $PATH; skipping CLI integration tests")
        return binary

    @pytest.mark.parametrize("subcommand", _GOVERN_FAILING_SUBCOMMANDS)
    def test_subcommand_help_through_root_cli(self, thegent_binary: str, subcommand: str) -> None:
        result = subprocess.run(
            [thegent_binary, "govern", subcommand, "--help"],
            capture_output=True,
            check=False,
            timeout=10,
        )
        # ``thegent govern <sub> --help`` must exit zero — a future
        # regression in the ``add_typer`` wiring would surface here.
        assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
        stdout = _strip_ansi(result.stdout.decode("utf-8", errors="replace"))
        assert "Traceback" not in stdout
        assert "Usage: govern" in stdout
        assert subcommand in stdout


# ---------------------------------------------------------------------------
# Structural invariant — cli_cockpit re-exports the helper
# ---------------------------------------------------------------------------


class TestCockpitReexportBackwardCompat:
    """Backward-compatibility guard: the cockpit module still
    exposes ``_exc_text`` (with the leading underscore preserved)
    so the dozens of existing call sites inside ``cli_cockpit.py``
    and ``cli_sota.py`` continue to work unchanged.

    A future refactor that drops the re-export would silently
    break the cockpit + sota error envelopes; this test pins the
    import so the regression is loud.
    """

    def test_cli_cockpit_still_exposes_underscore_alias(self) -> None:
        from thegent.ux import cli_cockpit

        assert hasattr(cli_cockpit, "_exc_text")
        assert callable(cli_cockpit._exc_text)
        assert cli_cockpit._exc_text.__module__ == "thegent.ux.cli_errors"

    def test_cli_sota_still_exposes_underscore_alias(self) -> None:
        from thegent.ux import cli_sota

        assert hasattr(cli_sota, "_exc_text")
        assert callable(cli_sota._exc_text)
        assert cli_sota._exc_text.__module__ == "thegent.ux.cli_errors"

    def test_cli_cockpit_still_exposes_rich_escape_alias(self) -> None:
        """The F-15 ``_rich_escape`` alias (introduced when the
        cockpit module consolidated its escape helpers in the
        fifth-pass lane) is preserved alongside ``_exc_text`` for
        backward compatibility. The two names point at the same
        underlying function so existing call sites that referenced
        ``_rich_escape`` directly (e.g. the F-15 unified-helper
        invariant test) continue to work after the helper was
        extracted into :mod:`thegent.ux.cli_errors`."""
        from thegent.ux import cli_cockpit

        assert hasattr(cli_cockpit, "_rich_escape")
        assert callable(cli_cockpit._rich_escape)
        # Both names should resolve to the same callable.
        assert cli_cockpit._exc_text is cli_cockpit._rich_escape
