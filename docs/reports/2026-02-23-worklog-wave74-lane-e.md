# Worklog Wave 74 - Lane E

Date: 2026-02-23
Lane focus: reliability/testing/security/prompt injection

## Item 1

- Thread: "AI Agent Testing" (`r/QualityAssurance`)
- Core claim: Most teams still lack production-grade agent eval loops (regression suites + trace review), even if prototypes look good.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://www.langchain.com/langsmith
  - https://docs.smith.langchain.com/
  - https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Item 2

- Thread: "How are you actually evaluating agents once they leave the notebook?" (`r/aiagents`)
- Core claim: Offline success is not enough; reliability requires continuous evals and runtime telemetry in real workflows.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://github.com/openai/evals
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://www.anthropic.com/engineering/building-effective-agents

## Item 3

- Thread: "Prompt injection risks -- where is it concentrated?" (`r/ClaudeCode`)
- Core claim: Prompt-injection risk concentrates at boundaries where untrusted content can trigger tools, exfiltrate data, or persist into memory/context.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
  - https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

## Item 4

- Thread: "So, we tried to get an AI agent to write vulnerability checks for us..." (`u/intruder_io`)
- Core claim: AI-generated security checks are useful only with deterministic scanners and explicit verification gates.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://codeql.github.com/docs/
  - https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql
  - https://semgrep.dev/docs/

## Item 5

- Thread: "Stop selling 'Autonomous Agents' to businesses. You are setting yourself up for a lawsuit." (`r/AI_Agents`)
- Core claim: Overstated autonomy claims create legal and operational risk when controls, monitoring, and accountability are weak.
- Evidence quality: B
- Verdict: Avoid Hype
- Corroborating non-Reddit links:
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
  - https://oecd.ai/en/ai-principles
