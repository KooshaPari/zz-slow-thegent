# Worklog Wave 75 - Lane E

Date: 2026-02-23
Lane focus: quality/security/testing workflows for coding agents

## Item 1

- Thread: "Secret Scanning" (`r/devsecops`) — https://www.reddit.com/r/devsecops/comments/1np3svv
- Core claim: Dedicated secret scanners must run separately from SAST, with pre-commit + CI + continuous monitoring as a combined control stack.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://docs.github.com/code-security/secret-scanning/protecting-pushes-with-secret-scanning
  - https://github.com/gitleaks/gitleaks
  - https://github.com/trufflesecurity/trufflehog
- Risk if ignored: Agent-generated commits can leak credentials to remote history before humans notice, creating immediate credential-rotation incidents.

## Item 2

- Thread: "How are you reviewing AI / code agent-generated changes? Any tools or best practices?" (`r/vibecoding`) — https://reddit.com/r/vibecoding/comments/1q7ps9n/how_are_you_reviewing_ai_code_agentgenerated/
- Core claim: Human review must be structured around deterministic checks (tests, policy, traceability) because output volume exceeds manual reasoning capacity.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://docs.anthropic.com/en/docs/claude-code/github-actions
  - https://github.com/openai/evals
  - https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Risk if ignored: Defects and insecure logic will pass as "plausible code," causing silent reliability and security regressions.

## Item 3

- Thread: "How are you actually evaluating agents once they leave the notebook?" (`r/aiagents`)
- Core claim: Offline demos are insufficient; production agents require continuous evals, dataset refresh, and runtime telemetry.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://www.langchain.com/langsmith
  - https://github.com/SWE-bench/SWE-bench
- Risk if ignored: Teams optimize for demo success while reliability collapses in real user/task distributions.

## Item 4

- Thread: "Prompt injection within GitHub Actions..." (`r/programming`) — https://www.reddit.com/r/programming/comments/1pe3cew/prompt_injection_within_github_actions_google/
- Core claim: Passing untrusted PR/issue text into privileged coding-agent workflows creates an exploitable prompt-injection path.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
- Risk if ignored: Attackers can coerce CI agents into privileged side effects (token misuse, repo mutation, data exfiltration).

## Item 5

- Thread: "I wrote secret magpie..." (`r/devops`) — https://www.reddit.com/r/devops/comments/1055i8e
- Core claim: Org-wide repository coverage and historical scanning are mandatory; scanning only one repo or default branch misses latent secrets.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://docs.github.com/en/code-security/secret-scanning/managing-alerts-from-secret-scanning/resolving-alerts
  - https://github.com/Yelp/detect-secrets
  - https://docs.gitguardian.com/ggshield-docs/integrations/overview
- Risk if ignored: Forgotten branches and archived repos become unmanaged secret debt that later re-enters active pipelines.

## Item 6

- Thread: "AI Agent Testing" (`r/QualityAssurance`)
- Core claim: Agent QA needs scenario-based regression suites with pass/fail contracts, not ad hoc spot checks.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://github.com/openai/evals
  - https://www.promptfoo.dev/
  - https://www.anthropic.com/engineering/building-effective-agents
- Risk if ignored: Release confidence will depend on anecdotal runs, leading to frequent production drift and rollback churn.

## Item 7

- Thread: "Prompt injection risks -- where is it concentrated?" (`r/ClaudeCode`)
- Core claim: Highest risk sits at boundaries where agents ingest untrusted content and can invoke tools with write/network permissions.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - https://genai.owasp.org/
  - https://modelcontextprotocol.io/
- Risk if ignored: Boundary blind spots turn normal user content into an execution channel for adversarial instructions.

## Item 8

- Thread: "So, we tried to get an AI agent to write vulnerability checks for us..." (`u/intruder_io`)
- Core claim: AI-generated security tests are useful as drafts, but must be backed by deterministic scanners and curated rulesets.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://codeql.github.com/docs/
  - https://semgrep.dev/docs/
  - https://trivy.dev/docs/
- Risk if ignored: Teams will over-trust generated checks and miss high-impact vulnerabilities outside model-generated coverage.

## Item 9

- Thread: "Stop selling 'Autonomous Agents' to businesses..." (`r/AI_Agents`)
- Core claim: Claims of autonomy without controls (audit logs, approval gates, rollback) create legal, security, and operational exposure.
- Evidence quality: B
- Verdict: Avoid Hype
- Corroborating non-Reddit links:
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://oecd.ai/en/ai-principles
  - https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
- Risk if ignored: Governance gaps will surface as compliance failures and incident-response delays when agent actions cause harm.

## Item 10

- Thread: "How are you actually measuring coding-agent quality over time?" (`r/aiagents`, related discussions)
- Core claim: Stable quality requires scorecards that combine defect escape rate, eval pass rate, MTTR, and security finding recurrence.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://github.com/openai/evals
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://opentelemetry.io/blog/2024/otel-generative-ai/
- Risk if ignored: Teams will chase raw output velocity and miss long-tail quality decay until incident volume forces reactive controls.
