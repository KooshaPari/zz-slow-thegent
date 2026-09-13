# playwright_recorder API Reference

> **Source**: `src/thegent/doc_tools/playwright_recorder.py`

Playwright-based browser automation and recording for VitePress documentation.

Provides high-level utilities for:

- Browser automation (launch, navigation, interactions)
- Video recording for feature demonstrations
- Screenshot capture with annotations
- Error recovery and timeout handling
- Multi-browser support (Chromium, Firefox, WebKit)

---

## PlaywrightRecorder

High-level wrapper for Playwright browser automation and recording.

Handles:

- Browser lifecycle (launch, close, context management)
- Navigation and page interactions
- Video recording with configurable quality
- Screenshot capture
- Error recovery and timeout handling
- Multi-browser support

### Methods

#### PlaywrightRecorder.**init**

```python
__init__(self: Any, config: Any)
```

Initialize recorder with configuration.

---

---

## RecordingConfig

Configuration for recording sessions.

**Inherits from**: `BaseModel`

### Methods

#### RecordingConfig.model_post_init

```python
model_post_init(self: Any, __context: Any)
```

Create output directory after model init.

---

#### RecordingConfig.validate_browser

```python
validate_browser(cls: Any, v: str)
```

Validate browser is one of the supported types.

---

---

## RecordingResult

Result of a recording session.

### Methods

#### RecordingResult.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---

#### RecordingResult.to_json

```python
to_json(self: Any, path: Any)
```

Convert to JSON string or save to file.

---

---

## ScreenshotOptions

Configuration for screenshot capture.

**Inherits from**: `BaseModel`

---

## VideoRecordingOptions

Configuration for video recording.

**Inherits from**: `BaseModel`

---

## model_post_init

```python
model_post_init(self: Any, __context: Any)
```

Create output directory after model init.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---

## to_json

```python
to_json(self: Any, path: Any)
```

Convert to JSON string or save to file.

---

## validate_browser

```python
validate_browser(cls: Any, v: str)
```

Validate browser is one of the supported types.

---
