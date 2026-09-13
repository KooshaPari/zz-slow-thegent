"""Tests for SingletonMixin."""

import threading

import pytest

from thegent.integrations.base import SingletonMixin


class SimpleSingleton(SingletonMixin):
    """Test singleton class."""

    def __init__(self, value: str = "default"):
        self.value = value


class CounterSingleton(SingletonMixin):
    """Singleton with counter."""

    def __init__(self):
        self.count = 0

    def increment(self) -> int:
        self.count += 1
        return self.count


class TestGetInstance:
    """Tests for get_instance."""

    def setup_method(self):
        """Reset singleton before each test."""
        SimpleSingleton.reset_instance()
        CounterSingleton.reset_instance()

    def test_returns_same_instance(self):
        """Test that get_instance returns the same instance."""
        instance1 = SimpleSingleton.get_instance()
        instance2 = SimpleSingleton.get_instance()

        assert instance1 is instance2

    def test_default_initialization(self):
        """Test default initialization."""
        instance = SimpleSingleton.get_instance()

        assert instance.value == "default"

    def test_custom_initialization(self):
        """Test custom initialization on first call."""
        instance = SimpleSingleton.get_instance(value="custom")

        assert instance.value == "custom"

    def test_subsequent_calls_ignore_args(self):
        """Test that args after first call are ignored."""
        instance1 = SimpleSingleton.get_instance(value="first")
        instance2 = SimpleSingleton.get_instance(value="second")

        assert instance1.value == "first"
        assert instance2.value == "first"
        assert instance1 is instance2


class TestResetInstance:
    """Tests for reset_instance."""

    def setup_method(self):
        """Reset singleton before each test."""
        SimpleSingleton.reset_instance()

    def test_reset_creates_new_instance(self):
        """Test that reset allows new instance creation."""
        instance1 = SimpleSingleton.get_instance(value="first")
        SimpleSingleton.reset_instance()
        instance2 = SimpleSingleton.get_instance(value="second")

        assert instance1 is not instance2
        assert instance2.value == "second"

    def test_reset_clears_instance(self):
        """Test that has_instance returns False after reset."""
        SimpleSingleton.get_instance()
        assert SimpleSingleton.has_instance()

        SimpleSingleton.reset_instance()
        assert not SimpleSingleton.has_instance()


class TestHasInstance:
    """Tests for has_instance."""

    def setup_method(self):
        """Reset singleton before each test."""
        SimpleSingleton.reset_instance()

    def test_false_before_creation(self):
        """Test has_instance is False before creation."""
        assert not SimpleSingleton.has_instance()

    def test_true_after_creation(self):
        """Test has_instance is True after creation."""
        SimpleSingleton.get_instance()
        assert SimpleSingleton.has_instance()


class TestThreadSafety:
    """Tests for thread safety."""

    def setup_method(self):
        """Reset singleton before each test."""
        CounterSingleton.reset_instance()

    def test_concurrent_access(self):
        """Test that concurrent access is thread-safe."""
        instances = []

        def create_instance():
            instance = CounterSingleton.get_instance()
            instances.append(instance)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same object
        assert all(inst is instances[0] for inst in instances)

    def test_concurrent_increment(self):
        """Test concurrent operations on singleton."""
        instance = CounterSingleton.get_instance()
        results = []

        def increment():
            results.append(instance.increment())

        threads = [threading.Thread(target=increment) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Final count should be 100
        assert instance.count == 100
        # All results should be unique (no race conditions)
        assert len(results) == 100
        assert len(set(results)) == 100


class TestMultipleSingletons:
    """Tests for multiple singleton classes."""

    def setup_method(self):
        """Reset all singletons."""
        SimpleSingleton.reset_instance()
        CounterSingleton.reset_instance()

    def test_different_classes_have_different_instances(self):
        """Test that different singleton classes have different instances."""
        simple = SimpleSingleton.get_instance()
        counter = CounterSingleton.get_instance()

        assert simple is not counter
        assert type(simple) is SimpleSingleton
        assert type(counter) is CounterSingleton

    def test_reset_one_does_not_affect_others(self):
        """Test that resetting one singleton doesn't affect others."""
        simple1 = SimpleSingleton.get_instance()
        counter1 = CounterSingleton.get_instance()

        SimpleSingleton.reset_instance()

        # Counter should still exist
        assert CounterSingleton.has_instance()
        counter2 = CounterSingleton.get_instance()
        assert counter1 is counter2

        # Simple should be new
        simple2 = SimpleSingleton.get_instance()
        assert simple1 is not simple2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
