"""Git author/committer identity helpers for thegent git wrappers."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

_NON_HUMAN_TOKENS = {
    "an-en",
    "anen",
    "antigravity",
    "antigravity-agent",
    "codex",
    "claude",
    "copilot",
    "droid",
    "fanta",
    "githubcopilot",
    "opencode",
    "robot",
    "thegent",
}

_HUMAN_TOKENS = {
    "human",
    "human-agent",
    "human-runner",
    "koosh",
    "kooshapari",
    "operator",
    "self",
    "user",
}


def normalize_actor_profile(value: str | None) -> str:
    """Normalize an actor/profile token to canonical key shape."""
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def infer_actor_profile(agent_id: str) -> str:
    """Infer actor profile from an agent id.

    Explicitly marks human-friendly identifiers and maps known model/agent aliases
    to dedicated profiles so commits cannot be attributed as another actor.
    """
    normalized = normalize_actor_profile(agent_id)
    if not normalized:
        return "human"

    if normalized in _HUMAN_TOKENS:
        return "human"
    if normalized in _NON_HUMAN_TOKENS:
        return normalized

    tokens = normalized.split("-")
    for token in tokens:
        if token in _HUMAN_TOKENS:
            return "human"
        if token in _NON_HUMAN_TOKENS:
            return token

    if normalized.startswith("agent"):
        return "agent"

    # Keep backwards-compatible identifier semantics: many agent ids are prefixed with
    # "agent-..." in this repo's orchestration.
    if normalized == "default-agent":
        return "agent"

    return "human"


def _git_config_get(project_root: Path, key: str) -> str:
    """Read git config key from the repository if possible."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "config",
                "--get",
                key,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except OSError as exc:
        raise RuntimeError(f"Unable to resolve git config for {key}: {exc}") from exc

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _build_actor_email(base_email: str, actor_profile: str) -> str:
    """Build an actor-specific noreply email while preserving the base domain."""
    if not base_email or "@" not in base_email:
        return f"thegent-{actor_profile}@users.noreply.github.com"

    local, _, domain = base_email.partition("@")
    return f"{local}+{actor_profile}@{domain}"


def _parse_profile_map(raw: str | None) -> dict[str, tuple[str, str]]:
    """Parse `THGENT_GIT_IDENTITY_MAP` JSON payload."""
    if not raw:
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid THGENT_GIT_IDENTITY_MAP JSON payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("THGENT_GIT_IDENTITY_MAP must be a JSON object")

    out: dict[str, tuple[str, str]] = {}
    for key, value in payload.items():
        profile = normalize_actor_profile(str(key))
        if not profile:
            continue

        if isinstance(value, str):
            out[profile] = (value.strip(), "")
            continue

        if not isinstance(value, dict):
            raise RuntimeError(f"Invalid profile payload for {profile}: expected string or object")

        name = str(value.get("name", "")).strip()
        email = str(value.get("email", "")).strip()
        out[profile] = (name, email)
    return out


def resolve_author_env(
    *,
    project_root: Path,
    actor_profile: str | None,
    agent_id: str,
) -> dict[str, str]:
    """Resolve git identity env for the requested actor profile and agent context.

    Profiles are read from `THGENT_GIT_IDENTITY_MAP`, then local git config.
    """
    profiles = _parse_profile_map(os.getenv("THGENT_GIT_IDENTITY_MAP"))
    selected_profile = normalize_actor_profile(actor_profile) or infer_actor_profile(agent_id)

    if not selected_profile:
        selected_profile = "human"

    config_name = _git_config_get(project_root, "user.name")
    config_email = _git_config_get(project_root, "user.email")

    base_name = config_name or os.getenv("GIT_AUTHOR_NAME", "").strip() or "thegent"
    base_email = config_email or os.getenv("GIT_AUTHOR_EMAIL", "").strip() or "noreply@thegent.dev"

    selected_name = ""
    selected_email = ""
    if selected_profile in profiles:
        selected_name, selected_email = profiles[selected_profile]

    if not selected_name and selected_profile == "human":
        selected_name = base_name
    elif not selected_name and selected_profile in _NON_HUMAN_TOKENS | {"agent"}:
        selected_name = f"{base_name} ({selected_profile})"

    if not selected_email:
        if selected_profile == "human":
            selected_email = base_email
        else:
            selected_email = _build_actor_email(base_email, selected_profile)

    # Explicit overrides for all modes can still be injected through env.
    selected_name = os.getenv("THGENT_GIT_AUTHOR_NAME", selected_name).strip()
    selected_email = os.getenv("THGENT_GIT_AUTHOR_EMAIL", selected_email).strip()
    selected_committer_name = os.getenv("THGENT_GIT_COMMITTER_NAME", selected_name).strip()
    selected_committer_email = os.getenv("THGENT_GIT_COMMITTER_EMAIL", selected_email).strip()

    if not selected_email:
        raise RuntimeError(f"Unable to resolve committer email for profile '{selected_profile}'.")

    return {
        "GIT_AUTHOR_NAME": selected_name,
        "GIT_AUTHOR_EMAIL": selected_email,
        "GIT_COMMITTER_NAME": selected_committer_name or selected_name,
        "GIT_COMMITTER_EMAIL": selected_committer_email or selected_email,
    }
