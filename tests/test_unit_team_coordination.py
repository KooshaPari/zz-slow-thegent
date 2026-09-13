import orjson as json
import pytest

from thegent.team.coordination import TeamCoordinator
from thegent.team.manager import TeamManager


@pytest.fixture
def session_dir(tmp_path):
    return tmp_path


@pytest.fixture
def tm(session_dir):
    return TeamManager(session_dir)


@pytest.fixture
def tc(session_dir):
    return TeamCoordinator(session_dir)


def test_team_manager_lifecycle(tm):
    team_id = tm.create_team("Test Team", "leader-1", ["agent-1", "agent-2"])
    assert team_id.startswith("team_")

    task_id = tm.add_task(team_id, "Test Task", "Description")
    assert task_id.startswith("task_")

    tasks = tm.list_tasks(team_id)
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id
    assert tasks[0]["status"] == "pending"

    success = tm.assign_task(team_id, task_id, "agent-1")
    assert success

    tasks = tm.list_tasks(team_id)
    assert tasks[0]["status"] == "in_progress"
    assert tasks[0]["assigned_to"] == "agent-1"


def test_coordinator_detect_idle(tc):
    assert tc.detect_idle("How can I help you today?")
    assert tc.detect_idle("Waiting for your input...")
    assert not tc.detect_idle("I am currently working on the task.")
    assert tc.detect_idle("What's next?")  # Short question mark output


def test_coordinator_handle_task_completed(tm, tc):
    team_id = tm.create_team("Test Team", "leader-1", ["agent-1"])
    task_id = tm.add_task(team_id, "Test Task", "Description")

    tc.handle_task_completed(team_id, task_id, "Success!")

    tasks = tm.list_tasks(team_id)
    assert tasks[0]["status"] == "completed"
    assert tasks[0]["result"] == "Success!"
    assert "completed_at" in tasks[0]


def test_coordinator_broadcast(tm, tc, session_dir):
    team_id = tm.create_team("Test Team", "leader-1", ["agent-1", "agent-2", "agent-3"])

    tc.broadcast_message(team_id, "agent-1", "Hello team!")

    # Check inboxes for agent-2 and agent-3
    inbox_2 = session_dir / "teams" / team_id / "inboxes" / "agent-2.jsonl"
    inbox_3 = session_dir / "teams" / team_id / "inboxes" / "agent-3.jsonl"
    inbox_1 = session_dir / "teams" / team_id / "inboxes" / "agent-1.jsonl"

    assert inbox_2.exists()
    assert inbox_3.exists()
    assert not inbox_1.exists()

    lines = inbox_2.read_text().splitlines()
    assert len(lines) == 1
    msg = json.loads(lines[0])
    assert msg["sender"] == "agent-1"
    assert msg["message"] == "Hello team!"
