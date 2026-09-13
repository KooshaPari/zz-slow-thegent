"""Database helpers for thegent.

Common database utilities.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_BUSY_TIMEOUT_MS = 5000


def apply_connection_pragmas(
    conn: sqlite3.Connection,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> None:
    """Apply pragmas that make SQLite safe under concurrent writers.

    Enables WAL journal mode (concurrent readers don't block on a writer
    and vice versa), sets a busy_timeout so contended writes retry
    transparently for up to ``busy_timeout_ms`` ms, and downgrades
    synchronous from FULL to NORMAL — a safe tradeoff on WAL that gives
    most of the durability guarantees at a fraction of the fsync cost.
    Idempotent; safe to run on every connection.
    """
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    conn.execute("PRAGMA synchronous = NORMAL")


class Database:
    """Simple SQLite wrapper."""

    def __init__(self, path: str = ":memory:", busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS):
        self.path = path
        self.busy_timeout_ms = busy_timeout_ms
        self.conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.path, timeout=max(1.0, self.busy_timeout_ms / 1000.0))
        apply_connection_pragmas(self.conn, busy_timeout_ms=self.busy_timeout_ms)

    def execute(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()  # type: ignore
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        self.conn.commit()
        return []

    def close(self) -> None:
        if self.conn:
            self.conn.close()


def init_db(path: str) -> Database:
    """Initialize database."""
    db = Database(path)
    db.connect()
    return db
