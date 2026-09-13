<DONE>
# ClaudeCode Reddit Research - Everything Dump (February 2026)

## Status

This is the consolidated master file with all currently collected outputs:

- full evidence register (51 requested items)
- match status (`Exact` / `Closest` / `Unresolved`)
- confidence scores
- ranked claims by theme
- strongest/weakest claims and rationale

As-of date: **2026-02-22**.

## Confidence Rubric

- `0.90`: exact permalink + strong title/substance match
- `0.60`: closest high-similarity source (cross-subreddit/platform drift)
- `0.10`: unresolved

## Coverage

- Exact: **40 / 51**
- Closest: **8 / 51**
- Unresolved: **3 / 51**

## Full Evidence Register

| ID  | Requested Title (Short)                        | Match Type | URL                                                                                                                                                  | Date       | Score |
| --- | ---------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----: |
| E01 | Skills hype vs plugins (6 examples)            | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qrlgij/everyones_hyped_on_skills_but_claude_code_plugins/                                              | 2026-01-30 |  0.90 |
| E02 | Waste of tokens better way?                    | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qyt0fo/this_seems_like_a_waste_of_tokens_there_has_got/                                                | 2026-02-07 |  0.90 |
| E03 | 100% AI code for 1+ year (13 lessons)          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qxvobt/ive_used_ai_to_write_100_of_my_code_for_1_year_as/                                              | 2026-02-06 |  0.90 |
| E04 | Desloppify toolset                             | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r2hsap/desloppify_agent_toolset_for_making_your_slop/                                                  | 2026-02-12 |  0.90 |
| E05 | CLAUDE.md MUST use agent ignored               | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qn9pb9/claudemd_says_must_use_agent_claude_ignores_it_80/                                              | 2026-01-26 |  0.90 |
| E06 | With Claude I became workaholic                | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qsa6oz/with_claude_i_have_become_a_workaholic/                                                         | 2026-01-31 |  0.90 |
| E07 | Burning 100k+ tokens/session                   | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r26miw/how_are_you_guys_not_burning_100k_tokens_per/                                                   | 2026-02-11 |  0.90 |
| E08 | 100 agent sessions mindmap                     | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qlmfh3/ive_spent_the_past_year_building_this_insane/                                                   | 2026-01-24 |  0.90 |
| E09 | Agent Teams walkthrough                        | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qz8tyy/how_to_set_up_claude_code_agent_teams_full/                                                     | 2026-02-08 |  0.90 |
| E10 | Agentic coding final boss                      | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r63p2q/agentic_coding_is_amazing_until_you_hit_the_final/                                              | 2026-02-16 |  0.90 |
| E11 | Claude Code + Playwright CLI                   | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r03a0t/claude_code_playwright_cli_superpowers/                                                         | 2026-02-09 |  0.90 |
| E12 | Webflow AI post                                | Closest    | https://www.reddit.com/r/webflow/comments/1qwsk1p/webflows_ai_site_builder_new_and_exciting_updates/                                                 | 2026-02-05 |  0.60 |
| E13 | Thinking outside the box trivial improvements  | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r0yhwm/thinking_outside_the_box_what_are_some_trivial/                                                 | 2026-02-10 |  0.90 |
| E14 | Permissions without renegade behavior          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r5nss7/any_advice_on_permissions_without_letting_claude/                                               | 2026-02-15 |  0.90 |
| E15 | GSD supports OpenCode                          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qk3f46/gsd_now_officially_supports_opencode/                                                           | 2026-01-22 |  0.90 |
| E16 | Memory system for coding agent                 | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r1w397/what_i_learned_building_a_memory_system_for_my/                                                 | 2026-02-11 |  0.90 |
| E17 | Ralph Wiggum explainer endorsed                | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qm5vmh/my_ralph_wiggum_breakdown_just_got_endorsed_as/                                                 | 2026-01-25 |  0.90 |
| E18 | Work 12h/day no limits                         | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r1orvx/i_work_12h_per_day_with_claude_code_and_dont_hit_any_limits/                                    | 2026-02-11 |  0.90 |
| E19 | Turning thinking time into microtasks          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r255kz/turning_claude_thinking_time_into_productive/                                                   | 2026-02-11 |  0.90 |
| E20 | Show me your /statusline                       | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qycvdu/show_me_your_statusline/                                                                        | 2026-02-07 |  0.90 |
| E21 | CLI black box open-source tool                 | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r3to9f/claude_codes_cli_feels_like_a_black_box_now_i/                                                  | 2026-02-13 |  0.90 |
| E22 | Introducing cmux                               | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r43cdr/introducing_cmux_tmux_for_claude_code/                                                          | 2026-02-13 |  0.90 |
| E23 | Reverse engineered Agent Teams                 | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qyj35i/i_reverse_engineered_how_agent_teams_works_under/                                               | 2026-02-07 |  0.90 |
| E24 | Open sourced personal Claude setup             | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qq2lur/ive_open_sourced_my_personal_claude_setup/                                                      | 2026-01-29 |  0.90 |
| E25 | Todos now Tasks in CC                          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qkddvz/todos_are_now_tasks_in_cc_inspired_by_beads/                                                    | 2026-01-23 |  0.90 |
| E26 | Automated Claude+Codex CLI workflow            | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r24g2i/i_automated_the_claude_code_and_codex_workflow/                                                 | 2026-02-11 |  0.90 |
| E27 | My personal CC setup not a joke                | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qwcg0g/my_personal_cc_setup_not_a_joke/                                                                | 2026-02-05 |  0.90 |
| E28 | Opus fell off workflow                         | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qnhgcc/opus_fell_off_heres_the_workflow_that_kept_my/                                                  | 2026-01-26 |  0.90 |
| E29 | Underrated feature: Hooks guide                | Closest    | https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/                                                 | 2026-01-24 |  0.60 |
| E30 | Subtask spawns subagents/worktrees             | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qhzagf/subtask_claude_code_creates_tasks_and_spawns/                                                   | 2026-01-20 |  0.90 |
| E31 | Open-source vibe coding tool (interview first) | Closest    | https://www.reddit.com/r/vibecoding/comments/1r2t02p/i_built_an_opensource_vibe_coding_tool_that_fixes/                                              | 2026-02-12 |  0.60 |
| E32 | Introducing Nelson                             | Closest    | https://www.linkedin.com/pulse/introducing-nelson-harry-munro--mvaie                                                                                 | 2026-02-11 |  0.60 |
| E33 | Website tracks Claude regressions              | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qqnhrl/website_that_tracks_claudes_regressions/                                                        | 2026-01-29 |  0.90 |
| E34 | haiku 4.6 - Google Search                      | Closest    | https://www.anthropic.com/claude/haiku                                                                                                               | 2025-10-15 |  0.60 |
| E35 | Auto-Memory feature 2.1.32                     | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qzmofn/how_claude_code_automemory_works_official_feature/                                              | 2026-02-08 |  0.90 |
| E36 | Codex 5.2 High vs Opus (Rust)                  | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qu26n8/codex_52_high_vs_opus_a_brutal_reality_check_in/                                                | 2026-02-02 |  0.90 |
| E37 | Insulting AI for 6 months                      | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qvunta/ive_been_insulting_ai_every_day_and_calling_the/                                                | 2026-02-04 |  0.90 |
| E38 | What happened to Opus 4.5 posts                | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qvticy/i_didnt_believe_all_the_what_happened_to_opus_45/                                               | 2026-02-04 |  0.90 |
| E39 | Codex 5.3 better than Opus 4.6                 | Closest    | https://www.dicebag.com/                                                                                                                             | 2026-02    |  0.60 |
| E40 | 18 months & 990k LOC guide                     | Unresolved | N/A                                                                                                                                                  | N/A        |  0.10 |
| E41 | Frame managing projects/tasks/context          | Closest    | https://www.linkedin.com/posts/mervegamzecinar_analyticsengineering-datalineage-terminalfirst-activity-7422266537148985345-Zj02                      | 2026-02    |  0.60 |
| E42 | It's too easy now. I have to pace myself.      | Unresolved | N/A                                                                                                                                                  | N/A        |  0.10 |
| E43 | Underestimated quality of local models         | Unresolved | N/A                                                                                                                                                  | N/A        |  0.10 |
| E44 | Plugin with 387 tools                          | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qnwtkn/i_made_a_new_plugin_for_claude_that_solves_your/                                                | 2026-01-26 |  0.90 |
| E45 | Claude devotee using Codex 95%                 | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qz2kv0/as_a_claude_code_devotee_i_am_currently_using/                                                  | 2026-02-08 |  0.90 |
| E46 | Thanks for subagents in plan mode              | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qi7v8v/to_the_person_that_recommended_using_sub_agents/                                                | 2026-01-20 |  0.90 |
| E47 | AI news agency runs itself                     | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qv4lqw/how_i_built_an_ai_news_agency_that_runs_itself/                                                 | 2026-02-03 |  0.90 |
| E48 | Stop memory frameworks                         | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r4asf6/please_stop_creating_memory_for_your_agent/                                                     | 2026-02-14 |  0.90 |
| E49 | 30-line MCP server for UI workflow             | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1r6c1er/built_a_30line_mcp_server_that_changed_my_entire/                                               | 2026-02-16 |  0.90 |
| E50 | Refactor 50k LOC without breaking prod         | Closest    | https://www.reddit.com/r/ClaudeAI/comments/1qokrqa/how_to_refactor_50k_lines_of_legacy_code_without/                                                 | 2026-01-27 |  0.60 |
| E51 | Built full game with Claude over 6 months      | Exact      | https://www.reddit.com/r/ClaudeCode/comments/1qknr1v/what_i_learned_building_a_full_game_with_claude_code_over_6_months_tips_for_long_term_projects/ | 2026-01-23 |  0.90 |

## Ranked Brief by Theme

### 1) Regressions

Strongest claim:

- Perceived regressions are persistent enough that users created and circulate monitoring trackers.
- Evidence: E33, E38, E28.
- Strength: Strong.

Weakest claim:

- Broad universal model-superiority claims (for all workloads).
- Evidence gap: E39 is closest-only.
- Strength: Weak.

### 2) Token Efficiency

Strongest claim:

- Token burn/context churn is a top shared pain point and optimization target.
- Evidence: E02, E07, E48.
- Strength: Strong.

Weakest claim:

- A single memory doctrine works for all projects.
- Counter-evidence split: E48 vs E16/E08/E51.
- Strength: Moderate-Weak.

### 3) Multi-Agent Architecture

Strongest claim:

- Rapid shift to explicit orchestration primitives: teams/tasks/subagents/worktrees/debate-review loops.
- Evidence: E09, E23, E25, E30, E26, E22.
- Strength: Strong.

Weakest claim:

- One architecture has already won.
- Evidence indicates fragmentation and workload-specific preferences.
- Strength: Weak.

### 4) Operational Best Practices

Strongest claim:

- Plan-first + verification-heavy process discipline correlates with stable outcomes.
- Evidence: E03, E28, E51, E14.
- Strength: Strong.

Weakest claim:

- Higher throughput always means higher quality.
- Counter-evidence: quality bottlenecks and variance remain.
- Evidence: E18, E06, E21.
- Strength: Weak.

## Executive Ranking

1. Multi-agent architecture standardization trend (strongest).
2. Token-efficiency pressure and optimization demand.
3. Regressions concern + monitoring behavior.
4. Process discipline as best-practice baseline.
5. Universal model-superiority claims (weak).
6. One-size-fits-all memory/architecture doctrine (weak).

## External Context Links

- https://marginlab.ai/trackers/claude-code/
- https://newreleases.io/project/github/glittercowboy/get-shit-done/release/v1.9.6
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.theverge.com/news/867673/claude-mcp-app-interactive-slack-figma-canva
- https://www.atlassian.com/blog/developer/how-to-effectively-utilise-ai-to-enhance-large-scale-refactoring

## Delta Log

This master file consolidates:

- `docs/research/claudecode_reddit_landscape_2026-02.md`
- `docs/research/claudecode_ranked_evidence_brief_2026-02.md`
