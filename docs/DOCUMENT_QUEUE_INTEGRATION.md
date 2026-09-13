# Document Queue Integration Guide

## Overview

The document queue system has been integrated into `thegent` as part of the document agent-facing suite of features. This provides comprehensive markdown file scanning, queue management, processing, and analysis capabilities.

## Architecture

```
thegent/
├── agents/
│   └── document/
│       ├── __init__.py          # Module exports
│       ├── scanner.py           # Markdown file scanner
│       ├── queue_manager.py     # Queue state management
│       ├── processor.py         # Document processing pipeline
│       └── analyzer.py          # Document analysis and categorization
├── mcp/
│   └── document_queue.py        # MCP server for queue operations
├── cli/
│   ├── main.py                  # Main CLI entry point
│   └── commands/
│       └── queue.py             # Queue management commands
└── config/
    └── document_queue.yaml      # Default configuration
```

## Features

### 1. Markdown File Scanner

Scans directories for markdown files, organizing by modification date and location.

**Key Features:**
- Configurable scan locations with recursive/depth options
- Exclusion patterns (node_modules, .venv, etc.)
- Date filtering (minimum modification date)
- JSON queue output

**Usage:**
```python
from thegent.agents.document import MarkdownScanner, ScanConfig

config = ScanConfig(
    locations={
        "kush": {"path": "~/kush", "recursive": True},
        "temp-PRODVERCEL": {"path": "~/temp-PRODVERCEL", "recursive": True},
    },
    min_date="2025-04",
)
scanner = MarkdownScanner(config)
scanner.scan()
queue_file = scanner.save_results()
```

### 2. Queue Manager

Manages processing state, tracks progress, and provides queue operations.

**Key Features:**
- State persistence (processed/skipped/failed files)
- Month-by-month iteration
- Location filtering
- Progress tracking

**Usage:**
```python
from thegent.agents.document import QueueManager

queue_manager = QueueManager(Path("queue.json"))
next_month = queue_manager.get_next_month()
files = queue_manager.get_month_files("2026-02", location="kush")
queue_manager.mark_file_processed("path/to/file.md")
```

### 3. Document Processor

Processes documents through configurable pipelines.

**Key Features:**
- Pluggable processing stages
- Batch processing
- Metadata extraction
- File hashing
- Statistics tracking

**Usage:**
```python
from thegent.agents.document import DocumentProcessor, ProcessingPipeline
from thegent.agents.document.processor import extract_metadata, compute_file_hash

pipeline = ProcessingPipeline()
pipeline.add_stage(extract_metadata)
pipeline.add_stage(compute_file_hash)

processor = DocumentProcessor(pipeline)
result = processor.process_file("path/to/file.md")
```

### 4. Document Analyzer

Analyzes markdown files for categorization and metadata extraction.

**Key Features:**
- Automatic categorization (research, plan, report, guide, etc.)
- Keyword extraction
- Reading time estimation
- Content analysis (code blocks, images, links, sections)

**Usage:**
```python
from thegent.agents.document import DocumentAnalyzer

analyzer = DocumentAnalyzer()
analysis = analyzer.analyze(Path("file.md"))
print(f"Category: {analysis.category.value}")
print(f"Reading time: {analysis.estimated_reading_time} minutes")
```

### 5. MCP Server

Provides Model Context Protocol tools for AI agents to interact with the queue.

**Available Tools:**
- `document_queue_list_months` - List all months in queue
- `document_queue_get_next` - Get next month to process
- `document_queue_get_files` - Get files for a month/location
- `document_queue_get_summary` - Get queue statistics
- `document_queue_mark_processed` - Mark file as processed
- `document_queue_scan` - Perform new scan
- `document_queue_analyze` - Analyze a document

**Usage:**
```python
from thegent.mcp.document_queue import create_document_queue_server

server = create_document_queue_server()
# Use with MCP client
```

### 6. CLI Commands

Command-line interface for queue management.

**Commands:**
- `thegent queue scan` - Scan for markdown files
- `thegent queue list` - List all months
- `thegent queue next` - Get next month to process
- `thegent queue files` - Get files for a month
- `thegent queue summary` - Get queue statistics
- `thegent queue process` - Process a file
- `thegent queue analyze` - Analyze a document

**Usage:**
```bash
# Scan for files
thegent queue scan --config config.yaml

# List months
thegent queue list

# Get next month
thegent queue next --files

# Process a file
thegent queue process path/to/file.md --analyze
```

## Configuration

Default configuration is in `thegent/config/document_queue.yaml`:

```yaml
locations:
  kush:
    path: "~/kush"
    recursive: true
    max_depth: null

  temp-PRODVERCEL:
    path: "~/temp-PRODVERCEL"
    recursive: true

exclude_patterns:
  - "node_modules"
  - ".venv"
  - ".git"

min_date: "2025-04"
output_dir: "~/.thegent/scans"
```

## Integration Points

### 1. Agent Integration

Agents can use the queue system to:
- Discover documents to process
- Track processing state
- Analyze documents before processing
- Batch process documents

### 2. MCP Integration

MCP servers can expose queue operations to AI agents, enabling:
- Queue inspection
- Document retrieval
- Processing coordination
- Progress tracking

### 3. CLI Integration

CLI provides human-friendly interface for:
- Manual scanning
- Queue inspection
- File processing
- Analysis

## Example Workflow

```python
# 1. Scan for files
from thegent.agents.document import MarkdownScanner, ScanConfig

config = ScanConfig(
    locations={"kush": {"path": "~/kush", "recursive": True}},
    min_date="2025-04",
)
scanner = MarkdownScanner(config)
scanner.scan()
queue_file = scanner.save_results()

# 2. Process queue
from thegent.agents.document import QueueManager, DocumentProcessor, ProcessingPipeline
from thegent.agents.document.processor import extract_metadata, compute_file_hash

queue_manager = QueueManager(queue_file)
processor = DocumentProcessor(ProcessingPipeline().add_stage(extract_metadata).add_stage(compute_file_hash))

# Process next month
next_month = queue_manager.get_next_month()
if next_month:
    files = queue_manager.get_month_files(next_month["month"])
    for filepath in files[:10]:  # Process first 10
        result = processor.process_file(filepath)
        if result.status.value == "completed":
            queue_manager.mark_file_processed(filepath)

    queue_manager.mark_month_complete(next_month["month"])
```

## Next Steps

1. **Enhanced Analysis**: Add NLP-based analysis, topic modeling, sentiment analysis
2. **Processing Plugins**: Plugin system for custom processing stages
3. **Distributed Processing**: Support for distributed/parallel processing
4. **Web UI**: Web interface for queue visualization and management
5. **Integration Tests**: Comprehensive test suite
6. **Documentation**: API documentation and examples

## Related Documentation

- Queue System: `/docs/research/QUEUE_README.md`
- Scan Summary: `/docs/research/MARKDOWN_SCAN_SUMMARY.md`
- Queue Processor: `/docs/research/process_queue.py`
