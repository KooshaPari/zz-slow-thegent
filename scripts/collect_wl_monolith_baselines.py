#!/usr/bin/env python3
"""Collect extraction baseline metrics for WL-124/WL-125/WL-126 monolith files."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WL_TARGETS = {
    "WL-124": ROOT / "src" / "thegent" / "cli" / "commands" / "cli.py",
    "WL-125": ROOT / "src" / "thegent" / "cli" / "commands" / "impl.py",
    "WL-126": ROOT / "src" / "thegent" / "mcp" / "server" / "__init__.py",
}


def _safe_attr_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _safe_attr_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    return None


def _extract_decorated_commands(tree: ast.AST) -> list[str]:
    commands: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef | ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            decorator_name = _safe_attr_name(decorator.func)
            if decorator_name is None or not decorator_name.endswith(".command"):
                continue
            if (
                decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                commands.append(decorator.args[0].value)
            else:
                commands.append(node.name)
    return sorted(set(commands))


def _extract_top_level_functions(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef | ast.AsyncFunctionDef)):
            names.append(node.name)
    return names


def collect_metrics(path: Path) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    module = tree if isinstance(tree, ast.Module) else ast.Module(body=[])

    top_level_functions = _extract_top_level_functions(module)
    async_function_count = sum(isinstance(node, ast.AsyncFunctionDef) for node in ast.walk(tree))
    class_count = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))

    lines = source.splitlines()
    max_line_length = max((len(line) for line in lines), default=0)

    return {
        "path": str(path.relative_to(ROOT)),
        "line_count": len(lines),
        "top_level_function_count": len(top_level_functions),
        "top_level_function_sample": top_level_functions[:20],
        "async_function_count": async_function_count,
        "class_count": class_count,
        "command_decorator_count": len(_extract_decorated_commands(tree)),
        "command_decorator_sample": _extract_decorated_commands(tree)[:25],
        "max_line_length": max_line_length,
    }


def collect_all() -> dict[str, dict[str, object]]:
    return {wl_id: collect_metrics(path) for wl_id, path in WL_TARGETS.items()}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--out", type=Path, default=None, help="Optional output file path.")
    return parser.parse_args(argv)


def _render_text(payload: dict[str, dict[str, object]]) -> str:
    lines: list[str] = []
    for wl_id in sorted(payload):
        info = payload[wl_id]
        lines.append(f"{wl_id} :: {info['path']}")
        lines.append(
            f"  lines={info['line_count']} top_level_functions={info['top_level_function_count']} classes={info['class_count']}"
        )
        lines.append(
            f"  async_functions={info['async_function_count']} command_decorators={info['command_decorator_count']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    payload = collect_all()

    if args.format == "json":
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    else:
        rendered = _render_text(payload)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
