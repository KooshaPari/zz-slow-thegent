# egress API Reference

> **Source**: `src/thegent/observability/egress.py`

WP-15001: External SOC/SIEM event egress for enterprise observability.

---

## EgressEvent

---

## SIEMEgress

Pushes normalized events to external enterprise security systems (WP-15001).

### Methods

#### SIEMEgress.**init**

```python
__init__(self: Any, endpoint_url: Any)
```

---

#### SIEMEgress.format_for_syslog

```python
format_for_syslog(self: Any, event: EgressEvent)
```

Format the event for traditional RFC 5424 syslog.

---

#### SIEMEgress.push_event

```python
push_event(self: Any, event: EgressEvent)
```

Push an event to the external SIEM endpoint via HTTP POST.

---

---

## format_for_syslog

```python
format_for_syslog(self: Any, event: EgressEvent)
```

Format the event for traditional RFC 5424 syslog.

---

## push_event

```python
push_event(self: Any, event: EgressEvent)
```

Push an event to the external SIEM endpoint via HTTP POST.

---
