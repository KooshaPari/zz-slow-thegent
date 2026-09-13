from __future__ import annotations

from thegent.cli.commands import impl
from thegent.cli.services import run_post_surface_helpers


def test_wl125_resume_wrapper_delegates_with_reprompt_callback(monkeypatch) -> None:
    forwarded: dict[str, object] = {}
    send_calls: dict[str, object] = {}

    def _fake_resume_impl(**kwargs):
        forwarded.update(kwargs)
        ok, message = kwargs["session_send_impl"]("s-1", "continue")
        forwarded["send_result"] = (ok, message)
        return {"delegated": True}

    def _fake_session_send_impl(session_id: str, message: str, msg_type: str = "reprompt"):
        send_calls["session_id"] = session_id
        send_calls["message"] = message
        send_calls["msg_type"] = msg_type
        return True, "ok"

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_post_surface_helpers.resume_impl",
        _fake_resume_impl,
    )
    monkeypatch.setattr("thegent.cli.commands.impl.session_send_impl", _fake_session_send_impl)

    result = impl.resume_impl(session_id="s-1", prompt="continue", skills=["alpha"])

    assert result == {"delegated": True}
    assert forwarded["session_id"] == "s-1"
    assert forwarded["prompt"] == "continue"
    assert forwarded["skills"] == ["alpha"]
    assert forwarded["resolve_latest_session_id"] is impl._resolve_latest_session_id
    assert forwarded["session_state_path"] is impl._session_state_path
    assert forwarded["normalize_contract_string"] is impl._normalize_contract_string
    assert forwarded["send_result"] == (True, "ok")
    assert send_calls == {
        "session_id": "s-1",
        "message": "continue",
        "msg_type": "reprompt",
    }


def test_wl125_run_post_surface_list_agents_functional_backend_mapping(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        run_post_surface_helpers,
        "list_agent_names",
        lambda: ["cursor-agent", "codex", "custom"],
    )
    monkeypatch.setattr(run_post_surface_helpers, "AGENT_LABELS", {"cursor-agent": "cursor"})

    result = run_post_surface_helpers.list_agents_impl()

    assert result == [
        {"name": "cursor", "backend": "Direct"},
        {"name": "codex", "backend": "codex"},
        {"name": "custom", "backend": "Direct"},
    ]
