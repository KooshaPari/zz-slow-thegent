"""Spec-only hardening tests for the dormant Evidence module (SOTA pass-26).

Covers a single dormant orchestration/strategies module that has never
been audited in the dormant-core chain:

  * ``thegent.orchestration.strategies.evidence``
    — ``PromotionGate`` class with ``capture_evidence(run_id, csm)``,
    ``validate_promotion(csm, policy)`` and
    ``verify_evidence_hash(run_id, phase, evidence_hash)`` public
    surface that drives evidence-based promotion decisions in the
    orchestrator strategy layer (WP-1005, FR-004).

This file is the AUDIT-N+42 contract spec (SOTA pass-26).  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37 / N+38 / N+39 / N+40 / N+41) so the next step is to
make every assertion here pass without breaking the dormant corridor
(``tests/orchestration/test_strategies_evidence.py``) or any other
SOTA audit-N+ invariant cluster.

This spec does NOT import from ``thegent.orchestration.strategies.
evidence`` — it validates the contract surface exclusively via AST
introspection and source-level string matching so the tests are
hermetic and never execute production code paths.

@trace FR-ORC-EV-001 -- Module source defines a class named
                       ``PromotionGate`` as the primary public
                       abstraction for evidence capture and
                       promotion validation at orchestration gates.
@trace FR-ORC-EV-002 -- ``PromotionGate.__init__`` accepts a
                       ``session_dir`` positional parameter so
                       the dormant corridor can construct instances
                       via ``PromotionGate(session_dir)`` without
                       keyword-only arguments.
@trace FR-ORC-EV-003 -- ``PromotionGate`` derives ``evidence_dir``
                       as ``session_dir / "evidence"`` so captured
                       evidence files are isolated in a dedicated
                       subdirectory of the session tree.
@trace FR-ORC-EV-004 -- ``PromotionGate`` derives ``audit_path``
                       as ``session_dir / "evidence_audit.jsonl"``
                       so the append-only audit trail uses newline-
                       delimited JSON for streaming consumption.
@trace FR-ORC-EV-005 -- ``PromotionGate.__init__`` converts string
                       paths to ``pathlib.Path`` objects so callers
                       that pass ``str(tmp_path / "session")`` do
                       not break with ``AttributeError`` on ``/``.
@trace FR-ORC-EV-006 -- ``capture_evidence`` is a method of
                       ``PromotionGate`` that accepts ``run_id``
                       and ``csm`` as parameters so the orchestrator
                       can record evidence snapshots keyed by run
                       and phase.
@trace FR-ORC-EV-007 -- ``capture_evidence`` creates the evidence
                       directory (``mkdir``) so the caller does not
                       need to pre-create the directory tree.
@trace FR-ORC-EV-008 -- ``capture_evidence`` writes a JSON file
                       into the evidence directory so downstream
                       verifiers can re-read the persisted snapshot.
@trace FR-ORC-EV-009 -- ``capture_evidence`` returns a SHA-256 hex
                       digest (``hashlib.sha256``) of the serialized
                       evidence so callers can store the integrity
                       hash without reimplementing hashing.
@trace FR-ORC-EV-010 -- ``capture_evidence`` appends a JSONL entry
                       to the ``audit_path`` file with fields
                       ``run_id``, ``phase``, ``evidence_hash``,
                       ``ts`` and ``evidence_path`` so the audit
                       trail is a complete append-only ledger.
@trace FR-ORC-EV-011 -- ``capture_evidence`` resolves the phase
                       value from ``csm.phase`` via ``.value`` when
                       available and falls back to ``str()`` when
                       the phase is a plain string, so callers with
                       both enum and string phases work correctly.
@trace FR-ORC-EV-012 -- ``validate_promotion`` is a method of
                       ``PromotionGate`` that accepts ``csm`` and
                       ``policy`` and returns a ``list[str]`` of
                       human-readable issue descriptors so the
                       orchestrator can decide whether to promote.
@trace FR-ORC-EV-013 -- ``validate_promotion`` checks
                       ``csm.confidence_level`` against
                       ``policy.min_confidence_threshold`` and
                       appends a diagnostic string when the score
                       is below the threshold so confidence
                       regressions are surfaced before promotion.
@trace FR-ORC-EV-014 -- ``validate_promotion`` inspects
                       ``csm.blockers`` and appends a diagnostic
                       string when blockers are present so the
                       orchestrator never promotes a run that has
                       unresolved blockers.
@trace FR-ORC-EV-015 -- ``verify_evidence_hash`` is a method of
                       ``PromotionGate`` that accepts ``run_id``,
                       ``phase`` and ``evidence_hash`` and returns
                       a boolean so callers can verify evidence
                       integrity before relying on the hash.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module under test — read source and parse AST so we never import
# the production module directly.
# ---------------------------------------------------------------------------

_EVIDENCE_SRC = Path("src/thegent/orchestration/strategies/evidence/__init__.py")

_EVIDENCE_AST = ast.parse(_EVIDENCE_SRC.read_text())
_EVIDENCE_TEXT = _EVIDENCE_SRC.read_text()


def _class_node(name: str) -> ast.ClassDef:
    """Return the first ``ast.ClassDef`` with the given *name*."""
    for node in ast.walk(_EVIDENCE_AST):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"Class {name!r} not found in AST")


def _method_names(cls: ast.ClassDef) -> list[str]:
    """Return all method names defined directly on *cls*."""
    return [node.name for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _method_node(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    """Return the ``FunctionDef`` for *name* inside *cls*."""
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"Method {name!r} not found in class {cls.name!r}")


def _param_names(func: ast.FunctionDef) -> list[str]:
    """Return parameter names for *func* (excluding ``self``)."""
    return [arg.arg for arg in func.args.args if arg.arg != "self"]


# ---------------------------------------------------------------------------
# FR-ORC-EV-001 -- PromotionGate class existence
# ---------------------------------------------------------------------------


class TestPromotionGateClassExists:
    """@trace FR-ORC-EV-001"""

    def test_class_promotion_gate_defined(self) -> None:
        """Module source defines ``class PromotionGate``."""
        cls = _class_node("PromotionGate")
        assert cls is not None

    def test_class_is_not_abstract_base(self) -> None:
        """``PromotionGate`` is not an ABC (no abstract methods)."""
        cls = _class_node("PromotionGate")
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id == "ABC":
                pytest.fail("PromotionGate must not inherit from ABC")

    def test_class_has_docstring(self) -> None:
        """``PromotionGate`` carries a docstring for documentation."""
        cls = _class_node("PromotionGate")
        first = cls.body[0]
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)


# ---------------------------------------------------------------------------
# FR-ORC-EV-002 -- __init__ accepts session_dir
# ---------------------------------------------------------------------------


class TestPromotionGateInitSignature:
    """@trace FR-ORC-EV-002"""

    def test_init_method_exists(self) -> None:
        """``PromotionGate`` has an ``__init__`` method."""
        cls = _class_node("PromotionGate")
        assert "__init__" in _method_names(cls)

    def test_init_accepts_session_dir_parameter(self) -> None:
        """``__init__`` has a ``session_dir`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "__init__")
        params = _param_names(node)
        assert "session_dir" in params

    def test_init_first_param_is_session_dir(self) -> None:
        """``session_dir`` is the first parameter after ``self``."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "__init__")
        params = _param_names(node)
        assert params[0] == "session_dir"


# ---------------------------------------------------------------------------
# FR-ORC-EV-003 -- evidence_dir derivation
# ---------------------------------------------------------------------------


class TestPromotionGateEvidenceDir:
    """@trace FR-ORC-EV-003"""

    def test_source_references_evidence_subdirectory(self) -> None:
        """Source contains ``"evidence"`` as a subdirectory name."""
        assert '"evidence"' in _EVIDENCE_TEXT or "'evidence'" in _EVIDENCE_TEXT

    def test_source_derives_evidence_dir_from_session_dir(self) -> None:
        """Source assigns ``evidence_dir`` from session_dir path join."""
        assert "evidence_dir" in _EVIDENCE_TEXT

    def test_evidence_dir_uses_path_division(self) -> None:
        """Source uses ``/`` operator or ``Path`` join for evidence_dir."""
        # Look for evidence_dir = session_dir / "evidence" pattern
        has_division = (
            'session_dir / "evidence"' in _EVIDENCE_TEXT
            or "session_dir / 'evidence'" in _EVIDENCE_TEXT
            or 'Path("evidence")' in _EVIDENCE_TEXT
            or "Path('evidence')" in _EVIDENCE_TEXT
        )
        assert has_division, "evidence_dir must be derived via Path division or Path('evidence')"


# ---------------------------------------------------------------------------
# FR-ORC-EV-004 -- audit_path derivation
# ---------------------------------------------------------------------------


class TestPromotionGateAuditPath:
    """@trace FR-ORC-EV-004"""

    def test_source_references_audit_path(self) -> None:
        """Source assigns ``audit_path`` as an attribute."""
        assert "audit_path" in _EVIDENCE_TEXT

    def test_audit_path_uses_jsonl_extension(self) -> None:
        """``audit_path`` ends with ``.jsonl``."""
        assert "evidence_audit.jsonl" in _EVIDENCE_TEXT

    def test_audit_path_derived_from_session_dir(self) -> None:
        """``audit_path`` is derived from ``session_dir``."""
        assert 'session_dir / "evidence_audit.jsonl"' in _EVIDENCE_TEXT or (
            "session_dir / 'evidence_audit.jsonl'" in _EVIDENCE_TEXT
        )


# ---------------------------------------------------------------------------
# FR-ORC-EV-005 -- string-to-Path conversion
# ---------------------------------------------------------------------------


class TestPromotionGateStringConversion:
    """@trace FR-ORC-EV-005"""

    def test_source_uses_path_constructor(self) -> None:
        """Source converts paths via ``Path(...)`` so string inputs work."""
        assert "Path(" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-006 -- capture_evidence method signature
# ---------------------------------------------------------------------------


class TestCaptureEvidenceSignature:
    """@trace FR-ORC-EV-006"""

    def test_capture_evidence_method_exists(self) -> None:
        """``PromotionGate`` defines ``capture_evidence``."""
        cls = _class_node("PromotionGate")
        assert "capture_evidence" in _method_names(cls)

    def test_capture_evidence_accepts_run_id(self) -> None:
        """``capture_evidence`` has a ``run_id`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "capture_evidence")
        assert "run_id" in _param_names(node)

    def test_capture_evidence_accepts_csm(self) -> None:
        """``capture_evidence`` has a ``csm`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "capture_evidence")
        assert "csm" in _param_names(node)

    def test_capture_evidence_has_two_params(self) -> None:
        """``capture_evidence`` accepts exactly two params (run_id, csm)."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "capture_evidence")
        params = _param_names(node)
        assert len(params) == 2, f"Expected 2 params, got {len(params)}: {params}"


# ---------------------------------------------------------------------------
# FR-ORC-EV-007 -- capture_evidence creates evidence directory
# ---------------------------------------------------------------------------


class TestCaptureEvidenceDirCreation:
    """@trace FR-ORC-EV-007"""

    def test_source_contains_mkdir(self) -> None:
        """Source calls ``mkdir`` to create the evidence directory."""
        assert "mkdir" in _EVIDENCE_TEXT

    def test_mkdir_uses_exist_ok(self) -> None:
        """``mkdir`` uses ``exist_ok=True`` for idempotency."""
        assert "exist_ok" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-008 -- capture_evidence writes JSON file
# ---------------------------------------------------------------------------


class TestCaptureEvidenceFileWrite:
    """@trace FR-ORC-EV-008"""

    def test_source_writes_evidence_file(self) -> None:
        """Source writes a file to the evidence directory."""
        assert "write_text" in _EVIDENCE_TEXT or ".write(" in _EVIDENCE_TEXT

    def test_source_references_evidence_file_path(self) -> None:
        """Source constructs a file path with run_id and phase."""
        # The file name pattern is {run_id}_{phase}.json
        assert "run_id" in _EVIDENCE_TEXT
        assert ".json" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-009 -- capture_evidence returns SHA-256 hash
# ---------------------------------------------------------------------------


class TestCaptureEvidenceHash:
    """@trace FR-ORC-EV-009"""

    def test_source_uses_hashlib_sha256(self) -> None:
        """Source uses ``hashlib.sha256`` for hashing evidence."""
        assert "hashlib" in _EVIDENCE_TEXT
        assert "sha256" in _EVIDENCE_TEXT

    def test_source_calls_hexdigest(self) -> None:
        """Source calls ``hexdigest()`` to produce the hex hash."""
        assert "hexdigest()" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-010 -- capture_evidence appends audit trail
# ---------------------------------------------------------------------------


class TestCaptureEvidenceAuditTrail:
    """@trace FR-ORC-EV-010"""

    def test_source_appends_to_audit_path(self) -> None:
        """Source appends to ``audit_path`` (not overwrite)."""
        assert "audit_path" in _EVIDENCE_TEXT
        # Should open in append mode or use a模式 that appends
        assert '"a"' in _EVIDENCE_TEXT or "'a'" in _EVIDENCE_TEXT or "append" in _EVIDENCE_TEXT.lower()

    def test_audit_entry_references_run_id(self) -> None:
        """Audit entry dict includes ``run_id`` field."""
        # The source should construct a dict with run_id as a key
        assert "run_id" in _EVIDENCE_TEXT

    def test_audit_entry_references_phase(self) -> None:
        """Audit entry dict includes ``phase`` field."""
        assert "phase" in _EVIDENCE_TEXT

    def test_audit_entry_references_evidence_hash(self) -> None:
        """Audit entry dict includes ``evidence_hash`` field."""
        assert "evidence_hash" in _EVIDENCE_TEXT

    def test_audit_entry_references_timestamp(self) -> None:
        """Audit entry dict includes a ``ts`` (timestamp) field."""
        assert '"ts"' in _EVIDENCE_TEXT or "'ts'" in _EVIDENCE_TEXT

    def test_audit_entry_references_evidence_path(self) -> None:
        """Audit entry dict includes ``evidence_path`` field."""
        assert "evidence_path" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-011 -- capture_evidence phase handling
# ---------------------------------------------------------------------------


class TestCaptureEvidencePhaseHandling:
    """@trace FR-ORC-EV-011"""

    def test_source_handles_phase_value_attribute(self) -> None:
        """Source accesses ``.value`` on the phase object."""
        assert ".value" in _EVIDENCE_TEXT

    def test_source_falls_back_to_str_for_phase(self) -> None:
        """Source uses ``str()`` as fallback when ``.value`` is absent."""
        # The pattern should be: phase.value if hasattr else str(phase)
        # or a try/except or getattr-based pattern
        has_fallback = "getattr" in _EVIDENCE_TEXT or "hasattr" in _EVIDENCE_TEXT or "str(" in _EVIDENCE_TEXT
        assert has_fallback, "Phase handling must have a str() fallback for non-enum phases"


# ---------------------------------------------------------------------------
# FR-ORC-EV-012 -- validate_promotion method signature
# ---------------------------------------------------------------------------


class TestValidatePromotionSignature:
    """@trace FR-ORC-EV-012"""

    def test_validate_promotion_method_exists(self) -> None:
        """``PromotionGate`` defines ``validate_promotion``."""
        cls = _class_node("PromotionGate")
        assert "validate_promotion" in _method_names(cls)

    def test_validate_promotion_accepts_csm(self) -> None:
        """``validate_promotion`` has a ``csm`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "validate_promotion")
        assert "csm" in _param_names(node)

    def test_validate_promotion_accepts_policy(self) -> None:
        """``validate_promotion`` has a ``policy`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "validate_promotion")
        assert "policy" in _param_names(node)

    def test_validate_promotion_has_two_params(self) -> None:
        """``validate_promotion`` accepts exactly two params."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "validate_promotion")
        params = _param_names(node)
        assert len(params) == 2, f"Expected 2 params, got {len(params)}: {params}"


# ---------------------------------------------------------------------------
# FR-ORC-EV-013 -- validate_promotion confidence check
# ---------------------------------------------------------------------------


class TestValidatePromotionConfidenceCheck:
    """@trace FR-ORC-EV-013"""

    def test_source_references_confidence_level(self) -> None:
        """Source checks ``confidence_level`` on the CSM."""
        assert "confidence_level" in _EVIDENCE_TEXT

    def test_source_references_min_confidence_threshold(self) -> None:
        """Source compares against ``min_confidence_threshold``."""
        assert "min_confidence_threshold" in _EVIDENCE_TEXT

    def test_validate_promotion_builds_issues_list(self) -> None:
        """Source constructs an ``issues`` list to accumulate diagnostics."""
        assert "issues" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-014 -- validate_promotion blocker check
# ---------------------------------------------------------------------------


class TestValidatePromotionBlockersCheck:
    """@trace FR-ORC-EV-014"""

    def test_source_references_blockers(self) -> None:
        """Source inspects ``blockers`` on the CSM."""
        assert "blockers" in _EVIDENCE_TEXT

    def test_source_reports_blocker_issue(self) -> None:
        """Source includes a diagnostic string when blockers are present."""
        # The dormant corridor expects "Active blockers present" in the issue
        assert "Active blockers present" in _EVIDENCE_TEXT


# ---------------------------------------------------------------------------
# FR-ORC-EV-015 -- verify_evidence_hash method signature
# ---------------------------------------------------------------------------


class TestVerifyEvidenceHashSignature:
    """@trace FR-ORC-EV-015"""

    def test_verify_evidence_hash_method_exists(self) -> None:
        """``PromotionGate`` defines ``verify_evidence_hash``."""
        cls = _class_node("PromotionGate")
        assert "verify_evidence_hash" in _method_names(cls)

    def test_verify_evidence_hash_accepts_run_id(self) -> None:
        """``verify_evidence_hash`` has a ``run_id`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "verify_evidence_hash")
        assert "run_id" in _param_names(node)

    def test_verify_evidence_hash_accepts_phase(self) -> None:
        """``verify_evidence_hash`` has a ``phase`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "verify_evidence_hash")
        assert "phase" in _param_names(node)

    def test_verify_evidence_hash_accepts_evidence_hash(self) -> None:
        """``verify_evidence_hash`` has an ``evidence_hash`` parameter."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "verify_evidence_hash")
        assert "evidence_hash" in _param_names(node)

    def test_verify_evidence_hash_has_three_params(self) -> None:
        """``verify_evidence_hash`` accepts exactly three params."""
        cls = _class_node("PromotionGate")
        node = _method_node(cls, "verify_evidence_hash")
        params = _param_names(node)
        assert len(params) == 3, f"Expected 3 params, got {len(params)}: {params}"


# ---------------------------------------------------------------------------
# FR-ORC-EV-015 (cont.) -- verify_evidence_hash behaviour contract
# ---------------------------------------------------------------------------


class TestVerifyEvidenceHashBehaviour:
    """@trace FR-ORC-EV-015"""

    def test_source_reads_evidence_file(self) -> None:
        """Source reads the evidence file for hash comparison."""
        assert "read_text" in _EVIDENCE_TEXT or ".read()" in _EVIDENCE_TEXT

    def test_source_computes_hash_of_file_content(self) -> None:
        """Source hashes the file content to compare with the expected hash."""
        assert "sha256" in _EVIDENCE_TEXT

    def test_source_returns_boolean(self) -> None:
        """Source returns ``True`` or ``False`` (boolean contract)."""
        # Verify the return statements use True/False literals
        assert "return True" in _EVIDENCE_TEXT or "return True\n" in _EVIDENCE_TEXT
        assert "return False" in _EVIDENCE_TEXT or "return False\n" in _EVIDENCE_TEXT

    def test_source_checks_file_existence(self) -> None:
        """Source checks that the evidence file exists before reading."""
        assert "exists()" in _EVIDENCE_TEXT or "is_file()" in _EVIDENCE_TEXT
