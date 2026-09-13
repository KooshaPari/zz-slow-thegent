"""Progressive disclosure for thegent decisions (WP-4002, FR-015, FR-039, P-092).

When thegent makes a routing, override, or pre-check decision, a human operator
frequently only needs a one-line answer.  But under *dig-deeper* pressure, the
operator needs to follow the chain of reasoning all the way down to the policy
rule and audit-log line that produced the verdict.

This module provides:

* :class:`DisclosureLevel` — 0:CONCISE / 1:SUMMARY / 2:DETAILED / 3:DEEPDIVE
* :class:`DecisionExplanation` — a structured explanation object with
  progressive layers; renders shorter or longer based on the chosen level.
* :class:`ExplanationBuilder` — fluent helper for the runtime to assemble
  explanations without having to know the disclosure grammar.
* :func:`render_explanation` — convenience one-shot renderer.

The disclosure grammar maps directly onto the cockpit progress bar (P-081)
and the explanations companion (P-092).  Levels are designed so::

    level 0 -> one line
    level 1 -> three lines + badge
    level 2 -> ~10 lines + table
    level 3 -> full reasoning chain + audit refs

Traces to: FR-015 (progressive disclosure), FR-039 (transport hints),
          P-092 (explanations companion), WP-4002.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------


class DisclosureLevel(IntEnum):
    """How much to disclose (IntEnum so callers can ++ / -- safely)."""

    CONCISE = 0
    SUMMARY = 1
    DETAILED = 2
    DEEPDIVE = 3


_LEVEL_NAMES = {
    DisclosureLevel.CONCISE: "CONCISE",
    DisclosureLevel.SUMMARY: "SUMMARY",
    DisclosureLevel.DETAILED: "DETAILED",
    DisclosureLevel.DEEPDIVE: "DEEPDIVE",
}


def _level_name(level: int) -> str:
    """Best-effort coercion of an arbitrary int to a level name."""
    try:
        return _LEVEL_NAMES[DisclosureLevel(level)]
    except (ValueError, KeyError):
        return f"L{level}"


# ---------------------------------------------------------------------------
# Explanation payload
# ---------------------------------------------------------------------------


@dataclass
class DecisionExplanation:
    """Structured explanation of a single thegent decision.

    Attributes are intentionally ``Any``-typed so callers can attach rich
    metadata (audit refs, hyperlinks, deep-dive breadcrumbs).  Empty
    attributes are skipped at render time.
    """

    title: str
    verdict: str = ""
    reason: str = ""
    reason_code: str = ""
    rule_id: str | None = None
    confidence: float | None = None
    citations: list[str] = field(default_factory=list)
    chain: list[str] = field(default_factory=list)
    rationale_steps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    audit_refs: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    # source attribution (which subsystem produced this explanation)
    source: str = "policy_engine"

    def with_citation(self, ref: str) -> DecisionExplanation:
        """Return self with a citation added; fluent helper."""
        if ref and ref not in self.citations:
            self.citations.append(ref)
        return self

    def with_chain_step(self, step: str) -> DecisionExplanation:
        """Append a step to the reasoning chain."""
        if step and step not in self.chain:
            self.chain.append(step)
        return self

    def with_audit_ref(self, ref: str) -> DecisionExplanation:
        if ref and ref not in self.audit_refs:
            self.audit_refs.append(ref)
        return self

    def with_action(self, action: str) -> DecisionExplanation:
        if action and action not in self.actions:
            self.actions.append(action)
        return self


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ExplanationBuilder:
    """Fluent builder for :class:`DecisionExplanation`.

    Typical use::

        e = (
            ExplanationBuilder()
            .title("Override applied")
            .verdict("ALLOW")
            .reason("hotfix")
            .confidence(0.92)
            .step("evaluated federated rule r1")
            .step("override active for r1")
            .citation("docs/governance/policies.md#r1")
            .build()
        )
        print(render_explanation(e, level=DisclosureLevel.SUMMARY))
    """

    def __init__(self) -> None:
        self._exp = DecisionExplanation(title="")

    def title(self, title: str) -> ExplanationBuilder:
        self._exp.title = title
        return self

    def verdict(self, verdict: str) -> ExplanationBuilder:
        self._exp.verdict = verdict
        return self

    def reason(self, reason: str) -> ExplanationBuilder:
        self._exp.reason = reason
        return self

    def reason_code(self, code: str) -> ExplanationBuilder:
        self._exp.reason_code = code
        return self

    def rule_id(self, rid: str) -> ExplanationBuilder:
        self._exp.rule_id = rid
        return self

    def confidence(self, value: float | None) -> ExplanationBuilder:
        self._exp.confidence = value
        return self

    def source(self, source: str) -> ExplanationBuilder:
        self._exp.source = source
        return self

    def citation(self, ref: str) -> ExplanationBuilder:
        self._exp.with_citation(ref)
        return self

    def step(self, description: str) -> ExplanationBuilder:
        self._exp.with_chain_step(description)
        return self

    def rationale(self, *steps: str) -> ExplanationBuilder:
        for s in steps:
            if s:
                self._exp.rationale_steps.append(s)
        return self

    def audit(self, ref: str) -> ExplanationBuilder:
        self._exp.with_audit_ref(ref)
        return self

    def action(self, description: str) -> ExplanationBuilder:
        self._exp.with_action(description)
        return self

    def metadata(self, **values: Any) -> ExplanationBuilder:
        self._exp.metadata.update(values)
        return self

    def build(self) -> DecisionExplanation:
        """Return the built :class:`DecisionExplanation`.

        Calling ``build()`` does *not* invalidate the builder; additional calls
        return the same payload.  This is intentional — callers can keep
        appending rationale after the first build for incremental disclosure.
        """
        return self._exp


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def render_explanation(
    exp: DecisionExplanation,
    *,
    level: int | DisclosureLevel = DisclosureLevel.SUMMARY,
    width: int = 80,
) -> str:
    """Render ``exp`` at the requested disclosure level.

    Args:
        exp: the structured explanation payload.
        level: which disclosure level to render (0..3).  Higher levels emit
            strictly more detail; lower levels emit strictly less.
        width: target output width in columns.

    Returns:
        A multi-line, human-readable string safe to embed in TTYs and logs.
    """
    try:
        lvl = DisclosureLevel(level)
    except (ValueError, KeyError):
        lvl = DisclosureLevel.CONCISE

    if lvl == DisclosureLevel.CONCISE:
        return _render_concise(exp, width=width)
    if lvl == DisclosureLevel.SUMMARY:
        return _render_summary(exp, width=width)
    if lvl == DisclosureLevel.DETAILED:
        return _render_detailed(exp, width=width)
    return _render_deepdive(exp, width=width)


def _hr(width: int, char: str = "-") -> str:
    return char * max(8, width)


def _badge(verdict: str) -> str:
    v = (verdict or "").lower()
    if v in ("allow", "yes", "approved"):
        return "[OK]"
    if v in ("deny", "no", "blocked"):
        return "[DENY]"
    if v in ("warn", "warning"):
        return "[WARN]"
    if v:
        return f"[{v.upper()[:6]}]"
    return "[?]"


def _pad(text: str, width: int) -> str:
    if len(text) >= width:
        return text
    return text + " " * (width - len(text))


def _render_concise(exp: DecisionExplanation, *, width: int) -> str:
    badge = _badge(exp.verdict)
    summary = exp.reason or exp.title or "(no reason given)"
    return f"{badge} {summary}"


def _core_attribute_lines(
    exp: DecisionExplanation,
    *,
    label_width: int,
    align: bool = True,
    include_source: bool = True,
) -> list[str]:
    """Render the per-level ``reason / reason_code / rule_id / confidence / source`` block.

    NEW-23 (SOTA fourth-pass): extracted from the three level-specific
    renderers (``_render_summary``, ``_render_detailed``,
    ``_render_deepdive``) so the column-padding contract lives in one
    place. Two modes:

    * ``align=True`` (DETAILED/DEEPDIVE): every label is padded with
      spaces so values start at column ``label_width`` regardless of
      label length.
    * ``align=False`` (SUMMARY compact): every label is followed by
      exactly one space — the historical "single-space" SUMMARY form
      pinned by ``test_summary_includes_rule`` in
      ``tests/test_unit_ux_explanations.py``.

    SUMMARY also historically omits ``source:`` (the original
    ``_render_summary`` only emitted reason / reason_code / rule_id /
    confidence), so ``include_source`` defaults to ``True`` for
    DETAILED/DEEPDIVE and is set to ``False`` by SUMMARY to preserve
    byte-for-byte output.

    Each level passes its own ``label_width`` (SUMMARY=0,
    DETAILED=14, DEEPDIVE=17) so the visual hierarchy is preserved;
    the lines themselves are byte-identical to the previous
    per-renderer copies, which keeps downstream SOTA regression
    tests pinned.
    """
    lines: list[str] = []
    pairs: list[tuple[str, str]] = []
    if exp.reason:
        pairs.append(("reason:", exp.reason))
    if exp.reason_code:
        pairs.append(("reason_code:", exp.reason_code))
    if exp.rule_id:
        pairs.append(("rule_id:", exp.rule_id))
    if exp.confidence is not None:
        pairs.append(("confidence:", f"{exp.confidence:.2f}"))
    if include_source and exp.source:
        pairs.append(("source:", exp.source))
    for label, value in pairs:
        if align:
            padding = max(1, label_width - len(label))
            lines.append(f"{label}{' ' * padding}{value}")
        else:
            lines.append(f"{label} {value}")
    return lines


def _header_lines(exp: DecisionExplanation, *, width: int) -> list[str]:
    """Render the title + verdict badge + ``=`` separator shared by all levels.

    NEW-23 (SOTA fourth-pass): extracted from the three level-specific
    renderers so the title-row alignment contract (``width - 6`` for
    the title padding) is enforced in one place.
    """
    return [
        f"{_pad(exp.title, width - 6)} {_badge(exp.verdict)}",
        _hr(width, "="),
    ]


def _actions_lines(exp: DecisionExplanation) -> list[str]:
    """Render the optional ``suggested actions:`` block (shared by all levels)."""
    if not exp.actions:
        return []
    out = ["suggested actions:"]
    out.extend(f"  - {action}" for action in exp.actions)
    return out


def _citations_lines(exp: DecisionExplanation) -> list[str]:
    """Render the optional ``citations:`` block (DETAILED + DEEPDIVE)."""
    if not exp.citations:
        return []
    out = ["citations:"]
    out.extend(f"  - {c}" for c in exp.citations)
    return out


def _chain_lines(exp: DecisionExplanation, *, width: int) -> list[str]:
    """Render the optional ``reasoning chain:`` block (DETAILED + DEEPDIVE)."""
    if not exp.chain:
        return []
    out = [_hr(width, "-"), "reasoning chain:"]
    out.extend(f"  {i}. {step}" for i, step in enumerate(exp.chain, 1))
    return out


def _metadata_lines(exp: DecisionExplanation, *, width: int) -> list[str]:
    """Render the optional ``metadata:`` block (DETAILED + DEEPDIVE)."""
    if not exp.metadata:
        return []
    out = [_hr(width, "-"), "metadata:"]
    out.extend(f"  {k}: {v}" for k, v in sorted(exp.metadata.items()))
    return out


def _rationale_lines(exp: DecisionExplanation, *, width: int) -> list[str]:
    """Render the optional ``rationale:`` block (DEEPDIVE only)."""
    if not exp.rationale_steps:
        return []
    out = [_hr(width, "-"), "rationale:"]
    out.extend(f"  [{i}] {step}" for i, step in enumerate(exp.rationale_steps, 1))
    return out


def _audit_refs_lines(exp: DecisionExplanation, *, width: int) -> list[str]:
    """Render the optional ``audit:`` block (DEEPDIVE only)."""
    if not exp.audit_refs:
        return []
    out = [_hr(width, "-"), "audit:"]
    out.extend(f"  - {r}" for r in exp.audit_refs)
    return out


def _render_summary(exp: DecisionExplanation, *, width: int) -> str:
    """SUMMARY level: title + verdict + a handful of attributes + actions.

    NEW-23 (SOTA fourth-pass): delegates to :func:`_header_lines` and
    :func:`_core_attribute_lines` (``align=False`` for the historical
    single-space SUMMARY layout pinned by SOTA regression tests) so
    the column-padding contract is shared with DETAILED and DEEPDIVE.
    """
    lines = _header_lines(exp, width=width)
    lines.extend(
        _core_attribute_lines(exp, label_width=0, align=False, include_source=False)
    )
    lines.extend(_actions_lines(exp))
    return "\n".join(lines)


def _render_detailed(exp: DecisionExplanation, *, width: int) -> str:
    """DETAILED level: SUMMARY + source + citations + chain + metadata.

    NEW-23 (SOTA fourth-pass): delegates the shared blocks to the
    helper family so the per-level composition reads top-to-bottom and
    the column-padding contract is single-sourced. ``label_width=14``
    reproduces the historical DETAILED alignment (values start at
    column 14 — e.g. ``reason:       value`` is 7 + 7 spaces = 14).
    """
    lines = _header_lines(exp, width=width)
    lines.extend(_core_attribute_lines(exp, label_width=14))
    lines.extend(_citations_lines(exp))
    lines.extend(_actions_lines(exp))
    lines.extend(_chain_lines(exp, width=width))
    lines.extend(_metadata_lines(exp, width=width))
    return "\n".join(lines)


def _render_deepdive(exp: DecisionExplanation, *, width: int) -> str:
    """DEEPDIVE level: DETAILED + rationale + audit_refs.

    NEW-23 (SOTA fourth-pass): adds the rationale / audit-only blocks
    via the dedicated helpers. ``label_width=17`` reproduces the
    historical DEEPDIVE alignment (values start at column 17 — e.g.
    ``reason:          value`` is 7 + 10 spaces = 17).
    """
    lines = _header_lines(exp, width=width)
    lines.extend(_core_attribute_lines(exp, label_width=17))
    lines.extend(_citations_lines(exp))
    lines.extend(_actions_lines(exp))
    lines.extend(_chain_lines(exp, width=width))
    lines.extend(_rationale_lines(exp, width=width))
    lines.extend(_audit_refs_lines(exp, width=width))
    lines.extend(_metadata_lines(exp, width=width))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Exit-code and exception explanations (Lane 2 UX polish)
# ---------------------------------------------------------------------------

EXPLANATION_MAP: dict[int, str] = {
    0: "success — operation completed without errors",
    1: "general error — check logs for details",
    2: "misuse — incorrect command-line usage or bad arguments",
    3: "policy deny — check governance rules",
    4: "replay mismatch — snapshot fields differ",
    127: "command not found — verify PATH or install the dependency",
    130: "interrupted — process was killed by SIGINT (Ctrl-C)",
}


def explain_exit_code(code: int) -> str:
    """Map a process exit code to a human-readable, actionable explanation.

    Args:
        code: The integer exit code from a subprocess.

    Returns:
        A one-line explanation the operator can act on.
    """
    if code in EXPLANATION_MAP:
        return EXPLANATION_MAP[code]
    return f"exit code {code} — consult the process documentation"


# Exception-type to hint mapping (checked in order)
_EXCEPTION_HINTS: list[tuple[type[Exception], str]] = [
    (TimeoutError, "timeout — increase the timeout or check network latency"),
    (PermissionError, "permission denied — check file/process permissions"),
    (ConnectionError, "connection failed — verify endpoint availability"),
    (
        ConnectionRefusedError,
        "connection refused — ensure the target service is running",
    ),
    (FileNotFoundError, "file not found — verify the path exists"),
    (ValueError, "validation error — check input format and constraints"),
    (KeyError, "missing key — verify the expected data structure"),
]


def explain_exception(exc: Exception) -> str:
    """Classify an exception into a category with an actionable one-line hint.

    Args:
        exc: The caught exception.

    Returns:
        A one-line string describing the category and what to try.
    """
    for exc_type, hint in _EXCEPTION_HINTS:
        if isinstance(exc, exc_type):
            return hint
    name = type(exc).__name__
    msg = str(exc).strip()
    summary = msg[:60] + "…" if len(msg) > 60 else msg
    return f"unexpected {name} — {summary}" if summary else f"unexpected {name}"


# ---------------------------------------------------------------------------
# Compose helper
# ---------------------------------------------------------------------------


def render_decision_chain(
    explanations: Sequence[DecisionExplanation],
    *,
    level: int | DisclosureLevel = DisclosureLevel.SUMMARY,
    width: int = 80,
    separator: str = "\n\n",
) -> str:
    """Render a sequence of explanations at the same level, joined cleanly."""
    try:
        lvl = DisclosureLevel(level)
    except (ValueError, KeyError):
        lvl = DisclosureLevel.CONCISE
    parts = [render_explanation(e, level=lvl, width=width) for e in explanations]
    return separator.join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Re-export
# ---------------------------------------------------------------------------


__all__ = [
    "EXPLANATION_MAP",
    "DecisionExplanation",
    "DisclosureLevel",
    "ExplanationBuilder",
    "explain_exception",
    "explain_exit_code",
    "render_decision_chain",
    "render_explanation",
]
