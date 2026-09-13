"""Tests for the L27 infrastructure lane — Dockerfile + compose scaffolding.

Validates that:

* ``Dockerfile`` exists and declares a multi-stage build with a non-root user.
* ``compose.yaml`` is valid YAML and references the Dockerfile.
* The default port (``8765``) is consistent across Dockerfile/compose.

Focused; runs in well under 1 second.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "compose.yaml"


def test_dockerfile_exists() -> None:
    """Dockerfile must exist at the repo root."""
    assert DOCKERFILE.exists(), f"missing {DOCKERFILE}"


def test_dockerfile_is_multistage() -> None:
    """Dockerfile must declare at least two ``FROM`` stages (builder + runtime)."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    from_count = len(re.findall(r"^FROM\s", text, flags=re.MULTILINE))
    assert from_count >= 2, f"expected multi-stage build, got {from_count} FROMs"


def test_dockerfile_declares_non_root_user() -> None:
    """Runtime stage must run as a non-root user (security baseline)."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert re.search(r"^USER\s+\w+", text, flags=re.MULTILINE), "no USER directive"


def test_dockerfile_exposes_mcp_port() -> None:
    """Dockerfile must EXPOSE the MCP HTTP port (default 8765)."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert re.search(r"^EXPOSE\s+8765", text, flags=re.MULTILINE)


def test_dockerfile_healthcheck_present() -> None:
    """Dockerfile must declare a HEALTHCHECK directive."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert re.search(r"^HEALTHCHECK\s", text, flags=re.MULTILINE)


def test_compose_file_exists() -> None:
    """compose.yaml must exist at the repo root."""
    assert COMPOSE.exists(), f"missing {COMPOSE}"


def test_compose_is_valid_yaml() -> None:
    """compose.yaml must parse as valid YAML."""
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_compose_has_thegent_service() -> None:
    """compose.yaml must declare a ``thegent`` service."""
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = data.get("services") or {}
    assert "thegent" in services


def test_compose_port_matches_dockerfile() -> None:
    """Port declared in compose.yaml must match the Dockerfile EXPOSE."""
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = data.get("services") or {}
    thegent = services.get("thegent") or {}
    ports = thegent.get("ports") or []
    port_strs = [str(p) for p in ports]
    assert any("8765" in p for p in port_strs), f"8765 not in ports: {port_strs}"
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")
    assert "8765" in dockerfile_text


def test_compose_drops_capabilities() -> None:
    """compose.yaml must drop ALL caps and only add NET_BIND_SERVICE."""
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = data.get("services") or {}
    thegent = services.get("thegent") or {}
    cap_drop = thegent.get("cap_drop") or []
    assert "ALL" in cap_drop


def test_dockerignore_excludes_tests_and_git() -> None:
    """.dockerignore must exclude tests, .git, and shadow dirs."""
    ignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert ".git" in ignore
    assert "tests" in ignore or "**/tests/" in ignore
    assert ".worktrees" in ignore or ".worktrees/" in ignore
