# Discovery Domain Technical Specification

## Overview

Project discovery, federation, and edge synchronization.

## Components

### Discovery Types

| Type       | Purpose   | Files                     |
| ---------- | --------- | ------------------------- |
| Projects   | Workspace | `discovery/projects.py`   |
| Federation | Cross-org | `discovery/federation.py` |
| Edge sync  | Offline   | `discovery/edge_sync.py`  |
| Mesh       | P2P       | `discovery/mesh.py`       |
| Galactic   | Global    | `discovery/galactic.py`   |

### Sync

| Component    | Purpose   | Files                       |
| ------------ | --------- | --------------------------- |
| Relativistic | Time sync | `discovery/relativistic.py` |
| Market       | Discovery | `discovery/market.py`       |

## Features

- Automatic project detection
- Cross-project references
- Offline capability
- Federation protocols
