# subprocess_manager API Reference

> **Source**: `src/thegent/infra/subprocess_manager.py`

Resource-aware subprocess management with automatic cleanup.

---

## SubprocessManager

Manager for subprocess lifecycle with resource tracking.

### Methods

#### SubprocessManager.**init**

```python
__init__(self: Any)
```

---

#### SubprocessManager.popen

```python
popen(self: Any, args: list[str], name: str)
```

Context manager for subprocess.Popen with automatic cleanup.

---

#### SubprocessManager.run

```python
run(self: Any, args: list[str], name: str, timeout: Any)
```

Run subprocess with resource tracking.

---

---

## get_subprocess_manager

Get global subprocess manager.

---

## popen

```python
popen(self: Any, args: list[str], name: str)
```

Context manager for subprocess.Popen with automatic cleanup.

---

## run

```python
run(self: Any, args: list[str], name: str, timeout: Any)
```

Run subprocess with resource tracking.

---
