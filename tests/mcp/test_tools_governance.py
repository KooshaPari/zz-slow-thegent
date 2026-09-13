from __future__ import annotations

import importlib.util
from pathlib import Path

import orjson as json


def _load_tools_governance_module() -> object:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "thegent"
        / "mcp"
        / "server"
        / "tools_governance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "thegent.mcp.server.tools_governance_test", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load tools_governance module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_json_content(content: object) -> dict[str, object]:
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and content:
        text = getattr(content[0], "text", None)
        if isinstance(text, str):
            return json.loads(text)
    raise TypeError(f"Unsupported ToolResult content type: {type(content)!r}")


def test_thegent_govern_vet_impl_wraps_service_result() -> None:
    tools_governance = _load_tools_governance_module()
    calls: list[dict[str, object]] = []

    def _stub(
        *,
        run_id: str,
        policy: str,
        session: str | None,
        dry_run: bool,
        org: str | None,
        project: str | None,
        environment: str | None,
        policy_id: str | None,
    ) -> dict[str, object]:
        calls.append(
            {
                "run_id": run_id,
                "policy": policy,
                "session": session,
                "dry_run": dry_run,
                "org": org,
                "project": project,
                "environment": environment,
                "policy_id": policy_id,
            }
        )
        return {"run_id": run_id, "policy": policy, "verdict": "approved", "checks": []}

    result = tools_governance.thegent_govern_vet_impl(
        run_id="run_123",
        policy="default",
        session="/tmp/session",
        dry_run=True,
        org="acme",
        project="thegent",
        environment="production",
        policy_id="vetter_default",
        govern_vet_impl=_stub,
    )

    assert calls == [
        {
            "run_id": "run_123",
            "policy": "default",
            "session": "/tmp/session",
            "dry_run": True,
            "org": "acme",
            "project": "thegent",
            "environment": "production",
            "policy_id": "vetter_default",
        }
    ]
    assert result.structured_content == {
        "run_id": "run_123",
        "policy": "default",
        "verdict": "approved",
        "checks": [],
    }
    assert _extract_json_content(result.content) == result.structured_content
    assert result.meta and result.meta["execution_time_ms"] >= 0


# noqa: PT018
