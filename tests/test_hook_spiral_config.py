"""Regression spiral hook config loading tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _run_loader(config_path: Path) -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    lib_path = repo_root / "hooks" / "lib" / "spiral-config.sh"
    dispatcher_bin = repo_root / "hooks" / "hook-dispatcher" / "target" / "debug" / "hook-dispatcher"
    assert dispatcher_bin.exists(), f"hook-dispatcher binary missing at {dispatcher_bin}"
    cmd = f"""
      set -euo pipefail
      export HOOK_DISPATCHER_BIN="{dispatcher_bin}"
      source "{lib_path}"
      load_spiral_guard_config "{config_path}"
      printf 'failed=%s\\n' "$CFG_SPIRAL_MAX_FAILED_TESTS"
      printf 'flaky=%s\\n' "$CFG_SPIRAL_MAX_FLAKY_TESTS"
      printf 'pairs=%s\\n' "$CFG_SPIRAL_MAX_MISSING_TEST_PAIRS"
      printf 'types=%s\\n' "$CFG_SPIRAL_MAX_MISSING_TEST_TYPES"
      printf 'test_age=%s\\n' "$CFG_SPIRAL_MAX_TEST_EVIDENCE_AGE_MINUTES"
      printf 'build_age=%s\\n' "$CFG_SPIRAL_MAX_BUILD_EVIDENCE_AGE_MINUTES"
      printf 'e2e_age=%s\\n' "$CFG_SPIRAL_MAX_E2E_EVIDENCE_AGE_MINUTES"
      printf 'streak=%s\\n' "$CFG_SPIRAL_STREAK_TRIGGER"
      printf 'e2e=%s\\n' "$CFG_REQUIRE_E2E_FIRST"
      printf 'env=%s\\n' "$CFG_REQUIRE_ENV_READY_FIRST"
    """
    proc = subprocess.run(
        ["zsh", "-c", cmd],
        capture_output=True,
        text=True,
        check=True,
    )
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        k, v = line.strip().split("=", 1)
        out[k] = v
    return out


@pytest.mark.unit
def test_spiral_loader_uses_defaults_when_config_missing(tmp_path: Path) -> None:
    cfg = tmp_path / "no-config.yaml"
    result = _run_loader(cfg)
    assert result == {
        "failed": "10",
        "flaky": "8",
        "pairs": "0",
        "types": "0",
        "test_age": "90",
        "build_age": "90",
        "e2e_age": "180",
        "streak": "2",
        "e2e": "true",
        "env": "true",
    }


@pytest.mark.unit
def test_spiral_loader_reads_hook_config_settings_block(tmp_path: Path) -> None:
    cfg = tmp_path / "hook-config.yaml"
    cfg.write_text(
        """settings:
  cache_ttl: 600
  regression_spiral_guard:
    max_failed_tests: 21
    max_flaky_tests: 13
    max_missing_test_pairs: 2
    max_missing_test_types: 1
    max_test_evidence_age_minutes: 45
    max_build_evidence_age_minutes: 60
    max_e2e_evidence_age_minutes: 120
    streak_trigger: 4
    require_e2e_first: false
    require_env_ready_first: true
hooks:
  quality-gate:
    scope: changed
""",
        encoding="utf-8",
    )
    result = _run_loader(cfg)
    assert result == {
        "failed": "21",
        "flaky": "13",
        "pairs": "2",
        "types": "1",
        "test_age": "45",
        "build_age": "60",
        "e2e_age": "120",
        "streak": "4",
        "e2e": "false",
        "env": "true",
    }


@pytest.mark.unit
def test_spiral_loader_ignores_partial_or_invalid_values(tmp_path: Path) -> None:
    cfg = tmp_path / "hook-config.yaml"
    cfg.write_text(
        """settings:
  regression_spiral_guard:
    max_failed_tests:
    max_flaky_tests: 5
hooks:
  quality-gate:
    scope: changed
""",
        encoding="utf-8",
    )
    result = _run_loader(cfg)
    assert result["failed"] == "10"
    assert result["flaky"] == "5"
    assert result["pairs"] == "0"
    assert result["test_age"] == "90"
    assert result["build_age"] == "90"
    assert result["e2e_age"] == "180"
    assert result["streak"] == "2"
