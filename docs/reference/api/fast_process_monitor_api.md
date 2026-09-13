# fast_process_monitor API Reference

> **Source**: `src/thegent/infra/fast_process_monitor.py`

Fast process and system monitoring with optimized backends.

This module provides a high-performance abstraction layer for process monitoring
that automatically selects the fastest available backend:

- Linux: Direct /proc filesystem access (10-100x faster than psutil.process_iter)
- Optional: procfs library (if installed) for structured /proc access
- macOS/Other: psutil (cross-platform, well-optimized)
- Fallback: Native system APIs where available

Performance improvements:

- Direct /proc access avoids subprocess overhead (10-100x faster)
- Batch directory scanning with os.scandir() (faster than Path.iterdir())
- Cached process enumeration for repeated queries (1s TTL)
- Lazy loading of process details (only fetch what's needed)
- Parallel processing for large process lists
- Memory-efficient iteration (generators, not lists)

Research-based optimizations:

- Using os.scandir() instead of Path.iterdir() for 2-3x speedup
- Reading /proc/PID/stat in one syscall (faster than multiple reads)
- Caching boot_time and clock_ticks (rarely change)
- Batch FD counting using /proc/PID/fd (faster than individual checks)

---

## FastProcessMonitor

High-performance process monitor with automatic backend selection.

Backend priority (fastest first):

1. procfs library (if installed) - structured /proc access
2. Direct /proc filesystem (Linux only) - raw file reads
3. psutil (cross-platform) - well-optimized fallback

### Methods

#### FastProcessMonitor.**init**

```python
__init__(self: Any)
```

---

#### FastProcessMonitor.find_by_command

```python
find_by_command(self: Any, patterns: list[str])
```

Find processes whose command line contains any of the patterns.

**Parameters**:

- `patterns`: List of strings to search for in command line

**Returns**: List of matching ProcessInfo objects

---

#### FastProcessMonitor.find_processes

```python
find_processes(self: Any, predicate: Callable[(Any, bool)])
```

Find processes matching a predicate function.

**Parameters**:

- `predicate`: Function that takes ProcessInfo and returns bool

**Returns**: List of matching ProcessInfo objects

---

#### FastProcessMonitor.get_process

```python
get_process(self: Any, pid: int)
```

Get process information by PID.

**Parameters**:

- `pid`: Process ID

**Returns**: ProcessInfo if found, None otherwise

---

#### FastProcessMonitor.get_process_count

```python
get_process_count(self: Any)
```

Get total number of processes (fast, optimized).

Uses os.scandir() for faster directory scanning (2-3x faster than Path.iterdir()).

---

#### FastProcessMonitor.get_process_info_detailed

```python
get_process_info_detailed(self: Any, pid: int)
```

Get detailed process information including memory and FD counts.

Slower than get_process() but provides more details.

---

#### FastProcessMonitor.iter_processes

```python
iter_processes(self: Any, attrs: Any, use_cache: bool)
```

Iterate through all processes using the fastest available backend.

Backend selection priority:

1. procfs library (if installed) - fastest, structured access
2. Direct /proc filesystem (Linux) - very fast, raw file reads
3. psutil (cross-platform) - slower but reliable fallback

**Parameters**:

- `attrs`: Optional list of attributes to fetch (for psutil backend)
- `use_cache`: Whether to use cached results (1 second TTL)

**Returns**: ProcessInfo objects for each process

---

---

## ProcessInfo

Lightweight process information.

---

## find_by_command

```python
find_by_command(self: Any, patterns: list[str])
```

Find processes whose command line contains any of the patterns.

**Parameters**:

- `patterns`: List of strings to search for in command line

**Returns**: List of matching ProcessInfo objects

---

## find_processes

```python
find_processes(self: Any, predicate: Callable[(Any, bool)])
```

Find processes matching a predicate function.

**Parameters**:

- `predicate`: Function that takes ProcessInfo and returns bool

**Returns**: List of matching ProcessInfo objects

---

## get_fast_monitor

Get global fast process monitor instance.

---

## get_process

```python
get_process(self: Any, pid: int)
```

Get process information by PID.

**Parameters**:

- `pid`: Process ID

**Returns**: ProcessInfo if found, None otherwise

---

## get_process_count

```python
get_process_count(self: Any)
```

Get total number of processes (fast, optimized).

Uses os.scandir() for faster directory scanning (2-3x faster than Path.iterdir()).

---

## get_process_info_detailed

```python
get_process_info_detailed(self: Any, pid: int)
```

Get detailed process information including memory and FD counts.

Slower than get_process() but provides more details.

---

## iter_processes

```python
iter_processes(self: Any, attrs: Any, use_cache: bool)
```

Iterate through all processes using the fastest available backend.

Backend selection priority:

1. procfs library (if installed) - fastest, structured access
2. Direct /proc filesystem (Linux) - very fast, raw file reads
3. psutil (cross-platform) - slower but reliable fallback

**Parameters**:

- `attrs`: Optional list of attributes to fetch (for psutil backend)
- `use_cache`: Whether to use cached results (1 second TTL)

**Returns**: ProcessInfo objects for each process

---

## matches

```python
matches(info: ProcessInfo) -> bool
```

---
