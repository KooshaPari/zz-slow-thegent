"""Tests for WL-263 credential source validator."""

from __future__ import annotations

import pytest

from thegent.integrations.credential_source_validator import (
    CredentialSources,
    resolve_credential_source,
)


@pytest.mark.requirement("WL-263")
def test_resolve_credential_source_with_env_only() -> None:
    source = resolve_credential_source(CredentialSources(env_token="abc"))
    assert source == "env"


@pytest.mark.requirement("WL-263")
def test_resolve_credential_source_rejects_ambiguous_sources() -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_credential_source(CredentialSources(env_token="abc", config_token_path="/tmp/tok"))
