"""AUDIT-N+27 — dormant-core observability shim-purity hardening parity.

This test pins the AUDIT-N+27 hand-off: the AUDIT-N+9 shim-purity contract
(``impl.py`` must NOT locally define any of the 22 moved helpers; they
live on :mod:`thegent.cli.commands.observability_impl` only) must continue
to hold **and** the 4 dual-mode helpers
(:func:`_resolve_audio_transcript_for_output`,
:func:`_resolve_grounding_sources_for_output`,
:func:`_build_audio_summary_metadata`,
:func:`_build_run_event_details`)
must dispatch the WL-116 / WL-119 / WL-125 forms cleanly through the
canonical :mod:`thegent.cli.services` modules without the impl-local
delegates that AUDIT-N+9 removed.

Specifically this test pins:

  1. ``observability_impl._resolve_audio_transcript_for_output`` is the
     canonical home for both the AUDIT-N+9 legacy ``(transcript)`` form
     and the WL-125 / WL-116 ``(injected_audio_transcript=..., result_audio_transcript=...)``
     form, and both forms return the expected values.
  2. ``observability_impl._resolve_grounding_sources_for_output`` is the
     canonical home for both the AUDIT-N+9 legacy ``(sources)`` form
     and the WL-119 ``(stdout=..., result_grounding_sources=...)`` form,
     and both forms return the expected values.
  3. ``impl._resolve_audio_transcript_for_output`` is identity-equal to
     ``observability_impl._resolve_audio_transcript_for_output`` (re-export
     shim contract).
  4. ``impl._resolve_grounding_sources_for_output`` is identity-equal to
     ``observability_impl._resolve_grounding_sources_for_output``.
  5. ``impl.py`` does NOT define ``_resolve_audio_transcript_for_output``,
     ``_resolve_grounding_sources_for_output``,
     ``_build_audio_summary_metadata``, or
     ``_build_run_event_details`` locally — only the re-export shim.
  6. WL-125 monkeypatch propagation: when
     ``monkeypatch.setattr("thegent.cli.commands.impl.run_event_helpers.resolve_audio_transcript_for_output", ...)``
     is applied, calls to ``observability_impl._resolve_audio_transcript_for_output``
     observe the patched value (proves the bridge delegates through
     ``impl.run_event_helpers`` which is identity-equal to
     ``thegent.cli.services.run_event_helpers``).
  7. WL-125 monkeypatch propagation for grounding sources:
     ``monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.resolve_grounding_sources_for_output", ...)``
     is observed.
  8. WL-125 monkeypatch propagation for audio summary metadata:
     ``monkeypatch.setattr("thegent.cli.commands.impl.run_audio_helpers.build_audio_summary_metadata", ...)``
     is observed.
  9. WL-125 monkeypatch propagation for run event details:
     ``monkeypatch.setattr("thegent.cli.commands.impl.run_event_helpers.build_run_event_details", ...)``
     is observed.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from thegent.cli.commands import impl, observability_impl
from thegent.cli.services import (
    run_audio_helpers,
    run_event_helpers,
    run_input_helpers,
)

# ---------------------------------------------------------------------------
# Module paths. Centralized so a future rename only touches one constant.
# ---------------------------------------------------------------------------

OBSERVABILITY_IMPL = "thegent.cli.commands.observability_impl"
IMPL = "thegent.cli.commands.impl"


def _load(module_path: str):  # type: ignore[no-untyped-def]
    return importlib.import_module(module_path)


# ---------------------------------------------------------------------------
# The 4 AUDIT-N+27 dual-mode helpers.
# ---------------------------------------------------------------------------

DUAL_MODE_HELPERS: tuple[str, ...] = (
    "_resolve_audio_transcript_for_output",
    "_resolve_grounding_sources_for_output",
    "_build_audio_summary_metadata",
    "_build_run_event_details",
)


# ---------------------------------------------------------------------------
# 1. observability_impl is the canonical home for the AUDIT-N+9 legacy form.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestObservabilityImplIsCanonicalHome:
    # @trace FR-AUDIT-N+27-001
    def test_resolve_audio_transcript_legacy_form(self) -> None:
        """AUDIT-N+9 legacy form: ``_resolve_audio_transcript_for_output(transcript)``
        returns ``{"transcript": ..., "duration": ...}``."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            {"text": "hello world", "duration": 1.5}
        )
        assert result == {"transcript": "hello world", "duration": 1.5}

    # @trace FR-AUDIT-N+27-002
    def test_resolve_audio_transcript_wl116_form(self) -> None:
        """WL-116 form: ``_resolve_audio_transcript_for_output(injected_audio_transcript=..., result_audio_transcript=...)``
        returns ``str`` (``result_audio_transcript`` wins per
        :func:`run_event_helpers.resolve_audio_transcript_for_output`)."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript="from-input-file",
            result_audio_transcript="from-runner",
        )
        assert result == "from-runner"

    # @trace FR-AUDIT-N+27-003
    def test_resolve_audio_transcript_wl116_only_injected(self) -> None:
        """WL-116 form: only ``injected_audio_transcript`` supplied returns
        that string."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript="from-input-file",
            result_audio_transcript=None,
        )
        assert result == "from-input-file"

    # @trace FR-AUDIT-N+27-004
    def test_resolve_audio_transcript_wl116_only_result(self) -> None:
        """WL-116 form: only ``result_audio_transcript`` supplied returns
        that string."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript=None,
            result_audio_transcript="from-runner",
        )
        assert result == "from-runner"

    # @trace FR-AUDIT-N+27-005
    def test_resolve_audio_transcript_wl116_via_kwargs(self) -> None:
        """WL-125 form via ``**kwargs``: the kwargs are recognised the
        same way as explicit kwargs."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript="from-input-file",
            result_audio_transcript="from-runner",
        )
        assert result == "from-runner"

    # @trace FR-AUDIT-N+27-006
    def test_resolve_grounding_sources_legacy_form(self) -> None:
        """AUDIT-N+9 legacy form: ``_resolve_grounding_sources_for_output(sources)``
        returns ``[{"source": ..., "content": ...[:100]}, ...]``."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_grounding_sources_for_output(
            [{"source": "doc.md", "content": "x" * 250}]
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["source"] == "doc.md"
        assert len(result[0]["content"]) == 100  # legacy 100-char slice

    # @trace FR-AUDIT-N+27-007
    def test_resolve_grounding_sources_wl119_form(self) -> None:
        """WL-119 form: ``_resolve_grounding_sources_for_output(stdout=..., result_grounding_sources=...)``
        delegates to ``run_input_helpers.resolve_grounding_sources_for_output``
        and returns the deduped URL list (structured result wins)."""
        obs = _load(OBSERVABILITY_IMPL)
        # When result_grounding_sources is provided as a list, it returns
        # that list (deduped). The stdout is ignored when structured result
        # is present.
        result = obs._resolve_grounding_sources_for_output(
            stdout="some stdout text containing url1 url2",
            result_grounding_sources=["https://a.example.com", "https://b.example.com"],
        )
        assert isinstance(result, list)
        assert "https://a.example.com" in result
        assert "https://b.example.com" in result

    # @trace FR-AUDIT-N+27-008
    def test_resolve_grounding_sources_wl119_only_stdout(self) -> None:
        """WL-119 form: when only ``stdout`` is supplied, the helper
        delegates to ``run_input_helpers.resolve_grounding_sources_for_output``
        which scans the stdout for URLs."""
        obs = _load(OBSERVABILITY_IMPL)
        # The service helper extracts URLs from the stdout text.
        result = obs._resolve_grounding_sources_for_output(
            stdout="Visit https://example.com/foo for details",
            result_grounding_sources=None,
        )
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 2. Dual-mode bridge: positional vs kwarg detection works correctly.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDualModeBridgeDetection:
    # @trace FR-AUDIT-N+27-009
    def test_audio_transcript_positional_dict_returns_legacy(self) -> None:
        """A positional dict triggers the AUDIT-N+9 legacy form."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            {"text": "hi", "duration": 0.5}
        )
        assert isinstance(result, dict)
        assert result == {"transcript": "hi", "duration": 0.5}

    # @trace FR-AUDIT-N+27-010
    def test_audio_transcript_kwarg_only_returns_string(self) -> None:
        """A kwarg-only call triggers the WL-116/WL-125 form and returns
        a ``str | None`` (not a dict)."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript="from-input-file"
        )
        assert isinstance(result, str)
        assert result == "from-input-file"

    # @trace FR-AUDIT-N+27-011
    def test_audio_transcript_none_args_returns_none_legacy(self) -> None:
        """No args at all triggers the AUDIT-N+9 legacy form (empty dict
        input → empty dict output, not None)."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output()
        assert isinstance(result, dict)
        assert result == {"transcript": "", "duration": 0.0}

    # @trace FR-AUDIT-N+27-012
    def test_grounding_sources_no_args_returns_empty_list(self) -> None:
        """No args → empty list (legacy form, empty sources)."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_grounding_sources_for_output()
        assert result == []

    # @trace FR-AUDIT-N+27-013
    def test_grounding_sources_positional_list_returns_legacy(self) -> None:
        """Positional list triggers the AUDIT-N+9 legacy form."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_grounding_sources_for_output(
            [{"source": "a", "content": "b"}]
        )
        assert isinstance(result, list)
        assert result[0]["source"] == "a"
        assert result[0]["content"] == "b"


# ---------------------------------------------------------------------------
# 3. Identity: impl.<name> re-export === observability_impl.<name>.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplReExportIdentity:
    # @trace FR-AUDIT-N+27-014
    def test_impl_resolve_audio_transcript_is_observability(self) -> None:
        assert (
            impl._resolve_audio_transcript_for_output
            is observability_impl._resolve_audio_transcript_for_output
        )

    # @trace FR-AUDIT-N+27-015
    def test_impl_resolve_grounding_sources_is_observability(self) -> None:
        assert (
            impl._resolve_grounding_sources_for_output
            is observability_impl._resolve_grounding_sources_for_output
        )

    # @trace FR-AUDIT-N+27-016
    def test_impl_build_audio_summary_metadata_is_observability(self) -> None:
        assert (
            impl._build_audio_summary_metadata
            is observability_impl._build_audio_summary_metadata
        )

    # @trace FR-AUDIT-N+27-017
    def test_impl_build_run_event_details_is_observability(self) -> None:
        assert (
            impl._build_run_event_details is observability_impl._build_run_event_details
        )

    # @trace FR-AUDIT-N+27-018
    def test_all_dual_mode_helpers_module_is_observability_impl(self) -> None:
        """Each dual-mode helper must have ``__module__ == observability_impl`` —
        proves the function is *defined* there, not just re-exported."""
        for name in DUAL_MODE_HELPERS:
            fn = getattr(observability_impl, name)
            assert fn.__module__ == OBSERVABILITY_IMPL, (
                f"{name}.__module__ != observability_impl (got {fn.__module__!r})"
            )


# ---------------------------------------------------------------------------
# 4. Shim purity: impl.py must NOT locally define any dual-mode helper.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplShimPurity:
    # @trace FR-AUDIT-N+27-019
    def test_impl_module_has_no_def_for_dual_mode_helpers(self) -> None:
        """impl.py must NOT define any dual-mode helper locally — only
        the re-export shim binds them to ``observability_impl``."""
        impl_src = inspect.getsource(_load(IMPL))
        for name in DUAL_MODE_HELPERS:
            assert f"def {name}(" not in impl_src, (
                f"impl.py must not define {name} locally — it's a re-export shim"
            )

    # @trace FR-AUDIT-N+27-020
    def test_impl_module_reexports_all_dual_mode_helpers(self) -> None:
        """impl.py must still re-export all 4 dual-mode helpers."""
        impl_mod = _load(IMPL)
        for name in DUAL_MODE_HELPERS:
            assert hasattr(impl_mod, name), f"impl.py missing re-export for {name}"

    # @trace FR-AUDIT-N+27-021
    def test_impl_reexport_block_present(self) -> None:
        """impl.py must still contain the AUDIT-N+9 re-export marker."""
        impl_src = inspect.getsource(_load(IMPL))
        assert "AUDIT-N+9: re-export observability surface" in impl_src


# ---------------------------------------------------------------------------
# 5. WL-125 monkeypatch propagation: patch sites resolve cleanly.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWL125MonkeypatchPropagation:
    # @trace FR-AUDIT-N+27-022
    def test_run_event_helpers_import_via_impl_is_identity(self) -> None:
        """``impl.run_event_helpers`` must be the same module object as
        ``thegent.cli.services.run_event_helpers`` so the WL-125 patch
        site resolves."""
        assert impl.run_event_helpers is run_event_helpers

    # @trace FR-AUDIT-N+27-023
    def test_run_audio_helpers_import_via_impl_is_identity(self) -> None:
        assert impl.run_audio_helpers is run_audio_helpers

    # @trace FR-AUDIT-N+27-024
    def test_run_input_helpers_import_via_impl_is_identity(self) -> None:
        assert impl.run_input_helpers is run_input_helpers

    # @trace FR-AUDIT-N+27-025
    def test_wl125_audio_transcript_monkeypatch_observed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patching ``impl.run_event_helpers.resolve_audio_transcript_for_output``
        is observed by ``observability_impl._resolve_audio_transcript_for_output``
        (proves the bridge delegates through the same module object)."""
        sentinel = "patched-transcript"

        def _patched(**kwargs):  # type: ignore[no-untyped-def]
            return sentinel

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_event_helpers.resolve_audio_transcript_for_output",
            _patched,
        )
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            injected_audio_transcript="from-input-file",
            result_audio_transcript="from-runner",
        )
        assert result == sentinel

    # @trace FR-AUDIT-N+27-026
    def test_wl125_grounding_sources_monkeypatch_observed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patching ``impl.run_input_helpers.resolve_grounding_sources_for_output``
        is observed by ``observability_impl._resolve_grounding_sources_for_output``."""
        sentinel = ["https://patched.example.com"]

        def _patched(*args, **kwargs):  # type: ignore[no-untyped-def]
            return sentinel

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_input_helpers.resolve_grounding_sources_for_output",
            _patched,
        )
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_grounding_sources_for_output(
            stdout="some stdout text",
            result_grounding_sources=["https://real.example.com"],
        )
        assert result == sentinel

    # @trace FR-AUDIT-N+27-027
    def test_wl125_audio_metadata_monkeypatch_observed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patching ``impl.run_audio_helpers.build_audio_summary_metadata``
        is observed by ``observability_impl._build_audio_summary_metadata``."""
        sentinel = {"patched": True}

        def _patched(**kwargs):  # type: ignore[no-untyped-def]
            return sentinel

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_audio_helpers.build_audio_summary_metadata",
            _patched,
        )
        obs = _load(OBSERVABILITY_IMPL)
        # WL-125 form (kwargs): triggers the delegation path.
        result = obs._build_audio_summary_metadata(
            audio_transcript="hello", audio_sources=[]
        )
        assert result == sentinel

    # @trace FR-AUDIT-N+27-028
    def test_wl125_run_event_details_monkeypatch_observed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patching ``impl.run_event_helpers.build_run_event_details``
        is observed by ``observability_impl._build_run_event_details``."""
        sentinel = {"patched": True}

        def _patched(**kwargs):  # type: ignore[no-untyped-def]
            return sentinel

        monkeypatch.setattr(
            "thegent.cli.commands.impl.run_event_helpers.build_run_event_details",
            _patched,
        )
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._build_run_event_details(
            grounding_sources=[],
            audio_transcript=None,
            audio_sources=None,
            context_usage_ratio=0.5,
        )
        assert result == sentinel


# ---------------------------------------------------------------------------
# 6. AUDIT-N+9 contract preserved: legacy observability surface intact.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAuditN9ContractPreserved:
    # @trace FR-AUDIT-N+27-029
    def test_legacy_audio_metadata_round_trip_still_works(self) -> None:
        """The AUDIT-N+9 round-trip test
        (``tests/test_unit_audit_n9_observability_impl_extraction_parity.py::TestObservabilityRoundTrip::test_audio_metadata_then_time_constraint_then_run_event``)
        pins ``_build_audio_summary_metadata(12.5, "wav")`` → legacy
        ``{"duration": 12.5, "format": "wav", "sample_rate": 16000}`` form.
        AUDIT-N+27 must preserve that legacy form."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._build_audio_summary_metadata(12.5, "wav")
        assert result["duration"] == 12.5
        assert result["format"] == "wav"
        assert result["sample_rate"] == 16000

    # @trace FR-AUDIT-N+27-030
    def test_legacy_run_event_details_round_trip_still_works(self) -> None:
        """The AUDIT-N+9 round-trip test pins
        ``_build_run_event_details({"type": "tool_call", "name": "read_logs"})``
        → ``{"event": ..., "timestamp": float}`` form. AUDIT-N+27 must
        preserve it."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._build_run_event_details(
            {"type": "tool_call", "name": "read_logs"}
        )
        assert result["event"]["type"] == "tool_call"
        assert "timestamp" in result
        assert isinstance(result["timestamp"], float)

    # @trace FR-AUDIT-N+27-031
    def test_legacy_audio_transcript_round_trip_still_works(self) -> None:
        """The AUDIT-N+9 round-trip test pins
        ``_resolve_audio_transcript_for_output({"text": "hello world", "duration": 1.5})``
        → ``{"transcript": "hello world", "duration": 1.5}`` form. AUDIT-N+27
        must preserve it."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_audio_transcript_for_output(
            {"text": "hello world", "duration": 1.5}
        )
        assert result == {"transcript": "hello world", "duration": 1.5}

    # @trace FR-AUDIT-N+27-032
    def test_legacy_grounding_sources_round_trip_still_works(self) -> None:
        """The AUDIT-N+9 round-trip test pins
        ``_resolve_grounding_sources_for_output([{"source": "doc.md", "content": "x" * 250}])``
        → ``[{"source": "doc.md", "content": "x" * 100}]`` form. AUDIT-N+27
        must preserve it."""
        obs = _load(OBSERVABILITY_IMPL)
        result = obs._resolve_grounding_sources_for_output(
            [{"source": "doc.md", "content": "x" * 250}]
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["source"] == "doc.md"
        assert len(result[0]["content"]) == 100
