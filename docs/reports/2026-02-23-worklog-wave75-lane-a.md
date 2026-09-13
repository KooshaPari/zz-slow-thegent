# Worklog Wave 75 - Lane A Research (2026-02-23)

Scope: `pytest/test performance optimization` and `FR/user-story traceability + DAG strategies` for thegent.

## 1) Baseline slow tests with built-in duration profiling

- Source: pytest docs - Usage (`--durations`, `--durations-min`) https://pytest.org/en/6.2.x/usage.html
- Core claim: `pytest --durations=N --durations-min=S` gives an immediate ranked list of slow tests, which is the fastest first step before optimization.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://manpages.debian.org/experimental/python3-pytest/pytest.1.en.html, https://pypi.org/project/pytest-durations/

## 2) Use xdist parallelism with explicit distribution mode selection

- Source: pytest-xdist docs - Running tests across multiple CPUs https://pytest-xdist.readthedocs.io/en/stable/distribution.html
- Core claim: `-n auto` and `--dist` modes (`load`, `loadscope`, `loadfile`, `worksteal`) materially change runtime and fixture reuse behavior; selecting mode by suite shape improves throughput.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://pytest-xdist.readthedocs.io/en/stable/, https://pytest-xdist.readthedocs.io/en/stable/how-it-works.html

## 3) Re-run only what failed to shorten developer loops

- Source: pytest docs - Cache provider (`--lf`, `--ff`) https://docs.pytest.org/en/6.2.x/cache.html
- Core claim: Last-failed and failed-first flows reduce re-run scope and time during iterative fixes while preserving full-suite fallback.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://docs.pytest.org/en/stable/reference/customize.html, https://docs.pytest.org/en/stable/reference.html

## 4) Cut collection overhead via explicit discovery boundaries

- Source: pytest docs - Collection controls (`--ignore`, `--ignore-glob`, discovery tuning) https://docs.pytest.org/en/stable/example/pythoncollection.html
- Core claim: Tight collection boundaries reduce non-test traversal and speed startup/collection in large repos.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://docs.pytest.org/en/stable/reference/customize.html, https://docs.pytest.org/en/7.1.x/reference/reference.html

## 5) Keep fast-path CI deterministic with marker-driven slices

- Source: pytest docs - Working with custom markers (`-m`, marker registration) https://docs.pytest.org/en/stable/example/markers.html
- Core claim: Registered markers plus marker expressions allow deterministic fast/slow/integration test slices for CI latency control.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://docs.pytest.org/en/stable/reference.html, https://docs.pytest.org/en/7.1.x/reference/reference.html

## 6) Encode FR IDs directly in tests and enforce marker strictness

- Source: pytest docs - `--strict-markers` + marker whitelist behavior https://docs.pytest.org/en/stable/reference.html
- Core claim: A required custom marker like `@pytest.mark.requirement("FR-...")` plus `--strict-markers` prevents unregistered/typo markers and stabilizes traceability metadata.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://docs.pytest.org/en/stable/example/markers.html, https://docs.pytest.org/en/7.1.x/deprecations.html

## 7) Emit machine-readable requirement links in JUnit XML

- Source: pytest docs - `record_property` / `record_testsuite_property` fixtures https://docs.pytest.org/en/stable/reference.html
- Core claim: Test-level and suite-level properties can carry FR/user-story IDs into JUnit XML for downstream tracker/report joins.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://docs.pytest.org/en/7.1.x/reference/fixtures.html, https://docs.pytest.org/en/stable/_modules/_pytest/junitxml.html

## 8) Use BDD tags as user-story selectors and map to pytest markers

- Source: pytest-bdd docs (tags -> pytest markers, selector compatibility) https://pytest-bdd.readthedocs.io/en/5.0.0/
- Core claim: Scenario tags can be used as marker-compatible selectors, enabling user-story-level execution/filtering and rollout slicing.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Watch
- Corroborating links: https://docs.pytest.org/en/stable/example/markers.html, https://github.com/cucumber/pytest-bdd-ng

## 9) Model workstream dependencies as an explicit DAG and topologically schedule

- Source: Python stdlib docs - `graphlib.TopologicalSorter` https://docs.python.org/3/library/graphlib.html
- Core claim: `TopologicalSorter` provides native DAG ordering and ready-node scheduling, suitable for FR/user-story task dependency execution in lanes.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.topological_sort.html, https://airflow.apache.org/docs/apache-airflow/3.0.0/best-practices.html

## 10) Enforce bidirectional traceability policy (FR <-> design/test/task)

- Source: NASA Systems Engineering Handbook Appendix (traceability + verification matrix guidance) https://www.nasa.gov/reference/system-engineering-handbook-appendix/
- Core claim: Requirements should be uniquely identified and bidirectionally traceable to verification artifacts; this aligns directly with FR-to-test/task governance for thegent.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://csrc.nist.gov/glossary/term/traceability_matrix, https://csrc.nist.gov/pubs/sp/800/160/v1/r1/final
