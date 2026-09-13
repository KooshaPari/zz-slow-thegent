"""Model-list enrichment and proxy-model injection for /v1/models.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

Covers GW-46 (per-entry enrichment with context_length and supported_parameters)
and GW-47 (inject missing canonical proxy models).
"""

from __future__ import annotations


def enrich_model_entry(entry: dict) -> dict:
    """Enrich a /v1/models entry with context_length and supported_parameters (GW-46).

    Adds:
    - context_length: int (max input tokens)
    - supported_parameters: list of supported params

    Uses thegent.routing.model_metadata if available; returns entry unchanged if not.

    # @trace FR-REQEXT-046
    """
    try:
        from thegent.utils.routing_impl.model_metadata import (
            get_model_metadata,
            has_model_metadata,
        )

        model_id = entry.get("id", "")
        if not has_model_metadata(model_id):
            return entry
        meta = get_model_metadata(model_id)
        if meta is None:
            return entry
        result = dict(entry)
        ctx_len = meta.get("context_length")
        if ctx_len:
            result["context_length"] = ctx_len
        sup_params = meta.get("supported_parameters")
        if sup_params:
            result["supported_parameters"] = sup_params
        return result
    except Exception:
        return entry


def inject_proxy_models(models_list: list[dict]) -> list[dict]:
    """Inject proxy model entries for models that may be missing from the backend (GW-47).

    Adds entries for thegent-known canonical model aliases if not already present.
    This fixes "Model metadata not found" errors for models served through the proxy.

    # @trace FR-REQEXT-047
    """
    try:
        from thegent.utils.routing_impl.harness_model_mapping import (
            CANONICAL_TO_OPENROUTER,
        )

        existing_ids = {m.get("id", "") for m in models_list}
        result = list(models_list)
        for alias in CANONICAL_TO_OPENROUTER:
            if alias not in existing_ids:
                result.append(
                    {
                        "id": alias,
                        "object": "model",
                        "created": 0,
                        "owned_by": "thegent-proxy",
                    }
                )
        return result
    except Exception:
        return models_list
