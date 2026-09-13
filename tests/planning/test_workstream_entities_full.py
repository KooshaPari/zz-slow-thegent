"""Comprehensive tests for thegent.planning.workstream_entities module."""

from __future__ import annotations

from pathlib import Path


class TestWorkstreamDBInit:
    """Tests for WorkstreamDB initialization."""

    def test_init_creates_tables(self, tmp_path: Path) -> None:
        """Initialization creates database tables."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db_path = tmp_path / "test.db"
        db = WorkstreamDB(db_path)
        assert db_path.exists()
        conn = db._get_conn()
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workstream_items'")
        assert cursor.fetchone() is not None


class TestWorkstreamDBOperations:
    """Tests for WorkstreamDB CRUD operations."""

    def test_upsert_creates_item(self, tmp_path: Path) -> None:
        """Upsert creates a new item."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        item = db.upsert_item("WL-001", "workstream_items", {"title": "Test Task"})
        assert item["item_id"] == "WL-001"
        assert item["title"] == "Test Task"

    def test_upsert_updates_existing(self, tmp_path: Path) -> None:
        """Upsert updates an existing item."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.upsert_item("WL-001", "workstream_items", {"title": "Original"})
        item = db.upsert_item("WL-001", "workstream_items", {"title": "Updated"})
        assert item["title"] == "Updated"

    def test_get_item_exists(self, tmp_path: Path) -> None:
        """Get item returns item when it exists."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.upsert_item("WL-001", "workstream_items", {"title": "Test"})
        item = db._get_item("WL-001")
        assert item["item_id"] == "WL-001"

    def test_get_item_not_exists(self, tmp_path: Path) -> None:
        """Get item returns empty dict when not found."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        item = db._get_item("NONEXISTENT")
        assert item == {}

    def test_list_items(self, tmp_path: Path) -> None:
        """List items returns all items of type."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.upsert_item("WL-001", "workstream_items", {"title": "Task1"})
        db.upsert_item("WL-002", "workstream_items", {"title": "Task2"})
        items, total = db.list_items("workstream_items")
        assert total == 2
        assert len(items) == 2

    def test_list_items_with_limit(self, tmp_path: Path) -> None:
        """List items respects limit."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        for i in range(5):
            db.upsert_item(f"WL-{i:03d}", "workstream_items", {"title": f"Task{i}"})
        items, total = db.list_items("workstream_items", limit=3)
        assert len(items) == 3
        assert total == 5

    def test_list_items_with_offset(self, tmp_path: Path) -> None:
        """List items respects offset."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        for i in range(5):
            db.upsert_item(f"WL-{i:03d}", "workstream_items", {"title": f"Task{i}"})
        items, _ = db.list_items("workstream_items", limit=3, offset=2)
        assert len(items) == 3

    def test_search_items(self, tmp_path: Path) -> None:
        """Search finds items by title."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.upsert_item("WL-001", "workstream_items", {"title": "Findable Task"})
        db.upsert_item("WL-002", "workstream_items", {"title": "Other Task"})
        items, total = db.search_items("workstream_items", "Findable")
        assert total == 1
        assert items[0]["item_id"] == "WL-001"

    def test_delete_item_exists(self, tmp_path: Path) -> None:
        """Delete returns True when item existed."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.upsert_item("WL-001", "workstream_items", {"title": "To Delete"})
        result = db.delete_item("WL-001")
        assert result is True

    def test_delete_item_not_exists(self, tmp_path: Path) -> None:
        """Delete returns False when item didn't exist."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        result = db.delete_item("NONEXISTENT")
        assert result is False

    def test_bulk_import(self, tmp_path: Path) -> None:
        """Bulk import creates multiple items."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        records = [
            {"entity_id": "WL-001", "title": "Task1"},
            {"entity_id": "WL-002", "title": "Task2"},
        ]
        items, count = db.bulk_import("workstream_items", records)
        assert count == 2
        assert len(items) == 2


class TestWorkstreamDBSync:
    """Tests for WorkstreamDB sync operations."""

    def test_sync_workstream(self, tmp_path: Path) -> None:
        """sync_workstream doesn't raise."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.sync_workstream({})

    def test_sync_from_agileplus(self, tmp_path: Path) -> None:
        """sync_from_agileplus returns 0."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        result = db.sync_from_agileplus(tmp_path)
        assert result == 0

    def test_sync_from_queues(self, tmp_path: Path) -> None:
        """sync_from_queues returns 0."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        result = db.sync_from_queues(tmp_path)
        assert result == 0


class TestWorkstreamDBClose:
    """Tests for WorkstreamDB.close method."""

    def test_close_without_conn(self, tmp_path: Path) -> None:
        """Close doesn't raise when conn is None."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db.close()

    def test_close_with_conn(self, tmp_path: Path) -> None:
        """Close closes the connection."""
        from thegent.planning.workstream_entities import WorkstreamDB

        db = WorkstreamDB(tmp_path / "test.db")
        db._get_conn()
        db.close()
        assert db._conn is None


class TestEntityOperation:
    """Tests for entity_operation function."""

    def test_upsert_operation(self, tmp_path: Path) -> None:
        """Upsert operation creates item."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation(
            "upsert",
            "workstream_items",
            entity_id="WL-001",
            properties={"title": "Test Task"},
            db_path=db_path,
        )
        assert result["operation"] == "upsert"
        assert result["item"]["item_id"] == "WL-001"

    def test_upsert_missing_params(self, tmp_path: Path) -> None:
        """Upsert without required params returns error."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation(
            "upsert",
            "workstream_items",
            db_path=db_path,
        )
        assert "error" in result

    def test_list_operation(self, tmp_path: Path) -> None:
        """List operation returns items."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        entity_operation(
            "upsert",
            "workstream_items",
            entity_id="WL-001",
            properties={"title": "Task"},
            db_path=db_path,
        )
        result = entity_operation("list", "workstream_items", limit=10, db_path=db_path)
        assert result["operation"] == "list"
        assert result["count"] == 1

    def test_search_operation(self, tmp_path: Path) -> None:
        """Search operation finds items."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        entity_operation(
            "upsert",
            "workstream_items",
            entity_id="WL-001",
            properties={"title": "UniqueTitle"},
            db_path=db_path,
        )
        result = entity_operation("search", "workstream_items", query="Unique", db_path=db_path)
        assert result["count"] == 1

    def test_search_missing_query(self, tmp_path: Path) -> None:
        """Search without query returns error."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation("search", "workstream_items", db_path=db_path)
        assert "error" in result

    def test_delete_operation(self, tmp_path: Path) -> None:
        """Delete operation removes item."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        entity_operation(
            "upsert",
            "workstream_items",
            entity_id="WL-001",
            properties={"title": "Task"},
            db_path=db_path,
        )
        result = entity_operation("delete", "workstream_items", entity_id="WL-001", db_path=db_path)
        assert result["deleted"] is True

    def test_import_operation(self, tmp_path: Path) -> None:
        """Import operation bulk imports records."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation(
            "import",
            "workstream_items",
            records=[
                {"entity_id": "WL-001", "title": "Task1"},
                {"entity_id": "WL-002", "title": "Task2"},
            ],
            db_path=db_path,
        )
        assert result["count"] == 2

    def test_sync_operation(self, tmp_path: Path) -> None:
        """Sync operation completes without error."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation("sync", "sessions", source="all", cd=tmp_path, db_path=db_path)
        assert result["operation"] == "sync"
        assert "total" in result

    def test_unknown_operation(self, tmp_path: Path) -> None:
        """Unknown operation returns error."""
        from thegent.planning.workstream_entities import entity_operation

        db_path = tmp_path / "test.db"
        result = entity_operation("unknown_op", "items", db_path=db_path)
        assert "error" in result


class TestThegentSettings:
    """Tests for ThegentSettings class."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""
        from thegent.planning.workstream_entities import ThegentSettings

        settings = ThegentSettings()
        assert settings.session_dir == Path.cwd()
        assert settings.environment == "development"
        assert settings.trust_score_threshold == 0.8
