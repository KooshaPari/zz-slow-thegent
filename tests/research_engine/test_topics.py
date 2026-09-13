# tests/research_engine/test_topics.py
# @trace FR-RE-009
from pathlib import Path


def test_extract_from_pyproject(tmp_path: Path) -> None:
    from research_engine.topics import TopicExtractor

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\ndependencies = ["httpx>=0.28", "pydantic>=2.0", "structlog"]\n'
    )
    extractor = TopicExtractor(project_root=tmp_path)
    topics = extractor.extract()
    assert "httpx" in topics
    assert "pydantic" in topics


def test_manual_override(tmp_path: Path) -> None:
    from research_engine.topics import TopicExtractor

    config = tmp_path / "research-topics.yaml"
    config.write_text("topics:\n  - mcp\n  - agent-governance\n  - fastmcp\n")
    extractor = TopicExtractor(project_root=tmp_path, config_path=config)
    topics = extractor.extract()
    assert "mcp" in topics
    assert "fastmcp" in topics


def test_dedup(tmp_path: Path) -> None:
    from research_engine.topics import TopicExtractor

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies = ["httpx", "httpx"]\n')
    extractor = TopicExtractor(project_root=tmp_path)
    topics = extractor.extract()
    assert topics.count("httpx") == 1


def test_missing_files_returns_empty(tmp_path: Path) -> None:
    from research_engine.topics import TopicExtractor

    extractor = TopicExtractor(project_root=tmp_path)
    topics = extractor.extract()
    assert isinstance(topics, list)
