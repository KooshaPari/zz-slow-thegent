"""
PRD Generator

Generates comprehensive Product Requirements Documents from analyzed markdown files.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime

from .cross_project_analyzer import CrossProjectAnalyzer
from .markdown_analyzer import ProjectSpecs


@dataclass
class PRD:
    """Product Requirements Document."""

    project_name: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)

    # Overview
    overview: str = ""
    objectives: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)

    # Stakeholders
    stakeholders: list[dict] = field(default_factory=list)
    target_users: list[str] = field(default_factory=list)

    # Requirements
    functional_requirements: list[dict] = field(default_factory=list)
    non_functional_requirements: list[dict] = field(default_factory=list)

    # Features
    features: list[dict] = field(default_factory=list)
    feature_priorities: dict[str, str] = field(default_factory=dict)

    # Architecture
    architecture_overview: str = ""
    technical_requirements: list[str] = field(default_factory=list)
    integration_points: list[dict] = field(default_factory=list)

    # Timeline
    phases: list[dict] = field(default_factory=list)
    milestones: list[dict] = field(default_factory=list)

    # Dependencies
    dependencies: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    # Cross-project
    related_projects: list[str] = field(default_factory=list)
    shared_features: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert PRD to markdown."""
        md = f"""# Product Requirements Document: {self.project_name}

**Version:** {self.version}
**Created:** {self.created_at.strftime("%Y-%m-%d")}

## 1. Overview

{self.overview}

## 2. Objectives

"""
        for obj in self.objectives:
            md += f"- {obj}\n"

        md += "\n## 3. Success Metrics\n\n"
        for metric in self.success_metrics:
            md += f"- {metric}\n"

        md += "\n## 4. Stakeholders\n\n"
        for stakeholder in self.stakeholders:
            md += f"- **{stakeholder.get('name', 'Unknown')}**: {stakeholder.get('role', '')}\n"

        md += "\n## 5. Target Users\n\n"
        for user in self.target_users:
            md += f"- {user}\n"

        md += "\n## 6. Functional Requirements\n\n"
        for i, req in enumerate(self.functional_requirements, 1):
            md += f"### FR-{i}: {req.get('title', 'Requirement')}\n\n"
            md += f"{req.get('description', '')}\n\n"
            if req.get("acceptance_criteria"):
                md += "**Acceptance Criteria:**\n"
                for ac in req.get("acceptance_criteria", []):
                    md += f"- {ac}\n"
            md += "\n"

        md += "\n## 7. Non-Functional Requirements\n\n"
        for i, req in enumerate(self.non_functional_requirements, 1):
            md += f"### NFR-{i}: {req.get('title', 'Requirement')}\n\n"
            md += f"{req.get('description', '')}\n\n"

        md += "\n## 8. Features\n\n"
        for feature in self.features:
            priority_badge = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(feature.get("priority", "medium"), "🟡")

            md += f"### {priority_badge} {feature.get('title', 'Feature')}\n\n"
            md += f"{feature.get('description', '')}\n\n"
            if feature.get("acceptance_criteria"):
                md += "**Acceptance Criteria:**\n"
                for ac in feature.get("acceptance_criteria", []):
                    md += f"- {ac}\n"
            md += "\n"

        md += "\n## 9. Architecture Overview\n\n"
        md += f"{self.architecture_overview}\n\n"

        md += "\n## 10. Technical Requirements\n\n"
        for req in self.technical_requirements:
            md += f"- {req}\n"

        md += "\n## 11. Integration Points\n\n"
        for integration in self.integration_points:
            md += f"- **{integration.get('name', 'Integration')}**: {integration.get('description', '')}\n"

        md += "\n## 12. Timeline & Phases\n\n"
        for phase in self.phases:
            md += f"### Phase {phase.get('number', '?')}: {phase.get('name', 'Phase')}\n\n"
            md += f"{phase.get('description', '')}\n\n"
            if phase.get("estimated_hours"):
                md += f"**Estimated Hours:** {phase.get('estimated_hours')}\n\n"

        md += "\n## 13. Milestones\n\n"
        for milestone in self.milestones:
            md += f"- **{milestone.get('name', 'Milestone')}**: {milestone.get('date', 'TBD')}\n"

        md += "\n## 14. Dependencies\n\n"
        for dep in self.dependencies:
            md += f"- {dep}\n"

        if self.blockers:
            md += "\n## 15. Blockers\n\n"
            for blocker in self.blockers:
                md += f"- {blocker}\n"

        if self.related_projects:
            md += "\n## 16. Related Projects\n\n"
            for proj in self.related_projects:
                md += f"- {proj}\n"

        if self.shared_features:
            md += "\n## 17. Shared Features\n\n"
            for feature in self.shared_features:
                md += f"- {feature}\n"

        return md

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "project_name": self.project_name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "overview": self.overview,
            "objectives": self.objectives,
            "success_metrics": self.success_metrics,
            "stakeholders": self.stakeholders,
            "target_users": self.target_users,
            "functional_requirements": self.functional_requirements,
            "non_functional_requirements": self.non_functional_requirements,
            "features": self.features,
            "feature_priorities": self.feature_priorities,
            "architecture_overview": self.architecture_overview,
            "technical_requirements": self.technical_requirements,
            "integration_points": self.integration_points,
            "phases": self.phases,
            "milestones": self.milestones,
            "dependencies": self.dependencies,
            "blockers": self.blockers,
            "related_projects": self.related_projects,
            "shared_features": self.shared_features,
        }


class PRDGenerator:
    """Generates PRDs from project specs."""

    def __init__(
        self,
        project_specs: ProjectSpecs,
        cross_analyzer: CrossProjectAnalyzer | None = None,
    ) -> None:
        self.project_specs = project_specs
        self.cross_analyzer = cross_analyzer

    def generate_prd(self) -> PRD:
        """Generate comprehensive PRD from project specs."""
        prd = PRD(project_name=self.project_specs.project_name)

        # Extract overview from README or main docs
        prd.overview = self._extract_overview()

        # Extract objectives
        prd.objectives = self._extract_objectives()

        # Extract success metrics
        prd.success_metrics = self._extract_success_metrics()

        # Extract stakeholders
        prd.stakeholders = self._extract_stakeholders()

        # Extract target users
        prd.target_users = self._extract_target_users()

        # Convert features to functional requirements
        prd.functional_requirements = self._features_to_requirements()

        # Extract non-functional requirements
        prd.non_functional_requirements = self._extract_non_functional_requirements()

        # Add features
        prd.features = self._extract_features()

        # Extract architecture
        prd.architecture_overview = self._extract_architecture()

        # Extract technical requirements
        prd.technical_requirements = self._extract_technical_requirements()

        # Extract integration points
        prd.integration_points = self._extract_integration_points()

        # Create phases from WBS
        prd.phases = self._wbs_to_phases()

        # Extract milestones
        prd.milestones = self._extract_milestones()

        # Extract dependencies
        prd.dependencies = list(self.project_specs.dependencies)
        prd.related_projects = list(self.project_specs.related_projects)

        # Add shared features from cross-analysis
        if self.cross_analyzer:
            shared = [
                f.title
                for f in self.cross_analyzer.unified_features.values()
                if self.project_specs.project_name in f.projects
            ]
            prd.shared_features = shared

        return prd

    def _extract_overview(self) -> str:
        """Extract project overview."""
        # Look for README
        readme_files = ["README.md", "README.rst"]
        for readme_name in readme_files:
            readme_path = self.project_specs.project_path / readme_name
            if readme_path.exists():
                content = readme_path.read_text()
                # Extract first paragraph or overview section
                overview_match = re.search(
                    r"##\s+Overview[:\-]?\s*(.+?)(?=##|$)",
                    content,
                    re.DOTALL | re.IGNORECASE,
                )
                if overview_match:
                    return overview_match.group(1).strip()[:500]
                # Or first paragraph
                paragraphs = content.split("\n\n")
                if paragraphs:
                    return paragraphs[0].strip()[:500]

        return f"Project {self.project_specs.project_name} requirements and specifications."

    def _extract_objectives(self) -> list[str]:
        """Extract objectives."""
        objectives = []

        # Look in PRD sections
        for section in self.project_specs.prd_sections:
            if "objective" in section.title.lower():
                # Extract list items
                items = re.findall(
                    r"[-*]\s*(.+?)(?=^[-*]|$)", section.content, re.MULTILINE
                )
                objectives.extend(items[:10])

        # Look in features for goals
        for feature in self.project_specs.features.values():
            if (
                "goal" in feature.description.lower()
                or "objective" in feature.description.lower()
            ):
                objectives.append(feature.title)

        return objectives[:10]

    def _extract_success_metrics(self) -> list[str]:
        """Extract success metrics."""
        metrics = []

        for section in self.project_specs.prd_sections:
            if "metric" in section.title.lower() or "success" in section.title.lower():
                items = re.findall(
                    r"[-*]\s*(.+?)(?=^[-*]|$)", section.content, re.MULTILINE
                )
                metrics.extend(items[:10])

        return metrics[:10]

    def _extract_stakeholders(self) -> list[dict]:
        """Extract stakeholders."""
        return []  # Would need specific extraction

    def _extract_target_users(self) -> list[str]:
        """Extract target users."""
        users = set()

        for feature in self.project_specs.features.values():
            # Look for user mentions
            user_matches = re.findall(
                r"\b(user|developer|admin|operator|end.?user)\b",
                feature.description,
                re.IGNORECASE,
            )
            users.update(user_matches)

        return list(users)

    def _features_to_requirements(self) -> list[dict]:
        """Convert features to functional requirements."""
        requirements = []

        for feature in self.project_specs.features.values():
            req = {
                "id": feature.id,
                "title": feature.title,
                "description": feature.description,
                "priority": feature.priority.value,
                "acceptance_criteria": feature.acceptance_criteria,
                "dependencies": feature.dependencies,
            }
            requirements.append(req)

        return requirements

    def _extract_non_functional_requirements(self) -> list[dict]:
        """Extract non-functional requirements."""
        nfrs = []

        # Look for NFR sections
        for section in self.project_specs.prd_sections:
            if any(
                term in section.title.lower()
                for term in ["performance", "security", "scalability", "reliability"]
            ):
                nfrs.append(
                    {
                        "title": section.title,
                        "description": section.content[:500],
                    }
                )

        return nfrs

    def _extract_features(self) -> list[dict]:
        """Extract features."""
        features = []

        for feature in self.project_specs.features.values():
            features.append(
                {
                    "id": feature.id,
                    "title": feature.title,
                    "description": feature.description,
                    "priority": feature.priority.value,
                    "acceptance_criteria": feature.acceptance_criteria,
                    "tags": list(feature.tags),
                }
            )

        return features

    def _extract_architecture(self) -> str:
        """Extract architecture overview."""
        for section in self.project_specs.prd_sections:
            if "architecture" in section.title.lower():
                return section.content[:1000]

        return "Architecture details to be documented."

    def _extract_technical_requirements(self) -> list[str]:
        """Extract technical requirements."""
        tech_reqs = []

        # Extract from technologies
        tech_reqs.extend(
            [f"Use {tech}" for tech in list(self.project_specs.technologies)[:10]]
        )

        return tech_reqs

    def _extract_integration_points(self) -> list[dict]:
        """Extract integration points."""
        integrations = []

        # From related projects
        for proj in self.project_specs.related_projects:
            integrations.append(
                {
                    "name": f"Integration with {proj}",
                    "description": f"Integration point with {proj} project",
                    "type": "project_integration",
                }
            )

        return integrations

    def _wbs_to_phases(self) -> list[dict]:
        """Convert WBS to phases."""
        phases = []

        # Get level 1 WBS elements as phases
        level1_elements = [
            w for w in self.project_specs.wbs_elements.values() if w.level == 1
        ]

        for i, element in enumerate(level1_elements, 1):
            phase = {
                "number": i,
                "name": element.name,
                "description": element.description,
                "estimated_hours": element.estimated_hours,
                "deliverables": element.deliverables,
                "dependencies": element.dependencies,
            }
            phases.append(phase)

        return phases

    def _extract_milestones(self) -> list[dict]:
        """Extract milestones."""
        milestones = []

        # Look for milestone patterns
        for section in self.project_specs.prd_sections:
            if "milestone" in section.title.lower():
                items = re.findall(
                    r"[-*]\s*(.+?)(?=^[-*]|$)", section.content, re.MULTILINE
                )
                for item in items[:10]:
                    milestones.append(
                        {
                            "name": item.strip(),
                            "date": "TBD",
                        }
                    )

        return milestones
