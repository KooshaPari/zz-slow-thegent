# @trace WL-281 B90-W2-B1
"""Tests for team ownership registry (WL-281).

Validates ownership assignments, escalation contacts, team lookups,
and JSON persistence.
"""

from __future__ import annotations

from datetime import datetime

import orjson as json
import pytest

from thegent.integrations.team_ownership import (
    OwnershipRegistry,
    TeamOwnership,
)


@pytest.mark.requirement("WL-281")
def test_team_ownership_dataclass_creation():
    """Test TeamOwnership dataclass creation with all fields."""
    assigned_at = "2026-02-22T10:00:00"
    ownership = TeamOwnership(
        wl_id="WL-281",
        team="platform",
        owner="alice@example.com",
        backup_owner="bob@example.com",
        assigned_at=assigned_at,
    )
    assert ownership.wl_id == "WL-281"
    assert ownership.team == "platform"
    assert ownership.owner == "alice@example.com"
    assert ownership.backup_owner == "bob@example.com"
    assert ownership.assigned_at == assigned_at


@pytest.mark.requirement("WL-281")
def test_team_ownership_default_timestamp():
    """Test TeamOwnership assigns default timestamp if not provided."""
    ownership = TeamOwnership(
        wl_id="WL-282",
        team="infra",
        owner="charlie@example.com",
        backup_owner="diana@example.com",
    )
    assert ownership.assigned_at is not None
    # Should be a valid ISO format string
    datetime.fromisoformat(ownership.assigned_at)


@pytest.mark.requirement("WL-281")
def test_registry_register_single_ownership(tmp_path):
    """Test registering a single ownership record."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    ownership = TeamOwnership(
        wl_id="WL-300",
        team="platform",
        owner="owner1@example.com",
        backup_owner="backup1@example.com",
    )
    registry.register(ownership)

    # Verify file was created and contains the record
    assert registry_path.exists()
    with open(registry_path) as f:
        data = json.load(f)
    assert "WL-300" in data
    assert data["WL-300"]["owner"] == "owner1@example.com"


@pytest.mark.requirement("WL-281")
def test_registry_get_owner_exists(tmp_path):
    """Test retrieving an existing ownership record."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    ownership = TeamOwnership(
        wl_id="WL-310",
        team="infra",
        owner="owner2@example.com",
        backup_owner="backup2@example.com",
    )
    registry.register(ownership)

    # Retrieve and verify
    result = registry.get_owner("WL-310")
    assert result is not None
    assert result.owner == "owner2@example.com"
    assert result.backup_owner == "backup2@example.com"


@pytest.mark.requirement("WL-281")
def test_registry_get_owner_not_exists(tmp_path):
    """Test retrieving a non-existent ownership record."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    result = registry.get_owner("WL-999")
    assert result is None


@pytest.mark.requirement("WL-281")
def test_registry_list_by_team(tmp_path):
    """Test listing all ownership records for a team."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    # Register multiple items for different teams
    registry.register(
        TeamOwnership(
            wl_id="WL-320",
            team="platform",
            owner="owner3@example.com",
            backup_owner="backup3@example.com",
        )
    )
    registry.register(
        TeamOwnership(
            wl_id="WL-321",
            team="platform",
            owner="owner4@example.com",
            backup_owner="backup4@example.com",
        )
    )
    registry.register(
        TeamOwnership(
            wl_id="WL-322",
            team="infra",
            owner="owner5@example.com",
            backup_owner="backup5@example.com",
        )
    )

    # List by team
    platform_items = registry.list_by_team("platform")
    assert len(platform_items) == 2
    assert all(o.team == "platform" for o in platform_items)
    assert {o.wl_id for o in platform_items} == {"WL-320", "WL-321"}

    infra_items = registry.list_by_team("infra")
    assert len(infra_items) == 1
    assert infra_items[0].wl_id == "WL-322"


@pytest.mark.requirement("WL-281")
def test_registry_update_existing_ownership(tmp_path):
    """Test updating an existing ownership record."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    # Register initial ownership
    registry.register(
        TeamOwnership(
            wl_id="WL-330",
            team="platform",
            owner="owner6@example.com",
            backup_owner="backup6@example.com",
        )
    )

    # Update with new owner
    registry.register(
        TeamOwnership(
            wl_id="WL-330",
            team="platform",
            owner="newowner@example.com",
            backup_owner="backup6@example.com",
        )
    )

    # Verify update
    result = registry.get_owner("WL-330")
    assert result.owner == "newowner@example.com"


@pytest.mark.requirement("WL-281")
def test_registry_persistence_across_instances(tmp_path):
    """Test that data persists correctly across registry instances."""
    registry_path = tmp_path / "team_ownership.json"

    # Create first instance and register
    registry1 = OwnershipRegistry(registry_path)
    registry1.register(
        TeamOwnership(
            wl_id="WL-340",
            team="platform",
            owner="owner7@example.com",
            backup_owner="backup7@example.com",
        )
    )

    # Create second instance and verify it can read the data
    registry2 = OwnershipRegistry(registry_path)
    result = registry2.get_owner("WL-340")

    assert result is not None
    assert result.owner == "owner7@example.com"
    assert result.team == "platform"


@pytest.mark.requirement("WL-281")
def test_registry_json_format_valid(tmp_path):
    """Test that the JSON file format is valid and correct."""
    registry_path = tmp_path / "team_ownership.json"
    registry = OwnershipRegistry(registry_path)

    # Register multiple items
    registry.register(
        TeamOwnership(
            wl_id="WL-350",
            team="platform",
            owner="owner8@example.com",
            backup_owner="backup8@example.com",
            assigned_at="2026-02-22T10:00:00",
        )
    )
    registry.register(
        TeamOwnership(
            wl_id="WL-351",
            team="infra",
            owner="owner9@example.com",
            backup_owner="backup9@example.com",
            assigned_at="2026-02-22T11:00:00",
        )
    )

    # Verify JSON structure
    with open(registry_path) as f:
        data = json.load(f)

    # Should be a dict with wl_id keys
    assert isinstance(data, dict)
    assert "WL-350" in data
    assert "WL-351" in data

    # Each entry should have the required fields
    for entry in data.values():
        assert "wl_id" in entry
        assert "team" in entry
        assert "owner" in entry
        assert "backup_owner" in entry
        assert "assigned_at" in entry
