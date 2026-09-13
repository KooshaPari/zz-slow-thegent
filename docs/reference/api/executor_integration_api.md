# executor_integration API Reference

> **Source**: `src/thegent/isolation/executor_integration.py`

Example: Integrating isolation provider into executor.

This module demonstrates how to integrate SubUserIsolationProvider
into the main agent executor for Phase 1.

---

## IsolatedExecutor

Example executor with isolation support.

### Methods

#### IsolatedExecutor.**init**

```python
__init__(self: Any, isolation_provider: Any, enable_isolation: bool)
```

Initialize executor with optional isolation.

**Parameters**:

- `isolation_provider`: Provider for tenant isolation
- `enable_isolation`: Whether to use isolation

---

#### IsolatedExecutor.execute_for_tenant

```python
execute_for_tenant(self: Any, tenant_id: str, agent_id: str, command: list, timeout_sec: int)
```

Execute a command for a tenant with optional isolation.

Integration point: This is where the executor would use
the isolation provider to ensure commands run in isolated
tenant contexts.

**Parameters**:

- `tenant_id`: Tenant identifier
- `agent_id`: Agent identifier
- `command`: Command to execute
- `timeout_sec`: Execution timeout

**Returns**: Execution result dict with returncode, stdout, stderr

---

---

## example_usage

Example: How to use IsolatedExecutor.

> > > import tempfile
> > > with tempfile.TemporaryDirectory() as tmpdir:
> > > ... provider = SubUserIsolationProvider(base_home_dir=tmpdir)
> > > ... executor = IsolatedExecutor(
> > > ... isolation_provider=provider,
> > > ... enable_isolation=True,
> > > ... )
> > > ... result = executor.execute_for_tenant(
> > > ... tenant_id='tenant-1',
> > > ... agent_id='agent-1',
> > > ... command=['echo', 'hello'],
> > > ... )
> > > ... print(f"Exit code: {result['returncode']}")
> > > ... print(f"Output: {result['stdout'].strip()}")
> > > Exit code: 0
> > > Output: hello

---

## execute_for_tenant

```python
execute_for_tenant(self: Any, tenant_id: str, agent_id: str, command: list, timeout_sec: int)
```

Execute a command for a tenant with optional isolation.

Integration point: This is where the executor would use
the isolation provider to ensure commands run in isolated
tenant contexts.

**Parameters**:

- `tenant_id`: Tenant identifier
- `agent_id`: Agent identifier
- `command`: Command to execute
- `timeout_sec`: Execution timeout

**Returns**: Execution result dict with returncode, stdout, stderr

---
