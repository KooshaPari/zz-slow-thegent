"""Tests for scripts/install-thegent-shims.sh symlink coverage."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_install_script_creates_extended_harness_symlinks(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install-thegent-shims.sh"
    assert script.exists()

    shim = tmp_path / "thegent-shims"
    shim.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    result = subprocess.run(
        ["zsh", str(script), "--install-dir", str(tmp_path)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    for name in (
        "dex",
        "clode",
        "roid",
        "fanta",
        "antigma",
        "cline",
        "roocode",
        "opencode",
    ):
        link = tmp_path / name
        assert link.is_symlink(), f"{name} should be a symlink"
        assert link.resolve() == shim.resolve()


def test_install_script_warns_on_path_shadowing(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "install-thegent-shims.sh"
    assert script.exists()

    install_dir = tmp_path / "install"
    install_dir.mkdir(parents=True, exist_ok=True)
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir(parents=True, exist_ok=True)

    shim = tmp_path / "thegent-shims"
    shim.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)

    # Shadow dex with a different binary earlier in PATH.
    shadow_dex = shadow_dir / "dex"
    shadow_dex.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    shadow_dex.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{shadow_dir}:{tmp_path}:{env.get('PATH', '')}"
    result = subprocess.run(
        ["zsh", str(script), "--install-dir", str(install_dir)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Warning: 'dex' resolves to" in result.stdout
