"""Tests for shared task worker pool (MTSP-03).

Tests cover TaskRequest, TaskResult, and TaskWorkerPool lifecycle.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.orchestration.worker_pool import (
    TaskRequest,
    TaskResult,
    TaskWorkerPool,
)


class TestTaskRequest:
    """Tests for TaskRequest dataclass."""

    def test_default_id_generated(self) -> None:
        """Verify default ID is generated."""
        task = TaskRequest()

        assert task.id.startswith("task_")
        assert len(task.id) == 13  # "task_" + 8 hex chars

    def test_unique_ids(self) -> None:
        """Verify generated IDs are unique."""
        task1 = TaskRequest()
        task2 = TaskRequest()

        assert task1.id != task2.id

    def test_default_command_empty(self) -> None:
        """Verify default command is empty list."""
        task = TaskRequest()

        assert task.command == []

    def test_default_cwd_none(self) -> None:
        """Verify default cwd is None."""
        task = TaskRequest()

        assert task.cwd is None

    def test_default_env_empty(self) -> None:
        """Verify default env is empty dict."""
        task = TaskRequest()

        assert task.env == {}

    def test_default_priority_zero(self) -> None:
        """Verify default priority is 0."""
        task = TaskRequest()

        assert task.priority == 0

    def test_custom_values(self) -> None:
        """Verify custom values are preserved."""
        task = TaskRequest(
            id="custom-task-001",
            command=["echo", "hello"],
            cwd="/workspace",
            env={"VAR": "value"},
            priority=10,
        )

        assert task.id == "custom-task-001"
        assert task.command == ["echo", "hello"]
        assert task.cwd == "/workspace"
        assert task.env == {"VAR": "value"}
        assert task.priority == 10

    def test_created_at_generated(self) -> None:
        """Verify created_at is generated."""
        task = TaskRequest()

        assert task.created_at is not None
        assert "T" in task.created_at  # ISO format


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_required_fields(self) -> None:
        """Verify required fields must be provided."""
        result = TaskResult(
            task_id="task-001",
            exit_code=0,
            stdout="output",
            stderr="",
            duration_s=1.5,
        )

        assert result.task_id == "task-001"
        assert result.exit_code == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.duration_s == 1.5

    def test_ended_at_generated(self) -> None:
        """Verify ended_at is generated."""
        result = TaskResult(
            task_id="task-001",
            exit_code=0,
            stdout="",
            stderr="",
            duration_s=1.0,
        )

        assert result.ended_at is not None
        assert "T" in result.ended_at  # ISO format

    def test_custom_ended_at(self) -> None:
        """Verify custom ended_at can be set."""
        result = TaskResult(
            task_id="task-001",
            exit_code=0,
            stdout="",
            stderr="",
            duration_s=1.0,
            ended_at="2025-01-01T00:00:00Z",
        )

        assert result.ended_at == "2025-01-01T00:00:00Z"


class TestTaskWorkerPoolInit:
    """Tests for TaskWorkerPool initialization."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.cache_dir = Path("/tmp/thegent/cache")
        return settings

    def test_default_max_workers(self, mock_settings: MagicMock) -> None:
        """Verify default max_workers is 4."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings", return_value=mock_settings):
            pool = TaskWorkerPool()

            assert pool.max_workers == 4

    def test_custom_max_workers(self, mock_settings: MagicMock) -> None:
        """Verify custom max_workers can be set."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings", return_value=mock_settings):
            pool = TaskWorkerPool(max_workers=8)

            assert pool.max_workers == 8

    def test_creates_queue_directories(self, tmp_path: Path) -> None:
        """Verify queue directories are created."""
        queue_dir = tmp_path / "queue"

        with patch("thegent.orchestration.worker_pool.ThegentSettings") as mock:
            mock.return_value.cache_dir = tmp_path

            pool = TaskWorkerPool(queue_dir=queue_dir)

            assert pool.queue_dir.exists()
            assert pool.inbox.exists()
            assert pool.results.exists()

    def test_not_running_initially(self, mock_settings: MagicMock) -> None:
        """Verify pool is not running initially."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings", return_value=mock_settings):
            pool = TaskWorkerPool()

            assert pool._running is False


class TestTaskWorkerPoolStop:
    """Tests for TaskWorkerPool.stop method."""

    @pytest.fixture
    def pool(self, tmp_path: Path) -> TaskWorkerPool:
        """Create a TaskWorkerPool instance."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings") as mock:
            mock.return_value.cache_dir = tmp_path
            return TaskWorkerPool(queue_dir=tmp_path / "queue")

    def test_sets_running_false(self, pool: TaskWorkerPool) -> None:
        """Verify stop sets _running to False."""
        pool._running = True
        pool.stop()

        assert pool._running is False

    def test_idempotent(self, pool: TaskWorkerPool) -> None:
        """Verify stop is idempotent."""
        pool.stop()
        pool.stop()

        assert pool._running is False


class TestTaskWorkerPoolSubmitTask:
    """Tests for TaskWorkerPool.submit_task method."""

    @pytest.fixture
    def pool(self, tmp_path: Path) -> TaskWorkerPool:
        """Create a TaskWorkerPool instance."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings") as mock:
            mock.return_value.cache_dir = tmp_path
            return TaskWorkerPool(queue_dir=tmp_path / "queue")

    def test_creates_task_file(self, pool: TaskWorkerPool) -> None:
        """Verify task file is created in inbox."""
        task = TaskRequest(
            id="test-task-001",
            command=["echo", "test"],
        )

        result = pool.submit_task(task)

        assert result.exists()
        assert result.name == "test-task-001.json"
        assert result.parent == pool.inbox

    def test_file_contains_task_data(self, pool: TaskWorkerPool) -> None:
        """Verify task file contains correct data."""
        task = TaskRequest(
            id="test-task-002",
            command=["python", "-c", "print(1)"],
            cwd="/workspace",
            env={"DEBUG": "1"},
            priority=5,
        )

        pool.submit_task(task)
        task_file = pool.inbox / "test-task-002.json"
        data = json.loads(task_file.read_text())

        assert data["id"] == "test-task-002"
        assert data["command"] == ["python", "-c", "print(1)"]
        assert data["cwd"] == "/workspace"
        assert data["env"] == {"DEBUG": "1"}
        assert data["priority"] == 5

    def test_returns_task_file_path(self, pool: TaskWorkerPool) -> None:
        """Verify task file path is returned."""
        task = TaskRequest(id="test-task-003")

        result = pool.submit_task(task)

        assert result == pool.inbox / "test-task-003.json"


class TestTaskWorkerPoolGetResult:
    """Tests for TaskWorkerPool.get_result method."""

    @pytest.fixture
    def pool(self, tmp_path: Path) -> TaskWorkerPool:
        """Create a TaskWorkerPool instance."""
        with patch("thegent.orchestration.worker_pool.ThegentSettings") as mock:
            mock.return_value.cache_dir = tmp_path
            return TaskWorkerPool(queue_dir=tmp_path / "queue")

    def test_returns_none_when_no_result(self, pool: TaskWorkerPool) -> None:
        """Verify None when no result exists."""
        result = pool.get_result("nonexistent-task", timeout=1)

        assert result is None

    def test_returns_result_when_exists(self, pool: TaskWorkerPool) -> None:
        """Verify result is returned when file exists."""
        # Create a result file
        result_data = {
            "task_id": "task-001",
            "exit_code": 0,
            "stdout": "hello",
            "stderr": "",
            "duration_s": 0.5,
            "ended_at": "2025-01-01T00:00:00Z",
        }
        result_file = pool.results / "task-001.json"
        result_file.write_text(json.dumps(result_data).decode())

        result = pool.get_result("task-001", timeout=1)

        assert result is not None
        assert result.task_id == "task-001"
        assert result.exit_code == 0
        assert result.stdout == "hello"
        assert result.duration_s == 0.5

    def test_deletes_result_file_after_read(self, pool: TaskWorkerPool) -> None:
        """Verify result file is deleted after reading."""
        result_data = {
            "task_id": "task-002",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "duration_s": 1.0,
        }
        result_file = pool.results / "task-002.json"
        result_file.write_text(json.dumps(result_data).decode())

        pool.get_result("task-002", timeout=1)

        assert not result_file.exists()

    def test_handles_corrupt_json(self, pool: TaskWorkerPool) -> None:
        """Verify corrupt JSON is handled gracefully."""
        result_file = pool.results / "task-003.json"
        result_file.write_text("not valid json")

        result = pool.get_result("task-003", timeout=1)

        assert result is None

    def test_timeout_parameter(self, pool: TaskWorkerPool) -> None:
        """Verify timeout parameter works."""
        import time

        start = time.time()
        result = pool.get_result("nonexistent", timeout=1)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 1.0
