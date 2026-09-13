"""Tests for SQLite-backed ProjectRegistry (wp-71001-registry-db)."""

from __future__ import annotations

import sqlite3
from pathlib import Path  # noqa: TC003 -- used at runtime for Path construction

import orjson as json
import pytest

from thegent.discovery.projects import ProjectRegistry


@pytest.mark.unit
def test_schema_created_on_init(tmp_path: Path) -> None:
    # @trace FR-AGT-020
    registry = ProjectRegistry(global_config_dir=tmp_path)

    assert registry.registry_db.exists()

    with sqlite3.connect(registry.registry_db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert "projects" in tables


@pytest.mark.unit
def test_migrates_jsonl_registry_into_sqlite(tmp_path: Path) -> None:
    # @trace FR-AGT-020
    jsonl_path = tmp_path / "project_registry.jsonl"
    rows = [
        {
            "id": "proj-alpha",
            "path": str((tmp_path / "alpha").resolve()),
            "name": "alpha",
            "last_active": "2026-02-20T00:00:00+00:00",
        },
        {
            "path": str((tmp_path / "beta").resolve()),
            "name": "beta",
            "last_active": "2026-02-20T00:10:00+00:00",
        },
    ]
    jsonl_path.write_text("\n".join(json.dumps(r).decode() for r in rows) + "\n", encoding="utf-8")

    registry = ProjectRegistry(global_config_dir=tmp_path)
    projects = registry.list_projects()

    assert len(projects) == 2
    by_name = {p["name"]: p for p in projects}
    assert by_name["alpha"]["id"] == "proj-alpha"
    assert by_name["beta"]["id"]


@pytest.mark.unit
def test_register_and_update_activity_crud_lifecycle(tmp_path: Path) -> None:
    # @trace FR-AGT-020
    registry = ProjectRegistry(global_config_dir=tmp_path)

    project_path = tmp_path / "my-project"
    project_path.mkdir()

    registry.register_project(project_path, "My Project")
    first = registry.list_projects()
    assert len(first) == 1

    first_entry = first[0]
    assert first_entry["name"] == "My Project"
    assert first_entry["path"] == str(project_path.resolve())

    # Duplicate register should update activity, not create a second row.
    registry.register_project(project_path, "My Project")
    second = registry.list_projects()
    assert len(second) == 1
    assert second[0]["id"] == first_entry["id"]
    assert second[0]["last_active"] >= first_entry["last_active"]

    # Explicit update keeps row count and path stable.
    registry.update_activity(project_path)
    third = registry.list_projects()
    assert len(third) == 1
    assert third[0]["path"] == first_entry["path"]
    assert third[0]["last_active"] >= second[0]["last_active"]
