"""Unified LLM Router using LiteLLM library.

This module provides a unified interface for routing LLM requests
to multiple providers using the LiteLLM library (already installed).

Replaces: litellm_router.py (1,017 LOC) + litellm_responses_handler.py (867 LOC)
Target: ~500 LOC unified router
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from litellm import acompletion, completion_cost
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    provider: str
    model_prefix: str
    api_key_env: str
    base_url: str | None = None
    max_retries: int = 3
    timeout: float = 60.0


# Provider configurations
PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig("openai", "gpt-4", "OPENAI_API_KEY"),
    "anthropic": ProviderConfig("anthropic", "claude-3", "ANTHROPIC_API_KEY"),
    "gemini": ProviderConfig("gemini", "gemini-1.5", "GEMINI_API_KEY"),
    "deepseek": ProviderConfig("deepseek", "deepseek-chat", "DEEPSEEK_API_KEY"),
    "openrouter": ProviderConfig("openrouter", "openrouter", "OPENROUTER_API_KEY"),
}


class LLMRouter:
    """Unified router for LLM providers using LiteLLM.

    Replaces the custom 1,884 LOC implementation with a ~200 LOC
    wrapper around the industry-standard LiteLLM library.

    Usage:
        router = LLMRouter()
        response = await router.route(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            provider="openai"
        )
    """

    def __init__(self) -> None:
        self._provider_configs = PROVIDERS
        self._fallback_chain: list[str] = ["openai", "anthropic", "gemini"]

    def get_model_string(self, provider: str, model: str) -> str:
        """Get the LiteLLM-compatible model string."""
        config = self._provider_configs.get(provider)
        if not config:
            return model  # Assume user passed full model string

        # Handle provider-specific prefixes
        if provider == "openrouter":
            return f"openrouter/{model}"
        return f"{config.provider}/{model}"

    def _get_api_key(self, provider: str) -> str | None:
        """Get API key from environment."""
        config = self._provider_configs.get(provider)
        if not config:
            return None
        return os.getenv(config.api_key_env)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def route(
        self,
        messages: list[dict[str, str]],
        model: str,
        provider: str = "openai",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Route a completion request to the specified provider.

        Uses tenacity for automatic retries with exponential backoff.
        All the complex retry logic from litellm_router.py is replaced
        by this single decorator.
        """
        model_string = self.get_model_string(provider, model)
        api_key = self._get_api_key(provider)

        if not api_key:
            raise ValueError(f"No API key found for provider: {provider}")

        try:
            if stream:
                return await acompletion(
                    model=model_string,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key,
                    stream=True,
                    **kwargs,
                )
            else:
                return await acompletion(
                    model=model_string,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key,
                    **kwargs,
                )
        except Exception:
            # Log and re-raise for tenacity retry
            raise

    async def route_with_fallback(
        self,
        messages: list[dict[str, str]],
        model: str,
        providers: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Route with automatic fallback to next provider on failure."""
        providers = providers or self._fallback_chain

        last_error = None
        for provider in providers:
            try:
                return await self.route(messages, model, provider, **kwargs)
            except Exception as e:
                last_error = e
                continue

        raise last_error or RuntimeError("All providers failed")

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request using LiteLLM's cost calculator."""
        try:
            return completion_cost(model=model, prompt=str(input_tokens), completion=str(output_tokens))
        except Exception:
            return 0.0  # Fallback if cost data unavailable


# Singleton instance for global use
_default_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    """Get or create the default LLM router instance."""
    global _default_router
    if _default_router is None:
        _default_router = LLMRouter()
    return _default_router


# Convenience function for simple routing
async def route_llm(
    messages: list[dict[str, str]],
    model: str = "gpt-4",
    provider: str = "openai",
    **kwargs: Any,
) -> Any:
    """Simple function to route an LLM request."""
    return await get_router().route(messages, model, provider, **kwargs)
