# helios_bridge API Reference

> **Source**: `src/thegent/mesh/helios_bridge.py`

Fix heliosShield bridge and tests.

---

## HeliosShieldBridge

Fixed heliosShield bridge implementation.

### Methods

#### HeliosShieldBridge.**init**

```python
__init__(self: Any)
```

Initialize helios shield bridge.

---

#### HeliosShieldBridge.connect

```python
connect(self: Any)
```

Connect to helios shield.

**Returns**: True if connected

---

#### HeliosShieldBridge.send_command

```python
send_command(self: Any, command: str)
```

Send command through bridge.

**Parameters**:

- `command`: Command to send

**Returns**: Command result

---

#### HeliosShieldBridge.test_connection

```python
test_connection(self: Any)
```

Test bridge connection.

**Returns**: Test results

---

---

## connect

```python
connect(self: Any)
```

Connect to helios shield.

**Returns**: True if connected

---

## send_command

```python
send_command(self: Any, command: str)
```

Send command through bridge.

**Parameters**:

- `command`: Command to send

**Returns**: Command result

---

## test_connection

```python
test_connection(self: Any)
```

Test bridge connection.

**Returns**: Test results

---
