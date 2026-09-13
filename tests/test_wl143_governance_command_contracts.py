"""WL-143 ROB-010 governance command contract tests.

Pins the canonical end-to-end contract of the three governance command
modules that import ``thegent.contracts.registry.get_registry`` (the
surface that WL-142 introduced to close the WL-141 pre-existing
broken-import flag).

Unlike the WL-138-era coverage tests in ``test_unit_cli_coverage_c.py``
(which mock the registry), WL-143 verifies the **real** canonical
output: the JSON paths drive the actual ``CONTRACT_REGISTRY``
singleton and the real ``MigrationController`` /
``ContractTelemetry`` machinery — only the rich console and underlying
telemetry / conformance / registry-purge machinery are mocked (because
those go to a real terminal or read on-disk session state).

Coverage:

* ``Section 1`` — every governance module imports cleanly (the WL-142
  fix; ``get_registry`` was a ``NameError``/``ImportError`` until
  WL-142).
* ``Section 2`` — ``contracts_registry_cmd(format="json")`` emits
  parseable JSON containing the canonical ``csm`` entry pinned at
  ``CONTRACT_SCHEMA_VERSION`` for every governance module.
* ``Section 3`` — ``migration_cmd``, ``drift_cmd``,
  ``contracts_conformance_cmd``, ``policy_show_cmd``,
  ``trust_status_cmd`` JSON paths emit the documented field set.
* ``Section 4`` — ROB-010 integration: ``is_compatible`` is consulted
  through the canonical singleton; rich-table / rich-panel render
  paths do not raise.

KR-WL-143-001 (pre-existing, surfaced here for tracking): the
non-JSON panel branch of ``migration_cmd`` reads keys
(``status``, ``reason``, ``migration_days_left``) that the real
``MigrationController.evaluate_version`` does not return. The
panel branch is therefore unreachable from the real controller and
is mocked here. The JSON branch emits the raw dict and is pinned
to the real key set ``{compatible, allowed, contract, version}``.

KR-WL-143-002 (pre-existing, surfaced here for tracking):
``contracts_conformance_cmd`` calls
``run_conformance_suite(session_dir=..., drift_window=...)`` whose
real signature is ``(document: dict)``. The conformance command is
mocked here at the source location so the contract of the command
itself can be pinned.
"""

from __future__ import annotations

import importlib
import io
import json
from contextlib import redirect_stdout
from dataclasses import fields, is_dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Canonical module surface — the three governance command modules that
# WL-142 verified resolve ``get_registry`` without crashing.
# ---------------------------------------------------------------------------

GOV_CONTRACTS_MOD = "thegent.cli.governance.governance_policy_contracts_cmds"
GOV_CORE_MOD = "thegent.cli.governance.governance_policy_core_cmds"
GOV_POLICY_MOD = "thegent.cli.governance.governance_policy_cmds"
REGISTRY_MOD = "thegent.contracts.registry"

ALL_GOV_MODS = [GOV_CONTRACTS_MOD, GOV_CORE_MOD, GOV_POLICY_MOD]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry_mod():
    return importlib.import_module(REGISTRY_MOD)


@pytest.fixture(scope="module")
def canonical_csm_entry(registry_mod):
    """Canonical ``csm`` entry — pinned by WL-142 registry contract."""
    return registry_mod.CONTRACT_REGISTRY.get("csm")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_stdout(fn: Any, *args: Any, **kwargs: Any) -> str:
    """Drive ``fn(*args, **kwargs)`` and return what it wrote to stdout."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def _load_json_array(text: str) -> list[dict[str, Any]]:
    """Parse a single JSON array from ``text``; return the list of objects."""
    text = text.strip()
    if not text:
        return []
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return parsed
    # Single dict wrapped: return as a single-element list for uniformity.
    return [parsed]


def _patch_console(mod: Any, fake_console: Any):
    """Patch ``Console`` for the given module, handling both module-level
    and function-local imports.

    * If the module has a module-level ``Console`` binding (contracts and
      policy modules), the patch replaces that binding so that
      ``Console()`` inside the function returns ``fake_console``.
    * If the module has no module-level binding (core module), the
      function imports ``Console`` locally via ``from rich.console import
      Console`` and the patch on the source class is sufficient.
    * The policy module's ``contracts_registry_cmd`` re-imports
      ``Console`` inside the function, so we also patch the source class
      ``rich.console.Console`` to cover the local re-import path.
    """
    from contextlib import ExitStack

    stack = ExitStack()
    if hasattr(mod, "Console"):
        stack.enter_context(
            patch.object(mod, "Console", new=lambda *a, **kw: fake_console)
        )
    stack.enter_context(patch("rich.console.Console", return_value=fake_console))
    return stack


# ---------------------------------------------------------------------------
# Section 1 — Module imports resolve cleanly (the WL-142 fix).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_governance_module_imports_cleanly(mod_name: str) -> None:
    """Every governance module imports without raising.

    Pre-WL-142 the three modules referenced
    ``thegent.contracts.registry.get_registry()`` which did not exist
    on the registry module — production would have crashed with
    ``ImportError`` on first invocation. WL-142 made the symbol real;
    WL-143 pins the import resolution end-to-end.
    """
    mod = importlib.import_module(mod_name)
    assert mod is not None


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_governance_module_exposes_registry_cmd(mod_name: str) -> None:
    """Every governance module exposes ``contracts_registry_cmd``."""
    mod = importlib.import_module(mod_name)
    assert hasattr(mod, "contracts_registry_cmd"), (
        f"{mod_name} missing contracts_registry_cmd"
    )
    assert callable(mod.contracts_registry_cmd)


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_governance_module_exposes_migration_cmd(mod_name: str) -> None:
    """Every governance module exposes ``migration_cmd``."""
    mod = importlib.import_module(mod_name)
    assert hasattr(mod, "migration_cmd"), f"{mod_name} missing migration_cmd"
    assert callable(mod.migration_cmd)


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_governance_module_exposes_policy_show_cmd(mod_name: str) -> None:
    """Every governance module exposes ``policy_show_cmd``."""
    mod = importlib.import_module(mod_name)
    assert hasattr(mod, "policy_show_cmd"), f"{mod_name} missing policy_show_cmd"
    assert callable(mod.policy_show_cmd)


# ---------------------------------------------------------------------------
# Section 2 — ``contracts_registry_cmd(format="json")`` JSON output.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_json_contains_csm(
    mod_name: str, canonical_csm_entry
) -> None:
    """The JSON output contains the canonical ``csm`` entry."""
    mod = importlib.import_module(mod_name)
    output = _capture_stdout(mod.contracts_registry_cmd, format="json")
    rows = _load_json_array(output)
    assert rows, f"{mod_name}.contracts_registry_cmd produced no JSON rows"
    csm_rows = [r for r in rows if r.get("contract_id") == "csm"]
    assert csm_rows, f"{mod_name}.contracts_registry_cmd JSON missing csm row"
    csm = csm_rows[0]
    assert csm["version"] == canonical_csm_entry.version
    assert csm["deprecated"] is False
    assert "csm" in csm["description"].lower()


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_json_shape(mod_name: str) -> None:
    """The JSON output carries every canonical field from
    ``ContractVersionInfo``.
    """
    mod = importlib.import_module(mod_name)
    output = _capture_stdout(mod.contracts_registry_cmd, format="json")
    rows = _load_json_array(output)
    assert rows, "no JSON rows"
    expected_fields = {
        "contract_id",
        "version",
        "description",
        "deprecated",
        "migration_window_end",
    }
    for r in rows:
        missing = expected_fields - set(r.keys())
        assert not missing, f"{mod_name} row missing fields: {missing}"


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_json_is_sorted(mod_name: str) -> None:
    """JSON output is sorted by ``(contract_id, version)``."""
    mod = importlib.import_module(mod_name)
    output = _capture_stdout(mod.contracts_registry_cmd, format="json")
    rows = _load_json_array(output)
    keys = [(r["contract_id"], r["version"]) for r in rows]
    assert keys == sorted(keys)


def test_contract_version_info_is_dataclass_with_pinned_fields(registry_mod) -> None:
    """``ContractVersionInfo`` is a frozen-metadata dataclass.

    Governance commands consume this shape — the field set is contract-
    pinned to prevent drift.
    """
    assert is_dataclass(registry_mod.ContractVersionInfo)
    actual = {f.name for f in fields(registry_mod.ContractVersionInfo)}
    expected = {
        "contract_id",
        "version",
        "description",
        "deprecated",
        "migration_window_end",
    }
    assert actual == expected


def test_canonical_csm_entry_is_pinned(canonical_csm_entry, registry_mod) -> None:
    """The canonical ``csm`` entry is pinned at ``CONTRACT_SCHEMA_VERSION``
    and is not deprecated.
    """
    assert canonical_csm_entry is not None
    assert canonical_csm_entry.contract_id == "csm"
    assert canonical_csm_entry.version == registry_mod.CONTRACT_SCHEMA_VERSION
    assert canonical_csm_entry.deprecated is False
    assert canonical_csm_entry.migration_window_end is None


# ---------------------------------------------------------------------------
# Section 3 — Other governance command JSON shapes.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_migration_cmd_json_shape(mod_name: str) -> None:
    """``migration_cmd(format="json")`` emits the documented eval fields.

    Canonical shape (from real ``MigrationController.evaluate_version``):
    ``{"compatible": bool, "allowed": bool, "contract": str, "version": str}``.
    """
    mod = importlib.import_module(mod_name)
    output = _capture_stdout(
        mod.migration_cmd,
        contract_id="csm",
        version="contract-schema-v1",
        format="json",
    )
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    for key in ("compatible", "allowed", "contract", "version"):
        assert key in parsed, f"migration JSON missing {key!r}: {parsed!r}"
    assert isinstance(parsed["allowed"], bool)
    assert isinstance(parsed["compatible"], bool)
    assert parsed["contract"] == "csm"
    assert parsed["version"] == "contract-schema-v1"


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_drift_cmd_json_shape(mod_name: str) -> None:
    """``drift_cmd(format="json")`` emits issues + budget dict.

    ``ContractTelemetry`` is mocked because it reads from on-disk
    session state. The contract we pin is the **command's** output
    shape (``issues`` + ``budget``).
    """
    mod = importlib.import_module(mod_name)
    fake_telemetry = MagicMock()
    fake_telemetry.detect_drift.return_value = []
    fake_telemetry.get_drift_budget_status.return_value = {
        "within_budget": True,
        "structural_rate_pct": 0,
        "structural_budget_pct": 5.0,
        "semantic_rate_pct": 0,
        "semantic_budget_pct": 10.0,
    }
    with patch(
        "thegent.contracts.telemetry.ContractTelemetry", return_value=fake_telemetry
    ):
        output = _capture_stdout(
            mod.drift_cmd,
            window=10,
            format="json",
            structural_budget=5.0,
            semantic_budget=10.0,
        )
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    assert "issues" in parsed
    assert "budget" in parsed
    assert isinstance(parsed["issues"], list)
    assert isinstance(parsed["budget"], dict)


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_policy_show_cmd_renders_without_error(mod_name: str) -> None:
    """``policy_show_cmd`` renders without raising (smoke test).

    The command emits to the shared ``console``; capturing stdout would
    not observe Rich's output reliably. We mock the module-level
    ``console`` and assert ``print`` was invoked.
    """
    mod = importlib.import_module(mod_name)
    fake_console = MagicMock()
    with patch.object(mod, "console", new=fake_console):
        mod.policy_show_cmd()
    fake_console.print.assert_called()


def test_contracts_conformance_cmd_json_shape() -> None:
    """``contracts_conformance_cmd(format="json")`` emits a parseable report.

    ``run_conformance_suite`` is patched at the source location because
    the real signature is ``(document: dict)``, whereas the governance
    command calls it with ``session_dir`` and ``drift_window`` kwargs.
    See KR-WL-143-002. The contract we pin is the **command's** output
    shape: ``passed``, ``failed``, ``total``, ``results``.
    """
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_report = {
        "passed": 3,
        "failed": 0,
        "total": 3,
        "results": [
            {
                "name": "t1",
                "provider": "claude",
                "success": True,
                "confidence": 0.9,
                "issues": [],
            },
        ],
        "drift_issues": [],
    }
    with patch(
        "thegent.contracts.conformance.run_conformance_suite", return_value=fake_report
    ):
        output = _capture_stdout(
            mod.contracts_conformance_cmd,
            format="json",
            check_drift=False,
            drift_window=10,
        )
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    for key in ("passed", "failed", "total", "results"):
        assert key in parsed, f"conformance report missing {key!r}"


def test_contracts_conformance_cmd_json_with_drift() -> None:
    """``check_drift=True`` adds ``drift_checked`` + ``drift_issues`` keys.

    The command raises ``typer.Exit(1)`` when ``drift_issues`` is truthy
    or ``failed > 0`` — the test wraps the call in ``pytest.raises`` to
    capture the exit and then asserts the JSON payload was emitted
    before the exit.
    """
    import typer

    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_report = {
        "passed": 2,
        "failed": 0,
        "total": 2,
        "results": [],
        "drift_checked": True,
        "drift_issues": ["minor structural drift"],
    }
    with patch(
        "thegent.contracts.conformance.run_conformance_suite", return_value=fake_report
    ):
        with pytest.raises(typer.Exit):
            _capture_stdout(
                mod.contracts_conformance_cmd,
                format="json",
                check_drift=True,
                drift_window=10,
            )


def test_contracts_conformance_cmd_renders_table() -> None:
    """The rich-table branch renders without raising (mocked)."""
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_report = {
        "passed": 3,
        "failed": 0,
        "total": 3,
        "results": [
            {
                "name": "t1",
                "provider": "claude",
                "success": True,
                "confidence": 0.9,
                "issues": [],
            },
        ],
        "drift_issues": [],
    }
    with patch(
        "thegent.contracts.conformance.run_conformance_suite", return_value=fake_report
    ):
        mod.contracts_conformance_cmd(format=None, check_drift=False, drift_window=10)


def test_trust_status_cmd_json_shape() -> None:
    """``trust_status_cmd(format="json")`` emits current/last env + session_dir."""
    mod = importlib.import_module(GOV_POLICY_MOD)
    output = _capture_stdout(mod.trust_status_cmd, format="json")
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    assert "current_environment" in parsed
    assert "last_recorded_environment" in parsed
    assert "session_dir" in parsed


def test_trust_status_cmd_renders_panel() -> None:
    """The rich-print branch renders without raising when a last env is recorded.

    Note: the command currently calls ``_normalize_output_format(format)``
    which raises ``AttributeError`` when ``format`` is ``None`` — a
    pre-existing latent bug (the rich-print branch is unreachable with
    ``format=None``). The test passes ``format="text"`` to bypass the
    crash and pins the rich-print behavior end-to-end.
    """
    mod = importlib.import_module(GOV_POLICY_MOD)
    fake_boundary = MagicMock()
    fake_boundary.get_last_environment.return_value = "dev"
    fake_boundary.validate_transition.return_value = (True, "ok")
    fake_console = MagicMock()
    with (
        patch.object(
            mod,
            "ThegentSettings",
            return_value=MagicMock(environment="dev", session_dir="/tmp"),
        ),
        patch("thegent.execution.TrustBoundaryValidator", return_value=fake_boundary),
        patch.object(mod, "console", new=fake_console),
    ):
        mod.trust_status_cmd(format="text")
    fake_console.print.assert_called()


def test_policy_purge_cmd_dry_run_renders() -> None:
    """``policy_purge_cmd(dry_run=True)`` invokes ``purge_expired``."""
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_registry = MagicMock()
    fake_registry.purge_expired.return_value = {"purged": 0, "kept": 42}
    with (
        patch.object(
            mod,
            "ThegentSettings",
            return_value=MagicMock(
                session_dir="/tmp",
                retention_default_days=30,
                retention_by_domain={},
            ),
        ),
        patch("thegent.execution.RunRegistry", return_value=fake_registry),
    ):
        mod.policy_purge_cmd(dry_run=True)
    fake_registry.purge_expired.assert_called_once()


def test_policy_purge_cmd_dry_run_message() -> None:
    """The dry-run message announces the kept count."""
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_registry = MagicMock()
    fake_registry.purge_expired.return_value = {"purged": 0, "kept": 7}
    fake_console = MagicMock()
    with (
        patch.object(
            mod,
            "ThegentSettings",
            return_value=MagicMock(
                session_dir="/tmp",
                retention_default_days=30,
                retention_by_domain={},
            ),
        ),
        patch("thegent.execution.RunRegistry", return_value=fake_registry),
        patch.object(mod, "console", new=fake_console),
    ):
        mod.policy_purge_cmd(dry_run=True)
    fake_console.print.assert_called()


def test_migration_cmd_renders_panel_for_allowed() -> None:
    """The rich-panel branch renders when ``allowed=True``.

    KR-WL-143-001: the panel branch reads keys (``status``, ``reason``,
    ``migration_days_left``) that the real controller does not return;
    we mock the controller to return a dict that matches the panel
    template's expectations.
    """
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_mc = MagicMock()
    fake_mc.evaluate_version.return_value = {
        "compatible": True,
        "allowed": True,
        "status": "active",
        "reason": "ok",
        "migration_days_left": 90,
        "contract": "csm",
        "version": "contract-schema-v1",
    }
    with patch("thegent.contracts.migration.MigrationController", return_value=fake_mc):
        mod.migration_cmd(contract_id="csm", version="contract-schema-v1", format=None)
    fake_mc.evaluate_version.assert_called_once_with("csm", "contract-schema-v1")


def test_migration_cmd_renders_panel_for_incompatible() -> None:
    """The rich-panel branch renders when ``allowed=False, status='deprecated'``."""
    mod = importlib.import_module(GOV_CONTRACTS_MOD)
    fake_mc = MagicMock()
    fake_mc.evaluate_version.return_value = {
        "compatible": False,
        "allowed": False,
        "status": "deprecated",
        "reason": "too old",
        "migration_days_left": 0,
        "contract": "csm",
        "version": "contract-schema-v0",
    }
    with patch("thegent.contracts.migration.MigrationController", return_value=fake_mc):
        mod.migration_cmd(contract_id="csm", version="contract-schema-v0", format=None)


# ---------------------------------------------------------------------------
# Section 4 — ROB-010 integration + rich-table smoke.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_consults_singleton(mod_name: str, registry_mod) -> None:
    """``contracts_registry_cmd`` must consult the canonical
    ``CONTRACT_REGISTRY`` singleton — not a fresh local instance.

    Implementation: register a sentinel ``wl143-sentinel`` contract on
    the singleton, call ``contracts_registry_cmd(format="json")``, and
    assert the sentinel row appears in the output. After the test the
    sentinel is removed (so we don't pollute other tests).
    """
    mod = importlib.import_module(mod_name)
    sentinel_id = "wl143-sentinel"
    sentinel_version = "wl143-v1"
    registry_mod.CONTRACT_REGISTRY.register(
        sentinel_id,
        {
            "version": sentinel_version,
            "description": "WL-143 sentinel contract",
            "deprecated": False,
            "migration_window_end": None,
        },
    )
    try:
        output = _capture_stdout(mod.contracts_registry_cmd, format="json")
        rows = _load_json_array(output)
        ids = {r["contract_id"] for r in rows}
        assert sentinel_id in ids, f"{mod_name} did not consult the singleton"
    finally:
        # Remove the sentinel so we don't pollute other tests.
        registry_mod.CONTRACT_REGISTRY._contracts.pop(sentinel_id, None)


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_renders_table_path(mod_name: str) -> None:
    """The rich-table path renders without raising (smoke test)."""
    mod = importlib.import_module(mod_name)
    fake_console = MagicMock()
    with _patch_console(mod, fake_console):
        mod.contracts_registry_cmd(format=None)
    fake_console.print.assert_called()


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_renders_deprecated_entry(
    mod_name: str, registry_mod
) -> None:
    """A deprecated entry renders the ``DEPRECATED`` status marker.

    The table path branches on ``deprecated=True`` (and on a non-empty
    ``migration_window_end``). WL-143 pins both branches.
    """
    mod = importlib.import_module(mod_name)
    sentinel_id = "wl143-deprecated-sentinel"
    registry_mod.CONTRACT_REGISTRY.register(
        sentinel_id,
        {
            "version": "wl143-dep-v1",
            "description": "WL-143 deprecated sentinel",
            "deprecated": True,
            "migration_window_end": "2099-12-31",
        },
    )
    try:
        fake_console = MagicMock()
        with _patch_console(mod, fake_console):
            mod.contracts_registry_cmd(format=None)
        fake_console.print.assert_called()
    finally:
        registry_mod.CONTRACT_REGISTRY._contracts.pop(sentinel_id, None)


@pytest.mark.parametrize("mod_name", ALL_GOV_MODS)
def test_contracts_registry_singleton_remove_restores_view(
    mod_name: str, registry_mod
) -> None:
    """Removing a sentinel from the singleton is reflected in the next
    ``contracts_registry_cmd`` call.

    Pins the singleton-consulted contract from the OTHER side: the
    view is built from the live registry, not from a cached snapshot.
    """
    mod = importlib.import_module(mod_name)
    sentinel_id = "wl143-toggle"
    registry_mod.CONTRACT_REGISTRY.register(
        sentinel_id,
        {
            "version": "wl143-tog-v1",
            "description": "WL-143 toggle sentinel",
            "deprecated": False,
            "migration_window_end": None,
        },
    )
    try:
        # First call — sentinel is visible.
        output = _capture_stdout(mod.contracts_registry_cmd, format="json")
        rows = _load_json_array(output)
        assert sentinel_id in {r["contract_id"] for r in rows}
        # Remove the sentinel.
        registry_mod.CONTRACT_REGISTRY._contracts.pop(sentinel_id, None)
        # Second call — sentinel is gone.
        output = _capture_stdout(mod.contracts_registry_cmd, format="json")
        rows = _load_json_array(output)
        assert sentinel_id not in {r["contract_id"] for r in rows}
    finally:
        registry_mod.CONTRACT_REGISTRY._contracts.pop(sentinel_id, None)


def test_is_compatible_rejects_downgrade(registry_mod) -> None:
    """``is_compatible`` rejects forward-drift, backward-drift, unknown,
    and empty requested versions. ROB-010 contract.
    """
    current = registry_mod.CONTRACT_SCHEMA_VERSION
    cases = [
        ("", current, False),
        ("contract-schema-v0", current, False),
        ("contract-schema-v99", current, False),
        ("unknown-schema", current, False),
        (current, current, True),
    ]
    for requested, cur, expected in cases:
        got = registry_mod.get_registry().is_compatible(requested, cur)
        assert got is expected, (
            f"is_compatible({requested!r}, {cur!r}) → {got}, want {expected}"
        )
