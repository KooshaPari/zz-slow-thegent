"""Tests for thegent git identity resolution helpers."""

from pathlib import Path

import pytest

from thegent.cli.commands import cli_git_identity as identity


def test_infer_actor_profile_prefers_human_tokens() -> None:
    assert identity.infer_actor_profile("KooshPari") == "human"
    assert identity.infer_actor_profile("agent-codex-proxy") == "codex"
    assert identity.infer_actor_profile("default-agent") == "agent"


def test_resolve_author_env_supports_identity_map(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    profile_map = '{"codex": {"name": "Claude Bot", "email": "claude-bot@example.com"}, "agent": "Agent Fallback"}'
    monkeypatch.setattr(
        identity,
        "_git_config_get",
        lambda _project_root, key: {
            "user.name": "Base Name",
            "user.email": "base@example.com",
        }.get(key, ""),
    )
    monkeypatch.setenv("THGENT_GIT_IDENTITY_MAP", profile_map)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "from-git-env-name")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "from-git-env-email@example.com")
    resolved = identity.resolve_author_env(project_root=tmp_path, actor_profile="codex", agent_id="agent-codex")
    assert resolved["GIT_AUTHOR_NAME"] == "Claude Bot"
    assert resolved["GIT_AUTHOR_EMAIL"] == "claude-bot@example.com"
    assert resolved["GIT_COMMITTER_NAME"] == "Claude Bot"
    assert resolved["GIT_COMMITTER_EMAIL"] == "claude-bot@example.com"


def test_resolve_author_env_uses_non_human_suffix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in [
        "THGENT_GIT_IDENTITY_MAP",
        "THGENT_GIT_AUTHOR_NAME",
        "THGENT_GIT_AUTHOR_EMAIL",
        "THGENT_GIT_COMMITTER_NAME",
        "THGENT_GIT_COMMITTER_EMAIL",
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setattr(
        identity,
        "_git_config_get",
        lambda _project_root, key: {
            "user.name": "Koosha Paridehpour",
            "user.email": "koosh+thegent@example.com",
        }.get(key, ""),
    )
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Koosha Parikh")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "koosh+thegent@example.com")
    resolved = identity.resolve_author_env(project_root=tmp_path, actor_profile=None, agent_id="agent-claude")
    assert resolved["GIT_AUTHOR_NAME"] == "Koosha Paridehpour (claude)"
    assert resolved["GIT_AUTHOR_EMAIL"] == "koosh+thegent+claude@example.com"
    assert resolved["GIT_COMMITTER_NAME"] == "Koosha Paridehpour (claude)"
    assert resolved["GIT_COMMITTER_EMAIL"] == "koosh+thegent+claude@example.com"


def test_resolve_author_env_allows_direct_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        identity,
        "_git_config_get",
        lambda _project_root, key: {
            "user.name": "Koosha Parid",
            "user.email": "ignore@example.com",
        }.get(key, ""),
    )
    monkeypatch.setenv("GIT_AUTHOR_NAME", "ignore-me")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "ignore-me@example.com")
    monkeypatch.setenv("THGENT_GIT_AUTHOR_NAME", "override-name")
    monkeypatch.setenv("THGENT_GIT_COMMITTER_NAME", "override-committer-name")
    resolved = identity.resolve_author_env(project_root=tmp_path, actor_profile="human", agent_id="kooshapari")
    assert resolved["GIT_AUTHOR_NAME"] == "override-name"
    assert resolved["GIT_COMMITTER_NAME"] == "override-committer-name"
