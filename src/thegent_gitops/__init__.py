"""Productized git operations components.

This package extracts multi-tenant Git, worktree coordination, native git wrappers,
lock cleanup daemons, and identity helpers into dedicated domain modules.
"""

from thegent_gitops.git import GitParallelismManager
from thegent_gitops.identity import (
    _build_actor_email,
    _git_config_get,
    _parse_profile_map,
    infer_actor_profile,
    normalize_actor_profile,
    resolve_author_env,
)
from thegent_gitops.lock_cleanup import (
    DEFAULT_SCAN_PATHS,
    _find_lock_files,
    _get_lock_mtime_seconds,
    _has_open_holder,
    _lock_cleanup_install_launchd,
    _lock_cleanup_install_systemd,
    _lock_cleanup_plist_path,
    _lock_cleanup_thegent_cmd,
    lock_cleanup_install,
    lock_cleanup_start,
    lock_cleanup_status,
    lock_cleanup_stop,
    lock_cleanup_uninstall,
    run_lock_cleanup,
)
from thegent_gitops.native import (
    GitNative,
    get_head,
    get_status,
    has_changes,
    list_branches,
)
from thegent_gitops.worktree import WorktreeContext, WorktreePool

__all__ = [
    "GitParallelismManager",
    "GitNative",
    "WorktreeContext",
    "WorktreePool",
    "resolve_author_env",
    "infer_actor_profile",
    "normalize_actor_profile",
    "_build_actor_email",
    "_git_config_get",
    "_parse_profile_map",
    "_find_lock_files",
    "_get_lock_mtime_seconds",
    "_has_open_holder",
    "_lock_cleanup_install_launchd",
    "_lock_cleanup_install_systemd",
    "_lock_cleanup_plist_path",
    "_lock_cleanup_thegent_cmd",
    "DEFAULT_SCAN_PATHS",
    "get_head",
    "get_status",
    "has_changes",
    "list_branches",
    "lock_cleanup_install",
    "lock_cleanup_start",
    "lock_cleanup_status",
    "lock_cleanup_stop",
    "lock_cleanup_uninstall",
    "run_lock_cleanup",
]
