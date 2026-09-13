"""Integration tests for agent_roles end-to-end flow. @trace FR-AGT-050"""

import pytest

from agent_roles.hook_registrar import HookRegistrar
from agent_roles.renderer import RoleRenderer
from agent_roles.spec import AgentRoleSpec


@pytest.fixture
def sample_spec():
    """Create a sample AgentRoleSpec for testing."""
    return AgentRoleSpec(
        name="integration-tester",
        display_name="Integration Tester",
        category="testers",
        trigger="post-test",
        description="Integration test agent role.",
        capabilities=["write integration tests", "verify end-to-end flows"],
        constraints=["no mocking in integration tests"],
        tools_allowed=["pytest", "httpx"],
        output_format="markdown",
        fr_traces=["FR-AGT-050"],
    )


def test_render_creates_file(tmp_path, sample_spec):
    """RoleRenderer writes agents/<name>.md with correct content."""
    renderer = RoleRenderer(tmp_path)
    out = renderer.render(sample_spec)
    assert out.exists()
    content = out.read_text()
    assert "integration-tester" in content
    assert "Integration Tester" in content
    assert "write integration tests" in content


def test_render_file_path(tmp_path, sample_spec):
    """RoleRenderer outputs file with correct name and location."""
    renderer = RoleRenderer(tmp_path)
    out = renderer.render(sample_spec)
    assert out.name == "integration-tester.md"
    assert out.parent == tmp_path


def test_hook_registrar_creates_file(tmp_path, sample_spec):
    """HookRegistrar creates hook-config.yaml if it doesn't exist."""
    config = tmp_path / "hook-config.yaml"
    config.write_text("hooks: []\n")
    registrar = HookRegistrar(config)
    registrar.register(sample_spec)
    assert config.exists()
    content = config.read_text()
    assert "integration-tester" in content


def test_hook_registrar_idempotent(tmp_path, sample_spec):
    """HookRegistrar is idempotent on second call."""
    config = tmp_path / "hook-config.yaml"
    config.write_text("hooks: []\n")
    registrar = HookRegistrar(config)
    registrar.register(sample_spec)
    registrar.register(sample_spec)
    content = config.read_text()
    # Should have exactly one entry with name: integration-tester
    assert content.count("name: integration-tester") == 1


def test_full_pipeline(tmp_path, sample_spec):
    """Full pipeline: spec → render → register hook."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    hook_config = tmp_path / "hook-config.yaml"
    hook_config.write_text("hooks: []\n")

    renderer = RoleRenderer(agents_dir)
    registrar = HookRegistrar(hook_config)

    out = renderer.render(sample_spec)
    registrar.register(sample_spec)

    assert out.exists()
    assert hook_config.exists()
    content = hook_config.read_text()
    assert "integration-tester" in content
    assert sample_spec.trigger in content


def test_all_library_yamls_load():
    """All 20 library YAML files load as valid AgentRoleSpec objects."""
    from agent_roles.cli import _all_yaml_files

    files = list(_all_yaml_files())
    assert len(files) == 20, f"Expected 20 YAML files, got {len(files)}"

    for f in files:
        spec = AgentRoleSpec.from_yaml(f)
        assert spec.name
        assert spec.display_name
        assert spec.category in ("testers", "content", "infrastructure", "core")
        assert spec.description
        assert spec.capabilities
        assert spec.constraints
        assert spec.tools_allowed
        assert spec.output_format
        assert spec.fr_traces


def test_render_includes_frontmatter(tmp_path, sample_spec):
    """Rendered markdown includes YAML frontmatter with all fields."""
    renderer = RoleRenderer(tmp_path)
    out = renderer.render(sample_spec)
    content = out.read_text()

    assert "---" in content
    assert "name: integration-tester" in content
    assert "display_name: Integration Tester" in content
    assert "category: testers" in content
    assert "trigger: post-test" in content
    assert "output_format: markdown" in content
    assert "fr_traces:" in content


def test_render_includes_sections(tmp_path, sample_spec):
    """Rendered markdown includes all required sections."""
    renderer = RoleRenderer(tmp_path)
    out = renderer.render(sample_spec)
    content = out.read_text()

    assert "## Capabilities" in content
    assert "## Constraints" in content
    assert "## Allowed Tools" in content


def test_render_formats_lists(tmp_path, sample_spec):
    """Rendered markdown formats lists with bullet points."""
    renderer = RoleRenderer(tmp_path)
    out = renderer.render(sample_spec)
    content = out.read_text()

    assert "- write integration tests" in content
    assert "- no mocking in integration tests" in content
    assert "- `pytest`" in content
    assert "- `httpx`" in content


def test_hook_registrar_preserves_existing_hooks(tmp_path, sample_spec):
    """HookRegistrar preserves existing hooks when adding new one."""
    config = tmp_path / "hook-config.yaml"
    config.write_text("hooks:\n  - name: existing\n    event: pre-test\n")

    registrar = HookRegistrar(config)
    registrar.register(sample_spec)

    content = config.read_text()
    assert "existing" in content
    assert "integration-tester" in content


def test_hook_registrar_includes_script_path(tmp_path, sample_spec):
    """HookRegistrar includes script path in registration."""
    config = tmp_path / "hook-config.yaml"
    config.write_text("hooks: []\n")

    registrar = HookRegistrar(config)
    registrar.register(sample_spec)

    content = config.read_text()
    assert f"hooks/role-{sample_spec.name}.sh" in content
