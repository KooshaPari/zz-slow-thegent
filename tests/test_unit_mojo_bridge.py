"""Tests for the Mojo Bridge module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from thegent.infra.mojo_bridge import (
    MOJO_KERNEL_CONTRACTS,
    MojoBridge,
    MojoNotAvailableError,
    MojoTask,
    build_provider_score_kernel_script,
    check_mojo_status,
    get_bridge,
    validate_kernel_contract,
)


class TestMojoBridge:
    """Test suite for MojoBridge."""

    def test_bridge_initialization(self, tmp_path):
        """Test that MojoBridge initializes correctly."""
        bridge = MojoBridge(
            mojo_root=tmp_path / "mojo",
            cache_root=tmp_path / "cache",
        )

        assert bridge.mojo_root == tmp_path / "mojo"
        assert bridge.cache_root == tmp_path / "cache"
        assert bridge.default_timeout > 0

    def test_mojo_not_available_error(self):
        """Test MojoNotAvailableError can be raised."""
        with pytest.raises(MojoNotAvailableError):
            raise MojoNotAvailableError("Test error")

    def test_mojo_task_creation(self):
        """Test MojoTask creation."""
        task = MojoTask(
            task_id="test_001",
            module="test_module",
            function="test_function",
            args={"arg1": "value1"},
            timeout=30.0,
        )

        assert task.task_id == "test_001"
        assert task.module == "test_module"
        assert task.function == "test_function"
        assert task.args == {"arg1": "value1"}
        assert task.timeout == 30.0

    def test_get_bridge_singleton(self):
        """Test that get_bridge returns a singleton."""
        bridge1 = get_bridge()
        bridge2 = get_bridge()

        assert bridge1 is bridge2

    def test_install_instructions_darwin(self):
        """Test install instructions on Darwin."""
        bridge = MojoBridge()

        # This test just verifies the method exists and returns a string
        instructions = bridge.install_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    @pytest.mark.asyncio
    async def test_check_mojo_status_returns_dict(self):
        """Test that check_mojo_status returns proper dict structure."""
        status = await check_mojo_status()

        assert isinstance(status, dict)
        assert "available" in status
        assert "version" in status
        assert "install_instructions" in status

    @pytest.mark.asyncio
    async def test_dispatch_returns_graceful_error_when_not_available(self):
        """Test that dispatch handles unavailable Mojo gracefully."""
        bridge = MojoBridge()

        # Mock is_available to return False (patch on the class since it's a property)
        from unittest.mock import PropertyMock

        with patch.object(type(bridge), "is_available", new_callable=PropertyMock, return_value=False):
            task = MojoTask(
                task_id="test_001",
                module="test",
                function="hello",
                args={},
            )

            result = await bridge.dispatch(task)

            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "mojo_not_available"


class TestMojoBridgeAvailability:
    """Tests for Mojo availability checking."""

    def test_check_mojo_returns_boolean(self):
        """Test that _check_mojo returns a boolean."""
        bridge = MojoBridge()
        result = bridge._check_mojo()

        assert isinstance(result, bool)


class TestMojoKernelContract:
    """WL-133 slice: deterministic kernel contract checks."""

    def test_provider_score_contract_registered(self):
        contract = MOJO_KERNEL_CONTRACTS[("math", "calculate_provider_score")]
        assert contract.required_args == ("cost_score", "quality_score", "latency_score")

    def test_validate_kernel_contract_raises_on_missing_args(self):
        with pytest.raises(ValueError):
            validate_kernel_contract(
                module="math",
                function="calculate_provider_score",
                args={"cost_score": 0.8},
            )

    def test_build_provider_score_kernel_script_contains_fields(self):
        script = build_provider_score_kernel_script()
        assert "cost_score" in script
        assert "quality_score" in script
        assert "latency_score" in script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
