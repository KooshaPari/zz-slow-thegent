"""VetterPolicy, VetterCheck, VetterResult — governance vetter core types.

Foundation for the vetter governance chain (WL-090). Fail fast, fail loudly.
No silent fallbacks. No legacy shims.

# @trace AUDIT-N+52
# @trace FR-GOV-VT-001..015
# @trace FR-VET-090
# @trace WL-090
# @trace WL-097
"""

from __future__ import annotations

import abc
import logging
import re
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from thegent.infra.shim_subprocess import run as shim_run

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class VetterOutcome(StrEnum):
    """Three-verdict taxonomy for individual check results.

    # @trace FR-GOV-VT-001
    # @trace FR-VET-090
    """

    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class VetterSeverity(StrEnum):
    """Severity levels for VetterPolicy.

    # @trace FR-GOV-VT-002
    # @trace FR-VET-090
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# VetterResult
# ---------------------------------------------------------------------------


class VetterResult(BaseModel):
    """Result returned by a single VetterCheck.run() call.

    Immutable via model_config frozen=True.

    # @trace FR-GOV-VT-003..007
    # @trace FR-VET-090
    """

    model_config = ConfigDict(frozen=True)

    outcome: VetterOutcome
    reason: str
    check_name: str
    policy_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_pass(self) -> bool:
        """True iff outcome is APPROVED. # @trace FR-GOV-VT-006 # @trace FR-VET-090"""
        return self.outcome == VetterOutcome.APPROVED

    @property
    def is_fail(self) -> bool:
        """True iff outcome is not APPROVED. # @trace FR-GOV-VT-006 # @trace FR-VET-090"""
        return not self.is_pass

    @classmethod
    def approved(
        cls,
        check_name: str,
        policy_name: str,
        reason: str = "",
        **metadata: Any,
    ) -> VetterResult:
        """Create an APPROVED result. # @trace FR-GOV-VT-003 # @trace FR-VET-090"""
        return cls(
            outcome=VetterOutcome.APPROVED,
            reason=reason,
            check_name=check_name,
            policy_name=policy_name,
            metadata=dict(metadata),
        )

    @classmethod
    def rejected(
        cls,
        check_name: str,
        policy_name: str,
        reason: str,
        **metadata: Any,
    ) -> VetterResult:
        """Create a REJECTED result. # @trace FR-GOV-VT-004 # @trace FR-VET-090"""
        return cls(
            outcome=VetterOutcome.REJECTED,
            reason=reason,
            check_name=check_name,
            policy_name=policy_name,
            metadata=dict(metadata),
        )

    @classmethod
    def revision_requested(
        cls,
        check_name: str,
        policy_name: str,
        reason: str,
        **metadata: Any,
    ) -> VetterResult:
        """Create a REVISION_REQUESTED result. # @trace FR-GOV-VT-005 # @trace FR-VET-090"""
        return cls(
            outcome=VetterOutcome.REVISION_REQUESTED,
            reason=reason,
            check_name=check_name,
            policy_name=policy_name,
            metadata=dict(metadata),
        )


# ---------------------------------------------------------------------------
# VetterPolicy
# ---------------------------------------------------------------------------


class VetterPolicy(BaseModel):
    """Policy configuration attached to each VetterCheck.

    Mutable: enabled state can be toggled via disable()/enable().

    # @trace FR-GOV-VT-008
    # @trace FR-VET-090
    """

    model_config = ConfigDict(frozen=False)

    name: str
    enabled: bool = True
    severity: VetterSeverity = VetterSeverity.ERROR
    description: str = ""

    def disable(self) -> None:
        """Disable this policy. # @trace FR-GOV-VT-008 # @trace FR-VET-090"""
        self.enabled = False

    def enable(self) -> None:
        """Enable this policy. # @trace FR-GOV-VT-008 # @trace FR-VET-090"""
        self.enabled = True

    def to_dict(self) -> dict[str, Any]:
        """Return model as plain dict. # @trace FR-GOV-VT-008 # @trace FR-VET-090"""
        return self.model_dump()


# ---------------------------------------------------------------------------
# VetterCheck (ABC)
# ---------------------------------------------------------------------------


class VetterCheck(abc.ABC):
    """Abstract base class for all vetter check implementations.

    Concrete subclasses must implement:
    - name (property): str — unique check identifier
    - policy (property): VetterPolicy — associated policy
    - run(payload) -> VetterResult — execute the check

    # @trace FR-GOV-VT-009
    # @trace FR-VET-090
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name for this check. # @trace FR-GOV-VT-009 # @trace FR-VET-090"""

    @property
    @abc.abstractmethod
    def policy(self) -> VetterPolicy:
        """Associated policy governing this check. # @trace FR-GOV-VT-009 # @trace FR-VET-090"""

    @abc.abstractmethod
    def run(self, payload: dict[str, Any]) -> VetterResult:
        """Execute the check against payload. Fail fast, fail loudly.

        # @trace FR-GOV-VT-009
        # @trace FR-VET-090
        """

    @property
    def is_enabled(self) -> bool:
        """True iff the associated policy is enabled. # @trace FR-GOV-VT-009 # @trace FR-VET-090"""
        return self.policy.enabled


__all__ = [
    "RuffVetterCheck",
    "TestPassVetterCheck",
    "VetterCheck",
    "VetterCheckResult",
    "VetterOutcome",
    "VetterPolicy",
    "VetterResult",
    "VetterSeverity",
]


# ---------------------------------------------------------------------------
# WL-097: Vetter Code Checks — TestPassVetterCheck + RuffVetterCheck
# ---------------------------------------------------------------------------

# Pattern to extract .py filenames from unified diff
_PY_FILE_RE = re.compile(r"^(?:\+\+\+|---)\s+(?:a/|b/)?(\S+\.py)", re.MULTILINE)

# Shell metacharacters that must never appear in subprocess arguments
_SHELL_META_RE = re.compile(r"[|&;`\$\n]")


def _extract_changed_py_files(diff_text: str) -> list[str]:
    """Extract unique .py filenames from a unified diff header. # @trace FR-GOV-VT-014 # @trace WL-097"""
    return list(dict.fromkeys(_PY_FILE_RE.findall(diff_text)))


def _validate_cwd(cwd: str | None) -> str | None:
    """Validate and resolve a cwd path, rejecting traversal attempts.

    # @trace FR-GOV-VT-010..011
    """
    if not cwd or not isinstance(cwd, str) or not cwd.strip():
        return None
    # Check raw path for '..' segments BEFORE resolving (resolve would strip them)
    raw_parts = Path(cwd).parts
    if ".." in raw_parts:
        raise ValueError(f"cwd path contains '..' segments: {cwd}")
    resolved = Path(cwd).resolve()
    return str(resolved)


def _filter_injection_files(files: list[str], check_name: str) -> list[str]:
    """Remove files containing shell metacharacters and log a warning.

    # @trace FR-GOV-VT-013
    """
    safe: list[str] = []
    for f in files:
        if _SHELL_META_RE.search(f):
            logger.warning(
                "[%s] filtered file with shell metacharacters: %r",
                check_name,
                f,
            )
        else:
            safe.append(f)
    return safe


@dataclass
class TestPassVetterCheck:
    """Run pytest (or configured test runner) on changed Python files from the diff.

    Extracts changed .py files from the unified diff in ``output`` (the agent's
    RunResult.stdout).  If no Python files are found in the diff, runs pytest
    with no file arguments (i.e., the full suite).

    Uses shim_run (not asyncio.create_subprocess_exec) so that tests can
    mock shim_run without an asyncio harness.

    Fail fast: non-zero exit code -> passed=False, message contains the
    truncated test output.  No silent error handling.

    # @trace FR-GOV-VT-010..012
    # @trace WL-097
    """

    test_runner: str = "pytest"
    scope: str = "changed_files"
    timeout_seconds: int = 120
    name: str = "test_pass_vetter"
    extra_args: list[str] = field(default_factory=lambda: ["--tb=short", "-q"])
    cwd: str | None = None

    def check(self, output: str, context: dict[str, Any] | None = None) -> VetterCheckResult:
        """Run pytest on changed Python files extracted from the diff.

        # @trace FR-GOV-VT-010..012
        # @trace WL-097
        """
        context = context or {}

        # --- path-traversal guard (FR-GOV-VT-010) ---
        resolved_cwd = _validate_cwd(self.cwd or context.get("cwd"))

        changed_files = _extract_changed_py_files(output)
        changed_files = _filter_injection_files(changed_files, self.name)

        cmd: list[str] = [self.test_runner, *self.extra_args]
        if changed_files and self.scope == "changed_files":
            cmd.extend(changed_files)

        try:
            proc = shim_run(
                cmd,
                capture_output=True,
                timeout=self.timeout_seconds,
                cwd=resolved_cwd,
            )
        except subprocess.TimeoutExpired:
            return VetterCheckResult(
                check_name=self.name,
                passed=False,
                message=f"Test runner timed out after {self.timeout_seconds}s",
                metadata={"timeout": True, "files_tested": changed_files},
            )
        except (OSError, ValueError) as exc:
            return VetterCheckResult(
                check_name=self.name,
                passed=False,
                message=f"Subprocess error: {exc}",
                metadata={"error": str(exc), "files_tested": changed_files},
            )

        combined_output = (proc.stdout or b"").decode(errors="replace") + (proc.stderr or b"").decode(errors="replace")
        passed = proc.returncode == 0

        return VetterCheckResult(
            check_name=self.name,
            passed=passed,
            message="" if passed else combined_output[-2000:],
            metadata={"returncode": proc.returncode, "files_tested": changed_files},
        )


@dataclass
class RuffVetterCheck:
    """Run ruff check on Python files touched in the diff.

    Extracts changed .py files from the unified diff in ``output`` (the agent's
    RunResult.stdout).  If no Python files are found in the diff, returns
    passed=True (nothing to lint).

    Uses shim_run (not asyncio.create_subprocess_exec) so that tests can
    mock shim_run without an asyncio harness.

    fix_mode=True passes --fix to ruff (auto-fix enabled).
    select_rules limits which rules are evaluated via --select.

    Fail fast: non-zero ruff exit code -> passed=False, message contains
    the full ruff output.  No silent error handling.

    # @trace FR-GOV-VT-011,013
    # @trace WL-097
    """

    fix_mode: bool = False
    select_rules: list[str] = field(default_factory=list)
    name: str = "ruff_vetter"
    cwd: str | None = None

    def check(self, output: str, context: dict[str, Any] | None = None) -> VetterCheckResult:
        """Run ruff linter on changed Python files extracted from the diff.

        # @trace FR-GOV-VT-011,013
        # @trace WL-097
        """
        context = context or {}

        # --- path-traversal guard (FR-GOV-VT-011) ---
        resolved_cwd = _validate_cwd(self.cwd or context.get("cwd"))

        changed_files = _extract_changed_py_files(output)
        changed_files = _filter_injection_files(changed_files, self.name)

        if not changed_files:
            return VetterCheckResult(
                check_name=self.name,
                passed=True,
                message="No Python files in diff — ruff check skipped",
            )

        cmd: list[str] = ["ruff", "check"]
        if self.fix_mode:
            cmd.append("--fix")
        if self.select_rules:
            cmd.extend(["--select", ",".join(self.select_rules)])
        cmd.extend(changed_files)

        proc = shim_run(
            cmd,
            capture_output=True,
            cwd=resolved_cwd,
        )

        ruff_output = (proc.stdout or b"").decode(errors="replace") + (proc.stderr or b"").decode(errors="replace")
        passed = proc.returncode == 0

        return VetterCheckResult(
            check_name=self.name,
            passed=passed,
            message="" if passed else ruff_output,
            metadata={"returncode": proc.returncode, "files_checked": changed_files},
        )


# ---------------------------------------------------------------------------
# Internal VetterCheckResult (for WL-097 checks)
# ---------------------------------------------------------------------------


class VetterCheckResult(BaseModel):
    """Result returned by a VetterCheck.

    # @trace FR-GOV-VT-015
    # @trace WL-097
    """

    model_config = ConfigDict(frozen=True)

    check_name: str
    passed: bool
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
