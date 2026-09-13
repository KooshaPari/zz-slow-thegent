from __future__ import annotations

from pathlib import Path

from thegent.ide.auto_setup import auto_setup_ghostty_shell_integration

BEGIN = "# >>> thegent managed: ghostty shell integration >>>"
END = "# <<< thegent managed: ghostty shell integration <<<"


def test_auto_setup_ghostty_inserts_managed_block_once(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text("export PATH=$PATH\n", encoding="utf-8")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GHOSTTY_RESOURCES_DIR", raising=False)
    monkeypatch.setattr("thegent.ide.auto_setup.shutil.which", lambda name: "/usr/bin/ghostty")

    first = auto_setup_ghostty_shell_integration(auto_configure=True)
    second = auto_setup_ghostty_shell_integration(auto_configure=True)

    content = zshrc.read_text(encoding="utf-8")
    assert first["success"] is True
    assert second["success"] is True
    assert second["message"] == "Ghostty shell integration already configured"
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1


def test_auto_setup_ghostty_rewrites_existing_managed_block(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text(
        "\n".join(
            [
                "export PATH=$PATH",
                BEGIN,
                "# stale body",
                "export GHOSTTY_SHELL_INTEGRATION=0",
                END,
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("GHOSTTY_RESOURCES_DIR", raising=False)
    monkeypatch.setattr("thegent.ide.auto_setup.shutil.which", lambda name: "/usr/bin/ghostty")

    result = auto_setup_ghostty_shell_integration(auto_configure=True)

    content = zshrc.read_text(encoding="utf-8")
    assert result["success"] is True
    assert "auto-configured" in result["message"]
    assert content.count(BEGIN) == 1
    assert content.count(END) == 1
    assert "export GHOSTTY_SHELL_INTEGRATION=1" in content
    assert "export GHOSTTY_SHELL_INTEGRATION=0" not in content
