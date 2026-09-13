#!/usr/bin/env python3
"""
Helios Local Runner - Harbor-compatible lightweight benchmarking
====================================================

This provides Harbor-compatible benchmarking without Docker overhead.

Key differences:
- Harbor: Full Docker sandbox, production-grade
- Helios: Local execution, fast iteration

Usage:
    helios-run --task palindrome --binary /path/to/codex
"""

import argparse
import json
import subprocess
import time
from typing import Any

TASKS = {
    "palindrome": {
        "instruction": "Write a Python function `is_palindrome(s: str) -> bool` that checks if a string is a palindrome.",
        "test": "assert is_palindrome('racecar') == True\nassert is_palindrome('hello') == False",
    },
    "fibonacci": {
        "instruction": "Write a Python function `fib(n: int) -> int` that returns nth Fibonacci number.",
        "test": "assert fib(10) == 55",
    },
    "buggy_add": {
        "instruction": "Fix this buggy code:\ndef add(a, b):\n    return a - b",
        "test": "assert add(2, 2) == 4",
    },
}


class HeliosRunner:
    def __init__(self, binary: str):
        self.binary = binary

    def run_task(self, task_id: str) -> dict[str, Any]:
        task = TASKS.get(task_id, TASKS["palindrome"])

        start = time.time()

        # Run the binary
        result = subprocess.run(
            [self.binary, "exec", "--skip-git-repo-check", task["instruction"]], capture_output=True, timeout=30
        )

        elapsed = time.time() - start

        return {
            "task_id": task_id,
            "elapsed": elapsed,
            "success": result.returncode == 0,
            "output": result.stdout.decode()[:500],
        }


def main():
    parser = argparse.ArgumentParser(description="Helios Local Runner")
    parser.add_argument("--binary", required=True)
    parser.add_argument("--task", default="palindrome")
    parser.add_argument("--output", default="helios-results.jsonl")

    args = parser.parse_args()

    runner = HeliosRunner(args.binary)
    result = runner.run_task(args.task)

    # Save
    with open(args.output, "a") as f:
        f.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
