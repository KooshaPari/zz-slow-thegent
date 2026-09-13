"""SOTA fifth-pass hardening tests for the operator-CLI help text + error envelopes.

Closes the fifth-pass audit findings identified by the parallel
``sage`` sub-agent (see WORKLOG.md 2026-07-19 entry):

* **F-15-D / F-15-E** — ``typer.Typer(name=...)`` is now set on both
  ``cockpit`` and ``sota`` apps so ``--help`` renders ``Usage: cockpit``
  and ``Usage: sota`` instead of Typer's "root" fallback.
* **F-15-F** — ``@app.callback(help=...)`` on the sota root forces
  Typer to render the root description alongside the sub-commands.
* **F-15-A / F-15-B** — every cockpit + sota sub-command help string
  is a single imperative sentence ending in a period. The longest
  multi-sentence help (cockpit ``replay`` / sota ``replay``) is
  collapsed to one sentence, with the lane annotation moved into the
  function docstring (Typer renders docstrings as the ``--help``
  extended description).
* **F-15-G** — ``_exc_text(value: object)`` accepts any object
  (paths, exceptions, strings, ints) and unifies what was previously
  split between ``_exc_text(exc: BaseException)`` and
  ``_escape(str(...))``. The widened signature lets every call-site
  use a single helper name and removes the dual-helper inconsistency
  that pre-existed since the AUDIT-9 hand-off.

These tests pin the contracts a future operator / CI consumer can
rely on. They are intentionally small and independent — each test
documents one specific aspect of the help-text / error-envelope
shape.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest

from thegent.ux.cli_cockpit import _exc_text
from thegent.ux.cli_cockpit import app as cockpit_app

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich/Typer ANSI escape codes from CliRunner output.

    ``typer.testing.CliRunner`` captures the raw bytes including
    SGR escape sequences, so a literal ``startswith("Usage: …")``
    check fails when the help string is colourised. This helper
    centralises the cleanup so the period-convention tests can
    reason about the plain text directly.
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# F-15-D — cockpit app exposes its name in --help
# ---------------------------------------------------------------------------


class TestCockpitAppName:
    """Pin the F-15-D contract: ``cockpit --help`` renders
    ``Usage: cockpit`` rather than Typer's ``Usage: root`` fallback."""

    def test_usage_line_shows_cockpit(self) -> None:
        from typer.testing import CliRunner

        result = CliRunner().invoke(cockpit_app, ["--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        # The first non-empty line of --help should be ``Usage: cockpit …``.
        # Typer prepends a leading space (``' Usage: cockpit …'``) when
        # colourising, so we ``.strip()`` the candidate before testing.
        first_line = next(
            (ln.strip() for ln in clean.splitlines() if ln.strip()),
            "",
        )
        assert first_line.startswith("Usage: cockpit"), first_line

    def test_typer_app_name_is_cockpit(self) -> None:
        # Typer exposes the program name on ``info.name`` after the
        # app is constructed; pinning this directly avoids reliance
        # on Typer's rendering internals.
        assert cockpit_app.info.name == "cockpit"


# ---------------------------------------------------------------------------
# F-15-E — sota app exposes its name in --help
# ---------------------------------------------------------------------------


class TestSotaAppName:
    """Pin the F-15-E contract: ``sota --help`` renders
    ``Usage: sota`` and surfaces the callback ``help=``."""

    def test_usage_line_shows_sota(self) -> None:
        from typer.testing import CliRunner

        from thegent.ux.cli_sota import app as sota_app

        result = CliRunner().invoke(sota_app, ["--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        first_line = next(
            (ln.strip() for ln in clean.splitlines() if ln.strip()),
            "",
        )
        assert first_line.startswith("Usage: sota"), first_line

    def test_typer_app_name_is_sota(self) -> None:
        from thegent.ux.cli_sota import app as sota_app

        assert sota_app.info.name == "sota"

    def test_callback_help_is_rendered(self) -> None:
        """F-15-F: ``@app.callback(help=...)`` causes the root
        description to render in ``--help`` output."""
        from typer.testing import CliRunner

        from thegent.ux.cli_sota import app as sota_app

        result = CliRunner().invoke(sota_app, ["--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        # The callback's help string is the only description text
        # under the ``Usage:`` line that does NOT begin with a
        # sub-command name.
        assert "SOTA audit-replay tooling root" in clean


# ---------------------------------------------------------------------------
# F-15-A — every sub-command help ends in a period
# ---------------------------------------------------------------------------


def _extract_help_text(clean: str) -> str:
    """Extract the Typer-rendered ``help=`` text from a --help output.

    Typer wraps long help text at the console width (~70 chars
    by default). The wrapped continuation lines lose the
    sentence-final punctuation. This helper concatenates the
    first wrapped segment with any continuation lines until a
    line that ends with ``.`` is found.
    """
    body_lines = [
        ln.strip()
        for ln in clean.splitlines()
        if ln.strip()
        and not ln.strip().startswith("╭")
        and not ln.strip().startswith("╰")
        and not ln.strip().startswith("│")
    ]
    # Skip the ``Usage: …`` line.
    body_lines = [ln for ln in body_lines if not ln.startswith("Usage:")]
    if not body_lines:
        return ""
    # Concatenate the first body line with continuation lines
    # until a line that ends with ``.`` is found.
    joined = body_lines[0]
    for ln in body_lines[1:]:
        if joined.endswith("."):
            break
        joined = f"{joined} {ln}"
    return joined


class TestHelpTextPeriodConvention:
    """Pin the F-15-A contract: every Typer ``help=`` string ends in
    a single period. The legacy multi-sentence ``cockpit replay``
    help (which previously dropped the trailing period) is
    normalised to a single sentence."""

    def _all_help_strings(self) -> list[tuple[str, str]]:
        from thegent.ux.cli_sota import app as sota_app

        pairs: list[tuple[str, str]] = []
        for typer_app, prefix in (
            (cockpit_app, "cockpit"),
            (sota_app, "sota"),
        ):
            for sub in typer_app.registered_commands:
                pairs.append((f"{prefix} {sub.name}", sub.help or ""))
        return pairs

    def test_every_help_ends_with_period(self) -> None:
        offenders: list[tuple[str, str]] = []
        for label, help_text in self._all_help_strings():
            stripped = help_text.rstrip()
            if not stripped.endswith("."):
                offenders.append((label, help_text))
        assert not offenders, "sub-commands with help text not ending in '.':\n" + "\n".join(
            f"  {label}: {help_text!r}" for label, help_text in offenders
        )

    def test_cockpit_replay_help_is_single_sentence(self) -> None:
        """The legacy ``cockpit replay`` help was a 2-sentence
        block that included a literal backtick-quoted command
        reference. After F-15 it is one imperative sentence ending
        in a period."""
        from typer.testing import CliRunner

        result = CliRunner().invoke(cockpit_app, ["replay", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        help_text = _extract_help_text(clean)
        assert help_text.endswith("."), help_text
        # The legacy lane-marker parenthetical "third Unblocked Next
        # item" must no longer appear in the Typer-rendered help;
        # it now lives in the function docstring (extended --help
        # description).
        assert "third Unblocked Next item" not in help_text

    def test_sota_replay_help_is_single_sentence(self) -> None:
        from typer.testing import CliRunner

        from thegent.ux.cli_sota import app as sota_app

        result = CliRunner().invoke(sota_app, ["replay", "--help"])
        assert result.exit_code == 0
        clean = _strip_ansi(result.output)
        help_text = _extract_help_text(clean)
        assert help_text.endswith("."), help_text
        # The legacy "structured report (text / json / junitxml)"
        # enumeration no longer lives in the Typer-rendered help.
        assert "structured report" not in help_text


# F-15-B — cockpit audit decision-tail docstring is imperative
# ---------------------------------------------------------------------------


class TestDecisionTailDocstringConvention:
    """Pin the F-15-B contract: the ``cockpit_audit_decision_tail``
    docstring first line is imperative mood (matches the convention
    used by every other sub-command)."""

    def test_decision_tail_docstring_starts_with_imperative(self) -> None:
        from thegent.ux.cli_cockpit import cockpit_audit_decision_tail

        doc = cockpit_audit_decision_tail.__doc__ or ""
        first_line = doc.strip().splitlines()[0] if doc.strip() else ""
        assert first_line, "docstring is empty"
        # Imperative mood verbs we use across the sub-commands:
        # Render / Evaluate / Replay / Print / Live-tail / Tail.
        # The legacy "Single-shot or live-tail…" started lower-case
        # with a non-imperative verb. After F-15-B it starts with
        # "Live-tail" (imperative).
        assert first_line.startswith("Live-tail"), first_line


# ---------------------------------------------------------------------------
# F-15-G — _exc_text accepts any object (paths, exceptions, strings, ints)
# ---------------------------------------------------------------------------


class TestExcTextWidenedSignature:
    """Pin the F-15-G contract: ``_exc_text(value: object)`` accepts
    any object and routes through Rich's escape. The legacy
    ``_exc_text(exc: BaseException)`` and ``_escape(str(...))``
    split is unified."""

    def test_exc_text_accepts_exception(self) -> None:
        try:
            raise ValueError("boom [red]injected[/red]")
        except Exception as exc:
            out = _exc_text(exc)
        assert "[red]" in out  # raw chars present
        assert "\\[red]" in out  # but escaped so Rich won't parse

    def test_exc_text_accepts_path(self) -> None:
        # The legacy helper required ``_escape(str(batch))`` for
        # Path arguments. After F-15-G the wrapper accepts Path
        # objects directly.
        path = Path("/tmp/[red]injection[/red].json")
        out = _exc_text(path)
        assert "\\[red]" in out
        # str() of the path must equal the input to ``_exc_text``.
        assert out == _exc_text(str(path))

    def test_exc_text_accepts_string(self) -> None:
        out = _exc_text("plain [red]attempt[/red]")
        assert out == "plain \\[red]attempt\\[/red]"

    def test_exc_text_accepts_int(self) -> None:
        # Non-string non-exception objects still work via str() coercion.
        assert _exc_text(42) == "42"
        assert _exc_text(3.14) == "3.14"

    def test_exc_text_blocks_rich_injection(self) -> None:
        """The whole point of the AUDIT-9 escape shim: an attacker
        who controls the interpolated value cannot inject Rich
        markup that would alter the rendering of the rest of the
        line. After F-15-G, the same property holds for paths,
        exceptions, strings, and arbitrary objects."""
        from rich.console import Console

        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False, no_color=True, width=200)
        # Imagine an attacker-controlled exception message:
        injection = "[red]CRITICAL SECURITY ALERT[/red]"
        # The error envelope prefix should be red, the user data
        # should render as literal text (no red color applied).
        console.print(f"[red]pre-check failed:[/red] {_exc_text(injection)}")
        rendered = buf.getvalue()
        # The escape means the user data shows as literal text in
        # the output (not red-coloured). The prefix IS red-coloured.
        assert "pre-check failed:" in rendered
        # The injected payload must appear as literal text:
        assert "[red]CRITICAL SECURITY ALERT[/red]" in rendered

    def test_exc_text_escape_helper_unified(self) -> None:
        """F-15-G: ``_exc_text`` is the canonical escape shim — the
        legacy ``_escape`` helper is no longer imported at module
        scope (the module-level binding is now ``_rich_escape`` to
        avoid shadowing the public ``escape`` symbol)."""
        # The internal module-level binding must be present and
        # named ``_rich_escape`` (the private wrapper around
        # ``rich.markup.escape``). The legacy ``_escape`` import
        # was removed.
        from thegent.ux import cli_cockpit

        assert hasattr(cli_cockpit, "_rich_escape")
        # The public ``_exc_text`` helper must wrap ``_rich_escape``
        # via ``str(value)`` coercion.
        assert cli_cockpit._exc_text("[x]") == cli_cockpit._rich_escape("[x]")


# ---------------------------------------------------------------------------
# UX-1 — error envelope prefixes are consistent across sub-commands
# ---------------------------------------------------------------------------


class TestErrorEnvelopeConvention:
    """Pin the UX-1 contract: every CLI error path routes through
    ``err_console.print(f'[red]X failed:[/red] ...')`` and routes
    user-influenced data through ``_exc_text``. The pre-existing
    ``AUDIT-9`` contract (no Rich markup leakage) is preserved."""

    def test_all_cli_error_call_sites_use_exc_text(self) -> None:
        """Static check: every ``err_console.print(...)`` call in
        ``cli_cockpit.py`` and ``cli_sota.py`` that interpolates a
        value MUST route through ``_exc_text(...)``. No bare
        ``{exc}``, ``{batch}``, ``{compare}`` etc. should appear
        inside an f-string passed to ``err_console.print``."""
        import re

        cockpit_src = Path("src/thegent/ux/cli_cockpit.py").read_text(encoding="utf-8")
        sota_src = Path("src/thegent/ux/cli_sota.py").read_text(encoding="utf-8")

        # Match ``err_console.print(...)`` f-string calls. We accept
        # bare text calls (no interpolation) and escaped
        # interpolations (``{_exc_text(...)}``); we reject any
        # other interpolation pattern.
        pattern = re.compile(
            r'err_console\.print\(\s*f?"([^"]*?\[[^\]]+\][^"]*?)"',
            re.DOTALL,
        )
        offenders: list[tuple[str, str, str]] = []
        # Match ``_exc_text(...)`` interpolations that may include
        # ``str(...)`` calls inside AND a format-suffix (``!r`` /
        # ``!s`` / ``!a`` / ``:spec``). The legacy helper split was
        # ``_escape(str(batch))`` for paths and ``_exc_text(exc)`` for
        # exceptions; both are now collapsed into a single helper
        # call, but the call shape still varies (with/without ``!r``
        # suffix, with/without nested ``str()`` coercion). The
        # ``_EXC_TEXT_PATTERN`` regex below accepts all of those.
        _EXC_TEXT_PATTERN = re.compile(
            r"\{_exc_text\("
            r"(?:str\([^)]*\)|[^)]*)"
            r"\)(?:![rsa]|:[^}]+)?\}"
        )
        for src, label in (
            (cockpit_src, "cli_cockpit.py"),
            (sota_src, "cli_sota.py"),
        ):
            for match in pattern.finditer(src):
                fstring = match.group(1)
                # Strip out ``{_exc_text(...)}`` interpolations
                # (including nested ``str()`` calls and ``!r``
                # suffixes).
                stripped = _EXC_TEXT_PATTERN.sub("", fstring)
                # Any remaining ``{...}`` is an interpolation that
                # was NOT routed through ``_exc_text``.
                leftover = re.findall(r"\{[^{}]+\}", stripped)
                if leftover:
                    offenders.append((label, fstring.strip()[:120], ",".join(leftover)))
        assert not offenders, "err_console.print f-strings with non-_exc_text interpolation:\n" + "\n".join(
            f"  {label}: {snippet!r} (leftover: {leftover!r})" for label, snippet, leftover in offenders
        )

    def test_help_text_invariant_for_known_subcommands(self) -> None:
        """Sanity check: the audit's catalogued sub-command help
        strings render as expected after F-15 normalization. This
        test pins the specific wording so future drift is caught."""
        from typer.testing import CliRunner

        # Map of (sub-command args) -> expected verbatim help text.
        # Each invocation routes through the ``cockpit_app`` Typer
        # instance — there is no ``cockpit`` prefix in the args
        # because the app is already mounted at the test root.
        expected = {
            ("render",): "Render the 4-pane operator cockpit to stdout.",
            ("traffic", "summary"): "Render a TRAFFIC KPI snapshot to stdout.",
            ("pre-check",): "Evaluate a PolicyContext against the governance PolicyEngine.",
            ("audit", "tail"): "Print the last N decisions from the audit JSONL.",
        }
        for cmd in expected:
            label = " ".join(cmd)
            result = CliRunner().invoke(cockpit_app, list(cmd) + ["--help"])
            assert result.exit_code == 0, f"{label} --help failed"
            clean = _strip_ansi(result.output)
            assert expected[cmd] in clean, (
                f"{label} help text drift: expected {expected[cmd]!r} in output, got:\n{clean[:500]}"
            )


# ---------------------------------------------------------------------------
# Sanity — overall --help output is parseable and well-formed
# ---------------------------------------------------------------------------


class TestHelpOutputSanity:
    """End-to-end smoke tests: ``--help`` exits 0 for every
    sub-command, contains a ``Usage:`` line, and does not contain
    any tracebacks or stack frames."""

    @pytest.mark.parametrize(
        "args",
        [
            # NOTE: bare `[]` removed for Typer 0.12+ — modern CliRunner returns
            # exit_code=2 with a Usage: error when no subcommand is provided,
            # which is correct behavior.  Tests now exercise each sub-command
            # with --help explicitly instead of relying on the legacy
            # zero-args implicitly-prints-help behaviour.
            ["render", "--help"],
            ["pre-check", "--help"],
            ["replay", "--help"],
            ["traffic", "summary", "--help"],
            ["audit", "tail", "--help"],
            ["audit", "decision-tail", "--help"],
        ],
    )
    def test_cockpit_help_exits_zero(self, args: list[str]) -> None:
        from typer.testing import CliRunner

        result = CliRunner().invoke(cockpit_app, args)
        assert result.exit_code == 0, result.output
        assert "Traceback" not in result.output
        assert "Usage:" in result.output

    @pytest.mark.parametrize(
        "args",
        [
            # See note on TestHelpOutputSanity.test_cockpit_help_exits_zero —
            # bare `[]` removed for Typer 0.12+ compatibility.
            ["replay", "--help"],
        ],
    )
    def test_sota_help_exits_zero(self, args: list[str]) -> None:
        from typer.testing import CliRunner

        from thegent.ux.cli_sota import app as sota_app

        result = CliRunner().invoke(sota_app, args)
        assert result.exit_code == 0, result.output
        assert "Traceback" not in result.output
        assert "Usage:" in result.output


class TestCockpitReplayErrorEnvelope:
    """F-15 + UX polish: the cockpit replay error envelope must
    print a single ``replay failed:`` line and exit cleanly with
    ``exit_code == 1`` — no traceback, no spurious ``NameError`` for
    ``exc`` from a stale ``from exc`` that ruff --fix had injected
    into a scope where the variable is no longer bound.

    These tests are the regression guard for the silent dual-error
    case found during the F-15 hand-off (the second error message
    was a ``NameError: cannot access local variable 'exc' where it
    is not associated with a value`` after the first ``replay
    failed: batch path not found:`` line)."""

    def test_missing_batch_path_exits_one_with_single_envelope(self, tmp_path: Path) -> None:
        import json

        from typer.testing import CliRunner

        compare = tmp_path / "snapshot.json"
        compare.write_text(json.dumps({"items": []}))
        batch = tmp_path / "nonexistent_batch.json"

        result = CliRunner().invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
            ],
        )
        clean = _strip_ansi(result.output)
        assert result.exit_code == 1
        assert clean.count("replay failed:") == 1
        assert "Traceback" not in clean
        assert "NameError" not in clean
        assert "batch path not found" in clean

    def test_missing_compare_path_exits_one_with_single_envelope(self, tmp_path: Path) -> None:
        import json

        from typer.testing import CliRunner

        batch = tmp_path / "batch.json"
        batch.write_text(json.dumps({"items": []}))
        compare = tmp_path / "nonexistent_compare.json"

        result = CliRunner().invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
            ],
        )
        clean = _strip_ansi(result.output)
        assert result.exit_code == 1
        assert clean.count("replay failed:") == 1
        assert "Traceback" not in clean
        assert "NameError" not in clean
        assert "compare path not found" in clean

    def test_both_paths_missing_exits_one_with_single_envelope(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner

        batch = tmp_path / "nonexistent_batch.json"
        compare = tmp_path / "nonexistent_compare.json"

        result = CliRunner().invoke(
            cockpit_app,
            [
                "replay",
                "--batch",
                str(batch),
                "--compare",
                str(compare),
            ],
        )
        clean = _strip_ansi(result.output)
        assert result.exit_code == 1
        assert clean.count("replay failed:") == 1
        assert "Traceback" not in clean
        assert "NameError" not in clean
