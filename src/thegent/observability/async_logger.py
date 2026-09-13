"""Async logging utilities."""

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class ObservabilityEvent:
    """An observability event."""

    name: str
    timestamp: float
    data: dict[str, Any] | None = None


class AsyncLogger:
    """Async-compatible logger."""

    def __init__(self, name: str = "thegent") -> None:
        self.logger = logging.getLogger(name)

    async def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(msg, **kwargs)

    async def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(msg, **kwargs)

    async def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(msg, **kwargs)

    async def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(msg, **kwargs)


async def get_logger(name: str = "thegent") -> AsyncLogger:
    """Get an async logger instance."""
    return AsyncLogger(name)


class AsyncObservabilityLogger(AsyncLogger):
    """Extended async logger for observability."""

    def __init__(self, name: str = "thegent-observability") -> None:
        """Initialize the observability logger."""
        super().__init__(name)

    async def log_event(self, event: str, **kwargs: Any) -> None:
        """Log a structured observability event."""
        await self.info(f"[EVENT] {event}", extra=kwargs)


__all__ = [
    "AsyncLogger",
    "AsyncObservabilityLogger",
    "ObservabilityEvent",
    "get_logger",
    "_default_log_handler",
    "get_obs_logger",
    "reset_obs_logger",
]


async def reset_obs_logger() -> None:
    """Reset the observability logger state."""


async def get_obs_logger(
    name: str = "thegent-observability",
) -> AsyncObservabilityLogger:
    """Get an observability logger instance.

    Args:
        name: Logger name.

    Returns:
        AsyncObservabilityLogger instance.
    """
    return AsyncObservabilityLogger(name)


def _default_log_handler() -> dict[str, Any]:
    """Get the default log handler configuration.

    Returns:
        Dictionary with log handler configuration.
    """
    return {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "handlers": ["console"],
    }
