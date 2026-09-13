"""Contract tests for WL-135 CI summary serialization.

# @trace WL-135 closeout-track-f
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "wl137_weekly_diagnosis.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wl137_weekly_diagnosis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ci_summary_runtime_buckets_and_drift_contract() -> None:
    module = _load_module()

    targets_payload = {
        "thegent": {
            "total_code": 1200,
            "code_by_language": {
                "Python": 700,
                "Rust": 300,
                "TypeScript": 100,
                "Zig": 50,
                "Mojo": 20,
                "Shell": 30,
            },
            "top_files": [
                {"path": "src/thegent/cli/commands/cli.py", "lines": 600},
                {"path": "src/thegent/cli/commands/impl.py", "lines": 500},
            ],
            "files_over_high": 4,
            "files_over_critical": 1,
        }
    }
    history = {
        "version": 1,
        "runs": [
            {
                "timestamp_utc": "2026-02-20T00:00:00+00:00",
                "targets": {
                    "thegent": {
                        "total_code": 1100,
                        "files_over_high": 3,
                        "files_over_critical": 1,
                    }
                },
            }
        ],
    }

    summary = module._build_ci_summary("2026-02-21T00:00:00+00:00", targets_payload, history)

    assert summary["timestamp_utc"] == "2026-02-21T00:00:00+00:00"
    assert "thegent" in summary["targets"]

    target = summary["targets"]["thegent"]
    assert target["total_code"] == 1200
    assert target["runtime_loc"] == {
        "python": 700,
        "rust": 300,
        "zig": 50,
        "mojo": 20,
        "typescript_js": 100,
        "other": 30,
    }
    assert target["top_files"][0]["path"] == "src/thegent/cli/commands/cli.py"
    assert target["drift"] == {
        "total_code_delta": 100,
        "files_over_high_delta": 1,
        "files_over_critical_delta": 0,
    }


def test_ci_summary_drift_defaults_when_no_history() -> None:
    module = _load_module()

    targets_payload = {
        "repo-a": {
            "total_code": 42,
            "code_by_language": {"Python": 42},
            "top_files": [{"path": "src/a.py", "lines": 42}],
            "files_over_high": 0,
            "files_over_critical": 0,
        }
    }

    summary = module._build_ci_summary("2026-02-21T00:00:00+00:00", targets_payload, {"version": 1, "runs": []})
    target = summary["targets"]["repo-a"]

    assert target["runtime_loc"] == {
        "python": 42,
        "rust": 0,
        "zig": 0,
        "mojo": 0,
        "typescript_js": 0,
        "other": 0,
    }
    assert target["drift"] == {
        "total_code_delta": 0,
        "files_over_high_delta": 0,
        "files_over_critical_delta": 0,
    }
