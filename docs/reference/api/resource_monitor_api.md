# resource_monitor API Reference

> **Source**: `src/thegent/infra/resource_monitor.py`

Resource monitoring and leak detection using psutil.

---

## ResourceMonitor

Monitor system resources using psutil and detect leaks.

### Methods

#### ResourceMonitor.**init**

```python
__init__(self: Any, check_interval: float)
```

Initialize resource monitor.

**Parameters**:

- `check_interval`: Interval in seconds between monitoring checks.

---

#### ResourceMonitor.detect_leak

```python
detect_leak(self: Any)
```

Detect potential resource leaks from history.

**Returns**: Description of detected leak, or None if no leak detected.

---

#### ResourceMonitor.get_history

```python
get_history(self: Any)
```

Get resource usage history.

---

#### ResourceMonitor.get_process_info

```python
get_process_info(self: Any, pid: int)
```

Get detailed process information using psutil.

**Parameters**:

- `pid`: Process ID.

**Returns**: Dictionary with process information, or None if process not found.

---

#### ResourceMonitor.get_stats

```python
get_stats(self: Any)
```

Get current resource statistics using psutil.

---

#### ResourceMonitor.start

```python
start(self: Any)
```

Start monitoring thread.

---

#### ResourceMonitor.stop

```python
stop(self: Any)
```

Stop monitoring thread.

---

---

## ResourceStats

Resource usage statistics.

### Methods

#### ResourceStats.get_suspicion_level

```python
get_suspicion_level(self: Any)
```

Get suspicion level and optimization suggestions.

Returns (level, suggestions) where level is one of:

- "low": Normal usage, no concerns
- "medium": Elevated usage, monitor
- "high": High usage, investigate
- "critical": Critical usage, immediate action needed

---

#### ResourceStats.is_critical

```python
is_critical(self: Any)
```

Check if resource usage is critical.

Critical thresholds:

- FD usage > 80% (file descriptor exhaustion risk)
- Process count > 500 (very high, may indicate leak)
- Memory > 2048MB (2GB) for this process

---

---

## detect_leak

```python
detect_leak(self: Any)
```

Detect potential resource leaks from history.

**Returns**: Description of detected leak, or None if no leak detected.

---

## get_history

```python
get_history(self: Any)
```

Get resource usage history.

---

## get_process_info

```python
get_process_info(self: Any, pid: int)
```

Get detailed process information using psutil.

**Parameters**:

- `pid`: Process ID.

**Returns**: Dictionary with process information, or None if process not found.

---

## get_resource_monitor

Get global resource monitor.

---

## get_stats

```python
get_stats(self: Any)
```

Get current resource statistics using psutil.

---

## get_suspicion_level

```python
get_suspicion_level(self: Any)
```

Get suspicion level and optimization suggestions.

Returns (level, suggestions) where level is one of:

- "low": Normal usage, no concerns
- "medium": Elevated usage, monitor
- "high": High usage, investigate
- "critical": Critical usage, immediate action needed

---

## is_critical

```python
is_critical(self: Any)
```

Check if resource usage is critical.

Critical thresholds:

- FD usage > 80% (file descriptor exhaustion risk)
- Process count > 500 (very high, may indicate leak)
- Memory > 2048MB (2GB) for this process

---

## start

```python
start(self: Any)
```

Start monitoring thread.

---

## stop

```python
stop(self: Any)
```

Stop monitoring thread.

---
