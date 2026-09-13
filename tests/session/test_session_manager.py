"""Tests for WL-106 SessionManager fork/rollback scaffolding."""

from __future__ import annotations

import pytest

from thegent.session.manager import (
    InvalidTurnIndexError,
    RollbackOutOfRangeError,
    SessionAlreadyExistsError,
    SessionManager,
)


def test_fork_session_clones_turn_prefix() -> None:
    manager = SessionManager()
    source_id = manager.create_session(session_id="source")
    manager.append_turn(source_id, {"turn_id": "t1", "content": "one"})
    manager.append_turn(source_id, {"turn_id": "t2", "content": "two"})
    manager.append_turn(source_id, {"turn_id": "t3", "content": "three"})

    fork_id = manager.fork_session(source_id, from_turn=2, new_session_id="forked")
    assert fork_id == "forked"
    assert [turn["turn_id"] for turn in manager.get_session(fork_id).turns] == [
        "t1",
        "t2",
    ]


def test_forked_session_diverges_from_original() -> None:
    manager = SessionManager()
    source_id = manager.create_session(session_id="source")
    manager.append_turn(source_id, {"turn_id": "t1", "content": "one"})

    fork_id = manager.fork_session(source_id, new_session_id="forked")
    manager.append_turn(fork_id, {"turn_id": "t2-fork", "content": "fork"})
    manager.append_turn(source_id, {"turn_id": "t2-source", "content": "source"})

    assert [turn["turn_id"] for turn in manager.get_session(source_id).turns] == [
        "t1",
        "t2-source",
    ]
    assert [turn["turn_id"] for turn in manager.get_session(fork_id).turns] == [
        "t1",
        "t2-fork",
    ]


def test_fork_session_rejects_invalid_index() -> None:
    manager = SessionManager()
    source_id = manager.create_session(session_id="source")
    manager.append_turn(source_id, {"turn_id": "t1", "content": "one"})

    with pytest.raises(InvalidTurnIndexError):
        manager.fork_session(source_id, from_turn=2)


def test_rollback_session_truncates_history() -> None:
    manager = SessionManager()
    session_id = manager.create_session(session_id="s")
    manager.append_turn(session_id, {"turn_id": "t1"})
    manager.append_turn(session_id, {"turn_id": "t2"})
    manager.append_turn(session_id, {"turn_id": "t3"})

    remaining = manager.rollback_session(session_id, n_turns=2)
    assert remaining == 1
    assert [turn["turn_id"] for turn in manager.get_session(session_id).turns] == ["t1"]


def test_rollback_session_rejects_overflow() -> None:
    manager = SessionManager()
    session_id = manager.create_session(session_id="s")
    manager.append_turn(session_id, {"turn_id": "t1"})

    with pytest.raises(RollbackOutOfRangeError):
        manager.rollback_session(session_id, n_turns=2)


def test_create_session_rejects_duplicate_session_id() -> None:
    manager = SessionManager()
    manager.create_session(session_id="s")

    with pytest.raises(SessionAlreadyExistsError):
        manager.create_session(session_id="s")


def test_fork_session_rejects_duplicate_target_session_id() -> None:
    manager = SessionManager()
    source_id = manager.create_session(session_id="source")
    manager.append_turn(source_id, {"turn_id": "t1"})
    manager.create_session(session_id="forked")

    with pytest.raises(SessionAlreadyExistsError):
        manager.fork_session(source_id, new_session_id="forked")
