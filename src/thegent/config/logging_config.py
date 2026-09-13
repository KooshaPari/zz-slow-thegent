"""Structured logging configuration for thegent.

# @trace WL152 — L20 Config + L22 logging sub-area hardening.

Provides:

* :class:`LoggingConfig` — pydantic-settings owned by ``thegent.config``.
  Reads env vars with prefix ``THGENT_LOG_*`` and exposes canonical
  knobs: ``level``, ``format``, ``redact``, ``sinks``.

* :func:`configure_logging` — installs a stderr-bound handler at the
  configured level. With ``format="JSON"`` it emits one JSON object per
  log line via the stdlib ``logging`` module (no runtime structlog
  dependency). With ``format="TEXT"`` it uses the conventional
  ``%(levelname)s %(name)s %(message)s`` template.

* :class:`SecretMaskingFormatter` — a ``logging.Formatter`` subclass
  that replaces values registered via :func:`register_secret_for_masking`
  with ``***SECRET***`` in every formatted record.

* :func:`register_secret_for_masking` — sidecar registry for known
  secret values. Idempotent registration; pass ``_remove=True`` to
  unregister.

The module is intentionally side-effect-free on import. Callers must
invoke :func:`configure_logging` to wire the root logger. This keeps
import-time deterministic for tests and CLI startup.
"""

from __future__ import annotations

import json as _json
import logging
import sys
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Type aliases for clarity at the public API surface.
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
type LogFormat = Literal["TEXT", "JSON"]
type LogSink = Literal["STDERR", "STDOUT", "NULL"]

# Canonical masking placeholder.
SECRET_PLACEHOLDER = "***SECRET***"

# Sidecar registry of values that should be replaced in log output.
# Module-level mutable container is intentional — the registry is a
# process-wide singleton, mirroring the stdlib ``logging`` module's own
# module-level state. Access via ``registered_secrets()`` /
# ``register_secret_for_masking()`` (no direct mutation).
_SECRET_REGISTRY: set[str] = set()


def registered_secrets() -> set[str]:
    """Return a snapshot of currently registered secret values."""
    return set(_SECRET_REGISTRY)


def register_secret_for_masking(value: str, *, _remove: bool = False) -> None:
    """Register or unregister a value for log masking.

    Args:
        value: The literal string to redact. Registration is a substring
            match; longer values are masked wherever they appear.
        _remove: Internal flag — pass ``True`` to unregister the value.
    """
    if _remove:
        _SECRET_REGISTRY.discard(value)
        return
    if value:
        _SECRET_REGISTRY.add(value)


class LoggingConfig(BaseSettings):
    """Canonical logging configuration for thegent.

    Defaults are tuned for local CLI use:
    * ``level=INFO`` — operational visibility without debug noise
    * ``format=text`` — human-readable lines for terminal output
    * ``redact=True`` — secrets masked before reaching the handler
    * ``sinks=["stderr"]`` — default sink is the terminal

    Overridable via env vars ``THGENT_LOG_LEVEL``, ``THGENT_LOG_FORMAT``,
    ``THGENT_LOG_REDACT``, ``THGENT_LOG_SINKS``.
    """

    model_config = SettingsConfigDict(
        env_prefix="THGENT_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: LogLevel = Field(
        default="INFO",
        description="Root logger level (THGENT_LOG_LEVEL)",
    )
    format: LogFormat = Field(
        default="TEXT",
        description="Log record format (THGENT_LOG_FORMAT)",
    )
    redact: bool = Field(
        default=True,
        description="Mask registered secret values in emitted records (THGENT_LOG_REDACT)",
    )
    sinks: Annotated[list[LogSink], NoDecode] = Field(
        default_factory=lambda: ["STDERR"],
        description="Log sinks to install (THGENT_LOG_SINKS, comma-separated)",
    )

    @field_validator("level", "format", mode="before")
    @classmethod
    def _coerce_upper(cls, value: object) -> object:
        # Env vars arrive in any case (THGENT_LOG_LEVEL=info/INFO/Info);
        # canonical literals are uppercase, so normalize before pydantic's
        # literal validation runs.
        if isinstance(value, str):
            return value.upper()
        return value

    @field_validator("sinks", mode="before")
    @classmethod
    def _split_sinks_csv(cls, value: object) -> object:
        # Env var THGENT_LOG_SINKS arrives as a comma-separated string;
        # programmatic callers may pass a list. Normalise both to list[str].
        if isinstance(value, str):
            return [item.strip().upper() for item in value.split(",") if item.strip()]
        return value

    @field_validator("sinks")
    @classmethod
    def _validate_sinks(cls, value: list[str]) -> list[LogSink]:
        if not value:
            raise ValueError("sinks must contain at least one entry")
        # Coerce and validate each entry to the canonical literal set.
        allowed = {"STDERR", "STDOUT", "NULL"}
        coerced: list[LogSink] = []
        for entry in value:
            if entry not in allowed:
                raise ValueError(f"invalid sink: {entry!r}")
            coerced.append(entry)  # type: ignore[arg-type]
        return coerced


class SecretMaskingFormatter(logging.Formatter):
    """Formatter that masks values registered via ``register_secret_for_masking``.

    The masking step runs after the underlying formatter produces its
    text, so all standard ``%(field)s`` substitutions work as expected.
    Substrings are replaced with the canonical ``***SECRET***``
    placeholder; repeated matches in one record are all replaced.
    """

    def __init__(self, fmt: str | None = None) -> None:
        super().__init__(fmt or "%(message)s")

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        rendered = super().format(record)
        secrets = registered_secrets()
        if not secrets:
            return rendered
        masked = rendered
        for value in secrets:
            if value and value in masked:
                masked = masked.replace(value, SECRET_PLACEHOLDER)
        return masked


class _ComposedMaskingFormatter(logging.Formatter):
    """Compose a base formatter with the secret-masking step.

    The base formatter is invoked first (it knows how to render JSON or
    text). The output is then post-processed by the masking step.
    This keeps the masking step orthogonal to the format kind.
    """

    def __init__(self, base: logging.Formatter) -> None:
        super().__init__()
        self._base = base

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        rendered = self._base.format(record)
        secrets = registered_secrets()
        if not secrets:
            return rendered
        masked = rendered
        for value in secrets:
            if value and value in masked:
                masked = masked.replace(value, SECRET_PLACEHOLDER)
        return masked


class _JsonFormatter(logging.Formatter):
    """Formatter that emits one JSON object per record.

    Mirrors the canonical text template's fields (level, name, message)
    while remaining a thin stdlib-only implementation — no runtime
    dependency on structlog (which is a declared dep but kept optional
    at the logging layer).
    """

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return _json.dumps(payload, ensure_ascii=False)


def _build_handler(level: int, fmt_kind: LogFormat, redact: bool) -> logging.Handler:
    """Build a stderr-bound handler with the configured formatter."""
    if fmt_kind == "JSON":
        base: logging.Formatter = _JsonFormatter()
    else:
        base = logging.Formatter("%(levelname)s %(name)s %(message)s")
    formatter: logging.Formatter = _ComposedMaskingFormatter(base) if redact else base
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def configure_logging(cfg: LoggingConfig | None = None) -> None:
    """Wire the root logger per ``cfg`` (default: ``LoggingConfig()``).

    Idempotent: replaces existing root handlers with the configured
    handler(s). Other loggers are not touched — only the root, so
    per-module loggers inherit the configuration via stdlib semantics.
    """
    if cfg is None:
        cfg = LoggingConfig()
    root = logging.getLogger()
    # Canonical form is lowercase ("info"); stdlib uses uppercase ("INFO").
    level_int = getattr(logging, cfg.level.upper())
    # Clear existing handlers to keep configure_logging idempotent.
    for handler in list(root.handlers):
        root.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # noqa: BLE001 — close failures are non-fatal
            pass
    if "STDERR" in cfg.sinks:
        root.addHandler(_build_handler(level_int, cfg.format, cfg.redact))
    # Future sinks ("STDOUT", "NULL") can be added here without API change.
    root.setLevel(level_int)


__all__ = [
    "LoggingConfig",
    "SecretMaskingFormatter",
    "configure_logging",
    "register_secret_for_masking",
    "registered_secrets",
    "SECRET_PLACEHOLDER",
    "LogLevel",
    "LogFormat",
    "LogSink",
]
