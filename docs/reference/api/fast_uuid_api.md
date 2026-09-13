# fast_uuid API Reference

> **Source**: `src/thegent/infra/fast_uuid.py`

Fast UUID generation with optimized backends.

This module provides optimized UUID generation:

- fastuuid for faster UUID generation (already installed!)
- Standard uuid module fallback

Performance improvements:

- fastuuid: Faster UUID generation (2-5x faster)
- Optimized for high-frequency UUID generation

---

## FastUUID

High-performance UUID generation with automatic backend selection.

### Methods

#### FastUUID.uuid1

Generate UUID1 (MAC address + timestamp).

**Returns**: UUID object

---

#### FastUUID.uuid1_str

Generate UUID1 as string.

**Returns**: UUID string

---

#### FastUUID.uuid4

Generate UUID4 (random UUID).

**Returns**: UUID object

---

#### FastUUID.uuid4_str

Generate UUID4 as string.

**Returns**: UUID string

---

---

## uuid1

Generate UUID1 (MAC address + timestamp).

**Returns**: UUID object

---

## uuid1_str

Generate UUID1 as string.

**Returns**: UUID string

---

## uuid4

Generate UUID4 (random UUID).

**Returns**: UUID object

---

## uuid4_str

Generate UUID4 as string.

**Returns**: UUID string

---
