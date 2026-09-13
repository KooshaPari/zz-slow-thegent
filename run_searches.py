#!/usr/bin/env python3
"""Run the 6 specific ddgr searches requested."""

import logging
import sys
from pathlib import Path

import orjson as json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from thegent.skills.research import ddg_search

SEARCHES = [
    ("git audit trail enterprise 2025 2026", 5),
    ("git refs local-only namespace best practices", 5),
    ("git journaling filesystem changes track", 5),
    ("gitoxide gix performance 2025", 5),
    ("content-addressable storage git objects efficient", 5),
    ("git forensics audit trail tools 2025", 5),
]

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    all_results = {}
    for query, max_results in SEARCHES:
        logger.info("=== Searching: %s ===", query)
        results = ddg_search(query, max_results=max_results)
        all_results[query] = results
        logger.info("Found %s results", len(results))
        for i, r in enumerate(results[:3], 1):
            logger.info("  %s. %s", i, r.get("title", "N/A"))
            logger.info("     %s", r.get("href", "N/A"))
            logger.info("     %s...", r.get("body", "N/A")[:200])

    # Save results
    output_file = Path(__file__).parent / "search_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    logger.info("Results saved to %s", output_file)
