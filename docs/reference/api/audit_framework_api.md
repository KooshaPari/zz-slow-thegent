# audit_framework API Reference

> **Source**: `src/thegent/sync/audit_framework.py`

SY-002: System Audit Framework for thegent.

Audit configuration, dependencies, security, and performance.

---

## AuditIssue

A single issue found during an audit.

### Methods

#### AuditIssue.to_dict

```python
to_dict(self: Any)
```

---

---

## AuditRegistry

### Methods

#### AuditRegistry.**init**

```python
__init__(self: Any)
```

---

#### AuditRegistry.get_all_audits

```python
get_all_audits(self: Any)
```

---

#### AuditRegistry.register

```python
register(self: Any, audit: AuditType)
```

---

---

## AuditResult

Result of a full system audit.

### Methods

#### AuditResult.add_issue

```python
add_issue(self: Any, issue: AuditIssue)
```

---

#### AuditResult.complete

```python
complete(self: Any)
```

---

#### AuditResult.to_dict

```python
to_dict(self: Any)
```

---

---

## AuditSeverity

---

## AuditType

**Inherits from**: `ABC`

### Methods

#### AuditType.description

```python
description(self: Any)
```

---

#### AuditType.name

```python
name(self: Any)
```

---

---

## ConfigAuditType

**Inherits from**: `AuditType`

**Method Resolution Order**: `ConfigAuditType -> AuditType`

### Methods

#### ConfigAuditType.description

```python
description(self: Any)
```

---

#### ConfigAuditType.name

```python
name(self: Any)
```

---

---

## DagAuditType

**Inherits from**: `AuditType`

**Method Resolution Order**: `DagAuditType -> AuditType`

### Methods

#### DagAuditType.description

```python
description(self: Any)
```

---

#### DagAuditType.name

```python
name(self: Any)
```

---

---

## DoctorAuditType

**Inherits from**: `AuditType`

**Method Resolution Order**: `DoctorAuditType -> AuditType`

### Methods

#### DoctorAuditType.description

```python
description(self: Any)
```

---

#### DoctorAuditType.name

```python
name(self: Any)
```

---

---

## InitiativeAuditType

**Inherits from**: `AuditType`

**Method Resolution Order**: `InitiativeAuditType -> AuditType`

### Methods

#### InitiativeAuditType.description

```python
description(self: Any)
```

---

#### InitiativeAuditType.name

```python
name(self: Any)
```

---

---

## PlanAuditType

**Inherits from**: `AuditType`

**Method Resolution Order**: `PlanAuditType -> AuditType`

### Methods

#### PlanAuditType.description

```python
description(self: Any)
```

---

#### PlanAuditType.name

```python
name(self: Any)
```

---

---

## SystemAuditFramework

### Methods

#### SystemAuditFramework.**init**

```python
__init__(self: Any, registry: Any)
```

---

---

## add_issue

```python
add_issue(self: Any, issue: AuditIssue)
```

---

## complete

```python
complete(self: Any)
```

---

## description

```python
description(self: Any) -> str
```

---

## get_all_audits

```python
get_all_audits(self: Any) -> list[AuditType]
```

---

## name

```python
name(self: Any) -> str
```

---

## register

```python
register(self: Any, audit: AuditType)
```

---

## to_dict

```python
to_dict(self: Any) -> dict[(str, Any)]
```

---
