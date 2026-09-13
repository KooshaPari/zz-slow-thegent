"""L21 secrets handling — pydantic.SecretStr promotion + audit hook.

Pins the canonical ``ThegentSettings`` secrets surface so that:

* The six canonical ``SECRET_FIELDS`` are now ``pydantic.SecretStr`` instances
  (or ``SecretStr | None`` for the two nullable ones).
* ``repr`` and ``str`` of any of these fields mask the underlying value.
* ``.get_secret_value()`` returns the underlying plain string.
* ``ThegentSettings.secret_value(name)`` is the canonical audit-friendly
  accessor for downstream consumers (it returns the plain string, or
  ``None`` for unset nullable fields).
* Constructors accept plain ``str`` (auto-coerced) and ``None``.
* Env vars (``THGENT_SUPERMEMORY_API_KEY`` etc.) round-trip while keeping
  repr/str masked.

Traces:
* L21 — secrets handling hardening
* L20 — config hardening (companion to WL152's LoggingConfig + masking)
"""

from __future__ import annotations

import os
from typing import get_type_hints

import pytest
from pydantic import SecretStr

from thegent.config import ThegentSettings

# ---------------------------------------------------------------------------
# Canonical six (audit pin — must match WL152's SECRET_FIELDS surface)
# ---------------------------------------------------------------------------


CANONICAL_SECRETS: tuple[str, ...] = (
    "supermemory_api_key",
    "redis_password",
    "cursor_api_token",
    "mcp_bearer_tokens",
    "reddit_client_secret",
    "linear_api_key",
)

NULLABLE_SECRETS: frozenset[str] = frozenset(
    {"supermemory_api_key", "redis_password"},
)


# ---------------------------------------------------------------------------
# Field-type pinning
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecretFieldTypes:
    """Every SECRET_FIELDS attribute is SecretStr-typed at the field level."""

    def test_secret_fields_tuple_is_canonical_six(self) -> None:
        settings = ThegentSettings()
        assert settings.SECRET_FIELDS == CANONICAL_SECRETS

    def test_secret_fields_returns_canonical_six(self) -> None:
        settings = ThegentSettings()
        assert settings.secret_fields() == CANONICAL_SECRETS

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_secret_field_is_secretstr_instance_or_none(self, name: str) -> None:
        settings = ThegentSettings()
        value = getattr(settings, name)
        # Nullable secrets default to None; non-nullable to SecretStr("").
        if name in NULLABLE_SECRETS:
            assert value is None or isinstance(value, SecretStr), (
                f"{name} must be None or SecretStr, got {type(value).__name__}"
            )
        else:
            assert isinstance(value, SecretStr), (
                f"{name} must be a SecretStr instance, got {type(value).__name__}"
            )

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_secret_field_declared_type_is_secretstr(self, name: str) -> None:
        """Static annotation must reference SecretStr (or SecretStr | None)."""
        hints = get_type_hints(ThegentSettings)
        annotation = hints[name]
        annotation_str = str(annotation)
        assert "SecretStr" in annotation_str, (
            f"{name} annotation must reference SecretStr; got {annotation}"
        )

    def test_nullable_secrets_annotation_accepts_none(self) -> None:
        """The two nullable secrets must declare Optional/SecretStr | None."""
        hints = get_type_hints(ThegentSettings)
        for name in NULLABLE_SECRETS:
            annotation_str = str(hints[name])
            assert "None" in annotation_str, (
                f"{name} must allow None; got annotation {annotation_str}"
            )

    def test_non_nullable_secrets_default_to_secretstr(self) -> None:
        """The four non-nullable secrets default to an empty SecretStr, not None."""
        non_nullable = frozenset(CANONICAL_SECRETS) - NULLABLE_SECRETS
        for name in non_nullable:
            settings = ThegentSettings()
            value = getattr(settings, name)
            assert isinstance(value, SecretStr)
            assert value.get_secret_value() == ""


# ---------------------------------------------------------------------------
# Masking semantics — repr / str hide the secret value
# ---------------------------------------------------------------------------


NON_EMPTY_SECRET = "this-is-a-secret-value-do-not-leak-9c2f"
ANOTHER_SECRET = "another-secret-with-marker-XYZ"


@pytest.fixture
def populated_settings() -> ThegentSettings:
    """Construct a settings instance with non-empty secret values."""
    return ThegentSettings(
        supermemory_api_key=NON_EMPTY_SECRET,
        redis_password=NON_EMPTY_SECRET,
        cursor_api_token=NON_EMPTY_SECRET,
        mcp_bearer_tokens=NON_EMPTY_SECRET,
        reddit_client_secret=NON_EMPTY_SECRET,
        linear_api_key=ANOTHER_SECRET,
    )


@pytest.mark.unit
class TestSecretMaskingSemantics:
    """repr/str of any SECRET_FIELDS must NOT leak the underlying value."""

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_repr_masks_secret(
        self, populated_settings: ThegentSettings, name: str
    ) -> None:
        secret_obj = getattr(populated_settings, name)
        rendered = repr(secret_obj)
        assert NON_EMPTY_SECRET not in rendered
        assert ANOTHER_SECRET not in rendered

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_str_masks_secret(
        self, populated_settings: ThegentSettings, name: str
    ) -> None:
        secret_obj = getattr(populated_settings, name)
        rendered = str(secret_obj)
        assert NON_EMPTY_SECRET not in rendered
        assert ANOTHER_SECRET not in rendered

    def test_settings_repr_does_not_leak_secrets(
        self,
        populated_settings: ThegentSettings,
    ) -> None:
        """The full settings repr must not include raw secret material."""
        rendered = repr(populated_settings)
        assert NON_EMPTY_SECRET not in rendered
        assert ANOTHER_SECRET not in rendered

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_get_secret_value_returns_raw_value(
        self,
        populated_settings: ThegentSettings,
        name: str,
    ) -> None:
        secret_obj = getattr(populated_settings, name)
        assert isinstance(secret_obj, SecretStr)
        # linear_api_key was assigned ANOTHER_SECRET in the fixture.
        expected = ANOTHER_SECRET if name == "linear_api_key" else NON_EMPTY_SECRET
        assert secret_obj.get_secret_value() == expected


# ---------------------------------------------------------------------------
# Constructor round-trips
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecretConstructorAcceptance:
    """Constructors must accept plain str (auto-coerce) and None."""

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_constructor_accepts_plain_str(self, name: str) -> None:
        kwargs = (
            {name: NON_EMPTY_SECRET}
            if name not in NULLABLE_SECRETS
            else {
                name: NON_EMPTY_SECRET,
            }
        )
        settings = ThegentSettings(**kwargs)
        assert isinstance(getattr(settings, name), SecretStr)
        assert getattr(settings, name).get_secret_value() == NON_EMPTY_SECRET

    @pytest.mark.parametrize("name", NULLABLE_SECRETS)
    def test_constructor_accepts_none_for_nullable(self, name: str) -> None:
        settings = ThegentSettings(**{name: None})
        assert getattr(settings, name) is None

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_constructor_accepts_secretstr_directly(self, name: str) -> None:
        settings = ThegentSettings(**{name: SecretStr(NON_EMPTY_SECRET)})
        assert getattr(settings, name).get_secret_value() == NON_EMPTY_SECRET

    def test_empty_string_constructor_becomes_empty_secretstr(self) -> None:
        settings = ThegentSettings(cursor_api_token="")
        assert isinstance(settings.cursor_api_token, SecretStr)
        assert settings.cursor_api_token.get_secret_value() == ""
        assert bool(settings.cursor_api_token) is False


# ---------------------------------------------------------------------------
# Env var round-trip — masking preserved across env bootstrap
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecretEnvRoundTrip:
    """Env vars populate SECRET_FIELDS while keeping repr/str masked."""

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_env_var_populates_secret(
        self,
        monkeypatch: pytest.MonkeyPatch,
        name: str,
    ) -> None:
        env_name = "THGENT_" + name.upper()
        # Nullable fields accept empty string from env too — empty is masked.
        monkeypatch.setenv(env_name, NON_EMPTY_SECRET)
        settings = ThegentSettings()
        secret_obj = getattr(settings, name)
        # For nullable fields with empty default, get_secret_value must work
        # regardless of underlying representation.
        if isinstance(secret_obj, SecretStr):
            assert secret_obj.get_secret_value() == NON_EMPTY_SECRET
            assert NON_EMPTY_SECRET not in repr(secret_obj)
            assert NON_EMPTY_SECRET not in str(secret_obj)
        else:
            # nullable + not provided via env should still be None
            assert secret_obj is None

    def test_env_unset_nullable_secret_stays_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        monkeypatch.delenv("THGENT_REDIS_PASSWORD", raising=False)
        settings = ThegentSettings()
        assert settings.supermemory_api_key is None
        assert settings.redis_password is None


# ---------------------------------------------------------------------------
# Model serialization — model_dump / model_dump_json must mask secrets
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecretSerialization:
    """model_dump / model_dump_json mask SecretStr fields by default."""

    def test_model_dump_masks_secrets(
        self, populated_settings: ThegentSettings
    ) -> None:
        dumped = populated_settings.model_dump()
        for name in CANONICAL_SECRETS:
            dumped_value = dumped[name]
            # Nullable secrets set via constructor are SecretStr instances;
            # they must be present and masked in the dump.
            assert isinstance(dumped_value, SecretStr), (
                f"{name} should serialize as SecretStr, got {type(dumped_value).__name__}"
            )
            # In the populated fixture, supermemory_api_key etc. hold
            # NON_EMPTY_SECRET and linear_api_key holds ANOTHER_SECRET.
            expected = ANOTHER_SECRET if name == "linear_api_key" else NON_EMPTY_SECRET
            assert dumped_value.get_secret_value() == expected
            assert expected not in repr(dumped_value)
            assert expected not in str(dumped_value)

    def test_model_dump_json_masks_secrets(
        self, populated_settings: ThegentSettings
    ) -> None:
        rendered = populated_settings.model_dump_json()
        assert NON_EMPTY_SECRET not in rendered
        assert ANOTHER_SECRET not in rendered


# ---------------------------------------------------------------------------
# Audit hook — secret_value(name) is the canonical consumer accessor
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecretValueAuditHook:
    """ThegentSettings.secret_value(name) is the canonical accessor."""

    @pytest.mark.parametrize("name", CANONICAL_SECRETS)
    def test_secret_value_returns_raw_value(
        self,
        populated_settings: ThegentSettings,
        name: str,
    ) -> None:
        expected = ANOTHER_SECRET if name == "linear_api_key" else NON_EMPTY_SECRET
        assert populated_settings.secret_value(name) == expected

    def test_secret_value_for_unset_nullable_is_none(self) -> None:
        # Ensure no env pollution.
        for name in CANONICAL_SECRETS:
            os.environ.pop("THGENT_" + name.upper(), None)
        settings = ThegentSettings()
        assert settings.secret_value("supermemory_api_key") is None
        assert settings.secret_value("redis_password") is None

    def test_secret_value_for_unset_non_nullable_is_empty_string(self) -> None:
        for name in CANONICAL_SECRETS:
            os.environ.pop("THGENT_" + name.upper(), None)
        settings = ThegentSettings()
        assert settings.secret_value("cursor_api_token") == ""
        assert settings.secret_value("linear_api_key") == ""

    def test_secret_value_unknown_field_raises(self) -> None:
        settings = ThegentSettings()
        with pytest.raises(KeyError):
            settings.secret_value("definitely_not_a_secret_field")

    def test_secret_value_empty_default_round_trip(self) -> None:
        settings = ThegentSettings()
        assert settings.secret_value("cursor_api_token") == ""

    def test_secret_value_does_not_leak_via_repr_or_str(
        self,
        populated_settings: ThegentSettings,
    ) -> None:
        """secret_value() returns the raw value — repr/str of the SecretStr still mask."""
        for name in CANONICAL_SECRETS:
            raw = populated_settings.secret_value(name)
            secret_obj = getattr(populated_settings, name)
            assert raw not in repr(secret_obj)
            assert raw not in str(secret_obj)
