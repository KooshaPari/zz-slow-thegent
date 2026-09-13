from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json
import pytest


def _hooks_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "hooks"


def _run_prompt_guard(
    prompt: str,
    project_dir: Path | None = None,
    env_override: dict[str, str | None] | None = None,
) -> subprocess.CompletedProcess:
    """Invoke prompt-submit-guard with given prompt via stdin."""
    hooks = _hooks_dir()
    script = hooks / "prompt-submit-guard.sh"
    if not script.exists():
        pytest.skip("prompt-submit-guard.sh not found")
    env = {
        "PENDING_QUEUE_ENABLED": "1",
        "BLOCK_ESCALATION_ENABLED": "0",  # avoid thegent call in $block tests
    }
    if project_dir:
        env["PROJECT_DIR"] = str(project_dir)
    if env_override:
        env.update(env_override)
    stdin = json.dumps({"tool_input": {"prompt": prompt}, "cwd": str(project_dir or ".").decode()})
    return subprocess.run(
        [str(script)],
        input=stdin,
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, **env},
        cwd=str(project_dir or Path.cwd()),
    )


class TestPromptSubmitGuardDefer:
    """Unit tests: prompt-submit-guard $defer/$pending detection."""

    def test_defer_blocks_prompt_and_appends_to_queue(self, tmp_path: Path) -> None:
        """$defer blocks prompt (exit 1) and appends to pending-queue.jsonl."""
        queue_dir = tmp_path / ".claude"
        queue_dir.mkdir()
        queue_file = queue_dir / "pending-queue.jsonl"
        queue_file.write_text("")  # start empty
        result = _run_prompt_guard("Add tests for auth.py $defer", project_dir=tmp_path)
        assert result.returncode == 1
        assert "Queued" in result.stdout or "queued" in result.stdout.lower()
        assert queue_file.exists()
        lines = queue_file.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "Add tests for auth.py" in entry.get("prompt", "")
        assert "ts" in entry

    def test_pending_same_as_defer(self, tmp_path: Path) -> None:
        """$pending behaves like $defer."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pending-queue.jsonl").write_text("")
        result = _run_prompt_guard("Refactor login $pending", project_dir=tmp_path)
        assert result.returncode == 1
        queue_file = tmp_path / ".claude" / "pending-queue.jsonl"
        assert queue_file.exists()
        entry = json.loads(queue_file.read_text().strip().splitlines()[0])
        assert "Refactor login" in entry.get("prompt", "")

    def test_empty_prompt_with_defer_rejected(self, tmp_path: Path) -> None:
        """Empty prompt with only $defer is rejected, not queued."""
        (tmp_path / ".claude").mkdir()
        result = _run_prompt_guard("$defer", project_dir=tmp_path)
        assert result.returncode == 1
        assert "Empty" in result.stdout or "empty" in result.stdout.lower()
        queue_file = tmp_path / ".claude" / "pending-queue.jsonl"
        if queue_file.exists():
            assert queue_file.read_text().strip() == ""

    def test_normal_prompt_passes(self, tmp_path: Path) -> None:
        """Prompt without $defer/$pending passes (exit 0)."""
        result = _run_prompt_guard("Add unit tests for cli_impl", project_dir=tmp_path)
        assert result.returncode == 0


def _run_harvest_pending_queue(
    project_dir: Path | None = None,
    state_dir: Path | None = None,
    queue_content: str = "",
    use_project_queue: bool = True,
) -> subprocess.CompletedProcess:
    """Invoke harvest-pending-queue with given queue state."""
    hooks = _hooks_dir()
    script = hooks / "harvest-pending-queue.sh"
    if not script.exists():
        pytest.skip("harvest-pending-queue.sh not found")
    env = {}
    if project_dir:
        env["PROJECT_DIR"] = str(project_dir)
        if use_project_queue and queue_content:
            qdir = project_dir / ".claude"
            qdir.mkdir(parents=True, exist_ok=True)
            (qdir / "pending-queue.jsonl").write_text(queue_content)
    if state_dir:
        env["STATE_DIR"] = str(state_dir)
        if not use_project_queue and queue_content:
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "pending-queue.jsonl").write_text(queue_content)
    return subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, **env},
        cwd=str(project_dir or Path.cwd()),
    )


class TestHarvestPendingQueue:
    """Unit tests: harvest-pending-queue Stop hook."""

    def test_flushes_queue_to_handoff_and_clears_queue(self, tmp_path: Path) -> None:
        """Reads queue, writes handoff, clears queue."""
        queue_content = '{"ts":"2026-02-16T12:00:00Z","prompt":"Add tests","project":"/x"}\n'
        queue_content += '{"ts":"2026-02-16T12:01:00Z","prompt":"Refactor login","project":"/x"}\n'
        result = _run_harvest_pending_queue(
            project_dir=tmp_path,
            queue_content=queue_content,
        )
        assert result.returncode == 0
        handoff = tmp_path / "docs" / "research" / "pending-handoff.md"
        assert handoff.exists()
        text = handoff.read_text()
        assert "Add tests" in text
        assert "Refactor login" in text
        assert "1." in text
        assert "2." in text
        queue_file = tmp_path / ".claude" / "pending-queue.jsonl"
        assert queue_file.read_text().strip() == ""

    def test_empty_queue_exits_zero(self, tmp_path: Path) -> None:
        """Empty queue: exit 0, no handoff created (or empty handoff)."""
        result = _run_harvest_pending_queue(project_dir=tmp_path, queue_content="")
        assert result.returncode == 0

    def test_global_queue_fallback(self, tmp_path: Path) -> None:
        """When project queue empty, uses global queue if present."""
        state = tmp_path / "state"
        state.mkdir()
        queue_content = '{"ts":"2026-02-16T12:00:00Z","prompt":"Global deferred","project":""}\n'
        (state / "pending-queue.jsonl").write_text(queue_content)
        result = _run_harvest_pending_queue(
            project_dir=tmp_path,
            state_dir=state,
            queue_content=queue_content,
            use_project_queue=False,
        )
        assert result.returncode == 0
        handoff = state / "pending-handoff.md"
        assert handoff.exists()
        assert "Global deferred" in handoff.read_text()


def _run_harvest_idea_seeds(
    claude_history: Path | None = None,
    state_dir: Path | None = None,
    cursor_projects: str = "",  # empty = skip Cursor
) -> subprocess.CompletedProcess:
    """Invoke harvest-idea-seeds with given paths."""
    scripts = Path(__file__).resolve().parent.parent / "scripts"
    script = scripts / "harvest-idea-seeds.sh"
    if not script.exists():
        pytest.skip("harvest-idea-seeds.sh not found")
    env = {
        "CURSOR_PROJECTS": cursor_projects,
        "CODEX_HISTORY": "/nonexistent/codex-history.jsonl",  # skip Codex
    }
    if claude_history:
        env["CLAUDE_HISTORY"] = str(claude_history)
    if state_dir:
        env["STATE_DIR"] = str(state_dir)
    return subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, **env},
        cwd=str(Path(__file__).resolve().parent.parent),
    )


class TestHarvestIdeaSeedsDefer:
    """Integration tests: harvest-idea-seeds $defer/$pending filter."""

    def test_harvest_defer_from_claude_history_appends_to_handoff(self, tmp_path: Path) -> None:
        """$defer in Claude history is harvested to pending-handoff.md."""
        project = tmp_path / "proj"
        project.mkdir()
        history = tmp_path / "history.jsonl"
        line = json.dumps(
            {
                "display": "Add OAuth flow $defer",
                "project": str(project).decode(),
                "timestamp": 1739620800000,
                "sessionId": "test-session",
            }
        )
        history.write_text(line + "\n")
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        result = _run_harvest_idea_seeds(
            claude_history=history,
            state_dir=state_dir,
        )
        assert result.returncode == 0
        handoff = project / "docs" / "research" / "pending-handoff.md"
        assert handoff.exists()
        text = handoff.read_text()
        assert "Add OAuth flow" in text
        assert "$defer" not in text
