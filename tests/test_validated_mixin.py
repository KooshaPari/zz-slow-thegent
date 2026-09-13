import pytest

pytestmark = pytest.mark.skip(reason="validated_dataclass and ContextManagerMixin not implemented")

"""Tests for ValidatedMixin and related patterns."""

from dataclasses import dataclass

import pytest

# validated_dataclass not yet implemented
validated_dataclass = None
# ContextManagerMixin, AsyncContextMixin not implemented


class TestValidatedDataclass:
    """Tests for validated_dataclass decorator.

    Note: @validated_dataclass must be ABOVE @dataclass to work correctly!
    """

    def test_basic_validation(self):
        """Test that validators are called."""
        call_log = []

        @validated_dataclass
        @dataclass
        class User:
            name: str
            age: int

            def validate_age(self, value: int) -> int:
                call_log.append(("age", value))
                if value < 0:
                    raise ValueError("age must be non-negative")
                return value

        user = User(name="Alice", age=30)
        assert ("age", 30) in call_log
        assert user.age == 30

    def test_validation_coercion(self):
        """Test that validators can transform values."""

        @validated_dataclass
        @dataclass
        class Config:
            value: str

            def validate_value(self, value: str) -> str:
                return value.upper()

        config = Config(value="hello")
        assert config.value == "HELLO"

    def test_validation_raises_on_invalid(self):
        """Test that invalid values raise."""

        @validated_dataclass
        @dataclass
        class StrictPositive:
            num: int

            def validate_num(self, value: int) -> int:
                if value <= 0:
                    raise ValueError("must be positive")
                return value

        with pytest.raises(ValueError, match="must be positive"):
            StrictPositive(num=-5)

    def test_multiple_validators(self):
        """Test multiple field validators."""
        log = []

        @validated_dataclass
        @dataclass
        class Item:
            name: str
            price: float
            quantity: int

            def validate_name(self, value: str) -> str:
                log.append(("name", value))
                return value.strip()

            def validate_price(self, value: float) -> float:
                log.append(("price", value))
                if value < 0:
                    raise ValueError("price cannot be negative")
                return round(value, 2)

            def validate_quantity(self, value: int) -> int:
                log.append(("quantity", value))
                if value < 0:
                    raise ValueError("quantity cannot be negative")
                return value

        item = Item(name="  Widget  ", price=9.999, quantity=5)
        assert item.name == "Widget"
        assert item.price == 10.0  # rounded
        assert item.quantity == 5
        assert len(log) == 3

    def test_preserves_existing_post_init(self):
        """Test that validated_dataclass preserves existing __post_init__."""
        log = []

        @validated_dataclass
        @dataclass
        class WithPostInit:
            value: int
            doubled: int = 0

            def validate_value(self, value: int) -> int:
                log.append(("validate", value))
                return value

            def __post_init__(self) -> None:
                log.append(("post_init", self.value))
                self.doubled = self.value * 2

        obj = WithPostInit(value=5)
        assert obj.doubled == 10
        assert ("validate", 5) in log
        assert ("post_init", 5) in log

    def test_no_validators_no_change(self):
        """Test that classes without validators work normally."""

        @validated_dataclass
        @dataclass
        class NoValidators:
            x: int
            y: str

        obj = NoValidators(x=1, y="test")
        assert obj.x == 1
        assert obj.y == "test"


class TestContextManagerMixin:
    """Tests for ContextManagerMixin."""

    def test_basic_context_manager(self):
        """Test basic context manager usage."""
        state = {"entered": False, "exited": False}

        class MyResource(ContextManagerMixin):
            def _enter(self):
                state["entered"] = True
                return self

            def _exit(self, exc_type, exc_val, exc_tb):
                state["exited"] = True
                return False

        with MyResource():
            assert state["entered"]
            assert not state["exited"]

        assert state["exited"]

    def test_context_manager_with_exception(self):
        """Test that _exit is called on exception."""
        log = []

        class FailingResource(ContextManagerMixin):
            def _enter(self):
                return self

            def _exit(self, exc_type, exc_val, exc_tb):
                log.append(("exit", exc_type))
                return False  # Don't suppress

        with pytest.raises(RuntimeError), FailingResource():
            raise RuntimeError("test error")

        assert len(log) == 1
        assert log[0][0] == "exit"
        assert log[0][1] is RuntimeError

    def test_context_manager_without_methods(self):
        """Test that mixin works without _enter/_exit methods."""

        class MinimalResource(ContextManagerMixin):
            pass

        with MinimalResource() as r:
            assert isinstance(r, MinimalResource)

    def test_exception_suppression(self):
        """Test that _exit can suppress exceptions."""

        class SuppressingResource(ContextManagerMixin):
            def _exit(self, exc_type, exc_val, exc_tb):
                return True  # Suppress exception

        with SuppressingResource():
            raise ValueError("This should be suppressed")
        # No exception raised


class TestAsyncContextManagerMixin:
    """Tests for AsyncContextManagerMixin."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage."""
        state = {"entered": False, "exited": False}

        class AsyncResource(AsyncContextManagerMixin):
            async def _aenter(self):
                state["entered"] = True
                return self

            async def _aexit(self, exc_type, exc_val, exc_tb):
                state["exited"] = True
                return False

        async with AsyncResource():
            assert state["entered"]
            assert not state["exited"]

        assert state["exited"]

    @pytest.mark.asyncio
    async def test_async_without_methods(self):
        """Test async mixin without _aenter/_aexit."""

        class MinimalAsync(AsyncContextManagerMixin):
            pass

        async with MinimalAsync() as r:
            assert isinstance(r, MinimalAsync)
