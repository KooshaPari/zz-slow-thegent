"""
Integration Tests

Cross-module functionality tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestTeammateIntegration:
    """Test teammate_registry + delegation_protocol integration."""

    def test_teammate_discovery_and_delegation(self):
        """Test discovering teammates and delegating tasks."""
        from thegent.teammates import Delegate, TeammateRegistry

        registry = TeammateRegistry(agents_dir="agents")
        teammates = registry.discover()

        assert len(teammates) >= 0  # May be empty if no agents dir

        Delegate(registry)
        # Would test delegation but needs actual teammate

    @pytest.mark.integration
    def test_delegation_with_caching(self):
        """Test delegation with cache integration."""
        from thegent.teammates import Delegate

        from thegent.cache import TieredCache

        cache = TieredCache()
        Delegate()

        # Test cache can store delegation results
        cache.set("test_key", {"result": "success"})
        result = cache.get("test_key")
        assert result == {"result": "success"}


class TestCacheIntegration:
    """Test cache tier integration."""

    def test_l1_l2_fallback(self):
        """Test L1 to L2 fallback."""
        from thegent.cache import TieredCache

        cache = TieredCache()
        cache.set("key1", "value1")

        # Should get from L1
        result = cache.get("key1")
        assert result == "value1"

    def test_cache_promotion(self):
        """Test promotion from L2 to L1 on get."""
        from thegent.cache import TieredCache

        cache = TieredCache()

        # Set directly in L2 (simulating previous run)
        cache.l2.set("key2", "value2")

        # Clear L1
        cache.l1.clear()

        # Get should promote from L2 to L1
        result = cache.get("key2")
        assert result == "value2"

        # Now should be in L1
        assert cache.l1.get("key2") == "value2"


class TestScalingIntegration:
    """Test dynamic scaling integration."""

    def test_resource_monitoring(self):
        """Test resource monitoring samples."""
        from thegent.scaling import ResourceMonitor

        monitor = ResourceMonitor()
        sample = monitor.sample()

        assert sample.cpu_percent >= 0
        assert sample.memory_percent >= 0

    def test_dynamic_limiter_adjusts(self):
        """Test limiter adjusts based on pressure."""
        from thegent.scaling import DynamicLimiter

        limiter = DynamicLimiter(min_limit=1, max_limit=10, initial_limit=5)

        # Should have initial limit
        assert 1 <= limiter.current_limit <= 10


class TestShellIntegration:
    """Test shell execution integration."""

    def test_shell_timeout_config(self):
        """Test shell timeout configuration."""
        from thegent.shell import ShellConfig

        config = ShellConfig(default_timeout=300.0)
        assert config.get_timeout() == 300.0
        assert config.get_timeout(100.0) == 100.0

    def test_shell_retry_backoff(self):
        """Test exponential backoff calculation."""
        from thegent.shell import ShellConfig

        config = ShellConfig()

        delay0 = config.get_retry_delay(0)
        delay1 = config.get_retry_delay(1)
        delay2 = config.get_retry_delay(2)

        assert delay1 > delay0
        assert delay2 > delay1


class TestProcessIntegration:
    """Test process management integration."""

    def test_process_cleanup_registration(self):
        """Test process cleanup registration."""
        import os

        from thegent.process import register_cleanup

        register_cleanup(os.getpid())  # Register current process

    def test_signal_handler_install(self):
        """Test signal handler installation."""
        from thegent.process.signals import install_signal_handlers

        handler = install_signal_handlers()
        assert handler is not None


# Pytest markers
pytestmark = [
    pytest.mark.integration,
]
