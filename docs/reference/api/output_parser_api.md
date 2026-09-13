# output_parser API Reference

> **Source**: `src/thegent/output_parser.py`

Condensed output extraction for agent streams.

Supports:

- JSONL / stream-json: Extract last assistant message (type=message, role=assistant).
- Plain text: Extract last meaningful block, stripping trailing noise.
- Structural validation: ParseResult with error_class for downstream routing/fallback.

BKM-02: When THGENT_USE_NATIVE_PARSER=1, uses thegent_parser Rust extension
for strip_think_blocks. Falls back to Python regex otherwise.

---

## ParseResult

Structured parse result with error classification for routing/fallback.

Use error_class to decide retry, fallback, or alert:

- parse_ok: extraction succeeded
- parse_truncated: output likely truncated (streaming)
- parse_malformed: JSON/XML parse failure
- parse_empty: no extractable content

---

## condense_stream_to_display

```python
condense_stream_to_display(stdout: str)
```

Produce Cursor-style condensed output from agent stream JSON.

Parses JSONL stream and formats:

- User answers: "User answered questions:" + bullets (Q → A)
- Agent turns: "agent(task)" + first tool + "+N more tool uses"

Returns empty string if input is not JSONL (caller should fall back to extract_condensed).
Supports Gemini/Codex stream-json; Copilot plain text returns empty.

---

## extract_condensed

```python
extract_condensed(stdout: str)
```

Extract condensed/final output from agent stdout.

Tries JSONL first (stream-json). Falls back to plain-text heuristics.
Prefers worker status report block (Summary, Items Done, Issues, Next Steps) when present.
Strips `think` blocks from final output.

---

## extract_condensed_structured

```python
extract_condensed_structured(stdout: str)
```

Extract condensed output with schema metadata for schema-aware consumers.

Returns {"text": str, "schema_version": str}. Use when downstream needs
versioned extraction contract for validation or replay.

---

## extract_condensed_validated

```python
extract_condensed_validated(stdout: str)
```

Extract condensed output with structural validation and error classification.

Returns ParseResult with success, text, error_class for downstream routing.
Detects truncation (unclosed XML tags), JSON malformation, and empty output.

---
