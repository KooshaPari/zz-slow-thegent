# Pytest Optimization and Atoms Research (PYW1-002)

## Do this before pushing

Run from repo root:

```bash
mkdir -p docs/reports/artifacts/2026-02-22-pyw1-002
```

### Lane A — Pytest optimization

```bash
python -m pytest --collect-only thegent/tests/test_unit_session_scraper.py thegent/tests/test_unit_scrapers.py -q | tee docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-collect-only.txt
python -m pytest -m "not slow and not integration and not e2e and not load" thegent/tests/test_unit_session_scraper.py thegent/tests/test_unit_scrapers.py -q | tee docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-fast-lane.txt
python -m pytest thegent/tests/test_unit_session_scraper_batch5.py thegent/tests/test_unit_session_scraper_batch6.py -q | tee docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-batch-regression.txt
```

### Lane B — Atoms/Ante scraper research guardrails

```bash
rg -n "scrape_ante|SCRAPER_REGISTRY|session.scraper|collect_all_recent_prompts" thegent/src/thegent/models/scrapers.py thegent/src/thegent/orchestration/state/session_scraper.py | tee docs/reports/artifacts/2026-02-22-pyw1-002/lane-b-code-evidence.txt
python -m pytest thegent/tests/test_unit_scrapers.py -k "Ante or scrape_ante" -q | tee docs/reports/artifacts/2026-02-22-pyw1-002/lane-b-ante-tests.txt
```

### Required artifact outputs

- `docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-collect-only.txt`
- `docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-fast-lane.txt`
- `docs/reports/artifacts/2026-02-22-pyw1-002/lane-a-batch-regression.txt`
- `docs/reports/artifacts/2026-02-22-pyw1-002/lane-b-code-evidence.txt`
- `docs/reports/artifacts/2026-02-22-pyw1-002/lane-b-ante-tests.txt`
