from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_rust_links_conflicts.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "check_rust_links_conflicts", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_report_from_metadata_passes_when_links_are_unique() -> None:
    mod = _load_module()
    metadata = {
        "packages": [
            {"id": "a 0.1.0", "name": "crate-a", "version": "0.1.0", "links": "python"},
            {
                "id": "b 0.2.0",
                "name": "crate-b",
                "version": "0.2.0",
                "links": "sqlite3",
            },
            {"id": "c 0.3.0", "name": "crate-c", "version": "0.3.0"},
        ]
    }
    report = mod.build_report_from_metadata(metadata)
    assert report["ok"] is True
    assert report["conflicts"] == []
    assert report["total_links_entries"] == 2


def test_build_report_from_metadata_fails_when_links_have_multiple_providers() -> None:
    mod = _load_module()
    metadata = {
        "packages": [
            {"id": "p1", "name": "pyo3-ffi", "version": "0.22.4", "links": "python"},
            {"id": "p2", "name": "pyo3-ffi", "version": "0.23.4", "links": "python"},
            {"id": "x1", "name": "other", "version": "1.0.0", "links": "otherlib"},
        ]
    }
    report = mod.build_report_from_metadata(metadata)
    assert report["ok"] is False
    assert report["total_links_entries"] == 2
    assert len(report["conflicts"]) == 1
    conflict = report["conflicts"][0]
    assert conflict["links"] == "python"
    assert conflict["providers"] == ["pyo3-ffi@0.22.4", "pyo3-ffi@0.23.4"]


def test_taskfile_wires_links_conflict_check_before_pyo3_drift() -> None:
    taskfile = yaml.safe_load((ROOT / "Taskfile.yml").read_text(encoding="utf-8"))

    links_task = taskfile["tasks"]["quality:rust:links-conflicts"]
    assert links_task["cmds"] == ["uv run python scripts/check_rust_links_conflicts.py"]

    quality_cmds = taskfile["tasks"]["quality"]["cmds"]
    assert {"task": "quality:rust:links-conflicts"} in quality_cmds
    assert {"task": "quality:rust:pyo3-drift"} in quality_cmds
    assert quality_cmds.index(
        {"task": "quality:rust:links-conflicts"}
    ) < quality_cmds.index({"task": "quality:rust:pyo3-drift"})
