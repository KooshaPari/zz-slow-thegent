# provisioner API Reference

> **Source**: `src/thegent/infra/provisioner.py`

WP-31001: Self-Provisioning Infra Bridge.

Enables agents to provision their own compute, storage, and networking resources.
Provides a high-level API over Terraform/Cloud-init/Docker.

---

## InfraProvisioner

Orchestrates self-provisioning of agent infrastructure.

### Methods

#### InfraProvisioner.**init**

```python
__init__(self: Any, provider: str)
```

---

#### InfraProvisioner.decommission

```python
decommission(self: Any, resource_id: str)
```

Release a previously provisioned resource.

---

#### InfraProvisioner.provision

```python
provision(self: Any, resource_id: str, spec: ResourceSpec)
```

Provision a resource based on the spec.

---

---

## ResourceSpec

Specification for an infra resource.

**Inherits from**: `BaseModel`

---

## decommission

```python
decommission(self: Any, resource_id: str)
```

Release a previously provisioned resource.

---

## provision

```python
provision(self: Any, resource_id: str, spec: ResourceSpec)
```

Provision a resource based on the spec.

---
