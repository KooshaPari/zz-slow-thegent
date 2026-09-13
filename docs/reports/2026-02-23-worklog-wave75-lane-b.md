# Worklog Wave 75 - Lane B

Date: 2026-02-23
Lane focus: code quality + performance sniffers across Python/TS/Go/Rust with CI integration

Evidence quality rubric:

- A: Official docs/changelog/release metadata + explicit CI guidance
- B: Official source + partial CI guidance or indirect corroboration
- C: Mostly secondary/community evidence

## Item 1: Ruff (Python lint/format + fast rule execution)

- Source: https://github.com/astral-sh/ruff/releases/tag/0.15.2 (published 2026-02-19)
- Core claim: Ruff remains actively maintained in 2026 and is production-ready for CI lint/format gates with very low runtime overhead.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://docs.astral.sh/ruff/integrations/
  - https://github.com/astral-sh/ruff-action

## Item 2: Mypy (Python static typing gate)

- Source: https://pypi.org/project/mypy/ (v1.19.1 uploaded 2025-12-15)
- Core claim: Mypy is still maintained through late 2025 and remains a stable strict-typing gate for CI (especially incremental rollout on legacy codebases).
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://mypy.readthedocs.io/en/stable/existing_code.html
  - https://github.com/python/mypy/blob/master/CHANGELOG.md

## Item 3: Pyright (Python/TS type analyzer in CI)

- Source: https://github.com/microsoft/pyright/releases/tag/1.1.408 (published 2026-01-08)
- Core claim: Pyright remains actively maintained in 2026 and is a strong fast type-check companion/alternative to mypy in CI.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://raw.githubusercontent.com/microsoft/pyright/main/docs/command-line.md
  - https://github.com/microsoft/pyright

## Item 4: golangci-lint (Go multi-linter runner)

- Source: https://github.com/golangci/golangci-lint/releases/tag/v2.10.1 (published 2026-02-17)
- Core claim: golangci-lint is actively maintained and still the most practical single-entrypoint Go quality sniffer for CI pipelines.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://golangci-lint.run/docs/welcome/install/
  - https://github.com/golangci/golangci-lint-action

## Item 5: Semgrep (multi-language SAST + policy sniffer)

- Source: https://github.com/semgrep/semgrep/releases/tag/v1.152.0 (published 2026-02-18)
- Core claim: Semgrep is actively maintained in 2026 and remains a practical cross-language static analysis layer for PR/blocking CI checks.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://semgrep.dev/docs/semgrep-ci/
  - https://github.com/semgrep/semgrep-action

## Item 6: CodeQL (deep code scanning in GitHub-native CI)

- Source: https://github.com/github/codeql-action/releases/tag/codeql-bundle-v2.24.2 (published 2026-02-20)
- Core claim: CodeQL remains actively maintained and is the highest-confidence path for semantic code scanning in GitHub Actions-centric pipelines.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating links:
  - https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning
  - https://github.com/github/codeql-action

## Item 7: Qodana (SonarQube alternative)

- Source: https://github.com/JetBrains/qodana-action/releases/tag/v2025.3.1 (published 2025-12-19)
- Core claim: Qodana is a maintained SonarQube alternative with first-class GitHub Action integration and built-in quality gate/baseline flows.
- Evidence quality: A
- Verdict: Pilot
- Corroborating links:
  - https://www.jetbrains.com/help/qodana/github.html
  - https://www.jetbrains.com/qodana/

## Item 8: StrykerJS (mutation testing for TS/JS)

- Source: https://github.com/stryker-mutator/stryker-js/releases/tag/v9.5.1 (published 2026-02-02)
- Core claim: StrykerJS remains actively maintained in 2026 and is a strong mutation-testing gate for TypeScript test-suite strength.
- Evidence quality: A
- Verdict: Adopt for critical paths
- Corroborating links:
  - https://stryker-mutator.io/docs/stryker-js/introduction/
  - https://github.com/stryker-mutator/stryker-js

## Item 9: cargo-mutants (Rust mutation testing)

- Source: https://github.com/sourcefrog/cargo-mutants/releases/tag/v26.2.0 (published 2026-02-01)
- Core claim: cargo-mutants is actively maintained in 2026 and currently the most practical Rust mutation-testing tool for CI-integrated confidence checks.
- Evidence quality: A
- Verdict: Adopt for Rust services/libraries
- Corroborating links:
  - https://mutants.rs/
  - https://github.com/sourcefrog/cargo-mutants

## Item 10: pytest-rerunfailures (flaky-test containment in Python CI)

- Source: https://pypi.org/project/pytest-rerunfailures/ (v16.1 uploaded 2025-10-10)
- Core claim: pytest-rerunfailures is maintained and useful for flaky-test containment signals in CI, but should be paired with root-cause tracking to avoid masking instability.
- Evidence quality: B
- Verdict: Adopt with guardrails
- Corroborating links:
  - https://github.com/pytest-dev/pytest-rerunfailures
  - https://docs.pytest.org/

## Synthesis (2025-2026 snapshot)

- Best immediate baseline stack: Ruff + (Mypy or Pyright) + golangci-lint + Semgrep + CodeQL.
- Add mutation testing where reliability matters most: StrykerJS for TS/JS, cargo-mutants for Rust.
- Treat flaky reruns as telemetry/containment, not a true fix: enforce retry budgets and open defects on recurring flakes.
- SonarQube alternatives with current momentum in this evidence set: Qodana (single-vendor suite), plus Semgrep/CodeQL as composable scanner stack.
