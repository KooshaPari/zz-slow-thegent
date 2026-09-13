"""AST governance checks for e2e test helper imports."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_TEST_DIR = REPO_ROOT / "tests" / "e2e"

FORBIDDEN_LOCAL_HELPERS = {
    "load_cli_json",
    "expected_trend_health_signature",
    "command_path_exists",
    "_build_command_surface_drift_skip_message",
}
HELPER_TO_REQUIRED_MODULE = {
    "load_cli_json": "tests.e2e.cli_assertions",
    "expected_trend_health_signature": "tests.e2e.cli_assertions",
    "command_path_exists": "tests.e2e.command_surface",
    "_build_command_surface_drift_skip_message": "tests.e2e.cli_runner_compat",
}


def _target_test_files() -> list[Path]:
    current_file = Path(__file__).name
    return sorted(
        path for path in E2E_TEST_DIR.glob("test_*.py") if path.name != current_file
    )


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(module: ast.Module) -> set[str]:
    imported_modules: set[str] = set()

    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    return imported_modules


def _used_helper_names(module: ast.Module) -> set[str]:
    used_names: set[str] = set()

    for node in ast.walk(module):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in HELPER_TO_REQUIRED_MODULE:
                used_names.add(node.id)
        if isinstance(node, ast.Attribute) and node.attr in HELPER_TO_REQUIRED_MODULE:
            used_names.add(node.attr)

    return used_names


def _iter_target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for elt in target.elts:
            names.update(_iter_target_names(elt))
        return names
    return set()


def test_cli_runner_files_exist() -> None:
    paths = _target_test_files()
    assert paths, "expected at least one tests/e2e/test_*.py target file"


def test_no_local_helper_function_redefinitions() -> None:
    for path in _target_test_files():
        module = _parse_module(path)
        local_redefinitions = sorted(
            node.name
            for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in FORBIDDEN_LOCAL_HELPERS
        )

        assert not local_redefinitions, (
            f"{path} defines forbidden local helper functions: "
            + ", ".join(local_redefinitions)
        )


def test_helper_usage_requires_shared_helper_module_import() -> None:
    for path in _target_test_files():
        module = _parse_module(path)
        imported_modules = _imported_modules(module)
        used_helper_names = _used_helper_names(module)
        missing_imports: list[str] = []

        for helper_name in sorted(used_helper_names):
            required_module = HELPER_TO_REQUIRED_MODULE[helper_name]
            if required_module not in imported_modules:
                missing_imports.append(f"{helper_name} -> {required_module}")

        assert not missing_imports, (
            f"{path} uses helpers without required shared module import: "
            + ", ".join(missing_imports)
        )


def test_helper_symbols_are_imported_only_from_required_modules() -> None:
    for path in _target_test_files():
        module = _parse_module(path)
        invalid_helper_imports: list[str] = []

        for node in ast.walk(module):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            for alias in node.names:
                if alias.name not in HELPER_TO_REQUIRED_MODULE:
                    continue
                required_module = HELPER_TO_REQUIRED_MODULE[alias.name]
                if node.module != required_module:
                    invalid_helper_imports.append(
                        f"{alias.name} from {node.module} (expected {required_module})"
                    )

        assert not invalid_helper_imports, (
            f"{path} imports helper symbols from non-governed modules: "
            + ", ".join(sorted(invalid_helper_imports))
        )


def test_helper_names_are_not_shadowed_by_local_bindings() -> None:
    for path in _target_test_files():
        module = _parse_module(path)
        shadowed_names: set[str] = set()

        for node in ast.walk(module):
            bound_names: set[str] = set()

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    bound_names.update(_iter_target_names(target))
            elif isinstance(
                node,
                (
                    ast.AnnAssign,
                    ast.AugAssign,
                    ast.For,
                    ast.AsyncFor,
                    ast.comprehension,
                ),
            ):
                bound_names.update(_iter_target_names(node.target))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        bound_names.update(_iter_target_names(item.optional_vars))
            elif isinstance(node, ast.NamedExpr):
                bound_names.update(_iter_target_names(node.target))
            elif isinstance(node, ast.ExceptHandler) and node.name:
                bound_names.add(node.name)
            elif isinstance(node, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
                bound_names.update(arg.arg for arg in node.args.posonlyargs)
                bound_names.update(arg.arg for arg in node.args.args)
                bound_names.update(arg.arg for arg in node.args.kwonlyargs)
                if node.args.vararg is not None:
                    bound_names.add(node.args.vararg.arg)
                if node.args.kwarg is not None:
                    bound_names.add(node.args.kwarg.arg)

            shadowed_names.update(bound_names & FORBIDDEN_LOCAL_HELPERS)

        assert not shadowed_names, (
            f"{path} shadows governed helper names with local bindings: "
            + ", ".join(sorted(shadowed_names))
        )
