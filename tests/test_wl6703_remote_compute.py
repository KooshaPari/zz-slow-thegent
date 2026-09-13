from __future__ import annotations

import subprocess
from pathlib import Path

from thegent.research.remote_compute import RemoteComputeClient


def test_execute_remote_quotes_cwd_and_command(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(cmd, capture_output, text, check):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("thegent.research.remote_compute.subprocess.run", fake_run)

    client = RemoteComputeClient("user@example.com", remote_port=2202)
    result = client.execute_remote("echo $HOME && ls", cwd=Path("/tmp/dir with space;echo pwn"))

    assert result == {"stdout": "ok", "stderr": "", "exit_code": 0, "status": "success"}

    ssh_cmd = seen["cmd"]
    assert ssh_cmd[:4] == ["ssh", "-p", "2202", "user@example.com"]
    assert ssh_cmd[4] == "cd '/tmp/dir with space;echo pwn' && sh -lc 'echo $HOME && ls'"


def test_execute_remote_payload_shape_on_failure(monkeypatch) -> None:
    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(args=cmd, returncode=9, stdout="", stderr="boom")

    monkeypatch.setattr("thegent.research.remote_compute.subprocess.run", fake_run)

    client = RemoteComputeClient("user@example.com")
    result = client.execute_remote("whoami")

    assert set(result.keys()) == {"stdout", "stderr", "exit_code", "status"}
    assert result["stdout"] == ""
    assert result["stderr"] == "boom"
    assert result["exit_code"] == 9
    assert result["status"] == "failed"
