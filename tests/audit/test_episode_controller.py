"""Tests for EpisodeController.

WBS: wp-71003-episode-ctrl
FR Traceability: FR-VER-004 (episode lifecycle management)
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest

from thegent.audit.episode_controller import EpisodeController
from thegent.audit.shadow_audit_git import ShadowAuditGit
from thegent.registry.project_registry import EpisodeStatus, ProjectRegistry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_episode.db"


@pytest.fixture
def registry(db_path: Path) -> ProjectRegistry:
    return ProjectRegistry(db_path=db_path)


@pytest.fixture
def shadow(db_path: Path) -> ShadowAuditGit:
    return ShadowAuditGit(db_path=db_path)


@pytest.fixture
def project_id(registry: ProjectRegistry) -> str:
    project = registry.register_project(name="ep-test-proj", path="/tmp/ep-test")
    return project.id


@pytest.fixture
def controller(registry: ProjectRegistry, shadow: ShadowAuditGit, project_id: str) -> EpisodeController:
    return EpisodeController(
        project_id=project_id,
        agent_id="test-agent",
        registry=registry,
        shadow=shadow,
    )


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestStart:
    def test_start_creates_episode(self, controller: EpisodeController) -> None:
        controller.start()
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.RUNNING

    def test_start_records_audit_entry(
        self, controller: EpisodeController, shadow: ShadowAuditGit, project_id: str
    ) -> None:
        controller.start()
        entries = shadow.get_audit_log(project_id)
        assert len(entries) == 1
        assert "episode_start" in entries[0].message

    def test_start_twice_raises(self, controller: EpisodeController) -> None:
        controller.start()
        with pytest.raises(RuntimeError, match="already started"):
            controller.start()


class TestEnd:
    def test_end_completes_episode(self, controller: EpisodeController) -> None:
        controller.start()
        controller.end()
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.COMPLETED

    def test_end_records_audit_entry(
        self, controller: EpisodeController, shadow: ShadowAuditGit, project_id: str
    ) -> None:
        controller.start()
        controller.end()
        entries = shadow.get_audit_log(project_id)
        assert len(entries) == 2
        assert "episode_end" in entries[1].message

    def test_end_without_start_raises(self, controller: EpisodeController) -> None:
        with pytest.raises(RuntimeError, match="not started"):
            controller.end()

    def test_end_with_failure(self, controller: EpisodeController) -> None:
        controller.start()
        controller.end(failed=True)
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.FAILED


class TestSuspendResume:
    def test_suspend(self, controller: EpisodeController) -> None:
        controller.start()
        controller.suspend()
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.SUSPENDED

    def test_resume_after_suspend(self, controller: EpisodeController) -> None:
        controller.start()
        controller.suspend()
        controller.resume()
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.RUNNING

    def test_suspend_without_start_raises(self, controller: EpisodeController) -> None:
        with pytest.raises(RuntimeError, match="not started"):
            controller.suspend()

    def test_resume_without_suspend_raises(self, controller: EpisodeController) -> None:
        controller.start()
        with pytest.raises(RuntimeError, match="not suspended"):
            controller.resume()


# ---------------------------------------------------------------------------
# Context manager tests
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager_normal(self, controller: EpisodeController) -> None:
        with controller:
            assert controller.episode is not None
            assert controller.episode.status == EpisodeStatus.RUNNING
        assert controller.episode.status == EpisodeStatus.COMPLETED

    def test_context_manager_on_exception(self, controller: EpisodeController) -> None:
        with pytest.raises(ValueError, match="boom"), controller:
            raise ValueError("boom")
        assert controller.episode is not None
        assert controller.episode.status == EpisodeStatus.FAILED


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_start_with_metadata(self, registry: ProjectRegistry, shadow: ShadowAuditGit, project_id: str) -> None:
        ctrl = EpisodeController(
            project_id=project_id,
            agent_id="agent-meta",
            registry=registry,
            shadow=shadow,
            metadata={"task_id": "WP-1001"},
        )
        ctrl.start()
        assert ctrl.episode is not None
        assert ctrl.episode.metadata["task_id"] == "WP-1001"


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_episode_persists_in_registry(
        self, controller: EpisodeController, registry: ProjectRegistry, project_id: str
    ) -> None:
        controller.start()
        controller.end()
        episodes = registry.get_episodes_for_project(project_id)
        assert len(episodes) == 1
        assert episodes[0].status == EpisodeStatus.COMPLETED
