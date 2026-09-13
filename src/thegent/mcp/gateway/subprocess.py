"""Subprocess transport for MCP gateway."""

import subprocess as _subprocess


def run(
    command: list[str],
    request_payload: str,
    env: dict[str, str],
    timeout_sec: float,
) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr).

    This function is designed to be monkeypatched in tests.
    """
    try:
        result = _subprocess.run(
            command,
            input=request_payload.encode(),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_sec,
        )
        # Return as tuple for compatibility
        return (result.returncode, result.stdout, result.stderr)
    except _subprocess.TimeoutExpired:
        return (124, "", "timeout")
    except Exception as e:
        return (1, "", str(e))
