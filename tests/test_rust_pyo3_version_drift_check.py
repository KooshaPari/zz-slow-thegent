from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_rust_pyo3_version_drift.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_rust_pyo3_version_drift", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _init_workspace(tmp_path: Path, *, workspace_pyo3: str | None = None) -> None:
    workspace_dep = f'pyo3 = "{workspace_pyo3}"' if workspace_pyo3 is not None else ""
    _write_manifest(
        tmp_path / "crates" / "Cargo.toml",
        f"""
        [workspace]
        members = ["crate-a", "crate-b", "crate-c"]

        [workspace.dependencies]
        {workspace_dep}
        """,
    )


def test_build_report_passes_with_uniform_version_including_optional_and_target_tables(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    _init_workspace(tmp_path)
    _write_manifest(
        tmp_path / "crates" / "crate-a" / "Cargo.toml",
        """
        [package]
        name = "crate-a"
        version = "0.1.0"

        [dependencies]
        pyo3 = { version = "0.23.4", optional = true }
        """,
    )
    _write_manifest(
        tmp_path / "crates" / "crate-b" / "Cargo.toml",
        """
        [package]
        name = "crate-b"
        version = "0.1.0"

        [dev-dependencies]
        pyo3 = { version = "0.23.4" }
        """,
    )
    _write_manifest(
        tmp_path / "crates" / "crate-c" / "Cargo.toml",
        """
        [package]
        name = "crate-c"
        version = "0.1.0"

        [target.'cfg(unix)'.dependencies]
        pyo3 = { version = "0.23.4", optional = true }
        """,
    )

    report = mod.build_report(tmp_path)
    assert report["ok"] is True
    assert report["drift"] is False
    assert report["versions"] == ["0.23.4"]
    assert report["total_references"] == 3


def test_build_report_fails_when_versions_drift(tmp_path: Path) -> None:
    mod = _load_module()
    _init_workspace(tmp_path)
    _write_manifest(
        tmp_path / "crates" / "crate-a" / "Cargo.toml",
        """
        [package]
        name = "crate-a"
        version = "0.1.0"

        [dependencies]
        pyo3 = { version = "0.23.4" }
        """,
    )
    _write_manifest(
        tmp_path / "crates" / "crate-b" / "Cargo.toml",
        """
        [package]
        name = "crate-b"
        version = "0.1.0"

        [dependencies]
        pyo3 = { version = "0.24.0" }
        """,
    )

    report = mod.build_report(tmp_path)
    assert report["ok"] is False
    assert report["drift"] is True
    assert report["versions"] == ["0.23.4", "0.24.0"]


def test_build_report_resolves_workspace_version_and_package_alias(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    _init_workspace(tmp_path, workspace_pyo3="0.23.4")
    _write_manifest(
        tmp_path / "crates" / "crate-a" / "Cargo.toml",
        """
        [package]
        name = "crate-a"
        version = "0.1.0"

        [dependencies]
        py = { package = "pyo3", workspace = true, optional = true }
        """,
    )

    report = mod.build_report(tmp_path)
    assert report["ok"] is True
    assert report["versions"] == ["0.23.4"]
    assert any(ref["dependency"] == "py" for ref in report["references"])


def test_build_report_fails_for_workspace_true_without_workspace_version(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    _init_workspace(tmp_path, workspace_pyo3=None)
    _write_manifest(
        tmp_path / "crates" / "crate-a" / "Cargo.toml",
        """
        [package]
        name = "crate-a"
        version = "0.1.0"

        [dependencies]
        pyo3 = { workspace = true }
        """,
    )

    report = mod.build_report(tmp_path)
    assert report["ok"] is False
    assert report["errors"]
    assert "workspace=true but workspace.dependencies.pyo3 has no version" in report["errors"][0]


def test_taskfile_wires_pyo3_drift_check_before_runtime_contracts() -> None:
    taskfile = yaml.safe_load((ROOT / "Taskfile.yml").read_text(encoding="utf-8"))
    pyo3_task = taskfile["tasks"]["quality:rust:pyo3-drift"]
    assert pyo3_task["cmds"] == ["uv run python scripts/check_rust_pyo3_version_drift.py"]

    quality_cmds = taskfile["tasks"]["quality"]["cmds"]
    assert {"task": "quality:rust:pyo3-drift"} in quality_cmds
    assert quality_cmds.index({"task": "quality:rust:pyo3-drift"}) < quality_cmds.index(
        {"task": "quality:runtime-contracts"}
    )
