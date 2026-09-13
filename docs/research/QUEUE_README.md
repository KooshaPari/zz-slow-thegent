<DONE>
# Markdown File Queue System

## Overview

This directory contains a comprehensive queue system for processing all markdown files found in:

- `kush/` (recursive, excluding node_modules)
- `kooshapari/` (3 levels down)
- `temp-PRODVERCEL/` (full recursive, excluding node_modules and .venv)

**Total files in queue:** 48,499 files (April 2025 - February 2026)

## Files Created

1. **`MARKDOWN_SCAN_QUEUE.json`** - Machine-readable queue data with full file listings
2. **`MARKDOWN_SCAN_QUEUE.txt`** - Human-readable text queue for browsing
3. **`MARKDOWN_SCAN_SUMMARY.md`** - Summary document with monthly breakdown
4. **`process_queue.py`** - Helper script to process the queue programmatically

## Queue Structure

The queue is organized by month (newest first), then by location:

```
[1] MONTH: 2026-02 (3572 files)
  Location: kush (5 files)
  Location: temp-PRODVERCEL (3567 files)

[2] MONTH: 2026-01 (7174 files)
  Location: temp-PRODVERCEL (7174 files)

... and so on back to April 2025
```

## Using the Queue Processor

### List all months

```bash
python3 process_queue.py --list
```

### Get next month to process

```bash
python3 process_queue.py --next
python3 process_queue.py --next --files  # Include file list
```

### Process specific month

```bash
# All files in a month
python3 process_queue.py --month 2026-02 --files

# Files from specific location
python3 process_queue.py --month 2026-02 --location kush --files

# Just count files
python3 process_queue.py --month 2026-02 --count
```

### Example Workflow

```bash
# 1. See what's next
python3 process_queue.py --next

# 2. Get files for February 2026, kush location
python3 process_queue.py --month 2026-02 --location kush --files > kush_feb_files.txt

# 3. Process files (your custom logic)
while IFS= read -r file; do
    echo "Processing: $file"
    # Your processing logic here
done < kush_feb_files.txt

# 4. Move to next month/location
python3 process_queue.py --next
```

## Monthly Summary

| Month   | Total  | kush | kooshapari | temp-PRODVERCEL |
| ------- | ------ | ---- | ---------- | --------------- |
| 2026-02 | 3,572  | 5    | 0          | 3,567           |
| 2026-01 | 7,174  | 0    | 0          | 7,174           |
| 2025-12 | 6,961  | 2    | 0          | 6,959           |
| 2025-11 | 8,077  | 0    | 0          | 8,077           |
| 2025-10 | 5,713  | 0    | 0          | 5,713           |
| 2025-09 | 528    | 0    | 0          | 528             |
| 2025-08 | 2,195  | 0    | 0          | 2,195           |
| 2025-07 | 2,792  | 0    | 0          | 2,792           |
| 2025-06 | 705    | 0    | 0          | 705             |
| 2025-05 | 120    | 0    | 0          | 120             |
| 2025-04 | 10,662 | 0    | 0          | 10,662          |

## Notes

- **kooshapari directory**: No markdown files found at 3 levels down
- **Exclusions**: All scans exclude `node_modules/` and `.venv/` directories
- **Processing order**: Start with February 2026 and work backwards to April 2025
- **File paths**: All paths are relative to `/Users/kooshapari/`

## Rescanning

To rescan with updated parameters, run the scan script again (it will overwrite the existing queue files).
