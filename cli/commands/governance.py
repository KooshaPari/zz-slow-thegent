"""
CLI Commands for Governance Operations

Provides command-line interface for governance setup, quality assessment,
auditing, and reporting.
"""

from pathlib import Path

import click
import orjson as json

from ...governance.audit_framework import AuditFramework, AuditType
from ...governance.project_setup_enhanced import ProjectGovernanceSetupEnhanced
from ...governance.quality_matrix_enhanced import QualityMatrixBuilderEnhanced
from ...governance.reporting import ReportFormat, ReportGenerator
from ...governance.task_manager_enhanced import TaskManagerEnhanced


@click.group("governance")
def governance_cmd():
    """Governance management commands."""


@governance_cmd.command("analyze")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", type=click.Choice(["json", "yaml", "markdown"]), default="json")
def analyze_project(project_path: str, output: str | None, format: str):
    """Analyze project structure and governance."""
    project = Path(project_path)

    click.echo(f"Analyzing project: {project}")

    setup = ProjectGovernanceSetupEnhanced(project)
    structure = setup.analyze()

    result = {
        "project_path": str(project),
        "governance_level": structure.governance_level.value,
        "score": structure.calculate_score(),
        "project_type": structure.project_type.value,
        "missing_items": structure.missing_items,
        "recommendations": structure.recommendations,
        "warnings": structure.warnings,
    }

    if output:
        output_path = Path(output)
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
        elif format == "yaml":
            import yaml

            with open(output_path, "w") as f:
                yaml.dump(result, f, default_flow_style=False)
        click.echo(f"Results saved to: {output_path}")
    else:
        click.echo(json.dumps(result, indent=2).decode())


@governance_cmd.command("setup")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Force overwrite existing files")
def setup_governance(project_path: str, force: bool):
    """Set up governance for a project."""
    project = Path(project_path)

    click.echo(f"Setting up governance for: {project}")

    setup = ProjectGovernanceSetupEnhanced(project)
    setup.setup_basic_structure(force=force)

    click.echo("✓ Governance setup complete!")


@governance_cmd.command("quality")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def assess_quality(project_path: str, output: str | None):
    """Assess project quality."""
    project = Path(project_path)

    click.echo(f"Assessing quality for: {project}")

    builder = QualityMatrixBuilderEnhanced(project)
    matrix = builder.build()

    if output:
        output_path = Path(output)
        matrix.save(output_path)
        click.echo(f"Quality matrix saved to: {output_path}")
    else:
        output_path = project / "governance" / "quality-matrix.json"
        matrix.save(output_path)
        click.echo(f"Quality matrix saved to: {output_path}")

    click.echo(f"\nOverall Score: {matrix.overall_score:.1f}/100")
    click.echo(f"Quality Level: {matrix.quality_level.value}")
    click.echo(f"Trend: {matrix.trend.value}")


@governance_cmd.command("audit")
@click.argument("project_path", type=click.Path(exists=True))
@click.option(
    "--type",
    "audit_type",
    type=click.Choice(
        [
            "code_review",
            "dependency",
            "security",
            "documentation",
            "performance",
            "compliance",
            "quality",
            "architecture",
            "accessibility",
            "testing",
            "all",
        ]
    ),
    default="all",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def run_audit(project_path: str, audit_type: str, output: str | None):
    """Run audits on a project."""
    project = Path(project_path)

    click.echo(f"Running audit for: {project}")

    framework = AuditFramework(project)

    if audit_type == "all":
        results = framework.run_all_audits()
    else:
        audit_enum = AuditType(audit_type)
        result = framework.run_audit(audit_enum)
        results = {audit_enum: result}

    if output:
        output_path = Path(output)
        framework.save_results(output_path)
    else:
        framework.save_results()

    click.echo("\nAudit Results:")
    for res_type, result in results.items():
        click.echo(f"  {res_type.value}: {len(result.findings)} findings")
        severity_counts = result.get_severity_counts()
        for severity, count in severity_counts.items():
            click.echo(f"    {severity}: {count}")


@governance_cmd.command("report")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["json", "yaml", "markdown", "html", "console"]), default="console")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def generate_report(project_path: str, format: str, output: str | None):
    """Generate comprehensive governance report."""
    project = Path(project_path)

    click.echo(f"Generating report for: {project}")

    # Gather data
    setup = ProjectGovernanceSetupEnhanced(project)
    structure = setup.analyze()
    structure_data = {
        "governance_level": structure.governance_level.value,
        "score": structure.calculate_score(),
        "missing_items": structure.missing_items,
        "recommendations": structure.recommendations,
    }

    quality_matrix = None
    try:
        builder = QualityMatrixBuilderEnhanced(project)
        matrix = builder.build()
        quality_matrix = matrix.to_dict()
    except Exception as e:
        click.echo(f"Warning: Could not generate quality matrix: {e}")

    audit_results = None
    try:
        framework = AuditFramework(project)
        framework.run_all_audits()
        audit_results = framework.generate_report()
    except Exception as e:
        click.echo(f"Warning: Could not run audits: {e}")

    # Generate report
    generator = ReportGenerator(project)
    report = generator.generate_comprehensive_report(
        structure_data=structure_data,
        quality_matrix=quality_matrix,
        audit_results=audit_results,
    )

    if format == "console":
        generator.print_console_report(report)
    else:
        format_enum = ReportFormat(format)
        if output:
            output_path = Path(output)
        else:
            ext = {"json": ".json", "yaml": ".yaml", "markdown": ".md", "html": ".html"}.get(format, ".json")
            output_path = project / "governance" / f"report{ext}"

        generator.save_report(report, output_path, format_enum)
        click.echo(f"\nReport saved to: {output_path}")


@governance_cmd.command("tasks")
@click.option("--status", type=click.Choice(["pending", "in_progress", "completed", "all"]), default="all")
@click.option("--project", type=click.Path(), help="Filter by project")
@click.option("--priority", type=click.Choice(["critical", "high", "medium", "low"]), help="Filter by priority")
def list_tasks(status: str, project: str | None, priority: str | None):
    """List tasks."""
    manager = TaskManagerEnhanced()

    if status == "all":
        tasks = list(manager.tasks.values())
    else:
        from ...governance.task_manager_enhanced import TaskStatus

        status_enum = TaskStatus(status)
        tasks = manager.get_tasks_by_status(status_enum)

    if project:
        project_path = Path(project)
        tasks = [t for t in tasks if t.project_path == project_path]

    if priority:
        from ...governance.task_manager_enhanced import TaskPriority

        priority_enum = TaskPriority(priority)
        tasks = [t for t in tasks if t.priority == priority_enum]

    click.echo(f"\nFound {len(tasks)} tasks")
    for task in tasks[:20]:
        click.echo(f"  [{task.status.value}] {task.title} ({task.priority.value})")


@governance_cmd.command("stats")
def show_stats():
    """Show task statistics."""
    manager = TaskManagerEnhanced()
    stats = manager.get_statistics()

    click.echo("\nTask Statistics:")
    click.echo(f"  Total Tasks: {stats['total_tasks']}")
    click.echo(f"  By Status: {stats['by_status']}")
    click.echo(f"  By Priority: {stats['by_priority']}")
    click.echo(f"  Ready Tasks: {stats['ready_tasks']}")
    click.echo(f"  Overdue Tasks: {stats['overdue_tasks']}")
    click.echo(f"  Conflicts: {stats['conflicts']}")
    click.echo(f"  Estimated Hours: {stats['total_estimated_hours']:.1f}")
    click.echo(f"  Actual Hours: {stats['total_actual_hours']:.1f}")
