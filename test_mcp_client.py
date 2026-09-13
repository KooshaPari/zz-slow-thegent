"""Simple MCP client for testing thegent server. Handles SSE responses."""

import asyncio

import httpx
import orjson as json


async def _get_mcp_response(url: str, payload: dict, headers: dict, timeout: float = 15.0):
    """Wait for final result message in SSE stream."""
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload, headers=headers, timeout=timeout) as response:
            if response.status_code != 200:
                try:
                    return await response.json()
                except:
                    return {"error": "HTTP Error", "status": response.status_code}

            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    # Skip notifications unless it's the result
                    if "result" in data or "error" in data:
                        return data
                    # Also handle case where result is directly in the message
                    if "jsonrpc" in data and ("result" in data or "error" in data):
                        return data
            return {"error": "No result received before stream closed"}


async def test_mcp() -> None:
    url = "http://127.0.0.1:3847/mcp"
    headers = {"Accept": "application/json, text/event-stream"}

    # 1. List tools
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    await _get_mcp_response(url, payload, headers)

    # 2. Call thegent_list_agents
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "thegent_list_agents", "arguments": {}},
    }
    await _get_mcp_response(url, payload, headers)

    # 3. Call thegent_run
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "thegent_run", "arguments": {"agent": "gemini", "prompt": "echo Hello from FastMCP"}},
    }
    await _get_mcp_response(url, payload, headers, timeout=30.0)


if __name__ == "__main__":
    asyncio.run(test_mcp())
