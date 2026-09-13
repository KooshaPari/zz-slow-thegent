from pathlib import Path

import pytest


def test_manifest_excludes_runtime_config_and_hooks() -> None:
    from thegent.install.factory_assets import FACTORY_ASSETS

    assert FACTORY_ASSETS
    assert all(asset.target.startswith("skills/") for asset in FACTORY_ASSETS)
    assert all("config" not in asset.target for asset in FACTORY_ASSETS)
    assert all("hook" not in asset.target for asset in FACTORY_ASSETS)


def test_install_writes_owned_assets_and_receipt(tmp_path: Path) -> None:
    from thegent.install.factory_assets import install_factory_assets

    result = install_factory_assets(tmp_path / "factory")

    assert result.installed
    assert (tmp_path / "factory" / "thegent" / "SKILL.md").is_file()
    assert (tmp_path / "factory" / ".thegent-assets.json").is_file()


def test_uninstall_removes_only_owned_assets(tmp_path: Path) -> None:
    from thegent.install.factory_assets import (
        install_factory_assets,
        uninstall_factory_assets,
    )

    root = tmp_path / "factory"
    install_factory_assets(root)
    user_file = root / "user-note.txt"
    user_file.write_text("keep", encoding="utf-8")

    result = uninstall_factory_assets(root)

    assert result.removed
    assert user_file.is_file()
    assert not (root / "thegent").exists()
    assert not (root / ".thegent-assets.json").exists()


def test_install_refuses_existing_unowned_asset(tmp_path: Path) -> None:
    from thegent.install.factory_assets import install_factory_assets

    root = tmp_path / "factory"
    target = root / "thegent" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("user content", encoding="utf-8")

    with pytest.raises(FileExistsError):
        install_factory_assets(root)
