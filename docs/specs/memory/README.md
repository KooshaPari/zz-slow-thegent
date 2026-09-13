# Memory Domain Technical Specification

## Overview

Memory systems for caching, context management, and knowledge retrieval.

## Components

### Memory Types

| Type        | Backend     | Purpose         |
| ----------- | ----------- | --------------- |
| Cache       | Multi-level | Fast retrieval  |
| Supermemory | Vector DB   | Semantic search |
| Garden      | Long-term   | Knowledge graph |
| Seed        | Immutable   | Provenance      |

### Cache Hierarchy

```
L1: In-memory (hot)
L2: Disk (warm)
L3: Remote (cold)
```

### Key Classes

| Class             | Purpose       | Files                          |
| ----------------- | ------------- | ------------------------------ |
| MemoryManager     | Lifecycle     | `memory/manager.py`            |
| CacheProvider     | Caching       | `memory/cache_provider.py`     |
| SupermemoryClient | Vector search | `memory/supermemory_client.py` |
| Garden            | Knowledge     | `memory/garden.py`             |

## Performance

| Metric         | Target |
| -------------- | ------ |
| L1 lookup      | <1ms   |
| L2 lookup      | <10ms  |
| L3 lookup      | <100ms |
| Seed detection | <50ms  |

## Features

- Frecency-based eviction
- Seed preservation
- Cross-session persistence
