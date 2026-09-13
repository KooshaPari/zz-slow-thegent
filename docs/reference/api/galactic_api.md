# galactic API Reference

> **Source**: `src/thegent/discovery/galactic.py`

WP-34001: Delay-Tolerant Networking (DTN) Bridge.

Enables agent communication over high-latency, intermittently connected links (Inter-Galactic).
Inspired by NASA's DTN (BPv7) protocols.

---

## Bundle

A DTN Bundle (data packet) for long-delay transport.

---

## DTNBridge

Bridges standard thegent networking with Delay-Tolerant protocols.

### Methods

#### DTNBridge.**init**

```python
__init__(self: Any, node_id: str)
```

---

#### DTNBridge.add_contact

```python
add_contact(self: Any, node_id: str, contact_time: float)
```

Schedule a future contact opportunity.

---

#### DTNBridge.process_contacts

```python
process_contacts(self: Any)
```

WP-34002: Reconcile state when contact is established.

---

#### DTNBridge.send_bundle

```python
send_bundle(self: Any, dest_node: str, payload: bytes)
```

Queue a bundle for transmission.

---

---

## add_contact

```python
add_contact(self: Any, node_id: str, contact_time: float)
```

Schedule a future contact opportunity.

---

## process_contacts

```python
process_contacts(self: Any)
```

WP-34002: Reconcile state when contact is established.

---

## send_bundle

```python
send_bundle(self: Any, dest_node: str, payload: bytes)
```

Queue a bundle for transmission.

---
