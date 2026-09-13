#!/usr/bin/env python3
"""
Queue Processor for Markdown Files

This script helps process the markdown file queue month by month.
Usage:
    python3 process_queue.py --month 2026-02 --location kush
    python3 process_queue.py --next
    python3 process_queue.py --list
"""

import argparse
import json
from pathlib import Path

QUEUE_FILE = Path(__file__).parent / "MARKDOWN_SCAN_QUEUE.json"


def load_queue() -> dict:
    """Load the queue JSON file."""
    with open(QUEUE_FILE) as f:
        return json.load(f)


def get_next_month(queue_data: dict, last_processed: str | None = None) -> dict | None:
    """Get the next month to process."""
    if last_processed is None:
        # Start with the first (newest) month
        return queue_data["queue"][0] if queue_data["queue"] else None

    # Find the month after last_processed
    found = False
    for month_entry in queue_data["queue"]:
        if found:
            return month_entry
        if month_entry["month"] == last_processed:
            found = True

    return None


def get_month_files(queue_data: dict, month: str, location: str | None = None) -> list[str]:
    """Get all files for a specific month, optionally filtered by location."""
    for month_entry in queue_data["queue"]:
        if month_entry["month"] == month:
            files = []
            for loc_entry in month_entry["locations"]:
                if location is None or loc_entry["location"] == location:
                    files.extend(loc_entry["files"])
            return files
    return []


def list_months(queue_data: dict):
    """List all months in the queue."""
    for month_entry in queue_data["queue"]:
        month_entry["month"]
        month_entry["total_files"]
        ", ".join([f"{loc['location']}({loc['file_count']})" for loc in month_entry["locations"]])


def main():
    parser = argparse.ArgumentParser(description="Process markdown file queue")
    parser.add_argument("--month", help="Process specific month (YYYY-MM)")
    parser.add_argument("--location", help="Filter by location (kush, kooshapari, temp-PRODVERCEL)")
    parser.add_argument("--next", action="store_true", help="Get next month to process")
    parser.add_argument("--list", action="store_true", help="List all months")
    parser.add_argument("--files", action="store_true", help="Output file list")
    parser.add_argument("--count", action="store_true", help="Show file count only")

    args = parser.parse_args()

    queue_data = load_queue()

    if args.list:
        list_months(queue_data)
        return

    if args.next:
        # Try to read last processed from a file
        last_file = Path(__file__).parent / ".last_processed"
        last_processed = None
        if last_file.exists():
            last_processed = last_file.read_text().strip()

        next_month = get_next_month(queue_data, last_processed)
        if next_month:
            if args.files:
                for loc_entry in next_month["locations"]:
                    for _filepath in loc_entry["files"][:10]:  # Show first 10
                        pass
                    if loc_entry["file_count"] > 10:
                        pass
        else:
            pass
        return

    if args.month:
        files = get_month_files(queue_data, args.month, args.location)

        if args.count:
            pass
        elif args.files:
            for _filepath in files:
                pass
        else:
            if args.location:
                pass
            for _filepath in files[:20]:
                pass
            if len(files) > 20:
                pass
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
