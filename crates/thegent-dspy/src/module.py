from abc import ABC, abstractmethod
from typing import Any


class DSPyModule(ABC):
    """Base class for DSPy-style modules within thegent."""

    def __init__(self, name: str = "module") -> None:
        self.name = name
        self.config: dict[str, Any] = {}

    @abstractmethod
    def forward(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the module's core logic. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement forward()")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.forward(*args, **kwargs)
