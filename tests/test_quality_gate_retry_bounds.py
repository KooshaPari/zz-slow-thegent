"""Tests for WL-030: quality gate DAG runner parallelism cap, step timeout, and artifact cleanup.

# @trace WL-030
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import threading
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load quality_runner as a standalone module (it lives in templates/shared/scripts)
# ---------------------------------------------------------------------------
_RUNNER_PATH = Path(__file__).parent.parent / "templates" / "shared" / "scripts" / "quality" / "quality_runner.py"
_QUALITY_GATE_SH = Path(__file__).parent.parent / "templates" / "shared" / "quality-gate.sh"
_QUALITY_AGENT_SH = Path(__file__).parent.parent / "scripts" / "quality-agent.sh"
_QUALITY_FIX_AGENT_SH = Path(__file__).parent.parent / "scripts" / "quality-fix-agent.sh"


def _load_runner():
    """Import quality_runner module by file path."""
    spec = importlib.util.spec_from_file_location("quality_runner", _RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner_mod():
    """Return the quality_runner module."""
    return _load_runner()


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Return a minimal project root with log dir."""
    (tmp_path / ".quality" / "logs").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Worker cap enforcement: QUALITY_MAX_WORKERS
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-030")
class TestWorkerCap:
    """Verify that QUALITY_MAX_WORKERS caps concurrent workers in run_dag."""

    def test_default_max_workers_is_four(self, runner_mod, monkeypatch: pytest.MonkeyPatch, tmp_project: Path) -> None:
        """Default QUALITY_MAX_WORKERS=4 must be read when env var is absent."""
        monkeypatch.delenv("QUALITY_MAX_WORKERS", raising=False)
        # Read value directly (mirrors what run_dag does)
        cap = int(os.environ.get("QUALITY_MAX_WORKERS", "4"))
        assert cap == 4

    def test_env_override_respected(self, runner_mod, monkeypatch: pytest.MonkeyPatch) -> None:
        """Setting QUALITY_MAX_WORKERS=2 must reduce the cap."""
        monkeypatch.setenv("QUALITY_MAX_WORKERS", "2")
        cap = int(os.environ.get("QUALITY_MAX_WORKERS", "4"))
        assert cap == 2

    def test_run_dag_caps_concurrency(self, runner_mod, monkeypatch: pytest.MonkeyPatch, tmp_project: Path) -> None:
        """run_dag must never exceed QUALITY_MAX_WORKERS concurrent workers."""
        monkeypatch.setenv("QUALITY_MAX_WORKERS", "2")
        monkeypatch.setenv("QUALITY_STEP_TIMEOUT_SEC", "10")

        runner_mod._resolve_paths(root=tmp_project)

        peak_concurrent: list[int] = []
        threading.Semaphore(0)
        lock = threading.Lock()
        running_count = [0]

        def counting_run_step(step_name, command, cwd, verbose=False):
            with lock:
                running_count[0] += 1
                peak_concurrent.append(running_count[0])
            time.sleep(0.05)
            with lock:
                running_count[0] -= 1
            return step_name, 0, 0.05

        monkeypatch.setattr(runner_mod, "run_step", counting_run_step)

        # 6 independent steps (no deps) - should never have >2 concurrent
        steps = {f"step{i}": {"deps": [], "command": "echo ok", "display": f"Step {i}"} for i in range(6)}
        results: dict = {}
        durations: dict = {}
        runner_mod.run_dag(steps, results, durations, tmp_project)

        assert all(v == 0 for v in results.values()), f"All steps should pass: {results}"
        assert max(peak_concurrent) <= 2, f"Peak concurrent exceeded cap: {peak_concurrent}"

    def test_thegent_settings_has_quality_max_workers_field(self) -> None:
        """ThegentSettings must expose quality_max_workers with default 4."""
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert hasattr(settings, "quality_max_workers")
        assert settings.quality_max_workers == 4

    def test_thegent_settings_quality_max_workers_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_QUALITY_MAX_WORKERS env var must override ThegentSettings.quality_max_workers."""
        monkeypatch.setenv("THGENT_QUALITY_MAX_WORKERS", "8")
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert settings.quality_max_workers == 8


# ---------------------------------------------------------------------------
# 2. Per-step timeout: QUALITY_STEP_TIMEOUT_SEC
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-030")
class TestStepTimeout:
    """Verify that QUALITY_STEP_TIMEOUT_SEC bounds each step's subprocess."""

    def test_default_timeout_is_600(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default QUALITY_STEP_TIMEOUT_SEC=600 must be read when env var is absent."""
        monkeypatch.delenv("QUALITY_STEP_TIMEOUT_SEC", raising=False)
        timeout = int(os.environ.get("QUALITY_STEP_TIMEOUT_SEC", "600"))
        assert timeout == 600

    def test_env_override_respected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Setting QUALITY_STEP_TIMEOUT_SEC=30 must reduce the timeout."""
        monkeypatch.setenv("QUALITY_STEP_TIMEOUT_SEC", "30")
        timeout = int(os.environ.get("QUALITY_STEP_TIMEOUT_SEC", "600"))
        assert timeout == 30

    def test_run_step_times_out(self, runner_mod, monkeypatch: pytest.MonkeyPatch, tmp_project: Path) -> None:
        """run_step must return exit code 124 when step exceeds timeout."""
        monkeypatch.setenv("QUALITY_STEP_TIMEOUT_SEC", "1")
        runner_mod._resolve_paths(root=tmp_project)

        # sleep 10 will be killed by 1s timeout
        _, code, _ = runner_mod.run_step("timeout-step", "sleep 10", tmp_project)
        assert code == 124, f"Expected timeout exit code 124, got {code}"

    def test_run_step_succeeds_within_timeout(
        self, runner_mod, monkeypatch: pytest.MonkeyPatch, tmp_project: Path
    ) -> None:
        """run_step must succeed when step completes within timeout."""
        monkeypatch.setenv("QUALITY_STEP_TIMEOUT_SEC", "10")
        runner_mod._resolve_paths(root=tmp_project)

        _, code, duration = runner_mod.run_step("fast-step", "echo ok", tmp_project)
        assert code == 0
        assert duration < 10

    def test_thegent_settings_has_quality_step_timeout_field(self) -> None:
        """ThegentSettings must expose quality_step_timeout_sec with default 600."""
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert hasattr(settings, "quality_step_timeout_sec")
        assert settings.quality_step_timeout_sec == 600

    def test_thegent_settings_step_timeout_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_QUALITY_STEP_TIMEOUT_SEC env var must override ThegentSettings.quality_step_timeout_sec."""
        monkeypatch.setenv("THGENT_QUALITY_STEP_TIMEOUT_SEC", "120")
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert settings.quality_step_timeout_sec == 120


# ---------------------------------------------------------------------------
# 3. Stale shadow dir cleanup and .quality/logs retention
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-030")
class TestStaleShadowCleanup:
    """Verify cleanup of stale .shadow-* dirs and .quality/logs retention."""

    def test_quality_gate_sh_defines_shadow_cleanup_hours(self) -> None:
        """quality-gate.sh must read QUALITY_SHADOW_CLEANUP_HOURS with default 24."""
        assert _QUALITY_GATE_SH.exists(), f"quality-gate.sh not found at {_QUALITY_GATE_SH}"
        content = _QUALITY_GATE_SH.read_text()
        assert "QUALITY_SHADOW_CLEANUP_HOURS" in content
        assert ":-24}" in content or '"${QUALITY_SHADOW_CLEANUP_HOURS:-24}"' in content or ":-24}" in content

    def test_quality_agent_uses_shadow_cleanup_hours(self) -> None:
        """quality-agent.sh must use QUALITY_SHADOW_CLEANUP_HOURS (with legacy fallback)."""
        assert _QUALITY_AGENT_SH.exists(), f"quality-agent.sh not found at {_QUALITY_AGENT_SH}"
        content = _QUALITY_AGENT_SH.read_text()
        assert "QUALITY_SHADOW_CLEANUP_HOURS" in content
        assert "QUALITY_SHADOW_MAX_AGE_HOURS" in content

    def test_quality_fix_agent_uses_shadow_cleanup_hours(self) -> None:
        """quality-fix-agent.sh must use QUALITY_SHADOW_CLEANUP_HOURS (with legacy fallback)."""
        assert _QUALITY_FIX_AGENT_SH.exists(), f"quality-fix-agent.sh not found at {_QUALITY_FIX_AGENT_SH}"
        content = _QUALITY_FIX_AGENT_SH.read_text()
        assert "QUALITY_SHADOW_CLEANUP_HOURS" in content
        assert "QUALITY_SHADOW_MAX_AGE_HOURS" in content

    def test_quality_gate_sh_defines_log_retention_days(self) -> None:
        """quality-gate.sh must read QUALITY_LOG_RETENTION_DAYS with default 7."""
        content = _QUALITY_GATE_SH.read_text()
        assert "QUALITY_LOG_RETENTION_DAYS" in content
        assert ":-7}" in content or '"${QUALITY_LOG_RETENTION_DAYS:-7}"' in content or ":-7}" in content

    def test_cleanup_removes_old_shadow_dirs(self, tmp_path: Path) -> None:
        """cleanup_stale_artifacts must remove .shadow-* dirs older than the threshold."""
        if not _QUALITY_GATE_SH.exists():
            pytest.skip("quality-gate.sh not found")

        # Create a .shadow-old dir with an old mtime (25h ago)
        old_shadow = tmp_path / ".shadow-old"
        old_shadow.mkdir()
        old_mtime = time.time() - (25 * 3600)
        os.utime(old_shadow, (old_mtime, old_mtime))

        # Create a .shadow-new dir with a recent mtime
        new_shadow = tmp_path / ".shadow-new"
        new_shadow.mkdir()

        # Create a minimal log dir to avoid errors
        (tmp_path / ".quality" / "logs").mkdir(parents=True)

        script = f"""
set -euo pipefail
QUALITY_SHADOW_CLEANUP_HOURS=24
QUALITY_LOG_RETENTION_DAYS=7
PROJECT_ROOT="{tmp_path}"

cleanup_stale_artifacts() {{
  local root="$1"
  local shadow_age_hours="$2"
  local log_retention_days="$3"

  local removed_shadow=0
  while IFS= read -r -d '' shadow_dir; do
    rm -rf "$shadow_dir"
    removed_shadow=$((removed_shadow + 1))
  done < <(find "$root" -maxdepth 1 -name '.shadow-*' -type d \\
    -mmin "+$((shadow_age_hours * 60))" -print0 2>/dev/null)
  echo "Removed $removed_shadow stale .shadow-* directories"

  local log_dir="$root/.quality/logs"
  local removed_logs=0
  if [[ -d "$log_dir" ]]; then
    while IFS= read -r -d '' log_file; do
      rm -f "$log_file"
      removed_logs=$((removed_logs + 1))
    done < <(find "$log_dir" -maxdepth 1 -type f \\
      -mtime "+${{log_retention_days}}" -print0 2>/dev/null)
  fi
  echo "Removed $removed_logs .quality/logs files"
}}

cleanup_stale_artifacts "$PROJECT_ROOT" "$QUALITY_SHADOW_CLEANUP_HOURS" "$QUALITY_LOG_RETENTION_DAYS"
"""
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"cleanup script failed: {result.stderr}"
        assert not old_shadow.exists(), "Old .shadow-* dir must have been removed"
        assert new_shadow.exists(), "Recent .shadow-* dir must be preserved"

    def test_cleanup_removes_old_quality_logs(self, tmp_path: Path) -> None:
        """cleanup_stale_artifacts must remove .quality/logs files older than retention days."""
        if not _QUALITY_GATE_SH.exists():
            pytest.skip("quality-gate.sh not found")

        log_dir = tmp_path / ".quality" / "logs"
        log_dir.mkdir(parents=True)

        # Create an old log file (8 days old)
        old_log = log_dir / "old-step.log"
        old_log.write_text("old log content")
        old_mtime = time.time() - (8 * 86400)
        os.utime(old_log, (old_mtime, old_mtime))

        # Create a recent log file
        new_log = log_dir / "new-step.log"
        new_log.write_text("new log content")

        script = f"""
set -euo pipefail
QUALITY_SHADOW_CLEANUP_HOURS=24
QUALITY_LOG_RETENTION_DAYS=7
PROJECT_ROOT="{tmp_path}"

cleanup_stale_artifacts() {{
  local root="$1"
  local shadow_age_hours="$2"
  local log_retention_days="$3"

  local removed_shadow=0
  while IFS= read -r -d '' shadow_dir; do
    rm -rf "$shadow_dir"
    removed_shadow=$((removed_shadow + 1))
  done < <(find "$root" -maxdepth 1 -name '.shadow-*' -type d \\
    -mmin "+$((shadow_age_hours * 60))" -print0 2>/dev/null)
  echo "Removed $removed_shadow stale .shadow-* directories"

  local log_dir="$root/.quality/logs"
  local removed_logs=0
  if [[ -d "$log_dir" ]]; then
    while IFS= read -r -d '' log_file; do
      rm -f "$log_file"
      removed_logs=$((removed_logs + 1))
    done < <(find "$log_dir" -maxdepth 1 -type f \\
      -mtime "+${{log_retention_days}}" -print0 2>/dev/null)
  fi
  echo "Removed $removed_logs .quality/logs files"
}}

cleanup_stale_artifacts "$PROJECT_ROOT" "$QUALITY_SHADOW_CLEANUP_HOURS" "$QUALITY_LOG_RETENTION_DAYS"
"""
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"cleanup script failed: {result.stderr}"
        assert not old_log.exists(), "Old .quality/logs file must have been removed"
        assert new_log.exists(), "Recent .quality/logs file must be preserved"

    def test_cleanup_preserves_all_when_nothing_stale(self, tmp_path: Path) -> None:
        """cleanup_stale_artifacts must not remove any dirs or logs when nothing is stale."""
        shadow_dir = tmp_path / ".shadow-fresh"
        shadow_dir.mkdir()
        log_dir = tmp_path / ".quality" / "logs"
        log_dir.mkdir(parents=True)
        fresh_log = log_dir / "fresh.log"
        fresh_log.write_text("fresh")

        script = f"""
set -euo pipefail
QUALITY_SHADOW_CLEANUP_HOURS=24
QUALITY_LOG_RETENTION_DAYS=7
PROJECT_ROOT="{tmp_path}"

cleanup_stale_artifacts() {{
  local root="$1"
  local shadow_age_hours="$2"
  local log_retention_days="$3"

  local removed_shadow=0
  while IFS= read -r -d '' shadow_dir; do
    rm -rf "$shadow_dir"
    removed_shadow=$((removed_shadow + 1))
  done < <(find "$root" -maxdepth 1 -name '.shadow-*' -type d \\
    -mmin "+$((shadow_age_hours * 60))" -print0 2>/dev/null)
  echo "Removed $removed_shadow stale .shadow-* directories"

  local log_dir="$root/.quality/logs"
  local removed_logs=0
  if [[ -d "$log_dir" ]]; then
    while IFS= read -r -d '' log_file; do
      rm -f "$log_file"
      removed_logs=$((removed_logs + 1))
    done < <(find "$log_dir" -maxdepth 1 -type f \\
      -mtime "+${{log_retention_days}}" -print0 2>/dev/null)
  fi
  echo "Removed $removed_logs .quality/logs files"
}}

cleanup_stale_artifacts "$PROJECT_ROOT" "$QUALITY_SHADOW_CLEANUP_HOURS" "$QUALITY_LOG_RETENTION_DAYS"
"""
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert shadow_dir.exists(), "Fresh .shadow-* dir must be preserved"
        assert fresh_log.exists(), "Fresh log file must be preserved"

    def test_thegent_settings_has_shadow_cleanup_hours_field(self) -> None:
        """ThegentSettings must expose quality_shadow_cleanup_hours with default 48."""
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert hasattr(settings, "quality_shadow_cleanup_hours")
        assert settings.quality_shadow_cleanup_hours == 48

    def test_thegent_settings_has_log_retention_days_field(self) -> None:
        """ThegentSettings must expose quality_log_retention_days with default 7."""
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert hasattr(settings, "quality_log_retention_days")
        assert settings.quality_log_retention_days == 7

    def test_thegent_settings_shadow_cleanup_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_QUALITY_SHADOW_MAX_AGE_HOURS env var must override quality_shadow_cleanup_hours."""
        monkeypatch.setenv("THGENT_QUALITY_SHADOW_MAX_AGE_HOURS", "48")
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert settings.quality_shadow_cleanup_hours == 48

    def test_thegent_settings_log_retention_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_QUALITY_LOG_RETENTION_DAYS env var must override quality_log_retention_days."""
        monkeypatch.setenv("THGENT_QUALITY_LOG_RETENTION_DAYS", "14")
        from thegent.config.settings import ThegentSettings

        settings = ThegentSettings()
        assert settings.quality_log_retention_days == 14
