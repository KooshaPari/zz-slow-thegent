### [WL-8080]

**Title:** Separate topic extraction failure reporting from scheduler dispatch in research CLI
**Source:** [thegent/src/research_engine/cli.py:33]
**Acceptance checklist:**

- [ ] Split command execution path so topic extraction failures and scheduler execution failures are reported separately.
- [ ] Preserve existing CLI behavior for successful digest and crawl runs.
- [ ] Add tests for topic extraction failures, scheduler failures, and successful CLI invocation.
      **Notes:** Clearer stage boundaries reduce debugging ambiguity in lane automation.

### [WL-8081]

**Title:** Distinguish scheduler startup from job execution failures in tiered run flow
**Source:** [thegent/src/research_engine/scheduler.py:74]
**Acceptance checklist:**

- [ ] Emit dedicated diagnostics for scheduler start/register failures versus crawler run failures.
- [ ] Preserve existing job interval configuration and tier behavior.
- [ ] Add unit tests for failed job registration, runner exceptions, and successful cycle execution.
      **Notes:** Separating lifecycle stages makes scheduler incidents actionable.

### [WL-8082]

**Title:** Separate SQLite connect/DDL initialization failures during research store startup
**Source:** [thegent/src/research_engine/store.py:28]
**Acceptance checklist:**

- [ ] Report schema initialization and connection errors with distinct context in store construction.
- [ ] Preserve existing database path defaults and read/write semantics for successful initialization.
- [ ] Add tests for invalid DB path creation, schema execution errors, and normal initialization.
      **Notes:** Explicit startup failure classes reduce recovery time for broken environments.

### [WL-8083]

**Title:** Split repository sync path resolution from persistence writes in mirror command
**Source:** [thegent/src/research_engine/store.py:126]
**Acceptance checklist:**

- [ ] Return explicit outcomes for path validation errors versus upsert/persistence errors during mirror.
- [ ] Keep existing mirror filtering and counts unchanged on successful execution.
- [ ] Add tests for bad target path, permission failures, and successful mirror completion.
      **Notes:** This isolates bad input from persistence regressions in sync workflows.

### [WL-8084]

**Title:** Separate topic derivation from deduplication when reading pyproject/manual topic sources
**Source:** [thegent/src/research_engine/topics.py:35]
**Acceptance checklist:**

- [ ] Split extraction errors from deduplication/path-read failures with explicit branch errors.
- [ ] Preserve final topic ordering and precedence behavior across existing sources.
- [ ] Add tests for malformed pyproject, bad YAML config, and successful topic extraction.
      **Notes:** Distinct branches make topic-source failures transparent.

### [WL-8085]

**Title:** Isolate crawler interface contract failures from concrete fetch logic
**Source:** [thegent/src/research_engine/crawlers/base.py:28]
**Acceptance checklist:**

- [ ] Separate abstract contract validation and concrete fetch error reporting.
- [ ] Preserve compatibility of `BaseCrawler.fetch` interface and existing concrete implementations.
- [ ] Add tests for contract violations and successful implementation compliance.
      **Notes:** Improves consistency in crawler onboarding and future extension.

### [WL-8086]

**Title:** Split crawler registration faults from retrieval filtering in registry lookups
**Source:** [thegent/src/research_engine/crawlers/registry.py:31]
**Acceptance checklist:**

- [ ] Distinguish bad registration state from tier-filter query failures in registry APIs.
- [ ] Preserve current tier matching behavior for all valid registrations.
- [ ] Add tests for empty tier queries, invalid registry state, and successful crawler filtering.
      **Notes:** Helps narrow scheduler failures that originate in registry lifecycle.

### [WL-8087]

**Title:** Differentiate Reddit query construction from API iteration failures in Reddit crawler
**Source:** [thegent/src/research_engine/crawlers/reddit.py:49]
**Acceptance checklist:**

- [ ] Split query-building/normalization errors from Reddit API iteration exceptions.
- [ ] Preserve fetched item mapping and tag extraction behavior on successful calls.
- [ ] Add tests for empty topic input, mocked API iteration errors, and successful fetch results.
      **Notes:** Gives operators a deterministic fix path for crawl instability.

### [WL-8088]

**Title:** Separate GitHub request setup from response parsing in repository crawler
**Source:** [thegent/src/research_engine/crawlers/github.py:44]
**Acceptance checklist:**

- [ ] Emit separate diagnostics for request setup/transport failures versus parse-time response schema issues.
- [ ] Preserve item scoring and URL/title mapping for successful responses.
- [ ] Add tests for HTTP transport failures, malformed responses, and successful fetch transforms.
      **Notes:** This keeps API failures and schema drift from masking each other.

### [WL-8089]

**Title:** Split arXiv query construction from result materialization and storage mapping
**Source:** [thegent/src/research_engine/crawlers/arxiv_crawler.py:34]
**Acceptance checklist:**

- [ ] Keep explicit branches for query-generation failures and result-iteration mapping failures.
- [ ] Preserve existing relevance scoring and item schema fields for successful imports.
- [ ] Add tests for malformed topic query input, iterator failures, and successful arXiv item materialization.
      **Notes:** Improves maintainability when arXiv result shapes shift.
