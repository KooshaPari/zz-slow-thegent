from __future__ import annotations

from pathlib import Path

import pytest

from thegent.security.macos_sandbox import SandboxLevel
from thegent.security.sandboxing import SandboxProvider


def test_sandbox_level_mapping_by_tier() -> None:
    provider = SandboxProvider()
    assert provider._sandbox_level_for_tier(1) == SandboxLevel.READONLY
    assert provider._sandbox_level_for_tier(2) == SandboxLevel.RESTRICTED
    assert provider._sandbox_level_for_tier(3) == SandboxLevel.RESTRICTED
    assert provider._sandbox_level_for_tier(4) == SandboxLevel.NETWORKED
    assert provider._sandbox_level_for_tier(5) == SandboxLevel.FULL


def test_generate_seatbelt_profile_uses_macos_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    provider = SandboxProvider()
    monkeypatch.setenv("THGENT_SANDBOX_WORKTREE", str(tmp_path))

    def _fake_generate(self, level, project_root):  # noqa: ANN001
        return f"profile:{level.value}:{project_root}"

    monkeypatch.setattr(
        "thegent.security.sandboxing.MacOSSandbox.generate_profile", _fake_generate
    )
    profile = provider._generate_seatbelt_profile(2)
    assert profile == f"profile:restricted:{tmp_path.resolve()}"


def test_seatbelt_wrap_raises_when_sandbox_exec_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = SandboxProvider()

    monkeypatch.setattr(
        "thegent.security.sandboxing.MacOSSandbox.is_sandbox_available",
        lambda _self: False,
    )
    with pytest.raises(RuntimeError, match="sandbox-exec is required"):
        provider._seatbelt_wrap(["echo", "hi"], tier=2)


def test_seatbelt_wrap_delegates_to_macos_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    provider = SandboxProvider()
    monkeypatch.setenv("THGENT_SANDBOX_WORKTREE", str(tmp_path))
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "thegent.security.sandboxing.MacOSSandbox.is_sandbox_available",
        lambda _self: True,
    )

    def _fake_apply(self, cmd, level, project_root):  # noqa: ANN001
        captured["cmd"] = cmd
        captured["level"] = level
        captured["project_root"] = project_root
        return ["sandbox-exec", "-f", "/tmp/test.sb", *cmd]

    monkeypatch.setattr(
        "thegent.security.sandboxing.MacOSSandbox.apply_to_command", _fake_apply
    )
    wrapped = provider._seatbelt_wrap(["echo", "hi"], tier=4)

    assert wrapped[:3] == ["sandbox-exec", "-f", "/tmp/test.sb"]
    assert captured["cmd"] == ["echo", "hi"]
    assert captured["level"] == SandboxLevel.NETWORKED
    assert captured["project_root"] == tmp_path.resolve()
