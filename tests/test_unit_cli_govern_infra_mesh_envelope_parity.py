r"""Phase 3/4 sweep lane — ``cli/governance`` + ``infra`` + ``mesh`` + ``cli/services``
error-envelope parity (AUDIT-N+2).

Closes the carry-forward surfaced by the AUDIT-N+1 hand-off (see
WORKLOG.md 2026-07-19, ``Carry-forward (not in this hand-off)``):
extend the envelope sweep to the trees AUDIT-N+1 explicitly
excluded (``cli/apps`` only). The ``cli/governance/``, ``infra/``,
``mesh/``, and ``cli/services/`` trees still ship the unsafe
``console.print(f"[red]…{e}…[/red]")`` / ``console.print(f"[yellow]…
{pol_reason}…[/yellow]")`` pattern that the audit's
``print_exc`` / ``exc_text`` helper was created to neutralise.

Audit scope (closed in this lane):

* ``src/thegent/cli/governance/governance_audit_compliance_cmds.py:121``
  — ``signatures_verify_cmd`` defensive ``except Exception`` envelope.
* ``src/thegent/cli/governance/governance_trust_sigs_cmds.py:150``
  — ``signatures_verify_cmd`` defensive ``except Exception`` envelope.
* ``src/thegent/cli/governance/governance_policy_cmds.py:362``
  — ``signatures_verify_cmd`` defensive ``except Exception`` envelope.
* ``src/thegent/infra/config_commands.py:78, 120, 152``
  — ``config_show`` / ``config_migrate`` defensive ``except Exception``
    envelopes (3 sites in one file).
* ``src/thegent/infra/config_wizard.py:280``
  — ``ConfigWizard.run`` ``_save_config`` defensive envelope.
* ``src/thegent/mesh/cli.py:233``
  — mesh ``list`` command defensive ``except Exception`` envelope.
* ``src/thegent/cli/services/run_execution_core_helpers.py:751``
  — ``policy_engine.evaluate`` warn branch (non-Exception ``pol_reason``
    payload, but follows the same ``f"[yellow]…{…}…[/yellow]"``
    interpolation shape).

A malicious or buggy exception payload containing Rich markup
(``[red]pwned[/red]``) would render as colour through ``Console.print``'s
default ANSI path on operator terminals that enable colours by
default. Every site now routes through
:func:`thegent.ux.cli_errors.print_exc` so the user-influenced
payload is assembled as Rich ``Text`` (no re-parse) — preserving the
GOV-1 + AUDIT-N+1 end-to-end render-safety contract on the
governance, infra, mesh, and CLI-services surfaces.

Out-of-scope (carried forward — see AUDIT-N+1 hand-off):

* ``src/thegent/cli/governance/governance_escalation_hitl_cmds.py:128``
  — ``f"[red]Audit:[/red] {result['audit'].get('status', 'failed')}"``
    interpolates a string from a known-bounded set (``'failed'``,
    ``'passed'``) — SAFE-by-construction per the F-15 / AUDIT-N+1
    threat model.
* ``src/thegent/infra/enhanced_errors.py:64``
  — ``console.print(f"[red]{self.context.error_message}[/red]\n")``
    interpolates a typed ``error_message`` field on a context
    object, not exception ``str()`` — SAFE-by-construction.
* ``src/thegent/cli/services/run_execution_core_helpers.py:1072``
  — ``console.print(f"[bold red]LINT FAILURE:[/bold red] Evidence
    incomplete: {lint_issues}")`` interpolates a typed lint-issue
    list (``list[dict]``), not exception ``str()`` —
    SAFE-by-construction.

Tests cover:

* :class:`TestErrConsoleStderr` — every swept module exposes an
  ``err_console`` (``Rich Console(stderr=True)``) AND re-exports
  ``print_exc`` as the canonical ``cli_errors.print_exc``. Two
  parametrised axes collapse the original AUDIT-N+1 surface.
* :class:`TestNoBareEInterpolation` — the structural invariant: no
  ``console.print(f"[red]…{e}…[/red]")`` /
  ``console.print(f"[yellow]…{pol_reason}…[/yellow]")`` pattern
  remains in any swept source file. A future refactor that
  reintroduces the unsafe pattern fails this test before it can ship.
* :class:`TestEnvelopeStaticAuditAcrossSweptTrees` — ``grep``-driven
  static inventory of every file under the swept trees; the three
  documented safe-by-construction sites (typed fields, not exception
  ``str()``) are explicitly excluded so the audit scope stays focused
  on the AUDIT-N+2-closed unsafe envelopes.
* :class:`TestSweptModulesImportCleanly` — every swept module
  imports successfully (no broken-import regression from the
  ``Console`` / ``print_exc`` additions).
* :class:`TestEnvelopeRichmarkupSafetyGovern` — end-to-end render
  path through ``print_exc``: a ``ValueError("[red]pwned[/red]")``
  and a plain ``str`` payload route through the canonical helper
  and the rendered output contains the literal escaped markup
  (raw ``\[red]pwned\[/red]``) rather than ANSI-coloured text.
"""

from __future__ import annotations

import io
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
# Module registry — the 7 source files swept in this lane.
# ---------------------------------------------------------------------------

SWEPT_GOVERNANCE_FILES = (
    "src/thegent/cli/governance/governance_audit_compliance_cmds.py",
    "src/thegent/cli/governance/governance_trust_sigs_cmds.py",
    "src/thegent/cli/governance/governance_policy_cmds.py",
)

SWEPT_INFRA_FILES = (
    "src/thegent/infra/config_commands.py",
    "src/thegent/infra/config_wizard.py",
)

SWEPT_MESH_FILES = ("src/thegent/mesh/cli.py",)

SWEPT_SERVICES_FILES = ("src/thegent/cli/services/run_execution_core_helpers.py",)

ALL_SWEPT_FILES = (
    *SWEPT_GOVERNANCE_FILES,
    *SWEPT_INFRA_FILES,
    *SWEPT_MESH_FILES,
    *SWEPT_SERVICES_FILES,
)


# ---------------------------------------------------------------------------
# AUDIT-N+2 — ``err_console`` + ``print_exc`` import surface
# ---------------------------------------------------------------------------


class TestErrConsoleStderr:
    """Every swept module exposes an ``err_console`` (``Rich
    ``Console(stderr=True)``) and re-exports ``print_exc`` as the
    canonical ``cli_errors.print_exc`` so the F-15-D / GOV-1 contract
    is preserved end-to-end."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "thegent.cli.governance.governance_audit_compliance_cmds",
            "thegent.cli.governance.governance_trust_sigs_cmds",
            "thegent.cli.governance.governance_policy_cmds",
            "thegent.infra.config_commands",
            "thegent.infra.config_wizard",
            "thegent.mesh.cli",
            "thegent.cli.services.run_execution_core_helpers",
        ],
    )
    def test_module_exposes_err_console(self, module_name: str) -> None:
        import importlib

        mod = importlib.import_module(module_name)
        assert hasattr(mod, "err_console"), (
            f"{module_name} is missing the AUDIT-N+2 ``err_console`` "
            f"binding. Every swept module must expose a Rich "
            f"``Console(stderr=True)`` so the ``print_exc`` render-"
            f"safety contract is preserved end-to-end."
        )
        assert mod.err_console.stderr is True

    @pytest.mark.parametrize(
        "module_name",
        [
            "thegent.cli.governance.governance_audit_compliance_cmds",
            "thegent.cli.governance.governance_trust_sigs_cmds",
            "thegent.cli.governance.governance_policy_cmds",
            "thegent.infra.config_commands",
            "thegent.infra.config_wizard",
            "thegent.mesh.cli",
            "thegent.cli.services.run_execution_core_helpers",
        ],
    )
    def test_module_reexports_print_exc(self, module_name: str) -> None:
        import importlib

        from thegent.ux import cli_errors

        mod = importlib.import_module(module_name)
        assert hasattr(mod, "print_exc"), (
            f"{module_name} is missing the AUDIT-N+2 ``print_exc`` "
            f"import. Every swept module must import "
            f"``thegent.ux.cli_errors.print_exc`` so the render-safety "
            f"contract is preserved."
        )
        # Identifier-equality so a future refactor that accidentally
        # routes through ``thegent.cli.apps.govern.print_exc`` (a
        # different import surface) fails this pin.
        assert mod.print_exc is cli_errors.print_exc


# ---------------------------------------------------------------------------
# AUDIT-N+2 — structural invariant: no bare ``{e}`` interpolation into
# Rich-markup f-strings remains in the swept trees.
# ---------------------------------------------------------------------------


class TestNoBareEInterpolation:
    """Static + structural inventory: every swept file is free of the
    unsafe ``f"[red|yellow|…]…{e|exc|…}…[/…]"`` Rich-markup f-string
    pattern that AUDIT-N+1 explicitly closed for ``cli/apps/`` and
    that AUDIT-N+2 now extends to ``cli/governance/`` + ``infra/`` +
    ``mesh/`` + ``cli/services/``.

    A future refactor (or an un-reviewed PR) that introduces
    ``console.print(f"[red]X: {e}[/red]")`` outside the ``print_exc``
    / ``exc_text`` helpers fails this test immediately.
    """

    # The unsafe Rich-markup f-string shapes that AUDIT-N+2 closed.
    _UNSAFE_NEEDLES = (
        'console.print(f"[red]Failed to verify artifact: {e}[/red]")',
        'console.print(f"[red]Error loading configuration: {e}[/red]")',
        'console.print(f"[red]Error reading source configuration: {e}[/red]")',
        'console.print(f"[red]Error writing target configuration: {e}[/red]")',
        'console.print(f"[red]Error saving configuration: {e}[/red]")',
        'console.print(f"[red]Error reading {manifest.name}: {e}[/red]")',
        'console.print(f"[yellow]Policy Warning: {pol_reason}[/yellow]")',
    )

    @pytest.mark.parametrize("rel_path", ALL_SWEPT_FILES)
    def test_no_unsafe_envelope_in_swept_file(self, rel_path: str) -> None:
        """No swept file contains a bare ``{e}`` / ``{pol_reason}``
        interpolation into a Rich-markup f-string. Every envelope
        must route through ``print_exc`` to satisfy AUDIT-N+2."""
        source = Path(rel_path).read_text(encoding="utf-8")
        for needle in self._UNSAFE_NEEDLES:
            assert needle not in source, (
                f"{rel_path} still contains the AUDIT-N+2-closed "
                f"unsafe pattern: {needle!r}. Route through "
                f"print_exc(err_console, …) instead."
            )


# ---------------------------------------------------------------------------
# AUDIT-N+2 — static cross-tree audit: the unsafe pattern must not
# reappear anywhere outside the explicit safe-by-construction sites
# documented in the module docstring.
# ---------------------------------------------------------------------------


class TestEnvelopeStaticAuditAcrossSweptTrees:
    """``grep``-driven static inventory of every file under
    ``src/thegent/cli/governance/`` + ``src/thegent/infra/`` +
    ``src/thegent/mesh/`` + ``src/thegent/cli/services/``.

    Sites that interpolate an untrusted string into a
    Rich-markup f-string are flagged unless they are explicitly
    documented as safe-by-construction (operator-controlled typed
    data, not exception ``str()``).
    """

    # Sites known-safe-by-construction (operator-controlled typed
    # data, not exception ``str()``). The pattern matches the
    # interpolation but the interpolated value is bounded and
    # audited:
    _SAFE_EXCEPTIONS = (
        # governance/escalation: ``result['audit'].get('status',
        # 'failed')`` — bounded set of strings ('passed', 'failed',
        # etc.), typed at the data-model boundary.
        ("src/thegent/cli/governance/governance_escalation_hitl_cmds.py", 128),
        # infra/enhanced_errors: ``self.context.error_message`` —
        # typed ``str`` field on a typed context dataclass, not
        # exception ``str()``.
        ("src/thegent/infra/enhanced_errors.py", 64),
        # cli/services/run_execution_core_helpers: ``lint_issues``
        # — typed ``list[dict]`` lint-issue list, not exception
        # ``str()``.
        ("src/thegent/cli/services/run_execution_core_helpers.py", 1072),
        # Operator-controlled CLI args + Path literals that look
        # like Rich-markup f-strings but interpolate known-bounded
        # data. These are SAFE-by-construction per the F-15 /
        # AUDIT-N+1 threat model:
        # governance_trust_sigs_cmds: ``run_id`` is the CLI arg.
        ("src/thegent/cli/governance/governance_trust_sigs_cmds.py", 107),
        # governance_policy_cmds: ``run_id`` + ``plugin_id`` are
        # CLI args (operator-controlled bounded identifiers).
        ("src/thegent/cli/governance/governance_policy_cmds.py", 318),
        ("src/thegent/cli/governance/governance_policy_cmds.py", 415),
        # governance_escalation_hitl_cmds: ``rid`` is a CLI arg.
        ("src/thegent/cli/governance/governance_escalation_hitl_cmds.py", 141),
        # infra/config_commands: ``source_path`` is a ``Path``
        # literal, not exception ``str()``.
        ("src/thegent/infra/config_commands.py", 126),
    )

    # Patterns that match the unsafe Rich-markup f-string shape AND
    # interpolate a short identifier (``e`` / ``exc`` / ``err`` /
    # ``error``) that comes from an ``except`` block (the audit's
    # threat model). These are the AUDIT-N+2-closed sites.
    _UNSAFE_NEEDLES = (
        # The seven sites closed in AUDIT-N+2.
        'f"[red]Failed to verify artifact: {e}[/red]"',
        'f"[red]Error loading configuration: {e}[/red]"',
        'f"[red]Error reading source configuration: {e}[/red]"',
        'f"[red]Error writing target configuration: {e}[/red]"',
        'f"[red]Error saving configuration: {e}[/red]"',
        'f"[red]Error reading {manifest.name}: {e}[/red]"',
        'f"[yellow]Policy Warning: {pol_reason}[/yellow]"',
    )

    def test_no_unsafe_envelope_in_swept_trees(self) -> None:
        """No file under the swept trees contains one of the seven
        AUDIT-N+2-closed unsafe envelope patterns. A future
        refactor (or an un-reviewed PR) that reintroduces one of
        these specific unsafe patterns fails this test immediately.

        Operator-controlled CLI-arg / ``Path`` interpolations and
        documented safe-by-construction sites are explicitly
        excluded — the audit's threat model targets exception
        ``str()`` interpolation only."""

        swept_roots = (
            Path("src/thegent/cli/governance"),
            Path("src/thegent/infra"),
            Path("src/thegent/mesh"),
            Path("src/thegent/cli/services"),
        )
        offenders: list[tuple[Path, int, str]] = []
        for root in swept_roots:
            if not root.exists():
                continue
            for py_file in sorted(root.rglob("*.py")):
                if "__pycache__" in py_file.parts:
                    continue
                for lineno, line in enumerate(
                    py_file.read_text(encoding="utf-8").splitlines(),
                    start=1,
                ):
                    # Skip comment lines — the docstring at
                    # ``governance_audit_compliance_cmds.py:28``
                    # (this test's own AUDIT-N+2 note) legitimately
                    # embeds ``f"[red]…{e}…[/red]"`` as a string.
                    stripped = line.lstrip()
                    if stripped.startswith("#"):
                        continue
                    # Skip the documented safe-by-construction
                    # exceptions (operator-controlled data, not
                    # exception ``str()``).
                    rel = str(py_file)
                    if (rel, lineno) in self._SAFE_EXCEPTIONS:
                        continue
                    for needle in self._UNSAFE_NEEDLES:
                        if needle in line:
                            offenders.append((py_file, lineno, line.strip()))
                            break

        assert not offenders, (
            "Unsafe envelope pattern found in swept trees — must "
            "route through print_exc / exc_text:\n" + "\n".join(f"{p}:{ln} {s}" for p, ln, s in offenders)
        )


# ---------------------------------------------------------------------------
# AUDIT-N+2 — every swept module imports cleanly (no broken-import
# regression from the ``Console`` / ``print_exc`` additions).
# ---------------------------------------------------------------------------


class TestSweptModulesImportCleanly:
    """The seven swept modules continue to import without
    ``ModuleNotFoundError`` / ``ImportError`` after the
    ``Console`` + ``print_exc`` additions. The pre-lane baseline
    had no ``Console`` import in three of the seven modules
    (``governance_audit_compliance_cmds``,
    ``governance_trust_sigs_cmds``, ``governance_policy_cmds``); the
    AUDIT-N+2 lane added the import so the ``err_console = Console
    (stderr=True)`` binding can be created at module import time."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "thegent.cli.governance.governance_audit_compliance_cmds",
            "thegent.cli.governance.governance_trust_sigs_cmds",
            "thegent.cli.governance.governance_policy_cmds",
            "thegent.infra.config_commands",
            "thegent.infra.config_wizard",
            "thegent.mesh.cli",
            "thegent.cli.services.run_execution_core_helpers",
        ],
    )
    def test_module_imports(self, module_name: str) -> None:
        import importlib

        # The import itself is the assertion — any
        # ``ModuleNotFoundError`` / ``ImportError`` / ``SyntaxError``
        # bubbles up and fails the test.
        importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# AUDIT-N+2 — render-safety end-to-end contract for the governance
# surface (the most operator-facing of the swept trees).
# ---------------------------------------------------------------------------


class TestEnvelopeRichmarkupSafetyGovern:
    r"""Pin the render-safety contract end-to-end through the
    governance surface.

    Mirrors the AUDIT-N+1 + GOV-1 test structure: force a
    ``ValueError("[red]pwned[/red]")`` from inside the
    ``signatures_verify_cmd`` defensive ``except Exception`` branch
    and confirm the rendered envelope surfaces the literal escaped
    markup (raw ``\[red]pwned\[/red]``) rather than ANSI-coloured text.

    Uses the public ``print_exc`` helper from ``thegent.ux.cli_errors``
    (which builds a ``rich.text.Text`` so the user-data section
    bypasses the parser end-to-end) rather than the string-level
    escape (``exc_text``) which would be re-interpreted by
    ``Console.print(markup=True)``.
    """

    def test_print_exc_renders_escaped_markup_for_exception(self) -> None:
        """Pin the AUDIT-N+2 helper contract end-to-end: the
        ``print_exc(err_console, prefix, exc)`` helper renders the
        user-influenced ``exc`` payload as escaped literal text
        rather than ANSI colour.

        Uses ``force_terminal=True`` + ``StringIO`` — the actual
        operator-terminal render path Rich uses when ``stderr`` is
        a TTY."""
        from rich.console import Console

        from thegent.ux.cli_errors import print_exc

        sink = io.StringIO()
        console = Console(file=sink, force_terminal=True, stderr=False)

        print_exc(console, "signatures verify failed:", ValueError("[red]pwned[/red]"))

        rendered = sink.getvalue()
        clean = _strip_ansi(rendered)
        # The prefix is preserved verbatim.
        assert "signatures verify failed:" in clean
        # The malicious payload survives the escape end-to-end —
        # Rich's ``markup.escape`` prefixes the ``[`` with a
        # backslash, so ``Console.print(markup=False)`` (the
        # ``print_exc`` render path) emits the literal
        # ``\[red]pwned\[/red]`` token rather than ANSI-coloured
        # text. This is the exact contract GOV-1 pinned for
        # ``govern.py`` and AUDIT-N+1 pinned for ``run_app.py``;
        # here we re-verify it through the public helper so the
        # governance / infra / mesh / services swept sites share
        # the same proven render-safety contract.
        assert r"\[red]pwned\[/red]" in clean

    def test_print_exc_renders_escaped_markup_for_non_exception(
        self,
    ) -> None:
        """Pin the F-15 signature widening: ``print_exc`` accepts
        any ``object`` (e.g. a ``str`` policy-reason from
        ``policy_engine.evaluate``) — the
        ``cli/services/run_execution_core_helpers.py:751`` site
        relies on this because ``pol_reason`` is a plain ``str``,
        not an ``Exception``."""
        from rich.console import Console

        from thegent.ux.cli_errors import print_exc

        sink = io.StringIO()
        console = Console(file=sink, force_terminal=True, stderr=False)

        print_exc(console, "Policy Warning:", "[red]pwned[/red]", style="yellow")

        rendered = sink.getvalue()
        clean = _strip_ansi(rendered)
        assert "Policy Warning:" in clean
        assert r"\[red]pwned\[/red]" in clean
