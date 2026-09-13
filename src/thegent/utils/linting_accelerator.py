"""Linting accelerator: run oxlint as fast pre-filter before ESLint.

# @trace FR-UX-011

oxlint is a Rust-based JS/TS linter that is 50-100x faster than ESLint.
This module integrates it as a drop-in accelerator:

- ``fast=True``  -> run oxlint first; fall back to ESLint only if oxlint
  is unavailable (or skip ESLint entirely for CI speed).
- ``fast=False`` -> always run ESLint (standard behaviour).
- ``run_ruff``   -> Python linting via ruff (similar philosophy).

All three runners return a uniform ``list[LintResult]`` so callers can
process results without caring which backend was used.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import orjson as json

from thegent.infra.shim_subprocess import run as shim_run

if TYPE_CHECKING:
    from pathlib import Path

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class LintResult:
    """A single diagnostic produced by any linter backend.

    Attributes:
        file:     Absolute or relative path to the source file.
        line:     1-based line number of the issue.
        column:   1-based column number of the issue.
        severity: ``"error"`` or ``"warning"``.
        rule:     Lint rule identifier (e.g. ``"no-unused-vars"``).
        message:  Human-readable description of the issue.
        source:   Which linter produced this result (``"oxlint"``,
                  ``"eslint"``, ``"ruff"``).
    """

    file: str
    line: int
    column: int
    severity: str  # "error" | "warning"
    rule: str
    message: str
    source: str = field(default="unknown")

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} [{self.severity}] {self.rule}: {self.message}"


# ---------------------------------------------------------------------------
# Accelerator
# ---------------------------------------------------------------------------


class LintingAccelerator:
    """Unified linting interface with oxlint fast-path.

    Usage::

        acc = LintingAccelerator()
        results = acc.lint([Path("src/")], fast=True)
        for r in results:
            print(r)
    """

    # ------------------------------------------------------------------
    # Availability checks
    # ------------------------------------------------------------------

    def is_oxlint_available(self) -> bool:
        """Return ``True`` if ``oxlint`` is found on ``$PATH``.

        Returns:
            ``True`` when the ``oxlint`` binary can be located via
            :func:`shutil.which`; ``False`` otherwise.
        """
        return shutil.which("oxlint") is not None

    def is_eslint_available(self) -> bool:
        """Return ``True`` if ``eslint`` is found on ``$PATH``.

        Returns:
            ``True`` when the ``eslint`` binary can be located via
            :func:`shutil.which`; ``False`` otherwise.
        """
        return shutil.which("eslint") is not None

    def is_ruff_available(self) -> bool:
        """Return ``True`` if ``ruff`` is found on ``$PATH``.

        Returns:
            ``True`` when the ``ruff`` binary can be located via
            :func:`shutil.which`; ``False`` otherwise.
        """
        return shutil.which("ruff") is not None

    # ------------------------------------------------------------------
    # oxlint runner
    # ------------------------------------------------------------------

    def run_oxlint(
        self,
        paths: list[Path],
        config: Path | None = None,
    ) -> list[LintResult]:
        """Run ``oxlint`` and return parsed diagnostics.

        Args:
            paths:  List of files or directories to lint.
            config: Optional path to an ``oxlintrc.json`` config file.
                    When ``None``, oxlint auto-discovers ``oxlintrc.json``
                    in the working directory.

        Returns:
            List of :class:`LintResult` objects, one per diagnostic.

        Raises:
            FileNotFoundError: If ``oxlint`` is not installed.
            ValueError: If the JSON output from oxlint cannot be parsed.
        """
        if not self.is_oxlint_available():
            raise FileNotFoundError(
                "oxlint not found on PATH. Install via: npm install -g oxlint  or  cargo install oxlint"
            )

        cmd: list[str] = ["oxlint", "--format", "json"]
        if config is not None:
            cmd.extend(["--config", str(config)])
        cmd.extend(str(p) for p in paths)

        _log.debug("running oxlint: %s", cmd)
        proc = shim_run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        raw_stdout = proc.stdout.strip()
        if not raw_stdout:
            return []

        return self._parse_oxlint_json(raw_stdout)

    def _parse_oxlint_json(self, raw: str) -> list[LintResult]:
        """Parse oxlint JSON output into :class:`LintResult` list.

        oxlint ``--format json`` produces either:

        - A JSON array of diagnostic objects, **or**
        - An ESLint-compatible array of file-level objects each with a
          ``messages`` array.

        Args:
            raw: Raw JSON string from oxlint stdout.

        Returns:
            Parsed list of :class:`LintResult`.

        Raises:
            ValueError: If the JSON structure is unrecognised.
        """
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"oxlint produced invalid JSON: {exc}\nOutput: {raw[:200]}") from exc

        results: list[LintResult] = []

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array from oxlint, got {type(data).__name__}")

        for item in data:
            if not isinstance(item, dict):
                continue

            # ESLint-compatible per-file format
            if "filePath" in item and "messages" in item:
                file_path = item.get("filePath", "")
                for msg in item.get("messages", []):
                    results.append(self._oxlint_msg_to_result(file_path, msg))
            else:
                # Flat diagnostic format
                file_path = item.get("filename", item.get("file", ""))
                results.append(self._oxlint_msg_to_result(file_path, item))

        return results

    @staticmethod
    def _oxlint_msg_to_result(file_path: str, msg: dict[str, Any]) -> LintResult:
        """Convert a single oxlint message dict to :class:`LintResult`.

        Args:
            file_path: Source file path string.
            msg:       Diagnostic dict from the JSON output.

        Returns:
            A populated :class:`LintResult`.
        """
        severity_code = msg.get("severity", 2)
        severity = "warning" if severity_code == 1 else "error"
        rule_id = msg.get("ruleId", msg.get("rule", "unknown"))
        return LintResult(
            file=file_path,
            line=msg.get("line", 1),
            column=msg.get("column", 1),
            severity=severity,
            rule=str(rule_id),
            message=msg.get("message", ""),
            source="oxlint",
        )

    # ------------------------------------------------------------------
    # ESLint runner
    # ------------------------------------------------------------------

    def run_eslint(
        self,
        paths: list[Path],
        config: Path | None = None,
    ) -> list[LintResult]:
        """Run ``eslint --format json`` and return parsed diagnostics.

        Args:
            paths:  List of files or directories to lint.
            config: Optional path to an ESLint config file.  When
                    ``None``, ESLint uses its default discovery logic.

        Returns:
            List of :class:`LintResult` objects, one per diagnostic.

        Raises:
            FileNotFoundError: If ``eslint`` is not installed.
            ValueError: If the JSON output from ESLint cannot be parsed.
        """
        if not self.is_eslint_available():
            raise FileNotFoundError(
                "eslint not found on PATH. Install via: npm install -g eslint  or  bun add -d eslint"
            )

        cmd: list[str] = ["eslint", "--format", "json"]
        if config is not None:
            cmd.extend(["--config", str(config)])
        cmd.extend(str(p) for p in paths)

        _log.debug("running eslint: %s", cmd)
        proc = shim_run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        raw_stdout = proc.stdout.strip()
        if not raw_stdout:
            return []

        return self._parse_eslint_json(raw_stdout)

    def _parse_eslint_json(self, raw: str) -> list[LintResult]:
        """Parse ESLint JSON output into :class:`LintResult` list.

        ESLint ``--format json`` produces an array of file-level objects,
        each with a ``messages`` array of diagnostic dicts.

        Args:
            raw: Raw JSON string from ESLint stdout.

        Returns:
            Parsed list of :class:`LintResult`.

        Raises:
            ValueError: If the JSON structure is unrecognised.
        """
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"eslint produced invalid JSON: {exc}\nOutput: {raw[:200]}") from exc

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array from eslint, got {type(data).__name__}")

        results: list[LintResult] = []
        for file_obj in data:
            if not isinstance(file_obj, dict):
                continue
            file_path = file_obj.get("filePath", "")
            for msg in file_obj.get("messages", []):
                severity_code = msg.get("severity", 2)
                severity = "warning" if severity_code == 1 else "error"
                results.append(
                    LintResult(
                        file=file_path,
                        line=msg.get("line", 1),
                        column=msg.get("column", 1),
                        severity=severity,
                        rule=str(msg.get("ruleId") or "unknown"),
                        message=msg.get("message", ""),
                        source="eslint",
                    )
                )

        return results

    # ------------------------------------------------------------------
    # ruff runner (Python)
    # ------------------------------------------------------------------

    def run_ruff(self, paths: list[Path]) -> list[LintResult]:
        """Run ``ruff check --output-format json`` and return diagnostics.

        Args:
            paths: List of Python files or directories to lint.

        Returns:
            List of :class:`LintResult` objects, one per diagnostic.

        Raises:
            FileNotFoundError: If ``ruff`` is not installed.
            ValueError: If the JSON output from ruff cannot be parsed.
        """
        if not self.is_ruff_available():
            raise FileNotFoundError("ruff not found on PATH. Install via: pip install ruff  or  uv tool install ruff")

        cmd: list[str] = ["ruff", "check", "--output-format", "json"]
        cmd.extend(str(p) for p in paths)

        _log.debug("running ruff: %s", cmd)
        proc = shim_run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        raw_stdout = proc.stdout.strip()
        if not raw_stdout:
            return []

        return self._parse_ruff_json(raw_stdout)

    def _parse_ruff_json(self, raw: str) -> list[LintResult]:
        """Parse ruff JSON output into :class:`LintResult` list.

        Ruff ``--output-format json`` produces an array of diagnostic
        objects with ``filename``, ``location``, ``code``, ``message``.

        Args:
            raw: Raw JSON string from ruff stdout.

        Returns:
            Parsed list of :class:`LintResult`.

        Raises:
            ValueError: If the JSON structure is unrecognised.
        """
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"ruff produced invalid JSON: {exc}\nOutput: {raw[:200]}") from exc

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array from ruff, got {type(data).__name__}")

        results: list[LintResult] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            location = item.get("location") or {}
            # severity: ruff diagnostics with an auto-fix are "warning"-level
            # by convention; unfixable issues are treated as errors.
            has_fix = item.get("fix") is not None
            severity = "warning" if has_fix else "error"
            results.append(
                LintResult(
                    file=item.get("filename", ""),
                    line=location.get("row", 1),
                    column=location.get("column", 1),
                    severity=severity,
                    rule=item.get("code", "unknown"),
                    message=item.get("message", ""),
                    source="ruff",
                )
            )

        return results

    # ------------------------------------------------------------------
    # Unified entry point
    # ------------------------------------------------------------------

    def lint(
        self,
        paths: list[Path],
        fast: bool = True,
        oxlint_config: Path | None = None,
        eslint_config: Path | None = None,
    ) -> list[LintResult]:
        """Run linting and return all diagnostics.

        When ``fast=True`` (default):

        1. If ``oxlint`` is available, run oxlint and return its results.
           This is 50-100x faster than ESLint and catches the majority of
           issues.
        2. If ``oxlint`` is **not** available, fall back to ESLint.

        When ``fast=False``:

        - Always run ESLint (standard, thorough behaviour).

        Args:
            paths:         List of files or directories to lint.
            fast:          Use oxlint fast-path when available.
            oxlint_config: Optional path to ``oxlintrc.json``.
            eslint_config: Optional path to an ESLint config file.

        Returns:
            Combined list of :class:`LintResult` from whichever backend(s)
            were executed.
        """
        if fast and self.is_oxlint_available():
            _log.info("lint: using oxlint fast-path")
            return self.run_oxlint(paths, config=oxlint_config)

        if self.is_eslint_available():
            _log.info("lint: using eslint (fast=False or oxlint unavailable)")
            return self.run_eslint(paths, config=eslint_config)

        _log.warning("lint: neither oxlint nor eslint available; returning empty results")
        return []
