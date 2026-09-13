"""Tests for SerializableMixin."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import pytest

from thegent.integrations.base import SerializableMixin


class Status(StrEnum):
    """Test status enum."""

    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"


class Priority(StrEnum):
    """Test priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Address(SerializableMixin):
    """Nested model for testing."""

    street: str
    city: str
    zip_code: str


@dataclass
class Person(SerializableMixin):
    """Test model with various field types."""

    name: str
    age: int
    status: Status
    created_at: datetime
    home_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    address: Address | None = None


class TestToDict:
    """Tests for to_dict serialization."""

    def test_basic_fields(self):
        """Test basic field serialization."""
        person = Person(
            name="Alice",
            age=30,
            status=Status.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            home_path=Path("/home/alice"),
        )
        result = person.to_dict()

        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["status"] == "active"  # Enum serialized as value
        assert result["created_at"] == "2024-01-15T10:30:00"  # ISO format
        assert result["home_path"] == "/home/alice"  # Path as string

    def test_enum_serialization(self):
        """Test enum serialization."""
        person = Person(
            name="Bob",
            age=25,
            status=Status.DONE,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            home_path=Path("/tmp"),
        )
        result = person.to_dict()

        assert result["status"] == "done"
        assert isinstance(result["status"], str)

    def test_datetime_with_timezone(self):
        """Test datetime with timezone serialization."""
        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        person = Person(
            name="Charlie",
            age=35,
            status=Status.PENDING,
            created_at=dt,
            home_path=Path("/tmp"),
        )
        result = person.to_dict()

        assert "2024-06-15T14:30:00" in result["created_at"]

    def test_nested_dict(self):
        """Test nested dict serialization."""
        person = Person(
            name="Diana",
            age=28,
            status=Status.ACTIVE,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            home_path=Path("/tmp"),
            metadata={"key": "value", "nested": {"inner": 123}},
        )
        result = person.to_dict()

        assert result["metadata"]["key"] == "value"
        assert result["metadata"]["nested"]["inner"] == 123

    def test_list_serialization(self):
        """Test list serialization."""
        person = Person(
            name="Eve",
            age=22,
            status=Status.PENDING,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            home_path=Path("/tmp"),
            tags=["tag1", "tag2", "tag3"],
        )
        result = person.to_dict()

        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_nested_serializable(self):
        """Test nested SerializableMixin serialization."""
        address = Address(street="123 Main St", city="Springfield", zip_code="12345")
        person = Person(
            name="Frank",
            age=40,
            status=Status.ACTIVE,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            home_path=Path("/tmp"),
            address=address,
        )
        result = person.to_dict()

        assert result["address"]["street"] == "123 Main St"
        assert result["address"]["city"] == "Springfield"
        assert result["address"]["zip_code"] == "12345"

    def test_none_field(self):
        """Test None field serialization."""
        person = Person(
            name="Grace",
            age=50,
            status=Status.DONE,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            home_path=Path("/tmp"),
            address=None,
        )
        result = person.to_dict()

        assert result["address"] is None


class TestFromDict:
    """Tests for from_dict deserialization."""

    def test_basic_deserialization(self):
        """Test basic field deserialization."""
        data = {
            "name": "Alice",
            "age": 30,
            "status": "active",
            "created_at": "2024-01-15T10:30:00",
            "home_path": "/home/alice",
        }
        person = Person.from_dict(data)

        assert person.name == "Alice"
        assert person.age == 30
        # Note: Enum/datetime/Path don't auto-convert in from_dict
        # They remain as strings - subclasses can override for custom deserialization

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        data = {
            "name": "Bob",
            "age": 25,
            "status": "done",
            "created_at": "2024-01-01",
            "home_path": "/tmp",
            "extra_field": "should be ignored",
        }
        person = Person.from_dict(data)

        assert person.name == "Bob"
        assert not hasattr(person, "extra_field")

    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        data = {
            "name": "Charlie",
            "age": 35,
            "status": "pending",
            "created_at": "2024-01-01",
            "home_path": "/tmp",
        }
        person = Person.from_dict(data)

        assert person.metadata == {}
        assert person.tags == []
        assert person.address is None


class TestRoundTrip:
    """Tests for serialization -> deserialization round trips."""

    def test_simple_roundtrip(self):
        """Test that simple data survives round trip."""
        original = Person(
            name="Alice",
            age=30,
            status=Status.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            home_path=Path("/home/alice"),
            metadata={"key": "value"},
            tags=["tag1"],
        )

        serialized = original.to_dict()
        restored = Person.from_dict(serialized)

        assert restored.name == original.name
        assert restored.age == original.age
        # status is now string "active" not enum
        # created_at is now string not datetime
        # home_path is now string not Path


class TestNonDataclass:
    """Tests for non-dataclass classes."""

    def test_non_dataclass_serialization(self):
        """Test that non-dataclass objects can use SerializableMixin."""

        class SimpleModel(SerializableMixin):
            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value

        obj = SimpleModel("test", 42)
        result = obj.to_dict()

        assert result["name"] == "test"
        assert result["value"] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
