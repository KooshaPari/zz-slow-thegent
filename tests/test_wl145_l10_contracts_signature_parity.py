"""WL145 — Contracts signature parity / regression pinning (FR-CTR-002, FR-CTR-006).

Pins public signatures and key semantics for the contracts package so any
accidental change to downstream contract surfaces is caught before release.
Backs up the WL144 export-parity lane with stricter version + signature locks.
"""

from __future__ import annotations

import inspect

import pytest

from thegent import contracts
from thegent.contracts import registry
from thegent.contracts.adapters import (
    ADAPTER_REGISTRY_VERSION,
    ADAPTERS,
    OutputAdapter,
    XMLOutputAdapter,
    get_adapter,
    register_adapter,
)
from thegent.contracts.parser import (
    CONTRACTS_PARSER_VERSION,
    IncrementalXMLParser,
    extract_tags,
    get_partial_state,
)

# ---------------------------------------------------------------------------
# Version pinning (FR-CTR-002)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContractsVersion:
    """Lock contract surface versions to detect accidental bumps."""

    def test_contracts_version_pinned(self) -> None:
        assert contracts.CONTRACTS_VERSION == "contracts-v1"

    def test_adapter_registry_version_pinned(self) -> None:
        assert ADAPTER_REGISTRY_VERSION == "adapters-v1"

    def test_parser_version_pinned(self) -> None:
        assert CONTRACTS_PARSER_VERSION == "parser-v1"

    def test_registry_version_pinned(self) -> None:
        assert registry.CONTRACTS_REGISTRY_VERSION == "registry-v1"


# ---------------------------------------------------------------------------
# Public surface signatures (FR-CTR-006)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAdaptersSignature:
    """Adapter public surface stays backward-compatible."""

    def test_adapters_dict_keys(self) -> None:
        assert "xml" in ADAPTERS
        assert isinstance(ADAPTERS["xml"], XMLOutputAdapter)

    def test_output_adapter_subclasses_count(self) -> None:
        subs = OutputAdapter.__subclasses__()
        assert XMLOutputAdapter in subs
        assert len(subs) >= 1

    def test_get_adapter_returns_xml(self) -> None:
        adapter = get_adapter("xml")
        assert isinstance(adapter, XMLOutputAdapter)

    def test_get_adapter_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            get_adapter("nonexistent-adapter")

    def test_register_adapter_function_is_callable(self) -> None:
        assert callable(register_adapter)


@pytest.mark.unit
class TestParserSignature:
    """Parser public surface stays backward-compatible."""

    def test_incremental_parser_constructor_signature(self) -> None:
        sig = inspect.signature(IncrementalXMLParser.__init__)
        params = list(sig.parameters)
        # The constructor takes ``case_sensitive`` (bool) and an
        # optional ``allowed_tags`` filter. Tests in
        # ``tests/test_unit_contracts.py`` predate this pinning test
        # and exercise ``allowed_tags``; WL145 freezes the exact
        # parameter list so future drift is caught.
        assert params == ["self", "case_sensitive", "allowed_tags"]

    def test_incremental_parser_methods(self) -> None:
        assert callable(IncrementalXMLParser.parse)
        assert callable(IncrementalXMLParser.get_partial_state)

    def test_extract_tags_signature(self) -> None:
        sig = inspect.signature(extract_tags)
        assert "text" in sig.parameters
        assert "tags" in sig.parameters

    def test_get_partial_state_alias(self) -> None:
        # get_partial_state is the module-level convenience alias
        assert get_partial_state is not None


# ---------------------------------------------------------------------------
# Semantic regression pins (FR-CTR-002)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestXMLOutputAdapterSemantic:
    """Pin key adapter behaviors that consumers depend on."""

    def test_pascalcase_task_update_maps_to_summary(self) -> None:
        # @trace FR-CTR-002 — Claude/Anthropic models emit PascalCase <TaskUpdate>.
        adapter = XMLOutputAdapter()
        payload = {"TaskUpdate": {"status": "in_progress", "summary": "Building"}}
        result = adapter.format(payload)
        assert result is not None
        text = str(result)
        assert "Building" in text

    def test_lowercase_summary_tag_supported(self) -> None:
        adapter = XMLOutputAdapter()
        payload = {"summary": "hello"}
        result = adapter.format(payload)
        text = str(result)
        assert "hello" in text

    def test_xml_format_returns_string(self) -> None:
        adapter = XMLOutputAdapter()
        result = adapter.format({"summary": "x"})
        assert isinstance(result, (str, bytes))


@pytest.mark.unit
class TestIncrementalParserSemantic:
    """Pin key parser semantics that telemetry downstream depends on."""

    def test_unclosed_tag_is_truncated(self) -> None:
        # @trace FR-CTR-002 — telemetry + output_parser both depend on this.
        parser_obj = IncrementalXMLParser()
        state = parser_obj.get_partial_state("<STATUS>working")
        assert state["is_truncated"] is True
        assert state["open_tag"] == "STATUS"

    def test_balanced_tags_not_truncated(self) -> None:
        parser_obj = IncrementalXMLParser()
        state = parser_obj.get_partial_state("<STATUS>ok</STATUS>")
        assert state["is_truncated"] is False

    def test_partial_content_captured(self) -> None:
        parser_obj = IncrementalXMLParser()
        state = parser_obj.get_partial_state("<STATUS>partial content here")
        assert "partial content here" in state["partial_content"]

    def test_nested_unclosed_reports_latest(self) -> None:
        # @trace FR-CTR-002 — telemetry downstream expects the LAST open tag.
        parser_obj = IncrementalXMLParser()
        state = parser_obj.get_partial_state("<OUTER><INNER>partial content")
        assert state["is_truncated"] is True
        assert state["open_tag"] == "INNER"

    def test_extract_tags_balanced(self) -> None:
        result = extract_tags("<STATUS>ok</STATUS><SUMMARY>done</SUMMARY>")
        assert result == {"STATUS": "ok", "SUMMARY": "done"}


# ---------------------------------------------------------------------------
# Back-compat: legacy re-exports from contracts.__init__ (FR-CTR-006)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContractsBackcompat:
    """Back-compat: __init__ re-exports required by downstream consumers."""

    def test_parser_module_re_exports(self) -> None:
        assert hasattr(contracts, "parser")
        assert hasattr(contracts, "IncrementalXMLParser")
        assert hasattr(contracts, "extract_tags")

    def test_adapters_module_re_exports(self) -> None:
        assert hasattr(contracts, "adapters")
        assert hasattr(contracts, "OutputAdapter")
        assert hasattr(contracts, "XMLOutputAdapter")
        assert hasattr(contracts, "register_adapter")

    def test_registry_module_re_exports(self) -> None:
        assert hasattr(contracts, "registry")
        assert hasattr(contracts, "CONTRACTS_REGISTRY_VERSION")

    def test_submodule_exports_listed_in_all(self) -> None:
        # @trace FR-CTR-006 — the canonical ROB-010 surface, the
        # legacy back-compat adapters + parser, and the modulo-level
        # registry submodule must all be declared in ``__all__`` so
        # ``from thegent.contracts import registry`` works
        # symmetrically with ``adapters`` and ``parser``. ``hasattr``
        # alone is not enough; the package-import machinery exposes
        # submodules as attributes regardless of ``__all__``, which
        # would let the asymmetry drift back unnoticed.
        assert "registry" in contracts.__all__
        assert "adapters" in contracts.__all__
        assert "parser" in contracts.__all__
