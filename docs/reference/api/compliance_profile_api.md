# compliance_profile API Reference

> **Source**: `src/thegent/phases/compliance_profile.py`

Compliance profile mapping (EU-AI-ACT, US-SEC, SOX, GDPR).

---

## ComplianceProfile

Compliance profile mapping.

### Methods

#### ComplianceProfile.**init**

```python
__init__(self: Any, profile_name: str)
```

Initialize compliance profile.

**Parameters**:

- `profile_name`: Name of compliance profile

---

#### ComplianceProfile.check_compliance

```python
check_compliance(self: Any, feature: str)
```

Check if a feature is compliant.

**Parameters**:

- `feature`: Feature name

**Returns**: True if compliant

---

#### ComplianceProfile.get_requirements

```python
get_requirements(self: Any)
```

Get requirements for this profile.

**Returns**: List of requirement names

---

---

## check_compliance

```python
check_compliance(self: Any, feature: str)
```

Check if a feature is compliant.

**Parameters**:

- `feature`: Feature name

**Returns**: True if compliant

---

## get_requirements

```python
get_requirements(self: Any)
```

Get requirements for this profile.

**Returns**: List of requirement names

---
