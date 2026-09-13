# seed_detector API Reference

> **Source**: `src/thegent/memory/seed_detector.py`

Detect and classify idea seeds from user prompts and agent outputs.

Seed ideas are nascent concepts, half-formed requirements, design sketches,
problem statements that could grow into full features.

Provides:

- Pattern matching for explicit seed signals
- Optional LLM-based classification for non-obvious seeds
- Metadata extraction (source, timestamp, confidence)

---

## Seed

Represents a detected idea seed.

### Methods

#### Seed.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---

---

## SeedConfidence

Confidence level of seed detection.

**Inherits from**: `Enum`

---

## SeedDetector

Detects idea seeds using pattern matching and optional LLM classification.

### Methods

#### SeedDetector.**init**

```python
__init__(self: Any, use_llm: bool)
```

Initialize detector.

**Parameters**:

- `use_llm`: Whether to use LLM for classification (requires API key)

---

#### SeedDetector.detect_seeds

```python
detect_seeds(self: Any, text: str, source: SeedSource)
```

Detect seeds in text using pattern matching.

**Parameters**:

- `text`: Input text to analyze
- `source`: Source of the text

**Returns**: List of detected Seed objects

---

#### SeedDetector.extract_flags

```python
extract_flags(text: str)
```

Extract special flags from text (e.g., $idea, $defer, $pending).

**Parameters**:

- `text`: Input text

**Returns**: Dict with flag presence: {"idea": True, "defer": False, ...}

---

---

## SeedSource

Source of the seed idea.

**Inherits from**: `Enum`

---

## detect_seeds

```python
detect_seeds(self: Any, text: str, source: SeedSource)
```

Detect seeds in text using pattern matching.

**Parameters**:

- `text`: Input text to analyze
- `source`: Source of the text

**Returns**: List of detected Seed objects

---

## extract_flags

```python
extract_flags(text: str)
```

Extract special flags from text (e.g., $idea, $defer, $pending).

**Parameters**:

- `text`: Input text

**Returns**: Dict with flag presence: {"idea": True, "defer": False, ...}

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---
