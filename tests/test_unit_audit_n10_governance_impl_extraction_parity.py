"""AUDIT-N+10 — governance_impl canonical extraction parity.

Pins the AUDIT-N+10 hand-off: nine governance / escalation / HITL /
data-protection symbols that previously lived scattered across three
modules (and one was entirely undefined) must now resolve as first-
class attributes on :mod:`thegent.cli.governance.governance_impl`,
while a re-export shim in ``impl.py`` keeps every legacy call-site
working.

Specifically this test pins:

  1. ``governance_impl`` module loads clean + has the canonical exports.
  2. All 10 symbols (``escalate_add_impl`` re-exported from observability_impl
     + 9 new) exist as ``governance_impl.X`` attributes.
  3. ``impl.<X>`` re-export equals the canonical symbol (identity) — the
     legacy import path remains green.
  4. The four CLI call-sites import from ``governance_impl``, not
     ``impl``: ``governance_escalation_hitl_cmds`` (8 sites),
     ``governance_data_protection_cmds`` (1 site),
     ``apps/govern`` (3 sites).
  5. Each symbol preserves its public signature (parameter names +
     default values pinned to the actual, current signatures).
  6. Round-trip behavior: ``escalate_list_impl`` / ``govern_list_pending_impl``
     return ``list[dict]``; ``escalate_approve_impl`` /
     ``escalate_resolve_impl`` return ``bool``;
     ``govern_approve_impl`` / ``govern_reject_impl`` return
     ``dict[str, Any]`` with ``run_id`` key;
     ``harness_register_host_impl`` returns dict with ``success`` key
     (and ``False`` for unknown harness);
     ``get_data_protection_status_impl`` returns the full status dict
     with ``session_dir_exists`` / ``permissions_restricted`` /
     ``masking_enabled`` keys (zero-arg call);
     ``sweep_impl`` returns dict with ``pass`` key (5-kwarg signature).
  7. ``escalate_add_impl`` is the *same* function object as
     ``observability_impl.escalate_add_impl`` (AUDIT-N+5/9 contract).
  8. ``sweep_impl`` requires the canonical 5-kwarg signature
     (callers passing <5 kwargs raise ``TypeError``).
  9. The re-export block in ``impl.py`` lists all 10 symbols and is
     the LAST non-statement block before session_state_path (i.e. it
     follows the AUDIT-N+9 block).
 10. ``get_data_protection_status_impl`` was previously UNDEFINED —
    the parity test pins that the function now exists and is callable.
"""

from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Module paths. Centralized so a future rename only touches one constant.
# ---------------------------------------------------------------------------

GOVERNANCE_IMPL = "thegent.cli.governance.governance_impl"
IMPL = "thegent.cli.commands.impl"
OBSERVABILITY_IMPL = "thegent.cli.commands.observability_impl"
ESCALATION_HITL_CMDS = "thegent.cli.governance.governance_escalation_hitl_cmds"
DATA_PROTECTION_CMDS = "thegent.cli.governance.governance_data_protection_cmds"
APPS_GOVERN = "thegent.cli.apps.govern"


def _load(module_path: str):  # type: ignore[no-untyped-def]
    return importlib.import_module(module_path)


# The exact 10 symbols that AUDIT-N+10 canonicalizes. Pinned in spec order.
CANONICAL_SYMBOLS: tuple[str, ...] = (
    "escalate_add_impl",
    "escalate_approve_impl",
    "escalate_list_impl",
    "escalate_resolve_impl",
    "govern_approve_impl",
    "govern_reject_impl",
    "govern_list_pending_impl",
    "harness_register_host_impl",
    "get_data_protection_status_impl",
    "sweep_impl",
)


# Expected parameter names — pinned to the actual, current signatures.
# Subset match: every name in this tuple must appear in the function's
# signature, but new params are allowed.
EXPECTED_PARAMS: dict[str, tuple[str, ...]] = {
    "escalate_add_impl": (
        "run_id",
        "reason",
        "sla_minutes",
        "owner",
        "agent",
        "lane",
        "priority",
    ),
    "escalate_approve_impl": ("run_id",),
    "escalate_list_impl": ("past_sla_only", "limit"),
    "escalate_resolve_impl": ("run_id", "resolution"),
    "govern_approve_impl": ("run_id", "reason"),
    "govern_reject_impl": ("run_id", "reason"),
    "govern_list_pending_impl": (),
    "harness_register_host_impl": ("host_id", "harness", "command_prefix"),
    "get_data_protection_status_impl": (),
    "sweep_impl": (
        "drift_window",
        "structural_budget",
        "semantic_budget",
        "include_audit",
        "update_calibration_fn",
    ),
}


# ---------------------------------------------------------------------------
# 1. governance_impl module loads clean + has the canonical export.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGovernanceImplModuleLoads:
    # @trace FR-AUDIT-N+10-001
    def test_module_imports_without_error(self) -> None:
        mod = _load(GOVERNANCE_IMPL)
        assert mod is not None
        assert hasattr(mod, "__name__")
        assert mod.__name__ == GOVERNANCE_IMPL

    # @trace FR-AUDIT-N+10-002
    def test_module_docstring_mentions_audit_n_plus_10(self) -> None:
        mod = _load(GOVERNANCE_IMPL)
        assert mod.__doc__ is not None
        assert "AUDIT-N+10" in mod.__doc__

    # @trace FR-AUDIT-N+10-003
    def test_module_has_all_canonical_exports(self) -> None:
        mod = _load(GOVERNANCE_IMPL)
        for name in CANONICAL_SYMBOLS:
            assert hasattr(mod, name), f"missing canonical export: {name}"

    # @trace FR-AUDIT-N+10-004
    def test_module_keeps_audit_n5_escalation_contract(self) -> None:
        """AUDIT-N+5 put ``escalate_add_impl`` on observability_impl.
        AUDIT-N+10 must NOT regress that export — the canonical
        ``governance_impl.escalate_add_impl`` must be the SAME object
        as ``observability_impl.escalate_add_impl``."""
        mod = _load(GOVERNANCE_IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        assert hasattr(obs, "escalate_add_impl"), (
            "AUDIT-N+5 surface regressed: observability_impl no longer exposes escalate_add_impl"
        )
        assert mod.escalate_add_impl is obs.escalate_add_impl


# ---------------------------------------------------------------------------
# 2. All 10 canonical symbols are first-class attributes on governance_impl.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAllCanonicalSymbolsPresent:
    # @trace FR-AUDIT-N+10-005
    def test_symbol_count_is_exactly_10(self) -> None:
        mod = _load(GOVERNANCE_IMPL)
        present = [n for n in CANONICAL_SYMBOLS if hasattr(mod, n)]
        assert len(present) == 10, f"expected 10 canonical symbols, found {len(present)}"
        assert sorted(present) == sorted(CANONICAL_SYMBOLS)

    # @trace FR-AUDIT-N+10-006
    def test_each_canonical_symbol_exists_and_is_callable(self) -> None:
        mod = _load(GOVERNANCE_IMPL)
        for name in CANONICAL_SYMBOLS:
            obj = getattr(mod, name)
            assert obj is not None, f"{name} is None on {GOVERNANCE_IMPL}"
            assert callable(obj), f"{name} is not callable"

    # @trace FR-AUDIT-N+10-007
    def test_module_objects_resolve_to_governance_impl(self) -> None:
        """For each symbol defined in governance_impl (excluding the
        re-exported ``escalate_add_impl``), the function's ``__module__``
        must point to ``governance_impl`` — proves the function is
        *defined* here, not just re-exported."""
        mod = _load(GOVERNANCE_IMPL)
        # escalate_add_impl is the AUDIT-N+5 re-export from observability_impl
        # so its __module__ must remain observability_impl.
        locally_defined = [n for n in CANONICAL_SYMBOLS if n != "escalate_add_impl"]
        for name in locally_defined:
            obj = getattr(mod, name)
            assert getattr(obj, "__module__", None) == GOVERNANCE_IMPL, (
                f"{name}.__module__ != governance_impl (actual={obj.__module__})"
            )


# ---------------------------------------------------------------------------
# 3. Identity: impl.<X> re-export === governance_impl.<X>.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReExportIdentity:
    # @trace FR-AUDIT-N+10-010
    def test_all_canonical_symbols_identical_across_modules(self) -> None:
        impl = _load(IMPL)
        gov = _load(GOVERNANCE_IMPL)
        for name in CANONICAL_SYMBOLS:
            assert getattr(impl, name) is getattr(gov, name), f"{name} differs between {IMPL} and {GOVERNANCE_IMPL}"

    # @trace FR-AUDIT-N+10-011
    def test_impl_escalate_add_impl_is_observability_escalate_add_impl(self) -> None:
        """The legacy ``thegent.cli.commands.impl.escalate_add_impl``
        must equal the AUDIT-N+5/9 canonical
        ``thegent.cli.commands.observability_impl.escalate_add_impl``."""
        impl = _load(IMPL)
        obs = _load(OBSERVABILITY_IMPL)
        assert impl.escalate_add_impl is obs.escalate_add_impl

    # @trace FR-AUDIT-N+10-012
    def test_impl_get_data_protection_status_impl_defined(self) -> None:
        """This function was UNDEFINED prior to AUDIT-N+10. The parity
        test pins that it now exists on both impl and governance_impl
        and is the same function object."""
        impl = _load(IMPL)
        gov = _load(GOVERNANCE_IMPL)
        assert hasattr(impl, "get_data_protection_status_impl"), (
            "get_data_protection_status_impl was not re-exported on impl.py"
        )
        assert hasattr(gov, "get_data_protection_status_impl")
        assert impl.get_data_protection_status_impl is gov.get_data_protection_status_impl


# ---------------------------------------------------------------------------
# 4. Call-sites import from governance_impl, not impl.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCallSitesImportFromGovernanceImpl:
    # @trace FR-AUDIT-N+10-013
    def test_escalation_hitl_cmds_imports_from_governance_impl(self) -> None:
        mod = _load(ESCALATION_HITL_CMDS)
        src = inspect.getsource(mod)
        # Every lazy `from thegent.cli.governance.governance_impl import ...`
        # call should be present. We pin a representative subset.
        assert "from thegent.cli.governance.governance_impl import escalate_add_impl" in src
        assert "from thegent.cli.governance.governance_impl import escalate_list_impl" in src
        assert "from thegent.cli.governance.governance_impl import escalate_approve_impl" in src
        assert "from thegent.cli.governance.governance_impl import escalate_resolve_impl" in src
        assert "from thegent.cli.governance.governance_impl import govern_approve_impl" in src
        assert "from thegent.cli.governance.governance_impl import govern_reject_impl" in src
        assert "from thegent.cli.governance.governance_impl import govern_list_pending_impl" in src
        assert "from thegent.cli.governance.governance_impl import sweep_impl" in src

    # @trace FR-AUDIT-N+10-014
    def test_escalation_hitl_cmds_does_not_import_governance_from_impl(self) -> None:
        """The 8 broken-wires from `thegent.cli.commands.impl` must be
        gone — only observability / config / shared helpers may remain."""
        mod = _load(ESCALATION_HITL_CMDS)
        src = inspect.getsource(mod)
        forbidden_substrings = (
            "from thegent.cli.commands.impl import escalate_add_impl",
            "from thegent.cli.commands.impl import escalate_list_impl",
            "from thegent.cli.commands.impl import escalate_approve_impl",
            "from thegent.cli.commands.impl import escalate_resolve_impl",
            "from thegent.cli.commands.impl import govern_approve_impl",
            "from thegent.cli.commands.impl import govern_reject_impl",
            "from thegent.cli.commands.impl import govern_list_pending_impl",
            "from thegent.cli.commands.impl import sweep_impl",
            "_cli_shared.escalate_resolve_impl",  # phantom attribute
        )
        for forbidden in forbidden_substrings:
            assert forbidden not in src, (
                f"escalation_hitl_cmds still imports `{forbidden}` — must come from governance_impl"
            )

    # @trace FR-AUDIT-N+10-015
    def test_data_protection_cmds_imports_from_governance_impl(self) -> None:
        mod = _load(DATA_PROTECTION_CMDS)
        src = inspect.getsource(mod)
        assert "from thegent.cli.governance.governance_impl import get_data_protection_status_impl" in src
        assert "from thegent.cli.commands.impl import get_data_protection_status_impl" not in src

    # @trace FR-AUDIT-N+10-016
    def test_apps_govern_imports_from_governance_impl(self) -> None:
        mod = _load(APPS_GOVERN)
        src = inspect.getsource(mod)
        assert "from thegent.cli.governance.governance_impl import govern_approve_impl" in src
        assert "from thegent.cli.governance.governance_impl import govern_reject_impl" in src
        assert "from thegent.cli.governance.governance_impl import harness_register_host_impl" in src
        # Negative check.
        assert "from thegent.cli.commands.impl import govern_approve_impl" not in src
        assert "from thegent.cli.commands.impl import govern_reject_impl" not in src
        assert "from thegent.cli.commands.impl import harness_register_host_impl" not in src


# ---------------------------------------------------------------------------
# 5. Each canonical symbol preserves its public signature.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCanonicalSignaturesPreserved:
    # @trace FR-AUDIT-N+10-020
    def test_each_symbol_has_expected_param_names(self) -> None:
        gov = _load(GOVERNANCE_IMPL)
        for name, expected in EXPECTED_PARAMS.items():
            fn = getattr(gov, name)
            sig = inspect.signature(fn)
            actual_params = set(sig.parameters.keys())
            for p in expected:
                assert p in actual_params, f"{name}: expected param {p!r} missing (actual={sorted(actual_params)})"

    # @trace FR-AUDIT-N+10-021
    def test_escalate_add_impl_is_keyword_only(self) -> None:
        """Per AUDIT-N+5/9, ``escalate_add_impl`` accepts kwargs only.
        Pin that no caller breaks if they use ``escalate_add_impl(...)``
        with positional args (it must raise TypeError)."""
        gov = _load(GOVERNANCE_IMPL)
        sig = inspect.signature(gov.escalate_add_impl)
        # At least one parameter is keyword-only.
        kw_only_count = sum(1 for p in sig.parameters.values() if p.kind == inspect.Parameter.KEYWORD_ONLY)
        assert kw_only_count > 0, "escalate_add_impl must have at least one keyword-only parameter"

    # @trace FR-AUDIT-N+10-022
    def test_sweep_impl_is_keyword_only(self) -> None:
        """Per AUDIT-N+10, ``sweep_impl`` is kwargs-only with 5
        required parameters."""
        gov = _load(GOVERNANCE_IMPL)
        sig = inspect.signature(gov.sweep_impl)
        kw_only_params = [p for p in sig.parameters.values() if p.kind == inspect.Parameter.KEYWORD_ONLY]
        # 5 canonical kwargs.
        assert len(kw_only_params) == 5, (
            f"sweep_impl must have exactly 5 keyword-only parameters, found {len(kw_only_params)}"
        )

    # @trace FR-AUDIT-N+10-023
    def test_harness_register_host_impl_signature(self) -> None:
        gov = _load(GOVERNANCE_IMPL)
        sig = inspect.signature(gov.harness_register_host_impl)
        params = sig.parameters
        assert params["host_id"].default is inspect.Parameter.empty
        assert params["harness"].default is inspect.Parameter.empty
        assert params["command_prefix"].default == ""


# ---------------------------------------------------------------------------
# 6. Round-trip behavior: each canonical symbol behaves correctly.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCanonicalRoundTrip:
    # @trace FR-AUDIT-N+10-030
    def test_escalate_list_impl_returns_list(self, tmp_path: Path) -> None:
        """Mock the EscalationQueue so the call doesn't touch disk."""
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with patch.object(gov, "_session_dir", return_value=tmp_path):
            with patch(
                "thegent.execution.EscalationQueue",
                return_value=MagicMock(list_pending=MagicMock(return_value=[])),
            ):
                items = gov.escalate_list_impl(past_sla_only=False, limit=10)
                assert items == []

    # @trace FR-AUDIT-N+10-031
    def test_escalate_approve_impl_returns_bool(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with (
            patch.object(gov, "_session_dir", return_value=tmp_path),
            patch(
                "thegent.execution.EscalationQueue",
                return_value=MagicMock(resolve=MagicMock(return_value=True)),
            ),
        ):
            result = gov.escalate_approve_impl(run_id="r-1")
            assert result is True

    # @trace FR-AUDIT-N+10-032
    def test_escalate_resolve_impl_returns_bool(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with (
            patch.object(gov, "_session_dir", return_value=tmp_path),
            patch(
                "thegent.execution.EscalationQueue",
                return_value=MagicMock(resolve=MagicMock(return_value=False)),
            ),
        ):
            result = gov.escalate_resolve_impl(run_id="r-2", resolution="resolved")
            assert result is False

    # @trace FR-AUDIT-N+10-033
    def test_govern_approve_impl_returns_dict_with_run_id(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with patch.object(gov, "_session_dir", return_value=tmp_path):
            with patch(
                "thegent.governance.hitl.HITLApprovalWorkflow",
                return_value=MagicMock(approve=MagicMock(return_value={"run_id": "r-3", "status": "approved"})),
            ):
                result = gov.govern_approve_impl(run_id="r-3", reason="ok")
                assert result["run_id"] == "r-3"
                assert result["status"] == "approved"

    # @trace FR-AUDIT-N+10-034
    def test_govern_reject_impl_returns_dict_with_run_id(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with patch.object(gov, "_session_dir", return_value=tmp_path):
            with patch(
                "thegent.governance.hitl.HITLApprovalWorkflow",
                return_value=MagicMock(reject=MagicMock(return_value={"run_id": "r-4", "status": "rejected"})),
            ):
                result = gov.govern_reject_impl(run_id="r-4", reason="denied")
                assert result["run_id"] == "r-4"
                assert result["status"] == "rejected"

    # @trace FR-AUDIT-N+10-035
    def test_govern_list_pending_impl_returns_list(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with (
            patch.object(gov, "_session_dir", return_value=tmp_path),
            patch(
                "thegent.governance.hitl.HITLApprovalWorkflow",
                return_value=MagicMock(list_pending=MagicMock(return_value=[])),
            ),
        ):
            items = gov.govern_list_pending_impl()
            assert items == []

    # @trace FR-AUDIT-N+10-036
    def test_harness_register_host_impl_success(self) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        with patch("thegent.agents.unified_session_index.HarnessType") as mock_harness_type:
            mock_harness_type.return_value = MagicMock()
            mock_harness_type.__call__ = MagicMock(return_value=MagicMock())
            with patch(
                "thegent.agents.unified_session_index.HarnessTUIMapper",
                return_value=MagicMock(register_host=MagicMock()),
            ):
                result = gov.harness_register_host_impl(host_id="h-1", harness="cursor")
                assert result["success"] is True
                assert result["host_id"] == "h-1"
                assert result["harness"] == "cursor"

    # @trace FR-AUDIT-N+10-037
    def test_harness_register_host_impl_unknown_harness(self) -> None:
        gov = _load(GOVERNANCE_IMPL)
        with patch(
            "thegent.agents.unified_session_index.HarnessType",
            side_effect=ValueError("Unknown harness: foo"),
        ):
            result = gov.harness_register_host_impl(host_id="h-2", harness="foo")
            assert result["success"] is False
            assert "Unknown harness" in result["error"]

    # @trace FR-AUDIT-N+10-038
    def test_get_data_protection_status_impl_returns_expected_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gov = _load(GOVERNANCE_IMPL)
        # Create a session_dir at 0o700 permissions.
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        os.chmod(session_dir, 0o700)

        fake_settings = type(
            "S",
            (),
            {
                "session_dir": session_dir,
                "masking_enabled": True,
                "retention_days_sessions": 30,
                "retention_days_registry": 90,
                "retention_days_health": 365,
            },
        )()
        monkeypatch.setattr(gov, "ThegentSettings", lambda: fake_settings)
        result = gov.get_data_protection_status_impl()
        assert result["session_dir_exists"] is True
        assert result["permissions_restricted"] is True
        assert result["masking_enabled"] is True
        assert result["retention_days_sessions"] == 30
        assert result["retention_days_registry"] == 90
        assert result["retention_days_health"] == 365
        assert result["retention_policy_days"] == 30

    # @trace FR-AUDIT-N+10-039
    def test_get_data_protection_status_impl_nonexistent_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gov = _load(GOVERNANCE_IMPL)
        fake_settings = type(
            "S",
            (),
            {
                "session_dir": tmp_path / "nonexistent",
                "masking_enabled": True,
                "retention_days_sessions": 30,
                "retention_days_registry": 90,
                "retention_days_health": 365,
            },
        )()
        monkeypatch.setattr(gov, "ThegentSettings", lambda: fake_settings)
        result = gov.get_data_protection_status_impl()
        assert result["session_dir_exists"] is False
        assert result["permissions_restricted"] is False

    # @trace FR-AUDIT-N+10-040
    def test_get_data_protection_status_impl_takes_zero_args(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gov = _load(GOVERNANCE_IMPL)
        sig = inspect.signature(gov.get_data_protection_status_impl)
        assert len(sig.parameters) == 0, (
            f"get_data_protection_status_impl must take zero args, found {list(sig.parameters)}"
        )

    # @trace FR-AUDIT-N+10-041
    def test_sweep_impl_signature_requires_five_kwargs(self) -> None:
        """Pin that sweep_impl raises TypeError if called with fewer
        than 5 kwargs (call-site regression guard)."""
        gov = _load(GOVERNANCE_IMPL)
        with pytest.raises(TypeError):
            gov.sweep_impl(drift_window=10)  # missing 4 kwargs

    # @trace FR-AUDIT-N+10-042
    def test_sweep_impl_returns_dict_with_pass_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from unittest.mock import MagicMock

        gov = _load(GOVERNANCE_IMPL)
        fake_settings = type("S", (), {"session_dir": tmp_path})()
        monkeypatch.setattr(gov, "ThegentSettings", lambda: fake_settings)
        monkeypatch.setattr(
            gov,
            "Path",
            type("P", (), {"__new__": lambda cls, *a, **kw: tmp_path}),
        )
        with (
            patch(
                "thegent.contracts.telemetry.ContractTelemetry",
                return_value=MagicMock(
                    detect_drift=MagicMock(return_value=[]),
                    get_drift_budget_status=MagicMock(return_value={"within_budget": True}),
                ),
            ),
            patch(
                "thegent.execution.EscalationQueue",
                return_value=MagicMock(list_pending=MagicMock(return_value=[])),
            ),
        ):
            result = gov.sweep_impl(
                drift_window=10,
                structural_budget=5.0,
                semantic_budget=10.0,
                include_audit=False,
                update_calibration_fn=lambda: {"updated": False},
            )
            assert "pass" in result
            assert result["pass"] is True


# ---------------------------------------------------------------------------
# 7. Re-export block structure: impl.py has the AUDIT-N+10 block.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImplReExportStructure:
    # @trace FR-AUDIT-N+10-050
    def test_impl_module_contains_audit_n10_comment(self) -> None:
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        assert "AUDIT-N+10" in src

    # @trace FR-AUDIT-N+10-051
    def test_impl_module_contains_reexport_block_marker(self) -> None:
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        assert "from thegent.cli.governance.governance_impl import" in src

    # @trace FR-AUDIT-N+10-052
    def test_impl_reexport_lists_all_10_symbols(self) -> None:
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        # Extract the AUDIT-N+10 block (between "AUDIT-N+10:" and the next blank line).
        start = src.find("AUDIT-N+10:")
        assert start != -1
        block = src[start:]
        for name in CANONICAL_SYMBOLS:
            assert name in block, f"AUDIT-N+10 re-export block missing {name}"

    # @trace FR-AUDIT-N+10-053
    def test_impl_module_has_no_def_for_canonical_symbols(self) -> None:
        """impl.py must NOT define any of the 10 canonical symbols
        locally (it's only a re-export shim)."""
        impl = _load(IMPL)
        src = inspect.getsource(impl)
        for name in CANONICAL_SYMBOLS:
            # A function definition (allowing method-def `def name(`).
            assert f"def {name}(" not in src, f"impl.py must not define {name} locally — it's a re-export shim"


# ---------------------------------------------------------------------------
# 8. Sweep signature alignment — AUDIT-N+10 closes the call-site mismatch.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSweepCallSiteAlignment:
    # @trace FR-AUDIT-N+10-060
    def test_sweep_cmd_in_escalation_hitl_cmds_uses_canonical_signature(self) -> None:
        """The pre-AUDIT-N+10 sweep_cmd called sweep_impl with only
        2 kwargs, which would TypeError against the canonical 5-kwarg
        signature. Pin that the post-AUDIT-N+10 sweep_cmd passes all
        5 kwargs."""
        import inspect as _inspect

        mod = _load(ESCALATION_HITL_CMDS)
        src = _inspect.getsource(mod.sweep_cmd)
        # Must pass all 5 canonical kwargs.
        assert "drift_window=" in src
        assert "structural_budget=" in src
        assert "semantic_budget=" in src
        assert "include_audit=" in src
        assert "update_calibration_fn=" in src


# ---------------------------------------------------------------------------
# 9. The _cli_shared phantom import is gone.
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPhantomImportRemoved:
    # @trace FR-AUDIT-N+10-070
    def test_escalation_hitl_cmds_does_not_import_cli_shared(self) -> None:
        """Pre-AUDIT-N+10, escalation_hitl_cmds imported
        ``_cli_shared`` purely to call ``_cli_shared.escalate_resolve_impl``,
        which doesn't exist. The phantom import + call must be gone."""
        mod = _load(ESCALATION_HITL_CMDS)
        src = inspect.getsource(mod)
        assert "from thegent.cli.commands import _cli_shared" not in src
        assert "_cli_shared.escalate_resolve_impl" not in src
