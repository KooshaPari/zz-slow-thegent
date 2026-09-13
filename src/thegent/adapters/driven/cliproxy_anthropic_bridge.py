"""Anthropic /v1/messages ↔ OpenAI chat-completions bridge utilities.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

Covers GW-43 (request/response conversion), GW-44 (providerOptions.gateway
passthrough), GW-45 (special header forwarding), and the CacheControl
extractor shared with the header pipeline.
"""

from __future__ import annotations


def anthropic_messages_to_chat_completions(body: dict) -> dict:
    """Convert Anthropic /v1/messages request body to OpenAI chat completions format.

    Maps:
    - body["model"] -> body["model"] (unchanged)
    - body["messages"] -> body["messages"] (format is compatible)
    - body["max_tokens"] -> body["max_tokens"]
    - body["system"] string -> prepend {"role": "system", "content": system} to messages
    - body["stream"] -> body["stream"] (if present)
    - body["temperature"] -> body["temperature"] (if present)

    Returns a new dict in chat completions format.

    # @trace FR-REQEXT-043
    """
    result: dict = {}
    result["model"] = body.get("model", "")
    result["max_tokens"] = body.get("max_tokens", 1024)

    messages = list(body.get("messages", []))
    system = body.get("system")
    if system:
        messages = [{"role": "system", "content": system}] + messages
    result["messages"] = messages

    for key in ("stream", "temperature", "top_p", "stop"):
        if key in body:
            result[key] = body[key]

    return result


def anthropic_response_to_messages_format(response: dict) -> dict:
    """Convert OpenAI chat completions response to Anthropic /v1/messages format.

    Maps:
    - response["choices"][0]["message"]["content"] -> content[0]["text"]
    - response["model"] -> model
    - response["usage"]["prompt_tokens"] -> usage.input_tokens
    - response["usage"]["completion_tokens"] -> usage.output_tokens

    Returns dict in Anthropic messages format.

    # @trace FR-REQEXT-043
    """
    choices = response.get("choices", [])
    content_text = ""
    stop_reason = "end_turn"
    if choices:
        msg = choices[0].get("message", {})
        content_text = msg.get("content", "")
        fr = choices[0].get("finish_reason", "stop")
        stop_reason = "end_turn" if fr == "stop" else fr

    usage = response.get("usage", {})

    return {
        "id": response.get("id", ""),
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content_text}],
        "model": response.get("model", ""),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


# ---------------------------------------------------------------------------
# GW-44: Vercel providerOptions.gateway passthrough
# ---------------------------------------------------------------------------


def extract_provider_gateway_options(body: dict) -> dict:
    """Extract Vercel AI SDK providerOptions.gateway object (GW-44).

    Reads body.get("providerOptions", {}).get("gateway", {}).
    These control gateway behavior: cache, retry, timeout, etc.
    Returns empty dict if not present.

    # @trace FR-REQEXT-044
    """
    provider_options = body.get("providerOptions")
    if not isinstance(provider_options, dict):
        return {}
    gateway_options = provider_options.get("gateway")
    if not isinstance(gateway_options, dict):
        return {}
    return gateway_options


# ---------------------------------------------------------------------------
# GW-45: Forward special headers
# ---------------------------------------------------------------------------

_SPECIAL_FORWARD_HEADERS: frozenset[str] = frozenset(
    {
        "x-session-id",
        "x-request-id",
        "x-anthropic-beta",
        "x-stainless-os",
        "x-stainless-arch",
        "structured-outputs-2025-11-13",
    }
)


def extract_special_headers(request_headers: dict) -> dict[str, str]:
    """Extract special headers to forward to the backend (GW-45).

    Returns a dict of header_name -> value for headers in _SPECIAL_FORWARD_HEADERS
    that are present in request_headers.

    # @trace FR-REQEXT-045
    """
    return {k: v for k, v in request_headers.items() if k.lower() in _SPECIAL_FORWARD_HEADERS}
