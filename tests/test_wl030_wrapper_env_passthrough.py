"""WL-030 wrapper env propagation checks (script parsing only)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
QUALITY_AGENT = REPO_ROOT / "scripts" / "quality-agent.sh"
QUALITY_FIX_AGENT = REPO_ROOT / "scripts" / "quality-fix-agent.sh"
QUALITY_GATE_TEMPLATE = REPO_ROOT / "templates" / "shared" / "quality-gate.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_shadow_arg(script_text: str) -> str:
    match = re.search(r'--shadow-max-age-hours\s+"([^"]+)"', script_text)
    assert match, "expected --shadow-max-age-hours argument in wrapper"
    return match.group(1)


def _extract_log_retention_arg(script_text: str) -> str:
    match = re.search(r'--log-max-age-days\s+"([^"]+)"', script_text)
    assert match, "expected --log-max-age-days argument in wrapper"
    return match.group(1)


def test_quality_max_workers_is_passthrough_in_quality_agent_wrapper() -> None:
    script = _read(QUALITY_AGENT)
    assert 'MAX_WORKERS="${QUALITY_MAX_WORKERS:-2}"' in script
    assert 'QUALITY_MAX_WORKERS="$MAX_WORKERS" task quality:dag' in script


def test_shadow_cleanup_hours_has_default_fallback_in_wrappers_and_gate_template() -> None:
    for wrapper in (QUALITY_AGENT, QUALITY_FIX_AGENT):
        script = _read(wrapper)
        shadow_arg = _extract_shadow_arg(script)
        assert shadow_arg == "${shadow_cleanup_hours}"
        assert "QUALITY_SHADOW_CLEANUP_HOURS" in script
        assert "QUALITY_SHADOW_MAX_AGE_HOURS" in script
        assert ":-24}}" in script or ":-24}" in script

    gate_template = _read(QUALITY_GATE_TEMPLATE)
    assert 'QUALITY_SHADOW_CLEANUP_HOURS="${QUALITY_SHADOW_CLEANUP_HOURS:-24}"' in gate_template


def test_retention_var_passthrough_is_consistent_in_wrappers() -> None:
    expected = "${QUALITY_LOG_RETENTION_DAYS:-7}"
    for wrapper in (QUALITY_AGENT, QUALITY_FIX_AGENT):
        assert _extract_log_retention_arg(_read(wrapper)) == expected
