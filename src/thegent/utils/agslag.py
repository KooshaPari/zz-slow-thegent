import logging
import os
from pathlib import Path
from typing import Any

from thegent.infra.shim_subprocess import run as shim_run
from thegent.skills.deep_research import perform_deep_research

logger = logging.getLogger(__name__)


def search_local_agslag(workspace_root: Path) -> list[dict[str, str]]:
    """Search for agslag related files in the local workspace."""
    results = []

    # Try using 'rg' for fast search
    try:
        # Search for 'agslag' in file contents
        cmd = [
            "rg",
            "-i",
            "agslag",
            str(workspace_root),
            "--files-with-matches",
            "--max-depth",
            "5",
        ]
        process = shim_run(cmd, capture_output=True, text=True, check=False)
        if process.returncode == 0:
            for line in process.stdout.splitlines():
                results.append(
                    {
                        "title": f"Local File: {os.path.basename(line)}",
                        "url": line,
                        "source": "Local Workspace (Content)",
                    }
                )

        # Search for 'agslag' in filenames
        cmd = ["find", str(workspace_root), "-maxdepth", "5", "-iname", "*agslag*"]
        process = shim_run(cmd, capture_output=True, text=True, check=False)
        if process.returncode == 0:
            for line in process.stdout.splitlines():
                if line not in [r["url"] for r in results]:
                    results.append(
                        {
                            "title": f"Local Path: {os.path.basename(line)}",
                            "url": line,
                            "source": "Local Workspace (Path)",
                        }
                    )
    except Exception as e:
        logger.error(f"Error during local agslag search: {e}")

    return results


def research_agslag_project(
    workspace_root: Path,
    query: str = "agslag project",
    subreddits: list[str] | None = None,
) -> dict[str, Any]:
    """Perform comprehensive research on the agslag project."""
    # 1. Local search
    local_results = search_local_agslag(workspace_root)

    # 2. Deep Research Protocol (Online)
    online_results = perform_deep_research(query, subreddits=subreddits)

    # Combine results
    combined_results = {
        "query": query,
        "local_results": local_results,
        "online_results": online_results,
        "summary": f"Found {len(local_results)} local files and {len(online_results['ddg_results']) + len(online_results['reddit_results'])} online results.",
    }

    return combined_results


def update_research_queue(results: dict[str, Any], queue_file: Path):
    """Update the research queue with new agslag findings."""
    if not queue_file.exists():
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, "w") as f:
            f.write("# To-Research Queue\n\n## Agslag Project Research\n\n")

    with open(queue_file) as f:
        content = f.read()

    new_links = []

    # Add local results
    for res in results["local_results"]:
        link = f"- [{res['title']}]({res['url']}) (Source: {res['source']})"
        if link not in content:
            new_links.append(link)

    # Add online results (DDG)
    for res in results["online_results"]["ddg_results"]:
        link = f"- [{res['title']}]({res['url']}) (Source: DDG)"
        if link not in content:
            new_links.append(link)

    # Add online results (Reddit)
    for res in results["online_results"]["reddit_results"]:
        link = f"- [{res['title']}]({res['url']}) (Source: Reddit/r/{res.get('subreddit', 'unknown')})"
        if link not in content:
            new_links.append(link)

    # Add online results (GitHub)
    for res in results["online_results"].get("github_results", []):
        link = f"- [{res['title']}]({res['url']}) (Source: GitHub)"
        if link not in content:
            new_links.append(link)

    if new_links:
        # Insert after the header or at the end
        if "## Agslag Project Research" in content:
            parts = content.split("## Agslag Project Research")
            new_content = parts[0] + "## Agslag Project Research\n\n" + "\n".join(new_links) + "\n" + parts[1]
        else:
            new_content = content + "\n\n## Agslag Project Research\n\n" + "\n".join(new_links) + "\n"

        with open(queue_file, "w") as f:
            f.write(new_content)
        return len(new_links)

    return 0
