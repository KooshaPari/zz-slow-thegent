"""Unit tests for thegent.contracts.adapters -- XMLOutputAdapter, GenericOutputAdapter, registry."""

import pytest

from tests.conftest_factories import make_adapter_result, make_csm
from thegent.adapters.ports import PLUGIN_HOST, PluginHost, PluginInterface
from thegent.contracts.adapters import (
    ADAPTER_REGISTRY,
    AdapterResult,
    GenericOutputAdapter,
    OutputAdapter,
    XMLOutputAdapter,
    get_adapter,
    normalize_output,
    register_adapter,
)
from thegent.contracts.csm import CSMStatus
from thegent.contracts.validation import SemanticValidationError


@pytest.mark.unit
class TestAdapterResult:
    """Tests for AdapterResult dataclass."""

    def test_default_confidence(self) -> None:
        # @trace FR-CTR-003
        csm = make_csm()
        result = AdapterResult(csm=csm)
        assert result.confidence == 1.0

    def test_default_parse_errors_empty(self) -> None:
        # @trace FR-CTR-003
        csm = make_csm()
        result = AdapterResult(csm=csm)
        assert result.parse_errors == []

    def test_default_source_provider_empty(self) -> None:
        # @trace FR-CTR-003
        csm = make_csm()
        result = AdapterResult(csm=csm)
        assert result.source_provider == ""

    def test_custom_fields(self) -> None:
        # @trace FR-CTR-003
        result = make_adapter_result(
            confidence=0.8,
            parse_errors=["truncated"],
            source_provider="gemini",
        )
        assert result.confidence == 0.8
        assert result.parse_errors == ["truncated"]
        assert result.source_provider == "gemini"

    def test_csm_accessible(self) -> None:
        # @trace FR-CTR-003
        csm = make_csm(task_id="t1", status="COMPLETED", progress=1.0, summary="done")
        result = AdapterResult(csm=csm)
        assert result.csm.task_id == "t1"
        assert result.csm.status == CSMStatus.COMPLETED


@pytest.mark.unit
class TestXMLOutputAdapter:
    """Tests for XMLOutputAdapter.normalize()."""

    def test_provider_property(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("test-provider")
        assert adapter.provider == "test-provider"

    def test_normalize_simple_xml(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>completed</STATUS><SUMMARY>Task done</SUMMARY>"
        result = adapter.normalize(raw, context={"task_id": "t1", "run_id": "r1"})
        assert result.csm.status == CSMStatus.COMPLETED
        assert result.csm.summary == "Task done"
        assert result.source_provider == "copilot"

    def test_normalize_with_task_id_tag(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<TASK_ID>my-task</TASK_ID><STATUS>pending</STATUS>"
        result = adapter.normalize(raw)
        assert result.csm.task_id == "my-task"

    def test_normalize_done_maps_to_completed(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("gemini")
        raw = "<STATUS>done</STATUS><SUMMARY>finished</SUMMARY>"
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.COMPLETED

    def test_normalize_blocked_status(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("codex")
        raw = "<STATUS>blocked</STATUS>"
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.BLOCKED

    def test_normalize_cancelled_status(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("claude")
        raw = "<STATUS>cancelled</STATUS>"
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.CANCELLED

    def test_normalize_skipped_maps_to_cancelled(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("claude")
        raw = "<STATUS>skipped</STATUS>"
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.CANCELLED

    def test_normalize_progress_percentage(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>in_progress</STATUS><PROGRESS>75%</PROGRESS>"
        result = adapter.normalize(raw)
        assert result.csm.progress == pytest.approx(0.75)

    def test_normalize_progress_decimal(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>in_progress</STATUS><PROGRESS>0.5</PROGRESS>"
        result = adapter.normalize(raw)
        assert result.csm.progress == pytest.approx(0.5)

    def test_normalize_progress_over_one_normalized(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>in_progress</STATUS><PROGRESS>50</PROGRESS>"
        result = adapter.normalize(raw)
        assert result.csm.progress == pytest.approx(0.5)

    def test_normalize_progress_invalid_defaults(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>completed</STATUS><PROGRESS>n/a</PROGRESS><SUMMARY>ok</SUMMARY>"
        result = adapter.normalize(raw)
        assert result.csm.progress == pytest.approx(1.0)

    def test_normalize_no_xml_tags(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "just some plain text with no tags"
        result = adapter.normalize(raw)
        assert result.confidence == 0.0
        assert "no_xml_tags_detected" in result.parse_errors

    def test_normalize_truncated_xml(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>working on it"
        result = adapter.normalize(raw)
        assert result.confidence == 0.0
        assert "parse_truncated" in result.parse_errors

    def test_normalize_dict_input_with_stdout(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = {"stdout": "<STATUS>completed</STATUS><SUMMARY>ok</SUMMARY>"}
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.COMPLETED

    def test_normalize_dict_input_with_content(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = {"content": "<STATUS>failed</STATUS><ISSUES>disk full</ISSUES>"}
        result = adapter.normalize(raw)
        assert result.csm.status == CSMStatus.FAILED

    def test_normalize_actions_completed_split(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>completed</STATUS><SUMMARY>ok</SUMMARY><ACTIONS_COMPLETED>step1\nstep2</ACTIONS_COMPLETED>"
        result = adapter.normalize(raw)
        assert result.csm.actions_completed == ["step1", "step2"]

    def test_normalize_issues_split(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>failed</STATUS><ISSUES>issue1\nissue2</ISSUES>"
        result = adapter.normalize(raw)
        assert result.csm.issues == ["issue1", "issue2"]

    def test_normalize_next_steps_split(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>in_progress</STATUS><NEXT_STEPS>retry\nescalate</NEXT_STEPS><PROGRESS>0.5</PROGRESS>"
        result = adapter.normalize(raw)
        assert result.csm.next_steps == ["retry", "escalate"]

    def test_normalize_context_provides_run_id(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>pending</STATUS>"
        result = adapter.normalize(raw, context={"run_id": "run-42"})
        assert result.csm.run_id == "run-42"

    def test_normalize_source_contract_is_xml_tags(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("copilot")
        raw = "<STATUS>completed</STATUS><SUMMARY>ok</SUMMARY>"
        result = adapter.normalize(raw)
        assert result.csm.source_contract == "xml-tags"

    def test_implements_output_adapter_protocol(self) -> None:
        # @trace FR-CTR-003
        adapter = XMLOutputAdapter("test")
        assert isinstance(adapter, OutputAdapter)


@pytest.mark.unit
class TestAdapterRegistry:
    """Tests for adapter registry functions."""

    def test_get_adapter_registered(self) -> None:
        # @trace FR-CTR-005
        adapter = get_adapter("copilot")
        assert adapter is not None
        assert adapter.provider == "copilot"

    def test_get_adapter_unknown_raises(self) -> None:
        # @trace FR-CTR-005
        # Contract pinned by WL145 — unknown providers raise
        # ``KeyError`` so callers are forced to handle the
        # missing-adapter case explicitly. ``ADAPTER_REGISTRY.get``
        # is the None-returning variant for soft lookups.
        with pytest.raises(KeyError):
            get_adapter("nonexistent-provider-xyz")

    def test_register_custom_adapter(self) -> None:
        # @trace FR-CTR-005
        custom = XMLOutputAdapter("my-custom")
        register_adapter("my-custom", custom)
        assert get_adapter("my-custom") is custom
        # Clean up
        ADAPTER_REGISTRY.pop("my-custom", None)


@pytest.mark.unit
class TestNormalizeOutput:
    """Tests for the normalize_output convenience function."""

    def test_normalize_known_provider_with_xml(self) -> None:
        # @trace FR-CTR-005
        raw = "<STATUS>completed</STATUS><SUMMARY>All good</SUMMARY>"
        result = normalize_output("copilot", raw)
        assert result.csm.status == CSMStatus.COMPLETED

    def test_normalize_fallback_disabled_raises(self) -> None:
        # @trace FR-CTR-005
        raw = "no tags here"
        with pytest.raises(SemanticValidationError):
            normalize_output("copilot", raw, allow_fallback=False)

    def test_normalize_fallback_produces_csm(self) -> None:
        # @trace FR-CTR-005
        raw = "plain text no tags"
        result = normalize_output("copilot", raw, allow_fallback=True)
        assert result.csm.source_contract == "fallback-plain"
        assert result.confidence < 1.0


class DummyPlugin(PluginInterface):
    def __init__(self):
        self._initialized = False
        self._shutdown = False

    @property
    def name(self) -> str:
        return "dummy-plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    def initialize(self, config: dict) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown = True


class TestPluginHost:
    def test_plugin_host_lifecycle(self) -> None:
        assert isinstance(PLUGIN_HOST, PluginHost)

        plugin = DummyPlugin()

        PLUGIN_HOST.register_plugin(plugin)
        assert "dummy-plugin" in PLUGIN_HOST.list_plugins()

        PLUGIN_HOST.load_plugin("dummy-plugin")
        assert plugin._initialized is True

        loaded_plugin = PLUGIN_HOST.get_plugin("dummy-plugin")
        assert loaded_plugin is plugin

        PLUGIN_HOST.unload_plugin("dummy-plugin")
        assert plugin._shutdown is True

        # swap plugin
        plugin2 = DummyPlugin()
        PLUGIN_HOST.swap_plugin("dummy-plugin", plugin2)
        assert PLUGIN_HOST.get_plugin("dummy-plugin") is plugin2

        # cleanup
        PLUGIN_HOST.unload_plugin("dummy-plugin")


@pytest.mark.unit
class TestGenericOutputAdapter:
    """Tests for GenericOutputAdapter -- covers lines 153, 156-167."""

    def test_provider_property(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("test-provider")
        assert adapter.provider == "test-provider"

    def test_normalize_string_input(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize("Hello world output text")
        assert result.csm.status == CSMStatus.COMPLETED
        assert result.csm.source_contract == "plain"
        assert "Hello world" in result.csm.summary or result.csm.summary != ""

    def test_normalize_dict_input_with_content(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize({"content": "Dict content here"})
        assert result.csm.status == CSMStatus.COMPLETED
        assert result.csm.source_contract == "plain"

    def test_normalize_dict_input_with_text(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize({"text": "Text field value"})
        assert result.csm.status == CSMStatus.COMPLETED

    def test_normalize_dict_input_fallback(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize({"other": "no content or text key"})
        assert result.csm.status == CSMStatus.COMPLETED

    def test_normalize_with_context_run_id(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize(
            "output", context={"run_id": "r-42", "chunk_id": "c-7"}
        )
        assert result.csm.run_id == "r-42"
        assert result.csm.chunk_id == "c-7"

    def test_normalize_with_none_context(self) -> None:
        # @trace FR-CTR-003
        adapter = GenericOutputAdapter("plain")
        result = adapter.normalize("output", context=None)
        assert result.csm.run_id == ""
        assert result.csm.chunk_id == ""


@pytest.mark.unit
class TestNormalizeOutputAdapterException:
    """Tests for normalize_output adapter exception branch -- covers lines 233-234."""

    def test_normalize_adapter_exception_falls_back(self) -> None:
        # @trace FR-CTR-005
        from unittest.mock import MagicMock, patch

        broken_adapter = MagicMock()
        broken_adapter.normalize.side_effect = RuntimeError("adapter crashed")
        broken_adapter.provider = "copilot"

        with patch(
            "thegent.contracts.adapters.get_adapter", return_value=broken_adapter
        ):
            result = normalize_output("copilot", "some raw output", allow_fallback=True)
        assert result.csm.source_contract == "fallback-plain"

    def test_normalize_adapter_exception_no_fallback_raises(self) -> None:
        # @trace FR-CTR-005
        from unittest.mock import MagicMock, patch

        broken_adapter = MagicMock()
        broken_adapter.normalize.side_effect = RuntimeError("adapter crashed")
        broken_adapter.provider = "copilot"

        with patch(
            "thegent.contracts.adapters.get_adapter", return_value=broken_adapter
        ):
            with pytest.raises(SemanticValidationError):
                normalize_output("copilot", "raw", allow_fallback=False)


@pytest.mark.unit
class TestNormalizeOutputTruncatedReturn:
    """Tests for normalize_output returning parse_truncated result (line 232)."""

    def test_truncated_xml_returns_adapter_result(self) -> None:
        # @trace FR-CTR-005
        """Truncated XML returns adapter result instead of falling back (line 232)."""
        raw = "<STATUS>working on it"
        result = normalize_output("copilot", raw, allow_fallback=True)
        # The XMLOutputAdapter detects truncation and returns parse_truncated
        assert "parse_truncated" in result.parse_errors
