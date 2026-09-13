# fast_compression API Reference

> **Source**: `src/thegent/infra/fast_compression.py`

Fast compression/decompression with optimized backends.

This module provides optimized compression utilities:

- brotli for better compression ratios (if available)
- zstandard (zstd) for fast compression (if available)
- Standard gzip/zlib fallback

Performance improvements:

- brotli: Better compression ratios than gzip
- zstd: Faster compression/decompression
- Optimized for common use cases

---

## FastCompression

High-performance compression with automatic backend selection.

### Methods

#### FastCompression.compress

```python
compress(data: bytes, method: str, level: int)
```

Compress data using fastest available method.

**Parameters**:

- `data`: Data to compress
- `method`: Compression method ("auto", "gzip", "brotli", "zstd")
- `level`: Compression level (1-9, higher = better compression)

**Returns**: Tuple of (compressed_data, method_used)

---

#### FastCompression.decompress

```python
decompress(data: bytes, method: Any)
```

Decompress data, auto-detecting method if not specified.

**Parameters**:

- `data`: Compressed data
- `method`: Compression method (None = auto-detect)

**Returns**: Decompressed data

---

---

## compress

```python
compress(data: bytes, method: str, level: int)
```

Compress data using fastest available method.

**Parameters**:

- `data`: Data to compress
- `method`: Compression method ("auto", "gzip", "brotli", "zstd")
- `level`: Compression level (1-9, higher = better compression)

**Returns**: Tuple of (compressed_data, method_used)

---

## decompress

```python
decompress(data: bytes, method: Any)
```

Decompress data, auto-detecting method if not specified.

**Parameters**:

- `data`: Compressed data
- `method`: Compression method (None = auto-detect)

**Returns**: Decompressed data

---
