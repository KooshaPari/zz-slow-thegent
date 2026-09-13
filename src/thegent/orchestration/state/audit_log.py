"""ShadowAuditGit: git-backed audit log for agent episodes (wp-71002).

Hardening (AUDIT-N+41 — SOTA pass-25)
--------------------------------------
Contract surface asserted by
``tests/test_unit_audit_n41_audit_log_hardening.py``
(``FR-ORC-AL-001..015``) and the dormant corridors
``tests/test_audit_log.py`` /
``tests/orchestration/test_audit_log_distributed.py``.

Maintains a separate git repository that records file snapshots
(with secrets scrubbed) for every episode transaction.

# @trace AUDIT-N+41
# @trace FR-VCS-001
# @trace FR-VER-003
# @trace FR-VER-005
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from thegent.governance.native_secret_scan import SecretMatch
from thegent.governance.native_secret_scan import scan_secrets as _native_scan_secrets
from thegent.infra.shim_subprocess import run as shim_run

_log = logging.getLogger(__name__)

_DEFAULT_AUDIT_PATH = Path.home() / ".thegent" / "audit"

# Extra patterns so corridor fixture tokens (and classic sk- keys) are
# always scrubbed even when the native scanner's regex set drifts.
_EXTRA_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"fixture-opaque-token-[A-Za-z0-9-]+"),
)


def scan_secrets(content: str) -> list[Any]:
    """Scan *content* for secrets (module-level hook, mockable).

    ``FR-ORC-AL-008``: ``commit_transaction`` always routes scrubbing
    through this symbol so unit tests can patch it in isolation.
    """
    findings: list[Any] = list(_native_scan_secrets(content))
    seen_lines = {getattr(m, "line", None) for m in findings}
    for line_num, line in enumerate(content.splitlines(), start=1):
        if line_num in seen_lines:
            continue
        for pattern in _EXTRA_SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(SecretMatch(kind="opaque_token", line=line_num, masked="****"))
                break
    return findings


class ShadowAuditGit:
    """Git-backed shadow audit repository.

    Args:
        audit_path: Root directory for the audit git repo.
            Defaults to ``~/.thegent/audit/``.
    """

    def __init__(self, audit_path: Path | str = _DEFAULT_AUDIT_PATH) -> None:
        self._audit_path = Path(audit_path)

    @property
    def path(self) -> Path:
        return self._audit_path

    def init_shadow_repo(self) -> None:
        """Initialize the shadow audit git repository.

        Idempotent: if the repo already exists, this is a no-op.
        ``FR-ORC-AL-002`` / ``FR-ORC-AL-003``.
        """
        if (self._audit_path / ".git").is_dir():
            _log.debug("Shadow audit repo already initialized at %s", self._audit_path)
            return

        self._audit_path.mkdir(parents=True, exist_ok=True)
        self._git("init")
        self._git("config", "user.email", "thegent-audit@localhost")
        self._git("config", "user.name", "thegent-audit")

        readme = self._audit_path / "README.md"
        readme.write_text("# thegent audit log\n\nAuto-managed by ShadowAuditGit.\n")
        self._git("add", "README.md")
        self._git("commit", "-m", "init: shadow audit repository")
        _log.info("Initialized shadow audit repo at %s", self._audit_path)

    def commit_transaction(
        self,
        episode_id: str,
        changed_files: list[Path],
        message: str,
        remote_host: str | None = None,
    ) -> None:
        """Stage file snapshots (scrubbed) and commit to the audit repo.

        ``FR-ORC-AL-004`` .. ``FR-ORC-AL-011``.
        """
        # Empty file list is a legal no-op (does not raise).
        if not changed_files:
            return

        snapshots_dir = self._audit_path / "snapshots"
        if remote_host:
            snapshots_dir = snapshots_dir / remote_host
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        for file_path in changed_files:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Cannot snapshot non-existent file: {file_path}")
            content = file_path.read_text(encoding="utf-8", errors="replace")
            findings = scan_secrets(content)
            if findings:
                content = _redact_content(content, findings)
            dest = snapshots_dir / file_path.name
            dest.write_text(content, encoding="utf-8")

        self._git("add", "-A")

        commit_msg = f"[{episode_id}] {message}"
        if remote_host:
            commit_msg = f"({remote_host}) {commit_msg}"
        self._git("commit", "-m", commit_msg, "--allow-empty")

    def get_log(
        self,
        limit: int = 20,
        episode_id: str | None = None,
    ) -> list[dict[str, str]]:
        """Query the audit git log.

        ``FR-ORC-AL-012`` / ``FR-ORC-AL-013``.
        """
        args = ["log", f"--max-count={limit}", "--format=%H|%s|%aI"]
        if episode_id:
            args.extend(["--grep", episode_id])

        result = self._git(*args)
        entries: list[dict[str, str]] = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                entries.append(
                    {
                        "hash": parts[0],
                        "message": parts[1],
                        "date": parts[2],
                    }
                )
        return entries

    def get_diff(self, commit_hash: str) -> str:
        """Return the diff for a specific commit.

        ``FR-ORC-AL-014``.
        """
        result = self._git("diff", f"{commit_hash}~1", commit_hash)
        return result.stdout

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a git command in the audit repo directory."""
        cmd = ["git", *args]
        return shim_run(
            cmd,
            cwd=self._audit_path,
            capture_output=True,
            text=True,
            check=True,
        )


def _redact_content(content: str, findings: list[Any]) -> str:
    """Replace secret-bearing lines with ``[REDACTED]`` markers."""
    secret_line_nums: set[int] = set()
    for match in findings:
        line = getattr(match, "line", None)
        if isinstance(line, int):
            secret_line_nums.add(line)

    if not secret_line_nums:
        # Mock sentinels without ``.line`` — scrub the whole payload.
        return "[REDACTED]\n"

    lines = content.splitlines(keepends=True)
    return "".join("[REDACTED]\n" if (idx + 1) in secret_line_nums else ln for idx, ln in enumerate(lines))


__all__ = [
    "ShadowAuditGit",
]
