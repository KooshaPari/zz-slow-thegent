# physical API Reference

> **Source**: `src/thegent/integration/physical.py`

WP-40001: IoT/Robotics Command Bridge.

Bridges agent logic with physical-world actuators and sensors.
Enables agents to interact with IoT devices or robotic swarms.

---

## physicalWorldBridge

Manages commands sent to physical IoT or robotic devices.

### Methods

#### physicalWorldBridge.**init**

```python
__init__(self: Any, bridge_id: str)
```

---

#### physicalWorldBridge.read_sensor

```python
read_sensor(self: Any, device_id: str, sensor_type: str)
```

Read telemetry from a physical sensor.

---

#### physicalWorldBridge.register_device

```python
register_device(self: Any, device_id: str, device_type: str)
```

Register a physical device.

---

#### physicalWorldBridge.send_command

```python
send_command(self: Any, device_id: str, command: str, params: dict[(str, Any)])
```

WP-40001: Send an actuation command to a physical device.

---

---

## read_sensor

```python
read_sensor(self: Any, device_id: str, sensor_type: str)
```

Read telemetry from a physical sensor.

---

## register_device

```python
register_device(self: Any, device_id: str, device_type: str)
```

Register a physical device.

---

## send_command

```python
send_command(self: Any, device_id: str, command: str, params: dict[(str, Any)])
```

WP-40001: Send an actuation command to a physical device.

---
