from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_EXCLUDED_REPOS,
)
from .git_ops import sanitize_repo_id
from .models import ModuleManifest, RepoSelection, TargetLock
from .paths import repository_root_candidates

__all__ = [
    "_parse_lock",
    "_lock_hash",
    "_repo_id_from_path",
    "_select_module_repos",
    "_stable_payload_hash",
]


def _stable_payload_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_lock(payload: dict[str, Any]) -> TargetLock:
    repos = [RepoSelection(**repo) for repo in payload.get("repos", [])]
    return TargetLock(
        schema_version=int(payload.get("schema_version", 1)),
        target_name=str(payload.get("target_name", "")),
        mode=payload.get("mode", "repo"),
        repos=repos,
        lock_hash=str(payload.get("lock_hash", "")),
        created_at_utc=str(payload.get("created_at_utc", "")),
    )


def _lock_hash(lock: TargetLock) -> str:
    from dataclasses import asdict

    payload = asdict(lock)
    payload["lock_hash"] = ""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _repo_id_from_path(repo_path: Path) -> str:
    return sanitize_repo_id(repo_path.name)


def _select_module_repos(
    manifest: ModuleManifest,
    exclude_repos: set[str] | None = None,
) -> list[Path]:
    from fnmatch import fnmatch

    excluded = {sanitize_repo_id(repo_name) for repo_name in (exclude_repos or set())}
    selected: list[Path] = []
    for repo_path in repository_root_candidates():
        repo_id = _repo_id_from_path(repo_path)
        if repo_id in DEFAULT_EXCLUDED_REPOS or repo_id in excluded:
            continue
        if not any(fnmatch(repo_id, pattern) for pattern in manifest.repo_patterns):
            continue
        if not (repo_path / ".git").exists():
            continue
        selected.append(repo_path)
    return selected
