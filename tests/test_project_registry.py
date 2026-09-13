"""Tests for ProjectRegistry (wp-71001).

# @trace FR-VCS-001
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from thegent.infra.project_registry import (
    Episode,
    Milestone,
    Product,
    ProjectRegistry,
    Sprint,
    Task,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def registry(tmp_path: Path) -> ProjectRegistry:
    """Create a ProjectRegistry backed by a temp SQLite DB."""
    db_path = tmp_path / "registry.db"
    return ProjectRegistry(db_path=db_path)


@pytest.mark.requirement("FR-VCS-001")
class TestProductModel:
    def test_product_fields(self) -> None:
        p = Product(id="p1", name="Test Product")
        assert p.id == "p1"
        assert p.name == "Test Product"

    def test_product_requires_name(self) -> None:
        with pytest.raises(Exception):
            Product(id="p1", name="")


@pytest.mark.requirement("FR-VCS-001")
class TestMilestoneModel:
    def test_milestone_fields(self) -> None:
        m = Milestone(id="m1", product_id="p1", name="v1.0")
        assert m.product_id == "p1"
        assert m.name == "v1.0"


@pytest.mark.requirement("FR-VCS-001")
class TestSprintModel:
    def test_sprint_fields(self) -> None:
        s = Sprint(id="s1", milestone_id="m1", name="Sprint 1")
        assert s.milestone_id == "m1"


@pytest.mark.requirement("FR-VCS-001")
class TestTaskModel:
    def test_task_fields(self) -> None:
        t = Task(id="t1", sprint_id="s1", name="Implement feature")
        assert t.sprint_id == "s1"


@pytest.mark.requirement("FR-VCS-001")
class TestEpisodeModel:
    def test_episode_fields(self) -> None:
        e = Episode(id="e1", task_id="t1", status="active")
        assert e.task_id == "t1"
        assert e.status == "active"


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryCreateProduct:
    def test_create_product(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="MyProduct")
        assert product.name == "MyProduct"
        assert product.id  # non-empty

    def test_create_product_returns_unique_ids(self, registry: ProjectRegistry) -> None:
        p1 = registry.create_product(name="A")
        p2 = registry.create_product(name="B")
        assert p1.id != p2.id


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryCreateMilestone:
    def test_create_milestone(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        assert milestone.product_id == product.id
        assert milestone.name == "v1.0"

    def test_create_milestone_invalid_product(self, registry: ProjectRegistry) -> None:
        with pytest.raises(ValueError, match=r"Product .* not found"):
            registry.create_milestone(product_id="nonexistent", name="v1.0")


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryCreateSprint:
    def test_create_sprint(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        sprint = registry.create_sprint(milestone_id=milestone.id, name="Sprint 1")
        assert sprint.milestone_id == milestone.id

    def test_create_sprint_invalid_milestone(self, registry: ProjectRegistry) -> None:
        with pytest.raises(ValueError, match=r"Milestone .* not found"):
            registry.create_sprint(milestone_id="nonexistent", name="Sprint 1")


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryCreateTask:
    def test_create_task(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        sprint = registry.create_sprint(milestone_id=milestone.id, name="S1")
        task = registry.create_task(sprint_id=sprint.id, name="Task 1")
        assert task.sprint_id == sprint.id

    def test_create_task_invalid_sprint(self, registry: ProjectRegistry) -> None:
        with pytest.raises(ValueError, match=r"Sprint .* not found"):
            registry.create_task(sprint_id="nonexistent", name="Task 1")


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryCreateEpisode:
    def test_create_episode(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        sprint = registry.create_sprint(milestone_id=milestone.id, name="S1")
        task = registry.create_task(sprint_id=sprint.id, name="T1")
        episode = registry.create_episode(task_id=task.id)
        assert episode.task_id == task.id
        assert episode.status == "active"

    def test_create_episode_invalid_task(self, registry: ProjectRegistry) -> None:
        with pytest.raises(ValueError, match=r"Task .* not found"):
            registry.create_episode(task_id="nonexistent")


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryGetActiveEpisode:
    def test_get_active_episode(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        sprint = registry.create_sprint(milestone_id=milestone.id, name="S1")
        task = registry.create_task(sprint_id=sprint.id, name="T1")
        episode = registry.create_episode(task_id=task.id)
        active = registry.get_active_episode()
        assert active is not None
        assert active.id == episode.id

    def test_get_active_episode_none(self, registry: ProjectRegistry) -> None:
        assert registry.get_active_episode() is None


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryListEpisodes:
    def test_list_episodes(self, registry: ProjectRegistry) -> None:
        product = registry.create_product(name="P")
        milestone = registry.create_milestone(product_id=product.id, name="v1.0")
        sprint = registry.create_sprint(milestone_id=milestone.id, name="S1")
        task = registry.create_task(sprint_id=sprint.id, name="T1")
        registry.create_episode(task_id=task.id)
        registry.create_episode(task_id=task.id)
        episodes = registry.list_episodes(task_id=task.id)
        assert len(episodes) == 2

    def test_list_episodes_empty(self, registry: ProjectRegistry) -> None:
        episodes = registry.list_episodes(task_id="nonexistent")
        assert episodes == []


@pytest.mark.requirement("FR-VCS-001")
class TestProjectRegistryPersistence:
    def test_data_persists_across_instances(self, tmp_path: Path) -> None:
        db_path = tmp_path / "registry.db"
        reg1 = ProjectRegistry(db_path=db_path)
        product = reg1.create_product(name="Persistent")
        del reg1

        reg2 = ProjectRegistry(db_path=db_path)
        # Verify we can create a milestone referencing the persisted product
        milestone = reg2.create_milestone(product_id=product.id, name="v1.0")
        assert milestone.product_id == product.id
