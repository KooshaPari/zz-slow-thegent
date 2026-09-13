"""Unit tests for WL152 — Structured LoggingConfig + Secret-masking hook.

# @trace WL152 — L20 Config + L22 logging sub-area hardening.

These tests pin the canonical surface for:

1. ``LoggingConfig`` — pydantic-settings owned by ``thegent.config``.
   Defaults: level=INFO, format=TEXT, redact=True, sinks=["STDERR"].
   Reads env vars with prefix ``THGENT_LOG_*``.
2. ``configure_logging(cfg=None)`` — installs a stderr handler at the
   configured level. With ``format="JSON"`` it emits structured JSON
   via stdlib ``logging`` (no structlog runtime dep). With
   ``format="TEXT"`` it uses the conventional ``%(levelname)s %(name)s
   ``%(message)s`` template.
3. ``SecretMaskingFormatter`` — a ``logging.Formatter`` subclass that
   replaces registered secret values with ``***SECRET***`` in every
   formatted record.

4. ``register_secret_for_masking(value)`` — sidecar registry for known
   secret values; ``SecretMaskingFormatter`` consults this registry.

5. ``ThegentSettings.log_config`` — nested field whose presence is
   part of the canonical surface (no consumer change required).
6. ``ThegentSettings.secret_fields()`` — returns the names of the six
   documented sensitive fields for audit and downstream masking.
"""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from thegent.config import ThegentSettings
from thegent.config.logging_config import (
    LoggingConfig,
    SecretMaskingFormatter,
    configure_logging,
    register_secret_for_masking,
    registered_secrets,
)


@pytest.fixture(autouse=True)
def _reset_logging_handlers() -> Iterator[None]:
    """Snapshot/restore root logger handlers around each test."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    root.handlers.clear()
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)


@pytest.fixture(autouse=True)
def _clear_secret_registry() -> Iterator[None]:
    """Clear registered_secrets() registry around each test."""
    saved = list(registered_secrets())
    yield
    for value in list(registered_secrets()):
        if value not in saved:
            register_secret_for_masking(value, _remove=True)


@pytest.fixture
def stream() -> io.StringIO:
    """In-memory stream for capturing log output."""
    return io.StringIO()


@pytest.mark.unit
class TestLoggingConfigDefaults:
    """LoggingConfig has the canonical defaults."""

    def test_defaults_match_canonical_surface(self) -> None:
        """Defaults: level=INFO, format=TEXT, redact=True, sinks=["STDERR"]."""
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.format == "TEXT"
        assert cfg.redact is True
        assert cfg.sinks == ["STDERR"]

    def test_invalid_level_rejected(self) -> None:
        """Level must be one of the canonical logging level names."""
        with pytest.raises(ValueError, match="level"):
            LoggingConfig(level="TRACE")  # type: ignore[arg-type]

    def test_invalid_format_rejected(self) -> None:
        """Format must be 'TEXT' or 'JSON'."""
        with pytest.raises(ValueError, match="format"):
            LoggingConfig(format="XML")  # type: ignore[arg-type]

    def test_invalid_sink_rejected(self) -> None:
        """Each sink must be in {STDERR, STDOUT, NULL}."""
        with pytest.raises(ValueError, match="sinks"):
            LoggingConfig(sinks=["stdout"])  # type: ignore[arg-type]


@pytest.mark.unit
class TestLoggingConfigEnv:
    """LoggingConfig reads env vars with THGENT_LOG_* prefix."""

    def test_env_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_LOG_* env vars override defaults (canonical upper-case values)."""
        monkeypatch.setenv("THGENT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("THGENT_LOG_FORMAT", "JSON")
        monkeypatch.setenv("THGENT_LOG_REDACT", "false")
        monkeypatch.setenv("THGENT_LOG_SINKS", "STDERR,STDOUT")
        cfg = LoggingConfig()
        assert cfg.level == "DEBUG"
        assert cfg.format == "JSON"
        assert cfg.redact is False
        assert cfg.sinks == ["STDERR", "STDOUT"]


@pytest.mark.unit
class TestConfigureLogging:
    """configure_logging wires a handler at the configured level."""

    def test_installs_stderr_handler_at_configured_level(
        self, stream: io.StringIO, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When sink=STDERR is configured, a stderr-bound handler is installed."""
        cfg = LoggingConfig(level="DEBUG", sinks=["STDERR"])
        with patch("sys.stderr", stream):
            configure_logging(cfg)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert any(
            isinstance(h, logging.StreamHandler) and h.stream is stream  # type: ignore[attr-defined]
            for h in root.handlers
        )

    def test_text_format_emits_human_readable(self, stream: io.StringIO) -> None:
        """TEXT format uses level/name/message template."""
        cfg = LoggingConfig(level="INFO", format="TEXT", sinks=["STDERR"])
        with patch("sys.stderr", stream):
            configure_logging(cfg)
        logging.getLogger("wl152.text").info("hello world")
        out = stream.getvalue()
        assert "hello world" in out
        assert "INFO" in out
        assert "wl152.text" in out

    def test_json_format_emits_parseable_json(self, stream: io.StringIO) -> None:
        """JSON format emits one JSON object per log line."""
        cfg = LoggingConfig(level="INFO", format="JSON", sinks=["STDERR"])
        with patch("sys.stderr", stream):
            configure_logging(cfg)
        logging.getLogger("wl152.json").info("structured hi")
        out = stream.getvalue().strip()
        record = json.loads(out)
        assert record["message"] == "structured hi"
        assert record["level"] == "INFO"
        assert record["name"] == "wl152.json"

    def test_configure_logging_default_uses_loggingconfig_defaults(
        self, stream: io.StringIO
    ) -> None:
        """configure_logging() with no arg uses LoggingConfig defaults."""
        with patch("sys.stderr", stream):
            configure_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO


@pytest.mark.unit
class TestSecretMaskingFormatter:
    """SecretMaskingFormatter masks registered secret values."""

    def test_mask_replaces_registered_value(self) -> None:
        """A registered secret value is replaced with ***SECRET***."""
        register_secret_for_masking("supersecret-token-xyz")
        fmt = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="token=supersecret-token-xyz used",
            args=(),
            exc_info=None,
        )
        assert fmt.format(record) == "token=***SECRET*** used"

    def test_no_mask_when_unregistered(self) -> None:
        """Unregistered substrings pass through unchanged."""
        fmt = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="nothing to redact here",
            args=(),
            exc_info=None,
        )
        assert fmt.format(record) == "nothing to redact here"

    def test_multiple_secrets_in_one_record(self) -> None:
        """Each registered secret is masked independently."""
        register_secret_for_masking("alpha-secret")
        register_secret_for_masking("beta-secret")
        fmt = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="a=alpha-secret b=beta-secret c=plain",
            args=(),
            exc_info=None,
        )
        assert fmt.format(record) == "a=***SECRET*** b=***SECRET*** c=plain"

    def test_remove_via_register_with_remove_flag(self) -> None:
        """register_secret_for_masking(value, _remove=True) unregisters."""
        register_secret_for_masking("one-shot")
        register_secret_for_masking("one-shot", _remove=True)
        fmt = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="x=one-shot",
            args=(),
            exc_info=None,
        )
        assert fmt.format(record) == "x=one-shot"

    def test_empty_registry_does_not_mask(self) -> None:
        """With no registered secrets, formatter is a pass-through."""
        fmt = SecretMaskingFormatter("%(message)s")
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="plain string",
            args=(),
            exc_info=None,
        )
        assert fmt.format(record) == "plain string"


@pytest.mark.unit
class TestConfigureLoggingIntegratesFormatter:
    """configure_logging wires SecretMaskingFormatter when redact=True."""

    def test_redact_true_writes_masking_formatter(self, stream: io.StringIO) -> None:
        """With redact=True, secrets in emitted records are masked."""
        register_secret_for_masking("leak-token-9")
        cfg = LoggingConfig(level="INFO", format="TEXT", redact=True, sinks=["STDERR"])
        with patch("sys.stderr", stream):
            configure_logging(cfg)
        logging.getLogger("wl152.redact").info("leak=leak-token-9 done")
        out = stream.getvalue()
        assert "leak=***SECRET*** done" in out
        assert "leak-token-9" not in out

    def test_redact_false_passes_through(self, stream: io.StringIO) -> None:
        """With redact=False, secrets pass through unredacted."""
        register_secret_for_masking("leak-token-9")
        cfg = LoggingConfig(level="INFO", format="TEXT", redact=False, sinks=["STDERR"])
        with patch("sys.stderr", stream):
            configure_logging(cfg)
        logging.getLogger("wl152.noredact").info("leak=leak-token-9 done")
        out = stream.getvalue()
        assert "leak-token-9" in out


@pytest.mark.unit
class TestThegentSettingsLoggingHook:
    """ThegentSettings exposes log_config and secret_fields()."""

    def test_log_config_field_is_loggingconfig_instance(self) -> None:
        """settings.log_config is a LoggingConfig with documented defaults."""
        s = ThegentSettings()
        assert isinstance(s.log_config, LoggingConfig)
        assert s.log_config.level == "INFO"
        assert s.log_config.format == "TEXT"
        assert s.log_config.redact is True

    def test_secret_fields_returns_canonical_six(self) -> None:
        """secret_fields() lists the documented sensitive field names."""
        s = ThegentSettings()
        names = s.secret_fields()
        assert isinstance(names, tuple)
        assert set(names) == {
            "supermemory_api_key",
            "redis_password",
            "cursor_api_token",
            "mcp_bearer_tokens",
            "reddit_client_secret",
            "linear_api_key",
        }

    def test_env_does_not_break_log_config_field(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Setting THGENT_LOG_* env vars is reflected on settings.log_config."""
        monkeypatch.setenv("THGENT_LOG_LEVEL", "WARNING")
        s = ThegentSettings()
        assert s.log_config.level == "WARNING"
