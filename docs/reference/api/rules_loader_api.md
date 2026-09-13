# rules_loader API Reference

> **Source**: `src/thegent/control_plane/rules_loader.py`

WP-10003: Unified rules loader for heliosShield rules.conf.

---

## Rule

### Methods

#### Rule.key

```python
key(self: Any)
```

---

---

## RulesLoader

Parses and caches rules from heliosShield/rules.conf.

### Methods

#### RulesLoader.**init**

```python
__init__(self: Any, rules_path: Path)
```

---

#### RulesLoader.get_rule

```python
get_rule(self: Any, command: str, subcommand: Any)
```

Find the matching rule for a command/subcommand.

---

#### RulesLoader.load

```python
load(self: Any, force: bool)
```

Load rules from file if modified or forced.

---

---

## get_rule

```python
get_rule(self: Any, command: str, subcommand: Any)
```

Find the matching rule for a command/subcommand.

---

## key

```python
key(self: Any) -> str
```

---

## load

```python
load(self: Any, force: bool)
```

Load rules from file if modified or forced.

---
