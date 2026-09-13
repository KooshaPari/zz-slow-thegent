<DONE>
# Starred Set Deep Research (Third Batch)

Date: February 23, 2026

## Scope

Third-pass outward deep research over the newly provided starred set, focused on:

- MCP/security/sandbox ecosystem,
- agent PM/orchestration frameworks,
- computer-use/UI control stacks,
- residual/reference repos for roadmap triage.

## Executive Summary

1. Strong immediate candidates from this batch:

- `sdi2200262/agentic-project-management`
- `superagent-ai/vibekit`
- `pathintegral-institute/mcpm.sh` (from prior MCP pass, still core)
- `f/mcptools`
- `isaacphi/mcp-language-server`
- `upstash/context7`

2. Best computer-use candidates to pilot:

- `testdriverai/testdriverai`
- `bytedance/UI-TARS-desktop`
- `mediar-ai/terminator` (or equivalent maintained fork)

3. Keep high-noise or stale repos in pilot/reference tiers only.

## A. MCP / Security / Sandbox Layer

Primary evaluated items:

- `Minidoracat/mcp-feedback-enhanced`
- `samanhappy/mcphub`
- `mcp-use/mcp-use`
- `upstash/context7`
- `GroundNG/VibeShift`
- `evalstate/fast-agent`
- `textcortex/claude-code-sandbox`
- `nesquikm/mcp-rubber-duck`
- `MCPCat/mcpcat-typescript-sdk`
- `mediar-ai/MCP-server-client-computer-use-ai-sdk`

### Practical picks

- `mcp-use`: strong framework candidate for MCP app/server development.
- `context7`: high-signal MCP documentation/context utility.
- `fast-agent`: good prompt/test workflow lane for MCP-enabled agents.
- `vibekit` (from orchestration lane): strongest sandbox/redaction/observability control plane.

### Risks

- Several small MCP servers are valuable but lightly governed (license/security/ops docs often thin).
- Archived projects (e.g., `claude-code-sandbox`) should not be selected as long-term foundations.

## B. Agent PM / Orchestration Layer

Primary evaluated items:

- `sdi2200262/agentic-project-management`
- `willer/claude-fsd`
- `nachoal/ai-fleet`
- `opactorai/Claudable`
- `superagent-ai/vibekit`
- `bobmatnyc/claude-multiagent-pm`
- `vanzan01/claude-code-sub-agent-collective`
- `Helmi/claude-simone`
- `benbasha/Claude-Autopilot`
- `praneybehl/code-review-mcp`

### Top recommendation

- Core orchestrator: `agentic-project-management`
- Safety/sandbox runtime: `vibekit`
- Product-facing UX adjunct: `Claudable`

### Caution items

- `claude-multiagent-pm`: archived.
- `ai-fleet`, `claude-fsd`, `code-review-mcp`: lower maturity or narrow scope.
- `Claude-Autopilot`: automation value exists, but unattended safety controls must be validated.

## C. Computer-Use / UI Agent Layer

Primary evaluated items:

- `testdriverai/testdriverai`
- `moonshinelabs-ai/skipper-tool`
- `bytedance/UI-TARS-desktop`
- `microsoft/aici`
- `hide-org/hide`
- `GongRzhe/terminator` (fork context, original ecosystem considered)
- `GongRzhe/Human-In-the-Loop-MCP-Server`
- `GongRzhe/ACP-MCP-Server`
- `GongRzhe/Quickchart-MCP-Server`
- `GongRzhe/Office-Visio-MCP-Server`

### Best near-term pilot path

1. `testdriverai` for QA-driven computer-use.
2. `UI-TARS-desktop` for full multimodal GUI agent stack.
3. `terminator`-class desktop automation where OS support is acceptable.
4. Add HITL approval server for risky actions.

### Key caveats

- Ambiguous protocol naming in “ACP-MCP” bridge space; verify exact protocol stack before adoption.
- Office/COM/desktop-specific MCP servers can be useful but carry high environment/dependency burden.

## D. Residual / Reference Classification

### Adopt/Pilot/Reference/Ignore summary

- `zed-industries/zed`: Reference
- `ChrisRoyse/Pheromind`: Ignore (until clearer fit)
- `jehna/humanify`: Reference utility
- `cvs-health/testaro`: Pilot (accessibility lane)
- `cvs-health/mcbizmod`: Ignore
- `chunkhound/chunkhound`: Pilot
- `bgauryy/octocode-mcp` / `Muvon/octocode`: Pilot
- `KooshaPari/odin-*`: Ignore for current agent-stack roadmap
- `KooshaPari/Frostify`: Reference

## Recommended Stack for This Batch

### Immediate baseline

- Orchestration: `agentic-project-management`
- Sandbox + observability: `vibekit`
- MCP ops: `mcpm.sh` + `mcptools` + `mcp-language-server`
- Context/doc channel: `context7`

### Pilot stream

- Computer-use: `testdriverai`, `UI-TARS-desktop`
- PM alternatives: `Claudable`, `claude-simone` (if roadmap requires)
- Niche MCP servers with strict allowlists and audits

## Hard Gates Before Promotion

1. Reproducible install/build/test in your environment.
2. License/security policy clarity.
3. Secrets/auth boundary validation.
4. Rollback and incident path proof.
5. Integration compatibility with your existing lane/worktree governance.

## High-Value Links

- https://github.com/sdi2200262/agentic-project-management
- https://github.com/superagent-ai/vibekit
- https://github.com/opactorai/Claudable
- https://github.com/mcp-use/mcp-use
- https://github.com/upstash/context7
- https://github.com/evalstate/fast-agent
- https://github.com/testdriverai/testdriverai
- https://github.com/bytedance/UI-TARS-desktop
- https://github.com/mediar-ai/terminator
- https://github.com/isaacphi/mcp-language-server
- https://github.com/f/mcptools
- https://github.com/pathintegral-institute/mcpm.sh
- https://github.com/hide-org/hide
- https://github.com/Helmi/claude-simone
- https://github.com/benbasha/Claude-Autopilot
- https://github.com/vanzan01/claude-code-sub-agent-collective
- https://github.com/praneybehl/code-review-mcp
- https://github.com/zed-industries/zed
- https://github.com/chunkhound/chunkhound
- https://github.com/cvs-health/testaro
