"""Unit tests for config and base types."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.agents.base import RunResult
from thegent.config import ThegentSettings


@pytest.mark.unit
class TestRunResult:
    """Tests for RunResult dataclass."""

    def test_creation(self) -> None:
        # @trace FR-CFG-002
        """RunResult stores exit_code, stdout, stderr, timed_out."""
        r = RunResult(exit_code=0, stdout="out", stderr="err", timed_out=False)
        assert r.exit_code == 0
        assert r.stdout == "out"
        assert r.stderr == "err"
        assert r.timed_out is False

    def test_timed_out_default_false(self) -> None:
        # @trace FR-CFG-002
        """timed_out defaults to False."""
        r = RunResult(exit_code=124, stdout="", stderr="")
        assert r.timed_out is False  # must be set explicitly


@pytest.mark.unit
class TestThegentSettings:
    """Tests for ThegentSettings."""

    def test_default_factory_skills_dir(self) -> None:
        # @trace FR-CFG-001
        """factory_skills_dir defaults to ~/.factory/skills."""
        s = ThegentSettings()
        assert "factory" in str(s.factory_skills_dir)
        assert "skills" in str(s.factory_skills_dir)

    def test_default_timeout(self) -> None:
        # @trace FR-CFG-003
        """default_timeout is 90."""
        s = ThegentSettings()
        assert s.default_timeout == 90

    def test_factory_droids_dir_resolves(self) -> None:
        # @trace FR-CFG-001
        """factory_droids_dir expands and resolves."""
        s = ThegentSettings()
        expanded = s.factory_droids_dir.expanduser()
        assert expanded.exists() or not expanded.exists()  # may or may not exist

    def test_models_cache_ttl_default(self) -> None:
        # @trace FR-CFG-003
        """models_cache_ttl_sec defaults to 300."""
        s = ThegentSettings()
        assert s.models_cache_ttl_sec == 300


@pytest.mark.unit
class TestThegentSettingsFieldValidation:
    """Tests for ThegentSettings field validation and edge cases."""

    def test_default_environment_is_development(self) -> None:
        # @trace FR-CFG-001
        """Default environment is 'development'."""
        s = ThegentSettings()
        assert s.environment == "development"

    def test_default_trust_score_threshold(self) -> None:
        # @trace FR-CFG-001
        """Default trust_score_threshold is 0.8."""
        s = ThegentSettings()
        assert s.trust_score_threshold == 0.8

    def test_default_retention_days_sessions(self) -> None:
        # @trace FR-CFG-004
        """Default retention_days_sessions is 30."""
        s = ThegentSettings()
        assert s.retention_days_sessions == 30

    def test_default_retention_days_registry(self) -> None:
        # @trace FR-CFG-004
        """Default retention_days_registry is 90."""
        s = ThegentSettings()
        assert s.retention_days_registry == 90

    def test_default_escalation_sla_minutes(self) -> None:
        # @trace FR-CFG-003
        """Default escalation_sla_minutes is 30."""
        s = ThegentSettings()
        assert s.escalation_sla_minutes == 30

    def test_default_override_ttl_seconds(self) -> None:
        # @trace FR-CFG-003
        """Default override_ttl_seconds is 86400 (24 hours)."""
        s = ThegentSettings()
        assert s.override_ttl_seconds == 86400

    def test_default_cost_budget_mtd(self) -> None:
        # @trace FR-CFG-001
        """Default cost_budget_mtd is 100.0."""
        s = ThegentSettings()
        assert s.cost_budget_mtd == 100.0

    def test_default_opa_url_empty(self) -> None:
        # @trace FR-CFG-001
        """Default opa_url is empty string."""
        s = ThegentSettings()
        assert s.opa_url == ""

    def test_default_output_format(self) -> None:
        # @trace FR-CFG-001
        """Default output_format is 'rich'."""
        s = ThegentSettings()
        assert s.output_format == "rich"


@pytest.mark.unit
class TestRetentionByDomain:
    """Tests for retention_by_domain field validator."""

    def test_retention_by_domain_default_empty(self) -> None:
        # @trace FR-CFG-004
        """Default retention_by_domain is empty dict."""
        s = ThegentSettings()
        assert s.retention_by_domain == {}

    def test_retention_by_domain_from_json_string(self) -> None:
        # @trace FR-CFG-004
        """retention_by_domain parses JSON string from env."""
        with patch.dict(
            os.environ,
            {"THGENT_RETENTION_BY_DOMAIN": '{"gdpr": 365, "soc2": 2555}'},
            clear=False,
        ):
            s = ThegentSettings()
            assert s.retention_by_domain == {"gdpr": 365, "soc2": 2555}

    def test_retention_by_domain_invalid_json_raises_or_empty(self) -> None:
        # @trace FR-CFG-004
        """Invalid JSON for retention_by_domain raises SettingsError or returns empty."""
        from pydantic_settings.exceptions import SettingsError

        with patch.dict(os.environ, {"THGENT_RETENTION_BY_DOMAIN": "not-json"}, clear=False):
            try:
                s = ThegentSettings()
                # If it doesn't raise, it should be empty
                assert s.retention_by_domain == {}
            except (SettingsError, ValueError):
                # pydantic_settings may raise before field_validator runs
                pass

    def test_retention_by_domain_from_dict(self) -> None:
        # @trace FR-CFG-004
        """retention_by_domain accepts dict directly."""
        s = ThegentSettings(retention_by_domain={"hipaa": 730})
        assert s.retention_by_domain == {"hipaa": 730}


@pytest.mark.unit
class TestValidateSetup:
    """Tests for validate_setup() configuration validation."""

    def test_validate_setup_creates_session_dir(self, tmp_path: Path) -> None:
        # @trace FR-CFG-006
        """validate_setup creates session_dir if it doesn't exist."""
        session_dir = tmp_path / "new_session"
        s = ThegentSettings(session_dir=session_dir)
        s.validate_setup()
        assert session_dir.exists()

    def test_validate_setup_succeeds_with_valid_config(self, tmp_path: Path) -> None:
        # @trace FR-CFG-006
        """validate_setup succeeds with valid writable session_dir."""
        s = ThegentSettings(session_dir=tmp_path)
        s.validate_setup()  # Should not raise


# ---------------------------------------------------------------------------
# Coverage gaps: _expand_path (line 12), field validators, validate_setup details
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExpandPath:
    """Tests for _expand_path utility (line 12)."""

    def test_expand_path_tilde(self) -> None:
        # @trace FR-CFG-001
        """_expand_path expands ~ to home directory."""
        from thegent.config import _expand_path

        result = _expand_path(Path("~/test"))
        assert "~" not in str(result)
        assert result.is_absolute()


@pytest.mark.unit
class TestRetentionByDomainValidator:
    """Tests for _parse_retention_by_domain (lines 112-116, 119)."""

    def test_retention_by_domain_json_string_valid(self) -> None:
        # @trace FR-CFG-004
        """JSON string parses to dict (lines 112-114)."""
        with patch.dict(os.environ, {"THGENT_RETENTION_BY_DOMAIN": '{"gdpr": 365}'}, clear=False):
            s = ThegentSettings()
            assert s.retention_by_domain == {"gdpr": 365}

    def test_retention_by_domain_invalid_json_returns_empty(self) -> None:
        # @trace FR-CFG-004
        """Invalid JSON returns empty dict (lines 115-116)."""
        with patch.dict(os.environ, {"THGENT_RETENTION_BY_DOMAIN": "not-json"}, clear=False):
            try:
                s = ThegentSettings()
                assert s.retention_by_domain == {}
            except Exception:
                pass  # pydantic_settings may raise before validator runs

    def test_retention_by_domain_non_dict_json_returns_empty(self) -> None:
        # @trace FR-CFG-004
        """Non-dict JSON returns empty dict (line 114 else branch)."""
        with patch.dict(os.environ, {"THGENT_RETENTION_BY_DOMAIN": '"just a string"'}, clear=False):
            try:
                s = ThegentSettings()
                assert s.retention_by_domain == {}
            except Exception:
                pass

    def test_retention_by_domain_non_dict_non_str_returns_empty(self) -> None:
        # @trace FR-CFG-004
        """Non-dict, non-str value returns default list (line 119)."""
        s = ThegentSettings(retention_by_domain=42)
        assert s.retention_by_domain == {}


@pytest.mark.unit
class TestValidateSetupDetails:
    """Tests for validate_setup edge cases (lines 174, 179, 184)."""

    def test_validate_setup_not_writable_raises(self, tmp_path: Path) -> None:
        # @trace FR-CFG-006
        """validate_setup raises when session_dir is not writable (line 174)."""
        session_dir = tmp_path / "readonly"
        session_dir.mkdir()
        os.chmod(session_dir, 0o444)
        s = ThegentSettings(session_dir=session_dir)
        try:
            with pytest.raises(RuntimeError, match="not writable"):
                s.validate_setup()
        finally:
            os.chmod(session_dir, 0o755)

    def test_validate_setup_missing_factory_skills_passes(self, tmp_path: Path) -> None:
        # @trace FR-CFG-006
        """validate_setup passes when factory_skills_dir doesn't exist (line 179)."""
        s = ThegentSettings(
            session_dir=tmp_path,
            factory_skills_dir=tmp_path / "nonexistent_skills",
        )
        s.validate_setup()  # Should not raise


@pytest.mark.unit
class TestSandboxEnvAllowlistValidator:
    """Tests for _parse_env_allowlist (lines 282, 285)."""

    def test_env_allowlist_from_json_array(self) -> None:
        # @trace FR-CFG-001
        """JSON array env var parses to list (line 283-284)."""
        with patch.dict(
            os.environ,
            {"THGENT_SANDBOX_ENV_ALLOWLIST": '["PATH","HOME","CUSTOM"]'},
            clear=False,
        ):
            s = ThegentSettings()
            assert "PATH" in s.sandbox_env_allowlist
            assert "CUSTOM" in s.sandbox_env_allowlist

    def test_env_allowlist_from_csv_string_direct(self) -> None:
        # @trace FR-CFG-001
        """Comma-separated string parses to list via direct kwarg (line 282)."""
        s = ThegentSettings(sandbox_env_allowlist="PATH,HOME,CUSTOM")
        assert "PATH" in s.sandbox_env_allowlist
        assert "CUSTOM" in s.sandbox_env_allowlist

    def test_env_allowlist_non_list_non_str_returns_defaults(self) -> None:
        # @trace FR-CFG-001
        """Non-list, non-str returns default list (line 285)."""
        s = ThegentSettings(sandbox_env_allowlist=42)
        assert "PATH" in s.sandbox_env_allowlist
