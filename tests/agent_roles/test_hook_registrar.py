"""Tests for HookRegistrar — writes AgentRoleSpec entries to hook-config.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml


def test_register_adds_to_hook_config(tmp_path: Path) -> None:
    """Test that register() adds spec to hook-config.yaml."""
    # @trace FR-AR-002
    from agent_roles.hook_registrar import HookRegistrar
    from agent_roles.spec import AgentRoleSpec

    config_path = tmp_path / "hook-config.yaml"
    config_path.write_text("hooks: []\n")

    spec = AgentRoleSpec(
        name="property_tester",
        display_name="Property-Based Tester",
        category="testers",
        trigger="PostToolUse:Write",
        description="Runs Hypothesis tests.",
        capabilities=["Generate tests", "Detect boundaries"],
        constraints=["Never modify source files"],
        tools_allowed=["Write", "Bash"],
        output_format="pytest_tests",
        fr_traces=["FR-QA-001"],
    )

    registrar = HookRegistrar(hook_config_path=config_path)
    registrar.register(spec)

    data = yaml.safe_load(config_path.read_text())
    hooks = data["hooks"]
    names = [h["name"] for h in hooks]
    assert "property_tester" in names
    hook = next(h for h in hooks if h["name"] == "property_tester")
    assert hook["event"] == "PostToolUse:Write"


def test_register_idempotent(tmp_path: Path) -> None:
    """Test that registering same spec twice does not duplicate entry."""
    # @trace FR-AR-002
    from agent_roles.hook_registrar import HookRegistrar
    from agent_roles.spec import AgentRoleSpec

    config_path = tmp_path / "hook-config.yaml"
    config_path.write_text("hooks: []\n")

    spec = AgentRoleSpec(
        name="doc_writer",
        display_name="Doc Writer",
        category="content",
        trigger="Stop",
        description="Writes docs.",
        capabilities=["Write docstrings", "Update README"],
        constraints=["Never change logic"],
        tools_allowed=["Read", "Edit"],
        output_format="markdown",
        fr_traces=["FR-DOC-001"],
    )
    registrar = HookRegistrar(hook_config_path=config_path)
    registrar.register(spec)
    registrar.register(spec)  # second call — no duplicate

    data = yaml.safe_load(config_path.read_text())
    assert len([h for h in data["hooks"] if h["name"] == "doc_writer"]) == 1
