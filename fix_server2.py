#!/usr/bin/env python3
# Read first 1258 lines
with open("src/thegent/protocols/jsonrpc_agent_server.py") as f:
    lines = f.readlines()[:1258]

content = "".join(lines)

# Add missing functions
content += """

def _build_turn_submit_commit_resolution_phase(route, request_id, turn, session):
    return {"route": route, "request_id": request_id, "turn": turn, "session": session}

def _build_turn_submit_side_effects_resolution_phase(route, request_id, approval_id, approval_status, approval_diff):
    return {"route": route, "request_id": request_id, "approval_id": approval_id, "approval_status": approval_status, "approval_diff": approval_diff}

def _build_turn_submit_response_resolution_phase(route, request_id, turn, approval):
    return {"route": route, "request_id": request_id, "turn": turn, "approval": approval}
"""

with open("src/thegent/protocols/jsonrpc_agent_server.py", "w") as f:
    f.write(content)
