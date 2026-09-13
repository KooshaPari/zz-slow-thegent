# tests/agent_roles/test_spec_renderer.py
# @trace FR-AR-001
from pathlib import Path


def test_spec_loads_from_yaml(tmp_path: Path) -> None:
    from agent_roles.spec import AgentRoleSpec

    yaml_content = """
name: property_tester
display_name: Property-Based Tester
category: testers
trigger: PostToolUse:Write
description: Generates property-based tests using Hypothesis.
capabilities:
  - Generate @given strategies from type signatures
  - Detect boundary values
constraints:
  - Never modify source files
tools_allowed:
  - Write
  - Bash
output_format: pytest_tests
fr_traces:
  - FR-QA-001
"""
    path = tmp_path / "property_tester.yaml"
    path.write_text(yaml_content)
    spec = AgentRoleSpec.from_yaml(path)
    assert spec.name == "property_tester"
    assert spec.category == "testers"
    assert "FR-QA-001" in spec.fr_traces


def test_renderer_produces_valid_md(tmp_path: Path) -> None:
    from agent_roles.renderer import RoleRenderer
    from agent_roles.spec import AgentRoleSpec

    spec = AgentRoleSpec(
        name="mutation_tester",
        display_name="Mutation Tester",
        category="testers",
        trigger="Stop",
        description="Runs mutmut mutation testing on changed files.",
        capabilities=["Run mutmut on src/", "Report surviving mutants"],
        constraints=["Read-only except test writes"],
        tools_allowed=["Bash", "Read"],
        output_format="mutation_report",
        fr_traces=["FR-QA-002"],
    )
    renderer = RoleRenderer(agents_dir=tmp_path)
    path = renderer.render(spec)
    assert path.exists()
    content = path.read_text()
    assert "---" in content
    assert "Mutation Tester" in content
    assert "mutmut" in content
    assert "FR-QA-002" in content


def test_renderer_output_path(tmp_path: Path) -> None:
    from agent_roles.renderer import RoleRenderer
    from agent_roles.spec import AgentRoleSpec

    spec = AgentRoleSpec(
        name="doc_writer",
        display_name="Doc Writer",
        category="content",
        trigger="Stop",
        description="Writes docs.",
        capabilities=["Write docs", "Update README"],
        constraints=["Never change logic"],
        tools_allowed=["Read", "Edit"],
        output_format="markdown",
        fr_traces=["FR-DOC-001"],
    )
    renderer = RoleRenderer(agents_dir=tmp_path)
    path = renderer.render(spec)
    assert path.name == "doc_writer.md"
