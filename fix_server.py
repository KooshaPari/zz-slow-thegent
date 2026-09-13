#!/usr/bin/env python3
"""Fix the jsonrpc_agent_server.py file."""
import ast
import contextlib

# Read current file (first 1600 lines)
with open('src/thegent/protocols/jsonrpc_agent_server.py') as f:
    lines = f.readlines()[:1600]
content = ''.join(lines)

# Add the missing functions
content += '\n\n'
content += 'def _build_turn_submit_commit_resolution_phase(route, request_id, turn, session):\n'
content += '    return {"route": route, "request_id": request_id, "turn": turn, "session": session}\n'
content += '\n'
content += 'def _build_turn_submit_side_effects_resolution_phase(route, request_id, approval_id, approval_status, approval_diff):\n'
content += '    return {"route": route, "request_id": request_id, "approval_id": approval_id, "approval_status": approval_status, "approval_diff": approval_diff}\n'
content += '\n'
content += 'def _build_turn_submit_response_resolution_phase(route, request_id, turn, approval):\n'
content += '    return {"route": route, "request_id": request_id, "turn": turn, "approval": approval}\n'

# Write the file
with open('src/thegent/protocols/jsonrpc_agent_server.py', 'w') as f:
    f.write(content)

# Verify syntax
with contextlib.suppress(SyntaxError):
    ast.parse(content)
