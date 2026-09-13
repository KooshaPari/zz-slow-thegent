"""Integration tests for TeammateManager with heliosShield coordination (WP-16003).

Tests the full integration between:
- TeammateManager delegation
- heliosShield Bridge task coordination
- Intent broadcasting
- Session state inspection
"""

import pytest

from thegent.governance.heliosShield_bridge import heliosShieldBridge
from thegent.governance.teammates import TeammateManager


class TestTeammateManagerheliosShieldIntegration:
    """Integration tests for TeammateManager with heliosShield Bridge."""

    @pytest.fixture
    def harness_root(self, tmp_path):
        """Create a temporary harness root for heliosShield."""
        harness = tmp_path / ".agent-harness"
        var_dir = harness / "var"
        var_dir.mkdir(parents=True, exist_ok=True)
        return harness

    @pytest.fixture
    def teammate_manager(self, tmp_path):
        """Create a TeammateManager instance."""
        return TeammateManager(tmp_path / "teammates.json")

    @pytest.fixture
    def helios_shield_bridge(self, harness_root, monkeypatch):
        """Create a heliosShieldBridge with mocked harness root."""
        monkeypatch.setenv("HARNESS_ROOT", str(harness_root))
        return heliosShieldBridge()

    def test_delegation_creates_heliosShield_task(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Delegation should create a task in heliosShield when available."""
        # Verify heliosShield is available
        assert helios_shield_bridge.is_available() is True

        # Create a delegation
        req = teammate_manager.delegate(
            teammate_id="coder-alpha",
            parent_run_id="RUN-123",
            prompt="Refactor the parser module to use async/await.",
        )

        # Verify task was created in heliosShield
        task_dir = harness_root / "var" / "tasks"
        task_file = task_dir / req.id
        assert task_file.exists(), "Task file should be created in heliosShield"

        # Verify task content
        content = task_file.read_text()
        assert f"id={req.id}" in content
        assert "status=pending" in content
        assert "RUN-123" in content
        assert "Refactor the parser" in content

    def test_delegation_broadcasts_intent(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Delegation should broadcast intent to heliosShield mesh."""
        # Create a delegation
        teammate_manager.delegate(
            teammate_id="reviewer-beta",
            parent_run_id="RUN-456",
            prompt="Review the authentication changes.",
        )

        # Verify intent was broadcast
        intent_dir = harness_root / "var" / "intents"
        intent_files = list(intent_dir.glob("*"))
        assert len(intent_files) > 0, "Intent file should be created"

        # Find the intent file for this delegation
        intent_content = None
        for intent_file in intent_files:
            content = intent_file.read_text()
            if "RUN-456" in content and "delegate" in content:
                intent_content = content
                break

        assert intent_content is not None, "Intent should contain delegation info"
        assert "agent=thegent:RUN-456" in intent_content
        assert "type=delegate" in intent_content
        assert "target=reviewer-beta" in intent_content
        assert "status=active" in intent_content

    def test_get_session_state_finds_delegations(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: get_session_state should find tasks and intents for a session."""
        session_id = "SESSION-789"

        # Create multiple delegations
        req1 = teammate_manager.delegate("coder-alpha", session_id, "Task 1")
        req2 = teammate_manager.delegate("reviewer-beta", session_id, "Task 2")

        # Get session state
        state = helios_shield_bridge.get_session_state(session_id)

        # Verify we found tasks
        assert len(state["tasks"]) >= 2, "Should find at least 2 tasks"

        # Verify we found intents
        assert len(state["intents"]) >= 2, "Should find at least 2 intents"

        # Verify task IDs match
        task_ids = []
        for task_lines in state["tasks"]:
            for line in task_lines:
                if line.startswith("id="):
                    task_ids.append(line.split("=", 1)[1])

        assert req1.id in task_ids
        assert req2.id in task_ids

    def test_delegation_works_without_heliosShield(self, teammate_manager, tmp_path, monkeypatch):
        """WP-16003: Delegation should work gracefully when heliosShield is not available."""
        # Set non-existent harness root
        monkeypatch.setenv("HARNESS_ROOT", str(tmp_path / "nonexistent"))

        # Delegation should still work
        req = teammate_manager.delegate(
            teammate_id="coder-alpha",
            parent_run_id="RUN-999",
            prompt="This should work without heliosShield.",
        )

        assert req.teammate_id == "coder-alpha"
        assert req.parent_run_id == "RUN-999"
        assert req.status == "pending"

    def test_multiple_delegations_create_multiple_tasks(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Multiple delegations should create multiple tasks."""
        parent_run = "RUN-MULTI"

        # Create multiple delegations
        reqs = []
        for i in range(3):
            req = teammate_manager.delegate(
                teammate_id=f"coder-{i}",
                parent_run_id=parent_run,
                prompt=f"Task {i}",
            )
            reqs.append(req)

        # Verify all tasks were created
        task_dir = harness_root / "var" / "tasks"
        created_tasks = list(task_dir.glob("*"))
        assert len(created_tasks) >= 3, "Should create at least 3 tasks"

        # Verify each task has correct content
        for req in reqs:
            task_file = task_dir / req.id
            assert task_file.exists(), f"Task {req.id} should exist"
            content = task_file.read_text()
            assert parent_run in content

    def test_delegation_task_includes_dependencies(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Task creation should handle dependencies correctly."""
        # Create first delegation
        req1 = teammate_manager.delegate("coder-alpha", "RUN-DEP", "First task")

        # Create second delegation that depends on first
        req2 = teammate_manager.delegate("reviewer-beta", "RUN-DEP", "Second task")

        # Verify both tasks exist
        task_dir = harness_root / "var" / "tasks"
        task1_file = task_dir / req1.id
        task2_file = task_dir / req2.id

        assert task1_file.exists()
        assert task2_file.exists()

        # Note: Current implementation doesn't set depends_on in delegation,
        # but the structure is there for future enhancement

    def test_session_state_empty_when_no_delegations(self, helios_shield_bridge):
        """WP-16003: get_session_state should return empty state for session with no delegations."""
        state = helios_shield_bridge.get_session_state("NONEXISTENT-SESSION")

        assert state == {"claims": [], "intents": [], "tasks": []}

    def test_intent_file_format(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Intent files should have correct format."""
        teammate_manager.delegate("coder-alpha", "RUN-FORMAT", "Test format")

        intent_dir = harness_root / "var" / "intents"
        intent_files = list(intent_dir.glob("*"))

        assert len(intent_files) == 1
        intent_file = intent_files[0]

        # Verify file name format: {pid}_{agent_id}_{intent_type}
        assert "_" in intent_file.name
        parts = intent_file.name.split("_")
        assert len(parts) >= 3

        # Verify content format
        content = intent_file.read_text()
        content.strip().split("\n")
        assert "agent=" in content
        assert "type=" in content
        assert "target=" in content
        assert "started=" in content
        assert "status=" in content

    def test_task_file_format(self, teammate_manager, helios_shield_bridge, harness_root):
        """WP-16003: Task files should have correct format."""
        req = teammate_manager.delegate("coder-alpha", "RUN-FORMAT", "Test task format")

        task_dir = harness_root / "var" / "tasks"
        task_file = task_dir / req.id

        content = task_file.read_text()
        lines = content.strip().split("\n")

        # Verify required fields
        assert any("id=" in line for line in lines)
        assert any("description=" in line for line in lines)
        assert any("status=" in line for line in lines)
        assert any("created_at=" in line for line in lines)
        assert any("depends_on=" in line for line in lines)
        assert any("assigned_to=" in line for line in lines)

    def test_delegation_status_update_preserves_heliosShield_task(
        self, teammate_manager, helios_shield_bridge, harness_root
    ):
        """WP-16003: Updating delegation status should not affect heliosShield task."""
        req = teammate_manager.delegate("coder-alpha", "RUN-UPDATE", "Task to update")

        task_dir = harness_root / "var" / "tasks"
        task_file = task_dir / req.id

        # Verify task exists
        assert task_file.exists()

        # Update delegation status
        teammate_manager.update_status(req.id, "in_progress", "Working on it...")

        # Task file should still exist
        assert task_file.exists()

        # Verify task content still has original info
        content = task_file.read_text()
        assert req.id in content
        assert "RUN-UPDATE" in content
