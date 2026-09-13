"""Canonical workstream entity operations."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from thegent.db_helpers import apply_connection_pragmas

logger = logging.getLogger(__name__)


class ThegentSettings:
    """Settings for thegent application."""

    def __init__(self) -> None:
        """Initialize settings with default values."""
        self.session_dir: Path = Path.cwd()
        self.environment: str = "development"
        self.trust_score_threshold: float = 0.8
        self.default_timeout: int = 90
        self.default_timeout_claude: int = 300


class WorkstreamDB:
    """Database for workstream entities."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize workstream database.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workstream_items (
                item_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                title TEXT,
                source TEXT,
                priority TEXT,
                status TEXT,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workstream_sessions (
                session_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path), timeout=5.0)
            self._conn.row_factory = sqlite3.Row
            apply_connection_pragmas(self._conn)
        return self._conn

    def upsert_item(
        self,
        item_id: str,
        entity_type: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Insert or update a workstream item.

        Args:
            item_id: Unique item identifier.
            entity_type: Type of entity (e.g., 'workstream_items').
            properties: Item properties.

        Returns:
            Created/updated item record.
        """
        conn = self._get_conn()
        metadata = properties.get("metadata", {})

        conn.execute(
            """
            INSERT INTO workstream_items
            (item_id, entity_type, title, source, priority, status, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(item_id) DO UPDATE SET
                title = excluded.title,
                source = excluded.source,
                priority = excluded.priority,
                status = excluded.status,
                metadata_json = excluded.metadata_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                item_id,
                entity_type,
                properties.get("title"),
                properties.get("source"),
                properties.get("priority"),
                properties.get("status"),
                json.dumps(metadata),
            ),
        )
        conn.commit()

        return self._get_item(item_id)

    def _get_item(self, item_id: str) -> dict[str, Any]:
        """Get item by ID.

        Args:
            item_id: Item identifier.

        Returns:
            Item record or empty dict if not found.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM workstream_items WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {}

        return self._row_to_item(row)

    def _row_to_item(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert database row to item dictionary.

        Args:
            row: Database row.

        Returns:
            Item dictionary.
        """
        item = dict(row)
        if item.get("metadata_json"):
            item["metadata"] = json.loads(item["metadata_json"])
        del item["metadata_json"]
        return item

    def list_items(
        self,
        entity_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List workstream items.

        Args:
            entity_type: Type of entities to list.
            limit: Maximum number of items to return.
            offset: Offset for pagination.

        Returns:
            Tuple of (items list, total count).
        """
        conn = self._get_conn()

        count_cursor = conn.execute(
            "SELECT COUNT(*) FROM workstream_items WHERE entity_type = ?",
            (entity_type,),
        )
        total = count_cursor.fetchone()[0]

        cursor = conn.execute(
            """
            SELECT * FROM workstream_items
            WHERE entity_type = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (entity_type, limit, offset),
        )

        items = [self._row_to_item(row) for row in cursor.fetchall()]
        return items, total

    def search_items(
        self,
        entity_type: str,
        query: str,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search workstream items.

        Args:
            entity_type: Type of entities to search.
            query: Search query string.
            limit: Maximum number of items to return.

        Returns:
            Tuple of (items list, total count).
        """
        conn = self._get_conn()
        search_pattern = f"%{query}%"

        count_cursor = conn.execute(
            """
            SELECT COUNT(*) FROM workstream_items
            WHERE entity_type = ? AND (title LIKE ? OR metadata_json LIKE ?)
            """,
            (entity_type, search_pattern, search_pattern),
        )
        total = count_cursor.fetchone()[0]

        cursor = conn.execute(
            """
            SELECT * FROM workstream_items
            WHERE entity_type = ? AND (title LIKE ? OR metadata_json LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (entity_type, search_pattern, search_pattern, limit),
        )

        items = [self._row_to_item(row) for row in cursor.fetchall()]
        return items, total

    def delete_item(self, item_id: str) -> bool:
        """Delete a workstream item.

        Args:
            item_id: Item identifier.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM workstream_items WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def bulk_import(
        self,
        entity_type: str,
        records: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int]:
        """Bulk import records.

        Args:
            entity_type: Type of entities to import.
            records: List of records to import.

        Returns:
            Tuple of (imported items, count).
        """
        imported = []
        for record in records:
            item_id = record.get("entity_id") or record.get("item_id")
            if item_id:
                item = self.upsert_item(item_id, entity_type, record)
                imported.append(item)

        return imported, len(imported)

    def sync_workstream(self, data: dict[str, Any]) -> None:
        """Sync workstream from data.

        Args:
            data: Workstream data dictionary.
        """

    def sync_from_agileplus(self, session_dir: Path) -> int:
        """Sync from AgilePlus data.

        Args:
            session_dir: Session directory.

        Returns:
            Number of items synced.
        """
        return 0

    def sync_from_queues(self, session_dir: Path) -> int:
        """Sync from queue data.

        Args:
            session_dir: Session directory.

        Returns:
            Number of items synced.
        """
        return 0

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


def entity_operation(
    operation: str,
    entity_type: str,
    entity_id: str | None = None,
    properties: dict[str, Any] | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
    source: str | None = None,
    cd: Path | None = None,
    db_path: Path | None = None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Perform an operation on a workstream entity.

    Args:
        operation: Operation to perform (upsert, list, search, delete, import, sync).
        entity_type: Type of entity.
        entity_id: Entity ID for single-item operations.
        properties: Properties for upsert operations.
        query: Search query.
        limit: Maximum items for list operations.
        offset: Offset for pagination.
        source: Source for sync operations.
        cd: Current directory for sync operations.
        db_path: Path to database file.
        records: Records for bulk import.

    Returns:
        Operation result dictionary.
    """
    if db_path is None:
        settings = ThegentSettings()
        if cd is not None:
            settings.session_dir = cd
        db_path = settings.session_dir / "workstream.db"

    db = WorkstreamDB(db_path)

    try:
        if operation == "upsert":
            if entity_id is None or properties is None:
                return {"error": "entity_id and properties required for upsert"}

            item = db.upsert_item(entity_id, entity_type, properties)
            return {
                "entity_type": entity_type,
                "item": item,
                "operation": "upsert",
            }

        elif operation == "list":
            items, total = db.list_items(entity_type, limit=limit, offset=offset)
            return {
                "entity_type": entity_type,
                "items": items,
                "count": total,
                "operation": "list",
            }

        elif operation == "search":
            if query is None:
                return {"error": "query required for search"}

            items, total = db.search_items(entity_type, query, limit=limit)
            return {
                "entity_type": entity_type,
                "items": items,
                "count": total,
                "operation": "search",
            }

        elif operation == "delete":
            if entity_id is None:
                return {"error": "entity_id required for delete"}

            deleted = db.delete_item(entity_id)
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "deleted": deleted,
                "operation": "delete",
            }

        elif operation == "import":
            if records is None:
                return {"error": "records required for import"}

            items, count = db.bulk_import(entity_type, records)
            return {
                "entity_type": entity_type,
                "items": items,
                "count": count,
                "operation": "import",
            }

        elif operation == "sync":
            settings = ThegentSettings()
            if cd is not None:
                settings.session_dir = cd

            total = 0
            if source is None or source == "all":
                db.sync_workstream({})
                total += db.sync_from_agileplus(settings.session_dir)
                total += db.sync_from_queues(settings.session_dir)
            elif source == "markdown":
                db.sync_workstream({})
            elif source == "agileplus":
                total = db.sync_from_agileplus(settings.session_dir)
            elif source == "queues":
                total = db.sync_from_queues(settings.session_dir)

            return {
                "entity_type": entity_type,
                "total": total,
                "operation": "sync",
            }

        else:
            return {"error": f"Unknown operation: {operation}"}

    finally:
        db.close()


__all__ = [
    "entity_operation",
    "ThegentSettings",
    "WorkstreamDB",
]
