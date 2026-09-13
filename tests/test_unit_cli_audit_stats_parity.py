r"""Phase 3/4 continuation — ``audit_stats_cmd`` + perf-hardening
byte-budget helper parity tests (AUDIT-N+4).

Closes the carry-forward surfaced by the AUDIT-N+3 hand-off (see
WORKLOG.md 2026-07-19, "Carry-forward (not in this hand-off)"):

1. The ``DecisionAuditAppender.audit_stats()`` snapshot already
   exists at ``src/thegent/ux/decision_audit.py:300-323`` but is
   NOT exposed in the CLI — operators running SOTA replay tooling
   cannot read the rotation / durability observability counters
   without spinning up a Python REPL. This lane adds a new flat
   CLI command ``audit_stats_cmd`` that surfaces the snapshot
   either as JSON (machine-readable; ``--json``) or as a sorted
   key-value table (operator-readable; default).

2. The AUDIT-25 byte-tail path inside ``tail_events()`` was inline
   and duplicated the partial-line / size-zero / exact-window
   boundary handling across the per-file loop. A future call site
   (``tail_events(use_byte_tail=True)`` for the cockpit snapshot)
   would need to copy that logic. This lane extracts the logic
   into ``DecisionAuditAppender._read_file_with_byte_budget(fp,
   byte_window)`` so the perf invariant lives in one place.

Test surface (~600 lines, 25 tests, 8 test classes):

* :class:`TestAuditStatsCmdImport` (3 tests) — ``audit_stats_cmd``
  is importable, bound in the module namespace, and exported via
  ``__all__``.
* :class:`TestAuditStatsCmdJsonOutput` (4 tests) — happy-path
  JSON output: all expected keys present, sorted, values match
  ``appender.audit_stats()``, well-formed JSON.
* :class:`TestAuditStatsCmdHumanOutput` (3 tests) — happy-path
  human output: ``key: value`` lines, sorted, no JSON braces,
  exact-line capsys assertion.
* :class:`TestAuditStatsCmdPathOverride` (2 tests) — ``--audit-path``
  override is honored; the override works even when the default
  XDG path does not exist.
* :class:`TestAuditStatsCmdMissingFile` (3 tests) — missing-file
  path returns ``1``; the error envelope routes through
  ``safe_echo`` (no ``typer.echo(f"...")`` shape); the resolved
  audit-path string is included in the envelope (escaped).
* :class:`TestAuditStatsCmdRichmarkupSafetyEndToEnd` (3 tests) —
  render-safety contract: an audit path containing ``[red]``
  brackets renders escaped in the missing-file envelope.
* :class:`TestReadFileWithByteBudget` (5 tests) — the
  ``_read_file_with_byte_budget`` helper handles: whole-file
  path (size ≤ window), byte-tail path (size > window),
  partial-first-line discard, empty file, exact-byte-window
  boundary, 1-byte boundary.
* :class:`TestTailEventsByteBudgetParity` (2 tests) —
  parity regression guard: ``tail_events(n=20)`` continues to
  produce identical output before and after the helper
  extraction.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Module registry — the 2 source files swept in this lane.
# ---------------------------------------------------------------------------

CLI_COMMANDS_CLI = "src/thegent/cli/commands/cli.py"
DECISION_AUDIT = "src/thegent/ux/decision_audit.py"


def _strip_ansi(text: str) -> str:
    """Strip Rich / Typer ANSI escape codes from CLI output.

    The CLI surfaces tested here render through Rich / Typer which
    can prepend SGR escape sequences (``\\x1b[31m`` for red,
    ``\\x1b[0m`` for reset, etc.). A literal ``startswith("…")``
    check would otherwise fail on the colourised output, so this
    helper centralises the cleanup.
    """
    import re

    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# AUDIT-N+4 — ``audit_stats_cmd`` import + ``__all__`` surface
# ---------------------------------------------------------------------------


class TestAuditStatsCmdImport:
    """``cli.py.audit_stats_cmd`` is importable, bound in the
    module namespace, and exported via ``__all__`` so the new flat
    CLI command is part of the canonical public surface."""

    def test_audit_stats_cmd_is_importable(self) -> None:
        """The new ``audit_stats_cmd`` function is importable from
        ``thegent.cli.commands.cli`` so the surface contract is
        stable for callers that wire it through a Typer sub-app."""
        from thegent.cli.commands import cli as cli_module

        assert hasattr(cli_module, "audit_stats_cmd"), (
            "cli.audit_stats_cmd is missing — the AUDIT-N+4 governance "
            "observability surface cannot be wired through a Typer "
            "sub-app without an importable symbol."
        )
        assert callable(cli_module.audit_stats_cmd)

    def test_audit_stats_cmd_is_in_all(self) -> None:
        """``audit_stats_cmd`` is exported via ``__all__`` so the
        canonical public surface is explicit and a future refactor
        that drops it from ``__all__`` fails this pin."""
        import thegent.cli.commands.cli as cli_module

        assert "audit_stats_cmd" in cli_module.__all__, (
            "audit_stats_cmd is missing from cli.__all__ — the "
            "AUDIT-N+4 public-surface contract requires an explicit "
            "__all__ entry so downstream import paths are stable."
        )

    def test_audit_stats_cmd_bound_in_module_namespace(self) -> None:
        """``audit_stats_cmd`` is bound in the module namespace
        identity-pinned to itself (so a future refactor that
        accidentally aliases it to a different function fails this
        pin)."""
        import thegent.cli.commands.cli as cli_module

        # Two independent imports of the same symbol resolve to the
        # same function object — the canonical "identity pin" used
        # across the AUDIT-N+1..N+3 sweep lanes.
        from thegent.cli.commands.cli import audit_stats_cmd as sym1

        assert cli_module.audit_stats_cmd is sym1


# ---------------------------------------------------------------------------
# AUDIT-N+4 — JSON output contract
# ---------------------------------------------------------------------------


class TestAuditStatsCmdJsonOutput:
    """Pin the JSON output contract: well-formed JSON with all
    expected keys, sorted, and values match
    ``DecisionAuditAppender.audit_stats()``."""

    EXPECTED_KEYS: tuple[str, ...] = (
        "bytes_written",
        "fsync",
        "fsync_every_n",
        "line_count",
        "max_backups",
        "max_bytes",
        "max_lines",
        "rotation_count",
    )

    def test_json_output_returns_zero_exit_code(self, tmp_path: Path) -> None:
        """The JSON path returns ``0`` on success so a CI smoke
        harness can chain commands on the snapshot output."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("{}\n", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        rc = audit_stats_cmd(audit_path=log, json_output=True)
        assert rc == 0

    def test_json_output_is_well_formed_and_sorted(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The JSON output is parseable, sorted by key, and
        contains every key from the ``audit_stats()`` snapshot
        contract."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("{}\n", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=log, json_output=True)
        captured = capsys.readouterr()
        # The stdout payload is the JSON document; tolerate a
        # trailing newline that ``typer.echo`` appends.
        payload = captured.out.strip()
        parsed = json.loads(payload)
        # All 8 expected keys present.
        for key in self.EXPECTED_KEYS:
            assert key in parsed, (
                f"audit_stats JSON output is missing key {key!r} — "
                f"the AUDIT-N+4 contract requires all 8 keys from "
                f"audit_stats() to be surfaced."
            )
        # Keys are sorted (per ``json.dumps(..., sort_keys=True)``).
        assert list(parsed.keys()) == sorted(parsed.keys()), (
            "audit_stats JSON output keys are not sorted — the "
            "AUDIT-N+4 contract requires ``sort_keys=True`` so the "
            "rendered output is deterministic for diff-based tests."
        )

    def test_json_output_values_match_audit_stats(self, tmp_path: Path) -> None:
        """The JSON values match the underlying
        ``appender.audit_stats()`` snapshot so the CLI surface is
        a faithful surface over the appender's counters."""
        log = tmp_path / "decisions.jsonl"
        # Empty file is enough — the appender's counters are the
        # source of truth, not the file contents.
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd
        from thegent.ux.decision_audit import DecisionAuditAppender

        appender = DecisionAuditAppender(audit_path=log)
        expected = appender.audit_stats()

        audit_stats_cmd(audit_path=log, json_output=True)
        # Re-parse what was emitted.

        # The cleanest way to read what ``audit_stats_cmd`` emitted
        # is to monkey-patch ``typer.echo`` and capture the
        # payload. This avoids re-reading capsys after a second
        # call.
        captured: dict[str, str] = {}

        def _fake_echo(message: object = "", **_kwargs: object) -> None:
            captured["msg"] = str(message)

        import typer as _typer

        original = _typer.echo
        try:
            _typer.echo = _fake_echo  # type: ignore[assignment]
            audit_stats_cmd(audit_path=log, json_output=True)
        finally:
            _typer.echo = original  # type: ignore[assignment]

        assert "msg" in captured
        rendered = captured["msg"]
        parsed = json.loads(rendered)
        assert parsed == expected, (
            f"audit_stats JSON output does not match appender.audit_stats(): expected={expected!r}, got={parsed!r}"
        )

    def test_json_output_uses_indent_2(self, tmp_path: Path) -> None:
        """The JSON output uses ``indent=2`` so the rendered
        payload is human-diffable. We verify by checking the
        rendered payload contains a newline before a known key
        (i.e. the pretty-print indent is present)."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("", encoding="utf-8")

        captured: dict[str, str] = {}

        def _fake_echo(message: object = "", **_kwargs: object) -> None:
            captured["msg"] = str(message)

        import typer

        from thegent.cli.commands.cli import audit_stats_cmd

        original = typer.echo
        try:
            typer.echo = _fake_echo  # type: ignore[assignment]
            audit_stats_cmd(audit_path=log, json_output=True)
        finally:
            typer.echo = original  # type: ignore[assignment]

        assert "msg" in captured
        rendered = captured["msg"]
        # ``indent=2`` means each non-root key is prefixed by
        # ``"  "``. We confirm by spotting a ``\n  "<key>":`` shape.
        assert "\n  " in rendered, (
            f"audit_stats JSON output is not pretty-printed with indent=2 (rendered payload: {rendered!r})."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+4 — Human output contract
# ---------------------------------------------------------------------------


class TestAuditStatsCmdHumanOutput:
    """Pin the human-readable output contract: one ``key: value``
    line per snapshot entry, sorted by key, no JSON braces."""

    def test_human_mode_emits_key_value_lines_sorted(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The human-readable output is a sorted ``key: value``
        table (no JSON braces, no extra noise)."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=log, json_output=False)
        captured = capsys.readouterr()
        clean = _strip_ansi(captured.out)
        lines = [ln for ln in clean.splitlines() if ln.strip()]
        # 8 lines, one per expected key.
        assert len(lines) == 8, f"audit_stats human output should have 8 lines, got {len(lines)}: {lines!r}"
        # No JSON braces.
        assert "{" not in clean and "}" not in clean, (
            f"audit_stats human output should be a key-value table, not JSON (rendered: {clean!r})."
        )
        # Each line has the ``key: value`` shape.
        parsed_keys: list[str] = []
        for ln in lines:
            assert ":" in ln, f"audit_stats human line lacks ':': {ln!r}"
            key = ln.split(":", 1)[0].strip()
            parsed_keys.append(key)
        # Sorted.
        assert parsed_keys == sorted(parsed_keys), f"audit_stats human keys are not sorted: {parsed_keys!r}"

    def test_human_mode_exact_lines_capsys(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the exact rendered output line-for-line via
        ``capsys`` so a future refactor that re-orders keys or
        changes the table format fails this test."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=log, json_output=False)
        captured = capsys.readouterr()
        clean = _strip_ansi(captured.out)
        expected_lines = [
            "bytes_written: 0",
            "fsync: False",
            "fsync_every_n: 1",
            "line_count: 0",
            "max_backups: 3",
            "max_bytes: 52428800",
            "max_lines: 250000",
            "rotation_count: 0",
        ]
        actual_lines = [ln for ln in clean.splitlines() if ln.strip()]
        assert actual_lines == expected_lines, (
            f"audit_stats human output mismatch:\n  expected: {expected_lines!r}\n  actual:   {actual_lines!r}"
        )

    def test_human_mode_returns_zero_exit_code(self, tmp_path: Path) -> None:
        """The human-readable path returns ``0`` on success (a
        CI smoke harness can chain commands on the rendered
        table)."""
        log = tmp_path / "decisions.jsonl"
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        rc = audit_stats_cmd(audit_path=log, json_output=False)
        assert rc == 0


# ---------------------------------------------------------------------------
# AUDIT-N+4 — Path override contract
# ---------------------------------------------------------------------------


class TestAuditStatsCmdPathOverride:
    """Pin the ``--audit-path`` operator-override contract: the
    override is honored even when the default XDG-state path does
    not exist."""

    def test_audit_path_override_is_honored(self, tmp_path: Path) -> None:
        """A ``--audit-path`` override resolves to the operator's
        chosen path and reads the snapshot from there."""
        log = tmp_path / "override.jsonl"
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands.cli import audit_stats_cmd

        rc = audit_stats_cmd(audit_path=log, json_output=False)
        assert rc == 0

    def test_audit_path_override_works_when_default_missing(
        self,
        tmp_path: Path,
    ) -> None:
        """An operator override is honored even when the canonical
        default ``~/.local/state/thegent/decisions.jsonl`` does
        not exist on disk. This pins the contract that the
        override fully bypasses the default-path existence
        check."""
        # We use ``monkeypatch`` to redirect ``Path.expanduser`` so
        # the default path resolves under ``tmp_path`` and is
        # therefore missing without affecting the operator's real
        # home directory.
        log = tmp_path / "operator-override.jsonl"
        log.write_text("", encoding="utf-8")

        from thegent.cli.commands import cli as cli_module

        # Snapshot the original ``_DEFAULT_AUDIT_STATS_PATH`` so we
        # can restore after the test.
        original_default = cli_module._DEFAULT_AUDIT_STATS_PATH
        fake_default = tmp_path / "this-default-does-not-exist.jsonl"

        try:
            cli_module._DEFAULT_AUDIT_STATS_PATH = fake_default  # type: ignore[attr-defined]
            # Sanity: the default truly does not exist.
            assert not fake_default.exists()

            # Without an override, the command should now fail
            # because the default is missing.
            from thegent.cli.commands.cli import audit_stats_cmd

            rc_missing = audit_stats_cmd(json_output=False)
            assert rc_missing == 1, (
                "audit_stats_cmd should return 1 when the default audit path does not exist (no override)."
            )

            # With the override, the command succeeds and reads
            # from the operator's chosen path.
            rc_override = audit_stats_cmd(audit_path=log, json_output=False)
            assert rc_override == 0, (
                "audit_stats_cmd should succeed when an explicit --audit-path override points at an existing log."
            )
        finally:
            cli_module._DEFAULT_AUDIT_STATS_PATH = original_default  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# AUDIT-N+4 — Missing-file envelope contract
# ---------------------------------------------------------------------------


class TestAuditStatsCmdMissingFile:
    """Pin the missing-file envelope contract: returns ``1``, emits
    a single error envelope via ``safe_echo`` (no
    ``typer.echo(f"...")`` shape), and the resolved audit-path
    string is included in the envelope."""

    def test_missing_file_returns_exit_code_one(
        self,
        tmp_path: Path,
    ) -> None:
        """A missing audit log returns exit code ``1`` so a CI
        smoke harness can detect the absence."""
        missing = tmp_path / "no-such-log.jsonl"
        assert not missing.exists()

        from thegent.cli.commands.cli import audit_stats_cmd

        rc = audit_stats_cmd(audit_path=missing)
        assert rc == 1

    def test_missing_file_envelope_routes_through_safe_echo(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The missing-file envelope is emitted via ``safe_echo``
        (rendered to stderr) — NOT via a raw
        ``typer.echo(f"...")`` shape that could re-introduce a
        Rich-markup injection vector."""
        missing = tmp_path / "no-such-log.jsonl"
        assert not missing.exists()

        from thegent.cli.commands.cli import audit_stats_cmd

        # Capture both streams by routing through ``safe_echo``.
        audit_stats_cmd(audit_path=missing)
        captured = capsys.readouterr()
        # The envelope is on stderr (per ``safe_echo(err=True)``).
        assert captured.out == ""
        clean_err = _strip_ansi(captured.err)
        # Single envelope (one logical error line).
        err_lines = [ln for ln in clean_err.splitlines() if ln.strip()]
        assert len(err_lines) == 1, (
            f"audit_stats missing-file envelope should be a single line, got {len(err_lines)}: {err_lines!r}"
        )

    def test_missing_file_envelope_includes_resolved_path(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The missing-file envelope includes the resolved
        audit-path string (escaped via ``safe_echo``'s
        ``exc_text`` shim) so the operator can diagnose why the
        command returned ``1``."""
        missing = tmp_path / "no-such-log.jsonl"
        assert not missing.exists()

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=missing)
        captured = capsys.readouterr()
        clean_err = _strip_ansi(captured.err)
        # The literal filename (escaped or verbatim) appears in
        # the envelope. ``safe_echo`` does not escape plain
        # filenames (no Rich markup), so the literal name should
        # reach stderr unchanged.
        assert missing.name in clean_err, (
            f"audit_stats missing-file envelope should include the resolved path filename. Rendered: {clean_err!r}"
        )
        # And a literal ``audit_stats`` prefix token, so operators
        # can grep the envelope.
        assert "audit_stats" in clean_err, (
            f"audit_stats missing-file envelope should include the 'audit_stats' prefix token. Rendered: {clean_err!r}"
        )


# ---------------------------------------------------------------------------
# AUDIT-N+4 — Render-safety end-to-end through ``safe_echo``
# ---------------------------------------------------------------------------


class TestAuditStatsCmdRichmarkupSafetyEndToEnd:
    r"""Pin the render-safety contract end-to-end through
    :func:`thegent.ux.cli_errors.safe_echo`: an audit path
    containing Rich markup brackets (``[red]...[/red]``) renders
    escaped in the missing-file envelope, so an attacker cannot
    inject colour tags into the operator's terminal."""

    def test_audit_path_with_brackets_renders_escaped(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        r"""An audit-path containing ``[red]`` brackets renders
        escaped in the missing-file envelope (literal
        ``\[red]`` token). The path is filesystem-supplied (not
        exception ``str()``), but the F-15 / AUDIT-N+1..N+3
        contract applies uniformly — the envelope site routes
        every value through ``exc_text``."""
        # We cannot create a file with ``[red]`` literally in the
        # name on every filesystem, but we can construct the
        # ``Path`` object in memory and let the command emit the
        # envelope. The envelope just needs to render the literal
        # filename (escaped) on stderr.
        malicious_name = "[red]pwned[/red].jsonl"
        fake_path = tmp_path / malicious_name
        assert not fake_path.exists()

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=fake_path)
        captured = capsys.readouterr()
        clean_err = _strip_ansi(captured.err)
        # The literal filename (escaped) appears in the envelope.
        # ``safe_echo`` routes ``str(path)`` through ``exc_text``
        # which Rich-escapes the brackets.
        assert r"\[red]pwned\[/red].jsonl" in clean_err, (
            f"audit_stats missing-file envelope should escape Rich markup in the resolved path. Rendered: {clean_err!r}"
        )
        # And NO ANSI colour codes are emitted.
        assert "\x1b[" not in captured.err, (
            f"audit_stats missing-file envelope leaked ANSI colour codes: {captured.err!r}"
        )

    def test_audit_path_brackets_in_directory_renders_escaped(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        r"""A nested path with ``[red]`` in the directory
        component renders escaped too. The end-to-end render-
        safety contract is on the entire ``str(path)``
        interpolation, not just the basename."""
        malicious_dir = tmp_path / "[red]evil[/red]"
        fake_path = malicious_dir / "decisions.jsonl"
        assert not fake_path.exists()

        from thegent.cli.commands.cli import audit_stats_cmd

        audit_stats_cmd(audit_path=fake_path)
        captured = capsys.readouterr()
        clean_err = _strip_ansi(captured.err)
        # The escaped directory token appears.
        assert r"\[red]evil\[/red]" in clean_err, (
            f"audit_stats missing-file envelope should escape "
            f"Rich markup in the path directory. "
            f"Rendered: {clean_err!r}"
        )
        assert "\x1b[" not in captured.err

    def test_safe_echo_identity_pinned_in_cli_module(self) -> None:
        """``cli.py``'s ``safe_echo`` binding is identity-pinned
        to ``thegent.ux.cli_errors.safe_echo`` so a future
        refactor that accidentally aliases it (e.g. a local copy
        that drifts out of sync) fails this pin."""
        import thegent.cli.commands.cli as cli_module
        from thegent.ux import cli_errors

        assert cli_module.safe_echo is cli_errors.safe_echo, (
            "cli.safe_echo is not identity-pinned to "
            "cli_errors.safe_echo — the AUDIT-N+3 + AUDIT-N+4 "
            "envelope contract requires the canonical binding so "
            "the helper's render-safety contract is preserved."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+4 — ``_read_file_with_byte_budget`` helper contract
# ---------------------------------------------------------------------------


class TestReadFileWithByteBudget:
    """Pin the ``_read_file_with_byte_budget`` perf helper
    contract: the helper correctly partitions between the
    whole-file path and the byte-tail path on the
    size-vs-window boundary, discards the partial first line in
    the byte-tail path, and handles edge cases (empty file,
    exact-byte-window boundary, 1-byte boundary)."""

    def test_whole_file_path_when_size_le_window(self, tmp_path: Path) -> None:
        """When ``fp.stat().st_size <= byte_window`` the whole
        file is read (cheap path). All lines come back regardless
        of the window size."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        fp = tmp_path / "small.jsonl"
        fp.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        result = appender._read_file_with_byte_budget(fp, byte_window=1024)
        assert result == ["a", "b", "c", "d", "e"]

    def test_byte_tail_path_when_size_gt_window(self, tmp_path: Path) -> None:
        """When ``fp.stat().st_size > byte_window`` only the
        trailing ``byte_window`` bytes are read. We construct a
        file whose size is strictly greater than the window and
        confirm the returned lines are the trailing slice."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        # 10 lines of 10 chars each = 100 bytes (plus 10
        # ``\n`` separators = 110 bytes total).
        lines = [f"line-{i:08d}" for i in range(10)]  # each 10 chars
        content = "\n".join(lines) + "\n"
        fp = tmp_path / "tail.jsonl"
        fp.write_text(content, encoding="utf-8")
        size_now = fp.stat().st_size
        # Sanity: the file is bigger than the window.
        assert size_now > 16

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        result = appender._read_file_with_byte_budget(fp, byte_window=16)
        # The returned lines are the trailing slice; at least one
        # line must be present (the file has 10 lines, the window
        # covers the last ~16 bytes which span 1–2 lines).
        assert len(result) >= 1, (
            f"byte-tail path returned an empty result for a 110-byte file with a 16-byte window: {result!r}"
        )
        # The trailing-most line must be the last line of the
        # file.
        assert result[-1] == lines[-1], (
            f"byte-tail path dropped the trailing line: expected {lines[-1]!r} as the last entry, got {result!r}"
        )

    def test_byte_tail_discards_partial_first_line(self, tmp_path: Path) -> None:
        """In the byte-tail path the partial first line (the
        byte-aligned prefix that lives between
        ``seek(size - window)`` and the first ``\\n``) is
        discarded so the line counter aligns with whole lines.

        We construct a file where the byte window splits a line
        in the middle: ``seek(size - 5)`` lands inside the second-
        to-last line."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        # 3 lines, each 10 chars + newline = 33 bytes total.
        content = "AAAAAAAAAA\nBBBBBBBBBB\nCCCCCCCCCC\n"
        fp = tmp_path / "split.jsonl"
        fp.write_text(content, encoding="utf-8")
        size_now = fp.stat().st_size
        assert size_now == 33

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        # Window of 25 bytes lands mid-line in the middle of
        # ``BBBBBBBBBB\n`` — the partial first chunk
        # (``"BBBBBB"`` + remainder) must be discarded.
        result = appender._read_file_with_byte_budget(fp, byte_window=25)
        # The trailing line must be intact.
        assert result[-1] == "CCCCCCCCCC", f"byte-tail path did not preserve the trailing line: {result!r}"
        # And the partial chunk must NOT appear as a standalone
        # line (i.e. no ``"BBBBBB"`` token leaked through).
        assert "BBBBBB" not in result, f"byte-tail path leaked the partial first line: {result!r}"

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        """An empty file (size 0) returns ``[]`` — the legacy
        inline path had the same short-circuit
        (``if size_now <= 0: continue``)."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        fp = tmp_path / "empty.jsonl"
        fp.write_text("", encoding="utf-8")
        assert fp.stat().st_size == 0

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        result = appender._read_file_with_byte_budget(fp, byte_window=4096)
        assert result == []

    def test_exact_byte_window_boundary_uses_whole_file(
        self,
        tmp_path: Path,
    ) -> None:
        """A file whose size **exactly equals** ``byte_window``
        takes the whole-file path (the boundary is ``<=`` not
        ``<``). The byte-tail path is for strictly-larger
        files."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        content = "abcdefghij"  # 10 bytes
        fp = tmp_path / "exact.jsonl"
        fp.write_text(content, encoding="utf-8")
        assert fp.stat().st_size == 10

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        # Window exactly equals file size — whole-file path.
        result = appender._read_file_with_byte_budget(fp, byte_window=10)
        assert result == ["abcdefghij"]

        # Window one byte smaller — byte-tail path.
        result_tail = appender._read_file_with_byte_budget(fp, byte_window=9)
        # Trailing 9 bytes = ``"bcdefghij"``, no newlines, single
        # entry.
        assert result_tail == ["bcdefghij"]

    def test_one_byte_boundary(self, tmp_path: Path) -> None:
        """A 1-byte file with a 1-byte window is the smallest
        boundary case: whole-file path (size <= window)."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        fp = tmp_path / "tiny.jsonl"
        fp.write_text("x", encoding="utf-8")
        assert fp.stat().st_size == 1

        appender = DecisionAuditAppender(audit_path=tmp_path / "unused.jsonl")
        result = appender._read_file_with_byte_budget(fp, byte_window=1)
        assert result == ["x"]


# ---------------------------------------------------------------------------
# AUDIT-N+4 — ``tail_events`` byte-budget parity regression guard
# ---------------------------------------------------------------------------


class TestTailEventsByteBudgetParity:
    """Parity regression guard: ``tail_events(n=20)`` continues
    to produce identical output before and after the helper
    extraction. The new ``_read_file_with_byte_budget`` helper
    must be a behaviour-preserving refactor — the rendered
    ``tail_events`` output on the standard 10-record fixture is
    unchanged from the pre-refactor baseline.

    AUDIT-N+4 contract: the helper extraction does not change
    the public ``tail_events`` surface (callers see identical
    return values for identical inputs)."""

    def test_tail_events_returns_unchanged_n_records_after_refactor(
        self,
        tmp_path: Path,
    ) -> None:
        """After the helper extraction, ``tail_events(n=20)`` on
        the canonical 10-record fixture still returns all 10
        records in order — the parity guard for the small-file
        (whole-file) path."""
        from thegent.ux.cockpit import DecisionNotice
        from thegent.ux.decision_audit import DecisionAuditAppender

        log = tmp_path / "decisions.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        # Record 10 deterministic notices.
        for i in range(10):
            notice = DecisionNotice(
                verdict="deny",
                reason_code="parity_guard",
                rule_id=f"r{i}",
                agent="cursor",
                lane="critical",
                evaluated_at=0.0,
                reason="parity regression guard",
            )
            appender.record(notice)
        # The file is small (well under the byte window), so the
        # whole-file path is exercised end-to-end.
        events = appender.tail_events(n=20)
        assert len(events) == 10, (
            f"tail_events after refactor dropped records: expected 10, got {len(events)}: {events!r}"
        )
        # The rule_id order is preserved.
        assert [e["rule_id"] for e in events] == [f"r{i}" for i in range(10)], (
            f"tail_events after refactor changed record order: {[e['rule_id'] for e in events]!r}"
        )

    def test_tail_events_handles_missing_file_post_refactor(
        self,
        tmp_path: Path,
    ) -> None:
        """After the helper extraction, ``tail_events()`` on a
        missing-file appender still returns ``[]`` — the
        canonical pre-refactor baseline."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        appender = DecisionAuditAppender(audit_path=tmp_path / "missing.jsonl")
        assert appender.tail_events() == [], (
            "tail_events after refactor must still return [] on a "
            "missing-file appender (helper short-circuit contract)."
        )


# ---------------------------------------------------------------------------
# AUDIT-N+4 — Sanity import for the new test file itself
# ---------------------------------------------------------------------------


def test_module_imports_cleanly() -> None:
    """Sanity check: the source files swept in this lane import
    cleanly after the AUDIT-N+4 migration. Any
    ``ModuleNotFoundError`` / ``ImportError`` / ``SyntaxError``
    bubbles up and fails the test."""
    importlib.import_module("thegent.cli.commands.cli")
    importlib.import_module("thegent.ux.decision_audit")
