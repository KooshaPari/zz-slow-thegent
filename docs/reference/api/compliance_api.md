# compliance API Reference

> **Source**: `src/thegent/governance/compliance.py`

WP-15004: Certification export profiles for SOC 2, ISO, and EU AI Act.

---

## ComplianceAuditTrail

Maintains audit trail for compliance verification.

### Methods

#### ComplianceAuditTrail.**init**

```python
__init__(self: Any, storage_path: Path)
```

---

#### ComplianceAuditTrail.record_action

```python
record_action(self: Any, action: str, context: dict[str, Any], profile: ComplianceProfile)
```

Record an action in the audit trail.

---

---

## ComplianceControl

Represents a compliance control requirement.

---

## ComplianceEnforcer

Enforces compliance controls based on active profile.

### Methods

#### ComplianceEnforcer.**init**

```python
__init__(self: Any, profile: ComplianceProfile)
```

---

#### ComplianceEnforcer.check_control

```python
check_control(self: Any, control_id: str, context: dict[str, Any])
```

Check if a control is satisfied.

---

#### ComplianceEnforcer.enforce_mandatory

```python
enforce_mandatory(self: Any, action: str, context: dict[str, Any])
```

Enforce all mandatory controls for an action.

---

---

## ComplianceExporter

Exports framework-specific evidence bundles for compliance audits (WP-15004).

### Methods

#### ComplianceExporter.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### ComplianceExporter.export_bundle

```python
export_bundle(self: Any, framework: str, target_path: Path)
```

Generate an evidence bundle for a specific compliance framework.

---

---

## ComplianceProfile

Represents a compliance profile with controls.

### Methods

#### ComplianceProfile.get_mandatory_controls

```python
get_mandatory_controls(self: Any)
```

Get all mandatory controls.

---

---

## ComplianceProfileType

**Inherits from**: `Enum`

---

## check_control

```python
check_control(self: Any, control_id: str, context: dict[str, Any])
```

Check if a control is satisfied.

---

## enforce_mandatory

```python
enforce_mandatory(self: Any, action: str, context: dict[str, Any])
```

Enforce all mandatory controls for an action.

---

## export_bundle

```python
export_bundle(self: Any, framework: str, target_path: Path)
```

Generate an evidence bundle for a specific compliance framework.

---

## get_mandatory_controls

```python
get_mandatory_controls(self: Any)
```

Get all mandatory controls.

---

## record_action

```python
record_action(self: Any, action: str, context: dict[str, Any], profile: ComplianceProfile)
```

Record an action in the audit trail.

---
