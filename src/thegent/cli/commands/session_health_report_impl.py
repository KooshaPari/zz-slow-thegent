"""Session-contract health-report module (AUDIT-N+19 Phase 4).

Defines :func:`session_contract_health_report_impl` (full per-session
contract health audit + snapshot append) and the three serialization
helpers

  * :func:`_serialize_health_report_md`   — markdown
  * :func:`_serialize_health_report_csv`  — CSV
  * :func:`_serialize_health_report_jsonl` — JSONL

Pinned by :class:`tests.test_unit_cli_impl_dag.TestHealthReportImpl` +
`TestSerializeHealthReport`.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import orjson as _orjson

from thegent.cli.commands.session_health_impl import (  # noqa: F401  (re-exported)
    HEALTH_PAYLOAD_SCHEMA_VERSION,
    _append_health_snapshot,
    _coerce_issue_types,
    _compact_health_snapshot_log,
    _hash_health_payload,
    _health_scope_key,
    _health_snapshot_log_path,
    _health_snapshot_max_lines,
    _load_previous_health_snapshot,
    _resolve_health_policy,
    session_contract_audit_impl,
)


def session_contract_health_report_impl(
    *,
    owner: str | None = None,
    all: bool = False,  # noqa: A002 — test surface
    top_blocked: int = 25,
    policy_profile: str | None = None,
    strict: bool = False,
    min_healthy_ratio: float = 1.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the canonical session-contract health report.

    Returns the canonical payload expected by tests (status / pass /
    healthy_count / blocked_count / total / blocked_ratio /
    schema_version / payload_signature / payload_type=...).
    """
    audit = session_contract_audit_impl(owner=owner)
    summary = audit.get("summary", {}) or {}
    health = summary.get("health", {}) or {}
    total = summary.get("total", 0)
    healthy = health.get("healthy", 0)
    blocked_count = max(0, total - healthy)
    blocked_ratio = (blocked_count / total) if total else 0.0

    policy = _resolve_health_policy(
        policy_profile,
        strict=strict,
        min_healthy_ratio=min_healthy_ratio,
    )
    status = "passed" if blocked_count == 0 else "blocked"
    pass_flag = blocked_count == 0

    rows = audit.get("rows", []) or []
    issue_counts: dict[str, int] = {}
    top_blocked_rows: list[dict[str, Any]] = []
    for row in rows:
        if row.get("contract_health") in ("error", "warning"):
            issues = _coerce_issue_types(row.get("contract_issues", []))
            for issue in issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            top_blocked_rows.append(
                {
                    "session_id": row.get("session_id"),
                    "owner": row.get("owner"),
                    "state": row.get("contract_state"),
                    "health": row.get("contract_health"),
                    "issues": issues,
                    "remediation": [
                        "Ensure route_contract includes provider metadata at session creation.",
                    ],
                    "started_at_utc": row.get("started_at_utc", ""),
                    "agent": row.get("agent", ""),
                }
            )
    top_blocked_rows = sorted(
        top_blocked_rows,
        key=lambda r: r.get("started_at_utc", ""),
        reverse=True,
    )[: max(1, top_blocked)]

    payload: dict[str, Any] = {
        "schema_version": HEALTH_PAYLOAD_SCHEMA_VERSION,
        "schema_compat_mode": "compat",
        "payload_type": "session_contract_health_report",
        "status": status,
        "pass": pass_flag,
        "owner": owner,
        "all": all,
        "top_blocked": top_blocked,
        "policy_profile": policy["profile"],
        "strict": policy["strict"],
        "min_healthy_ratio": policy["min_healthy_ratio"],
        "total": total,
        "total_sessions": total,
        "healthy_count": healthy,
        "healthy_sessions": healthy,
        "unhealthy_count": blocked_count,
        "unhealthy_sessions": blocked_count,
        "blocked_count": blocked_count,
        "blocked_sessions": blocked_count,
        "blocked_sessions_count": blocked_count,
        "blocked_ratio": blocked_ratio,
        "top_blocked_count": len(top_blocked_rows),
        "strict_checks_enabled": policy["strict"],
        "health": health,
        "issue_counts": issue_counts,
        "issue_breakdown": [
            {"issue": k, "count": v} for k, v in sorted(issue_counts.items())
        ],
        "owner_breakdown": {
            (owner or "all"): {
                "total": total,
                "healthy": healthy,
                "warning": health.get("warning", 0),
                "error": health.get("error", 0),
                "missing": health.get("missing", 0),
            },
        },
        "top_blocked": top_blocked_rows,  # noqa: F601 (canonical key, same name as int field above)
        "generated_at_utc": "",
        "generated_query": {
            "owner": owner,
            "all": all,
            "strict": policy["strict"],
            "top_blocked": top_blocked,
            "policy_profile": policy["profile"],
            "min_healthy_ratio": policy["min_healthy_ratio"],
        },
        "compat": {"mode": "compat", "aliases": {}},
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
        "issue_types": sorted(issue_counts),
        "owner": owner,
        "all": all,
        "strict": policy["strict"],
        "policy_profile": policy["profile"],
        "min_healthy_ratio": policy["min_healthy_ratio"],
        "top_blocked": top_blocked,
    }
    _append_health_snapshot(record)
    payload["payload_signature"] = _hash_health_payload(
        {**payload, "payload_signature": {}}
    )
    return payload


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_health_report_md(report: dict[str, Any]) -> str:
    """Render ``report`` as markdown."""
    lines: list[str] = ["## Session Contract Health Report"]
    lines.append("")
    lines.append(f"- schema_version: `{report.get('schema_version', '')}`")
    lines.append(f"- payload_type: `{report.get('payload_type', '')}`")
    lines.append(f"- status: `{report.get('status', '')}`")
    lines.append(f"- total: `{report.get('total', 0)}`")
    lines.append(f"- healthy_count: `{report.get('healthy_count', 0)}`")
    lines.append(f"- blocked_count: `{report.get('blocked_count', 0)}`")
    lines.append(f"- blocked_ratio: `{report.get('blocked_ratio', 0.0)}`")
    top = report.get("top_blocked", []) or []
    if top:
        lines.append("")
        lines.append("### top_blocked")
        lines.append("")
        lines.append("| session_id | owner | state | health | issues |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in top:
            issues = ", ".join(_coerce_issue_types(row.get("issues", [])))
            lines.append(
                "| {sid} | {own} | {st} | {hl} | {issues} |".format(
                    sid=row.get("session_id", ""),
                    own=row.get("owner", ""),
                    st=row.get("state", ""),
                    hl=row.get("health", ""),
                    issues=issues,
                )
            )
    return "\n".join(lines) + "\n"


def _serialize_health_report_csv(report: dict[str, Any]) -> str:
    """Render ``report`` as a single-row CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    headers = [
        "schema_version",
        "payload_type",
        "status",
        "pass",
        "total",
        "healthy_count",
        "blocked_count",
        "blocked_ratio",
        "owner",
        "all",
        "strict",
        "policy_profile",
        "min_healthy_ratio",
        "top_blocked",
    ]
    writer.writerow(headers)
    writer.writerow(
        [
            report.get("schema_version", ""),
            report.get("payload_type", ""),
            report.get("status", ""),
            "true" if report.get("pass") else "false",
            report.get("total", 0),
            report.get("healthy_count", 0),
            report.get("blocked_count", 0),
            report.get("blocked_ratio", 0.0),
            report.get("owner", ""),
            "true" if report.get("all") else "false",
            "true" if report.get("strict") else "false",
            report.get("policy_profile", ""),
            report.get("min_healthy_ratio", 0.0),
            report.get("top_blocked", 0),
        ]
    )
    return buf.getvalue()


def _serialize_health_report_jsonl(report: dict[str, Any]) -> str:
    """Render ``report`` as JSONL (a single ``summary`` record)."""
    rec = {"record_type": "summary", **report}
    return _orjson.dumps(rec, option=_orjson.OPT_SORT_KEYS).decode() + "\n"


__all__ = [
    "session_contract_health_report_impl",
    "_serialize_health_report_md",
    "_serialize_health_report_csv",
    "_serialize_health_report_jsonl",
]
