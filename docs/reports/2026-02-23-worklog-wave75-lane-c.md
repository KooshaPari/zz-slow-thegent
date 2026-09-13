# Worklog Wave 75 - Lane C (2026-02-23)

## Scope

10 practical, automatable controls for **generated-code anti-pattern detection** and **AI code governance** across linting, architecture checks, and secure-by-default gates.

## Recommended Detector + Policy Stack (10 Items)

| #   | Detector / Gate                                                                       | What It Catches                                                                                                                        | Automatable Policy (Example)                                                                                                                                                            | CI/CD Enforcement                                                                   |
| --- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | **Semgrep Code policies**                                                             | Generated-code anti-patterns (dangerous APIs, insecure defaults, missing validation, weak crypto usage, etc.)                          | Start rules in `Monitor`, promote high-signal rules to blocking mode; maintain org ruleset for "AI-generated code must not use `eval`, unsafe deserialization, broad exception swallow" | `semgrep ci` required status check; block merge on `ERROR` findings                 |
| 2   | **ast-grep custom rules (`sgconfig.yml`)**                                            | Structural "AI slop" patterns in AST form (placeholder stubs, suspicious control flow, banned API calls, retry/fallback anti-patterns) | Add repo-local YAML rules for anti-pattern signatures and set severity `error`; include policy metadata URL and remediation text per rule                                               | Run `ast-grep scan` in PR checks; fail on any high-confidence match                 |
| 3   | **CodeQL + custom query packs/model packs**                                           | Dataflow/path vulnerabilities and project-specific insecure idioms that common linters miss                                            | Maintain an org query pack for recurrent generated-code issues (injection sinks, taint flow, auth bypass patterns) and run with standard suites                                         | Code scanning must pass; code scanning merge protection enabled                     |
| 4   | **GitHub rulesets + required checks + merge protection**                              | Policy bypass risk (merging without scans, stale branch, unsigned commits/required reviewers not enforced)                             | Ruleset requires: code scanning results, security/lint checks, review approvals, and up-to-date branch                                                                                  | Branch/ruleset enforcement blocks merge until required checks are green             |
| 5   | **SonarQube Quality Gate (AI-qualified gate)**                                        | New-code regressions in reliability/security/maintainability, coverage and duplication drift in generated code                         | Use "Sonar way for AI Code" (or stricter custom gate): no blocker issues, minimum coverage, max duplication, reviewed hotspots                                                          | PR decoration + pipeline fail on quality gate failure                               |
| 6   | **Architecture boundary checks (dependency-cruiser / import-linter / Nx boundaries)** | Architectural erosion from generated code (layer violations, forbidden imports, cyclic deps, cross-domain leakage)                     | Define forbidden dependency rules/contracts: e.g., `ui -> data-access` only via API layer; disallow `domain -> infra` imports                                                           | Run architecture checks in PR; fail if boundaries or cycle rules break              |
| 7   | **OPA + Conftest policy-as-code**                                                     | Governance violations in repo config, CI workflows, IaC, and deployment manifests                                                      | Rego policies for secure defaults: pinned action SHAs, minimal token permissions, mandatory SAST/SCA jobs, no privileged containers                                                     | `conftest test` on PR for `.github/workflows`, IaC, and policy-controlled manifests |
| 8   | **Secret leakage prevention (GitHub push protection + Gitleaks/Trivy)**               | Hardcoded secrets and accidental credential commits common in generated code                                                           | Enforce push protection org-wide; run secondary secret scan in CI for defense-in-depth and historical drift                                                                             | Push blocked pre-merge; CI fails on detected secrets                                |
| 9   | **Dependency vulnerability gates (OSV-Scanner + language-native audit)**              | Newly introduced vulnerable dependencies from generated scaffolds/snippets                                                             | Fail PR when new vulnerabilities are introduced; optionally gate by severity (`HIGH`/`CRITICAL`) with documented exception SLA                                                          | OSV PR-diff scan required; scheduled full scans publish to code scanning            |
| 10  | **OpenSSF Scorecard governance baseline**                                             | Weak repo posture (branch protection gaps, unpinned actions, token-permission issues, missing security process)                        | Set minimum score threshold and track critical checks (`Branch-Protection`, `Token-Permissions`, `Pinned-Dependencies`)                                                                 | Run `ossf/scorecard-action`; fail if threshold/checks regress                       |

## Implementation Sequence (Pragmatic Rollout)

1. **Week 1:** Enable non-blocking visibility (`Semgrep Monitor`, `CodeQL`, `OSV`, `Scorecard`, Sonar baseline).
2. **Week 2:** Add architecture contracts and Conftest policies; tune false positives.
3. **Week 3:** Flip high-confidence controls to blocking (rulesets required checks + merge protection).
4. **Week 4+:** Ratchet thresholds (coverage, duplication, vulnerability severity, scorecard minimum).

## Source Links

1. Semgrep policies: https://semgrep.dev/docs/semgrep-code/policies
2. Semgrep Supply Chain: https://semgrep.dev/docs/semgrep-supply-chain/getting-started
3. ast-grep config reference: https://ast-grep.github.io/reference/yaml.html
4. ast-grep project config (`sgconfig.yml`): https://ast-grep.github.io/guide/project/project-config.html
5. GitHub CodeQL packs customization: https://docs.github.com/code-security/codeql-cli/getting-started-with-the-codeql-cli/customizing-analysis-with-codeql-packs
6. CodeQL query authoring overview: https://codeql.github.com/docs/writing-codeql-queries/about-codeql-queries/
7. GitHub rulesets available rules: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
8. GitHub code scanning merge protection: https://docs.github.com/code-security/concepts/code-scanning/merge-protection
9. SonarQube quality gates (incl. AI Code gate): https://docs.sonarsource.com/sonarqube/latest/user-guide/quality-gates
10. dependency-cruiser: https://github.com/sverweij/dependency-cruiser
11. import-linter contract types (layers): https://import-linter.readthedocs.io/en/stable/contract_types.html
12. Nx enforce module boundaries rule: https://nx.dev/technologies/eslint/eslint-plugin/recipes/enforce-module-boundaries
13. OPA in CI/CD: https://www.openpolicyagent.org/docs/cicd
14. Conftest docs: https://www.conftest.dev/
15. GitHub push protection: https://docs.github.com/code-security/secret-scanning/working-with-push-protection
16. Gitleaks Action: https://github.com/gitleaks/gitleaks-action
17. Trivy secret scanning: https://trivy.dev/docs/latest/guide/scanner/secret/
18. OSV-Scanner Action: https://github.com/google/osv-scanner-action
19. pip-audit GitHub Action: https://github.com/pypa/gh-action-pip-audit
20. OpenSSF Scorecard Action: https://github.com/ossf/scorecard-action
