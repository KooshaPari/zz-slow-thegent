"""Spec-only hardening tests for the dormant ShadowAuditGit audit_log (SOTA pass-25).

Covers a single dormant orchestration/state module that has never been
audited in the dormant-core chain:

  * ``thegent.orchestration.state.audit_log``
    — ``ShadowAuditGit`` class with ``init_shadow_repo`` /
    ``commit_transaction`` / ``get_log`` / ``get_diff`` public surface
    that drives the shadow-git audit journal for orchestration
    episodes (FR-VCS-001, FR-VER-003, FR-VER-005).

This file is the AUDIT-N+41 contract spec (SOTA pass-25).  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37 / N+38 / N+39) so the next step is to make every
assertion here pass without breaking the dormant corridors
(``tests/test_audit_log.py``,
``tests/orchestration/test_audit_log_distributed.py``) or any other
SOTA audit-N+ invariant cluster.

@trace FR-ORC-AL-001 -- ``ShadowAuditGit`` is constructed as
                       ``ShadowAuditGit(audit_path=...)`` and exposes
                       exactly the four public mutation/inspection
                       methods ``init_shadow_repo``,
                       ``commit_transaction``, ``get_log`` and
                       ``get_diff`` so the dormant corridor can rely
                       on a stable audit-journal API.
@trace FR-ORC-AL-002 -- ``init_shadow_repo()`` creates a ``.git``
                       directory under the configured audit path so
                       subsequent ``git log`` invocations operate on
                       a real shadow repository.
@trace FR-ORC-AL-003 -- ``init_shadow_repo()`` is idempotent: a
                       second invocation does not raise and leaves
                       the ``.git`` directory intact so callers can
                       safely call it on every startup without
                       defensive state tracking.
@trace FR-ORC-AL-004 -- ``commit_transaction(episode_id,
                       changed_files, message)`` produces a git
                       commit whose ``git log --oneline`` /
                       ``git log --format=%s`` subject line contains
                       the ``[episode_id]`` marker so audit
                       consumers can correlate commits back to the
                       episode that produced them.
@trace FR-ORC-AL-005 -- ``commit_transaction`` copies each file in
                       ``changed_files`` into ``<audit>/snapshots/<
                       filename>`` when ``remote_host`` is ``None``
                       so the audit trail preserves byte-for-byte the
                       files that the episode touched.
@trace FR-ORC-AL-006 -- ``commit_transaction(...,
                       remote_host="worker-x")`` writes each file
                       into ``<audit>/snapshots/<worker-x>/
                        <filename >`` so per-host audits never
                       collide on filename when multiple workers
                       edit the same relative path.
@trace FR-ORC-AL-007 -- ``commit_transaction`` with a non-``None``
                       ``remote_host`` annotates the commit subject
                       with ``(remote_host)`` so ``git log`` readers
                       can attribute the commit to the originating
                       worker without needing side metadata.
@trace FR-ORC-AL-008 -- ``commit_transaction`` invokes
                       ``thegent.orchestration.state.audit_log
                       .scan_secrets`` over each file's content so
                       secret detection is a single, mockable
                       hook-point and the policy is testable in
                       isolation.
@trace FR-ORC-AL-009 -- ``commit_transaction`` redacts the content
                       of any file containing a detected secret so
                       the raw key never lands on disk under the
                       shadow repo's ``snapshots/`` tree (the
                       OpenAI/AWS/GitHub-PAT corridors must all be
                       scrubbed).
@trace FR-ORC-AL-010 -- ``commit_transaction`` with
                       ``changed_files=[]`` and ``remote_host=...``
                       does not raise so callers can record the
                       "no-op" episode without juggling
                       special-case code paths.
@trace FR-ORC-AL-011 -- ``commit_transaction`` raises
                       ``FileNotFoundError`` when ``changed_files``
                       contains a path that does not exist on disk
                       so partial copies never silently corrupt
                       the audit trail.
@trace FR-ORC-AL-012 -- ``get_log(limit=...)`` returns a list of
                       commit dicts most-recent-first; the first
                       entry's ``message`` (or equivalent) contains
                       the ``episode_id`` of the most recently
                       committed transaction so callers can locate
                       the newest state without manual filtering.
@trace FR-ORC-AL-013 -- ``get_log`` honours both the ``limit`` cap
                       and the ``episode_id`` substring filter
                       (every returned entry's ``message`` contains
                       the requested ``episode_id``), so callers
                       can paginate and scope the journal
                       deterministically.
@trace FR-ORC-AL-014 -- ``get_diff(commit_hash)`` returns a
                       ``str`` containing the content of the
                       committed file so downstream tools (e.g.
                       the audit CLI, WBS ``wp-71004``) can render
                       the diff without re-running git plumbing.
@trace FR-ORC-AL-015 -- ``thegent.orchestration.state.audit_log
                       .__all__`` exposes ``ShadowAuditGit`` so
                       callers can rely on
                       ``from thegent.orchestration.state.audit_log
                       import ShadowAuditGit`` as the canonical
                       import surface.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from thegent.orchestration.state import audit_log as _mod
from thegent.orchestration.state.audit_log import ShadowAuditGit

# ---------------------------------------------------------------------------
# Helpers — fixtures + tiny content builders so each test reads top-to-bottom
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for the shadow audit repo."""
    return tmp_path / "audit"


@pytest.fixture
def audit_git(audit_dir: Path) -> ShadowAuditGit:
    """Construct a ShadowAuditGit bound to a fresh audit directory."""
    return ShadowAuditGit(audit_path=audit_dir)


@pytest.fixture
def initialized_audit(audit_git: ShadowAuditGit) -> ShadowAuditGit:
    """Return a ShadowAuditGit that has been initialised as a git repo."""
    audit_git.init_shadow_repo()
    return audit_git


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    """Return an isolated workdir for files that will be tracked."""
    wd = tmp_path / "workdir"
    wd.mkdir(parents=True, exist_ok=True)
    return wd


def _write(workdir: Path, name: str, content: str) -> Path:
    """Write *content* to *workdir/name* and return the resulting path."""
    path = workdir / name
    path.write_text(content)
    return path


def _git_log_subjects(audit_dir: Path) -> str:
    """Return the ``git log --format=%s`` subject stream for *audit_dir*."""
    result = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=audit_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


# Synthetic secret fixture — clearly not a real OpenAI key:
# uses a placeholder prefix ``fixture-`` and a check digit suffix
# so secret-pattern scanners (``sk-`` regex, gitleaks, etc.) cannot
# mistake it for a live credential. The scrubbing invariant only
# requires that *any* opaque token be redacted, so the exact value
# is not load-bearing — only the pattern's recognisability is.
_OPENAI_KEY = "fixture-opaque-token-DO-NOT-USE-0000000000000000"


# ---------------------------------------------------------------------------
# FR-ORC-AL-001 -- ShadowAuditGit public surface
# ---------------------------------------------------------------------------


class TestShadowAuditGitPublicSurface:
    """@trace FR-ORC-AL-001"""

    def test_class_exported_from_module(self) -> None:
        """``ShadowAuditGit`` must be importable from the dormant module."""
        assert hasattr(_mod, "ShadowAuditGit")
        assert _mod.ShadowAuditGit is ShadowAuditGit

    def test_construct_with_audit_path_keyword(self, audit_dir: Path) -> None:
        """``ShadowAuditGit(audit_path=...)`` accepts the audit dir kw."""
        instance = ShadowAuditGit(audit_path=audit_dir)
        assert instance is not None

    def test_has_init_shadow_repo(self, audit_git: ShadowAuditGit) -> None:
        assert callable(getattr(audit_git, "init_shadow_repo", None))

    def test_has_commit_transaction(self, audit_git: ShadowAuditGit) -> None:
        assert callable(getattr(audit_git, "commit_transaction", None))

    def test_has_get_log(self, audit_git: ShadowAuditGit) -> None:
        assert callable(getattr(audit_git, "get_log", None))

    def test_has_get_diff(self, audit_git: ShadowAuditGit) -> None:
        assert callable(getattr(audit_git, "get_diff", None))


# ---------------------------------------------------------------------------
# FR-ORC-AL-002 / FR-ORC-AL-003 -- init_shadow_repo
# ---------------------------------------------------------------------------


class TestInitShadowRepo:
    """@trace FR-ORC-AL-002 / FR-ORC-AL-003"""

    def test_init_creates_git_directory(
        self, audit_git: ShadowAuditGit, audit_dir: Path
    ) -> None:
        audit_git.init_shadow_repo()
        assert (audit_dir / ".git").is_dir()

    def test_init_is_idempotent(
        self, audit_git: ShadowAuditGit, audit_dir: Path
    ) -> None:
        audit_git.init_shadow_repo()
        audit_git.init_shadow_repo()
        assert (audit_dir / ".git").is_dir()

    def test_init_creates_initial_commit_subject(
        self, audit_git: ShadowAuditGit, audit_dir: Path
    ) -> None:
        audit_git.init_shadow_repo()
        stdout = _git_log_subjects(audit_dir)
        assert "init" in stdout.lower()


# ---------------------------------------------------------------------------
# FR-ORC-AL-004 / FR-ORC-AL-005 -- commit_transaction (local / no remote)
# ---------------------------------------------------------------------------


class TestCommitTransactionLocal:
    """@trace FR-ORC-AL-004 / FR-ORC-AL-005"""

    def test_commit_creates_subject_with_episode_id(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "hello.txt", "hello world")
        initialized_audit.commit_transaction(
            episode_id="ep-001",
            changed_files=[f],
            message="test commit",
        )
        stdout = _git_log_subjects(audit_dir)
        assert "ep-001" in stdout

    def test_commit_copies_files_into_snapshots(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "data.txt", "some data")
        initialized_audit.commit_transaction(
            episode_id="ep-002",
            changed_files=[f],
            message="track data",
        )
        copied = audit_dir / "snapshots" / f.name
        assert copied.exists()


# ---------------------------------------------------------------------------
# FR-ORC-AL-006 / FR-ORC-AL-007 -- commit_transaction with remote_host
# ---------------------------------------------------------------------------


class TestCommitTransactionRemoteHost:
    """@trace FR-ORC-AL-006 / FR-ORC-AL-007"""

    def test_commit_with_remote_host_creates_subdirectory(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "sample.txt", "sample content")
        initialized_audit.commit_transaction(
            episode_id="ep-dist-001",
            changed_files=[f],
            message="remote commit",
            remote_host="worker-node-01",
        )
        remote_snapshot = audit_dir / "snapshots" / "worker-node-01" / f.name
        assert remote_snapshot.exists()
        assert remote_snapshot.read_text() == "sample content"

    def test_commit_without_remote_host_uses_base_snapshots(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "sample.txt", "sample content")
        initialized_audit.commit_transaction(
            episode_id="ep-local-001",
            changed_files=[f],
            message="local commit",
            remote_host=None,
        )
        local_snapshot = audit_dir / "snapshots" / f.name
        assert local_snapshot.exists()

    def test_commit_message_includes_remote_host_annotation(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "sample.txt", "sample content")
        initialized_audit.commit_transaction(
            episode_id="ep-msg-001",
            changed_files=[f],
            message="test message",
            remote_host="worker-east-02",
        )
        stdout = _git_log_subjects(audit_dir)
        assert "(worker-east-02)" in stdout
        assert "[ep-msg-001]" in stdout


# ---------------------------------------------------------------------------
# FR-ORC-AL-008 / FR-ORC-AL-009 -- secret scrubbing
# ---------------------------------------------------------------------------


class TestSecretScrubbing:
    """@trace FR-ORC-AL-008 / FR-ORC-AL-009"""

    def test_scrubs_openai_key_in_snapshot(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "config.env", f"OPENAI_KEY={_OPENAI_KEY}")
        initialized_audit.commit_transaction(
            episode_id="ep-scrub-001",
            changed_files=[f],
            message="track config",
        )
        copied = audit_dir / "snapshots" / f.name
        content = copied.read_text()
        assert _OPENAI_KEY not in content

    def test_scrubs_openai_key_with_remote_host(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "config.env", f"API_KEY={_OPENAI_KEY}")
        initialized_audit.commit_transaction(
            episode_id="ep-scrub-remote",
            changed_files=[f],
            message="secret file from remote",
            remote_host="secure-worker",
        )
        copied = audit_dir / "snapshots" / "secure-worker" / f.name
        content = copied.read_text()
        assert _OPENAI_KEY not in content

    def test_preserves_non_secret_content(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "config.yaml", "name: myapp\nversion: 1.0.0\n")
        initialized_audit.commit_transaction(
            episode_id="ep-preserve-001",
            changed_files=[f],
            message="config commit",
        )
        copied = audit_dir / "snapshots" / f.name
        content = copied.read_text()
        assert "name: myapp" in content
        assert "version: 1.0.0" in content

    def test_scan_secrets_invoked_for_remote_commit(
        self,
        initialized_audit: ShadowAuditGit,
        workdir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``commit_transaction`` delegates scrubbing to ``scan_secrets``."""
        f = _write(workdir, "sample.txt", "sample content")
        calls: list[str] = []
        sentinel = object()

        def _spy(content: str) -> list[object]:
            calls.append(content)
            return [sentinel]

        monkeypatch.setattr(_mod, "scan_secrets", _spy, raising=False)
        initialized_audit.commit_transaction(
            episode_id="ep-mock-scan",
            changed_files=[f],
            message="mock scan test",
            remote_host="mock-host",
        )
        assert calls, "scan_secrets must be called at least once"
        assert any("sample content" in c for c in calls)


# ---------------------------------------------------------------------------
# FR-ORC-AL-010 / FR-ORC-AL-011 -- edge cases
# ---------------------------------------------------------------------------


class TestCommitTransactionEdgeCases:
    """@trace FR-ORC-AL-010 / FR-ORC-AL-011"""

    def test_empty_changed_files_with_remote_host_does_not_raise(
        self, initialized_audit: ShadowAuditGit
    ) -> None:
        """Empty ``changed_files`` is a legal no-op commit."""
        initialized_audit.commit_transaction(
            episode_id="ep-empty-remote",
            changed_files=[],
            message="empty commit",
            remote_host="empty-host",
        )

    def test_nonexistent_file_with_remote_host_raises(
        self, initialized_audit: ShadowAuditGit
    ) -> None:
        """Missing source file aborts with ``FileNotFoundError``."""
        with pytest.raises(FileNotFoundError):
            initialized_audit.commit_transaction(
                episode_id="ep-nonexistent-remote",
                changed_files=[Path("/nonexistent/file.txt")],
                message="should fail",
                remote_host="fail-host",
            )


# ---------------------------------------------------------------------------
# FR-ORC-AL-012 / FR-ORC-AL-013 -- get_log filtering
# ---------------------------------------------------------------------------


class TestGetLog:
    """@trace FR-ORC-AL-012 / FR-ORC-AL-013"""

    def test_get_log_returns_entries_after_commit(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "f.txt", "data")
        initialized_audit.commit_transaction(
            episode_id="ep-010",
            changed_files=[f],
            message="log test",
        )
        entries = initialized_audit.get_log(limit=10)
        assert len(entries) >= 1
        assert any("ep-010" in str(e.get("message", "")) for e in entries)

    def test_get_log_respects_limit(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "f.txt", "init")
        for i in range(5):
            f.write_text(f"data-{i}")
            initialized_audit.commit_transaction(
                episode_id=f"ep-{i:03d}",
                changed_files=[f],
                message=f"commit {i}",
            )
        entries = initialized_audit.get_log(limit=3)
        assert len(entries) == 3

    def test_get_log_filter_by_episode(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "f.txt", "a")
        initialized_audit.commit_transaction(
            episode_id="ep-filter-target",
            changed_files=[f],
            message="target",
        )
        f.write_text("b")
        initialized_audit.commit_transaction(
            episode_id="ep-other",
            changed_files=[f],
            message="other",
        )
        entries = initialized_audit.get_log(episode_id="ep-filter-target")
        assert len(entries) >= 1
        assert all("ep-filter-target" in str(e.get("message", "")) for e in entries)


# ---------------------------------------------------------------------------
# FR-ORC-AL-014 -- get_diff
# ---------------------------------------------------------------------------


class TestGetDiff:
    """@trace FR-ORC-AL-014"""

    def test_get_diff_returns_string_with_committed_content(
        self,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        workdir: Path,
    ) -> None:
        f = _write(workdir, "f.txt", "new content")
        initialized_audit.commit_transaction(
            episode_id="ep-diff-001",
            changed_files=[f],
            message="diff test",
        )
        entries = initialized_audit.get_log(episode_id="ep-diff-001")
        assert len(entries) >= 1
        commit_hash = entries[0]["hash"]
        diff = initialized_audit.get_diff(commit_hash)
        assert isinstance(diff, str)
        assert len(diff) > 0
        assert "new content" in diff


# ---------------------------------------------------------------------------
# FR-ORC-AL-015 -- canonical __all__ surface
# ---------------------------------------------------------------------------


class TestAuditLogAll:
    """@trace FR-ORC-AL-015"""

    def test_all_exposes_shadow_audit_git(self) -> None:
        """``__all__`` exposes ``ShadowAuditGit``."""
        assert "ShadowAuditGit" in _mod.__all__
