"""WL-010 CLI parity tests for project brownfield command surfaces.

Focus: help/command presence parity across:
- thegent sys setup project
- thegent install project
- thegent update project
"""

from __future__ import annotations

import pytest
from typer import Typer
from typer.testing import CliRunner

from thegent.cli.apps.project import install_app, setup_project_app, update_app

BROWNFIELD_VARIANTS = ("brownfield", "ag-dd", "none")
PROJECT_SURFACES: tuple[tuple[str, Typer], ...] = (
    ("sys setup project", setup_project_app),
    ("install project", install_app),
    ("update project", update_app),
)


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    return CliRunner()


def _command_names(app: Typer) -> set[str]:
    return {cmd.name for cmd in app.registered_commands if cmd.name}


@pytest.mark.requirement("WL-010")
def test_brownfield_variants_present_across_setup_install_update_help(
    runner: CliRunner,
) -> None:
    for surface_name, surface_app in PROJECT_SURFACES:
        result = runner.invoke(surface_app, ["--help"])

        assert result.exit_code == 0, f"{surface_name} help failed: {result.stdout}"

        lowered = result.stdout.lower()
        for variant in BROWNFIELD_VARIANTS:
            assert variant in lowered, f"{surface_name} missing '{variant}' in --help output"


@pytest.mark.requirement("WL-010")
def test_brownfield_variants_registered_for_all_three_command_surfaces() -> None:
    for surface_name, surface_app in PROJECT_SURFACES:
        names = _command_names(surface_app)
        missing = set(BROWNFIELD_VARIANTS) - names
        assert not missing, f"{surface_name} missing variants: {sorted(missing)}"


@pytest.mark.requirement("WL-010")
@pytest.mark.parametrize("variant", BROWNFIELD_VARIANTS)
@pytest.mark.parametrize(("surface_name", "surface_app"), PROJECT_SURFACES)
def test_each_brownfield_variant_has_help_on_each_surface(
    runner: CliRunner,
    surface_name: str,
    surface_app: Typer,
    variant: str,
) -> None:
    result = runner.invoke(surface_app, [variant, "--help"])

    assert result.exit_code == 0, f"{surface_name} {variant} --help failed: {result.stdout}"
    assert variant in result.stdout.lower(), f"{surface_name} {variant} help omitted command name"
