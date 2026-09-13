# triggers API Reference

> **Source**: `src/thegent/governance/triggers.py`

AgilePlus trigger modes: watchdog, timer, and manual.

Provides three ways to trigger governance cycles:

- Watchdog: File system watcher with debounce (uses watchfiles for 5-10x performance)
- Timer: Periodic interval-based triggering
- Manual: One-shot CLI invocation

---

## HealthThresholdTrigger

Trigger governance cycle when health drops below threshold.

### Methods

#### HealthThresholdTrigger.**init**

```python
__init__(self: Any, loop: Any, threshold: float, check_interval: int)
```

---

#### HealthThresholdTrigger.start

```python
start(self: Any)
```

Start health monitoring in background.

---

#### HealthThresholdTrigger.stop

```python
stop(self: Any)
```

Stop health monitoring.

---

---

## ManualTrigger

One-shot manual trigger.

Runs a single governance cycle and exits.

### Methods

#### ManualTrigger.**init**

```python
__init__(self: Any, loop: Any)
```

---

#### ManualTrigger.run

```python
run(self: Any, force: bool)
```

Run a single governance cycle.

---

---

## TimerTrigger

Periodic timer-based trigger.

Triggers governance cycles at fixed intervals.

### Methods

#### TimerTrigger.**init**

```python
__init__(self: Any, loop: Any, config: TriggerConfig)
```

---

#### TimerTrigger.start

```python
start(self: Any)
```

Start the timer trigger.

---

#### TimerTrigger.stop

```python
stop(self: Any)
```

Stop the timer trigger.

---

---

## TriggerConfig

Configuration for trigger modes.

**Inherits from**: `BaseModel`

---

## TriggerProtocol

Protocol for trigger implementations.

**Inherits from**: `Protocol`

### Methods

#### TriggerProtocol.start

```python
start(self: Any)
```

---

#### TriggerProtocol.stop

```python
stop(self: Any)
```

---

---

## WatchdogTrigger

File system watcher trigger with debounce.

Uses watchfiles (5-10x faster) or watchdog fallback to watch specified paths
for changes and triggers cycles after a debounce period without new changes.

### Methods

#### WatchdogTrigger.**init**

```python
__init__(self: Any, loop: Any, config: TriggerConfig)
```

---

#### WatchdogTrigger.start

```python
start(self: Any)
```

Start the watchdog trigger.

---

#### WatchdogTrigger.stop

```python
stop(self: Any)
```

Stop the watchdog trigger.

---

---

## \_WatchdogEventHandler

Event handler for watchdog file system events (fallback).

Filters events to only process relevant file changes.
Only used when watchfiles is not available.

**Inherits from**: `FileSystemEventHandler`

### Methods

#### \_WatchdogEventHandler.**init**

```python
__init__(self: Any, on_change: Any, exclude_dirs: frozenset[str], watch_extensions: frozenset[str])
```

---

#### \_WatchdogEventHandler.on_created

```python
on_created(self: Any, event: Any)
```

Called when a file is created.

---

#### \_WatchdogEventHandler.on_deleted

```python
on_deleted(self: Any, event: Any)
```

Called when a file is deleted.

---

#### \_WatchdogEventHandler.on_modified

```python
on_modified(self: Any, event: Any)
```

Called when a file is modified.

---

---

## create_trigger

```python
create_trigger(mode: str, loop: Any, config: TriggerConfig)
```

Factory function to create the appropriate trigger.

---

## main

CLI entry point for triggers.

---

## monitor

---

## on_created

```python
on_created(self: Any, event: Any)
```

Called when a file is created.

---

## on_deleted

```python
on_deleted(self: Any, event: Any)
```

Called when a file is deleted.

---

## on_modified

```python
on_modified(self: Any, event: Any)
```

Called when a file is modified.

---

## run

```python
run(self: Any, force: bool)
```

Run a single governance cycle.

---

## shutdown

```python
shutdown(signum: int, frame: Any) -> None
```

---

## start

```python
start(self: Any)
```

Start health monitoring in background.

---

## stop

```python
stop(self: Any)
```

Stop health monitoring.

---

## watch_filter

```python
watch_filter(change: Change, path_str: str)
```

Filter changes to only process relevant files.

---
