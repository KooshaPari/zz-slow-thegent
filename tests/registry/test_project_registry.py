"""Tests for ProjectRegistry SQLite-backed registry.

WBS: wp-71001-registry-db
FR Traceability: FR-VER-001 (project registry and episode tracking)
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from thegent.registry.project_registry import (
    EpisodeRecord,
    EpisodeStatus,
    ProjectRecord,
    ProjectRegistry,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a temporary database path for test isolation."""
    return tmp_path / "test_registry.db"


@pytest.fixture
def registry(db_path: Path) -> ProjectRegistry:
    """Return a fresh ProjectRegistry backed by a temp DB."""
    return ProjectRegistry(db_path=db_path)


# ---------------------------------------------------------------------------
# ProjectRecord model tests
# ---------------------------------------------------------------------------


class TestProjectRecord:
    """Tests for the ProjectRecord pydantic model."""

    def test_create_project_record(self) -> None:
        record = ProjectRecord(name="my-project", path="/tmp/my-project")
        assert record.name == "my-project"
        assert record.path == "/tmp/my-project"
        assert record.id is not None
        assert record.created_at is not None
        assert record.metadata == {}

    def test_project_record_with_metadata(self) -> None:
        record = ProjectRecord(
            name="proj",
            path="/tmp/proj",
            metadata={"type": "milestone", "tag": "m-reliability"},
        )
        assert record.metadata["type"] == "milestone"
        assert record.metadata["tag"] == "m-reliability"

    def test_project_record_auto_id(self) -> None:
        r1 = ProjectRecord(name="a", path="/a")
        r2 = ProjectRecord(name="b", path="/b")
        assert r1.id != r2.id


# ---------------------------------------------------------------------------
# EpisodeRecord model tests
# ---------------------------------------------------------------------------


class TestEpisodeRecord:
    """Tests for the EpisodeRecord pydantic model."""

    def test_create_episode_record(self) -> None:
        record = EpisodeRecord(
            project_id="proj-1",
            agent_id="agent-x",
            status=EpisodeStatus.RUNNING,
        )
        assert record.project_id == "proj-1"
        assert record.agent_id == "agent-x"
        assert record.status == EpisodeStatus.RUNNING
        assert record.started_at is not None
        assert record.ended_at is None

    def test_episode_record_with_metadata(self) -> None:
        record = EpisodeRecord(
            project_id="proj-1",
            agent_id="agent-x",
            status=EpisodeStatus.COMPLETED,
            metadata={"task_id": "WP-1001"},
        )
        assert record.metadata["task_id"] == "WP-1001"

    def test_episode_status_values(self) -> None:
        assert EpisodeStatus.RUNNING == "running"
        assert EpisodeStatus.COMPLETED == "completed"
        assert EpisodeStatus.FAILED == "failed"
        assert EpisodeStatus.SUSPENDED == "suspended"


# ---------------------------------------------------------------------------
# Registry initialization tests
# ---------------------------------------------------------------------------


class TestRegistryInit:
    """Tests for ProjectRegistry initialization and DB setup."""

    def test_creates_db_file(self, db_path: Path) -> None:
        ProjectRegistry(db_path=db_path)
        assert db_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        deep_path = tmp_path / "a" / "b" / "c" / "registry.db"
        ProjectRegistry(db_path=deep_path)
        assert deep_path.exists()

    def test_wal_mode_enabled(self, db_path: Path) -> None:
        ProjectRegistry(db_path=db_path)
        conn = sqlite3.connect(str(db_path))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_tables_created(self, db_path: Path) -> None:
        ProjectRegistry(db_path=db_path)
        conn = sqlite3.connect(str(db_path))
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert "projects" in tables
        assert "episodes" in tables
        assert "schema_version" in tables

    def test_schema_version_initialized(self, db_path: Path) -> None:
        ProjectRegistry(db_path=db_path)
        conn = sqlite3.connect(str(db_path))
        version_row = conn.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        assert version_row is not None
        assert version_row[0] == 1

    def test_legacy_db_bootstrap_without_schema_version(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO projects (id, name, path, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("legacy-1", "legacy", "/legacy", datetime.now(UTC).isoformat(), "{}"),
        )
        conn.commit()
        conn.close()

        registry = ProjectRegistry(db_path=db_path)
        migrated = registry.get_project("legacy-1")

        assert migrated is not None
        assert migrated.name == "legacy"

        conn = sqlite3.connect(str(db_path))
        version_row = conn.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1").fetchone()
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert version_row is not None
        assert version_row[0] == 1
        assert "episodes" in tables


# ---------------------------------------------------------------------------
# Project CRUD tests
# ---------------------------------------------------------------------------


class TestProjectCRUD:
    """Tests for project registration and retrieval."""

    def test_register_project(self, registry: ProjectRegistry) -> None:
        project = registry.register_project(name="test-proj", path="/tmp/test")
        assert project.name == "test-proj"
        assert project.path == "/tmp/test"
        assert project.id is not None

    def test_get_project_by_id(self, registry: ProjectRegistry) -> None:
        created = registry.register_project(name="proj-a", path="/a")
        fetched = registry.get_project(created.id)
        assert fetched is not None
        assert fetched.name == "proj-a"
        assert fetched.path == "/a"

    def test_get_project_not_found(self, registry: ProjectRegistry) -> None:
        result = registry.get_project("nonexistent-id")
        assert result is None

    def test_list_projects_empty(self, registry: ProjectRegistry) -> None:
        projects = registry.list_projects()
        assert projects == []

    def test_list_projects_multiple(self, registry: ProjectRegistry) -> None:
        registry.register_project(name="alpha", path="/alpha")
        registry.register_project(name="beta", path="/beta")
        registry.register_project(name="gamma", path="/gamma")
        projects = registry.list_projects()
        assert len(projects) == 3
        names = {p.name for p in projects}
        assert names == {"alpha", "beta", "gamma"}

    def test_register_project_with_metadata(self, registry: ProjectRegistry) -> None:
        project = registry.register_project(
            name="milestone-proj",
            path="/tmp/ms",
            metadata={"type": "milestone", "label": "v1.0"},
        )
        fetched = registry.get_project(project.id)
        assert fetched is not None
        assert fetched.metadata["type"] == "milestone"
        assert fetched.metadata["label"] == "v1.0"

    def test_register_project_preserves_created_at(self, registry: ProjectRegistry) -> None:
        project = registry.register_project(name="ts-test", path="/ts")
        fetched = registry.get_project(project.id)
        assert fetched is not None
        assert fetched.created_at == project.created_at


# ---------------------------------------------------------------------------
# Episode CRUD tests
# ---------------------------------------------------------------------------


class TestEpisodeCRUD:
    """Tests for episode creation, update, and retrieval."""

    def test_create_episode(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="ep-proj", path="/ep")
        episode = registry.create_episode(project_id=proj.id, agent_id="agent-1")
        assert episode.project_id == proj.id
        assert episode.agent_id == "agent-1"
        assert episode.status == EpisodeStatus.RUNNING

    def test_update_episode_status(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="ep-proj", path="/ep")
        episode = registry.create_episode(project_id=proj.id, agent_id="agent-1")
        updated = registry.update_episode(
            episode_id=episode.id,
            status=EpisodeStatus.COMPLETED,
        )
        assert updated is not None
        assert updated.status == EpisodeStatus.COMPLETED
        assert updated.ended_at is not None

    def test_update_episode_metadata(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="ep-proj", path="/ep")
        episode = registry.create_episode(project_id=proj.id, agent_id="agent-1")
        updated = registry.update_episode(
            episode_id=episode.id,
            metadata={"summary": "did some work"},
        )
        assert updated is not None
        assert updated.metadata["summary"] == "did some work"

    def test_update_nonexistent_episode(self, registry: ProjectRegistry) -> None:
        result = registry.update_episode(
            episode_id="no-such-id",
            status=EpisodeStatus.FAILED,
        )
        assert result is None

    def test_get_episodes_for_project(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="multi-ep", path="/multi")
        registry.create_episode(project_id=proj.id, agent_id="agent-1")
        registry.create_episode(project_id=proj.id, agent_id="agent-2")
        registry.create_episode(project_id=proj.id, agent_id="agent-3")
        episodes = registry.get_episodes_for_project(proj.id)
        assert len(episodes) == 3
        agent_ids = {e.agent_id for e in episodes}
        assert agent_ids == {"agent-1", "agent-2", "agent-3"}

    def test_get_episodes_empty(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="empty-ep", path="/empty")
        episodes = registry.get_episodes_for_project(proj.id)
        assert episodes == []

    def test_episode_ended_at_set_on_terminal_status(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="end-test", path="/end")
        episode = registry.create_episode(project_id=proj.id, agent_id="agent-1")
        assert episode.ended_at is None
        updated = registry.update_episode(
            episode_id=episode.id,
            status=EpisodeStatus.FAILED,
        )
        assert updated is not None
        assert updated.ended_at is not None

    def test_episode_with_initial_metadata(self, registry: ProjectRegistry) -> None:
        proj = registry.register_project(name="meta-ep", path="/meta")
        episode = registry.create_episode(
            project_id=proj.id,
            agent_id="agent-1",
            metadata={"task_id": "WP-1001"},
        )
        assert episode.metadata["task_id"] == "WP-1001"


# ---------------------------------------------------------------------------
# Persistence / reload tests
# ---------------------------------------------------------------------------


class TestPersistence:
    """Tests that data survives registry re-instantiation."""

    def test_project_persists_across_instances(self, db_path: Path) -> None:
        reg1 = ProjectRegistry(db_path=db_path)
        created = reg1.register_project(name="persist-test", path="/persist")

        reg2 = ProjectRegistry(db_path=db_path)
        fetched = reg2.get_project(created.id)
        assert fetched is not None
        assert fetched.name == "persist-test"

    def test_episode_persists_across_instances(self, db_path: Path) -> None:
        reg1 = ProjectRegistry(db_path=db_path)
        proj = reg1.register_project(name="ep-persist", path="/ep-persist")
        episode = reg1.create_episode(project_id=proj.id, agent_id="agent-persist")

        reg2 = ProjectRegistry(db_path=db_path)
        episodes = reg2.get_episodes_for_project(proj.id)
        assert len(episodes) == 1
        assert episodes[0].id == episode.id
        assert episodes[0].agent_id == "agent-persist"
