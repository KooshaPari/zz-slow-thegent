"""Git index.lock cleanup and periodic daemon (launchd/systemd).

Removes stale .git/index.lock files to unblock nix, direnv, and agents.
Uses mtime + lsof for safe removal (per GIT_INDEX_LOCK_OS_LEVEL_AND_AGENT_SYSTEM_USER_PLAN).
"""

import platform
import shlex
import subprocess
from collections.abc import Iterator
from pathlib import Path

from thegent.infra import run_subprocess_optimized

# Default scan paths when no --path given
DEFAULT_SCAN_PATHS = [
    Path.cwd(),
    Path.home() / "projects",
    Path.home() / "dev",
    Path.home() / "src",
    Path.home() / "code",
    Path.home() / "repos",
    Path.home() / "work",
]


def _get_lock_mtime_seconds(lock_path: Path) -> float | None:
    """Get mtime of lock file in seconds since epoch. Cross-platform."""
    try:
        stat = lock_path.stat()
        return stat.st_mtime
    except OSError:
        return None


def _resolve_git_dir(git_ref: Path) -> Path | None:
    """Resolve .git as directory or gitfile pointer to worktree git dir."""
    if not git_ref.exists():
        return None

    if git_ref.is_dir():
        return git_ref

    if not git_ref.is_file():
        return None

    try:
        raw = git_ref.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None

    if not raw.lower().startswith("gitdir:"):
        return None

    payload = raw.split(":", 1)[1].strip()
    return (git_ref.parent / payload).resolve()


def _has_open_holder(lock_path: Path) -> bool | None:
    """Return True if any process has the lock file open (lsof)."""
    try:
        result = run_subprocess_optimized(
            ["lsof", str(lock_path)],
            capture_output=True,
            timeout=5,
        )
        stdout_text = (
            result.stdout
            if isinstance(result.stdout, str)
            else (result.stdout.decode("utf-8", errors="replace") if result.stdout else "")
        )
        stderr_text = (
            result.stderr
            if isinstance(result.stderr, str)
            else (result.stderr.decode("utf-8", errors="replace") if result.stderr else "")
        )

        if result.returncode == 0:
            return bool(stdout_text and stdout_text.strip())
        if result.returncode == 1 and not stdout_text.strip() and not stderr_text.strip():
            return False
        return None
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return False


def _find_lock_files(paths: list[Path]) -> Iterator[Path]:
    """Yield .git/index.lock under each path.

    Supports:
      - Standard repos with .git as a directory
      - Worktrees where .git is a pointer file
      - Shared gitdir worktrees metadata under <gitdir>/worktrees/*
    """
    seen: set[Path] = set()
    for base in paths:
        if not base.exists():
            continue

        git_dir = _resolve_git_dir(base / ".git")
        if git_dir is not None:
            lock = git_dir / "index.lock"
            if lock.exists() and lock not in seen:
                seen.add(lock)
                yield lock

            worktree_index = git_dir / "worktrees"
            if worktree_index.exists() and worktree_index.is_dir():
                try:
                    for candidate in worktree_index.iterdir():
                        if not candidate.is_dir():
                            continue
                        lock = candidate / "index.lock"
                        if lock.exists() and lock not in seen:
                            seen.add(lock)
                            yield lock
                except (OSError, PermissionError):
                    pass

        else:
            lock = base / ".git" / "index.lock"
        if lock.exists() and lock not in seen:
            seen.add(lock)
            yield lock


def run_lock_cleanup(
    paths: list[Path] | None = None,
    max_age: int = 60,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Remove stale .git/index.lock files. Returns (removed_count, skipped_count)."""
    import time

    now = time.time()
    paths = paths or DEFAULT_SCAN_PATHS
    removed = 0
    skipped = 0

    for lock_path in _find_lock_files(paths):
        mtime = _get_lock_mtime_seconds(lock_path)
        if mtime is None:
            continue
        age = now - mtime
        if age < max_age:
            skipped += 1
            continue
        has_open_holder = _has_open_holder(lock_path)
        if has_open_holder is None:
            skipped += 1
            continue
        if has_open_holder:
            skipped += 1
            continue
        if dry_run:
            removed += 1
            continue
        try:
            lock_path.unlink()
            removed += 1
        except OSError:
            skipped += 1

    return removed, skipped


def _lock_cleanup_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.thegent.git-lock-cleanup.plist"


def _lock_cleanup_thegent_cmd() -> list[str]:
    """Command to run thegent git lock-cleanup."""
    import sys

    python = sys.executable
    if not python or not Path(python).exists():
        python = "python3"
    return [python, "-m", "thegent.main", "git", "lock-cleanup"]


def lock_cleanup_install() -> tuple[bool, str]:
    """Install thegent git lock-cleanup as launchd (macOS) or systemd timer (Linux)."""
    if platform.system() == "Darwin":
        return _lock_cleanup_install_launchd()
    if platform.system() == "Linux":
        return _lock_cleanup_install_systemd()
    return False, "Only macOS and Linux supported. Use cron manually."


def _lock_cleanup_install_launchd() -> tuple[bool, str]:
    plist_path = _lock_cleanup_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _lock_cleanup_thegent_cmd()
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>Label</key>
<string>com.thegent.git-lock-cleanup</string>
<key>ProgramArguments</key>
<array>
<string>{cmd[0]}</string>
<string>{cmd[1]}</string>
<string>{cmd[2]}</string>
<string>{cmd[3]}</string>
<string>{cmd[4]}</string>
</array>
<key>StartInterval</key>
<integer>300</integer>
<key>RunAtLoad</key>
<false/>
<key>StandardOutPath</key>
<string>{Path.home()}/.cache/thegent/git-lock-cleanup.log</string>
<key>StandardErrorPath</key>
<string>{Path.home()}/.cache/thegent/git-lock-cleanup.err</string>
</dict>
</plist>
"""
    plist_path.write_text(plist)
    Path.home().joinpath(".cache/thegent").mkdir(parents=True, exist_ok=True)
    return True, f"Installed to {plist_path}. Run: thegent git lock-cleanup service start"


def _lock_cleanup_install_systemd() -> tuple[bool, str]:
    """Install systemd user timer."""
    user_home = Path.home()
    systemd_user = user_home / ".config" / "systemd" / "user"
    systemd_user.mkdir(parents=True, exist_ok=True)

    cmd = _lock_cleanup_thegent_cmd()
    exec_line = shlex.join(cmd)
    service_content = f"""[Unit]
Description=thegent git index.lock cleanup
After=network.target

[Service]
Type=oneshot
ExecStart={exec_line}
"""
    timer_content = """[Unit]
Description=thegent git lock-cleanup every 5 min

[Timer]
OnUnitInactiveSec=300
Persistent=true

[Install]
WantedBy=timers.target
"""
    service_path = systemd_user / "thegent-git-lock-cleanup.service"
    timer_path = systemd_user / "thegent-git-lock-cleanup.timer"
    service_path.write_text(service_content)
    timer_path.write_text(timer_content)
    return (
        True,
        f"Installed to {service_path} and {timer_path}. Run: systemctl --user enable --now thegent-git-lock-cleanup.timer",
    )


def lock_cleanup_uninstall() -> tuple[bool, str]:
    """Remove launchd or systemd timer."""
    if platform.system() == "Darwin":
        plist_path = _lock_cleanup_plist_path()
        run_subprocess_optimized(["launchctl", "unload", str(plist_path)], check=False, capture_output=True)
        if plist_path.exists():
            plist_path.unlink()
        return True, "Uninstalled"
    if platform.system() == "Linux":
        run_subprocess_optimized(
            ["systemctl", "--user", "disable", "--now", "thegent-git-lock-cleanup.timer"],
            check=False,
            capture_output=True,
        )
        for name in ("thegent-git-lock-cleanup.timer", "thegent-git-lock-cleanup.service"):
            p = Path.home() / ".config" / "systemd" / "user" / name
            if p.exists():
                p.unlink()
        return True, "Uninstalled"
    return False, "Only macOS and Linux supported"


def lock_cleanup_start() -> tuple[bool, str]:
    """Start the lock-cleanup daemon."""
    if platform.system() == "Darwin":
        plist_path = _lock_cleanup_plist_path()
        if not plist_path.exists():
            return False, "Not installed. Run: thegent git lock-cleanup service install"
        run_subprocess_optimized(["launchctl", "load", str(plist_path)], capture_output=True, check=True)
        return True, "Started"
    if platform.system() == "Linux":
        run_subprocess_optimized(
            ["systemctl", "--user", "enable", "--now", "thegent-git-lock-cleanup.timer"],
            capture_output=True,
            check=True,
        )
        return True, "Started"
    return False, "Only macOS and Linux supported"


def lock_cleanup_stop() -> tuple[bool, str]:
    """Stop the lock-cleanup daemon."""
    if platform.system() == "Darwin":
        plist_path = _lock_cleanup_plist_path()
        if not plist_path.exists():
            return False, "Not installed"
        run_subprocess_optimized(["launchctl", "unload", str(plist_path)], check=False, capture_output=True)
        return True, "Stopped"
    if platform.system() == "Linux":
        run_subprocess_optimized(
            ["systemctl", "--user", "disable", "--now", "thegent-git-lock-cleanup.timer"],
            check=False,
            capture_output=True,
        )
        return True, "Stopped"
    return False, "Only macOS and Linux supported"


def lock_cleanup_status() -> tuple[bool, str]:
    """Check if lock-cleanup daemon is installed and running."""
    if platform.system() == "Darwin":
        plist_path = _lock_cleanup_plist_path()
        if not plist_path.exists():
            return True, "Not installed"
        result = run_subprocess_optimized(
            ["launchctl", "list", "com.thegent.git-lock-cleanup"],
            check=False,
            capture_output=True,
            text=True,
        )
        stdout_text = (
            result.stdout
            if isinstance(result.stdout, str)
            else (result.stdout.decode("utf-8", errors="replace") if result.stdout else "")
        )
        if result.returncode == 0 and stdout_text and "com.thegent.git-lock-cleanup" in stdout_text:
            return True, "Running (launchd)"
        return True, "Stopped"
    if platform.system() == "Linux":
        result = run_subprocess_optimized(
            ["systemctl", "--user", "is-active", "thegent-git-lock-cleanup.timer"],
            check=False,
            capture_output=True,
            text=True,
        )
        stdout_text = (
            result.stdout
            if isinstance(result.stdout, str)
            else (result.stdout.decode("utf-8", errors="replace") if result.stdout else "")
        )
        if result.returncode == 0 and stdout_text and "active" in stdout_text.strip():
            return True, "Running (systemd)"
        return True, "Stopped"
    return True, "Unknown platform"
