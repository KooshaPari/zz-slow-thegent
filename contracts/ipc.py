# IPC Contracts
# Part of thegent-contracts sub-project

from dataclasses import dataclass
from typing import Any


@dataclass
class IPCRequest:
    """IPC Request format."""

    request_id: str
    command: str
    payload: dict
    source: str


@dataclass
class IPCResponse:
    """IPC Response format."""

    request_id: str
    success: bool
    result: Any = None
    error: str | None = None


def create_request(command: str, payload: dict, source: str = "cli") -> IPCRequest:
    """Create an IPC request."""
    import uuid

    return IPCRequest(request_id=str(uuid.uuid4()), command=command, payload=payload, source=source)


def create_response(request_id: str, success: bool, result: Any = None, error: str | None = None) -> IPCResponse:
    """Create an IPC response."""
    return IPCResponse(request_id=request_id, success=success, result=result, error=error)
