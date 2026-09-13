# Document Queue System - Quick Start

## Installation

The document queue system is integrated into `thegent`. Ensure you're in the project root:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
```

## Quick Usage

### 1. Scan for Markdown Files

```python
from thegent.agents.document import MarkdownScanner, ScanConfig

config = ScanConfig(
    locations={
        "kush": {"path": "/Users/kooshapari/kush", "recursive": True},
        "temp-PRODVERCEL": {"path": "/Users/kooshapari/temp-PRODVERCEL", "recursive": True},
    },
    min_date="2025-04",
)
scanner = MarkdownScanner(config)
scanner.scan()
queue_file = scanner.save_results()
print(f"Queue saved to: {queue_file}")
```

### 2. Process Queue

```python
from thegent.agents.document import QueueManager

queue_manager = QueueManager(queue_file)

# Get next month
next_month = queue_manager.get_next_month()
if next_month:
    print(f"Processing: {next_month['month']}")
    files = queue_manager.get_month_files(next_month["month"])
    print(f"Found {len(files)} files")
```

### 3. Analyze Documents

```python
from thegent.agents.document import DocumentAnalyzer
from pathlib import Path

analyzer = DocumentAnalyzer()
analysis = analyzer.analyze(Path("path/to/file.md"))
print(f"Category: {analysis.category.value}")
print(f"Reading time: {analysis.estimated_reading_time:.1f} minutes")
```

## CLI Usage

If CLI is set up, use:

```bash
# Scan
python3 -m thegent.cli.commands.queue scan --location kush:/Users/kooshapari/kush:true

# List months
python3 -m thegent.cli.commands.queue list

# Get next
python3 -m thegent.cli.commands.queue next --files
```

## Files Created

All integration files are in:
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/agents/document/`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/mcp/document_queue.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/cli/commands/queue.py`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/config/document_queue.yaml`

## Original Queue Files

The original queue system files are preserved in:
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/docs/research/MARKDOWN_SCAN_QUEUE.json`
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/docs/research/process_queue.py`

These can be used directly or migrated to use the new thegent integration.
