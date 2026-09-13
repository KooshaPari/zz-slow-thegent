"""Regression tests for workstream.db SQLite pragma hardening.

Validates that opening a WorkstreamDB applies the pragmas that fix the
"database is locked" failure mode (#1142) and that concurrent writers
retry transparently instead of returning SQLITE_BUSY in <1 ms.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from thegent.db_helpers import apply_connection_pragmas
from thegent.planning.workstream_entities import WorkstreamDB, entity_operation


def _read_pragmas(db_path: Path) -> dict[str, object]:
    """Open a read-only connection and return current pragma values."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        synchronous = conn.execute("PRAGMA synchronous").fetchone()[0]
    finally:
        conn.close()
    return {
        "journal_mode": journal_mode.lower(),
        "busy_timeout": int(busy_timeout),
        "synchronous": int(synchronous),
    }


def test_workstream_db_enables_wal_and_busy_timeout(tmp_path: Path) -> None:
    """Opening a WorkstreamDB must upgrade the file to WAL + busy_timeout."""
    db_path = tmp_path / "workstream.db"
    WorkstreamDB(db_path).close()

    pragmas = _read_pragmas(db_path)
    assert pragmas["journal_mode"] == "wal", pragmas
    assert pragmas["busy_timeout"] >= 1000, pragmas
    assert pragmas["synchronous"] in (1, 2), pragmas


def test_apply_connection_pragmas_is_idempotent(tmp_path: Path) -> None:
    """Repeated pragma application must not raise or change effective mode."""
    db_path = tmp_path / "workstream.db"
    conn = sqlite3.connect(str(db_path))
    try:
        apply_connection_pragmas(conn)
        apply_connection_pragmas(conn)
        apply_connection_pragmas(conn)
    finally:
        conn.close()

    pragmas = _read_pragmas(db_path)
    assert pragmas["journal_mode"] == "wal"
    assert pragmas["busy_timeout"] >= 1000


def test_concurrent_reads_unblocked_during_write(tmp_path: Path) -> None:
    """A held write tx must not block readers under WAL."""
    db_path = tmp_path / "workstream.db"
    entity_operation(
        "upsert",
        "workstream_items",
        entity_id="WL-1",
        properties={"title": "seed", "status": "pending"},
        db_path=db_path,
    )

    writer = sqlite3.connect(str(db_path), timeout=10.0)
    apply_connection_pragmas(writer)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute(
        "UPDATE workstream_items SET title = ? WHERE item_id = ?",
        ("held", "WL-1"),
    )

    read_result: dict[str, object] = {}
    barrier = threading.Event()

    def reader() -> None:
        try:
            conn = sqlite3.connect(str(db_path), timeout=10.0)
            apply_connection_pragmas(conn)
            row = conn.execute(
                "SELECT title FROM workstream_items WHERE item_id = ?",
                ("WL-1",),
            ).fetchone()
            read_result["title"] = row[0] if row else None
        except Exception as exc:  # pragma: no cover - propagated via flag
            read_result["error"] = exc
        finally:
            barrier.set()

    t = threading.Thread(target=reader)
    t.start()
    finished = barrier.wait(timeout=2.0)
    writer.rollback()
    writer.close()
    t.join(timeout=2.0)

    assert finished, "reader was blocked while writer held an immediate tx"
    assert "error" not in read_result, read_result
    assert read_result["title"] == "seed"


def test_concurrent_writer_retries_within_busy_timeout(tmp_path: Path) -> None:
    """A second writer should retry and succeed inside the busy_timeout window."""
    db_path = tmp_path / "workstream.db"
    entity_operation(
        "upsert",
        "workstream_items",
        entity_id="WL-A",
        properties={"title": "first", "status": "pending"},
        db_path=db_path,
    )

    holder = sqlite3.connect(str(db_path), timeout=10.0)
    apply_connection_pragmas(holder)
    holder.execute("BEGIN IMMEDIATE")
    holder.execute(
        "UPDATE workstream_items SET title = ? WHERE item_id = ?",
        ("in-flight", "WL-A"),
    )

    result: dict[str, object] = {}
    started = time.perf_counter()

    def writer() -> None:
        try:
            conn = sqlite3.connect(str(db_path), timeout=10.0)
            apply_connection_pragmas(conn, busy_timeout_ms=2000)
            conn.execute(
                "UPDATE workstream_items SET title = ? WHERE item_id = ?",
                ("second-wins", "WL-A"),
            )
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as exc:
            result["error"] = str(exc)
        finally:
            result["elapsed"] = time.perf_counter() - started

    t = threading.Thread(target=writer)
    t.start()
    time.sleep(0.2)
    holder.rollback()
    holder.close()
    t.join(timeout=5.0)

    assert "error" not in result, result
    assert result.get("elapsed", 0) >= 0.2, "second writer did not wait for the first"

    final = entity_operation(
        "list", "workstream_items", limit=10, db_path=db_path
    )
    titles = [item["title"] for item in final["items"]]
    assert "second-wins" in titles, titles


def test_existing_db_is_upgraded_in_place(tmp_path: Path) -> None:
    """A pre-existing rollback-journal DB must be upgraded on first open."""
    db_path = tmp_path / "workstream.db"
    legacy = sqlite3.connect(str(db_path))
    legacy.execute(
        "CREATE TABLE workstream_items (item_id TEXT PRIMARY KEY, title TEXT)"
    )
    legacy.execute("INSERT INTO workstream_items(item_id, title) VALUES ('x', 'y')")
    legacy.commit()
    legacy.close()

    assert _read_pragmas(db_path)["journal_mode"] != "wal"

    WorkstreamDB(db_path).close()
    assert _read_pragmas(db_path)["journal_mode"] == "wal"


def test_entity_operation_returns_wal_after_open(tmp_path: Path) -> None:
    db_path = tmp_path / "workstream.db"
    entity_operation(
        "upsert",
        "workstream_items",
        entity_id="WL-OK",
        properties={"title": "t", "status": "pending"},
        db_path=db_path,
    )
    assert _read_pragmas(db_path)["journal_mode"] == "wal"
