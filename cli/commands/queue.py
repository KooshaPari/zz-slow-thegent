"""
CLI Command for Document Queue Management

Provides command-line interface for scanning, managing, and processing
document queues.
"""

from pathlib import Path

import click
import orjson as json

from ...agents.document import (
    DocumentAnalyzer,
    DocumentProcessor,
    MarkdownScanner,
    ProcessingPipeline,
    QueueManager,
    ScanConfig,
    compute_file_hash,
    count_lines,
    extract_metadata,
)


@click.group("queue")
def queue_cmd():
    """Document queue management commands."""


@queue_cmd.command("scan")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--min-date", help="Minimum date (YYYY-MM)")
@click.option("--location", multiple=True, help="Location to scan (name:path:recursive:max_depth)")
def scan(config: str | None, output: str | None, min_date: str | None, location: tuple):
    """Scan for markdown files and create queue."""
    if config:
        # Load config from file
        with open(config) as f:
            config_data = json.load(f)
        scan_config = ScanConfig(
            locations=config_data.get("locations", {}),
            exclude_patterns=set(config_data.get("exclude_patterns", [])),
            min_date=min_date or config_data.get("min_date"),
            output_dir=Path(config_data.get("output_dir", "~/.thegent/scans")),
        )
    else:
        # Use default config or command-line locations
        locations = {}
        if location:
            for loc_str in location:
                parts = loc_str.split(":")
                if len(parts) >= 2:
                    name = parts[0]
                    path = parts[1]
                    recursive = parts[2].lower() == "true" if len(parts) > 2 else True
                    max_depth = int(parts[3]) if len(parts) > 3 and parts[3] else None
                    locations[name] = {
                        "path": path,
                        "recursive": recursive,
                        "max_depth": max_depth,
                    }

        scan_config = ScanConfig(
            locations=locations,
            min_date=min_date,
        )

    scanner = MarkdownScanner(scan_config)
    click.echo("Scanning for markdown files...")
    scanner.scan()

    output_path = Path(output) if output else None
    result_path = scanner.save_results(output_path)

    summary = scanner.get_summary()
    click.echo("\nScan complete!")
    click.echo(f"Total files: {summary['total_files']}")
    click.echo(f"Months: {summary['months']}")
    click.echo(f"Results saved to: {result_path}")


@queue_cmd.command("list")
@click.option("--queue-file", "-q", type=click.Path(exists=True), help="Queue file path")
def list_months(queue_file: str | None):
    """List all months in the queue."""
    if queue_file:
        queue_manager = QueueManager(Path(queue_file))
    else:
        queue_manager = QueueManager(Path.home() / ".thegent" / "scans" / "MARKDOWN_SCAN_QUEUE.json")

    months = queue_manager.list_months()
    click.echo("Available months:")
    for month_entry in months:
        month = month_entry["month"]
        total = month_entry["total_files"]
        locations = ", ".join([f"{loc['location']}({loc['file_count']})" for loc in month_entry["locations"]])
        click.echo(f"  {month}: {total} files [{locations}]")


@queue_cmd.command("next")
@click.option("--queue-file", "-q", type=click.Path(exists=True), help="Queue file path")
@click.option("--files", is_flag=True, help="Show file list")
def next_month(queue_file: str | None, files: bool):
    """Get next month to process."""
    if queue_file:
        queue_manager = QueueManager(Path(queue_file))
    else:
        queue_manager = QueueManager(Path.home() / ".thegent" / "scans" / "MARKDOWN_SCAN_QUEUE.json")

    next_month = queue_manager.get_next_month()
    if next_month:
        click.echo(f"Next month: {next_month['month']}")
        click.echo(f"Total files: {next_month['total_files']}")

        if files:
            for loc_entry in next_month["locations"]:
                click.echo(f"\n[{loc_entry['location']}] ({loc_entry['file_count']} files):")
                for filepath in loc_entry["files"][:10]:
                    click.echo(f"  {filepath}")
                if loc_entry["file_count"] > 10:
                    click.echo(f"  ... and {loc_entry['file_count'] - 10} more")
    else:
        click.echo("No more months to process!")


@queue_cmd.command("files")
@click.argument("month")
@click.option("--location", help="Filter by location")
@click.option("--queue-file", "-q", type=click.Path(exists=True), help="Queue file path")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def get_files(month: str, location: str | None, queue_file: str | None, output: str | None):
    """Get files for a specific month."""
    if queue_file:
        queue_manager = QueueManager(Path(queue_file))
    else:
        queue_manager = QueueManager(Path.home() / ".thegent" / "scans" / "MARKDOWN_SCAN_QUEUE.json")

    files = queue_manager.get_month_files(month, location)

    if output:
        with open(output, "w") as f:
            f.writelines(f"{filepath}\n" for filepath in files)
        click.echo(f"Wrote {len(files)} files to {output}")
    else:
        for filepath in files:
            click.echo(filepath)


@queue_cmd.command("summary")
@click.option("--queue-file", "-q", type=click.Path(exists=True), help="Queue file path")
def summary(queue_file: str | None):
    """Get queue summary statistics."""
    if queue_file:
        queue_manager = QueueManager(Path(queue_file))
    else:
        queue_manager = QueueManager(Path.home() / ".thegent" / "scans" / "MARKDOWN_SCAN_QUEUE.json")

    summary_data = queue_manager.get_summary()
    click.echo("Queue Summary:")
    click.echo(f"  Total files: {summary_data['total_files']}")
    click.echo(f"  Total months: {summary_data['total_months']}")
    click.echo(f"  Processed: {summary_data['processed']}")
    click.echo(f"  Skipped: {summary_data['skipped']}")
    click.echo(f"  Failed: {summary_data['failed']}")
    click.echo(f"  Remaining: {summary_data['remaining']}")
    if summary_data["last_processed_month"]:
        click.echo(f"  Last processed: {summary_data['last_processed_month']}")
        if summary_data["last_processed_location"]:
            click.echo(f"    Location: {summary_data['last_processed_location']}")


@queue_cmd.command("process")
@click.argument("filepath")
@click.option("--queue-file", "-q", type=click.Path(exists=True), help="Queue file path")
@click.option("--analyze", is_flag=True, help="Also analyze the document")
def process_file(filepath: str, queue_file: str | None, analyze: bool):
    """Process a single file."""
    path = Path(filepath)
    if not path.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return

    # Create processing pipeline
    pipeline = ProcessingPipeline()
    pipeline.add_stage(extract_metadata)
    pipeline.add_stage(compute_file_hash)
    pipeline.add_stage(count_lines)

    processor = DocumentProcessor(pipeline)
    result = processor.process_file(filepath)

    if result.status.value == "completed":
        click.echo(f"Processed: {filepath}")
        click.echo(f"  Processing time: {result.processing_time:.2f}s")
        if result.metadata:
            click.echo(f"  Metadata: {json.dumps(result.metadata, indent=2).decode()}")

        # Mark as processed in queue
        if queue_file:
            queue_manager = QueueManager(Path(queue_file))
            queue_manager.mark_file_processed(filepath)
    else:
        click.echo(f"Failed: {filepath}")
        if result.error:
            click.echo(f"  Error: {result.error}", err=True)

    if analyze:
        analyzer = DocumentAnalyzer()
        analysis = analyzer.analyze(path)
        click.echo("\nAnalysis:")
        click.echo(f"  Category: {analysis.category.value}")
        click.echo(f"  Word count: {analysis.word_count}")
        click.echo(f"  Estimated reading time: {analysis.estimated_reading_time:.1f} minutes")
        click.echo(f"  Sections: {analysis.section_count}")


@queue_cmd.command("analyze")
@click.argument("filepath")
def analyze_file(filepath: str):
    """Analyze a document."""
    path = Path(filepath)
    if not path.exists():
        click.echo(f"Error: File not found: {filepath}", err=True)
        return

    analyzer = DocumentAnalyzer()
    analysis = analyzer.analyze(path)

    click.echo(f"Analysis for: {filepath}")
    click.echo(f"  Category: {analysis.category.value}")
    click.echo(f"  Word count: {analysis.word_count}")
    click.echo(f"  Estimated reading time: {analysis.estimated_reading_time:.1f} minutes")
    click.echo(f"  Sections: {analysis.section_count}")
    click.echo(f"  Has code blocks: {analysis.has_code_blocks}")
    click.echo(f"  Has images: {analysis.has_images}")
    click.echo(f"  Has links: {analysis.has_links}")
    if analysis.keywords:
        click.echo(f"  Keywords: {', '.join(list(analysis.keywords)[:10])}")
