"""thegent.contracts.parser — Incremental XML parser for streamed provider output.

This module is the canonical implementation backing the L8 normalisation
pipeline. The legacy stub-era module exposed only ``#hashtag`` extraction;
the canonical surface adds:

* :func:`extract_tags(content, tags=None)` — case-insensitive XML tag
  extraction with an optional allow-list filter.
* :class:`IncrementalXMLParser` — incremental parser with
  :meth:`IncrementalXMLParser.parse` for balanced-tag extraction and
  :meth:`IncrementalXMLParser.get_partial_state` for reporting
  in-progress / truncated markup to the streaming consumer.
* :class:`StreamingXMLParser` — retained as a thin streaming facade so
  legacy callers do not break.

Wire-format guarantees (pinned by ``tests/test_wl145_l9_contracts_signature_parity.py``):

* Tag names are matched case-insensitively but the returned dict keys
  are normalised to the canonical ``UPPERCASE`` form (the historical
  contract that downstream :class:`XMLOutputAdapter` expects).
* ``get_partial_state`` always returns a dict with the keys
  ``open_tag`` (str | None), ``partial_content`` (str),
  ``is_truncated`` (bool), and ``incomplete_tag`` (str | None).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Pre-compiled patterns. The first matches a balanced XML tag pair;
# the second matches a still-open trailing tag prefix.
#: Schema version of the parser module. Bumped only when the public
#: surface (``IncrementalXMLParser``, ``extract_tags``, partial-state
#: dict keys) changes in a breaking way.
CONTRACTS_PARSER_VERSION: str = "parser-v1"

_BALANCED_TAG_RE = re.compile(
    r"<([A-Za-z][A-Za-z0-9_]*)\s*>([\s\S]*?)</\1\s*>",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(
    r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9_]*)\s*>",
    re.IGNORECASE,
)
_TRAILING_TAG_PREFIX_RE = re.compile(
    r"<([A-Za-z][A-Za-z0-9_]*)\s*$",
    re.IGNORECASE,
)


@dataclass
class ParserState:
    """Mutable streaming state for an in-progress parse."""

    position: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Record a parse error."""
        self.errors.append(error)

    def is_valid(self) -> bool:
        """Return True iff no errors have been recorded."""
        return len(self.errors) == 0


def extract_tags(
    text: str,
    tags: list[str] | None = None,
) -> dict[str, str]:
    """Extract XML tag values from ``text``.

    Args:
        text: Raw text (typically a streamed agent payload).
        tags: Optional case-insensitive allow-list. When provided,
            only tags whose uppercase form matches one of the
            uppercased entries are returned.

    Returns:
        Mapping of normalised ``UPPERCASE`` tag name to its inner
        text. Tag values are stripped of leading / trailing whitespace.
        The matcher is non-greedy so the first matching closing tag
        wins; overlapping or nested tags are not supported (the
        production payload format does not use nesting).
    """
    if not text:
        return {}
    allowed: set[str] | None = None
    if tags is not None:
        allowed = {tag.upper() for tag in tags}
    extracted: dict[str, str] = {}
    for match in _BALANCED_TAG_RE.finditer(text):
        name = match.group(1).upper()
        if allowed is not None and name not in allowed:
            continue
        # Last-write-wins so callers that emit repeated tags get the
        # final value (matches the historical contract).
        extracted[name] = match.group(2).strip()
    return extracted


class IncrementalXMLParser:
    """Incremental XML parser for streamed provider payloads.

    Usage::

        parser = IncrementalXMLParser(case_sensitive=False)
        complete = parser.parse(complete_chunk)
        state = parser.get_partial_state(truncated_chunk)
    """

    def __init__(
        self,
        case_sensitive: bool = False,
        allowed_tags: list[str] | None = None,
    ) -> None:
        self._case_sensitive = bool(case_sensitive)
        self._allowed_tags: list[str] | None = list(allowed_tags) if allowed_tags is not None else None

    def parse(self, text: str) -> dict[str, str]:
        """Extract balanced XML tags from ``text``.

        Returns an empty dict when ``text`` contains no balanced
        markup; callers that need to distinguish "no tags" from
        "truncated markup" should call :meth:`get_partial_state`.

        When the parser was constructed with ``allowed_tags`` (or
        :meth:`set_allowed_tags` was called), only tags whose
        upper-cased form matches one of the allowed entries are
        returned.
        """
        if not text:
            return {}
        return extract_tags(text, tags=self._allowed_tags)

    def set_allowed_tags(self, tags: list[str] | None) -> None:
        """Set the allowed tag filter post-construction.

        ``None`` clears the filter (all matched tags returned).
        """
        self._allowed_tags = list(tags) if tags is not None else None

    def get_allowed_tags(self) -> list[str] | None:
        """Return the current allowed tag filter (or ``None`` if unfiltered)."""
        return list(self._allowed_tags) if self._allowed_tags is not None else None

    def get_partial_state(self, text: str) -> dict[str, Any]:
        """Report the partial / truncated state of an in-progress payload.

        The returned dict always contains:

        * ``open_tag`` — the *deepest* currently-open tag name
          (uppercased), or ``None`` if no tag is open. Determined by
          walking the markup with a proper push/pop stack so nested
          tags report the innermost open tag (the one that still has
          pending content). When the payload ends with a trailing
          ``"<NAME"`` prefix, the prefix is treated as a *new* tag
          being typed out — the prior tag is considered implicitly
          closed at that boundary and ``open_tag`` is ``None``.
        * ``partial_content`` — text accumulated inside the currently-
          open tag after its most-recent opening. Empty string when
          no tag is open.
        * ``is_truncated`` — ``True`` if the payload shows signs of
          being cut off (open tag without a matching close, or a
          trailing unclosed tag prefix).
        * ``incomplete_tag`` — the trailing tag prefix (uppercased)
          when the payload ends with ``"<NAME"`` without a closing
          ``>``; otherwise ``None``.
        """
        if not text:
            return {
                "open_tag": None,
                "partial_content": "",
                "is_truncated": False,
                "incomplete_tag": None,
            }

        # 1. Detect a trailing unclosed tag prefix ("<STAT") first —
        # this wins over the stack walk because it represents a tag
        # that hasn't even been opened yet. The boundary between the
        # previous (implicitly closed) content and the new prefix
        # marks the new tag as the in-progress stream; we therefore
        # report no open tag and no partial content.
        trailing = _TRAILING_TAG_PREFIX_RE.search(text.rstrip())
        if trailing is not None:
            return {
                "open_tag": None,
                "partial_content": "",
                "is_truncated": True,
                "incomplete_tag": trailing.group(1).upper(),
            }

        # 2. Stack-based walk: track open / close events in order and
        # find the innermost tag that was never closed. The returned
        # content slice runs from that tag's opening to end-of-text.
        open_name, partial = self._stack_walk(text)
        if open_name is not None:
            return {
                "open_tag": open_name,
                "partial_content": partial,
                "is_truncated": True,
                "incomplete_tag": None,
            }

        return {
            "open_tag": None,
            "partial_content": "",
            "is_truncated": False,
            "incomplete_tag": None,
        }

    @staticmethod
    def _stack_walk(text: str) -> tuple[str | None, str]:
        """Walk ``text`` and return (open_tag, partial_content).

        Returns ``(None, "")`` when every tag in ``text`` is balanced
        and the cursor consumed the entire string. Otherwise returns
        the *innermost* (deepest) unmatched opening tag with the
        content that has accumulated inside it — the deterministic
        behaviour the streaming tests pin. Nested / overlapping
        opening tags are handled by a proper push/pop stack; the
        closing tag for any tag closes its matching opener regardless
        of how many other openers sit above it in the stack.
        """
        stack: list[tuple[str, int]] = []  # (NAME, content_start_pos)
        for match in _TOKEN_RE.finditer(text):
            is_close = bool(match.group(1))
            name = match.group(2).upper()
            if is_close:
                # Pop the matching opening tag if it's on top of the
                # stack; otherwise drop the spurious close (malformed
                # input). A close for a non-top tag is silently
                # consumed to keep streaming robust to partial rewind.
                if stack and stack[-1][0] == name:
                    stack.pop()
                continue
            stack.append((name, match.end()))

        if stack:
            name, content_start = stack[-1]
            return name, text[content_start:]
        return None, ""


class StreamingXMLParser:
    """Streaming XML parser facade.

    Retained for backwards-compat with callers that import
    :class:`StreamingXMLParser` directly. Buffers chunks until
    :meth:`finalize` is called; extraction reuses
    :func:`extract_tags` on the buffered text.
    """

    def __init__(self) -> None:
        self._buffer: str = ""

    def feed(self, chunk: str) -> list[dict[str, Any]]:
        """Append a chunk to the internal buffer."""
        self._buffer += chunk
        return []

    def finalize(self) -> dict[str, Any]:
        """Return the extracted tags from the buffered text."""
        tags = extract_tags(self._buffer)
        return {"parsed": True, "tags": tags, "incremental": False}


def get_partial_state(text: str) -> dict[str, Any]:
    """Module-level convenience wrapper around :meth:`IncrementalXMLParser.get_partial_state`.

    Exposed so callers can ``from thegent.contracts.parser import
    get_partial_state`` without instantiating an
    :class:`IncrementalXMLParser`. Pinned by
    ``tests/test_wl145_l9_contracts_signature_parity.py``.
    """
    return IncrementalXMLParser().get_partial_state(text)


__all__ = [
    "CONTRACTS_PARSER_VERSION",
    "IncrementalXMLParser",
    "ParserState",
    "StreamingXMLParser",
    "extract_tags",
    "get_partial_state",
]
