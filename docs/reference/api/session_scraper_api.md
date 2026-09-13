# session_scraper API Reference

> **Source**: `src/thegent/orchestration/session_scraper.py`

## SessionScraper

MTSP-18: Session Scraper to extract user prompts and context.

Focuses on terminal panes (tmux) and local history files.

### Methods

#### SessionScraper.**init**

```python
__init__(self: Any, project_root: Path)
```

---

#### SessionScraper.collect_all_recent_prompts

```python
collect_all_recent_prompts(self: Any)
```

Unified collection from all available scrapers.

---

#### SessionScraper.scrape_claude_history

```python
scrape_claude_history(self: Any)
```

Scrape prompts from local Claude history files if they exist.

---

#### SessionScraper.scrape_tmux_prompts

```python
scrape_tmux_prompts(self: Any)
```

Scrape likely user prompts from active Claude Code tmux panes.

---

---

## collect_all_recent_prompts

```python
collect_all_recent_prompts(self: Any)
```

Unified collection from all available scrapers.

---

## scrape_claude_history

```python
scrape_claude_history(self: Any)
```

Scrape prompts from local Claude history files if they exist.

---

## scrape_tmux_prompts

```python
scrape_tmux_prompts(self: Any)
```

Scrape likely user prompts from active Claude Code tmux panes.

---
