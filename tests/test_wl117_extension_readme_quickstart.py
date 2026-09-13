from __future__ import annotations

import re
from pathlib import Path

import orjson as json


def test_vscode_readme_quickstart_commands_exist_in_package_scripts() -> None:
    extension_dir = Path(__file__).resolve().parents[1] / "extensions" / "vscode"
    readme = (extension_dir / "README.md").read_text(encoding="utf-8")
    package = json.loads((extension_dir / "package.json").read_text(encoding="utf-8"))
    scripts = package.get("scripts", {})

    assert "## Run Steps" in readme
    command_names = re.findall(r"npm run ([a-zA-Z0-9:_-]+)", readme)
    assert command_names, "README quickstart must include at least one `npm run <script>` command"
    assert "lint" in command_names
    assert "test" in command_names

    for command in command_names:
        assert command in scripts, f"README references `npm run {command}` but package.json lacks scripts.{command}"
