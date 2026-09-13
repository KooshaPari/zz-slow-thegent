# payments API Reference

> **Source**: `src/thegent/security/payments.py`

WP-30003: Micro-payment Settlement Bridge.

Interfaces with external payment gateways or blockchains to settle agent-to-agent debts.
Ensures that the virtual agent treasury can be backed by real-world liquidity.

---

## PaymentBridge

Bridges internal agent payments to external settlement providers.

### Methods

#### PaymentBridge.**init**

```python
__init__(self: Any, provider: str)
```

---

#### PaymentBridge.initiate_settlement

```python
initiate_settlement(self: Any, agent_id: str, amount: float)
```

Settle an agent's accumulated micro-debts with an external provider.

---

#### PaymentBridge.verify_liquidity

```python
verify_liquidity(self: Any, agent_id: str)
```

Check if an agent has enough real-world backing for its virtual treasury.

---

---

## Settlement

Metadata for a settlement operation.

**Inherits from**: `BaseModel`

---

## initiate_settlement

```python
initiate_settlement(self: Any, agent_id: str, amount: float)
```

Settle an agent's accumulated micro-debts with an external provider.

---

## verify_liquidity

```python
verify_liquidity(self: Any, agent_id: str)
```

Check if an agent has enough real-world backing for its virtual treasury.

---
