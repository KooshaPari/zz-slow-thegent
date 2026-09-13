# information_life API Reference

> **Source**: `src/thegent/agents/information_life.py`

WP-44001: Pure Information Persona Encoding.

Encodes an agent's 'soul' (weights, value vectors, and memory) into a substrate-independent
information format. Allows for migration between model architectures or digital-to-analog bridges.

---

## InformationPersona

Substrate-independent encoding of an agent identity.

### Methods

#### InformationPersona.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### InformationPersona.check_integrity

```python
check_integrity(self: Any)
```

Calculate the information entropy of the persona encoding.

---

#### InformationPersona.decode_persona

```python
decode_persona(self: Any, encoded_data: str)
```

Reconstruct persona from an information stream.

---

#### InformationPersona.encode_persona

```python
encode_persona(self: Any)
```

WP-44001: Serialize persona into a high-density, portable format.

---

---

## check_integrity

```python
check_integrity(self: Any)
```

Calculate the information entropy of the persona encoding.

---

## decode_persona

```python
decode_persona(self: Any, encoded_data: str)
```

Reconstruct persona from an information stream.

---

## encode_persona

```python
encode_persona(self: Any)
```

WP-44001: Serialize persona into a high-density, portable format.

---
