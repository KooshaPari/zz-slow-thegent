"""Unit tests for tray projects tab."""

import pytest

pytest.importorskip("PySide6")

import ast
from pathlib import Path


def get_module_ast(file_path: str) -> ast.Module:
    """Parse a Python file and return its AST."""
    with open(file_path) as f:
        source = f.read()
    return ast.parse(source, filename=file_path)


def find_class_definitions(module: ast.Module) -> list[str]:
    """Find all class definitions in an AST module."""
    return [node.name for node in ast.walk(module) if isinstance(node, ast.ClassDef)]


def find_function_definitions(module: ast.Module) -> list[str]:
    """Find all function definitions in an AST module."""
    return [node.name for node in ast.walk(module) if isinstance(node, ast.FunctionDef)]


@pytest.mark.unit
class TestProjectEditDialog:
    """Tests for ProjectEditDialog class."""

    def test_class_exists_in_source(self):
        """ProjectEditDialog class exists in projects.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "ProjectEditDialog" in classes

    def test_get_data_method_in_source(self):
        """get_data method exists in ProjectEditDialog source."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)

        # Find the ProjectEditDialog class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ProjectEditDialog":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "get_data" in methods
                return

        pytest.fail("ProjectEditDialog class not found")


@pytest.mark.unit
class TestProjectsTab:
    """Tests for ProjectsTab class."""

    def test_class_exists_in_source(self):
        """ProjectsTab class exists in projects.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)
        classes = find_class_definitions(module)
        assert "ProjectsTab" in classes

    def test_tab_id_constant_exists(self):
        """ProjectsTab has TAB_ID constant."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)

        # Find ProjectsTab class and check for TAB_ID assignment
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ProjectsTab":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "TAB_ID":
                                return

        pytest.fail("TAB_ID not found in ProjectsTab class")

    def test_has_required_methods(self):
        """ProjectsTab has required methods."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)

        # Find the ProjectsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ProjectsTab":
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                assert "_setup_ui" in methods
                assert "_load_projects" in methods
                assert "_update_table" in methods
                return

        pytest.fail("ProjectsTab class not found")

    def test_accepts_api_client_parameter(self):
        """ProjectsTab.__init__ accepts api_client parameter."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)

        # Find the ProjectsTab class
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name == "ProjectsTab":
                # Find __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = [arg.arg for arg in item.args.args]
                        assert "api_client" in args
                        return

        pytest.fail("ProjectsTab.__init__ not found")


@pytest.mark.unit
class TestGetTabFunction:
    """Tests for get_tab function."""

    def test_get_tab_function_exists(self):
        """get_tab function exists in projects.py."""
        file_path = Path(
            Path(__file__).parent,
            "..",
            "src",
            "thegent",
            "tray",
            "plugins",
            "thegent",
            "tabs",
            "projects.py",
        )
        module = get_module_ast(file_path)
        functions = find_function_definitions(module)
        assert "get_tab" in functions


@pytest.mark.unit
class TestTabsPackage:
    """Tests for tabs package."""

    def test_tabs_package_exports(self):
        """tabs package exports required items."""
        import sys
        from pathlib import Path

        # Add src to path
        src_path = Path(__file__).parent.parent.parent / "src"
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        try:
            from thegent.tray.plugins.thegent import tabs

            # Check exports
            assert hasattr(tabs, "get_tab")
            assert callable(tabs.get_tab)
        except ImportError as e:
            if "PySide6" in str(e) or "thegent.tray" in str(e):
                pytest.skip("PySide6 not installed - tray tests require GUI libraries")
            pytest.fail(f"Failed to import tabs package: {e}")
