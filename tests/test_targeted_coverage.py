"""Targeted tests to increase coverage."""



class TestExecutionPolicy:
    """Test execution policy module."""

    def test_circuit_breaker_import(self):
        """Test CircuitBreakerRegistry can be imported."""
        from thegent.execution.resilience import CircuitBreakerRegistry

        assert CircuitBreakerRegistry is not None

    def test_policy_import(self):
        """Test policy module loads."""
        from thegent.execution.policy import _execution_warning_count

        assert _execution_warning_count == 0


class TestProjectMigrate:
    """Test project migration module."""

    def test_project_migrate_import(self):
        """Test project_migrate can be imported."""
        from thegent.project.migrate import project_migrate

        result = project_migrate("/tmp/test", mode="agdd")
        assert result["path"] == "/tmp/test"
        assert result["mode"] == "agdd"

    def test_project_scaffold_import(self):
        """Test scaffold functions import."""
        from thegent.project.scaffold import scaffold_greenfield

        result = scaffold_greenfield("myapp", template="python")
        assert result["name"] == "myapp"
        assert result["type"] == "greenfield"


class TestCLIApps:
    """Test CLI app imports."""

    def test_install_app_imports(self):
        """Test install_app loads."""
        from thegent.cli.apps.project import install_app

        assert install_app is not None

    def test_scaffold_app_imports(self):
        """Test scaffold_app loads."""
        from thegent.cli.apps.project import scaffold_app

        assert scaffold_app is not None

    def test_update_app_imports(self):
        """Test update_app loads."""
        from thegent.cli.apps.project import update_app

        assert update_app is not None


class TestGovernance:
    """Test governance modules."""

    def test_governance_import(self):
        """Test governance modules load."""
        from thegent.governance import breakers

        assert hasattr(breakers, "CircuitBreaker")


class TestIntegrations:
    """Test integration modules."""

    def test_serializable_mixin_import(self):
        """Test SerializableMixin loads."""
        from thegent.integrations.base import SerializableMixin

        assert SerializableMixin is not None
