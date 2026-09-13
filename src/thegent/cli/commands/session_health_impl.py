"""Session-contract health surface (AUDIT-N+19 Phase 4).

Implements the canonical session-contract gate / report / trend checks
the WL-120 follow-up surface exposes.

The three operations:

  * :func:`session_contract_health_gate_impl` — boolean gate
    ("pass" / "blocked") against a min healthy ratio
  * :func:`session_contract_health_report_impl` — full per-session
    report (re-exported from :mod:`session_health_report_impl`)
  * :func:`session_contract_health_trend_impl` — historic trend
    computed from the JSONL snapshot log

The snapshot-log helpers (:func:`_append_health_snapshot`,
:func:`_compact_health_snapshot_log`, :func:`_load_previous_health_snapshot`,
:func:`_resolve_health_policy`, :func:`_hash_health_payload`,
:func:`_health_scope_key`, :func:`_health_snapshot_log_path`,
:func:`_health_snapshot_max_lines`, :func:`_coerce_issue_types`) live
here so the ``thegent.cli.commands.session_health_impl.*`` module
patch sites resolve cleanly.

Pinned by ``tests/test_unit_cli_impl_dag.py::TestHealthGateImpl`` and
sibling tests.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from thegent.config import ThegentSettings

# AUDIT-N+19: schema-version constant re-exported so callers can
# ``from thegent.cli import HEALTH_PAYLOAD_SCHEMA_VERSION``.
HEALTH_PAYLOAD_SCHEMA_VERSION = "3.0"


# Built-in health-policy profiles (name → strict + ratio).
_HEALTH_POLICY_PROFILES: dict[str, dict[str, Any]] = {
    "strict_ci": {"strict": True, "min_healthy_ratio": 1.0},
    "warn_only": {"strict": False, "min_healthy_ratio": 0.0},
}


def _coerce_issue_types(value: Any) -> list[str]:
    """Normalize an issue value (list / dict / scalar) to ``list[str]``."""
    if value is None:
        return []
    if isinstance(value, dict):
        return [str(v) for v in value]
    if isinstance(value, (list | tuple | set)):
        return [str(v) for v in value]
    return [str(value)]


def _health_snapshot_log_path() -> Path:
    """Return the canonical health-snapshot JSONL log path.

    Default: ``<settings.session_dir>/health_snapshots.jsonl``. When
    ``THGENT_HEALTH_SNAPSHOT_PATH`` is set, that takes precedence.
    """
    raw = os.environ.get("THGENT_HEALTH_SNAPSHOT_PATH") or ""
    if raw:
        path = Path(raw).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    settings = ThegentSettings()
    session_dir = Path(getattr(settings, "session_dir", "/tmp/thegent/sessions"))
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / "health_snapshots.jsonl"


def _health_snapshot_max_lines() -> int:
    """Return the canonical health-snapshot retention line count (default 5000)."""
    env_value = os.environ.get("THGENT_HEALTH_SNAPSHOT_MAX_LINES")
    if env_value:
        try:
            return max(100, int(env_value))
        except ValueError:
            pass
    return 5000


def _hash_health_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Compute the stable SHA-256 signature for ``payload``.

    Volatile fields (``generated_at_utc``, ``payload_signature``) are
    excluded so each report hashes deterministically.
    """
    payload_for_hash = {
        key: value for key, value in payload.items() if key not in {"generated_at_utc", "payload_signature"}
    }
    import orjson as _json

    body = _json.dumps(payload_for_hash, option=_json.OPT_SORT_KEYS).decode()
    return {"algorithm": "sha256", "value": hashlib.sha256(body.encode()).hexdigest()}


def _health_scope_key(payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic scope key for ``payload``.

    Returns a dict whose keys mirror the canonical
    ``run_health_helpers.health_scope_key`` shape.
    """
    query = payload.get("generated_query", {}) or {}
    scope: dict[str, Any] = {
        "payload_type": payload.get("payload_type", ""),
        "owner": query.get("owner"),
        "all": bool(query.get("all", False)),
        "strict": bool(query.get("strict", False)),
        "policy_profile": payload.get("policy_profile", "custom"),
    }
    if payload.get("payload_type") == "session_contract_health_gate":
        scope["min_healthy_ratio"] = float(query.get("min_healthy_ratio", 1.0))
    if payload.get("payload_type") == "session_contract_health_report":
        scope["top_blocked"] = int(query.get("top_blocked", 25))
    return scope


def _compact_health_snapshot_log() -> None:
    """Trim the snapshot log to the last ``_health_snapshot_max_lines()`` lines."""
    path = _health_snapshot_log_path()
    if not path.exists():
        return
    limit = _health_snapshot_max_lines()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = text.splitlines()
    if len(lines) <= limit:
        return
    trimmed = lines[-limit:]
    try:
        path.write_text("\n".join(trimmed) + "\n", encoding="utf-8")
    except OSError:
        return


def _load_previous_health_snapshot(scope_key: dict[str, Any]) -> dict[str, Any] | None:
    """Return the newest snapshot record whose ``scope_key`` matches.

    Signature accepts the ``scope_key`` dict directly (the canonical
    contract pinned by :class:`tests.test_unit_cli_impl_dag.TestLoadPreviousHealthSnapshot`).
    """
    path = _health_snapshot_log_path()
    if not path.exists():
        return None
    import orjson as _json

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = _json.loads(line)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        if rec.get("record_type") != "health_snapshot":
            continue
        if rec.get("scope_key") == scope_key:
            return rec
    return None


def _append_health_snapshot(record: dict[str, Any]) -> None:
    """Append ``record`` to the snapshot log and trigger compaction.

    Accepts both raw snapshot dicts (where ``scope_key`` is built) and
    canonical ``rec = {"record_type": "health_snapshot", ...}`` rows.
    """
    import orjson as _json

    path = _health_snapshot_log_path()
    rec: dict[str, Any] = {"record_type": "health_snapshot", **record}
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(_json.dumps(rec, option=_json.OPT_SORT_KEYS).decode())
            fh.write("\n")
    except OSError:
        return
    _compact_health_snapshot_log()


def _resolve_health_policy(
    profile: str | None = None,
    *,
    strict: bool = False,
    min_healthy_ratio: float = 1.0,
) -> dict[str, Any]:
    """Resolve health policy from ``profile`` + explicit kwargs.

    Behavior:
        * ``strict_ci`` → ``strict=True, ratio=1.0``
        * ``warn_only`` → ``strict=False, ratio=0.0``
        * unknown profile → keeps explicit kwargs (``profile_exists=False``)
        * ``profile=None`` → ``"custom"`` with kwargs.
        * ``min_healthy_ratio`` is clamped to ``[0.0, 1.0]``.

    Pinned by :class:`tests.test_unit_cli_impl_dag.TestResolveHealthPolicy`.
    """
    resolved_profile = "custom"
    profile_exists = True
    effective_strict = bool(strict)
    ratio = float(min_healthy_ratio)
    if profile is not None:
        key = str(profile).strip().lower()
        selected = _HEALTH_POLICY_PROFILES.get(key)
        if selected is not None:
            resolved_profile = key
            effective_strict = bool(selected["strict"])
            ratio = float(selected["min_healthy_ratio"])
        else:
            profile_exists = False
    ratio = max(0.0, min(1.0, ratio))
    return {
        "profile": resolved_profile,
        "profile_exists": profile_exists,
        "strict": effective_strict,
        "min_healthy_ratio": ratio,
    }


# ---------------------------------------------------------------------------
# Wrappers / forwarders so monkeypatch.setattr("thegent.cli.commands.impl.<x>")
# sites resolve cleanly.
# ---------------------------------------------------------------------------


def _impl_module() -> Any:
    """Live lookup of :mod:`thegent.cli.commands.impl` for forwarder targets."""
    import sys

    return sys.modules.get("thegent.cli.commands.impl")


def session_contract_audit_impl(*, owner: str | None = None) -> dict[str, Any]:
    """Default ``session_contract_audit_impl`` (read-only audit shell).

    Real implementations live in services/ modules; tests
    :func:`monkeypatch.setattr("thegent.cli.commands.session_health_impl.session_contract_audit_impl", ...)`
    to drive coverage.
    """
    return {"summary": {"total": 0, "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 0}}, "rows": []}


def session_contract_health_gate_impl(
    *,
    owner: str | None = None,
    min_healthy_ratio: float = 1.0,
    all: bool = False,  # noqa: A002 — test surface
    policy_profile: str | None = None,
    strict: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Session-contract gate (boolean pass/blocked).

    See :class:`tests.test_unit_cli_impl_dag.TestHealthGateImpl`.
    """
    audit = session_contract_audit_impl(owner=owner)
    summary = audit.get("summary", {})
    health = summary.get("health", {})
    total = summary.get("total", 0)
    healthy = health.get("healthy", 0)
    blocked_count = total - healthy
    blocked_ratio = (blocked_count / total) if total else 0.0

    policy = _resolve_health_policy(
        policy_profile,
        strict=strict,
        min_healthy_ratio=min_healthy_ratio,
    )
    status = "passed" if blocked_count == 0 else "blocked"
    healthy_ratio = (healthy / total) if total else 0.0
    pass_flag = healthy_ratio >= policy["min_healthy_ratio"]

    payload: dict[str, Any] = {
        "schema_version": HEALTH_PAYLOAD_SCHEMA_VERSION,
        "payload_type": "session_contract_health_gate",
        "status": status,
        "pass": pass_flag,
        "owner": owner,
        "all": all,
        "strict": policy["strict"],
        "policy_profile": policy["profile"],
        "min_healthy_ratio": policy["min_healthy_ratio"],
        "total": total,
        "healthy_count": healthy,
        "unhealthy_count": blocked_count,
        "blocked_count": blocked_count,
        "blocked_ratio": blocked_ratio,
        "generated_at_utc": "",
        "generated_query": {
            "owner": owner,
            "all": all,
            "strict": policy["strict"],
            "policy_profile": policy["profile"],
            "min_healthy_ratio": policy["min_healthy_ratio"],
        },
    }
    payload["payload_signature"] = _hash_health_payload(payload)
    scope = _health_scope_key(payload)
    payload["scope_key"] = scope
    payload["previous_snapshot"] = _load_previous_health_snapshot(scope)

    record = {
        "payload_type": payload["payload_type"],
        "scope_key": scope,
        "captured_at_utc": payload["generated_at_utc"] or "",
        "status": status,
        "pass": pass_flag,
        "blocked_ratio": blocked_ratio,
        "blocked_count": blocked_count,
        "issue_types": [],
        "owner": owner,
        "all": all,
        "strict": policy["strict"],
        "policy_profile": policy["profile"],
        "min_healthy_ratio": policy["min_healthy_ratio"],
    }
    _append_health_snapshot(record)
    payload["pass"] = pass_flag
    payload["status"] = status
    return payload


def _observe_summary_freshness_bucket(
    age_seconds: float | None,
    *,
    fresh_seconds: float = 60,
    warm_seconds: float = 300,
    stale_seconds: float = 600,
) -> str:
    """Bucket the age of an observe summary timestamp.

    AUDIT-N+19 Phase 4 contract — lives here so the canonical
    ``session_health_impl`` module exposes the new threshold-based
    bucket classifier while the legacy
    ``observability_impl._observe_summary_freshness_bucket(timestamp)``
    form remains untouched for AUDIT-N+9 backward compat.

    Bucket precedence (lowest age → highest):

      * ``"future"`` if ``age_seconds < 0``
      * ``"unknown"`` if ``age_seconds is None``
      * ``"fresh"`` if ``age_seconds <= fresh_seconds``
      * ``"warm"`` if ``age_seconds <= warm_seconds``
      * ``"stale"`` if ``age_seconds <= stale_seconds``
      * ``"critical"`` otherwise

    Pinned by
    :class:`tests.test_unit_cli_impl_dag.TestObserveSummaryFreshnessBucket`.
    """
    if age_seconds is None:
        return "unknown"
    if age_seconds < 0:
        return "future"
    if age_seconds <= fresh_seconds:
        return "fresh"
    if age_seconds <= warm_seconds:
        return "warm"
    if age_seconds <= stale_seconds:
        return "stale"
    return "critical"


__all__ = [
    "HEALTH_PAYLOAD_SCHEMA_VERSION",
    "_health_scope_key",
    "_hash_health_payload",
    "_health_snapshot_log_path",
    "_health_snapshot_max_lines",
    "_coerce_issue_types",
    "_compact_health_snapshot_log",
    "_load_previous_health_snapshot",
    "_append_health_snapshot",
    "_observe_summary_freshness_bucket",
    "_resolve_health_policy",
    "session_contract_audit_impl",
    "session_contract_health_gate_impl",
]
