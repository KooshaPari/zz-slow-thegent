"""Unit tests for operations module."""

import pytest

from thegent.operations import (
    OPERATION_MAP,
    Operation,
    OperationEntry,
    get_operations_by_type,
    list_operations,
)


@pytest.mark.unit
class TestOperationEnum:
    """Tests for Operation enum values."""

    def test_orchestrate_value(self) -> None:
        # @trace FR-OPS-001
        """ORCHESTRATE has value 'orchestrate'."""
        assert Operation.ORCHESTRATE.value == "orchestrate"

    def test_govern_value(self) -> None:
        # @trace FR-OPS-001
        """GOVERN has value 'govern'."""
        assert Operation.GOVERN.value == "govern"

    def test_recover_value(self) -> None:
        # @trace FR-OPS-001
        """RECOVER has value 'recover'."""
        assert Operation.RECOVER.value == "recover"

    def test_observe_value(self) -> None:
        # @trace FR-OPS-001
        """OBSERVE has value 'observe'."""
        assert Operation.OBSERVE.value == "observe"

    def test_plan_value(self) -> None:
        # @trace FR-OPS-001
        """PLAN has value 'plan'."""
        assert Operation.PLAN.value == "plan"

    def test_all_enum_values_present(self) -> None:
        # @trace FR-OPS-001
        """All five operation types are defined."""
        values = {op.value for op in Operation}
        assert values == {"orchestrate", "govern", "recover", "observe", "plan"}


@pytest.mark.unit
class TestGetOperationsByType:
    """Tests for get_operations_by_type grouping."""

    def test_orchestrate_has_run_command(self) -> None:
        # @trace FR-OPS-002
        """ORCHESTRATE type includes the 'run' command."""
        entries = get_operations_by_type(Operation.ORCHESTRATE)
        commands = [e.command for e in entries]
        assert "run" in commands

    def test_observe_has_ps_command(self) -> None:
        # @trace FR-OPS-002
        """OBSERVE type includes the 'ps' command."""
        entries = get_operations_by_type(Operation.OBSERVE)
        commands = [e.command for e in entries]
        assert "ps" in commands

    def test_plan_has_dag_list(self) -> None:
        # @trace FR-OPS-002
        """PLAN type includes the 'dag list' command."""
        entries = get_operations_by_type(Operation.PLAN)
        commands = [e.command for e in entries]
        assert "dag list" in commands

    def test_recover_has_stop(self) -> None:
        # @trace FR-OPS-002
        """RECOVER type includes the 'stop' command."""
        entries = get_operations_by_type(Operation.RECOVER)
        commands = [e.command for e in entries]
        assert "stop" in commands

    def test_govern_has_policy_show(self) -> None:
        # @trace FR-OPS-002
        """GOVERN type includes the 'policy show' command."""
        entries = get_operations_by_type(Operation.GOVERN)
        commands = [e.command for e in entries]
        assert "policy show" in commands


@pytest.mark.unit
class TestListOperations:
    """Tests for list_operations() grouping."""

    def test_list_operations_has_all_types(self) -> None:
        # @trace FR-OPS-002
        """list_operations returns all five operation type keys."""
        ops = list_operations()
        assert set(ops.keys()) == {
            "orchestrate",
            "govern",
            "recover",
            "observe",
            "plan",
        }

    def test_list_operations_entries_have_required_keys(self) -> None:
        # @trace FR-OPS-002
        """Each entry dict has command, description, and mcp_tool keys."""
        ops = list_operations()
        for entries in ops.values():
            for entry in entries:
                assert "command" in entry
                assert "description" in entry
                assert "mcp_tool" in entry


@pytest.mark.unit
class TestOperationMap:
    """Tests for OPERATION_MAP completeness."""

    def test_all_entries_are_operation_entries(self) -> None:
        # @trace FR-OPS-001
        """All items in OPERATION_MAP are OperationEntry instances."""
        for entry in OPERATION_MAP:
            assert isinstance(entry, OperationEntry)

    def test_all_entries_have_valid_operation_type(self) -> None:
        # @trace FR-OPS-001
        """All entries have a valid Operation enum value."""
        for entry in OPERATION_MAP:
            assert isinstance(entry.operation, Operation)

    def test_map_has_entries_for_each_operation_type(self) -> None:
        # @trace FR-OPS-001
        """Every Operation type has at least one entry."""
        types_present = {e.operation for e in OPERATION_MAP}
        for op in Operation:
            assert op in types_present, f"No entry for {op.value}"
