#!/usr/bin/env python3
"""
Generate All Specs, WBS, and PRDs

Analyzes all projects, extracts specs/WBS/PRD content from markdown files,
performs cross-project analysis, and generates unified work streams and PRDs.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import orjson as json

# Add thegent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from thegent.specs.cross_project_analyzer import CrossProjectAnalyzer
from thegent.specs.markdown_analyzer import MarkdownAnalyzer, ProjectSpecs
from thegent.specs.prd_generator import PRDGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecsGenerator:
    """Generates specs, WBS, and PRDs for all projects."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.project_specs: dict[str, ProjectSpecs] = {}
        self.cross_analyzer: CrossProjectAnalyzer | None = None
        self.results = {
            "started_at": datetime.now().isoformat(),
            "projects_analyzed": [],
            "specs_generated": [],
            "wbs_generated": [],
            "prds_generated": [],
        }

    def discover_projects(self, limit: int | None = None) -> list[Path]:
        """Discover all projects to analyze."""
        projects = set()

        # Scan temp-PRODVERCEL for actual project directories
        temp_prodvercel = self.base_path.parent.parent

        # Look for directories that contain markdown files (limit depth for performance)
        for item in temp_prodvercel.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Quick check: has README or docs directory
            if (item / "README.md").exists() or (item / "docs").exists():
                projects.add(item)
                if limit and len(projects) >= limit:
                    break

        # Also check 485 subdirectory (prioritize this)
        dir_485 = temp_prodvercel / "485"
        if dir_485.exists():
            for item in dir_485.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # Quick check for markdown files (limit depth)
                    try:
                        md_count = len(list(item.glob("*.md"))) + len(
                            list((item / "docs").glob("*.md") if (item / "docs").exists() else [])
                        )
                        if md_count > 0:
                            projects.add(item)
                            if limit and len(projects) >= limit:
                                break
                    except:
                        pass

        # Filter to only directories
        projects = {p for p in projects if p.is_dir()}

        logger.info(f"Discovered {len(projects)} project directories")
        return sorted(projects)

    def analyze_all_projects(
        self, max_projects: int | None = None, max_files_per_project: int = 200
    ) -> dict[str, ProjectSpecs]:
        """Analyze all projects."""
        projects = self.discover_projects(limit=max_projects)
        logger.info(f"Analyzing {len(projects)} projects")

        for i, project_path in enumerate(projects):
            try:
                logger.info(f"[{i + 1}/{len(projects)}] Analyzing: {project_path.name}")
                analyzer = MarkdownAnalyzer(project_path)
                specs = analyzer.analyze_all_markdown(max_files=max_files_per_project)
                self.project_specs[project_path.name] = specs
                self.results["projects_analyzed"].append(
                    {
                        "project": project_path.name,
                        "files_analyzed": len(specs.analyzed_files),
                        "features": len(specs.features),
                        "tasks": len(specs.tasks),
                        "wbs_elements": len(specs.wbs_elements),
                    }
                )
                logger.info(
                    f"  ✓ Found {len(specs.features)} features, {len(specs.tasks)} tasks, {len(specs.wbs_elements)} WBS elements"
                )
            except Exception as e:
                logger.error(f"Error analyzing {project_path}: {e}")

        return self.project_specs

    def perform_cross_analysis(self):
        """Perform cross-project analysis."""
        logger.info("Performing cross-project analysis...")

        self.cross_analyzer = CrossProjectAnalyzer(self.project_specs)
        self.cross_analyzer.analyze()

        logger.info(f"Found {len(self.cross_analyzer.relationships)} relationships")
        logger.info(f"Found {len(self.cross_analyzer.unified_features)} shared features")
        logger.info(f"Created {len(self.cross_analyzer.unified_work_streams)} unified work streams")
        logger.info(f"Created {len(self.cross_analyzer.unified_prds)} unified PRDs")

    def generate_wbs_for_all(self):
        """Generate WBS for all projects."""
        logger.info("Generating WBS structures...")

        wbs_output_dir = self.base_path / "docs" / "specs" / "wbs"
        wbs_output_dir.mkdir(parents=True, exist_ok=True)

        for project_name in self.project_specs:
            try:
                wbs_data = self.cross_analyzer.generate_wbs_for_project(project_name)

                output_file = wbs_output_dir / f"{project_name}_wbs.json"
                with open(output_file, "w") as f:
                    json.dump(wbs_data, f, indent=2)

                self.results["wbs_generated"].append(project_name)
                logger.info(f"Generated WBS for {project_name}")
            except Exception as e:
                logger.error(f"Error generating WBS for {project_name}: {e}")

    def generate_prds_for_all(self):
        """Generate PRDs for all projects."""
        logger.info("Generating PRDs...")

        prd_output_dir = self.base_path / "docs" / "specs" / "prds"
        prd_output_dir.mkdir(parents=True, exist_ok=True)

        for project_name, specs in self.project_specs.items():
            try:
                generator = PRDGenerator(specs, self.cross_analyzer)
                prd = generator.generate_prd()

                # Save as markdown
                md_file = prd_output_dir / f"{project_name}_prd.md"
                with open(md_file, "w") as f:
                    f.write(prd.to_markdown())

                # Save as JSON
                json_file = prd_output_dir / f"{project_name}_prd.json"
                with open(json_file, "w") as f:
                    json.dump(prd.to_dict(), f, indent=2)

                self.results["prds_generated"].append(project_name)
                logger.info(f"Generated PRD for {project_name}")
            except Exception as e:
                logger.error(f"Error generating PRD for {project_name}: {e}")

    def generate_unified_work_stream(self):
        """Generate unified work stream document."""
        logger.info("Generating unified work stream...")

        output_dir = self.base_path / "docs" / "specs"
        output_dir.mkdir(parents=True, exist_ok=True)

        unified_ws = {
            "generated_at": datetime.now().isoformat(),
            "total_projects": len(self.project_specs),
            "work_streams": {},
            "cross_project_features": {},
            "dependencies": {},
        }

        # Add unified work streams
        for ws_id, ws in self.cross_analyzer.unified_work_streams.items():
            unified_ws["work_streams"][ws_id] = {
                "name": ws.name,
                "projects": ws.projects,
                "phases": ws.phases,
                "estimated_hours": ws.estimated_hours,
            }

        # Add cross-project features
        for feat_id, feat in self.cross_analyzer.unified_features.items():
            unified_ws["cross_project_features"][feat_id] = {
                "title": feat.title,
                "projects": feat.projects,
                "priority": feat.priority,
            }

        # Add relationships
        for rel in self.cross_analyzer.relationships:
            if rel.project1 not in unified_ws["dependencies"]:
                unified_ws["dependencies"][rel.project1] = []
            unified_ws["dependencies"][rel.project1].append(
                {
                    "project": rel.project2,
                    "type": rel.relationship_type,
                    "strength": rel.strength,
                }
            )

        # Save
        output_file = output_dir / "UNIFIED_WORK_STREAM.json"
        with open(output_file, "w") as f:
            json.dump(unified_ws, f, indent=2)

        # Generate markdown version
        md_content = self._generate_work_stream_markdown(unified_ws)
        md_file = output_dir / "UNIFIED_WORK_STREAM.md"
        with open(md_file, "w") as f:
            f.write(md_content)

        logger.info(f"Unified work stream saved to: {output_file}")

    def _generate_work_stream_markdown(self, unified_ws: dict) -> str:
        """Generate markdown for unified work stream."""
        md = f"""# Unified Work Stream

**Generated:** {unified_ws["generated_at"]}
**Total Projects:** {unified_ws["total_projects"]}

## Overview

This document represents a unified work stream across {unified_ws["total_projects"]} projects,
consolidating features, requirements, and work breakdown structures from all project markdown files.

## Work Streams

"""
        for ws_data in unified_ws["work_streams"].values():
            md += f"### {ws_data['name']}\n\n"
            md += f"**Projects:** {', '.join(ws_data['projects'])}\n\n"
            md += f"**Estimated Hours:** {ws_data.get('estimated_hours', 0):.1f}\n\n"
            md += "**Phases:**\n\n"
            for phase in ws_data.get("phases", []):
                md += f"- **{phase.get('name', 'Phase')}**: {phase.get('description', '')[:100]}\n"
            md += "\n"

        md += "\n## Cross-Project Features\n\n"
        for feat_data in unified_ws["cross_project_features"].values():
            md += f"### {feat_data['title']}\n\n"
            md += f"**Projects:** {', '.join(feat_data['projects'])}\n"
            md += f"**Priority:** {feat_data['priority']}\n\n"

        md += "\n## Project Dependencies\n\n"
        for proj, deps in unified_ws["dependencies"].items():
            md += f"### {proj}\n\n"
            for dep in deps:
                md += f"- **{dep['project']}** ({dep['type']}, strength: {dep['strength']:.2f})\n"
            md += "\n"

        return md

    def save_results(self):
        """Save analysis results."""
        output_file = self.base_path / "docs" / "specs" / "ANALYSIS_RESULTS.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        results = {
            **self.results,
            "completed_at": datetime.now().isoformat(),
            "project_specs_summary": {
                name: {
                    "files_analyzed": len(specs.analyzed_files),
                    "features": len(specs.features),
                    "tasks": len(specs.tasks),
                    "wbs_elements": len(specs.wbs_elements),
                    "keywords": len(specs.keywords),
                    "technologies": list(specs.technologies),
                }
                for name, specs in self.project_specs.items()
            },
            "cross_analysis": self.cross_analyzer.to_dict() if self.cross_analyzer else {},
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate specs, WBS, and PRDs for all projects")
    parser.add_argument("--max-projects", type=int, help="Maximum number of projects to analyze")
    parser.add_argument("--max-files", type=int, default=200, help="Maximum files per project")
    parser.add_argument("--base-path", type=str, default="/Users/kooshapari/temp-PRODVERCEL/485/kush")

    args = parser.parse_args()

    base_path = Path(args.base_path)

    generator = SpecsGenerator(base_path)

    # Step 1: Analyze all projects
    generator.analyze_all_projects(max_projects=args.max_projects, max_files_per_project=args.max_files)

    if not generator.project_specs:
        logger.error("No projects analyzed. Exiting.")
        return 1

    # Step 2: Cross-project analysis
    generator.perform_cross_analysis()

    # Step 3: Generate WBS
    generator.generate_wbs_for_all()

    # Step 4: Generate PRDs
    generator.generate_prds_for_all()

    # Step 5: Generate unified work stream
    generator.generate_unified_work_stream()

    # Step 6: Save results
    generator.save_results()

    if generator.cross_analyzer:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
