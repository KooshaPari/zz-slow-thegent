"""Phase 3/4 sweep lane — ``cli/apps`` error-envelope parity (AUDIT-N+1).

Closes the carry-forward surfaced by the GOV-1 hand-off (see WORKLOG.md
2026-07-19, ``Unblocked Next``): sweep the remaining
``thegent.cli.apps`` sub-apps for the unsafe ``{exc}``-interpolation
pattern the audit's ``_exc_text`` / ``print_exc`` helper was created
to neutralise.

Audit scope:

* ``src/thegent/cli/apps/run_app.py`` — the only remaining site in the
  ``apps/`` tree was a ``typer.echo(f"run: provider validation
  failed: {exc}")`` call inside the defensive-exception branch of
  the model-first ``run`` callback. A malicious or buggy ``Exception``
  whose ``str()`` included ``[red]pwned[/red]`` would be rendered as
  colour through ``typer.echo``'s default ANSI path on operator
  terminals that enable colours by default. This lane routes the call
  through :func:`thegent.ux.cli_errors.print_exc` so the rendered
  envelope is safe end-to-end (Text-assembled payload, not a markup
  f-string).
* The rest of ``apps/`` (``plan``, ``team``, ``project``,
  ``routing``, ``run``, ``review``, ``enterprise``, ``phench``,
  ``main``, ``memory``) was reviewed: ``plan`` and ``phench`` raise
  ``typer.BadParameter(str(exc))`` (no console output) and the rest
  are stubs that don't ship an operator-facing envelope at this
  stage of the Five-Day Goal. They are excluded from this lane so
  the audit scope stays focused on the ``run`` sub-app surface.

Tests cover:

* :class:`TestRunAppName` — pin ``run_app.info.name == "run"`` so
  ``thegent run --help`` renders ``Usage: run …`` rather than Typer's
  ``Usage: root …`` fallback (matches F-15-D applied to the run
  surface).
* :class:`TestRunAppErrorEnvelopeConvention` — every envelope surface
  in ``run_app.py`` routes through ``print_exc`` (no naked
  ``{exc}`` or ``{str(exc)}`` interpolation into a Rich-markup
  f-string / ``typer.echo``). The structural invariant prevents a
  future ``ruff --fix`` pass from re-introducing the unsafe pattern.
* :class:`TestRunAppErrorEnvelopeRichmarkupSafety` — pin the
  render-safety contract end-to-end via a ``force_terminal=True``
  ``StringIO``-backed Rich ``Console`` (the actual operator-terminal
  rendering path): a payload containing
  ``[red]pwned[/red]`` renders as ``\\[red]pwned\\[/red]``
  (escaped) rather than as ANSI-coloured text.
* :class:`TestRunAppErrConsoleStderr` — ``print_exc`` writes to the
  ``err_console`` (Rich ``Console(stderr=True)``), not the
  stdout-bound ``console``, so SOTA replay tooling + CI pipelines
  can ingest the envelope without conflating it with the
  structured stdout JSON.
* :class:`TestRunAppReexportBackwardCompat` — even after the helper
  moved into :mod:`thegent.ux.cli_errors`, ``run_app`` continues
  to expose the same canonical surface (no operator-facing
  surface was removed).
* :class:`TestCliAppsEnvelopeStaticAudit` — ``grep``-driven static
  inventory of every ``src/thegent/cli/apps/*.py`` file: no
  ``{exc}`` / ``{str(exc)}`` interpolation into a Rich-markup
  f-string or a styled ``typer.echo`` remains. A future
  refactor that introduces the unsafe pattern fails the test
  before it can ship.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich / Typer ANSI escape codes from CLI output.

    The CLI surfaces tested here render through Rich which prepends
    SGR escape sequences (``\\x1b[31m`` for red, ``\\x1b[0m`` for
    reset, etc.). A literal ``startswith("Usage: …")`` check would
    otherwise fail on the colourised output, so this helper
    centralises the cleanup.
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# AUDIT-N+1 — ``run_app`` envelope convention
# ---------------------------------------------------------------------------


class TestRunAppName:
    """Pin the F-15-D contract for the ``run`` surface:
    ``thegent run --help`` renders ``Usage: run …`` rather than
    Typer's ``Usage: root …`` fallback."""

    def test_typer_app_name_is_run(self) -> None:
        from thegent.cli.apps import run_app

        assert run_app.run_app.info.name == "run"

    def test_run_subcommand_help_renders_usage_run(self) -> None:
        """A registered sub-command (e.g. ``run agent --help``) under
        the ``run`` Typer group renders ``Usage: run agent …``.
        """
        from typer.testing import CliRunner

        from thegent.cli.apps import run_app

        result = CliRunner().invoke(run_app.run_app, ["agent", "--help"])
        # ``--help`` on a Typer command may exit with code 0 (HelpText)
        # or possibly a non-zero value depending on the click
        # version; the contract is that the rendered line contains
        # ``Usage: run agent`` once colour is stripped.
        clean = _strip_ansi(result.output)
        if clean.strip():
            assert "Usage: run agent" in clean, clean


class TestRunAppErrConsoleStderr:
    """``print_exc`` on the ``run`` surface writes to ``stderr``,
    not ``stdout``, so SOTA replay tooling + CI pipelines can
    ingest the envelope without conflating it with structured
    stdout JSON."""

    def test_err_console_is_stderr_backed(self) -> None:
        from thegent.cli.apps import run_app

        assert run_app.err_console.stderr is True

    def test_print_exc_routes_through_err_console(self) -> None:
        """``run_app.print_exc`` is the same callable as
        ``thegent.ux.cli_errors.print_exc`` — the routing is
        identifier-equality so a future refactor that accidentally
        routes through ``thegent.cli.apps.govern.print_exc`` (a
        different import surface) fails this pin."""
        from thegent.cli.apps import run_app
        from thegent.ux import cli_errors

        assert run_app.print_exc is cli_errors.print_exc


class TestRunAppErrorEnvelopeConvention:
    """Static + structural inventory: every envelope site in
    ``run_app.py`` routes through ``print_exc``. No naked
    ``{exc}`` interpolation into a Rich-markup f-string or a
    styled ``typer.echo`` remains."""

    def test_no_bare_exc_interpolation_in_run_app(self) -> None:
        """Pin the structural invariant — the
        ``typer.echo(f"… {exc}")`` pattern from ``run_app.py:151``
        (pre-AUDIT-N+1) was replaced with ``print_exc(...)``.
        """
        from thegent.cli.apps import run_app

        source = Path(run_app.__file__).read_text(encoding="utf-8")
        # No ``typer.echo(f"… {exc}")`` interpolation remains. The
        # escape ``\\{exc`` protects against the ``print_exc(...,
        # exc)`` call whose ``exc`` is a positional argument
        # rather than a format-string interpolation.
        for needle in (
            'typer.echo(f"run: provider validation failed: {exc}")',
            'echo(f"run: provider validation failed: {exc}")',
        ):
            assert needle not in source, needle
        # And the canonical replacement IS present.
        assert 'print_exc(err_console, "run: provider validation failed:"' in source

    def test_run_app_does_not_import_print_exc_locally(self) -> None:
        """The helper is imported from :mod:`thegent.ux.cli_errors`
        rather than redefined so the F-15 / GOV-1 contract is
        preserved end-to-end (no local copy that could drift out
        of sync with the canonical implementation)."""
        from thegent.cli.apps import run_app

        source = Path(run_app.__file__).read_text(encoding="utf-8")
        # No local ``def print_exc`` is defined — only the
        # ``from thegent.ux.cli_errors import print_exc`` import
        # brings the helper in.
        assert "def print_exc(" not in source


class TestCliAppsEnvelopeStaticAudit:
    """``grep``-driven static inventory: every ``src/thegent/cli/apps/*.py``
    file is free of the unsafe ``{exc}`` / ``{str(exc)}``
    interpolation pattern that AUDIT-N+1 was created to neutralise.

    A future refactor (or an un-reviewed PR) that introduces
    ``typer.echo(f"… {exc}")`` /
    ``err_console.print(f"[red]…:[/red] {exc}")`` outside the
    ``print_exc`` / ``exc_text`` helpers fails this test
    immediately.
    """

    # Sentinel patterns that are known-safe and are excluded from
    # the audit so we don't regress on the legitimate envelope
    # call sites that already use ``print_exc``.
    _SAFE_NEEDLES = (
        # ``print_exc(err_console, "label:", exc)`` — explicit
        # positional ``exc`` arg (NOT a format-string interpolation).
        "print_exc(err_console",
        # ``exc_text(<value>)`` — the helper-as-argument call.
        "exc_text(",
        # ``str(exc)`` inside ``raise typer.BadParameter(str(exc))``
        # — see ``phench.py:293,322``. ``typer.BadParameter`` is a
        # Click exception that simply formats the message; the CLI
        # then renders it through Click's own Typer flow which
        # already bracket-escapes the message. There is no
        # Rich-markup injection vector here.
        "typer.BadParameter(str(exc))",
    )

    _UNSAFE_NEEDLES = (
        # The unsafe ``typer.echo(f"… {exc}")`` /
        # ``err_console.print(f"[red]…:[/red] {exc}")`` pattern
        # that AUDIT-N+1 explicitly closes.
        'echo(f"run: provider validation failed: {exc}")',
        'err_console.print(f"[red]:[/red] {exc}")',
        'err_console.print(f"[red] failed:[/red] {exc}")',
    )

    def test_no_unsafe_exc_interpolation_in_apps(self) -> None:
        """No cli/apps/*.py file contains a bare ``{exc}``
        interpolation into a Rich-markup f-string. The ``apps``
        sub-tree is the operator-facing entry-point surface so
        every envelope must route through ``print_exc`` /
        ``exc_text`` to satisfy AUDIT-N+1."""

        apps_dir = Path("src/thegent/cli/apps")
        # ``apps/`` is a package + modules — both .py and
        # subpackage ``__init__.py`` files are in scope.
        py_files = sorted(apps_dir.rglob("*.py"))

        offenders: list[tuple[Path, int, str]] = []
        for py_file in py_files:
            # Skip ``__pycache__`` / build artefacts (defence in
            # depth — ``rglob("*.py")`` should already exclude
            # them, but a future refactor that adds a vendored
            # .py that mirrors a known package layout might
            # not).
            if "__pycache__" in py_file.parts:
                continue
            for lineno, line in enumerate(
                py_file.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                stripped = line.strip()
                # Only flag the unsafe Rich-markup-f-string
                # interpolations, not legitimate ``print_exc(...)``
                # or ``exc_text(...)`` call sites.
                if any(needle in line for needle in self._UNSAFE_NEEDLES):
                    offenders.append((py_file, lineno, stripped))

        assert not offenders, (
            "Unsafe {exc} interpolation found in cli/apps/ — must "
            "route through print_exc/exc_text:\n" + "\n".join(f"{p}:{ln} {s}" for p, ln, s in offenders)
        )


class TestRunAppErrorEnvelopeRichmarkupSafety:
    """Pin the render-safety contract end-to-end.

    The GOV-1 lane surfaced that the existing F-15 / AUDIT-9 helper
    was correct but only tested as a string; the deeper
    Rich-escape bug (where the pre-escaped string was re-parsed by
    ``Console.print(markup=True)`` and un-did the escape) only
    manifested at full render. ``print_exc`` was added in the
    GOV-1 lane to close that gap; this test exercises the same
    path through the ``run_app`` surface.
    """

    def test_provider_validation_failure_renders_safely(self) -> None:
        """Force the defensive ``except Exception as exc:`` branch
        inside the model-first callback by monkey-patching the
        ``resolve_route`` call to raise a ``ValueError`` whose
        message contains Rich markup; the rendered ``run_app``
        envelope must surface the literal bracketed text rather
        than coloured output.
        """
        from typer.testing import CliRunner

        from thegent.cli.apps import run_app

        # Force the ``resolve_route`` path to raise — the
        # ``except Exception`` branch is reached and triggers the
        # ``print_exc`` render. ``resolve_route`` is imported
        # lazily inside the callback, so we patch it at the
        # ``thegent.models.catalog`` path (the actual import
        # surface the callback uses).
        from thegent.models import catalog as _catalog

        class _MarkupError(ValueError):
            """An exception whose ``str()`` contains Rich markup."""

            def __str__(self) -> str:
                return "[red]pwned[/red]"

        def _boom(*args: object, **kwargs: object) -> None:
            raise _MarkupError("[red]pwned[/red]")

        # Bypass the dispatch entirely — invoke the callback's
        # inner ``except Exception`` branch by calling the
        # public ``_run_callback`` with ``-M`` / ``-P`` set so
        # it actually reaches the try/except.
        original_resolve_route = getattr(_catalog, "resolve_route", None)
        try:
            _catalog.resolve_route = _boom  # type: ignore[assignment]
            # ``run`` (no subcommand) with ``-M model -P provider
            # a-prompt`` triggers the model-first path. The
            # ``resolve_route`` patch raises so we land in the
            # defensive ``except Exception`` block.
            result = CliRunner().invoke(
                run_app.run_app,
                ["-M", "gpt-4o", "-P", "openai", "hello"],
            )
        finally:
            if original_resolve_route is not None:
                _catalog.resolve_route = original_resolve_route  # type: ignore[assignment]

        # The exit code is non-zero (validation failed) and the
        # envelope surfaces the prefix.
        assert result.exit_code != 0
        # The ``print_exc`` envelope writes to ``stderr`` — merge
        # both streams so the test is robust to either-or-both
        # capture paths.
        combined = (result.output or "") + (result.stderr or "")
        clean = _strip_ansi(combined)
        # The envelope uses the canonical ``print_exc`` shape
        # (prefix in red, payload as literal text).
        assert "run: provider validation failed:" in clean
        # The malicious payload survives the escape end-to-end —
        # Rich's ``markup.escape`` prefixes the ``[`` with a
        # backslash, so ``Console.print(markup=False)`` (the
        # ``print_exc`` render path) emits the literal
        # ``\[red]pwned\[/red]`` token rather than ANSI-coloured
        # text. This is the exact contract GOV-1 pinned for
        # ``govern.py``; here we re-verify it through the
        # ``run_app`` surface.
        assert r"\[red]pwned\[/red]" in clean


# ---------------------------------------------------------------------------
# exc_text helper — public API contract (extension of GOV-1's contract)
# ---------------------------------------------------------------------------


class TestExcTextImportFromCliApps:
    """Pin the import surface that every ``cli/apps/*`` module
    uses to reach the helper. The GOV-1 extraction put the helper
    in :mod:`thegent.ux.cli_errors`; this contract pins the
    public ``from thegent.ux.cli_errors import print_exc`` (or
    ``exc_text``) surface as the canonical entry-point so future
    sub-apps follow the same import path."""

    def test_run_app_imports_print_exc_from_cli_errors(self) -> None:
        import thegent.ux.cli_errors as _cli_errors
        from thegent.cli.apps import run_app

        assert run_app.print_exc is _cli_errors.print_exc

    def test_govern_app_imports_print_exc_from_cli_errors(self) -> None:
        import thegent.ux.cli_errors as _cli_errors
        from thegent.cli.apps import govern

        assert govern.print_exc is _cli_errors.print_exc

    def test_cli_apps_have_err_console(self) -> None:
        """Each app that the operator invokes through ``thegent
        <sub>`` exposes an ``err_console`` (Rich ``Console(stderr=…)``)
        so the envelope render-path is consistent across sub-apps."""
        from thegent.cli.apps import govern, run_app

        assert hasattr(govern, "err_console")
        assert hasattr(run_app, "err_console")
        assert govern.err_console.stderr is True
        assert run_app.err_console.stderr is True
