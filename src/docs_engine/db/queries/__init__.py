"""Doc queries module."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class DocQueries:
    """SQLite-based document queries."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_by_type(self, doc_type: str) -> list[dict[str, Any]]:
        """Get documents by type."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM docs WHERE type = ?",
                (doc_type,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get documents by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM docs WHERE status = ?",
                (status,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search documents by title."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM docs WHERE title LIKE ?",
                (f"%{query}%",),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all(self) -> list[dict[str, Any]]:
        """Get all documents."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM docs")
            rows = cursor.fetchall()
        return [dict(row) for row in rows]


__all__ = ["DocQueries"]
