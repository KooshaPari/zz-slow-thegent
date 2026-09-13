"""thegent.contracts.adapters — output adapter surface for the contracts pipeline.

This module is the canonical, contract-pinned implementation of the
adapter layer feeding the L8 normalisation pipeline. It exposes:

* :class:`AdapterResult` — dataclass with ``csm`` /
  ``confidence`` / ``parse_errors`` / ``source_provider`` fields.
* :class:`OutputAdapter` — abstract base class every concrete
  adapter implements (``provider`` attribute + ``normalize(raw, context)``).
* :class:`XMLOutputAdapter` — XML-tagged payload adapter
  (PascalCase + snake_case tag variants).
* :class:`GenericOutputAdapter` — generic plain-text adapter that
  emits ``source_contract="plain"`` CSMs with heuristic confidence.
* :func:`normalize_output` — convenience function that resolves the
  registered adapter for a provider and delegates to it, with
  fallback handling.
* :class:`AdapterRegistry` — singleton-backed registry that
  stores / retrieves adapters and exposes the canonical
  ``ADAPTER_REGISTRY`` instance for governance / CLI consumers.

The provider set is the canonical seven supported providers:

* copilot, gemini, claude, codex, cursor, cursor-agent, antigravity
  (all XMLOutputAdapter)
* minimax, cliproxy (GenericOutputAdapter)
* cline (XMLOutputAdapter, not in the test suite but exposed for parity)

Wire-format guarantees (pinned by ``tests/test_wl145_l9_contracts_signature_parity.py``):

* Adapter-returned CSMs always include ``source_contract`` set to
  one of: ``"xml-tags"``, ``"plain"``, ``"fallback-plain"``.
* Confidence is in ``[0.0, 1.0]``; ``0.0`` indicates a parse failure
  (parse_errors populated).
* The fallback path uses :func:`extract_condensed` to surface
  JSONL-shaped payloads as best-effort CSM summaries.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from thegent.contracts.csm.v1 import CanonicalStructuredMessage, CSMPhase, CSMStatus
from thegent.contracts.parser import IncrementalXMLParser, extract_tags
from thegent.contracts.validation import SemanticValidationError

__all__ = [
    "ADAPTER_REGISTRY",
    "ADAPTER_REGISTRY_VERSION",
    "ADAPTERS",
    "AdapterRegistry",
    "AdapterResult",
    "ContractAdapter",
    "ContractValidator",
    "GenericOutputAdapter",
    "OutputAdapter",
    "XMLOutputAdapter",
    "extract_condensed",
    "get_adapter",
    "normalize_output",
    "register_adapter",
]


#: Canonical adapter-registry schema version. Bumped only when the
#: public surface (``AdapterRegistry``, ``OutputAdapter.normalize``,
#: ``normalize_output`` signature) changes in a breaking way.
ADAPTER_REGISTRY_VERSION: str = "adapters-v1"


#: Progress strings are coerced into ``[0.0, 1.0]``. Integers greater
#: than 1 are divided by 100 (assumed percentage); values already in
#: ``[0.0, 1.0]`` pass through unchanged.
_PERCENT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*%\s*$")
_NUMBER_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*$")


@dataclass
class AdapterResult:
    """Result of a single adapter invocation.

    Holds the normalised :class:`CanonicalStructuredMessage` plus
    diagnostic metadata. ``confidence`` is in ``[0.0, 1.0]``; ``0.0``
    indicates a parse / structural failure (in which case
    ``parse_errors`` is non-empty).
    """

    csm: CanonicalStructuredMessage
    confidence: float = 1.0
    parse_errors: list[str] = field(default_factory=list)
    source_provider: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "csm": self.csm.to_dict(),
            "confidence": self.confidence,
            "parse_errors": list(self.parse_errors),
            "source_provider": self.source_provider,
        }


class OutputAdapter(ABC):
    """Abstract base class for output adapters.

    Concrete subclasses set a ``provider`` class attribute and
    implement :meth:`normalize`.
    """

    provider: str = ""

    @abstractmethod
    def normalize(
        self,
        raw: Any,
        context: dict[str, Any] | None = None,
    ) -> AdapterResult:
        """Normalise a raw agent payload into an :class:`AdapterResult`."""


class XMLOutputAdapter(OutputAdapter):
    """Adapter that extracts CSM fields from XML-tagged payloads.

    Supports both the PascalCase ("STATUS", "SUMMARY", "TASK_ID",
    "PROGRESS" …) and the snake_case ("task_status", "task_summary",
    "task_objective" …) tag variants that real-world providers emit.

    The ``provider`` argument is optional and defaults to ``"xml"``
    so legacy zero-arg callers (``XMLOutputAdapter()``) keep working.
    """

    def __init__(self, provider: str = "xml") -> None:
        self.provider = provider

    def format(self, payload: dict[str, Any] | Any) -> str:
        """Serialise ``payload`` as an XML-tagged string.

        Convenience for downstream consumers (logging, telemetry,
        tests) that want a deterministic textual representation of an
        :class:`OutputAdapter` payload. ``payload`` may be a dict
        (rendered as ``<KEY>value</KEY>`` per key) or any other value
        (rendered via ``str(payload)`` wrapped in ``<MESSAGE>``).
        """
        if isinstance(payload, dict):
            parts: list[str] = []
            for key, value in payload.items():
                # Normalise the key — PascalCase is the canonical form
                # but we accept any case from legacy callers.
                tag = str(key).replace(" ", "_").strip() or "ITEM"
                if not tag[0].isalpha():
                    tag = f"X_{tag}"
                parts.append(f"<{tag}>{value}</{tag}>")
            return "".join(parts)
        return f"<MESSAGE>{payload}</MESSAGE>"

    @staticmethod
    def _extract_text(raw: Any) -> str:
        """Coerce ``raw`` into a string suitable for tag extraction."""
        if raw is None:
            return ""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            # Prefer ``stdout`` / ``content`` / ``text`` keys in that
            # order; fall back to JSON-serialising the dict.
            for key in ("stdout", "content", "text", "message"):
                value = raw.get(key)
                if isinstance(value, str):
                    return value
            try:
                return json.dumps(raw, default=str)
            except (TypeError, ValueError):
                return str(raw)
        return str(raw)

    def normalize(
        self,
        raw: Any,
        context: dict[str, Any] | None = None,
    ) -> AdapterResult:
        context = context or {}
        text = self._extract_text(raw)
        run_id = str(context.get("run_id", "") or "")
        chunk_id = str(context.get("chunk_id", "") or "")

        # 1. Detect truncated payload before attempting extraction.
        parser = IncrementalXMLParser()
        partial = parser.get_partial_state(text)
        if (
            partial.get("open_tag")
            or partial.get("incomplete_tag")
            or partial.get("is_truncated")
        ):
            return AdapterResult(
                csm=CanonicalStructuredMessage(
                    status=CSMStatus.PENDING,
                    phase=CSMPhase.UNKNOWN,
                    source_contract="xml-tags",
                    run_id=run_id,
                    chunk_id=chunk_id,
                ),
                confidence=0.0,
                parse_errors=["parse_truncated"],
                source_provider=self.provider,
            )

        # 2. Extract case-insensitive tags.
        tags = extract_tags(text)
        if not tags:
            return AdapterResult(
                csm=CanonicalStructuredMessage(
                    status=CSMStatus.PENDING,
                    phase=CSMPhase.UNKNOWN,
                    source_contract="xml-tags",
                    run_id=run_id,
                    chunk_id=chunk_id,
                ),
                confidence=0.0,
                parse_errors=["no_xml_tags_detected"],
                source_provider=self.provider,
            )

        # 3. Map tags → CSM fields. Both PascalCase and snake_case
        # variants are honoured; PascalCase takes precedence.
        kwargs: dict[str, Any] = {
            "run_id": run_id,
            "chunk_id": chunk_id,
            "source_contract": "xml-tags",
        }

        # STATUS / status
        for status_key in ("STATUS", "TASK_STATUS"):
            if status_key in tags:
                kwargs["status"] = _coerce_status(tags[status_key])
                break
        else:
            kwargs["status"] = CSMStatus.PENDING

        # PHASE / phase
        for phase_key in ("PHASE", "TASK_PHASE"):
            if phase_key in tags:
                kwargs["phase"] = _coerce_phase(tags[phase_key])
                break

        # TASK_ID / task_id / TaskId
        for task_key in ("TASK_ID", "TASKID", "TASK_ID_TAG"):
            if task_key in tags:
                kwargs["task_id"] = tags[task_key]
                break
        if "task_id" not in kwargs:
            for task_key in ("task_id", "TaskId"):
                if task_key in tags:
                    kwargs["task_id"] = tags[task_key]
                    break

        # SUMMARY / task_summary / TaskUpdate — Claude/Anthropic and
        # some Codex payloads emit `<TaskUpdate>...</TaskUpdate>` to
        # describe the in-progress summary text. Map to ``summary``.
        for summary_key in ("SUMMARY", "TASK_SUMMARY", "TASKUPDATE"):
            if summary_key in tags:
                kwargs["summary"] = tags[summary_key]
                break
        if "summary" not in kwargs and "summary" in tags:
            kwargs["summary"] = tags["summary"]

        # OBJECTIVE / task_objective
        for obj_key in ("OBJECTIVE", "TASK_OBJECTIVE"):
            if obj_key in tags:
                kwargs["objective"] = tags[obj_key]
                break

        # PROGRESS / progress
        for prog_key in ("PROGRESS", "TASK_PROGRESS"):
            if prog_key in tags:
                kwargs["progress"] = _coerce_progress(tags[prog_key])
                break

        # List fields (multi-line content is split on newlines).
        for src_key, dst_key in (
            ("ACTIONS_COMPLETED", "actions_completed"),
            ("ISSUES", "issues"),
            ("NEXT_STEPS", "next_steps"),
            ("BLOCKERS", "blockers"),
        ):
            if src_key in tags:
                kwargs[dst_key] = _split_lines(tags[src_key])

        # Multi-field INPUT_ALIASES (snake_case variant `task_<field>`)
        for src_key, dst_key in (
            ("task_summary", "summary"),
            ("task_objective", "objective"),
            ("task_id", "task_id"),
            ("task_progress", "progress"),
            ("task_status", "status"),
            ("task_phase", "phase"),
        ):
            if src_key in tags and dst_key not in kwargs:
                if src_key.endswith("progress"):
                    kwargs[dst_key] = _coerce_progress(tags[src_key])
                elif src_key.endswith("status"):
                    kwargs[dst_key] = _coerce_status(tags[src_key])
                elif src_key.endswith("phase"):
                    kwargs[dst_key] = _coerce_phase(tags[src_key])
                else:
                    kwargs[dst_key] = tags[src_key]

        csm = CanonicalStructuredMessage(**kwargs)
        confidence = 1.0
        if not csm.summary:
            confidence = 0.5
        if csm.status == CSMStatus.PENDING:
            confidence = min(confidence, 0.5)
        return AdapterResult(
            csm=csm,
            confidence=confidence,
            parse_errors=[],
            source_provider=self.provider,
        )


class GenericOutputAdapter(OutputAdapter):
    """Adapter for generic plain-text payloads.

    Emits ``source_contract="plain"`` CSMs with ``status=COMPLETED``
    (we accept the best-effort parse as-is) and a modest confidence
    score. ``minimax`` / ``cliproxy`` are the canonical users of this
    adapter class.
    """

    def __init__(self, provider: str, *, confidence: float = 0.7) -> None:
        self.provider = provider
        self._confidence = float(confidence)

    def normalize(
        self,
        raw: Any,
        context: dict[str, Any] | None = None,
    ) -> AdapterResult:
        context = context or {}
        run_id = str(context.get("run_id", "") or "")
        chunk_id = str(context.get("chunk_id", "") or "")

        if isinstance(raw, dict):
            text = (
                raw.get("content")
                or raw.get("text")
                or raw.get("message")
                or raw.get("stdout")
                or ""
            )
            if not isinstance(text, str):
                text = str(text)
        elif raw is None:
            text = ""
        elif isinstance(raw, str):
            text = raw
        else:
            text = str(raw)

        # Best-effort JSON-content extraction if the text looks like a
        # JSONL/JSON envelope (mirrors the historical behaviour).
        condensed = extract_condensed(text) or text
        csm = CanonicalStructuredMessage(
            run_id=run_id,
            chunk_id=chunk_id,
            status=CSMStatus.COMPLETED,
            phase=CSMPhase.OPERATOR,
            progress=1.0,
            summary=condensed,
            source_contract="plain",
            confidence_level=self._confidence,
        )
        return AdapterResult(
            csm=csm,
            confidence=self._confidence,
            parse_errors=[],
            source_provider=self.provider,
        )


class AdapterRegistry:
    """Singleton-backed registry for output adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, OutputAdapter] = {}

    def register(self, name: str, adapter: OutputAdapter) -> None:
        """Register ``adapter`` under ``name``."""
        self._adapters[name] = adapter

    def get(self, name: str) -> OutputAdapter | None:
        """Return the adapter registered for ``name``, or ``None``."""
        return self._adapters.get(name)

    def list_adapters(self) -> list[str]:
        """Return all registered adapter names (canonical method)."""
        return sorted(self._adapters.keys())

    # Aliases retained for backwards compat with the stub-era API.
    def keys(self) -> list[str]:
        """Alias for :meth:`list_adapters`."""
        return self.list_adapters()

    def pop(self, name: str, default: Any = ...) -> OutputAdapter | None:
        """Remove and return the adapter for ``name``.

        ``default`` is returned when ``name`` is not registered;
        omitting ``default`` raises ``KeyError`` (matching the
        :meth:`dict.pop` contract).
        """
        if default is ...:
            return self._adapters.pop(name)
        return self._adapters.pop(name, default)

    def __getitem__(self, name: str) -> OutputAdapter:
        """Dict-style access — raises :class:`KeyError` when missing."""
        return self._adapters[name]

    def __setitem__(self, name: str, adapter: OutputAdapter) -> None:
        """Dict-style assignment — delegates to :meth:`register`."""
        self.register(name, adapter)

    def __delitem__(self, name: str) -> None:
        """Dict-style deletion — raises :class:`KeyError` when missing."""
        del self._adapters[name]

    def __iter__(self) -> Any:
        """Iterate over registered adapter names."""
        return iter(self._adapters)

    def __contains__(self, name: object) -> bool:
        return name in self._adapters

    def __len__(self) -> int:
        return len(self._adapters)


def get_adapter(name: str) -> OutputAdapter:
    """Return the adapter for ``name``.

    Raises :class:`KeyError` when ``name`` is not registered — matches
    the historical contract pinned by
    ``tests/test_wl145_l10_contracts_signature_parity.py``.
    """
    adapter = ADAPTER_REGISTRY.get(name)
    if adapter is None:
        raise KeyError(name)
    return adapter


ADAPTER_REGISTRY: AdapterRegistry = AdapterRegistry()


#: Back-compat alias for :data:`ADAPTER_REGISTRY`. The legacy stub-era
#: module exposed ``ADAPTERS`` as a dict-like registry; the canonical
#: ``AdapterRegistry`` instance satisfies the same dict-key /
#: ``__getitem__`` contract so this alias is API-stable.
ADAPTERS: AdapterRegistry = ADAPTER_REGISTRY


# ---------------------------------------------------------------------------
# Provider registration (module import side effect).
# ---------------------------------------------------------------------------

_XML_PROVIDERS: tuple[str, ...] = (
    "copilot",
    "gemini",
    "claude",
    "codex",
    "cursor",
    "cursor-agent",
    "antigravity",
)
_GENERIC_PROVIDERS: tuple[str, ...] = ("minimax", "cliproxy")


def _register_default_providers() -> None:
    # The canonical ``"xml"`` provider is registered first so legacy
    # callers (``ADAPTERS["xml"]``, ``get_adapter("xml")``) resolve to
    # the :class:`XMLOutputAdapter` instance under the canonical name.
    ADAPTER_REGISTRY.register("xml", XMLOutputAdapter("xml"))
    for name in _XML_PROVIDERS:
        ADAPTER_REGISTRY.register(name, XMLOutputAdapter(name))
    for name in _GENERIC_PROVIDERS:
        ADAPTER_REGISTRY.register(name, GenericOutputAdapter(name))


_register_default_providers()


def register_adapter(name: str, adapter: OutputAdapter) -> None:
    """Register ``adapter`` under ``name`` on the canonical :data:`ADAPTER_REGISTRY`."""
    ADAPTER_REGISTRY.register(name, adapter)


# ---------------------------------------------------------------------------
# JSONL / JSON envelope extraction used by the fallback path.
# ---------------------------------------------------------------------------

_CONDENSED_JSON_RE = re.compile(r'\{\s*"[^"]+"\s*:[^}]*\}')


def extract_condensed(text: str) -> str:
    """Best-effort extraction of a string summary from JSONL / JSON content.

    Used by the :func:`normalize_output` fallback path to surface a
    human-readable summary when the input is not XML-tagged. Returns
    the input verbatim when no JSON envelope is detectable.
    """
    if not text:
        return ""
    # JSON brace pair (greedy enough for a single top-level object).
    match = _CONDENSED_JSON_RE.search(text)
    if match:
        try:
            decoded = json.loads(match.group(0))
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, dict):
            for key in ("content", "message", "text", "summary"):
                value = decoded.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    # Otherwise try to parse the whole input as JSON.
    text_stripped = text.strip()
    if text_stripped.startswith(("{", "[")):
        try:
            decoded = json.loads(text_stripped)
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, dict):
            for key in ("content", "message", "text", "summary", "type", "role"):
                value = decoded.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return text.strip()


# ---------------------------------------------------------------------------
# The public normalize_output() entry point.
# ---------------------------------------------------------------------------

_FALLBACK_CONFIDENCE: float = 0.5


def normalize_output(
    provider: str,
    raw: Any,
    *,
    allow_fallback: bool = True,
    context: dict[str, Any] | None = None,
) -> AdapterResult:
    """Normalise a raw agent payload to an :class:`AdapterResult`.

    Resolution order:

    1. Look up the registered adapter for ``provider`` via the
       module-level :func:`get_adapter` (so tests can patch the
       lookup) and delegate to :meth:`OutputAdapter.normalize`.
    2. If the adapter returns a "no XML tags" parse failure *and*
       ``allow_fallback`` is true, fall back to :func:`extract_condensed`
       and produce a ``source_contract="fallback-plain"`` CSM.
    3. On adapter exception / registry miss with ``allow_fallback``,
       fall back to the plain-text extraction helper.
    4. On registry miss or adapter exception with ``allow_fallback=False``,
       raise :class:`SemanticValidationError`.
    """
    try:
        adapter = get_adapter(provider)
    except KeyError:
        adapter = None
    if adapter is not None:
        try:
            result = adapter.normalize(raw, context=context)
        except Exception:
            if not allow_fallback:
                raise SemanticValidationError(
                    f"Adapter for {provider} raised and fallback is disabled"
                ) from None
            return _fallback_result(provider, raw, context)
        # If the adapter reports a no-xml-tags failure (plain text
        # payload), downgrade to a plain-text fallback rather than
        # reporting a parse failure. Truncated XML payloads are
        # preserved (the streaming consumer needs to know to retry).
        if (
            allow_fallback
            and "no_xml_tags_detected" in (result.parse_errors or [])
            and "parse_truncated" not in (result.parse_errors or [])
        ):
            return _fallback_result(provider, raw, context)
        # When fallback is disabled and the adapter produced a parse
        # failure, surface it as a SemanticValidationError so callers
        # can react explicitly (matches the contract pinned by
        # ``tests/test_unit_contracts_adapters.py``).
        if not allow_fallback and result.parse_errors:
            raise SemanticValidationError(
                f"Adapter for {provider} failed validation: {', '.join(result.parse_errors)}"
            )
        return result

    if not allow_fallback:
        raise SemanticValidationError(
            f"No adapter registered for {provider!r} and fallback is disabled"
        )
    return _fallback_result(provider, raw, context)


def _fallback_result(
    provider: str,
    raw: Any,
    context: dict[str, Any] | None,
) -> AdapterResult:
    """Build a fallback AdapterResult from a raw payload."""
    context = context or {}
    if isinstance(raw, str):
        text = raw
    elif isinstance(raw, dict):
        text = raw.get("stdout") or raw.get("content") or raw.get("text") or ""
        if not isinstance(text, str):
            text = str(text)
    else:
        text = "" if raw is None else str(raw)

    summary = extract_condensed(text) or text
    csm = CanonicalStructuredMessage(
        run_id=str(context.get("run_id", "") or ""),
        chunk_id=str(context.get("chunk_id", "") or ""),
        status=CSMStatus.PENDING,
        phase=CSMPhase.UNKNOWN,
        summary=summary,
        source_contract="fallback-plain",
        confidence_level=_FALLBACK_CONFIDENCE,
    )
    return AdapterResult(
        csm=csm,
        confidence=_FALLBACK_CONFIDENCE,
        parse_errors=[],
        source_provider=str(provider or ""),
    )


# ---------------------------------------------------------------------------
# Compat / type-stubs preserved from the stub era.
# ---------------------------------------------------------------------------


class ContractAdapter:
    """Back-compat alias retained so legacy imports resolve.

    New code should use :class:`OutputAdapter` directly.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def adapt(self, data: Any) -> Any:
        return data


class ContractValidator:
    """Back-compat stub retained for legacy imports."""

    def validate(self, data: Any, schema: dict[str, Any]) -> bool:
        return True


# ---------------------------------------------------------------------------
# Internal coercion helpers.
# ---------------------------------------------------------------------------


_STATUS_ALIAS_MAP: dict[str, CSMStatus] = {
    "completed": CSMStatus.COMPLETED,
    "complete": CSMStatus.COMPLETED,
    "done": CSMStatus.COMPLETED,
    "success": CSMStatus.COMPLETED,
    "succeeded": CSMStatus.COMPLETED,
    "ok": CSMStatus.COMPLETED,
    "in_progress": CSMStatus.IN_PROGRESS,
    "inprogress": CSMStatus.IN_PROGRESS,
    "in-progress": CSMStatus.IN_PROGRESS,
    "running": CSMStatus.IN_PROGRESS,
    "processing": CSMStatus.IN_PROGRESS,
    "pending": CSMStatus.PENDING,
    "queued": CSMStatus.PENDING,
    "failed": CSMStatus.FAILED,
    "failure": CSMStatus.FAILED,
    "error": CSMStatus.FAILED,
    "blocked": CSMStatus.BLOCKED,
    "cancelled": CSMStatus.CANCELLED,
    "canceled": CSMStatus.CANCELLED,
    "skipped": CSMStatus.CANCELLED,
}


def _coerce_status(value: Any) -> CSMStatus:
    """Best-effort coerce ``value`` to a :class:`CSMStatus` member."""
    if isinstance(value, CSMStatus):
        return value
    if isinstance(value, str):
        key = value.strip().lower()
        if not key:
            return CSMStatus.PENDING
        if key in _STATUS_ALIAS_MAP:
            return _STATUS_ALIAS_MAP[key]
        try:
            return CSMStatus[value.strip().upper()]
        except KeyError:
            pass
    return CSMStatus.PENDING


def _coerce_phase(value: Any) -> CSMPhase:
    """Best-effort coerce ``value`` to a :class:`CSMPhase` member."""
    if isinstance(value, CSMPhase):
        return value
    if isinstance(value, str):
        key = value.strip()
        if not key:
            return CSMPhase.UNKNOWN
        try:
            return CSMPhase[key.upper()]
        except KeyError:
            pass
    return CSMPhase.UNKNOWN


def _coerce_progress(value: Any) -> float:
    """Coerce a progress value into the ``[0.0, 1.0]`` range.

    * Percent strings (``"75%"``) → ``0.75``.
    * Integers / floats ``>= 2`` → divided by 100.
    * Floats already in ``[0.0, 1.0]`` → returned unchanged.
    * Unparseable → ``1.0`` (matches the historical "missing progress
      is treated as done" behaviour pinned by
      ``tests/test_integration_normalization_pipeline.py``).
    """
    if isinstance(value, bool):
        return 1.0
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric >= 2.0:
            return min(max(numeric / 100.0, 0.0), 1.0)
        return min(max(numeric, 0.0), 1.0)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return 1.0
        percent_match = _PERCENT_RE.match(cleaned)
        if percent_match:
            return min(max(float(percent_match.group(1)) / 100.0, 0.0), 1.0)
        number_match = _NUMBER_RE.match(cleaned)
        if number_match:
            numeric = float(number_match.group(1))
            if numeric >= 2.0:
                return min(max(numeric / 100.0, 0.0), 1.0)
            return min(max(numeric, 0.0), 1.0)
    return 1.0


def _split_lines(value: str) -> list[str]:
    """Split a multi-line string into a ``list[str]`` of non-empty segments."""
    return [segment.strip() for segment in value.splitlines() if segment.strip()]
