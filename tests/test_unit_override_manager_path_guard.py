"""Direct tests for ``OverrideManager`` path-traversal hardening.

Closes a P1 hardening gap flagged in the Phase 3/4 audit: while
``PolicyEngine.register_override`` validates ``rule_id`` shapes (see
``test_unit_policy_engine.TestRegisterOverridePathTraversalGuard``),
the underlying ``OverrideManager.apply_override`` interpolates
``policy_id`` directly into a filename
(``self.override_dir / f"{policy_id}.json"``) without any guard.
Direct callers of ``OverrideManager`` (CLI surfaces, test fixtures,
refactors) could write to ``../escape.json`` style paths.

These tests pin the contract:

* Rejection shapes: ``/``, ``\\``, ``..``, NUL byte, empty string,
  non-string types.
* Rejection happens **before** any file is written (no leak).
* ``get_override`` validates too — a rejected id returns ``None``
  rather than raising.
* ``cleanup_expired`` skips files with traversal-shaped names (defense
  in depth for legacy leftovers).
* Clean rule_ids with ``[A-Za-z0-9_.-]`` are accepted (negative
  control).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from thegent.config import ThegentSettings
from thegent.governance.overrides import (
    OverrideManager,
    PolicyOverridePathError,
    _validate_policy_id,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings(tmp_path):
    """Settings whose override_dir is rooted inside an isolated tmp_path."""
    settings = MagicMock(spec=ThegentSettings)
    settings.session_dir = tmp_path / "sessions"
    settings.session_dir.mkdir()
    return settings


@pytest.fixture
def manager(mock_settings) -> OverrideManager:
    return OverrideManager(settings=mock_settings)


# ---------------------------------------------------------------------------
# _validate_policy_id direct tests
# ---------------------------------------------------------------------------


class TestValidatePolicyIdUnit:
    """``_validate_policy_id`` is the single source of truth for the guard."""

    @pytest.mark.parametrize(
        "good_id",
        [
            "no-network-prod",
            "HIGH_RISK_RULE",
            "rule.with.dots",
            "a",
            "123",
            "x-y-z-1-2-3",
            "with_underscore_and-numbers-123",
        ],
    )
    def test_accepts_clean_rule_ids(self, good_id: str) -> None:
        """Negative control: clean ids are accepted without raising."""
        # Should not raise.
        _validate_policy_id(good_id)

    @pytest.mark.parametrize(
        ("bad_id", "expected_substr"),
        [
            ("", "non-empty"),
            ("/", "separator"),
            ("rule/with/slash", "separator"),
            ("rule\\backslash", "separator"),
            ("..", ".."),
            ("rule..with..dots", ".."),
            ("../escape", ".."),
            ("rule/with/../dots", "separator"),
            ("/etc/passwd", "separator"),
            ("a\x00b", "NUL"),
            ("rule\x00", "NUL"),
        ],
    )
    def test_rejects_traversal_shapes(self, bad_id: str, expected_substr: str) -> None:
        """Every traversal shape raises PolicyOverridePathError with a useful message."""
        with pytest.raises(PolicyOverridePathError) as exc_info:
            _validate_policy_id(bad_id)
        # Error message must mention the rejection reason so operators
        # can diagnose without reading source.
        assert expected_substr.lower() in str(exc_info.value).lower()

    def test_rejects_non_string(self) -> None:
        """A non-string ``policy_id`` is rejected (defense against config drift)."""
        with pytest.raises(PolicyOverridePathError) as exc_info:
            _validate_policy_id(123)  # type: ignore[arg-type]
        assert "string" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# apply_override integration tests
# ---------------------------------------------------------------------------


class TestOverrideManagerApplyGuard:
    """``OverrideManager.apply_override`` rejects traversal shapes pre-write."""

    def test_apply_override_rejects_forward_slash(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """``rule/with/slash`` is rejected and no override file is written."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("rule/with/slash", "reason", "sre", duration_minutes=1)
        # Defense-in-depth: even if apply_override somehow let it through,
        # ``_save_override`` would re-validate. But since apply_override
        # raises, no file should ever exist on disk.
        override_dir = mock_settings.session_dir / "overrides"
        assert list(override_dir.glob("*.json")) == []

    def test_apply_override_rejects_backslash(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """``rule\\backslash`` is rejected (Windows separator)."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("rule\\backslash", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_rejects_double_dot(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """A bare ``..`` substring is rejected."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("rule..with..dots", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_rejects_parent_traversal(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """A leading ``../foo`` parent-directory escape is rejected."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("../escape", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_rejects_absolute_path(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """``/etc/passwd`` style traversal is rejected."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("/etc/passwd", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_rejects_nul_byte(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """A NUL byte in ``policy_id`` is rejected (filesystem truncation guard)."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("a\x00b", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_rejects_empty_string(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """Empty ``policy_id`` is rejected — no file is written."""
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("", "reason", "sre", duration_minutes=1)
        assert list((mock_settings.session_dir / "overrides").glob("*.json")) == []

    def test_apply_override_accepts_clean_id_writes_file(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """Negative control: a clean rule_id succeeds and the file lands on disk."""
        manager.apply_override("clean-rule-id", "reason", "sre", duration_minutes=10)
        on_disk = mock_settings.session_dir / "overrides" / "clean-rule-id.json"
        assert on_disk.exists()
        # Round-trip works.
        loaded = manager.get_override("clean-rule-id")
        assert loaded is not None
        assert loaded.policy_id == "clean-rule-id"

    def test_apply_override_does_not_escape_override_dir(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """A rejected call never escapes the override directory.

        We simulate the most dangerous shape (``../etc`` would write
        outside ``override_dir``) and assert the parent dir has not
        gained any files outside ``overrides/``.
        """
        with pytest.raises(PolicyOverridePathError):
            manager.apply_override("../../etc/passwd", "reason", "sre", duration_minutes=1)
        # No files at all under session_dir that didn't exist before.
        for f in mock_settings.session_dir.rglob("*"):
            if f.is_file():
                # The only allowed file is whatever ``mock_settings`` itself
                # created — which is nothing in this fixture. Anything
                # under session_dir is a leaked override.
                pytest.fail(f"unexpected file leaked outside override_dir: {f}")


# ---------------------------------------------------------------------------
# get_override hardening
# ---------------------------------------------------------------------------


class TestOverrideManagerGetHardening:
    """``get_override`` validates too — a rejected id returns ``None``."""

    def test_get_override_rejects_traversal_shapes(
        self,
        manager: OverrideManager,
    ) -> None:
        """A traversal-shaped ``policy_id`` is treated as 'no override'."""
        # The manager should swallow the validation error and return None
        # so callers don't have to wrap every get_override in try/except.
        assert manager.get_override("rule/with/slash") is None
        assert manager.get_override("../escape") is None
        assert manager.get_override("..") is None
        assert manager.get_override("") is None

    def test_get_override_legitimate_miss_returns_none(
        self,
        manager: OverrideManager,
    ) -> None:
        """A clean id that simply has no override still returns ``None``."""
        assert manager.get_override("nonexistent-rule") is None


# ---------------------------------------------------------------------------
# cleanup_expired hardening (defense in depth)
# ---------------------------------------------------------------------------


class TestOverrideManagerCleanupHardening:
    """``cleanup_expired`` skips files whose names look like traversal shapes."""

    def test_cleanup_skips_traversal_named_files(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """A file named ``..json`` or ``../escape.json`` is skipped, not loaded."""
        override_dir = mock_settings.session_dir / "overrides"

        # Drop a fake file that *would* have escaped the override_dir had
        # the manager trusted its filename. ``glob('*.json')`` matches
        # the literal filename ``..json`` because it doesn't span
        # directories — but ``is_traversal_filename`` flags it.
        (override_dir / "..json").write_text("{}", encoding="utf-8")

        # cleanup_expired must NOT raise and must NOT delete the bad file.
        count = manager.cleanup_expired()
        # The bad file is skipped (not counted as a cleaned entry).
        assert count == 0
        assert (override_dir / "..json").exists()

    def test_cleanup_still_removes_normal_expired(
        self,
        manager: OverrideManager,
        mock_settings,
    ) -> None:
        """Negative control: a normal expired override IS removed."""
        manager.apply_override("EXPIRED_OK", "Test", "sre", duration_minutes=-1)
        before = list((mock_settings.session_dir / "overrides").glob("*.json"))
        assert any(f.name == "EXPIRED_OK.json" for f in before)

        count = manager.cleanup_expired()
        assert count == 1
        assert not (mock_settings.session_dir / "overrides" / "EXPIRED_OK.json").exists()


# ---------------------------------------------------------------------------
# Public-surface contract: PolicyEngine.register_override still works
# ---------------------------------------------------------------------------


class TestPolicyEngineRegisterOverrideStillRejects:
    """The public-API guard still fires after the manager-side hardening.

    These tests are a regression guard: the policy-engine-level guard
    in ``register_override`` (PolicyEngineConfigError) must continue to
    work even though the underlying manager now also raises its own
    ``PolicyOverridePathError`` for traversal shapes.
    """

    def test_engine_register_override_propagates_validation_error(
        self,
        tmp_path,
    ) -> None:
        """PolicyEngine.register_override wraps the manager's error.

        The policy_engine layer catches the manager-side rejection and
        surfaces it as a PolicyEngineConfigError so callers don't have
        to import two exception types.
        """
        from thegent.governance.policy_engine import (
            PolicyEngine,
            PolicyEngineConfigError,
        )

        settings = ThegentSettings(environment="development", session_dir=tmp_path)
        engine = PolicyEngine(settings=settings, use_federation=False)

        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "rule/with/slash",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
