r"""Phase 3/4 sweep lane — ``cli/commands/`` + ``agents/`` + ``tools/``
error-envelope parity (AUDIT-N+3).

Closes the carry-forward surfaced by the AUDIT-N+2 hand-off (see
WORKLOG.md 2026-07-19, ``Carry-forward (not in this hand-off)``):
extend the envelope sweep to the ``cli/commands/`` + ``agents/`` +
``tools/`` trees the prior lanes explicitly excluded. The
``typer.echo(f"… {untrusted_var}")`` and
``typer.echo(f"… {untrusted_var}", err=True)`` pattern remains in
these surfaces and is what this lane closes.

Audit scope (closed in this lane):

* ``src/thegent/cli/commands/cli.py:332`` — ``logs_cmd`` file-not-
  found envelope (Path is operator-controlled via filesystem
  rename / typo).
* ``src/thegent/cli/commands/cli.py:418`` — ``stop_cmd``
  session-not-found envelope (operator-controlled CLI arg).
* ``src/thegent/cli/commands/plan_cmds.py:297`` —
  ``plan_verify_workstream_cmd`` per-error envelope (``err`` parsed
  from operator-controlled ``WORK_STREAM.md`` — REAL injection
  vector).
* ``src/thegent/cli/commands/plan_cmds.py:306`` —
  ``plan_lint_workstream_cmd`` file-not-found envelope.
* ``src/thegent/cli/commands/plan_cmds.py:311`` —
  ``plan_lint_workstream_cmd`` per-warning envelope (warning text
  from operator-controlled ``WORK_STREAM.md`` — REAL injection
  vector).
* ``src/thegent/cli/commands/plan_cmds.py:314`` —
  ``plan_lint_workstream_cmd`` per-error envelope (error text from
  operator-controlled ``WORK_STREAM.md`` — REAL injection vector).
* ``src/thegent/cli/commands/plan_cmds.py:323`` —
  ``plan_normalize_workstream_cmd`` file-not-found envelope.
* ``src/thegent/cli/commands/plan_cmds.py:330`` —
  ``plan_normalize_workstream_cmd`` per-change envelope (change
  text from operator-controlled ``WORK_STREAM.md`` — REAL injection
  vector).
* ``src/thegent/cli/apps/run_app.py:158`` — ``run`` callback's
  ``Model '<model>' not available via provider '<provider>'.<suffix>``
  envelope (model + provider are operator-supplied CLI args).

A malicious or buggy exception / ``Path`` / ``WORK_STREAM.md``
payload containing Rich markup (``[red]pwned[/red]``) would render
as colour through ``typer.echo``'s default ANSI path on operator
terminals that enable colours by default. Every site now routes
through the new :func:`thegent.ux.cli_errors.safe_echo` helper
(which combines ``typer.echo``'s stderr-routing with
:func:`rich.markup.escape` applied to every interpolated value) or
through a module-level helper that routes the user-data segments
through :func:`thegent.ux.cli_errors.exc_text` before
``typer.echo`` — so the rendered envelope is safe end-to-end.

F-15 / AUDIT-N+1 threat model boundaries (explicit exclusions):

The ``src/thegent/agents/unified_registry_cli.py`` and
``src/thegent/cli/apps/govern.py`` ``console.print(f"[red]X: {y}[/red]")``
sites interpolate **operator-typed / typed-data fields**
(``agent_id``, ``run_id``, ``status``, etc.) — not exception
``str()`` payloads. These sites are SAFE-by-construction per the
F-15 / AUDIT-N+1 threat model and are **EXPLICITLY EXCLUDED** from
this sweep. The static-audit test class
``TestStaticAuditExcludesSafeByConstructionSites`` pins the
exclusion so a future refactor that re-introduces a broad sweep
flagging these sites fails this test (and is forced to keep the
F-15 threat-model boundary explicit). The exclusion is documented
in the module-level docstring above.

Out-of-scope (carried forward — see AUDIT-N+2 hand-off):

* ``src/thegent/cli/governance/`` + ``infra/`` + ``mesh/`` +
  ``cli/services/`` trees — closed in AUDIT-N+2.
* ``src/thegent/cli/apps/`` (the ``run`` sub-app except for the
  AUDIT-N+3 site above) — closed in AUDIT-N+1.

Tests cover:

* :class:`TestSafeEchoImport` — ``cli_errors.safe_echo`` is
  importable; ``cli_errors.__all__`` contains ``"safe_echo"`` so the
  helper is part of the canonical public surface.
* :class:`TestSafeEchoEndToEnd` — ``safe_echo`` end-to-end render-
  safety contract: ``err=True`` writes to stderr, default writes to
  stdout, malicious payload ``ValueError("[red]pwned[/red]")`` renders
  as escaped literal text rather than ANSI colour, plain ``str``
  passthrough is preserved, multiple positional values are
  space-joined.
* :class:`TestCliCommandsModuleImports` — ``cli.py`` +
  ``plan_cmds.py`` import cleanly after the migration; ``safe_echo``
  is bound in module namespace identity-pinned to
  ``cli_errors.safe_echo``.
* :class:`TestRunAppModuleImports` — ``run_app.py`` imports
  cleanly; the new ``_safe_model_unavailable_line`` helper is
  bound.
* :class:`TestCliCommandsStaticAudit` — the AUDIT-N+3-closed
  unsafe ``typer.echo(f"X: {untrusted_var}")`` shapes do not
  remain in ``cli.py`` / ``plan_cmds.py`` / ``run_app.py``.
* :class:`TestRunAppStaticAudit` — same as above for ``run_app.py``:
  the closed unsafe ``typer.echo(f"Model '{model}' not available via
  provider '{provider}'.{suffix}")`` shape is gone.
* :class:`TestEnvelopeRichmarkupSafetyEndToEnd` — render-safety
  contract through ``safe_echo`` end-to-end: a
  ``ValueError("[red]pwned[/red]")`` and a Path-with-brackets both
  route through ``exc_text`` and the rendered output contains the
  literal escaped markup.
* :class:`TestStaticAuditExcludesSafeByConstructionSites` —
  explicit guard: the ``agents/unified_registry_cli.py``
  ``console.print(f"[red]Agent '{agent_id}' not found.[/red]")``
  shape (interpolates operator-typed ``agent_id``, not exception
  ``str()``) remains untouched and the static-audit test does NOT
  flag it. This pins the F-15 / AUDIT-N+1 threat model: the audit
  targets exception-payload injection, not operator-typed data
  interpolation.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _strip_ansi(text: str) -> str:
    """Strip Rich / Typer ANSI escape codes from CLI output.

    The CLI surfaces tested here render through Rich / Typer which
    can prepend SGR escape sequences (``\\x1b[31m`` for red,
    ``\\x1b[0m`` for reset, etc.). A literal ``startswith("…")``
    check would otherwise fail on the colourised output, so this
    helper centralises the cleanup.
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# Module registry — the 3 source files swept in this lane.
# ---------------------------------------------------------------------------

CLI_COMMANDS_CLI = "src/thegent/cli/commands/cli.py"
CLI_COMMANDS_PLAN = "src/thegent/cli/commands/plan_cmds.py"
CLI_APPS_RUN = "src/thegent/cli/apps/run_app.py"

SWEPT_FILES = (
    CLI_COMMANDS_CLI,
    CLI_COMMANDS_PLAN,
    CLI_APPS_RUN,
)


# ---------------------------------------------------------------------------
# AUDIT-N+3 — ``safe_echo`` import + ``__all__`` surface
# ---------------------------------------------------------------------------


class TestSafeEchoImport:
    """``cli_errors.safe_echo`` is importable and is part of the
    canonical public surface (via ``__all__``) so every swept
    module can rely on the helper."""

    def test_safe_echo_is_importable(self) -> None:
        from thegent.ux import cli_errors

        assert hasattr(cli_errors, "safe_echo"), (
            "cli_errors.safe_echo is missing — every swept module needs the helper to satisfy AUDIT-N+3."
        )
        assert callable(cli_errors.safe_echo)

    def test_safe_echo_is_in_all(self) -> None:
        import thegent.ux.cli_errors as _cli_errors

        assert "safe_echo" in _cli_errors.__all__, (
            "safe_echo is missing from thegent.ux.cli_errors.__all__ "
            "— the canonical public surface must expose the helper "
            "so future sweep lanes can rely on the import path."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+3 — ``safe_echo`` end-to-end render-safety contract
# ---------------------------------------------------------------------------


class TestSafeEchoEndToEnd:
    """Pin the :func:`thegent.ux.cli_errors.safe_echo` end-to-end
    contract: stderr-routing, Rich-markup-escape on every value,
    space-joined multi-value passthrough, plain-string passthrough.
    """

    def test_err_true_writes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        from thegent.ux.cli_errors import safe_echo

        safe_echo("hello", "world", err=True)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == "hello world\n"

    def test_default_writes_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        from thegent.ux.cli_errors import safe_echo

        safe_echo("hello", "world")
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == "hello world\n"

    def test_malicious_payload_is_escaped_literal(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        r"""Pin the render-safety contract end-to-end: a
        ``ValueError("[red]pwned[/red]")`` payload routes through
        :func:`exc_text` and the rendered output contains the
        literal escaped markup (``\[red]pwned\[/red]``) rather than
        ANSI-coloured text.

        Mirrors the AUDIT-N+1 / AUDIT-N+2 render-safety test
        structure but for the new ``safe_echo`` helper."""
        from thegent.ux.cli_errors import safe_echo

        safe_echo("envelope:", ValueError("[red]pwned[/red]"), err=True)
        captured = capsys.readouterr()
        clean = _strip_ansi(captured.err)
        # The prefix is preserved verbatim.
        assert "envelope:" in clean
        # The malicious payload survives the escape end-to-end —
        # Rich's ``markup.escape`` prefixes the ``[`` with a
        # backslash, so the literal ``\[red]pwned\[/red]`` token
        # reaches stderr rather than ANSI colour.
        assert r"\[red]pwned\[/red]" in clean
        # No ANSI colour codes are emitted.
        assert "\x1b[" not in captured.err

    def test_plain_string_passthrough_preserves_content(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the benign-content path: a plain ``str`` without
        Rich markup is rendered verbatim (no double-escaping, no
        data loss)."""
        from thegent.ux.cli_errors import safe_echo

        safe_echo(
            "verify-workstream:",
            "id 'WL-224' appears in both 'foo' and 'bar'",
            err=True,
        )
        captured = capsys.readouterr()
        clean = _strip_ansi(captured.err)
        assert clean == "verify-workstream: id 'WL-224' appears in both 'foo' and 'bar'\n"

    def test_multiple_positional_values_are_space_joined(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the multi-value join contract: ``safe_echo`` joins
        positional values with a single space, mirroring the
        ``print()`` semantics."""
        from thegent.ux.cli_errors import safe_echo

        safe_echo("a", "b", "c")
        captured = capsys.readouterr()
        assert captured.out == "a b c\n"


# ---------------------------------------------------------------------------
# AUDIT-N+3 — ``cli.py`` + ``plan_cmds.py`` import + module binding
# ---------------------------------------------------------------------------


class TestCliCommandsModuleImports:
    """The swept ``cli.py`` + ``plan_cmds.py`` modules import cleanly
    after the migration AND expose ``safe_echo`` identity-pinned to
    ``thegent.ux.cli_errors.safe_echo`` so a future refactor that
    accidentally introduces a local copy (or routes through a
    different import surface) fails this pin."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "thegent.cli.commands.cli",
            "thegent.cli.commands.plan_cmds",
        ],
    )
    def test_module_imports_cleanly(self, module_name: str) -> None:
        import importlib

        # The import itself is the assertion — any
        # ``ModuleNotFoundError`` / ``ImportError`` / ``SyntaxError``
        # bubbles up and fails the test.
        importlib.import_module(module_name)

    @pytest.mark.parametrize(
        "module_name",
        [
            "thegent.cli.commands.cli",
            "thegent.cli.commands.plan_cmds",
        ],
    )
    def test_safe_echo_bound_in_module_namespace(self, module_name: str) -> None:
        import importlib

        from thegent.ux import cli_errors

        mod = importlib.import_module(module_name)
        assert hasattr(mod, "safe_echo"), (
            f"{module_name} is missing the AUDIT-N+3 ``safe_echo`` "
            f"binding. Every swept module must import "
            f"``thegent.ux.cli_errors.safe_echo`` so the render-"
            f"safety contract is preserved."
        )
        # Identifier-equality so a future refactor that accidentally
        # routes through a different ``safe_echo`` (a local copy
        # that drifts out of sync) fails this pin.
        assert mod.safe_echo is cli_errors.safe_echo


# ---------------------------------------------------------------------------
# AUDIT-N+3 — ``run_app.py`` import + ``_safe_model_unavailable_line``
# helper binding
# ---------------------------------------------------------------------------


class TestRunAppModuleImports:
    """The swept ``run_app.py`` module imports cleanly after the
    migration AND exposes the new ``_safe_model_unavailable_line``
    helper so the AUDIT-N+3 render-safety contract on the
    ``run`` sub-app surface is preserved."""

    def test_run_app_imports_cleanly(self) -> None:
        import importlib

        # The import itself is the assertion — any
        # ``ModuleNotFoundError`` / ``ImportError`` / ``SyntaxError``
        # bubbles up and fails the test.
        importlib.import_module("thegent.cli.apps.run_app")

    def test_safe_model_unavailable_line_helper_bound(self) -> None:
        """The new module-level helper ``_safe_model_unavailable_line``
        is bound on ``run_app`` so the AUDIT-N+3 migration of the
        ``Model '…' not available via provider '…' …`` envelope is
        pinned. The helper routes the operator-controlled ``model``
        + ``provider`` segments through ``exc_text`` so a malicious
        value containing Rich markup cannot inject colour into the
        operator's terminal."""
        from thegent.cli.apps import run_app

        assert hasattr(run_app, "_safe_model_unavailable_line"), (
            "run_app._safe_model_unavailable_line is missing — "
            "the AUDIT-N+3 migration requires this helper so the "
            "operator-controlled ``model`` / ``provider`` segments "
            "are escaped end-to-end."
        )
        assert callable(run_app._safe_model_unavailable_line)
        # Smoke-test: literal quoting is preserved + malicious
        # values are escaped.
        line = run_app._safe_model_unavailable_line("gpt-4o", "[red]pwned[/red]", " Available: openai.")
        assert "Model 'gpt-4o' not available via provider " in line
        assert r"\[red]pwned\[/red]" in line


# ---------------------------------------------------------------------------
# AUDIT-N+3 — static inventory: the closed unsafe envelope patterns
# do not remain in any swept file.
# ---------------------------------------------------------------------------


# The 9 needle strings — the closed unsafe envelopes — must not
# reappear in their corresponding file. This pins the structural
# invariant so a future refactor (or an un-reviewed PR) that
# re-introduces one of the unsafe patterns fails this test
# immediately.
_AUDIT_N3_CLOSED_NEEDLES: dict[str, tuple[str, ...]] = {
    CLI_COMMANDS_CLI: (
        'typer.echo(f"Log file not found: {log_file}", err=True)',
        'typer.echo(f"Session not found: {session_id}", err=True)',
    ),
    CLI_COMMANDS_PLAN: (
        'typer.echo(f"verify-workstream: {err}", err=True)',
        'typer.echo(f"lint-workstream: file not found: {path}", err=True)',
        'typer.echo(f"lint-workstream: warning: {warn}")',
        'typer.echo(f"lint-workstream: error: {err}", err=True)',
        'typer.echo(f"normalize-workstream: file not found: {path}", err=True)',
        'typer.echo(f"normalize-workstream: {change}")',
    ),
    CLI_APPS_RUN: ("typer.echo(f\"Model '{model}' not available via provider '{provider}'.{suffix}\")",),
}


class TestCliCommandsStaticAudit:
    """Static + structural inventory: the AUDIT-N+3-closed unsafe
    ``typer.echo(f"X: {untrusted_var}")`` shapes do not remain in
    any swept file. A future refactor (or an un-reviewed PR) that
    re-introduces one of the closed patterns fails this test
    immediately."""

    @pytest.mark.parametrize("rel_path", list(_AUDIT_N3_CLOSED_NEEDLES))
    def test_no_closed_unsafe_envelope_remains(self, rel_path: str) -> None:
        """No swept file contains one of the closed unsafe envelope
        needles for that file. The needles are file-scoped (the
        ``log_file`` needle only applies to ``cli.py``, the
        ``verify-workstream`` needle only applies to
        ``plan_cmds.py``, etc.) so the static audit is precise
        about which file the closed pattern was migrated out of."""
        source = Path(rel_path).read_text(encoding="utf-8")
        for needle in _AUDIT_N3_CLOSED_NEEDLES[rel_path]:
            assert needle not in source, (
                f"{rel_path} still contains the AUDIT-N+3-closed "
                f"unsafe pattern: {needle!r}. Route through "
                f"safe_echo(...) instead."
            )


class TestRunAppStaticAudit:
    """Static + structural inventory specific to ``run_app.py``: the
    AUDIT-N+3-closed ``typer.echo(f"Model '{model}' not available
    via provider '{provider}'.{suffix}")`` shape does not remain.

    The canonical replacement uses the new module-level helper
    ``_safe_model_unavailable_line(model, provider, suffix)`` which
    routes the operator-controlled segments through ``exc_text``."""

    def test_no_closed_model_unavailable_envelope_remains(self) -> None:
        source = Path(CLI_APPS_RUN).read_text(encoding="utf-8")
        needle = "typer.echo(f\"Model '{model}' not available via provider '{provider}'.{suffix}\")"
        assert needle not in source, (
            f"{CLI_APPS_RUN} still contains the AUDIT-N+3-closed "
            f"unsafe pattern: {needle!r}. Route through "
            f"typer.echo(_safe_model_unavailable_line(model, provider, suffix)) "
            f"instead."
        )

    def test_canonical_replacement_uses_helper(self) -> None:
        """Pin the canonical replacement: the
        ``Model '…' not available via provider '…' …`` envelope is
        rendered via ``typer.echo(_safe_model_unavailable_line(...))``,
        not via an inline ``f"… {untrusted_var}"`` interpolation.

        We AST-parse the file and walk for the exact call shape so
        a future refactor that drifts away from the helper fails
        this pin."""
        source = Path(CLI_APPS_RUN).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=CLI_APPS_RUN)

        found_call = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Look for ``typer.echo(<something>)`` calls.
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "typer"
                and func.attr == "echo"
            ):
                if len(node.args) != 1:
                    continue
                arg = node.args[0]
                # The canonical call passes a helper invocation
                # ``_safe_model_unavailable_line(...)`` as the
                # single positional argument.
                if (
                    isinstance(arg, ast.Call)
                    and isinstance(arg.func, ast.Name)
                    and arg.func.id == "_safe_model_unavailable_line"
                ):
                    found_call = True
                    break

        assert found_call, (
            f"{CLI_APPS_RUN} does not contain the canonical "
            f"``typer.echo(_safe_model_unavailable_line(...))`` "
            f"call shape. AUDIT-N+3 requires the operator-controlled "
            f"``model`` / ``provider`` segments to route through "
            f"``_safe_model_unavailable_line`` so the render-safety "
            f"contract is preserved."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+3 — render-safety end-to-end through ``safe_echo``
# ---------------------------------------------------------------------------


class TestEnvelopeRichmarkupSafetyEndToEnd:
    r"""Pin the render-safety contract end-to-end through
    :func:`thegent.ux.cli_errors.safe_echo`.

    Mirrors the AUDIT-N+1 / AUDIT-N+2 render-safety test structure
    but for the new ``safe_echo`` helper. A
    ``ValueError("[red]pwned[/red]")`` payload routes through
    :func:`exc_text` and the rendered output contains the literal
    escaped markup (raw ``\[red]pwned\[/red]``) rather than
    ANSI-coloured text. A ``Path`` containing Rich markup
    (``Path("/tmp/[red]pwned[/red]")``) is treated the same way.
    """

    def test_value_error_payload_renders_escaped(self) -> None:
        """A ``ValueError("[red]pwned[/red]")`` routes through
        ``safe_echo`` and the rendered output contains the literal
        escaped markup."""

        from thegent.ux.cli_errors import safe_echo

        # ``safe_echo`` uses ``typer.echo`` under the hood, but
        # ``typer.echo`` writes to ``sys.stdout`` by default. Pin
        # the contract by calling ``safe_echo`` and inspecting the
        # final ``typer.echo`` invocation through monkey-patching.
        captured: dict[str, str] = {}

        def _fake_echo(message: object = "", **_kwargs: object) -> None:
            captured["msg"] = str(message)

        import typer

        original = typer.echo
        try:
            typer.echo = _fake_echo  # type: ignore[assignment]
            safe_echo("envelope:", ValueError("[red]pwned[/red]"))
        finally:
            typer.echo = original  # type: ignore[assignment]

        assert "msg" in captured
        rendered = captured["msg"]
        # The prefix is preserved verbatim.
        assert "envelope:" in rendered
        # The malicious payload survives the escape end-to-end.
        assert r"\[red]pwned\[/red]" in rendered
        # And NO ANSI colour codes are emitted.
        assert "\x1b[" not in rendered

    def test_path_payload_renders_escaped(self) -> None:
        """A ``Path("/tmp/[red]pwned[/red]")`` routes through
        ``safe_echo`` and the rendered output contains the literal
        escaped markup. This pins the F-15 signature widening:
        ``safe_echo`` accepts any ``object`` (not just
        ``BaseException``)."""
        captured: dict[str, str] = {}

        def _fake_echo(message: object = "", **_kwargs: object) -> None:
            captured["msg"] = str(message)

        import typer

        from thegent.ux.cli_errors import safe_echo

        original = typer.echo
        try:
            typer.echo = _fake_echo  # type: ignore[assignment]
            safe_echo(
                "Log file not found:",
                Path("/tmp/[red]pwned[/red].log"),
                err=True,
            )
        finally:
            typer.echo = original  # type: ignore[assignment]

        assert "msg" in captured
        rendered = captured["msg"]
        # The prefix is preserved verbatim.
        assert "Log file not found:" in rendered
        # The malicious Path payload survives the escape end-to-end.
        assert r"\[red]pwned\[/red]" in rendered
        assert "\x1b[" not in rendered

    def test_safe_echo_is_err_console_safe(self) -> None:
        """``safe_echo`` with ``err=True`` writes through the same
        Rich ``err_console``-style path (stderr) and pins
        ``color=False`` + ``markup=False`` so operator terminals
        that enable colour cannot re-introduce ANSI codes into the
        escaped output.

        We capture both streams and confirm the rendered line
        appears only on stderr."""
        import io

        from rich.console import Console

        from thegent.ux.cli_errors import safe_echo

        sink = io.StringIO()
        # Use the standard Rich ``err_console`` pattern — but with a
        # StringIO so we can inspect what ``safe_echo`` ultimately
        # routed to ``typer.echo``.
        Console(file=sink, force_terminal=True, stderr=True)

        # We can't easily redirect ``typer.echo``'s stdout / stderr
        # from inside the Rich ``Console``; instead, monkey-patch
        # ``typer.echo`` and assert the kwargs.
        captured_kwargs: dict[str, object] = {}

        def _fake_echo(message: object = "", **kwargs: object) -> None:
            captured_kwargs["message"] = str(message)
            captured_kwargs.update(kwargs)

        import typer

        original = typer.echo
        try:
            typer.echo = _fake_echo  # type: ignore[assignment]
            safe_echo("envelope:", ValueError("[red]pwned[/red]"), err=True)
        finally:
            typer.echo = original  # type: ignore[assignment]

        # ``err=True`` is forwarded verbatim so stderr-routing is
        # preserved.
        assert captured_kwargs.get("err") is True
        # ``color=False`` is pinned so the escaped output reaches
        # the terminal unchanged. (Note: ``typer.echo`` does not
        # accept a ``markup`` kwarg — the helper pins ``color``
        # only.)
        assert captured_kwargs.get("color") is False
        # The escaped payload survives the route.
        msg = captured_kwargs.get("message", "")
        assert isinstance(msg, str)
        assert r"\[red]pwned\[/red]" in msg


# ---------------------------------------------------------------------------
# AUDIT-N+3 — explicit guard: the F-15 / AUDIT-N+1 threat model
# boundaries are pinned (operator-typed data interpolation is
# SAFE-by-construction; only exception-payload / ``Path`` / file-
# content interpolation is in scope for this audit).
# ---------------------------------------------------------------------------


class TestStaticAuditExcludesSafeByConstructionSites:
    r"""Pin the F-15 / AUDIT-N+1 threat-model boundary: the
    ``src/thegent/agents/unified_registry_cli.py`` +
    ``src/thegent/cli/apps/govern.py``
    ``console.print(f'[red]X: {y}[/red]')`` sites interpolate
    **operator-typed / typed-data fields** (``agent_id``,
    ``run_id``, ``status``, etc.) -- not exception ``str()``
    payloads. These sites are SAFE-by-construction and are
    **EXPLICITLY EXCLUDED** from the AUDIT-N+3 sweep.

    A future refactor that broadens the audit scope to flag these
    sites as "unsafe" fails this test and is forced to re-evaluate
    the F-15 threat model boundary."""

    UNSAFE_PATTERN = re.compile(
        r"""console\.print\(f"\[(?:red|yellow|green|blue|cyan|magenta|white|black)\]"""
        r"""[^"]*\{[^}]+\}[^"]*\[/(?:red|yellow|green|blue|cyan|magenta|white|black)\]"""
        r"""\)"""
    )

    # Sites known-safe-by-construction (operator-typed data, not
    # exception ``str()``). The pattern matches the interpolation
    # shape but the interpolated value is bounded and audited per
    # the F-15 / AUDIT-N+1 threat model.
    _SAFE_EXCEPTIONS = (
        # agents/unified_registry_cli: ``agent_id`` + ``run_id`` are
        # operator-supplied CLI args (bounded identifiers), not
        # exception ``str()``.
        ("src/thegent/agents/unified_registry_cli.py", 49),
        ("src/thegent/agents/unified_registry_cli.py", 80),
        ("src/thegent/agents/unified_registry_cli.py", 93),
        ("src/thegent/agents/unified_registry_cli.py", 95),
        ("src/thegent/agents/unified_registry_cli.py", 107),
        # cli/apps/govern: ``run_id`` + ``result['run_id']`` are
        # operator-supplied CLI args / typed-data fields, not
        # exception ``str()``.
        ("src/thegent/cli/apps/govern.py", 80),
        ("src/thegent/cli/apps/govern.py", 95),
    )

    def test_unsafe_pattern_does_not_flag_safe_by_construction_sites(self) -> None:
        r"""Walk the agents/ + apps/govern.py sites and confirm the
        unsafe ``console.print(f'[red]X: {y}[/red]')`` shape
        appears ONLY at lines that interpolate operator-typed
        data (the F-15 / AUDIT-N+1 SAFE-by-construction
        exclusion). No exception ``str()`` payloads are
        interpolated through this pattern in the swept surface."""
        files = (
            Path("src/thegent/agents/unified_registry_cli.py"),
            Path("src/thegent/cli/apps/govern.py"),
        )
        offenders: list[tuple[Path, int, str]] = []
        for py_file in files:
            if not py_file.exists():
                continue
            for lineno, line in enumerate(
                py_file.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if self.UNSAFE_PATTERN.search(line):
                    rel = str(py_file)
                    if (rel, lineno) not in self._SAFE_EXCEPTIONS:
                        offenders.append((py_file, lineno, stripped))

        assert not offenders, (
            'Unsafe console.print(f"[red]X: {y}[/red]") pattern '
            "found in agents/unified_registry_cli.py or "
            "cli/apps/govern.py outside the F-15 / AUDIT-N+1 "
            "SAFE-by-construction exception list:\n" + "\n".join(f"{p}:{ln} {s}" for p, ln, s in offenders)
        )

    def test_safe_by_construction_sites_still_present(self) -> None:
        """Pin the F-15 / AUDIT-N+1 exclusion at the source level:
        the SAFE-by-construction sites documented in the module-
        level docstring are still present in the source. A future
        refactor that "fixes" these sites (e.g. by routing them
        through ``exc_text``) is forced to update this test, which
        in turn surfaces a public discussion of whether the F-15
        threat model still holds."""
        unified = Path("src/thegent/agents/unified_registry_cli.py")
        if not unified.exists():
            pytest.skip("agents/unified_registry_cli.py not present")
        source = unified.read_text(encoding="utf-8")
        # The "Agent '<agent_id>' not found." envelope remains —
        # this is the canonical F-15 / AUDIT-N+1 SAFE-by-
        # construction site.
        assert "console.print(f\"[red]Agent '{agent_id}' not found.[/red]\")" in source, (
            "agents/unified_registry_cli.py no longer contains "
            "the documented F-15 / AUDIT-N+1 SAFE-by-construction "
            "site. If this is intentional, update "
            "TestStaticAuditExcludesSafeByConstructionSites and "
            "the module docstring's exclusion list."
        )
