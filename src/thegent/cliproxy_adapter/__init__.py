"""Backward-compatible Cliproxy adapter package.

This package exists for compatibility with import paths expecting
`thegent.cliproxy_adapter`. It proxies to the legacy `cliproxy_adapter.py`
implementation and exposes the same public symbols.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_legacy_module() -> ModuleType:
    module_path = Path(__file__).resolve().parent.parent / "cliproxy_adapter.py"
    module_name = "thegent._cliproxy_adapter_impl"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load legacy cliproxy_adapter from {module_path}")

    module = importlib.util.module_from_spec(spec)
    # Add to sys.modules BEFORE exec_module to ensure dataclasses works correctly
    import sys

    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_legacy = _load_legacy_module()

# Re-export all symbols that callers may depend on
for symbol in [
    "_chat_completions_to_responses",
    "_map_model_for_backend",
    "_responses_to_chat_completions",
    "_transform_models_response",
    "_process_sse_line",
    "_proxy_stream",
    "_proxy_request",
    "_make_error_body",
    "_OR_PASSTHROUGH_FIELDS",
    "_compute_models_etag",
    "build_openrouter_passthrough_body",
    "inject_native_finish_reason",
    "normalize_finish_reason",
    "anthropic_messages_to_chat_completions",
    "anthropic_response_to_messages_format",
    "enrich_model_entry",
    "extract_provider_gateway_options",
    "extract_special_headers",
    "inject_proxy_models",
    "_TG_HEADER_NAMES",
    "create_adapter_app",
    "proxy_handler",
    "websocket_responses_handler",
    "CliproxyAdapter",
    "CacheControl",
    "TgHeaders",
    "extract_cache_control",
    "extract_tg_headers",
    "build_cache_response_headers",
    "build_cost_response_header",
    "inject_usage_cost",
    "generate_event_id",
    "build_event_id_header",
    "build_fallback_step_header",
    "TTFTTracker",
]:
    if hasattr(_legacy, symbol):
        globals()[symbol] = getattr(_legacy, symbol)
    else:
        # Provide stub for missing symbols
        globals()[symbol] = None


__all__ = [
    "_chat_completions_to_responses",
    "_map_model_for_backend",
    "_responses_to_chat_completions",
    "_transform_models_response",
    "_process_sse_line",
    "_proxy_stream",
    "_proxy_request",
    "_make_error_body",
    "_OR_PASSTHROUGH_FIELDS",
    "_compute_models_etag",
    "build_openrouter_passthrough_body",
    "inject_native_finish_reason",
    "normalize_finish_reason",
    "anthropic_messages_to_chat_completions",
    "anthropic_response_to_messages_format",
    "enrich_model_entry",
    "extract_provider_gateway_options",
    "extract_special_headers",
    "inject_proxy_models",
    "_TG_HEADER_NAMES",
    "create_adapter_app",
    "proxy_handler",
    "websocket_responses_handler",
    "CliproxyAdapter",
    "CacheControl",
    "TgHeaders",
    "extract_cache_control",
    "extract_tg_headers",
    "build_cache_response_headers",
    "build_cost_response_header",
    "inject_usage_cost",
    "generate_event_id",
    "build_event_id_header",
    "build_fallback_step_header",
    "TTFTTracker",
]
