"""
CLI commands for specs/WBS/PRD generation.
"""

import sys
from pathlib import Path

import click
import orjson as json

# Add thegent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from thegent.specs.generate_all_specs import SpecsGenerator

console = Console()


@click.group()
def specs():
    """Generate specs, WBS, and PRDs from markdown files."""


@specs.command()
@click.option("--max-projects", type=int, help="Maximum number of projects to analyze")
@click.option("--max-files", type=int, default=200, help="Maximum files per project")
@click.option(
    "--base-path",
    type=str,
    default=None,
    help="Base path for analysis (defaults to current directory)",
)
@click.option("--output-dir", type=str, default="docs/specs")
def generate(max_projects, max_files, base_path, output_dir):
    """Generate specs, WBS, and PRDs for all projects."""
    base_path = Path.cwd() if base_path is None else Path(base_path)
    output_dir = Path(output_dir)

    console.print("[bold blue]Starting specs/WBS/PRD generation...[/bold blue]")

    generator = SpecsGenerator(base_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task1 = progress.add_task("Analyzing projects...", total=None)
        generator.analyze_all_projects(
            max_projects=max_projects, max_files_per_project=max_files
        )
        progress.update(task1, completed=True)

        if not generator.project_specs:
            console.print("[red]No projects analyzed. Exiting.[/red]")
            return

        task2 = progress.add_task("Cross-project analysis...", total=None)
        generator.perform_cross_analysis()
        progress.update(task2, completed=True)

        task3 = progress.add_task("Generating WBS...", total=None)
        generator.generate_wbs_for_all()
        progress.update(task3, completed=True)

        task4 = progress.add_task("Generating PRDs...", total=None)
        generator.generate_prds_for_all()
        progress.update(task4, completed=True)

        task5 = progress.add_task("Generating unified work stream...", total=None)
        generator.generate_unified_work_stream()
        progress.update(task5, completed=True)

        task6 = progress.add_task("Saving results...", total=None)
        generator.save_results()
        progress.update(task6, completed=True)

    # Display summary
    console.print("\n[bold green]✓ Generation Complete![/bold green]\n")

    table = Table(title="Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Projects Analyzed", str(len(generator.project_specs)))
    table.add_row("WBS Generated", str(len(generator.results["wbs_generated"])))
    table.add_row("PRDs Generated", str(len(generator.results["prds_generated"])))

    if generator.cross_analyzer:
        table.add_row(
            "Relationships Found", str(len(generator.cross_analyzer.relationships))
        )
        table.add_row(
            "Shared Features", str(len(generator.cross_analyzer.unified_features))
        )
        table.add_row(
            "Unified Work Streams",
            str(len(generator.cross_analyzer.unified_work_streams)),
        )
        table.add_row("Unified PRDs", str(len(generator.cross_analyzer.unified_prds)))

    console.print(table)

    console.print(f"\n[bold]Output directory:[/bold] {output_dir}")


@specs.command()
@click.option("--output-dir", type=str, default="docs/specs")
def list_projects(output_dir):
    """List all projects with generated specs."""
    output_dir = Path(output_dir)

    results_file = output_dir / "ANALYSIS_RESULTS.json"
    if not results_file.exists():
        console.print("[red]No analysis results found. Run 'generate' first.[/red]")
        return

    with open(results_file) as f:
        results = json.load(f)

    table = Table(title="Projects with Generated Specs")
    table.add_column("Project", style="cyan")
    table.add_column("Files", style="yellow")
    table.add_column("Features", style="green")
    table.add_column("Tasks", style="blue")
    table.add_column("WBS Elements", style="magenta")

    for project_data in results.get("project_specs_summary", {}).items():
        project_name, data = project_data
        table.add_row(
            project_name,
            str(data.get("files_analyzed", 0)),
            str(data.get("features", 0)),
            str(data.get("tasks", 0)),
            str(data.get("wbs_elements", 0)),
        )

    console.print(table)


@specs.command()
@click.argument("project_name")
@click.option("--output-dir", type=str, default="docs/specs")
def show_prd(project_name, output_dir):
    """Show PRD for a specific project."""
    output_dir = Path(output_dir)
    prd_file = output_dir / "prds" / f"{project_name}_prd.md"

    if not prd_file.exists():
        console.print(f"[red]PRD not found for project: {project_name}[/red]")
        return

    with open(prd_file) as f:
        content = f.read()

    console.print(content)


@specs.command()
@click.option("--output-dir", type=str, default="docs/specs")
def show_unified_workstream(output_dir):
    """Show unified work stream."""
    output_dir = Path(output_dir)
    ws_file = output_dir / "UNIFIED_WORK_STREAM.md"

    if not ws_file.exists():
        console.print("[red]Unified work stream not found. Run 'generate' first.[/red]")
        return

    with open(ws_file) as f:
        content = f.read()

    console.print(content)


if __name__ == "__main__":
    specs()
