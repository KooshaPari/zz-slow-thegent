import re
from pathlib import Path


def extract_links_from_md(file_path):
    links = []
    try:
        with open(file_path) as f:
            content = f.read()
            # Find markdown links [title](url)
            matches = re.findall(r"\[([^\]]+)\]\((https?://[^\)]+)\)", content)
            for title, url in matches:
                links.append({"title": title, "url": url, "source": f"MD: {Path(file_path).name}"})

            # Find bare URLs
            bare_urls = re.findall(r"(?<!\()https?://[a-zA-Z0-9./_-]+", content)
            for url in bare_urls:
                if not any(l["url"] == url for l in links):
                    links.append({"title": "Direct Link", "url": url, "source": f"MD: {Path(file_path).name}"})
    except Exception:
        pass
    return links


research_dirs = [
    "/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/research",
    "/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/plans",
    "/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/docset",
    "/Users/kooshapari/temp-PRODVERCEL/485/kush/task2",
    "/Users/kooshapari/temp-PRODVERCEL/485/kush/plangent/docs/planning",
]

all_md_links = []
for d in research_dirs:
    path = Path(d)
    if path.exists():
        for f in path.glob("*.md"):
            all_md_links.extend(extract_links_from_md(f))

# Deduplicate
seen_urls = set()
unique_md_links = []
for l in all_md_links:
    if l["url"] not in seen_urls:
        unique_md_links.append(l)
        seen_urls.add(l["url"])


# Append to research queue
with open("docs/research/to-research-queue.md", "a") as out:
    out.write(f"\n\n## Agent Aggregation (Droid, Codex, Cursor, Claude - {len(unique_md_links)} links discovered)\n\n")

    # Categorize by source file
    sources = {}
    for l in unique_md_links:
        src = l["source"]
        if src not in sources:
            sources[src] = []
        sources[src].append(l)

    for src in sorted(sources.keys()):
        items = sources[src]
        out.write(f"### {src}\n")
        out.writelines(f"- [{item['title']}]({item['url']})\n" for item in items)
        out.write("\n")
