"""
Cross-Project Analysis Engine

Analyzes multiple projects to find:
- Shared features
- Common patterns
- Dependencies
- Integration opportunities
- Unified work streams
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from .markdown_analyzer import ProjectSpecs, WBSElement

logger = logging.getLogger(__name__)


@dataclass
class CrossProjectRelationship:
    """Relationship between projects."""

    project1: str
    project2: str
    relationship_type: str  # dependency, shared_feature, integration, etc.
    strength: float  # 0.0 to 1.0
    details: dict = field(default_factory=dict)


@dataclass
class UnifiedFeature:
    """Feature that appears across multiple projects."""

    id: str
    title: str
    description: str
    projects: list[str] = field(default_factory=list)
    implementations: dict[str, str] = field(default_factory=dict)  # project -> feature_id
    priority: str = "medium"
    unified_requirement: str | None = None


@dataclass
class UnifiedWorkStream:
    """Unified work stream across projects."""

    id: str
    name: str
    description: str
    projects: list[str] = field(default_factory=list)
    phases: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimated_hours: float | None = None
    priority: str = "medium"


@dataclass
class UnifiedPRD:
    """Unified PRD across projects."""

    id: str
    title: str
    description: str
    projects: list[str] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    cross_project_dependencies: list[str] = field(default_factory=list)


class CrossProjectAnalyzer:
    """Analyzes multiple projects to find relationships and create unified specs."""

    def __init__(self, project_specs: dict[str, ProjectSpecs]) -> None:
        self.project_specs = project_specs
        self.relationships: list[CrossProjectRelationship] = []
        self.unified_features: dict[str, UnifiedFeature] = {}
        self.unified_work_streams: dict[str, UnifiedWorkStream] = {}
        self.unified_prds: dict[str, UnifiedPRD] = {}

    def analyze(self):
        """Perform cross-project analysis."""
        logger.info(f"Analyzing {len(self.project_specs)} projects")

        # Find relationships
        self._find_relationships()

        # Find shared features
        self._find_shared_features()

        # Create unified work streams
        self._create_unified_work_streams()

        # Create unified PRDs
        self._create_unified_prds()

    def _find_relationships(self):
        """Find relationships between projects."""
        project_names = list(self.project_specs.keys())

        for i, proj1 in enumerate(project_names):
            for proj2 in project_names[i + 1 :]:
                spec1 = self.project_specs[proj1]
                spec2 = self.project_specs[proj2]

                # Check for explicit references
                if proj2 in spec1.related_projects or proj1 in spec2.related_projects:
                    rel = CrossProjectRelationship(
                        project1=proj1,
                        project2=proj2,
                        relationship_type="reference",
                        strength=0.7,
                        details={"type": "explicit_reference"},
                    )
                    self.relationships.append(rel)

                # Check for shared keywords
                shared_keywords = spec1.keywords & spec2.keywords
                if len(shared_keywords) > 5:
                    rel = CrossProjectRelationship(
                        project1=proj1,
                        project2=proj2,
                        relationship_type="shared_domain",
                        strength=min(1.0, len(shared_keywords) / 20.0),
                        details={"shared_keywords": list(shared_keywords)[:10]},
                    )
                    self.relationships.append(rel)

                # Check for shared technologies
                shared_tech = spec1.technologies & spec2.technologies
                if shared_tech:
                    rel = CrossProjectRelationship(
                        project1=proj1,
                        project2=proj2,
                        relationship_type="shared_technology",
                        strength=min(1.0, len(shared_tech) / 5.0),
                        details={"shared_technologies": list(shared_tech)},
                    )
                    self.relationships.append(rel)

    def _find_shared_features(self):
        """Find features that appear across multiple projects."""
        feature_titles: dict[str, list[tuple[str, str]]] = defaultdict(list)  # title -> [(project, feature_id)]

        # Collect all features by normalized title
        for project_name, specs in self.project_specs.items():
            for feature_id, feature in specs.features.items():
                normalized_title = self._normalize_title(feature.title)
                feature_titles[normalized_title].append((project_name, feature_id))

        # Find features that appear in multiple projects
        for occurrences in feature_titles.values():
            if len(occurrences) > 1:
                # Get first occurrence as reference
                ref_project, ref_feature_id = occurrences[0]
                ref_feature = self.project_specs[ref_project].features[ref_feature_id]

                unified_feature = UnifiedFeature(
                    id=f"unified-feat-{len(self.unified_features)}",
                    title=ref_feature.title,
                    description=ref_feature.description,
                    projects=[proj for proj, _ in occurrences],
                    priority=ref_feature.priority.value,
                )

                for project_name, feature_id in occurrences:
                    unified_feature.implementations[project_name] = feature_id

                self.unified_features[unified_feature.id] = unified_feature

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Remove special chars, lowercase, remove common words
        normalized = re.sub(r"[^\w\s]", "", title.lower())
        words = normalized.split()
        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(sorted(words))  # Sort for consistency

    def _create_unified_work_streams(self):
        """Create unified work streams from all projects."""
        # Group projects by domain/keywords
        project_groups = self._group_projects_by_domain()

        for group_name, project_names in project_groups.items():
            if len(project_names) < 2:
                continue

            # Collect all WBS elements from these projects
            all_wbs = []
            for proj_name in project_names:
                specs = self.project_specs[proj_name]
                all_wbs.extend(specs.wbs_elements.values())

            # Create unified work stream
            work_stream = UnifiedWorkStream(
                id=f"unified-ws-{len(self.unified_work_streams)}",
                name=f"Unified Work Stream: {group_name}",
                description=f"Unified work stream for {len(project_names)} related projects",
                projects=project_names,
                phases=self._create_phases_from_wbs(all_wbs),
                estimated_hours=sum(w.estimated_hours or 0 for w in all_wbs),
            )

            self.unified_work_streams[work_stream.id] = work_stream

    def _group_projects_by_domain(self) -> dict[str, list[str]]:
        """Group projects by shared domain/keywords."""
        groups = defaultdict(list)

        for project_name, specs in self.project_specs.items():
            # Use top keywords to determine domain
            top_keywords = sorted(specs.keywords, key=len, reverse=True)[:5]
            domain = "-".join(top_keywords[:2]) if top_keywords else "general"
            groups[domain].append(project_name)

        return dict(groups)

    def _create_phases_from_wbs(self, wbs_elements: list[WBSElement]) -> list[dict]:
        """Create phases from WBS elements."""
        # Group by level 1 elements
        level1_elements = [w for w in wbs_elements if w.level == 1]

        phases = []
        for element in level1_elements:
            phase = {
                "name": element.name,
                "description": element.description,
                "estimated_hours": element.estimated_hours,
                "deliverables": element.deliverables,
                "dependencies": element.dependencies,
            }
            phases.append(phase)

        return phases

    def _create_unified_prds(self):
        """Create unified PRDs for related projects."""
        # Group projects by relationships
        project_groups = self._group_projects_by_relationships()

        for group_name, project_names in project_groups.items():
            if len(project_names) < 2:
                continue

            # Collect all PRD sections
            all_sections = []
            all_features = []
            all_requirements = []

            for proj_name in project_names:
                specs = self.project_specs[proj_name]
                all_sections.extend(specs.prd_sections)
                all_features.extend(list(specs.features.keys()))
                # Extract requirements from PRD sections
                for section in specs.prd_sections:
                    all_requirements.extend(section.requirements)

            # Create unified PRD
            prd = UnifiedPRD(
                id=f"unified-prd-{len(self.unified_prds)}",
                title=f"Unified PRD: {group_name}",
                description=f"Unified Product Requirements Document for {len(project_names)} related projects",
                projects=project_names,
                sections=[{"title": s.title, "content": s.content} for s in all_sections],
                features=all_features,
                requirements=all_requirements,
                cross_project_dependencies=list(
                    {dep for proj_name in project_names for dep in self.project_specs[proj_name].dependencies}
                ),
            )

            self.unified_prds[prd.id] = prd

    def _group_projects_by_relationships(self) -> dict[str, list[str]]:
        """Group projects by relationships."""
        # Use relationship graph to find connected components
        groups = {}

        for rel in self.relationships:
            if rel.strength > 0.5:  # Strong relationships only
                group_key = f"{rel.project1}-{rel.project2}"
                if group_key not in groups:
                    groups[group_key] = [rel.project1, rel.project2]
                else:
                    if rel.project1 not in groups[group_key]:
                        groups[group_key].append(rel.project1)
                    if rel.project2 not in groups[group_key]:
                        groups[group_key].append(rel.project2)

        return groups

    def generate_wbs_for_project(self, project_name: str) -> dict:
        """Generate comprehensive WBS for a project."""
        specs = self.project_specs[project_name]

        # Build WBS tree
        wbs_tree = {}
        root_elements = [w for w in specs.wbs_elements.values() if w.level == 1]

        for root in root_elements:
            wbs_tree[root.id] = self._build_wbs_tree(root, specs.wbs_elements)

        return {
            "project": project_name,
            "wbs_elements": len(specs.wbs_elements),
            "tree": wbs_tree,
            "total_estimated_hours": sum(w.estimated_hours or 0 for w in specs.wbs_elements.values()),
        }

    def _build_wbs_tree(self, element: WBSElement, all_elements: dict[str, WBSElement]) -> dict:
        """Build WBS tree recursively."""
        tree = {
            "id": element.id,
            "name": element.name,
            "description": element.description,
            "level": element.level,
            "estimated_hours": element.estimated_hours,
            "deliverables": element.deliverables,
            "dependencies": element.dependencies,
            "children": {},
        }

        for child_id in element.children:
            if child_id in all_elements:
                child = all_elements[child_id]
                tree["children"][child_id] = self._build_wbs_tree(child, all_elements)

        return tree

    def generate_prd_for_project(self, project_name: str) -> dict:
        """Generate comprehensive PRD for a project."""
        specs = self.project_specs[project_name]

        # Build PRD structure
        prd = {
            "project": project_name,
            "title": f"Product Requirements Document: {project_name}",
            "sections": [],
            "features": [],
            "requirements": [],
            "cross_project_dependencies": list(specs.related_projects),
        }

        # Add PRD sections
        for section in specs.prd_sections:
            prd["sections"].append(
                {
                    "title": section.title,
                    "content": section.content,
                    "features": section.features,
                    "requirements": section.requirements,
                }
            )

        # Add all features
        for feature in specs.features.values():
            prd["features"].append(
                {
                    "id": feature.id,
                    "title": feature.title,
                    "description": feature.description,
                    "priority": feature.priority.value,
                    "acceptance_criteria": feature.acceptance_criteria,
                }
            )

        # Extract requirements from features
        for feature in specs.features.values():
            prd["requirements"].extend(feature.acceptance_criteria)

        return prd

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "analyzed_at": datetime.now().isoformat(),
            "projects_analyzed": list(self.project_specs.keys()),
            "relationships": [
                {
                    "project1": r.project1,
                    "project2": r.project2,
                    "type": r.relationship_type,
                    "strength": r.strength,
                    "details": r.details,
                }
                for r in self.relationships
            ],
            "unified_features": {
                fid: {
                    "id": f.id,
                    "title": f.title,
                    "projects": f.projects,
                    "priority": f.priority,
                }
                for fid, f in self.unified_features.items()
            },
            "unified_work_streams": {
                wsid: {
                    "id": ws.id,
                    "name": ws.name,
                    "projects": ws.projects,
                    "phases": ws.phases,
                    "estimated_hours": ws.estimated_hours,
                }
                for wsid, ws in self.unified_work_streams.items()
            },
            "unified_prds": {
                prid: {
                    "id": prd.id,
                    "title": prd.title,
                    "projects": prd.projects,
                    "sections_count": len(prd.sections),
                    "features_count": len(prd.features),
                }
                for prid, prd in self.unified_prds.items()
            },
        }
