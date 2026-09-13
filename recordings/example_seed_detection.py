"""Example: Record seed detection feature demo.

This script demonstrates how to use PlaywrightRecorder to capture
interactive demonstrations of the seed detection workflow.

Usage:
    # Start VitePress dev server in another terminal:
    #   bun run docs:dev

    # Then run this script:
    python3 recordings/example_seed_detection.py
"""

import asyncio
import logging
from pathlib import Path

from thegent.doc_tools import PlaywrightRecorder, RecordingConfig  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def record_seed_detection_demo() -> None:
    """Record seed detection feature demonstration."""

    # Configure recording
    config = RecordingConfig(
        base_url="http://localhost:5173",
        browser="chromium",
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        output_dir=Path("docs/recordings/outputs"),
    )

    async with PlaywrightRecorder(config) as recorder:
        # Record a feature demo with interactions
        result = await recorder.record_feature(
            feature_name="seed-detection-workflow",
            route="/guides/seed-detection/",
            initial_wait_ms=2000,
            interactions=[
                # Wait for page to fully load
                ("wait", "[data-demo='seed-input']", None),
                # Click input field
                ("click", "input[type='text'][placeholder*='Seed']", None),
                # Type a seed value
                (
                    "type",
                    "input[type='text'][placeholder*='Seed']",
                    "example_seed_12345",
                ),
                # Wait a moment for validation
                ("sleep", "1000", None),
                # Click analyze button
                ("click", "button[type='submit']:contains('Analyze')", None),
                # Wait for results
                ("wait", "[data-demo='detection-results']", None),
                ("sleep", "1500", None),
            ],
            description="Demonstrates seed detection workflow",
        )

        if result.success:
            logger.info("Recording succeeded!")
            logger.info(f"Screenshots: {result.screenshot_paths}")
            logger.info(f"Metadata: {result.metadata}")

            # Save metadata
            if result.screenshot_paths:
                metadata_path = config.output_dir / "seed-detection-metadata.json"
                result.to_json(metadata_path)
                logger.info(f"Metadata saved to {metadata_path}")
        else:
            logger.error(f"Recording failed: {result.error}")


async def record_health_scoring_demo() -> None:
    """Record health scoring demonstration."""

    config = RecordingConfig(
        base_url="http://localhost:5173",
        browser="chromium",
        headless=False,
        output_dir=Path("docs/recordings/outputs"),
    )

    async with PlaywrightRecorder(config) as recorder:
        # Multi-step workflow
        result = await recorder.record_page_flow(
            flow_name="health-scoring-workflow",
            description="Complete health scoring workflow",
            steps=[
                # Step 1: Navigate to health scoring page
                {
                    "navigate": "/guides/health-scoring/",
                    "wait_ms": 2000,
                },
                # Step 2: Fill out health parameters
                {
                    "actions": [
                        ("wait", "form[data-form='health-params']", None),
                        ("fill", "input[name='name']", "Example Agent", None),
                        ("fill", "input[name='uptime_hours']", "24", None),
                        ("click", "button[name='score-type']:contains('Full')", None),
                    ],
                },
                # Step 3: Submit and wait for results
                {
                    "actions": [
                        ("click", "button[type='submit']:contains('Calculate')", None),
                        ("wait", "[data-result='health-score']", None),
                    ],
                    "screenshot": "health-score-result",
                },
                # Step 4: View detailed metrics
                {
                    "actions": [
                        ("click", "button:contains('View Metrics')", None),
                        ("wait", "[data-section='detailed-metrics']", None),
                    ],
                    "screenshot": "health-score-metrics",
                },
            ],
        )

        if result.success:
            logger.info(
                f"Flow recording succeeded with {len(result.screenshot_paths)} screenshots"
            )
            metadata_path = config.output_dir / "health-scoring-metadata.json"
            result.to_json(metadata_path)
        else:
            logger.error(f"Flow recording failed: {result.error}")


async def record_tui_lifecycle_demo() -> None:
    """Record TUI (Text User Interface) lifecycle demonstration."""

    config = RecordingConfig(
        base_url="http://localhost:5173",
        browser="chromium",
        headless=False,
        viewport_width=1280,
        viewport_height=900,  # Taller for terminal UI
        output_dir=Path("docs/recordings/outputs"),
    )

    async with PlaywrightRecorder(config) as recorder:
        # Record TUI lifecycle interaction
        result = await recorder.record_feature(
            feature_name="tui-lifecycle-demo",
            route="/guides/tui-lifecycle/",
            initial_wait_ms=3000,
            interactions=[
                ("wait", "[data-component='tui-terminal']", None),
                ("click", "button[data-action='start-session']", None),
                ("wait", "[data-state='session-active']", None),
                ("sleep", "2000", None),
                ("click", "button[data-action='expand-panel']", None),
                ("sleep", "1000", None),
                ("screenshot", "tui-expanded-state", None),
            ],
            description="TUI lifecycle and session management",
        )

        if result.success:
            logger.info(f"TUI demo recorded: {result.screenshot_paths}")
            metadata_path = config.output_dir / "tui-lifecycle-metadata.json"
            result.to_json(metadata_path)
        else:
            logger.error(f"TUI demo failed: {result.error}")


async def main() -> None:
    """Run all example recordings."""
    logger.info("Starting example recordings...")
    logger.info("Make sure VitePress dev server is running: bun run docs:dev")

    try:
        logger.info("\n=== Recording Seed Detection Demo ===")
        await record_seed_detection_demo()

        logger.info("\n=== Recording Health Scoring Demo ===")
        await record_health_scoring_demo()

        logger.info("\n=== Recording TUI Lifecycle Demo ===")
        await record_tui_lifecycle_demo()

        logger.info("\nAll recordings completed!")

    except Exception as e:
        logger.error(f"Error during recordings: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
