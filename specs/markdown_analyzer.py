"""
Markdown Analysis System

Analyzes markdown files to extract:
- Specifications
- Work Breakdown Structures (WBS)
- Product Requirements (PRD)
- Features
- Tasks
- Dependencies
- Cross-project relationships
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content found in markdown."""

    SPECIFICATION = "specification"
    WBS = "wbs"
    PRD = "prd"
    FEATURE = "feature"
    TASK = "task"
    PLAN = "plan"
    ARCHITECTURE = "architecture"
    API_DOC = "api_doc"
    RESEARCH = "research"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractedFeature:
    """Extracted feature from markdown."""

    id: str
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    status: str = "pending"
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimated_effort: str | None = None
    tags: set[str] = field(default_factory=set)
    source_file: Path = None
    line_number: int | None = None


@dataclass
class ExtractedTask:
    """Extracted task from markdown."""

    id: str
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    estimated_hours: float | None = None
    assignee: str | None = None
    tags: set[str] = field(default_factory=set)
    source_file: Path = None
    line_number: int | None = None


@dataclass
class WBSElement:
    """Work Breakdown Structure element."""

    id: str
    name: str
    description: str
    level: int  # 1 = top level, 2 = sub-level, etc.
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    estimated_hours: float | None = None
    dependencies: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    source_file: Path = None


@dataclass
class PRDSection:
    """PRD section."""

    title: str
    content: str
    subsections: list["PRDSection"] = field(default_factory=list)
    features: list[str] = field(default_factory=list)  # Feature IDs
    requirements: list[str] = field(default_factory=list)


@dataclass
class ProjectSpecs:
    """Complete project specifications extracted from markdown."""

    project_path: Path
    project_name: str
    analyzed_files: list[Path] = field(default_factory=list)

    # Extracted content
    features: dict[str, ExtractedFeature] = field(default_factory=dict)
    tasks: dict[str, ExtractedTask] = field(default_factory=dict)
    wbs_elements: dict[str, WBSElement] = field(default_factory=dict)
    prd_sections: list[PRDSection] = field(default_factory=list)

    # Metadata
    content_types: dict[ContentType, int] = field(default_factory=dict)
    keywords: set[str] = field(default_factory=set)
    technologies: set[str] = field(default_factory=set)
    dependencies: set[str] = field(default_factory=dict)  # Other projects

    # Cross-references
    related_projects: set[str] = field(default_factory=set)
    shared_features: dict[str, list[str]] = field(default_factory=dict)  # feature_id -> [project_names]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "project_path": str(self.project_path),
            "project_name": self.project_name,
            "analyzed_files": [str(f) for f in self.analyzed_files],
            "features": {
                fid: {
                    "id": f.id,
                    "title": f.title,
                    "description": f.description,
                    "priority": f.priority.value,
                    "status": f.status,
                    "acceptance_criteria": f.acceptance_criteria,
                    "dependencies": f.dependencies,
                    "tags": list(f.tags),
                    "source_file": str(f.source_file) if f.source_file else None,
                }
                for fid, f in self.features.items()
            },
            "tasks": {
                tid: {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority.value,
                    "status": t.status,
                    "dependencies": t.dependencies,
                    "estimated_hours": t.estimated_hours,
                    "tags": list(t.tags),
                    "source_file": str(t.source_file) if t.source_file else None,
                }
                for tid, t in self.tasks.items()
            },
            "wbs_elements": {
                wid: {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "level": w.level,
                    "parent_id": w.parent_id,
                    "children": w.children,
                    "estimated_hours": w.estimated_hours,
                    "dependencies": w.dependencies,
                    "deliverables": w.deliverables,
                }
                for wid, w in self.wbs_elements.items()
            },
            "content_types": {ct.value: count for ct, count in self.content_types.items()},
            "keywords": list(self.keywords),
            "technologies": list(self.technologies),
            "related_projects": list(self.related_projects),
        }


class MarkdownAnalyzer:
    """Analyzes markdown files to extract specs, WBS, and PRD content."""

    def __init__(self, project_path: Path) -> None:
        self.project_path = Path(project_path).resolve()
        self.specs = ProjectSpecs(
            project_path=self.project_path,
            project_name=self.project_path.name,
        )
        self._feature_counter = 0
        self._task_counter = 0
        self._wbs_counter = 0

    def analyze_all_markdown(self, max_files: int | None = None) -> ProjectSpecs:
        """Analyze all markdown files in project."""
        # Prioritize certain files
        priority_patterns = [
            "README.md",
            "SPEC.md",
            "PRD.md",
            "WBS.md",
            "specs/",
            "docs/",
            "requirements/",
        ]

        all_md_files = list(self.project_path.rglob("*.md"))

        # Sort: priority files first
        priority_files = []
        other_files = []

        for md_file in all_md_files:
            file_str = str(md_file)
            if any(pattern in file_str for pattern in priority_patterns):
                priority_files.append(md_file)
            else:
                other_files.append(md_file)

        md_files = priority_files + other_files

        if max_files:
            md_files = md_files[:max_files]

        logger.info(
            f"Analyzing {len(md_files)} markdown files in {self.project_path} (out of {len(all_md_files)} total)"
        )

        for i, md_file in enumerate(md_files):
            if i % 50 == 0 and i > 0:
                logger.info(f"  Progress: {i}/{len(md_files)} files analyzed")
            try:
                self._analyze_file(md_file)
                self.specs.analyzed_files.append(md_file)
            except Exception as e:
                logger.warning(f"Error analyzing {md_file}: {e}")

        # Post-process: build relationships
        self._build_relationships()

        return self.specs

    def _analyze_file(self, file_path: Path):
        """Analyze a single markdown file."""
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Detect content type
        content_type = self._detect_content_type(file_path, content)
        self.specs.content_types[content_type] = self.specs.content_types.get(content_type, 0) + 1

        # Extract based on content type
        if content_type == ContentType.SPECIFICATION:
            self._extract_specification(content, file_path)
        elif content_type == ContentType.WBS:
            self._extract_wbs(content, file_path)
        elif content_type == ContentType.PRD:
            self._extract_prd(content, file_path)
        elif content_type == ContentType.FEATURE:
            self._extract_features(content, file_path)
        elif content_type == ContentType.TASK:
            self._extract_tasks(content, file_path)
        elif content_type == ContentType.PLAN:
            self._extract_plan(content, file_path)
        elif content_type == ContentType.ARCHITECTURE:
            self._extract_architecture(content, file_path)
        elif content_type == ContentType.RESEARCH:
            self._extract_research(content, file_path)

        # Always extract keywords and technologies
        self._extract_keywords(content)
        self._extract_technologies(content)
        self._extract_project_references(content)

    def _detect_content_type(self, file_path: Path, content: str) -> ContentType:
        """Detect content type from file path and content."""
        path_lower = str(file_path).lower()
        content.lower()

        # Check file name patterns
        if any(term in path_lower for term in ["spec", "specification"]):
            return ContentType.SPECIFICATION
        if any(term in path_lower for term in ["wbs", "work", "breakdown"]):
            return ContentType.WBS
        if any(term in path_lower for term in ["prd", "requirements", "requirement"]):
            return ContentType.PRD
        if any(term in path_lower for term in ["feature", "features"]):
            return ContentType.FEATURE
        if any(term in path_lower for term in ["task", "todo", "checklist"]):
            return ContentType.TASK
        if any(term in path_lower for term in ["plan", "roadmap", "strategy"]):
            return ContentType.PLAN
        if any(term in path_lower for term in ["arch", "architecture", "design"]):
            return ContentType.ARCHITECTURE
        if any(term in path_lower for term in ["research", "study", "analysis"]):
            return ContentType.RESEARCH

        # Check content patterns
        if re.search(r"##\s*(?:Work\s+)?Breakdown\s+Structure|##\s*WBS", content, re.IGNORECASE):
            return ContentType.WBS
        if re.search(r"##\s*Product\s+Requirements|##\s*PRD|##\s*Requirements", content, re.IGNORECASE):
            return ContentType.PRD
        if re.search(r"##\s*Features?|##\s*Feature\s+List", content, re.IGNORECASE):
            return ContentType.FEATURE
        if re.search(r"##\s*Tasks?|##\s*TODO|##\s*Checklist", content, re.IGNORECASE):
            return ContentType.TASK
        if re.search(r"##\s*Plan|##\s*Roadmap|##\s*Strategy", content, re.IGNORECASE):
            return ContentType.PLAN

        return ContentType.UNKNOWN

    def _extract_specification(self, content: str, file_path: Path):
        """Extract specification content."""
        # Look for specification sections
        sections = re.split(r"^##+\s+", content, flags=re.MULTILINE)
        for section in sections[1:]:  # Skip first (before first heading)
            lines = section.split("\n")
            title = lines[0].strip()

            # Extract features from spec
            if any(term in title.lower() for term in ["feature", "requirement", "spec"]):
                self._extract_features_from_section(section, file_path)

    def _extract_wbs(self, content: str, file_path: Path):
        """Extract Work Breakdown Structure."""
        # Look for WBS patterns
        wbs_patterns = [
            r"^(\d+\.?\d*\.?\d*)\s+(.+?)$",  # 1.1.1 Task name
            r"^[-*]\s*(\d+\.?\d*\.?\d*)\s+(.+?)$",  # - 1.1.1 Task name
            r"^##+\s*(\d+\.?\d*\.?\d*)\s+(.+?)$",  # ## 1.1.1 Task name
        ]

        for pattern in wbs_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                wbs_id = match.group(1)
                name = match.group(2).strip()

                # Determine level from ID
                level = len(wbs_id.split("."))

                # Extract description (next lines until next WBS item or heading)
                start_pos = match.end()
                next_match = re.search(pattern, content[start_pos:], re.MULTILINE)
                if next_match:
                    description = content[start_pos : start_pos + next_match.start()].strip()
                else:
                    description = content[start_pos : start_pos + 500].strip()

                element = WBSElement(
                    id=f"{self.specs.project_name}-wbs-{wbs_id}",
                    name=name,
                    description=description,
                    level=level,
                    source_file=file_path,
                )

                # Try to find parent
                if level > 1:
                    parent_id_parts = wbs_id.split(".")[:-1]
                    parent_id = ".".join(parent_id_parts)
                    element.parent_id = f"{self.specs.project_name}-wbs-{parent_id}"

                self.specs.wbs_elements[element.id] = element
                self._wbs_counter += 1

    def _extract_prd(self, content: str, file_path: Path):
        """Extract Product Requirements Document content."""
        # Split by major headings
        sections = re.split(r"^(##\s+.+?)$", content, flags=re.MULTILINE)

        current_section = None
        for i, section in enumerate(sections):
            if i % 2 == 0:  # Content
                if current_section:
                    current_section.content = section.strip()
            else:  # Heading
                title = section.replace("##", "").strip()
                current_section = PRDSection(title=title, content="")
                self.specs.prd_sections.append(current_section)

    def _extract_features(self, content: str, file_path: Path):
        """Extract features from content."""
        self._extract_features_from_section(content, file_path)

    def _extract_features_from_section(self, section: str, file_path: Path):
        """Extract features from a section."""
        # Look for feature patterns
        feature_patterns = [
            r"^[-*]\s*\*\*([^*]+)\*\*[:\-]?\s*(.+?)(?=^[-*]|^##|$)",
            r"^###\s+(.+?)$",
            r"^\d+\.\s+\*\*([^*]+)\*\*[:\-]?\s*(.+?)(?=^\d+\.|^##|$)",
        ]

        for pattern in feature_patterns:
            matches = re.finditer(pattern, section, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.groups()) >= 2:
                    title = match.group(1).strip()
                    description = match.group(2).strip()
                else:
                    title = match.group(1).strip()
                    description = ""

                # Extract priority
                priority = Priority.MEDIUM
                if re.search(r"\b(critical|high|important|priority)\b", title + description, re.IGNORECASE):
                    priority = Priority.HIGH
                if re.search(r"\b(critical|urgent|blocking)\b", title + description, re.IGNORECASE):
                    priority = Priority.CRITICAL

                # Extract acceptance criteria
                acceptance_criteria = []
                criteria_match = re.search(
                    r"Acceptance\s+Criteria[:\-]?\s*(.+?)(?=^##|$)", section, re.IGNORECASE | re.DOTALL
                )
                if criteria_match:
                    criteria_text = criteria_match.group(1)
                    criteria_items = re.findall(r"[-*]\s*(.+?)(?=^[-*]|$)", criteria_text, re.MULTILINE)
                    acceptance_criteria = [item.strip() for item in criteria_items]

                feature = ExtractedFeature(
                    id=f"{self.specs.project_name}-feat-{self._feature_counter}",
                    title=title,
                    description=description,
                    priority=priority,
                    acceptance_criteria=acceptance_criteria,
                    source_file=file_path,
                    tags=self._extract_tags(title + " " + description),
                )

                self.specs.features[feature.id] = feature
                self._feature_counter += 1

    def _extract_tasks(self, content: str, file_path: Path):
        """Extract tasks from content."""
        # Look for task patterns
        task_patterns = [
            r"^[-*]\s*\[([ xX])\]\s*(.+?)$",  # - [ ] Task
            r"^[-*]\s*(.+?)$",  # - Task
            r"^\d+\.\s+(.+?)$",  # 1. Task
        ]

        for pattern in task_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                if len(match.groups()) == 2:
                    checked = match.group(1).strip().lower() == "x"
                    title = match.group(2).strip()
                    status = "completed" if checked else "pending"
                else:
                    title = match.group(1).strip()
                    status = "pending"

                # Extract priority
                priority = Priority.MEDIUM
                if re.search(r"\b(critical|high|important)\b", title, re.IGNORECASE):
                    priority = Priority.HIGH

                # Extract estimated hours
                hours_match = re.search(r"(\d+(?:\.\d+)?)\s*h(?:ours?)?", title, re.IGNORECASE)
                estimated_hours = float(hours_match.group(1)) if hours_match else None

                task = ExtractedTask(
                    id=f"{self.specs.project_name}-task-{self._task_counter}",
                    title=title,
                    description="",
                    priority=priority,
                    status=status,
                    estimated_hours=estimated_hours,
                    source_file=file_path,
                    tags=self._extract_tags(title),
                )

                self.specs.tasks[task.id] = task
                self._task_counter += 1

    def _extract_plan(self, content: str, file_path: Path):
        """Extract plan content (combines WBS, features, tasks)."""
        self._extract_wbs(content, file_path)
        self._extract_features(content, file_path)
        self._extract_tasks(content, file_path)

    def _extract_architecture(self, content: str, file_path: Path):
        """Extract architecture content."""
        # Extract components, systems, etc.
        self._extract_features(content, file_path)

    def _extract_research(self, content: str, file_path: Path):
        """Extract research content."""
        # Extract findings, recommendations, etc.
        self._extract_features(content, file_path)
        self._extract_tasks(content, file_path)

    def _extract_keywords(self, content: str):
        """Extract keywords from content."""
        # Extract important terms
        keywords = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content)
        self.specs.keywords.update(k.lower() for k in keywords if len(k) > 3)

    def _extract_technologies(self, content: str):
        """Extract technology mentions."""
        tech_patterns = [
            r"\b(Python|JavaScript|TypeScript|Rust|Go|Java|C\+\+|React|Vue|Angular|Django|Flask|FastAPI|Node\.js)\b",
            r"\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b",
            r"\b(Docker|Kubernetes|AWS|Azure|GCP)\b",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            self.specs.technologies.update(m.lower() for m in matches)

    def _extract_project_references(self, content: str):
        """Extract references to other projects."""
        # Look for project names in paths or mentions
        project_refs = re.findall(r"(?:temp-PRODVERCEL|projects?)[/\s]+([\w-]+)", content, re.IGNORECASE)
        self.specs.related_projects.update(project_refs)

    def _extract_tags(self, text: str) -> set[str]:
        """Extract tags from text."""
        tags = set()

        # Common tag patterns
        tag_patterns = [
            r"#(\w+)",  # #tag
            r"tag[s]?:\s*([\w, ]+)",  # tags: tag1, tag2
        ]

        for pattern in tag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                tags.update(t.strip().lower() for t in match.split(","))

        return tags

    def _build_relationships(self):
        """Build relationships between extracted elements."""
        # Link WBS elements
        for element in self.specs.wbs_elements.values():
            if element.parent_id and element.parent_id in self.specs.wbs_elements:
                parent = self.specs.wbs_elements[element.parent_id]
                parent.children.append(element.id)

        # Link features to tasks
        for task in self.specs.tasks.values():
            # Try to match tasks to features by keywords
            task_keywords = set(task.title.lower().split())
            for feature in self.specs.features.values():
                feature_keywords = set(feature.title.lower().split())
                if task_keywords & feature_keywords:  # Intersection
                    if feature.id not in task.tags:
                        task.tags.add(f"feature:{feature.id}")
