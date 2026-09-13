# Worklog Wave 74 - Lane D

Date: 2026-02-23
Lane focus: Claude Code/OpenCode ops, limits, telemetry, cost

## Item 1

- Thread: cclimits – read your Claude Code subscription limits from the terminal (`r/ClaudeCode`): https://www.reddit.com/r/ClaudeCode/comments/1r8ju9m/cclimits_read_your_claude_code_subscription/
- Core claim: Terminal-native limit visibility is now table-stakes for stable Claude Code operations.
- Evidence quality: B
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://github.com/cruzanstx/cclimits
  - https://docs.anthropic.com/en/docs/claude-code/costs
  - https://docs.anthropic.com/en/api/data-usage-cost-api

## Item 2

- Thread: ai-heatmap (`r/ClaudeCode`): https://www.reddit.com/r/ClaudeCode/comments/1r8cvzj/aiheatmap_githubstyle_contribution_graph_for_your/
- Core claim: Cost and token spend heatmaps improve behavior by making usage patterns visible over time.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://github.com/seunggabi/ai-heatmap
  - https://opentelemetry.io/docs/specs/semconv/gen-ai/
  - https://opentelemetry.io/blog/2024/otel-generative-ai/

## Item 3

- Thread: i built a free macOS menu bar app to track Claude Code usage (`r/ClaudeCode`): https://www.reddit.com/r/ClaudeCode/comments/1qmoaet/i_built_a_free_macos_menu_bar_app_to_track_claude/
- Core claim: Passive always-on usage telemetry (menu bar/dashboard) reduces surprise limit hits and improves daily cost control.
- Evidence quality: B
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://www.codequota.dev/
  - https://docs.anthropic.com/en/docs/claude-code/costs
  - https://docs.anthropic.com/en/docs/about-claude/pricing

## Item 4

- Thread: Max 20x plan i audited my jsonl files against my ... (`r/ClaudeCode`): https://www.reddit.com/r/ClaudeCode/comments/1r3zbvt/max_20x_plan_i_audited_my_jsonl_files_against_my/
- Core claim: Reconciling local session logs against provider usage/cost endpoints is necessary for trustworthy spend reporting.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://docs.anthropic.com/en/api/data-usage-cost-api
  - https://docs.anthropic.com/en/docs/claude-code/costs
  - https://docs.anthropic.com/en/docs/about-claude/pricing

## Item 5

- Thread: Built a VS Code companion for OpenCode users: session monitoring + handoff + coding workflows (feedback welcome) (`r/opencodeCLI`): https://reddit.com/r/opencodeCLI/comments/1r8kwsu/built_a_vs_code_companion_for_opencode_users/
- Core claim: OpenCode operations are moving toward companion-control patterns (monitoring + handoff) rather than single-terminal-only workflows.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://github.com/opencode-ai/opencode
  - https://opencode.ai/docs/cli/
  - https://opencode.ai/docs/github/
