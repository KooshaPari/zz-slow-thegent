# sensory_context API Reference

> **Source**: `src/thegent/work_packages/sensory_context.py`

WP-32001: Sensory Context Bridge (Audio/Video).

Provides audio and video processing capabilities for agent context awareness.
Supports transcription, feature extraction, and frame analysis.

---

## AudioFeatures

Extracted audio features.

---

## SensoryContextBridge

Bridge for audio/video sensory context processing.

Provides unified interface for processing audio and video data
to extract contextual information for agent decision-making.

### Methods

#### SensoryContextBridge.**init**

```python
__init__(self: Any)
```

Initialize sensory context bridge.

---

#### SensoryContextBridge.process_audio

```python
process_audio(self: Any, audio_data: bytes, format: str, language: Any)
```

Process audio data and extract features.

**Parameters**:

- `audio_data`: Raw audio bytes
- `format`: Audio format (wav, mp3, flac, etc.)
- `language`: Expected language code (e.g., 'en', 'es') for transcription

**Returns**: Dictionary containing transcript, features, and metadata

---

#### SensoryContextBridge.process_video

```python
process_video(self: Any, video_data: bytes, format: str, extract_frames: bool, frame_interval: float)
```

Process video data and extract features.

**Parameters**:

- `video_data`: Raw video bytes
- `format`: Video format (mp4, avi, mov, etc.)
- `extract_frames`: Whether to extract individual frames
- `frame_interval`: Interval between frames in seconds

**Returns**: Dictionary containing frames, features, and metadata

---

#### SensoryContextBridge.register_audio_processor

```python
register_audio_processor(self: Any, name: str, processor: Any)
```

Register a custom audio processor.

**Parameters**:

- `name`: Processor identifier
- `processor`: Processor instance with process() method

---

#### SensoryContextBridge.register_video_processor

```python
register_video_processor(self: Any, name: str, processor: Any)
```

Register a custom video processor.

**Parameters**:

- `name`: Processor identifier
- `processor`: Processor instance with process() method

---

---

## VideoFeatures

Extracted video features.

---

## process_audio

```python
process_audio(self: Any, audio_data: bytes, format: str, language: Any)
```

Process audio data and extract features.

**Parameters**:

- `audio_data`: Raw audio bytes
- `format`: Audio format (wav, mp3, flac, etc.)
- `language`: Expected language code (e.g., 'en', 'es') for transcription

**Returns**: Dictionary containing transcript, features, and metadata

---

## process_video

```python
process_video(self: Any, video_data: bytes, format: str, extract_frames: bool, frame_interval: float)
```

Process video data and extract features.

**Parameters**:

- `video_data`: Raw video bytes
- `format`: Video format (mp4, avi, mov, etc.)
- `extract_frames`: Whether to extract individual frames
- `frame_interval`: Interval between frames in seconds

**Returns**: Dictionary containing frames, features, and metadata

---

## register_audio_processor

```python
register_audio_processor(self: Any, name: str, processor: Any)
```

Register a custom audio processor.

**Parameters**:

- `name`: Processor identifier
- `processor`: Processor instance with process() method

---

## register_video_processor

```python
register_video_processor(self: Any, name: str, processor: Any)
```

Register a custom video processor.

**Parameters**:

- `name`: Processor identifier
- `processor`: Processor instance with process() method

---
