"""OpenRouter attribution header injection helpers (OR-08).

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.
"""

from __future__ import annotations

# OR-08: App identification headers for OpenRouter attribution
_OPENROUTER_REFERER = "https://thegent.dev"
_OPENROUTER_TITLE = "thegent"


def _is_openrouter_backend(url: str) -> bool:
    """Return True when the backend URL targets OpenRouter."""
    return "openrouter.ai" in url


def _inject_openrouter_headers(headers: dict[str, str], backend_url: str) -> None:
    """OR-08: Inject HTTP-Referer and X-Title when routing to OpenRouter."""
    if _is_openrouter_backend(backend_url):
        headers.setdefault("HTTP-Referer", _OPENROUTER_REFERER)
        headers.setdefault("X-Title", _OPENROUTER_TITLE)
