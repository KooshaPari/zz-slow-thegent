"""Unit and integration tests for WL-010: First-class project tenancy commands.

# @trace FR-TEN-001
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json
import pytest
from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A temporary directory that acts as a project root."""
    proj = tmp_path / "my-project"
    proj.mkdir()
    return proj


@pytest.fixture
def tmp_registry(tmp_path: Path) -> Path:
    """A temporary registry JSON path (does not need to exist yet)."""
    return tmp_path / "registry.json"


@pytest.fixture
def tenancy(tmp_registry: Path):  # noqa: ANN201 -- pytest fixture
    from thegent.infra.project_tenancy import ProjectTenancy

    return ProjectTenancy(registry_path=tmp_registry)


# ---------------------------------------------------------------------------
# ProjectTenancy data model tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-TEN-001")
class TestTenancyProjectModel:
    """Tests for TenancyProject pydantic model."""

    def test_model_fields_required(self) -> None:
        from thegent.infra.project_tenancy import TenancyProject

        record = TenancyProject(
            project_id="abc123",
            name="test",
            tenant_id="test",
            path="/tmp/test",
            template="none",
            template_version="1.0.0",
            created_at="2026-02-20T00:00:00+00:00",
            updated_at="2026-02-20T00:00:00+00:00",
        )
        assert record.project_id == "abc123"
        assert record.name == "test"
        assert record.tenant_id == "test"

    def test_model_rejects_extra_fields(self) -> None:
        from pydantic import ValidationError

        from thegent.infra.project_tenancy import TenancyProject

        with pytest.raises(ValidationError):
            TenancyProject(  # type: ignore[call-arg]
                project_id="x",
                name="x",
                tenant_id="x",
                path="/tmp",
                template="none",
                template_version="1.0.0",
                created_at="now",
                updated_at="now",
                unexpected_field="boom",
            )

    def test_model_frozen(self) -> None:
        from thegent.infra.project_tenancy import TenancyProject

        record = TenancyProject(
            project_id="abc123",
            name="test",
            tenant_id="test",
            path="/tmp/test",
            template="none",
            template_version="1.0.0",
            created_at="2026-02-20T00:00:00+00:00",
            updated_at="2026-02-20T00:00:00+00:00",
        )
        with pytest.raises(Exception):
            record.name = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ProjectTenancy registry CRUD tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-TEN-001")
class TestProjectTenancyRegistry:
    """Tests for ProjectTenancy registry read/write/lookup."""

    def test_init_project_creates_record(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        record = tenancy.init_project(
            name="alpha",
            tenant_id="alpha",
            path=tmp_project,
            template="none",
        )
        assert record.name == "alpha"
        assert record.tenant_id == "alpha"
        assert record.path == str(tmp_project)
        assert tmp_registry.exists()

    def test_init_project_persists(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.infra.project_tenancy import ProjectTenancy

        tenancy.init_project(
            name="persist-me",
            tenant_id="persist-me",
            path=tmp_project,
            template="none",
        )
        tenancy2 = ProjectTenancy(registry_path=tmp_registry)
        projects = tenancy2.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "persist-me"

    def test_list_projects_empty(self, tenancy) -> None:
        projects = tenancy.list_projects()
        assert projects == []

    def test_list_projects_multiple(self, tenancy, tmp_path: Path) -> None:
        for i in range(3):
            p = tmp_path / f"proj{i}"
            p.mkdir()
            tenancy.init_project(
                name=f"project-{i}",
                tenant_id=f"tenant-{i}",
                path=p,
                template="none",
            )
        projects = tenancy.list_projects()
        assert len(projects) == 3

    def test_get_project_by_name(self, tenancy, tmp_project: Path) -> None:
        tenancy.init_project(
            name="findme",
            tenant_id="findme",
            path=tmp_project,
            template="none",
        )
        record = tenancy.get_project(name="findme")
        assert record is not None
        assert record.name == "findme"

    def test_get_project_by_tenant_id(self, tenancy, tmp_project: Path) -> None:
        tenancy.init_project(
            name="t-project",
            tenant_id="my-tenant",
            path=tmp_project,
            template="none",
        )
        record = tenancy.get_project(tenant_id="my-tenant")
        assert record is not None
        assert record.tenant_id == "my-tenant"

    def test_get_project_by_path(self, tenancy, tmp_project: Path) -> None:
        tenancy.init_project(
            name="path-proj",
            tenant_id="path-proj",
            path=tmp_project,
            template="none",
        )
        record = tenancy.get_project(path=tmp_project)
        assert record is not None
        assert record.path == str(tmp_project)

    def test_get_project_not_found_returns_none(self, tenancy) -> None:
        record = tenancy.get_project(name="nonexistent")
        assert record is None

    def test_get_project_no_selector_raises(self, tenancy) -> None:
        with pytest.raises(ValueError, match="At least one selector"):
            tenancy.get_project()

    def test_duplicate_name_and_tenant_raises(self, tenancy, tmp_project: Path, tmp_path: Path) -> None:
        tenancy.init_project(
            name="dup",
            tenant_id="dup",
            path=tmp_project,
            template="none",
        )
        other = tmp_path / "other"
        other.mkdir()
        with pytest.raises(ValueError, match="conflict"):
            tenancy.init_project(
                name="dup",
                tenant_id="dup",
                path=other,
                template="none",
            )

    def test_duplicate_path_raises(self, tenancy, tmp_project: Path) -> None:
        tenancy.init_project(
            name="first",
            tenant_id="first",
            path=tmp_project,
            template="none",
        )
        with pytest.raises(ValueError, match="conflict"):
            tenancy.init_project(
                name="second",
                tenant_id="second",
                path=tmp_project,
                template="none",
            )

    def test_sync_project_updates_template_metadata(self, tenancy, tmp_project: Path) -> None:
        tenancy.init_project(
            name="sync-me",
            tenant_id="sync-me",
            path=tmp_project,
            template="none",
            template_version="1.0.0",
        )

        updated = tenancy.sync_project(
            path=tmp_project,
            template="ag-dd",
            template_version="2.0.0",
        )

        assert updated.template == "ag-dd"
        assert updated.template_version == "2.0.0"
        refreshed = tenancy.get_project(path=tmp_project)
        assert refreshed is not None
        assert refreshed.template == "ag-dd"
        assert refreshed.template_version == "2.0.0"

    def test_missing_path_raises(self, tenancy) -> None:
        with pytest.raises(FileNotFoundError):
            tenancy.init_project(
                name="ghost",
                tenant_id="ghost",
                path="/nonexistent/path/does/not/exist",
                template="none",
            )


# ---------------------------------------------------------------------------
# AG-DD template spawning
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-TEN-001")
class TestSpawnTemplateAgdd:
    """Tests for AG-DD template materialization."""

    def _mock_template_root(self, tmp_path: Path) -> Path:
        """Build a minimal fake ag-dd template tree."""
        tmpl = tmp_path / "ag-dd"
        tmpl.mkdir()
        (tmpl / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
        (tmpl / "PLAN.md").write_text("# PLAN\n", encoding="utf-8")
        sub = tmpl / "docs"
        sub.mkdir()
        (sub / "WORK_STREAM.md").write_text("# WORK_STREAM\n", encoding="utf-8")
        return tmpl

    def test_spawn_installs_new_files(self, tenancy, tmp_project: Path, tmp_path: Path, monkeypatch) -> None:
        template_root = self._mock_template_root(tmp_path)
        monkeypatch.setattr(tenancy, "_template_root", lambda: template_root)

        tenancy.init_project(
            name="agdd-test",
            tenant_id="agdd-test",
            path=tmp_project,
            template="ag-dd",
        )
        result = tenancy.spawn_template_agdd(tmp_project, mode="smart")
        assert "AGENTS.md" in result.installed or "AGENTS.md" in result.unchanged

    def test_spawn_skip_mode_reports_conflicts(self, tenancy, tmp_project: Path, tmp_path: Path, monkeypatch) -> None:
        template_root = self._mock_template_root(tmp_path)
        monkeypatch.setattr(tenancy, "_template_root", lambda: template_root)

        tenancy.init_project(
            name="skip-test",
            tenant_id="skip-test",
            path=tmp_project,
            template="ag-dd",
        )
        # Pre-create a conflicting file
        existing = tmp_project / "AGENTS.md"
        existing.write_text("# DIFFERENT CONTENT\n", encoding="utf-8")

        result = tenancy.spawn_template_agdd(tmp_project, mode="skip")
        assert "AGENTS.md" in result.conflicts

    def test_spawn_overwrite_mode_replaces_files(self, tenancy, tmp_project: Path, tmp_path: Path, monkeypatch) -> None:
        template_root = self._mock_template_root(tmp_path)
        monkeypatch.setattr(tenancy, "_template_root", lambda: template_root)

        tenancy.init_project(
            name="ow-test",
            tenant_id="ow-test",
            path=tmp_project,
            template="ag-dd",
        )
        existing = tmp_project / "AGENTS.md"
        existing.write_text("# OLD\n", encoding="utf-8")

        result = tenancy.spawn_template_agdd(tmp_project, mode="overwrite")
        assert "AGENTS.md" in result.overwritten
        assert existing.read_text(encoding="utf-8") == "# AGENTS\n"

    def test_spawn_invalid_mode_raises(self, tenancy, tmp_project: Path) -> None:
        with pytest.raises(ValueError, match="mode must be one of"):
            tenancy.spawn_template_agdd(tmp_project, mode="invalid")  # type: ignore[arg-type]

    def test_spawn_missing_path_raises(self, tenancy) -> None:
        with pytest.raises(FileNotFoundError):
            tenancy.spawn_template_agdd("/nonexistent/path/xxxx", mode="smart")


# ---------------------------------------------------------------------------
# run_install_project tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-TEN-001")
class TestRunInstallProject:
    """Tests for the install.run_install_project function."""

    def test_install_creates_thegent_assets(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="install-test",
            tenant_id="install-test",
            path=tmp_project,
            template="none",
        )

        result = run_install_project(
            project_selector="install-test",
            template="none",
            mode="smart",
            dry_run=False,
            registry_path=tmp_registry,
        )

        assert result["project_name"] == "install-test"
        assert (tmp_project / ".thegent" / "config.yaml").exists()
        assert (tmp_project / ".thegent" / "ownership.json").exists()
        assert (tmp_project / ".thegent" / "templates.lock").exists()
        assert result["errors"] == []

    def test_install_config_yaml_contents(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="cfg-test",
            tenant_id="cfg-tenant",
            path=tmp_project,
            template="none",
        )
        run_install_project(
            project_selector="cfg-test",
            template="none",
            mode="smart",
            registry_path=tmp_registry,
        )
        config_text = (tmp_project / ".thegent" / "config.yaml").read_text(encoding="utf-8")
        assert "tenant_id: cfg-tenant" in config_text
        assert "project_name: cfg-test" in config_text

    def test_install_ownership_json_contents(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="own-test",
            tenant_id="own-tenant",
            path=tmp_project,
            template="none",
        )
        run_install_project(
            project_selector="own-test",
            template="none",
            mode="smart",
            registry_path=tmp_registry,
        )
        data = json.loads((tmp_project / ".thegent" / "ownership.json").read_text(encoding="utf-8"))
        assert data["tenant_id"] == "own-tenant"

    def test_install_skip_mode_does_not_overwrite(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="skip-install",
            tenant_id="skip-install",
            path=tmp_project,
            template="none",
        )
        # Pre-create config with sentinel content
        thegent_dir = tmp_project / ".thegent"
        thegent_dir.mkdir()
        cfg = thegent_dir / "config.yaml"
        cfg.write_text("# SENTINEL\n", encoding="utf-8")

        result = run_install_project(
            project_selector="skip-install",
            template="none",
            mode="skip",
            registry_path=tmp_registry,
        )
        assert "# SENTINEL" in cfg.read_text(encoding="utf-8")
        assert ".thegent/config.yaml" in result["skipped"]

    def test_install_overwrite_mode_replaces(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="ow-install",
            tenant_id="ow-install",
            path=tmp_project,
            template="none",
        )
        thegent_dir = tmp_project / ".thegent"
        thegent_dir.mkdir()
        cfg = thegent_dir / "config.yaml"
        cfg.write_text("# OLD\n", encoding="utf-8")

        run_install_project(
            project_selector="ow-install",
            template="none",
            mode="overwrite",
            registry_path=tmp_registry,
        )
        content = cfg.read_text(encoding="utf-8")
        assert "# OLD" not in content
        assert "tenant_id: ow-install" in content

    def test_install_dry_run_writes_nothing(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="dry-install",
            tenant_id="dry-install",
            path=tmp_project,
            template="none",
        )
        result = run_install_project(
            project_selector="dry-install",
            template="none",
            mode="smart",
            dry_run=True,
            registry_path=tmp_registry,
        )
        assert not (tmp_project / ".thegent" / "config.yaml").exists()
        assert any("dry-run" in s for s in result["installed"])

    def test_install_invalid_mode_raises(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="bad-mode",
            tenant_id="bad-mode",
            path=tmp_project,
            template="none",
        )
        with pytest.raises(ValueError, match="Invalid install mode"):
            run_install_project(
                project_selector="bad-mode",
                template="none",
                mode="invalid",
                registry_path=tmp_registry,
            )

    def test_install_unregistered_project_raises(self, tmp_path: Path) -> None:
        from thegent.install import run_install_project

        isolated_reg = tmp_path / "empty_registry.json"
        with pytest.raises(KeyError, match="No registered project"):
            run_install_project(
                project_selector="no-such-project",
                registry_path=isolated_reg,
            )

    def test_install_cwd_fallback(self, tenancy, tmp_project: Path, tmp_registry: Path, monkeypatch) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="cwd-test",
            tenant_id="cwd-test",
            path=tmp_project,
            template="none",
        )
        monkeypatch.chdir(tmp_project)
        result = run_install_project(
            project_selector=None,
            template="none",
            mode="smart",
            registry_path=tmp_registry,
        )
        assert result["project_name"] == "cwd-test"

    def test_install_selector_by_path(self, tenancy, tmp_project: Path, tmp_registry: Path) -> None:
        from thegent.install import run_install_project

        tenancy.init_project(
            name="path-sel",
            tenant_id="path-sel",
            path=tmp_project,
            template="none",
        )
        result = run_install_project(
            project_selector=str(tmp_project),
            template="none",
            mode="smart",
            registry_path=tmp_registry,
        )
        assert result["project_name"] == "path-sel"


# ---------------------------------------------------------------------------
# CLI command tests (Typer test client)
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def project_cli():
    """Return the setup_project_app typer for direct invocation."""
    from thegent.cli.apps.project import setup_project_app

    return setup_project_app


@pytest.fixture
def install_cli():
    """Return the install_project_app typer for direct invocation."""
    from thegent.cli.apps.project import install_project_app

    return install_project_app


def _patch_tenancy(monkeypatch, reg_path: Path) -> ProjectTenancy:  # type: ignore[name-defined]  # noqa: F821
    """Patch the default tenancy singleton in the project_tenancy module."""
    import thegent.infra.project_tenancy as pt_module
    from thegent.infra.project_tenancy import ProjectTenancy

    fresh = ProjectTenancy(registry_path=reg_path)
    monkeypatch.setattr(pt_module, "_DEFAULT_TENANCY", fresh)
    monkeypatch.setattr(pt_module, "_DEFAULT_REGISTRY_PATH", reg_path)
    return fresh


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectInitCli:
    """CLI tests for `thegent sys setup project init`."""

    def test_init_missing_name_exits_nonzero(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        result = cli_runner.invoke(project_cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code != 0

    def test_init_missing_path_exits_nonzero(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        result = cli_runner.invoke(project_cli, ["init", "--name", "myproject", "--path", "/no/such/path/xyzzy"])
        assert result.exit_code != 0

    def test_init_creates_project(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "test-proj"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        result = cli_runner.invoke(
            project_cli,
            ["init", "--name", "test-proj", "--path", str(proj), "--tenant", "test-proj"],
        )
        assert result.exit_code == 0, result.output
        assert "test-proj" in result.output

    def test_init_json_output(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "json-proj"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        result = cli_runner.invoke(
            project_cli,
            ["init", "--name", "json-proj", "--path", str(proj), "--json"],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["name"] == "json-proj"
        assert "project_id" in payload


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectScaffoldCli:
    """CLI tests for `thegent sys setup project scaffold`."""

    def test_scaffold_invalid_profile_exits_nonzero(self, cli_runner: CliRunner, project_cli, tmp_path: Path) -> None:
        dest = tmp_path / "scaffold-invalid"
        result = cli_runner.invoke(project_cli, ["scaffold", str(dest), "--profile", "invalid"])
        assert result.exit_code != 0
        assert "Unknown scaffold profile" in result.output
        assert "service_api" in result.output

    def test_scaffold_rejects_nonempty_destination(self, cli_runner: CliRunner, project_cli, tmp_path: Path) -> None:
        dest = tmp_path / "scaffold-nonempty"
        dest.mkdir()
        (dest / "existing.txt").write_text("x", encoding="utf-8")
        result = cli_runner.invoke(project_cli, ["scaffold", str(dest)])
        assert result.exit_code != 0
        assert "destination is not empty" in result.output

    def test_scaffold_invokes_copier_with_profile_data(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        captured: dict[str, object] = {}

        def _fake_run(cmd: list[str], check: bool) -> None:
            from pathlib import Path

            assert check is True
            captured["cmd"] = cmd
            data_file = Path(cmd[5])
            payload = json.loads(data_file.read_text(encoding="utf-8"))
            captured["project_type"] = payload["project_type"]
            captured["interfaces"] = payload["interfaces"]
            captured["include_act"] = payload["include_act"]
            captured["include_qa_tools"] = payload["include_qa_tools"]
            captured["include_pm_tools"] = payload["include_pm_tools"]

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _fake_run)

        dest = tmp_path / "scaffold-service-api"
        result = cli_runner.invoke(project_cli, ["scaffold", str(dest), "--profile", "service_api"])
        assert result.exit_code == 0, result.output
        assert captured["project_type"] == "service_api"
        assert captured["interfaces"] == ["http_api", "docs"]
        assert captured["include_act"] is True
        assert captured["include_qa_tools"] is True
        assert captured["include_pm_tools"] is True
        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        assert cmd[0:3] == ["uvx", "copier", "copy"]

    def test_scaffold_dry_run_does_not_execute_copier(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        def _should_not_run(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            raise AssertionError("subprocess.run must not be called during dry-run")

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _should_not_run)

        dest = tmp_path / "scaffold-dry-run"
        result = cli_runner.invoke(
            project_cli, ["scaffold", str(dest), "--profile", "service_api", "--dry-run", "--json"]
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["dry_run"] is True
        assert payload["copier_cmd"] == []
        assert not dest.exists()

    def test_scaffold_flags_disable_optional_assets(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        captured: dict[str, object] = {}

        def _fake_run(cmd: list[str], check: bool) -> None:
            from pathlib import Path

            assert check is True
            captured["cmd"] = cmd
            data_file = Path(cmd[5])
            payload = json.loads(data_file.read_text(encoding="utf-8"))
            captured["include_act"] = payload["include_act"]
            captured["include_qa_tools"] = payload["include_qa_tools"]
            captured["include_pm_tools"] = payload["include_pm_tools"]

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _fake_run)

        dest = tmp_path / "scaffold-disable-flags"
        result = cli_runner.invoke(
            project_cli,
            [
                "scaffold",
                str(dest),
                "--profile",
                "service_api",
                "--no-include-act",
                "--no-include-qa-tools",
                "--no-include-pm-tools",
            ],
        )

        assert result.exit_code == 0, result.output
        assert captured["include_act"] is False
        assert captured["include_qa_tools"] is False
        assert captured["include_pm_tools"] is False

    def test_scaffold_registers_project_tenancy(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        def _fake_run(cmd: list[str], check: bool) -> None:
            assert check is True
            assert cmd[0:3] == ["uvx", "copier", "copy"]

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _fake_run)

        dest = tmp_path / "scaffold-register"
        result = cli_runner.invoke(
            project_cli,
            ["scaffold", str(dest), "--profile", "service_api", "--name", "svc", "--register", "--json"],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["register"] is True
        assert payload["tenant_id"] == "svc"
        record = fresh.get_project(name="svc")
        assert record is not None
        assert record.path == str(dest.resolve())

    def test_scaffold_install_runtime_requires_register_when_not_dry_run(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path
    ) -> None:
        dest = tmp_path / "scaffold-install-runtime-needs-register"
        result = cli_runner.invoke(
            project_cli,
            ["scaffold", str(dest), "--profile", "service_api", "--install-runtime"],
        )
        assert result.exit_code != 0
        assert "--install-runtime requires --register" in result.output

    def test_scaffold_install_runtime_runs_after_register(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        captured: dict[str, object] = {}

        def _fake_run(cmd: list[str], check: bool) -> None:
            assert check is True
            assert cmd[0:3] == ["uvx", "copier", "copy"]

        def _fake_install(
            project_selector: str | None = None,
            template: str = "none",
            mode: str = "smart",
            dry_run: bool = False,
            registry_path: Path | None = None,
        ) -> dict[str, object]:
            captured["project_selector"] = project_selector
            captured["template"] = template
            captured["mode"] = mode
            captured["dry_run"] = dry_run
            captured["registry_path"] = str(registry_path) if registry_path else ""
            return {
                "project_name": "svc-install",
                "path": str(project_selector),
                "template": "none",
                "installed": [".thegent/config.yaml"],
                "skipped": [".thegent/ownership.json"],
                "errors": [],
            }

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _fake_run)
        monkeypatch.setattr("thegent.install.run_install_project", _fake_install)

        dest = tmp_path / "scaffold-install-runtime"
        result = cli_runner.invoke(
            project_cli,
            [
                "scaffold",
                str(dest),
                "--profile",
                "service_api",
                "--name",
                "svc-install",
                "--register",
                "--install-runtime",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["install_runtime_requested"] is True
        assert payload["install_runtime_applied"] is True
        assert payload["install_runtime_status"] == "applied"
        assert payload["install_runtime_result"]["errors"] == []
        assert captured["project_selector"] == str(dest.resolve())
        assert captured["mode"] == "smart"
        assert captured["dry_run"] is False
        assert captured["registry_path"]

    def test_scaffold_install_runtime_skipped_for_dry_run(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        def _should_not_install(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            raise AssertionError("run_install_project must not be called during dry-run")

        monkeypatch.setattr("thegent.install.run_install_project", _should_not_install)

        dest = tmp_path / "scaffold-install-runtime-dry-run"
        result = cli_runner.invoke(
            project_cli,
            [
                "scaffold",
                str(dest),
                "--profile",
                "service_api",
                "--install-runtime",
                "--dry-run",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["dry_run"] is True
        assert payload["install_runtime_requested"] is True
        assert payload["install_runtime_applied"] is False
        assert payload["install_runtime_status"] == "skipped_dry_run"

    def test_scaffold_install_runtime_failure_exits_nonzero(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        def _fake_run(cmd: list[str], check: bool) -> None:
            assert check is True
            assert cmd[0:3] == ["uvx", "copier", "copy"]

        def _fail_install(*args, **kwargs) -> dict[str, object]:  # type: ignore[no-untyped-def]
            raise KeyError("no project")

        monkeypatch.setattr("thegent.cli.apps.project.subprocess.run", _fake_run)
        monkeypatch.setattr("thegent.install.run_install_project", _fail_install)

        dest = tmp_path / "scaffold-install-runtime-fail"
        result = cli_runner.invoke(
            project_cli,
            [
                "scaffold",
                str(dest),
                "--profile",
                "service_api",
                "--name",
                "svc-fail",
                "--register",
                "--install-runtime",
            ],
        )
        assert result.exit_code != 0
        assert "runtime install failed" in result.output

    def test_scaffold_profiles_text_output(self, cli_runner: CliRunner, project_cli) -> None:
        result = cli_runner.invoke(project_cli, ["scaffold-profiles"])
        assert result.exit_code == 0
        assert "service_api" in result.output
        assert "library_sdk" in result.output

    def test_scaffold_profiles_json_output(self, cli_runner: CliRunner, project_cli) -> None:
        result = cli_runner.invoke(project_cli, ["scaffold-profiles", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert "service_api" in payload
        assert "cli_tool" in payload


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectListCli:
    """CLI tests for `thegent sys setup project list`."""

    def test_list_empty(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        result = cli_runner.invoke(project_cli, ["list"])
        assert result.exit_code == 0
        assert "No projects" in result.output

    def test_list_shows_projects(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "listed-proj"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "listed-proj", "--path", str(proj), "--tenant", "listed-proj"],
        )
        result = cli_runner.invoke(project_cli, ["list"])
        assert result.exit_code == 0
        assert "listed-proj" in result.output

    def test_list_json_output(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "jlist"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "jlist", "--path", str(proj), "--tenant", "jlist"],
        )
        result = cli_runner.invoke(project_cli, ["list", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert isinstance(payload, list)
        assert payload[0]["name"] == "jlist"


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectShowCli:
    """CLI tests for `thegent sys setup project show`."""

    def test_show_not_found_exits_nonzero(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        result = cli_runner.invoke(project_cli, ["show", "nonexistent"])
        assert result.exit_code != 0

    def test_show_found(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "show-proj"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "show-proj", "--path", str(proj), "--tenant", "show-proj"],
        )
        result = cli_runner.invoke(project_cli, ["show", "show-proj"])
        assert result.exit_code == 0
        assert "show-proj" in result.output

    def test_show_json(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "sjson"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "sjson", "--path", str(proj), "--tenant", "sjson"],
        )
        result = cli_runner.invoke(project_cli, ["show", "sjson", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["name"] == "sjson"
        assert "tenant_root" in payload


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectDoctorCli:
    """CLI tests for `thegent sys setup project doctor`."""

    def test_doctor_pass_after_fix(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "dr-proj"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "dr-proj", "--path", str(proj), "--tenant", "dr-proj"],
        )
        cli_runner.invoke(project_cli, ["doctor", "dr-proj", "--fix"])
        # After fix, all fixable checks should pass
        assert (proj / ".thegent" / "config.yaml").exists()
        assert (proj / ".thegent" / "ownership.json").exists()
        assert (proj / ".thegent" / "templates.lock").exists()

    def test_doctor_json_output(self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "dr-json"
        proj.mkdir()
        _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        cli_runner.invoke(
            project_cli,
            ["init", "--name", "dr-json", "--path", str(proj), "--tenant", "dr-json"],
        )
        result = cli_runner.invoke(project_cli, ["doctor", "dr-json", "--json", "--fix"])
        payload = json.loads(result.output)
        assert isinstance(payload, list)
        assert payload[0]["project"] == "dr-json"


@pytest.mark.requirement("FR-TEN-001")
class TestSetupProjectMigrateCli:
    """CLI tests for `thegent sys setup project migrate`."""

    def test_migrate_dry_run_adopt_does_not_write_registry(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        proj = tmp_path / "migrate-dry-run"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        monkeypatch.setattr(
            "thegent.install.run_install_project",
            lambda *_, **__: {
                "project_selector": str(proj),
                "template": "none",
                "installed": [],
                "skipped": [],
                "errors": [],
                "status": "deferred",
            },
        )

        result = cli_runner.invoke(
            project_cli,
            ["migrate", str(proj), "--dry-run", "--register", "--json"],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["registration"]["status"] == "adopted (dry-run)"
        assert payload["runtime"]["status"] == "deferred"
        assert fresh.get_project(path=proj) is None

    def test_migrate_rejects_conflicting_name_on_dry_run(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        existing = tmp_path / "existing"
        existing.mkdir()
        new_project = tmp_path / "new-project"
        new_project.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        fresh.init_project(
            name="conflict-name",
            tenant_id="existing-tenant",
            path=existing,
            template="none",
        )

        result = cli_runner.invoke(
            project_cli,
            [
                "migrate",
                str(new_project),
                "--name",
                "conflict-name",
                "--dry-run",
                "--register",
            ],
        )
        assert result.exit_code != 0
        assert "Conflict on name" in result.output
        assert fresh.get_project(name="conflict-name", path=existing) is not None

    def test_migrate_invalid_lock_is_warning_only(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        proj = tmp_path / "existing-project"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        record = fresh.init_project(name="existing-project", tenant_id="existing-project", path=proj, template="ag-dd")
        (proj / ".thegent").mkdir(exist_ok=True)
        (proj / ".thegent" / "templates.lock").write_text("{", encoding="utf-8")

        captured: dict[str, object] = {}

        def _fake_install(
            project_selector: str | None = None,
            template: str = "none",
            mode: str = "smart",
            dry_run: bool = False,
            registry_path: Path | None = None,
        ) -> dict[str, object]:
            captured["project_selector"] = project_selector
            return {
                "project_selector": str(project_selector),
                "template": template,
                "mode": mode,
                "installed": [],
                "skipped": [],
                "errors": [],
                "status": "applied",
            }

        monkeypatch.setattr("thegent.install.run_install_project", _fake_install)

        result = cli_runner.invoke(
            project_cli,
            ["migrate", str(proj), "--template", "auto", "--json"],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["snapshot"]["lock_state"] == "invalid"
        assert payload["snapshot"]["registry_template"] == record.template
        assert captured["project_selector"] == str(proj)

    def test_migrate_reconciles_existing_template_built_project(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        proj = tmp_path / "existing-built"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        fresh.init_project(
            name="existing-built",
            tenant_id="existing-built",
            path=proj,
            template="none",
            template_version="1.0.0",
        )
        thegent_dir = proj / ".thegent"
        thegent_dir.mkdir()
        (thegent_dir / "templates.lock").write_text(
            json.dumps({"template": "ag-dd", "version": "1.1.0"}).decode(), encoding="utf-8"
        )

        calls: dict[str, object] = {}

        def _fake_install(
            project_selector: str | None = None,
            template: str = "none",
            mode: str = "smart",
            dry_run: bool = False,
            registry_path: Path | None = None,
        ) -> dict[str, object]:
            calls["template"] = template
            calls["mode"] = mode
            calls["dry_run"] = dry_run
            calls["registry_path"] = registry_path
            return {
                "project_selector": str(project_selector),
                "template": template,
                "installed": [],
                "skipped": [],
                "errors": [],
                "status": "applied" if not dry_run else "dry_run",
            }

        monkeypatch.setattr("thegent.install.run_install_project", _fake_install)

        result = cli_runner.invoke(project_cli, ["migrate", str(proj), "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)

        assert payload["registration"]["status"] == "reconciled"
        assert calls["template"] == "ag-dd"
        updated = fresh.get_project(path=proj)
        assert updated is not None
        assert updated.template == "ag-dd"
        assert updated.template_version == "1.1.0"

    def test_migrate_dry_run_keeps_registry_updates_planned(
        self, cli_runner: CliRunner, project_cli, tmp_path: Path, monkeypatch
    ) -> None:
        proj = tmp_path / "existing-built-dry"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")
        fresh.init_project(
            name="existing-built-dry",
            tenant_id="existing-built-dry",
            path=proj,
            template="none",
            template_version="1.0.0",
        )
        thegent_dir = proj / ".thegent"
        thegent_dir.mkdir()
        (thegent_dir / "templates.lock").write_text(
            json.dumps({"template": "ag-dd", "version": "1.2.0"}).decode(), encoding="utf-8"
        )

        result = cli_runner.invoke(project_cli, ["migrate", str(proj), "--dry-run", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["registration"]["status"] == "already_registered"
        assert payload["registration"]["planned_reconcile"] is True
        assert payload["registration"]["reconcile_changes"]["template"] == "ag-dd"
        recorded = fresh.get_project(path=proj)
        assert recorded is not None
        assert recorded.template == "none"
        assert recorded.template_version == "1.0.0"


@pytest.mark.requirement("FR-TEN-001")
class TestInstallProjectCli:
    """CLI tests for `thegent install project`."""

    def test_install_project_creates_assets(
        self, cli_runner: CliRunner, install_cli, tmp_path: Path, monkeypatch
    ) -> None:
        proj = tmp_path / "iproj"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        fresh.init_project(
            name="iproj",
            tenant_id="iproj",
            path=proj,
            template="none",
        )

        result = cli_runner.invoke(install_cli, ["--project", "iproj"])
        assert result.exit_code == 0, result.output
        assert (proj / ".thegent" / "config.yaml").exists()

    def test_install_project_dry_run(self, cli_runner: CliRunner, install_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "dry-iproj"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        fresh.init_project(
            name="dry-iproj",
            tenant_id="dry-iproj",
            path=proj,
            template="none",
        )

        result = cli_runner.invoke(install_cli, ["--project", "dry-iproj", "--dry-run"])
        assert result.exit_code == 0, result.output
        assert not (proj / ".thegent" / "config.yaml").exists()
        assert "dry-run" in result.output

    def test_install_project_invalid_mode_exits_nonzero(
        self, cli_runner: CliRunner, install_cli, tmp_path: Path
    ) -> None:
        result = cli_runner.invoke(install_cli, ["--project", "any", "--mode", "invalid-mode"])
        assert result.exit_code != 0

    def test_install_project_json_output(self, cli_runner: CliRunner, install_cli, tmp_path: Path, monkeypatch) -> None:
        proj = tmp_path / "json-iproj"
        proj.mkdir()
        fresh = _patch_tenancy(monkeypatch, tmp_path / "reg.json")

        fresh.init_project(
            name="json-iproj",
            tenant_id="json-iproj",
            path=proj,
            template="none",
        )

        result = cli_runner.invoke(install_cli, ["--project", "json-iproj", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["project_name"] == "json-iproj"
        assert "installed" in payload
        assert "skipped" in payload
        assert "errors" in payload
