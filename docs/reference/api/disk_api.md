# disk API Reference

> **Source**: `src/thegent/resources/disk.py`

Disk I/O queue depth monitoring for thegent resource management.

@trace FR-RESOURCE-001

---

## DiskIoStats

Per-device disk I/O counters from the OS.

All `*_count` and `*_bytes` fields reflect cumulative totals
since boot (monotonically increasing), matching the semantics of
`psutil.disk_io_counters()`.

---

## DiskMonitor

Monitors disk I/O statistics and estimates queue depth.

Uses `psutil.disk_io_counters(perdisk=True)` as the data source.
If psutil is not installed, all methods return empty results rather
than raising, keeping callers resilient to missing dependencies.

Usage::

    monitor = DiskMonitor()
    stats = monitor.get_io_stats()           # snapshot I/O counters
    samples = monitor.sample_queue_depth()   # estimate queue depth
    devices = monitor.list_devices()         # enumerate block devices
    usage = monitor.get_disk_usage("/")      # wrapper for disk_usage

### Methods

#### DiskMonitor.get_disk_usage

```python
get_disk_usage(self: Any, path: str)
```

Return disk usage statistics for the filesystem at _path_.

Wraps `psutil.disk_usage(path)` and converts the named-tuple to a
plain dictionary with keys `total`, `used`, `free`, and
`percent`.

**Parameters**:

- `path`: Mount point or any path on the target filesystem.

**Returns**: Dict with keys `total`, `used`, `free`, `percent`.
Returns `{}` when psutil is unavailable or the path is invalid.

---

#### DiskMonitor.get_io_stats

```python
get_io_stats(self: Any, device: Any)
```

Return per-device I/O counters.

**Parameters**:

- `device`: If given, return only stats for that device name.
  `None` returns all devices.

**Returns**: List of :class:`DiskIoStats`, one per block device.
Returns `[]` when psutil is unavailable.

---

#### DiskMonitor.list_devices

```python
list_devices(self: Any)
```

Return names of all block devices reported by the OS.

**Returns**: Sorted list of device name strings (e.g. `["disk0", "disk1"]`
on macOS or `["sda", "sdb"]` on Linux).
Returns `[]` when psutil is unavailable.

---

#### DiskMonitor.sample_queue_depth

```python
sample_queue_depth(self: Any, interval_s: float)
```

Estimate I/O queue depth by comparing two snapshots.

Takes two `get_io_stats()` snapshots separated by `interval_s`
seconds and derives:

- `utilization_pct`: fraction of the interval the device was busy
  (using `busy_time_ms` when available, otherwise `read_time_ms +
write_time_ms` saturated at `interval_s * 1000` ms).
- `queue_depth`: average number of pending I/O requests during the
  interval, estimated as `utilization_fraction * io_rate`.

**Parameters**:

- `interval_s`: Sampling window in seconds (must be &gt; 0).

**Returns**: List of :class:`DiskQueueSample`, one per device seen in both
snapshots. Returns `[]` when psutil is unavailable.

---

---

## DiskQueueSample

Estimated queue depth and utilization for one block device.

`queue_depth` is derived from Little's Law applied to the busy-time
delta between two `DiskIoStats` samples:

    queue_depth = (busy_time_delta_ms / elapsed_ms)
                  * (io_count_delta / max(io_count_delta, 1))

When `busy_time_ms` is unavailable (e.g. macOS), `utilization_pct`
is still computed from the combined read/write time delta.

---

## get_disk_usage

```python
get_disk_usage(self: Any, path: str)
```

Return disk usage statistics for the filesystem at _path_.

Wraps `psutil.disk_usage(path)` and converts the named-tuple to a
plain dictionary with keys `total`, `used`, `free`, and
`percent`.

**Parameters**:

- `path`: Mount point or any path on the target filesystem.

**Returns**: Dict with keys `total`, `used`, `free`, `percent`.
Returns `{}` when psutil is unavailable or the path is invalid.

---

## get_io_stats

```python
get_io_stats(self: Any, device: Any)
```

Return per-device I/O counters.

**Parameters**:

- `device`: If given, return only stats for that device name.
  `None` returns all devices.

**Returns**: List of :class:`DiskIoStats`, one per block device.
Returns `[]` when psutil is unavailable.

---

## list_devices

```python
list_devices(self: Any)
```

Return names of all block devices reported by the OS.

**Returns**: Sorted list of device name strings (e.g. `["disk0", "disk1"]`
on macOS or `["sda", "sdb"]` on Linux).
Returns `[]` when psutil is unavailable.

---

## sample_queue_depth

```python
sample_queue_depth(self: Any, interval_s: float)
```

Estimate I/O queue depth by comparing two snapshots.

Takes two `get_io_stats()` snapshots separated by `interval_s`
seconds and derives:

- `utilization_pct`: fraction of the interval the device was busy
  (using `busy_time_ms` when available, otherwise `read_time_ms +
write_time_ms` saturated at `interval_s * 1000` ms).
- `queue_depth`: average number of pending I/O requests during the
  interval, estimated as `utilization_fraction * io_rate`.

**Parameters**:

- `interval_s`: Sampling window in seconds (must be &gt; 0).

**Returns**: List of :class:`DiskQueueSample`, one per device seen in both
snapshots. Returns `[]` when psutil is unavailable.

---
