"""Tests for WL-316: Sandbox Seeding Utility.

@trace WL-316
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import orjson as json
import pytest

from thegent.integrations.sandbox_seeder import SandboxSeeder, SeedRecord


@pytest.mark.requirement("WL-316")
def test_seed_record_dataclass() -> None:
    """Test SeedRecord dataclass creation."""
    seed = SeedRecord(
        wl_id="SEED-001",
        title="Test seed",
        status="TODO",
        priority="P1",
        connector="github",
    )
    assert seed.wl_id == "SEED-001"
    assert seed.title == "Test seed"
    assert seed.status == "TODO"
    assert seed.priority == "P1"
    assert seed.connector == "github"


@pytest.mark.requirement("WL-316")
def test_default_seeds_constant() -> None:
    """Test DEFAULT_SEEDS has 3 sample records."""
    assert len(SandboxSeeder.DEFAULT_SEEDS) == 3
    assert all(isinstance(seed, dict) for seed in SandboxSeeder.DEFAULT_SEEDS)
    assert all("wl_id" in seed for seed in SandboxSeeder.DEFAULT_SEEDS)
    assert all("title" in seed for seed in SandboxSeeder.DEFAULT_SEEDS)
    assert all("status" in seed for seed in SandboxSeeder.DEFAULT_SEEDS)
    assert all("priority" in seed for seed in SandboxSeeder.DEFAULT_SEEDS)
    assert all("connector" in seed for seed in SandboxSeeder.DEFAULT_SEEDS)


@pytest.mark.requirement("WL-316")
def test_generate_seeds_single() -> None:
    """Test generating a single seed."""
    seeds = SandboxSeeder.generate_seeds(1, "github")
    assert len(seeds) == 1
    assert seeds[0].wl_id == "SEED-001"
    assert seeds[0].connector == "github"
    assert seeds[0].title == "Seeded sync task 1"


@pytest.mark.requirement("WL-316")
def test_generate_seeds_multiple() -> None:
    """Test generating multiple seeds."""
    seeds = SandboxSeeder.generate_seeds(5, "jira")
    assert len(seeds) == 5
    assert seeds[0].wl_id == "SEED-001"
    assert seeds[4].wl_id == "SEED-005"
    assert all(seed.connector == "jira" for seed in seeds)


@pytest.mark.requirement("WL-316")
def test_generate_seeds_status_pool() -> None:
    """Test status pool cycling."""
    status_pool = ["TODO", "DONE"]
    seeds = SandboxSeeder.generate_seeds(4, "github", status_pool=status_pool)
    assert seeds[0].status == "TODO"
    assert seeds[1].status == "DONE"
    assert seeds[2].status == "TODO"
    assert seeds[3].status == "DONE"


@pytest.mark.requirement("WL-316")
def test_generate_seeds_default_status_pool() -> None:
    """Test default status pool."""
    seeds = SandboxSeeder.generate_seeds(6, "slack")
    assert seeds[0].status == "TODO"
    assert seeds[1].status == "IN_PROGRESS"
    assert seeds[2].status == "DONE"
    assert seeds[3].status == "TODO"
    assert seeds[4].status == "IN_PROGRESS"
    assert seeds[5].status == "DONE"


@pytest.mark.requirement("WL-316")
def test_generate_seeds_priorities() -> None:
    """Test priority assignment."""
    seeds = SandboxSeeder.generate_seeds(3, "github")
    assert seeds[0].priority == "P1"
    assert seeds[1].priority == "P2"
    assert seeds[2].priority == "P3"


@pytest.mark.requirement("WL-316")
def test_write_seeds_success() -> None:
    """Test writing seeds to file."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        output_file = tmppath / "seeds.json"

        seeds = SandboxSeeder.generate_seeds(2, "github")
        SandboxSeeder.write_seeds(seeds, output_file)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["wl_id"] == "SEED-001"


@pytest.mark.requirement("WL-316")
def test_write_seeds_invalid_path() -> None:
    """Test write_seeds fails if parent dir doesn't exist."""
    nonexistent_dir = Path("/nonexistent/seeds.json")
    seeds = [SeedRecord("SEED-001", "test", "TODO", "P1", "github")]

    with pytest.raises(ValueError, match="Parent directory does not exist"):
        SandboxSeeder.write_seeds(seeds, nonexistent_dir)


@pytest.mark.requirement("WL-316")
def test_load_seeds_success() -> None:
    """Test loading seeds from file."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        output_file = tmppath / "seeds.json"

        original_seeds = SandboxSeeder.generate_seeds(2, "github")
        SandboxSeeder.write_seeds(original_seeds, output_file)

        loaded_seeds = SandboxSeeder.load_seeds(output_file)
        assert len(loaded_seeds) == 2
        assert loaded_seeds[0].wl_id == "SEED-001"
        assert loaded_seeds[0].connector == "github"


@pytest.mark.requirement("WL-316")
def test_load_seeds_not_found() -> None:
    """Test load_seeds fails if file doesn't exist."""
    nonexistent_file = Path("/nonexistent/seeds.json")

    with pytest.raises(FileNotFoundError, match="Seed file not found"):
        SandboxSeeder.load_seeds(nonexistent_file)


@pytest.mark.requirement("WL-316")
def test_roundtrip_seeds() -> None:
    """Test write then load preserves data."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        output_file = tmppath / "seeds.json"

        original_seeds = SandboxSeeder.generate_seeds(3, "jira")
        SandboxSeeder.write_seeds(original_seeds, output_file)
        loaded_seeds = SandboxSeeder.load_seeds(output_file)

        assert len(loaded_seeds) == len(original_seeds)
        for original, loaded in zip(original_seeds, loaded_seeds, strict=False):
            assert original.wl_id == loaded.wl_id
            assert original.title == loaded.title
            assert original.status == loaded.status
            assert original.priority == loaded.priority
            assert original.connector == loaded.connector
