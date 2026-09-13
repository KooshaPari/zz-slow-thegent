# Product Requirements Document: CLIProxyAPI

**Version:** 1.0.0  
**Created:** 2026-02-18

## 1. Overview

- OpenAI/Gemini/Claude compatible API endpoints for CLI models
- OpenAI Codex support (GPT models) via OAuth login
- Claude Code support via OAuth login
- Qwen Code support via OAuth login
- iFlow support via OAuth login
- **Cursor Agent CLI support** via local subprocess invocation
- Amp CLI and IDE extensions support with provider routing
- Streaming and non-streaming responses
- Function calling/tools support
- Multimodal input support (text and images)
- Multiple accounts with round-robin lo

## 2. Objectives

- Review this research

## 3. Success Metrics

- \*seven dimensions\*\* with specific metrics:
- ----------|----------------|-------------------|--------|
- \*Code Generation\*\* | HumanEval+ pass@1 | BigCodeBench, LiveCodeBench, MBPP+ | 15% |
- \*Agentic SWE\*\* | SWE-bench Verified | Aider Polyglot, SWE-bench Lite | 25% |
- \*Tool Use\*\* | BFCL accuracy | ToolBench, τ-Bench | 15% |
- \*Autonomous Agents\*\* | GAIA Level 3 | WebArena, AgentBench | 15% |
- \*ML Engineering\*\* | MLE-bench medals | RE-bench, DevAI | 10% |
- \*Security\*\* | CyberSecEval safe rate | SecCodePLT | 5% |
- \*Reasoning\*\* | GPQA Diamond | AIME, MATH-500 | 15% |
- -------|-------------|-------------|

## 4. Stakeholders

## 5. Target Users

- User
- user

## 6. Functional Requirements

### FR-1: Accuracy:

93.17%

### FR-2: Latency:

50ms

### FR-3: Output:

Domain + Action (e.g., "programming/code-generation")

### FR-4: Input:

User prompt + context

### FR-5: Abilities:

25-dimensional latent space per model

### FR-6: Formula:

P(success) = sigmoid(∑ a_i · (θ_i - b_i))

### FR-7: Features:

25-dimensional difficulty vector from prompt

### FR-8: Score:

P(success) / cost_per_token

### FR-9: Latency:

15-30ms

### FR-10: For Users Who Want to Get Started

### FR-11: For Developers Who Want to Understand the Code

### FR-12: High-Level Flow

### FR-13: Component Breakdown

### FR-14: Documentation

### FR-15: Source Code

### FR-16: Database

### FR-17: Arch-Router (Task Classification)

### FR-18: MIRT-BERT (Cost-Quality Prediction)

### FR-19: ExecutorRegistry (Model Unification)

### FR-20: FeatureExtractor (Query Analysis)

### FR-21: 1. Install Dependencies

### FR-22: 2. Set up Database

### FR-23: 3. Start MLX-LM Server

### FR-24: 4. Run Tests

### FR-25: 5. Integrate into CLIProxyAPI

### FR-26: Basic Usage

### FR-27: Testing Components Individually

### FR-28: DualRouter

### FR-29: ExecutorRegistry

### FR-30: MIRT Client

### FR-31: FeatureExtractor

### FR-32: Expected Latency

### FR-33: Run Benchmarks

### FR-34: MLX-LM Server Not Responding

### FR-35: MIRT Checkpoint Not Loading

### FR-36: Feature Extraction Too Slow

### FR-37: Unit Tests

### FR-38: Integration Tests (Pending)

### FR-39: Week 2: MLX-LM Integration

### FR-40: Week 3: Vibeproxy UI

### FR-41: Week 4: Testing & Optimization

### FR-42: Week 5: Production

### FR-43: For Technical Questions

### FR-44: For Integration Issues

### FR-45: For Performance Issues

### FR-46: Read the Overview

→ [DUAL_ROUTER_WEEK1_IMPLEMENTATION.md](./DUAL_ROUTER_WEEK1_IMPLEMENTATION.md)

### FR-47: Follow Setup Guide

→ [DUAL_ROUTER_SETUP_GUIDE.md](./DUAL_ROUTER_SETUP_GUIDE.md)

### FR-48: Check Status

→ [DUAL_ROUTER_IMPLEMENTATION_STATUS.md](./DUAL_ROUTER_IMPLEMENTATION_STATUS.md)

### FR-49: Architecture Review

→ See "System Architecture" below

### FR-50: Code Tour

→ Start with `internal/router/dual_router.go`

### FR-51: Run Tests

→ `go test ./internal/router/... -v`

### FR-52: Check Examples

→ See "Integration Examples" below

### FR-53: Tools Used

LS, Read, Grep tools

### FR-54: Files Analyzed

go.mod, go.sum, README, config.example.yaml, Docker, internal packages

### FR-55: Output

Comprehensive tech stack inventory and architecture map

### FR-56: Cursor Agent

3 official documentation pages fetched

### FR-57: Auggie CLI

3 official documentation pages fetched

### FR-58: Total Sources

6+ official docs, 15+ web research sources

### FR-59: MCP Architecture

Mapped transport methods, capabilities, security models

### FR-60: ACP Protocol

Reviewed Agent Client Protocol standards

### FR-61: CLI Features

Documented all flags, modes, and configurations

### FR-62: Tool Design

Proposed 5 major MCP tools for each CLI

### FR-63: Implementation Phases

4-phase roadmap for each integration

### FR-64: Use Cases

Real-world examples for automation and development

### FR-65: Project Context

`agileplus/project.md`

### FR-66: Cursor Agent Research

`docs/cursor-agent-research.md`

### FR-67: Auggie CLI Research

`docs/auggie-cli-research.md`

### FR-68: This Summary

`docs/RESEARCH_SUMMARY.md`

### FR-69: Total Words Written

12,000+

### FR-70: Code Examples Provided

70+

### FR-71: Tables Created

30+

### FR-72: Research Sources

25+

### FR-73: Hours of Research

~8 hours of focused research

### FR-74: 1. Project Context Document

### FR-75: 2. Cursor Agent CLI Research

### FR-76: 3. Auggie CLI Research

### FR-77: Phase 1: Codebase Analysis

### FR-78: Phase 2: Official Documentation Review

### FR-79: Phase 3: Integration Analysis

### FR-80: Phase 4: Opportunity Identification

### FR-81: About CLIProxyAPI

### FR-82: About Cursor Agent CLI

### FR-83: About Auggie CLI

### FR-84: Integration Opportunities

### FR-85: For AI Assistants (Auggie, Cursor Agent)

### FR-86: For Team Planning

### FR-87: For Community Engagement

### FR-88: Step 1: Team Review (This Week)

### FR-89: Step 2: Proposal Creation (Next Week)

### FR-90: Step 3: Proof of Concept (Weeks 3-4)

### FR-91: Step 4: Implementation (Weeks 5+)

### FR-92: File Locations

### FR-93: Key Statistics

### FR-94: Installation Commands (For Reference)

### FR-95: Quick MCP Overview

### FR-96: Complete Project Context

- Documented conventions, architecture, constraints

### FR-97: Cursor Agent CLI Research

- Integration opportunities via MCP servers

### FR-98: Auggie CLI Research

- Automation and CI/CD integration possibilities

### FR-99: CLIProxyAPI Integration Opportunities

- Vision: Why combine them?

### FR-100: CLIProxyAPI Integration Opportunities

- Vision: Automation and CI/CD focus

### FR-101: Project Onboarding

Reference `agileplus/project.md` for new contributors

### FR-102: Feature Proposals

Use MCP tool designs from research documents

### FR-103: Architecture Decisions

Reference integration patterns from both CLIs

### FR-104: Implementation Roadmaps

Follow 4-phase approach from each research doc

### FR-105: GitHub Issues

Link to research for context on feature requests

### FR-106: PRs

Reference conventions from `project.md`

### FR-107: Discussions

Share research findings for feedback

### FR-108: Documentation

Incorporate findings into official docs

### FR-109: Understands code deeply

- Indexes entire codebases automatically

### FR-110: Executes tools

- Runs shell commands, reads/writes files, uses MCP tools

### FR-111: Integrates everywhere

- Works in standalone terminal, CI/CD, ACP editors

### FR-112: Automates tasks

- Designed for code reviews, issue triage, monitoring, exception handling

### FR-113: Runtime

Node.js 22.x or later

### FR-114: Shell

zsh, bash, or fish

### FR-115: Platforms

macOS, Linux, Windows (WSL)

### FR-116: Authentication

Augment account (free tier available for beta)

### FR-117: Network

Optional (works offline with cached context)

### FR-118: Tools

- Functions agent can call

### FR-119: Resources

- Structured data sources

### FR-120: Prompts

- Pre-built workflows

### FR-121: Roots

- Filesystem/URI boundary checks

### FR-122: Elicitation

- Server-initiated information requests

### FR-123: Universal access

- Same Auggie instance across editors

### FR-124: Consistent behavior

- Same tools and context everywhere

### FR-125: Easy deployment

- Single binary, works in any ACP editor

### FR-126: No custom integration

- Standard ACP protocol handling

### FR-127: Auggie CLI Overview

https://docs.augmentcode.com/cli/overview

### FR-128: CLI Reference

https://docs.augmentcode.com/cli/reference

### FR-129: Integrations & MCP

https://docs.augmentcode.com/cli/integrations

### FR-130: Automation

https://docs.augmentcode.com/cli/automation

### FR-131: ACP Clients

https://docs.augmentcode.com/cli/acp/clients

### FR-132: GitHub Repository

https://github.com/augmentcode/auggie

### FR-133: NPM Package

https://www.npmjs.com/package/@augmentcode/auggie

### FR-134: Blog

https://www.augmentcode.com/blog

### FR-135: MCP Directory

https://www.augmentcode.com/mcp/

### FR-136: ACP Spec

https://agentclientprotocol.com/

### FR-137: MCP Protocol

https://modelcontextprotocol.io/

### FR-138: Augment Code Docs

https://docs.augmentcode.com/

### FR-139: Key Findings

### FR-140: 1.1 What is Auggie CLI?

### FR-141: 1.2 Core Architecture

### FR-142: 1.3 System Requirements

### FR-143: 2.1 Interactive Mode

### FR-144: 2.2 Print Mode (Automation)

### FR-145: 2.3 Quiet Mode

### FR-146: 2.4 Compact Mode

### FR-147: 2.5 Custom Commands

### FR-148: 2.6 Session Management

### FR-149: 2.7 Configuration & Customization

### FR-150: 3.1 MCP Architecture in Auggie

### FR-151: 3.2 MCP Transport Methods

### FR-152: 3.3 Configuring MCP Servers

### FR-153: 3.4 MCP Capabilities in Auggie

### FR-154: 3.5 MCP Overrides

### FR-155: 4.1 What is ACP?

### FR-156: 4.2 Using Auggie with ACP Editors

### FR-157: 4.3 ACP Benefits for CLIProxyAPI Integration

### FR-158: 5.1 Supported Native Integrations

### FR-159: 5.2 Using Integrations in Commands

### FR-160: 6.1 Vision: Why Auggie CLI + CLIProxyAPI?

### FR-161: 6.2 Proposed MCP Server Architecture

### FR-162: 6.3 Proposed MCP Tools for CLIProxyAPI

### FR-163: 6.4 Example Auggie Commands with CLIProxyAPI MCP

### FR-164: 6.5 Implementation Phases

### FR-165: 7.1 GitHub Actions Integration

### FR-166: 7.2 CLI Scripts

### FR-167: 7.3 Pipe-based Workflows

### FR-168: 7.4 Pre-commit Hooks

### FR-169: 8.1 Authentication

### FR-170: 8.2 MCP Server Security

### FR-171: 8.3 Integration with CLIProxyAPI Security

### FR-172: Key Differentiator

### FR-173: Official Documentation

### FR-174: Community Resources

### FR-175: Related Standards

### FR-176: For CLIProxyAPI Maintainers

### FR-177: For Integration Explorers

### FR-178: Community Engagement

### FR-179: Recommended Path Forward

### FR-180: Review this research

Assess alignment with project roadmap

### FR-181: Create AgilePlus proposal

Formalize MCP server feature

### FR-182: Design MCP interface

Define tool set and security model

### FR-183: Prototype

Build minimal MCP server for proof-of-concept

### FR-184: Test with Auggie

Verify integration works end-to-end

### FR-185: Gather feedback

Community input on proposed tools

### FR-186: Implement

Execute in phases from section 6.5

### FR-187: Install Auggie CLI

`npm install -g @augmentcode/auggie`

### FR-188: Login

`auggie login`

### FR-189: Explore

`auggie "Analyze the CLIProxyAPI codebase"`

### FR-190: Test MCP

Configure a custom `.augment/settings.json`

### FR-191: Create command

Write a custom Auggie command for CLIProxyAPI

### FR-192: Provide feedback

Share findings with team

### FR-193: Better Automation

- Native support in CI/CD and scripting

### FR-194: Natural Language Management

- Conversational provider control

### FR-195: Enterprise Features

- Audit logging, multi-tenant support

### FR-196: Community Alignment

- Both embrace open standards (MCP, ACP)

### FR-197: Novel Use Cases

- Enable scenarios previously impossible

### FR-198: Short term

(1-2 weeks): Create AgilePlus proposal

### FR-199: Medium term

(3-4 weeks): Prototype core MCP tools

### FR-200: Long term

(2+ months): Production release with CI/CD examples

### FR-201: Cursor CLI Overview

https://cursor.com/docs/cli/overview

### FR-202: Using Agent in CLI

https://cursor.com/docs/cli/using

### FR-203: MCP in Cursor

https://cursor.com/docs/context/mcp

### FR-204: Building MCP Servers

https://cursor.com/docs/cookbook/building-mcp-server

### FR-205: MCP Protocol Spec

https://modelcontextprotocol.io/introduction

### FR-206: MCP Directory

https://cursor.com/docs/context/mcp/directory

### FR-207: Cursor Blog

https://cursor.com/blog/cli (Release announcement)

### FR-208: Smithery MCP Hub

https://smithery.ai/ (MCP server directory)

### FR-209: Example MCP Servers

https://github.com/msfeldstein/mcp-test-servers

### FR-210: CursorMCP Hub

https://cursormcp.com/en

### FR-211: Key Findings

### FR-212: 1.1 What is Cursor Agent CLI?

### FR-213: 1.2 Core Architecture

### FR-214: 2.1 Interactive Mode

### FR-215: 2.2 Non-Interactive Mode (Print Mode)

### FR-216: 2.3 Session Management

### FR-217: 2.4 Output Formats

### FR-218: 3.1 What is MCP?

### FR-219: 3.2 MCP Architecture in Cursor Agent

### FR-220: 3.3 MCP Transport Methods

### FR-221: 3.4 MCP Capabilities Supported by Cursor Agent

### FR-222: 3.5 MCP Configuration

### FR-223: 4.1 Rules System

### FR-224: 4.2 Codebase Indexing

### FR-225: 5.1 Command Approval

### FR-226: 5.2 MCP Tool Approval

### FR-227: 5.3 Security Best Practices

### FR-228: 6.1 Vision: Why Cursor Agent + CLIProxyAPI?

### FR-229: 6.2 Proposed Integration Architecture

### FR-230: 6.3 Potential MCP Tools for CLIProxyAPI

### FR-231: 6.4 Benefits to CLIProxyAPI Users

### FR-232: 6.5 Implementation Phases

### FR-233: 7.1 Go MCP Server Implementation

### FR-234: 7.2 Security Implications

### FR-235: 7.3 Performance & Scalability

### FR-236: Cursor Agent vs. Traditional CI/CD

### FR-237: MCP Ecosystem Alternatives

### FR-238: Official Documentation

### FR-239: Key Resources

### FR-240: Community & Examples

### FR-241: For CLIProxyAPI Maintainers

### FR-242: For Integration Explorers

### FR-243: Review this research

Assess alignment with project goals

### FR-244: Create change proposal

Use AgilePlus to formalize MCP server feature

### FR-245: Design MCP interface

Define tool set and protocols

### FR-246: Prototype

Build minimal MCP server for proof-of-concept

### FR-247: Community feedback

Share proposal for community input

### FR-248: Implementation

Execute in phases per section 6.5

### FR-249: Experiment locally

````bash


### FR-250: Test MCP setup

Configure a simple `.cursor/mcp.json` for CLIProxyAPI


### FR-251: Prototype custom tool

Write a minimal MCP server to understand protocol


### FR-252: Provide feedback

Share findings with team and community


### FR-253: Better User Experience

Conversational provider management


### FR-254: Automation

CI/CD-friendly credential and routing management


### FR-255: Innovation

New workflows previously impossible


### FR-256: Community

Aligns with open standards (MCP) and tools (Cursor)


### FR-257: Documentation

Tutorials, examples, API docs


### FR-258: Testing

Additional test coverage, edge cases


### FR-259: Features

Community-requested enhancements


### FR-260: Bug Fixes

Issues from GitHub tracker


### FR-261: Performance

Optimizations and benchmarks


### FR-262: Security

Security audits and improvements


### FR-263: Security patches

Immediate (within 24 hours)


### FR-264: Bug fixes

Weekly


### FR-265: Features

Monthly evaluation


### FR-266: Breaking changes

Evaluated case-by-case


### FR-267: Major releases

Annually or when breaking changes needed


### FR-268: Minor releases

Monthly or when significant features ready


### FR-269: Patch releases

As needed for bugs and security


### FR-270: Documentation

Start with docs in `/docs`


### FR-271: Issues

GitHub issue tracker


### FR-272: Discussions

GitHub discussions for questions


### FR-273: Security

See [SECURITY.md](../SECURITY.md)


### FR-274: Code of Conduct

We maintain a welcoming environment


### FR-275: Communication

Respectful and constructive


### FR-276: Recognition

Contributors acknowledged in releases


### FR-277: Project Background




### FR-278: Project Goals




### FR-279: Relationship with Upstream




### FR-280: Enhanced Features




### FR-281: Configuration Differences




### FR-282: API Differences




### FR-283: Breaking Changes (if any)




### FR-284: For Users of Original CLIProxyAPI




### FR-285: Migration Checklist




### FR-286: Compatibility Matrix




### FR-287: Rollback Plan




### FR-288: Quick Start for Contributors




### FR-289: Areas for Contribution




### FR-290: Contribution Standards




### FR-291: Our Approach




### FR-292: Divergence Documentation




### FR-293: Contributing Back to Upstream




### FR-294: Versioning




### FR-295: Release Schedule




### FR-296: Support Policy




### FR-297: Getting Help




### FR-298: Community




### FR-299: Planned Enhancements




### FR-300: Long-term Vision




### FR-301: Why fork instead of contributing to original?




### FR-302: Will you merge back with the original?




### FR-303: Is this fork production-ready?




### FR-304: How do I report issues?




### FR-305: Can I contribute?




### FR-306: What about licensing?




### FR-307: Original Project




### FR-308: Fork Maintainers




### FR-309: Enhanced Maintenance

Provide more frequent updates and faster response to issues


### FR-310: Community-Driven Development

Enable community features and improvements


### FR-311: Extended Features

Add functionality requested by users but not implemented upstream


### FR-312: Improved Developer Experience

Better documentation, testing, and tooling


### FR-313: Security Focus

Faster security patches and proactive security measures


### FR-314: Prioritize security

Always take security improvements


### FR-315: Preserve fork features

Keep fork-specific enhancements


### FR-316: Document divergence

Update this guide with differences


### FR-317: Test thoroughly

Ensure no regressions


### FR-318: Current

Creating a new connection for each request adds 200-500ms overhead


### FR-319: After

Reusing pooled connections reduces overhead to <5ms


### FR-320: Scale Impact

10 concurrent requests = 2-5 seconds saved per batch


### FR-321: Automatic Connection Reuse

Returns healthy connections from pool


### FR-322: Health Monitoring

Background health checks every 30s


### FR-323: Idle Eviction

Removes unused connections after 5 minutes


### FR-324: Thread-Safe

Safe concurrent access with proper synchronization


### FR-325: Statistics

Track creation, reuse, evictions, and errors


### FR-326: Graceful Shutdown

Proper cleanup on close


### FR-327: Connection Reuse Rate

70-90% of requests (initial plateau at 40%)


### FR-328: Latency Reduction

200-500ms → 5-20ms per request


### FR-329: Throughput Increase

3-5x improvement for concurrent requests


### FR-330: Memory Overhead

~5-10MB per 10 connections


### FR-331: Current

Identical requests are re-executed from scratch


### FR-332: After

Identical requests return cached results in <1ms


### FR-333: Use Cases

Code analysis, documentation lookup, model inference


### FR-334: Intelligent Key Generation

MD5 hash of agent type + input


### FR-335: Size-Based Eviction

LRU eviction when cache full


### FR-336: TTL Management

Auto-expiration with periodic cleanup


### FR-337: Hit Rate Tracking

Monitor cache effectiveness


### FR-338: Thread-Safe

Safe concurrent access


### FR-339: Statistics

Hits, misses, evictions, current size/entries


### FR-340: Cache Hit Rate

40-70% for typical usage


### FR-341: Response Time (Hit)

<1ms


### FR-342: Response Time (Miss)

Original execution time


### FR-343: Memory Overhead

100MB for 100MB cache


### FR-344: Throughput

10-20x improvement for cache-heavy workloads


### FR-345: Current

Polling or batch responses = high latency


### FR-346: After

Real-time streaming with <100ms latency


### FR-347: Use Cases

Live agent output, progress tracking, long-running operations


### FR-348: Real-Time Streaming

Server-Sent Events protocol


### FR-349: Multiple Clients

One stream, many subscribers


### FR-350: Message Buffering

New clients receive recent history


### FR-351: Automatic Heartbeat

Keep-alive every 30s


### FR-352: Thread-Safe

Concurrent client access


### FR-353: Statistics

Messages sent, bytes, clients, errors


### FR-354: Message Latency

<100ms end-to-end


### FR-355: Throughput

Hundreds of messages/second per stream


### FR-356: Memory per Stream

~1-5MB (including buffers)


### FR-357: Connection Overhead

Minimal (HTTP/1.1 keep-alive)


### FR-358: Days 1-2

Copy code, update structs, integrate with session management


### FR-359: Days 3-4

Add HTTP request handling, test concurrent operations


### FR-360: Day 5

Performance testing, monitoring integration


### FR-361: Days 1-2

Copy code, integrate with query handlers


### FR-362: Days 3-4

Add cache invalidation logic, test hit rates


### FR-363: Day 5

Configuration tuning, analytics


### FR-364: Days 1-3

Copy code, HTTP endpoint setup, client testing


### FR-365: Days 4-5

Integration with agent execution, production testing


### FR-366: Unit Tests

All three components


### FR-367: Integration Tests

Pool + Cache + Streaming together


### FR-368: Load Tests

Concurrent connections, throughput, latency


### FR-369: Staging Deployment

Real workload testing


### FR-370: Cause

MaxConnections too low for workload


### FR-371: Solution

Increase MaxConnections config


### FR-372: Cause

MaxIdleTime too short


### FR-373: Solution

Increase MaxIdleTime or reduce connections


### FR-374: Cause

Workload doesn't have repeating requests


### FR-375: Solution

Reduce TTL, focus on specific query patterns


### FR-376: Cause

Entries not expiring, cache full


### FR-377: Solution

Reduce MaxSizeKB or TTL


### FR-378: Cause

Browser doesn't support SSE or firewall blocking


### FR-379: Solution

Use polling fallback, check CORS


### FR-380: Cause

Proxy timeout


### FR-381: Solution

Heartbeat already implemented, check proxy config


### FR-382: Problem Solved




### FR-383: What's Provided




### FR-384: Key Components




### FR-385: Features




### FR-386: Integration Steps




### FR-387: Performance Expectations




### FR-388: Problem Solved




### FR-389: What's Provided




### FR-390: Key Components




### FR-391: Features




### FR-392: Integration Steps




### FR-393: Configuration Strategies




### FR-394: Performance Expectations




### FR-395: Problem Solved




### FR-396: What's Provided




### FR-397: Key Components




### FR-398: Features




### FR-399: HTTP Integration




### FR-400: Client Implementation (JavaScript)




### FR-401: Integration Steps




### FR-402: Performance Expectations




### FR-403: Week 1: Connection Pooling




### FR-404: Week 2: Response Caching




### FR-405: Week 3: SSE Streaming




### FR-406: Week 3+: Testing & Staging




### FR-407: Connection Pooling




### FR-408: Response Caching




### FR-409: SSE Streaming




### FR-410: Performance Metrics




### FR-411: Resource Impact




### FR-412: Connection Pool Issues




### FR-413: Cache Issues




### FR-414: Streaming Issues




### FR-415: Create pool on AgentAPI startup

```go


### FR-416: Use pool in request handlers

```go


### FR-417: Monitor pool health

```go


### FR-418: Create cache on startup

```go


### FR-419: Use cache in query handling

```go


### FR-420: Monitor cache effectiveness

```go


### FR-421: Create stream on operation start

```go


### FR-422: Stream output as it arrives

```go


### FR-423: Set up HTTP endpoints

```go


### FR-424: 80% increase in production reliability

- **Reduced MTTR by 50%** (better diagnostics)


### FR-425: Fewer runaway processes

(enforcement)


### FR-426: Zero auth failures

(automatic refresh)


### FR-427: Dynamic model support

(no hardcoding)


### FR-428: Integration

Review PHASE1_IMPLEMENTATION_GUIDE.md


### FR-429: Code details

Check comments in source files


### FR-430: Architecture

Review AGENTAPI_AUGGIE_CURSOR_REVIEW.md


### FR-431: Testing

See PHASE1_IMPLEMENTATION_GUIDE.md testing section


### FR-432: Deployment

Use PHASE1_IMPLEMENTATION_SUMMARY.md checklist


### FR-433: Code Files (5 complete Go modules)




### FR-434: Documentation Files (7 comprehensive guides)




### FR-435: Pre-Integration




### FR-436: Integration (Week 1)




### FR-437: Testing (Week 1)




### FR-438: Deployment (Week 2)




### FR-439: All Code Includes:




### FR-440: Standards Met:




### FR-441: Error Classification




### FR-442: Health Checks




### FR-443: Resource Limits




### FR-444: Token Refresh




### FR-445: Model Discovery




### FR-446: Unit Tests (existing in code examples)




### FR-447: Integration Tests (to add)




### FR-448: E2E Tests (to add)




### FR-449: Load Tests (recommended)




### FR-450: Metrics to Expose




### FR-451: Alerts to Configure




### FR-452: Immediate (Days 1-3 after integration)




### FR-453: Short-term (Week 1)




### FR-454: Medium-term (Weeks 2-4)




### FR-455: Phase 1 Success = All Below True:




### FR-456: Expected Improvement:




### FR-457: agentapi-error-classification.go

(250+ lines)


### FR-458: agentapi-health-check.go

(400+ lines)


### FR-459: agentapi-resource-limits.go

(400+ lines)


### FR-460: agentapi-auggie-token-refresh.go

(350+ lines)


### FR-461: agentapi-cursor-model-discovery.go

(450+ lines)


### FR-462: PHASE1_IMPLEMENTATION_GUIDE.md

- Step-by-step integration guide


### FR-463: PHASE1_IMPLEMENTATION_SUMMARY.md

- Executive summary


### FR-464: DYNAMIC_SERVICE_DISCOVERY_IMPLEMENTATION.md

(from earlier)


### FR-465: AGENTAPI_AUGGIE_CURSOR_REVIEW.md

(from earlier)


### FR-466: AGENTAPI_IMPLEMENTATION_PATTERNS.md

(from earlier)


### FR-467: AGENTAPI_REVIEW_SUMMARY.md

(from earlier)


### FR-468: DOCUMENTATION_INDEX.md

(from earlier)


### FR-469: DYNAMIC_SERVICE_DISCOVERY_IMPLEMENTATION.md

- VibeProxy service discovery


### FR-470: AGENTAPI_AUGGIE_CURSOR_REVIEW.md

- Comprehensive review


### FR-471: AGENTAPI_IMPLEMENTATION_PATTERNS.md

- Code patterns


### FR-472: AGENTAPI_REVIEW_SUMMARY.md

- Executive summary


### FR-473: DOCUMENTATION_INDEX.md

- Navigation guide


### FR-474: Problem

System not fully optimized for target workload


### FR-475: Solution

Systematic performance optimization across all layers


### FR-476: Problem

Basic round-robin doesn't handle complex scenarios


### FR-477: Solution

Sophisticated routing with multiple strategies


### FR-478: Problem

Cache only helps identical queries


### FR-479: Solution

Match semantically similar queries


### FR-480: What It Solves




### FR-481: What It Provides




### FR-482: Optimization Strategies




### FR-483: Integration Steps




### FR-484: Performance Targets & Achievable Results




### FR-485: What It Solves




### FR-486: What It Provides




### FR-487: Advanced Routing Scenarios




### FR-488: Integration Steps




### FR-489: What It Solves




### FR-490: What It Provides




### FR-491: Integration Steps




### FR-492: Architecture




### FR-493: Implementation




### FR-494: Performance Targets




### FR-495: Week 9: Performance Tuning




### FR-496: Week 10: Advanced Routing & Semantic Cache




### FR-497: Week 11: Multi-Region & Final Integration




### FR-498: Phase 4A: Staging Validation (3 days)




### FR-499: Phase 4B: Canary Deployment (3 days)




### FR-500: Phase 4C: Full Rollout (2 days)




### FR-501: Rollback Plan




### FR-502: Key Metrics to Monitor




### FR-503: Alerting Strategy




### FR-504: Performance Tuning

- CPU, memory, and network optimization


### FR-505: Advanced Routing

- Sophisticated load balancing strategies


### FR-506: Semantic Caching

- AI-powered query similarity matching


### FR-507: Multi-Region Deployment

- Geographic distribution and failover


### FR-508: WHEN

request specifies model explicitly


### FR-509: THEN

skip router and use specified model (unless disabled)


### FR-510: WHEN

task is classified as "tool_call"


### FR-511: THEN

rule: "prioritize Claude/GPT-4 → fallback to Gemini if unavailable"


### FR-512: WHEN

model fails on task_type > 30% of time


### FR-513: THEN

auto-generate rule: "avoid [model] for [task_type] → fallback to [better_model]"


### FR-514: Routing Latency

<20ms (with caching)


### FR-515: Cache Hit Rate

Expected 60-80% for repeated requests


### FR-516: Task Classification Accuracy

95%+ (based on feature detection)


### FR-517: Model Selection Accuracy

90%+ (based on cost-quality optimization)


### FR-518: Code Written

~1215 LOC


### FR-519: Files Created

10


### FR-520: API Endpoints

4


### FR-521: Unit Tests

13


### FR-522: Test Coverage

85%+


### FR-523: Routing Latency

<20ms


### FR-524: Week 4: Semantic Router Integration ✅




### FR-525: Week 5: RouteLLM Integration ✅




### FR-526: Week 6: Request Feature Extraction & Caching ✅




### FR-527: Integration & API Layer ✅




### FR-528: Code Files Created (~1215 LOC)




### FR-529: Routing Endpoints




### FR-530: 1. Semantic Router




### FR-531: 2. RouteLLM Cost-Quality Optimizer




### FR-532: 3. Request Parser & Feature Extractor




### FR-533: 4. Redis Caching




### FR-534: 5. Routing Service




### FR-535: Unit Tests Created




### FR-536: Test Coverage




### FR-537: Route Request




### FR-538: Classify Task




### FR-539: Auggie CLI Docs

https://docs.augmentcode.com/cli/


### FR-540: Augment Code

https://www.augmentcode.com/


### FR-541: CLIProxyAPI Repo

https://github.com/router-for-me/CLIProxyAPI


### FR-542: This Implementation

docs/auggie-integration.md


### FR-543: Phase 1: Core Executor (4 files)




### FR-544: Phase 2: Authentication (4 files)




### FR-545: Phase 3: System Integration (4 files modified)




### FR-546: Phase 4: Documentation (2 files)




### FR-547: Minimal Configuration




### FR-548: Full Configuration




### FR-549: Multi-Instance Load Balancing




### FR-550: Setup




### FR-551: Run Unit Tests




### FR-552: Run Integration Tests




### FR-553: Run All Tests




### FR-554: Local Testing

✅


### FR-555: Configuration

✅


### FR-556: Verification

✅


### FR-557: Production Deployment

✅


### FR-558: Token Expiration

Auggie tokens are long-lived but may expire. Monitor logs for validation failures.


### FR-559: Model List Cache

1-hour TTL means new models may not be visible immediately.


### FR-560: Concurrent Limit

Default 5, can be adjusted but impacts resource usage.


### FR-561: Timeout

Some complex tasks may need timeout adjustment.


### FR-562: SQLite

Persistent local storage (routing decisions, policy cache, execution history)


### FR-563: Redis

High-speed caching layer (model scores, classification results, hot data)


### FR-564: NATS

Real-time event streaming (routing decisions, metrics, alerts)


### FR-565: Prompt Classification Cache

(`arch:{hash(prompt)}` → ArchRouterClassification)


### FR-566: Model Score Cache

(`mirt:{model_count}:{hash(features)}` → ScoreMap)


### FR-567: Executor Registry Cache

(`registry:executors` → [Model])


### FR-568: Routing Decision Cache

(`decision:{hash(prompt)}:{executor}` → SelectedModel)


### FR-569: routing.decision

→ Published for every routing decision


### FR-570: routing.cache

→ Published on cache hits/misses


### FR-571: health.status

→ Published every 30s by health worker


### FR-572: metrics.summary

→ Published every 60s


### FR-573: What We Have




### FR-574: What's Missing




### FR-575: 1. Redis Integration (High-Speed Caching)




### FR-576: 2. NATS Integration (Real-Time Event Streaming)




### FR-577: 3. SQLite Integration (Persistent Local Storage)




### FR-578: Phase 1: Redis Caching (Days 1-2)




### FR-579: Phase 2: NATS Events (Days 3-4)




### FR-580: Phase 3: SQLite Storage (Days 5-6)




### FR-581: Phase 4: Integration & Optimization (Days 7-8)




### FR-582: Microservice Framework

Complete with 6-state lifecycle, health checks, graceful shutdown


### FR-583: Redis/NATS Connections

Basic initialization and lifecycle management added


### FR-584: DualRouter Core

7-step routing pipeline with Arch-Router + MIRT-BERT


### FR-585: PostgreSQL Database

Used for initial data (can coexist with SQLite for specific purposes)


### FR-586: Redis Usage

No caching, no session management, no hot-data persistence


### FR-587: NATS Usage

No event publishing, no distributed messaging, no real-time monitoring


### FR-588: SQLite Usage

Not integrated at all (PostgreSQL is primary DB)


### FR-589: Disable Redis caching

Set `CacheEnabled: false` → routes bypass cache, use source directly


### FR-590: Disable NATS publishing

Set `NATSPublishAsync: false` → fail silently, routing continues


### FR-591: Disable SQLite logging

Set `SQLitePath: ""` → skip logging, routing unaffected


### FR-592: Unit Tests

Cache hits/misses, event publishing, SQLite queries


### FR-593: Integration Tests

Full routing pipeline with all three


### FR-594: Load Tests

Performance improvement measurement


### FR-595: Chaos Tests

Redis/NATS/SQLite failures → verify graceful degradation


### FR-596: Analytics Tests

SQLite query correctness


### FR-597: Accuracy

93.17% (outperforms Claude-Sonnet-3.7 by 7.71%)


### FR-598: Latency

51ms (28x faster than Claude-Sonnet-3.7)


### FR-599: Advantage

Decoupled route selection from model assignment


### FR-600: Relevance

Validates your 1.5B router approach + Domain-Action taxonomy


### FR-601: Savings: 300-425 LOC (67% reduction)

**New Total Custom Code**:


### FR-602: Option 1: sqlc (RECOMMENDED for your use case)




### FR-603: Option 2: GORM




### FR-604: Option 3: Ent




### FR-605: Option 4: Raw database/sql




### FR-606: Option 1: Terraform (RECOMMENDED)




### FR-607: Option 2: Pulumi




### FR-608: Option 3: Docker Compose (LIGHTWEIGHT)




### FR-609: With sqlc + sql-migrate + Terraform:




### FR-610: Database Layer




### FR-611: Infrastructure Layer




### FR-612: sqlc

for model registry queries


### FR-613: sql-migrate

for database migrations


### FR-614: Terraform

for production infrastructure


### FR-615: Docker Compose

for local development


### FR-616: Overall

99%


### FR-617: Pattern Detection

<100ms


### FR-618: Rule Generation

<50ms


### FR-619: Knowledge Graph Query

<10ms


### FR-620: Recommendation Lookup

<5ms


### FR-621: Learning Update

<500ms (hourly)


### FR-622: Code Written

~1390 LOC


### FR-623: Files Created

6


### FR-624: API Endpoints

8


### FR-625: Unit Tests

20


### FR-626: Test Coverage

99%+


### FR-627: Pattern Detection

<100ms


### FR-628: Rule Generation

<50ms


### FR-629: Week 9: Performance Tracking & Pattern Detection ✅




### FR-630: Week 10: Rule Generation & Knowledge Graph ✅




### FR-631: Code Files Created (~1390 LOC)




### FR-632: Learning Endpoints




### FR-633: 1. Performance Tracker




### FR-634: 2. Pattern Detector




### FR-635: 3. Rule Generator




### FR-636: 4. Knowledge Graph




### FR-637: 5. Learning System (Orchestration)




### FR-638: Unit Tests Created (20 tests)




### FR-639: Test Coverage




### FR-640: Record Performance




### FR-641: Get Detected Patterns




### FR-642: Get Generated Rules




### FR-643: Get Recommendations




### FR-644: Get Learning Stats




### FR-645: Pattern Detection




### FR-646: Rule Generation




### FR-647: Knowledge Graph




### FR-648: Learning Feedback




### FR-649: Semantic Router

Classify task type (tool_call, code_gen, reasoning, etc.)


### FR-650: RouteLLM

Optimize cost-quality trade-off


### FR-651: Fallback Chain

Execute provider-specific fallback rules


### FR-652: Caching

Cache routing decisions for <20ms latency


### FR-653: Gemini Strategy

Exponential backoff (0-10s), max 3 retries


### FR-654: Cerebras Strategy

Indefinite limit detection, 1m+ cooldown


### FR-655: Budget-Based

Track usage, throttle at 85%, block at 100%


### FR-656: Task-Specific

Tool calls prefer Claude/GPT-4, code gen prefers GPT-4


### FR-657: Language

Go 1.21+


### FR-658: Database

PostgreSQL 15 + pgvector + TimescaleDB


### FR-659: ORM

sqlc (SQL code generation)


### FR-660: Migrations

Goose


### FR-661: Caching

Redis


### FR-662: IaC

Pulumi (Go)


### FR-663: Routing

RouteLLM, Semantic Router


### FR-664: Language

Python 3.11+


### FR-665: ML

scikit-learn, pandas, numpy


### FR-666: Vector DB

pgvector (PostgreSQL)


### FR-667: Knowledge Graph

PostgreSQL recursive CTEs


### FR-668: Containerization

Docker


### FR-669: Local Dev

Docker Compose


### FR-670: Production

Pulumi + AWS


### FR-671: Monitoring

Prometheus + Grafana (optional)


### FR-672: Mitigation

Fallback chains, quality analysis, human review


### FR-673: Mitigation

Caching, rate limiting, monitoring


### FR-674: Mitigation

Validation, quality checks, feedback loops


### FR-675: Mitigation

Database optimization, caching, horizontal scaling


### FR-676: 1. Model Registry (PostgreSQL)




### FR-677: 2. Request Router (Go)




### FR-678: 3. Fallback Rules Engine (Go)




### FR-679: 4. Learning System (Python)




### FR-680: 5. Performance Tracker (PostgreSQL + TimescaleDB)




### FR-681: Backend




### FR-682: ML/Learning




### FR-683: DevOps




### FR-684: Phase 1: Foundation (Weeks 1-3) ✅ COMPLETE




### FR-685: Phase 2: Routing (Weeks 4-6)




### FR-686: Phase 3: Fallback Rules (Weeks 7-8)




### FR-687: Phase 4: Learning (Weeks 9-10)




### FR-688: Phase 5: Production (Weeks 11-12)




### FR-689: Go Code (~3350-4650 LOC)




### FR-690: Python Code (~2200-3150 LOC)




### FR-691: SQL Code (~100-150 LOC)




### FR-692: Infrastructure (~50-75 LOC)




### FR-693: Core Tables




### FR-694: Indexes




### FR-695: Model Management




### FR-696: Routing




### FR-697: Performance




### FR-698: Learning




### FR-699: Routing Accuracy




### FR-700: Cost Optimization




### FR-701: Learning Effectiveness




### FR-702: System Performance




### FR-703: Risk: Routing Errors




### FR-704: Risk: Performance Degradation




### FR-705: Risk: Data Quality




### FR-706: Risk: Scaling Issues




### FR-707: Week 4: Semantic Router Integration




### FR-708: Week 5: RouteLLM Integration




### FR-709: Week 6: Request Feature Extraction & Caching




### FR-710: Week 7: Provider-Specific Strategies




### FR-711: Week 8: Task-Specific Rules & Integration




### FR-712: Week 9: Performance Tracking & Pattern Detection




### FR-713: Week 10: Rule Generation & Knowledge Graph




### FR-714: Week 11: Infrastructure & Monitoring




### FR-715: Week 12: Testing & Deployment




### FR-716: Review

this comprehensive plan


### FR-717: Approve

the architecture and approach


### FR-718: Continue

with Phase 2 (Routing)


### FR-719: Follow

phase-by-phase breakdown


### FR-720: Deploy

to production


### FR-721: Your scale

<1M task embeddings ✅


### FR-722: Performance

Competitive with Qdrant at your scale


### FR-723: Recommendation

USE POSTGRES


### FR-724: Your scale

<10K model descriptions ✅


### FR-725: Performance

Excellent for your scale


### FR-726: Recommendation

USE POSTGRES


### FR-727: Your scale

<100K role-task-model relationships ✅


### FR-728: Performance

1.1s (faster than Neo4j's 3.4s in benchmarks)


### FR-729: Recommendation

USE POSTGRES


### FR-730: Your scale

<10M performance history points ✅


### FR-731: Performance

Excellent compression


### FR-732: Recommendation

USE POSTGRES


### FR-733: BEFORE (Complex Multi-Database)




### FR-734: AFTER (Simplified Single Database)




### FR-735: 1. Vector Search (pgvector)




### FR-736: 2. Full-Text Search (FTS)




### FR-737: 3. Graph Queries (Recursive CTEs)




### FR-738: 4. Time-Series Data (TimescaleDB)




### FR-739: With PostgreSQL Only (No Qdrant/Neo4j):




### FR-740: Year 1-2

PostgreSQL + extensions (current)


### FR-741: Year 2-3

Add Qdrant if vectors exceed 10M


### FR-742: Year 3+

Add Neo4j if graph nodes exceed 10M


### FR-743: Latency

500ms → 50ms (10x improvement)


### FR-744: Throughput

2 req/s → 50+ req/s (25x improvement)


### FR-745: Cache Hit Rate

0% → 60%


### FR-746: Connection Pool Efficiency

70%+


### FR-747: Unified Interface

Single API for all providers


### FR-748: Intelligent Routing

Optimal provider selection


### FR-749: Session Management

Multi-user support


### FR-750: Semantic Caching

80%+ hit rate on similar queries


### FR-751: Auto-Scaling

Automatic resource management


### FR-752: Multi-Region

Global failover capability


### FR-753: SLA

99.99% availability


### FR-754: Advanced Features

Enterprise-grade capabilities


### FR-755: Latency P95

< 100ms (target)


### FR-756: Throughput

> 100 req/s (target)


### FR-757: Cache Hit Rate

> 60% (target)


### FR-758: Availability

99.99% (target)


### FR-759: Error Rate

< 0.1%


### FR-760: Automatic Failover

< 1 second


### FR-761: Recovery Time

< 30 seconds


### FR-762: SLA Compliance

99.99%


### FR-763: CPU Usage

< 60% peak


### FR-764: Memory Usage

< 75% peak


### FR-765: Connection Pool Utilization

70%+


### FR-766: Cache Efficiency

60%+ hit rate


### FR-767: Module 1: Connection Pooling




### FR-768: Module 2: Response Caching




### FR-769: Module 3: SSE Streaming




### FR-770: Module 4: Unified Service Provider




### FR-771: Module 5: Intelligent Request Router




### FR-772: Module 6: Session Manager




### FR-773: Module 7: Semantic Cache




### FR-774: Module 8: Performance Tuning




### FR-775: Module 9: Advanced Routing Strategies




### FR-776: Module 10: Multi-Region Deployment




### FR-777: Module 11: Resource Limits & Monitoring




### FR-778: Module 12: Token Refresh & Model Discovery




### FR-779: Phase 2 Results




### FR-780: Phase 3 Results




### FR-781: Phase 4 Results




### FR-782: Phase 2 Integration




### FR-783: Phase 3 Integration




### FR-784: Phase 4 Integration




### FR-785: Phase 2 Testing




### FR-786: Phase 3 Testing




### FR-787: Phase 4 Testing




### FR-788: Pre-Deployment Checklist




### FR-789: Staging Deployment




### FR-790: Production Rollout




### FR-791: Performance Metrics




### FR-792: Reliability Metrics




### FR-793: Operational Metrics




### FR-794: Review

this roadmap


### FR-795: Approve

the implementation plan


### FR-796: Begin

Phase 2 implementation (Days 5-6)


### FR-797: Progress

through Phases 3-4 (Days 7-11)


### FR-798: Deploy

to staging (Day 12)


### FR-799: Validate

performance targets


### FR-800: Release

to production


### FR-801: Fallback Latency

<50ms


### FR-802: Rate Limit Detection

Immediate


### FR-803: Indefinite Limit Detection

5 attempts (Cerebras)


### FR-804: Budget Tracking

Real-time


### FR-805: Task Rule Lookup

<1ms


### FR-806: Code Written

~1380 LOC


### FR-807: Files Created

8


### FR-808: API Endpoints

6


### FR-809: Unit Tests

15


### FR-810: Test Coverage

95%+


### FR-811: Fallback Latency

<50ms


### FR-812: Week 7: Provider-Specific Strategies ✅




### FR-813: Week 8: Task-Specific Rules & Integration ✅




### FR-814: Code Files Created (~1380 LOC)




### FR-815: Fallback Endpoints




### FR-816: 1. Gemini Fallback Strategy




### FR-817: 2. Cerebras Fallback Strategy




### FR-818: 3. Budget-Based Fallback




### FR-819: 4. Task-Specific Rules




### FR-820: 5. Fallback Engine




### FR-821: Unit Tests Created (15 tests)




### FR-822: Test Coverage




### FR-823: Execute Fallback




### FR-824: Get Fallback Chain




### FR-825: Get Task Rules




### FR-826: Get Strategy Info




### FR-827: Gemini (Exponential Backoff)




### FR-828: Cerebras (Indefinite Detection)




### FR-829: Budget-Based




### FR-830: Task-Specific Rules




### FR-831: Auggie

❌ NO native streaming support - returns 501 (Not Implemented)


### FR-832: Cursor Agent

❌ Currently BLOCKS streaming - returns 501 (Not Implemented)


### FR-833: GeminiCLI

✅ FULL streaming support via Server-Sent Events (SSE)


### FR-834: Solution Needed

Implement streaming workaround for Auggie; enable Cursor Agent streaming


### FR-835: Status

Fully implemented


### FR-836: Method

Spawns local Auggie CLI subprocess via `exec.CommandContext`


### FR-837: Flow

1. Translates OpenAI-compatible request to Auggie JSON format


### FR-838: Current

Hard-coded 501 Not Implemented error


### FR-839: Issue

Auggie CLI itself may not support streaming output format


### FR-840: Evidence

No streaming-specific CLI flags documented (like `--output-format stream-json`)


### FR-841: 1. AugieExecutor (`internal/runtime/executor/auggie_executor.go`)




### FR-842: 2. CursorAgentExecutor (`internal/runtime/executor/cursor_agent_executor.go`)




### FR-843: 3. GeminiCLIExecutor (`internal/runtime/executor/gemini_cli_executor.go`)




### FR-844: Why Auggie Doesn't Support Streaming




### FR-845: Why Cursor Agent SHOULD Support Streaming




### FR-846: Strategy A: Chunked Emission Workaround for Auggie




### FR-847: Strategy B: Streaming Response Format Negotiation




### FR-848: Strategy C: Process Stdout Line Buffering




### FR-849: Phase 1: Enable Cursor Agent Streaming (Quick Win) ✅




### FR-850: Phase 2: Implement Auggie Streaming Workaround




### FR-851: Phase 3: Pre-Research (Optional)




### FR-852: Cursor Agent Streaming (Phase 1)




### FR-853: Auggie Streaming (Phase 2)




### FR-854: For Auggie




### FR-855: For Cursor Agent




### FR-856: CLI-based architecture

Spawns subprocess, limited by Auggie CLI capabilities


### FR-857: Response format

Only supports JSON output (`--output-format json`)


### FR-858: No streaming flags

Unlike cursor-agent, no `--stream` or `--output-format stream-json` flag present


### FR-859: Full buffering

Current implementation buffers entire response before returning


### FR-860: ExecuteStream delegates to Execute()

with `opts.Stream = true`


### FR-861: Execute() then checks opts.Stream and rejects it

with 501


### FR-862: Result

Circular rejection - streaming is hardcoded as unsupported


### FR-863: Auggie CLI Architecture

Subprocess-based, not server-based


### FR-864: No Streaming Output Format

- Auggie CLI only supports `--output-format json` (batch)


### FR-865: Subprocess Limitations

- Cannot spawn incrementally flushed JSON chunks


### FR-866: CLI Supports It

`--output-format stream-json` flag exists


### FR-867: Response Parser Ready

`streamCursorAgentOutput()` method fully implemented


### FR-868: OpenAI Conversion Ready

Builds proper OpenAI streaming chunks


### FR-869: Only Blocker

Hardcoded 501 rejection in Execute()


### FR-870: Word-based

Split on whitespace boundaries (natural)


### FR-871: Token-based

Use token counter if available


### FR-872: Sentence-based

Split on `.!?` followed by space


### FR-873: Fixed-size

Simple character count threshold


### FR-874: Remove hardcoded 501 in Execute()

```go


### FR-875: Route to streaming handler

```go


### FR-876: Fix ExecuteStream delegation

```go


### FR-877: Lines of Code:

1,850+ (production-ready)


### FR-878: Components:

7 core modules


### FR-879: Database Tables:

8 new tables with indices


### FR-880: Tests:

Unit + benchmark tests included


### FR-881: Documentation:

3 comprehensive guides


### FR-882: Baseline

(always GPT-4): $5.00/1M tokens


### FR-883: Random Selection

$3.00/1M tokens


### FR-884: RouteLLM

$2.50/1M tokens


### FR-885: MIRT (expected)

$2.20/1M tokens


### FR-886: Expected Savings

27-56% cost reduction


### FR-887: ✅ Phase 1: Architecture Design




### FR-888: ✅ Phase 2: Database Schema




### FR-889: ✅ Phase 3: Core Go Implementation




### FR-890: ✅ Phase 4: Testing & Documentation




### FR-891: ⏳ Phase 5: MLX-LM Server Integration




### FR-892: ⏳ Phase 6: MIRT Checkpoint Integration




### FR-893: ⏳ Phase 7: Vibeproxy UI Integration




### FR-894: ⏳ Phase 8: Production Deployment




### FR-895: Routing Process Flow




### FR-896: Feature Dimensions (25 Total)




### FR-897: IRT Formula




### FR-898: Database Schema




### FR-899: Lines of Code (Production-Ready)




### FR-900: Test Coverage




### FR-901: Documentation




### FR-902: Latency Breakdown




### FR-903: Cost Projections




### FR-904: Accuracy Projections




### FR-905: High Priority Risks




### FR-906: Medium Priority Risks




### FR-907: Low Priority Risks




### FR-908: Runtime Dependencies




### FR-909: External Services




### FR-910: Week 2: MLX-LM Integration




### FR-911: Week 3: Vibeproxy UI




### FR-912: Week 4: Testing & Optimization




### FR-913: Week 5: Production Rollout




### FR-914: Functional Requirements




### FR-915: Performance Requirements




### FR-916: Quality Requirements




### FR-917: MLX-LM Server Stability

- Risk: Server crashes or OOM


### FR-918: MIRT Checkpoint Compatibility

- Risk: Checkpoint version mismatch


### FR-919: Feature Extraction Accuracy

- Risk: Heuristic rules inaccurate for edge cases


### FR-920: Latency Impact

- Risk: Total routing > 100ms


### FR-921: Database Lock Contention

- Risk: High-traffic scenarios cause bottlenecks


### FR-922: Policy Configuration Errors

- Risk: Incorrect domain-action mappings


### FR-923: Metrics Collection

<1ms


### FR-924: Health Check

<50ms


### FR-925: Logging

<5ms


### FR-926: API Response

<100ms


### FR-927: Database Query

<50ms


### FR-928: Cache Hit

<10ms


### FR-929: Code Written

~550 LOC


### FR-930: Files Created

3


### FR-931: API Endpoints

6 + 3 Kubernetes probes


### FR-932: Monitoring Components

3


### FR-933: Infrastructure Modules

1


### FR-934: Documentation

1 comprehensive guide


### FR-935: Week 11: Infrastructure & Monitoring ✅




### FR-936: Week 12: Testing & Deployment ✅




### FR-937: Code Files Created (~550 LOC)




### FR-938: Monitoring Endpoints




### FR-939: Kubernetes Probes




### FR-940: 1. Metrics Collection




### FR-941: 2. Structured Logging




### FR-942: 3. Health Checks




### FR-943: 4. Pulumi Infrastructure




### FR-944: 5. Deployment Guide




### FR-945: End-to-End Tests




### FR-946: Load Testing




### FR-947: Security Testing




### FR-948: Sub-1ms latency

for hot classification/scoring


### FR-949: Session management

across distributed instances


### FR-950: Pub/Sub coordination

between services


### FR-951: Request deduplication

(cache recent decisions)


### FR-952: Feature caching

(extracted 25D vectors)


### FR-953: ACID guarantees

for critical data


### FR-954: Time-series analysis

via TimescaleDB


### FR-955: Vector similarity search

via pgvector


### FR-956: Full-text search

for semantic matching


### FR-957: Audit trail

and compliance


### FR-958: Policy rules storage

(domain/action/model relationships)


### FR-959: Learning inference

(infer new routing patterns)


### FR-960: Fallback chains

(variable-length dynamic traversal)


### FR-961: Pattern matching

(find implicit relationships)


### FR-962: Rule engine

(apply business logic)


### FR-963: Real-time observability

(publish routing decisions)


### FR-964: Multi-service coordination

(request-reply pattern)


### FR-965: Event replay

(persistent streams)


### FR-966: Cache invalidation

(distribute updates)


### FR-967: Learning signals

(publish patterns)


### FR-968: Redis

Hot caching for sub-1ms lookups


### FR-969: PostgreSQL

ACID record store + pgvector for semantic search (NO Qdrant needed)


### FR-970: Neo4j

Policy graph + learning inference + dynamic fallback chains


### FR-971: NATS

Real-time events for observability and coordination


### FR-972: Purpose




### FR-973: Data Structures Used




### FR-974: Implementation in Go




### FR-975: Configuration




### FR-976: Performance Impact




### FR-977: Purpose




### FR-978: Schema Enhancements




### FR-979: Query Patterns




### FR-980: Optimization Settings




### FR-981: Backup & Recovery




### FR-982: Purpose




### FR-983: Graph Model




### FR-984: Query Patterns




### FR-985: Implementation in Go




### FR-986: Purpose




### FR-987: Topic Structure




### FR-988: Event Schemas




### FR-989: Implementation in Go




### FR-990: Configuration




### FR-991: Decision: Keep pgvector, Don't Add Qdrant




### FR-992: pgvector Implementation Details




### FR-993: Data Flow Diagram




### FR-994: Sync Diagram: How Layers Talk




### FR-995: Phase 1: Redis Caching (Weeks 1-2, 16 hours)




### FR-996: Phase 2: PostgreSQL Optimization (Weeks 3-4, 12 hours)




### FR-997: Phase 3: Neo4j Implementation (Weeks 5-7, 24 hours)




### FR-998: Phase 4: NATS Event Streaming (Weeks 8-9, 12 hours)




### FR-999: Phase 5: Integration & Optimization (Weeks 10-11, 16 hours)




### FR-1000: docker-compose.full-stack.yml (Enhanced)




### FR-1001: Performance Baselines




### FR-1002: Dashboards (Grafana)




### FR-1003: Alerts




### FR-1004: Setup Redis locally

(2 hours)


### FR-1005: Implement Redis cache layer

(4 hours)


### FR-1006: Integration with DualRouter

(5 hours)


### FR-1007: Testing & Performance

(5 hours)


### FR-1008: Index tuning

(3 hours)


### FR-1009: Full-text search

(3 hours)


### FR-1010: Advanced queries

(4 hours)


### FR-1011: Optimization

(2 hours)


### FR-1012: Setup Neo4j

(3 hours)


### FR-1013: Graph schema design

(4 hours)


### FR-1014: Policy engine implementation

(8 hours)


### FR-1015: Learning integration

(6 hours)


### FR-1016: Testing & validation

(3 hours)


### FR-1017: Setup NATS

(2 hours)


### FR-1018: Event publishing

(5 hours)


### FR-1019: Subscriptions

(3 hours)


### FR-1020: Testing

(2 hours)


### FR-1021: Full-stack integration

(6 hours)


### FR-1022: Performance optimization

(5 hours)


### FR-1023: Learning system maturation

(3 hours)


### FR-1024: Documentation & monitoring

(2 hours)


### FR-1025: Request Metrics

- Latency (P50/P95/P99)


### FR-1026: Cache Performance

- Hit rate by cache type


### FR-1027: Neo4j Performance

- Query response time


### FR-1028: System Health

- Redis memory usage


### FR-1029: Embedding Model

All-MiniLM-L6-v2 (sentence-transformers) for semantic matching


### FR-1030: Python Execution

Sandboxed via V8 isolates or Docker


### FR-1031: Caching

Redis (existing infrastructure)


### FR-1032: Logging

Structured logging with tool execution details


### FR-1033: MCP Implementation

Go-based server supporting stdio + HTTP


### FR-1034: 1.1 Tool Discovery Service




### FR-1035: 1.2 Tool Schema Registry




### FR-1036: 1.3 Tool Validation




### FR-1037: 2.1 Tool Filtering Strategies




### FR-1038: 2.2 Mid-Prompt Tool Recommendation




### FR-1039: 3.1 Safe Python DSL Executor




### FR-1040: 3.2 Tool Orchestrator




### FR-1041: 4.1 `/v1/tools` Endpoints




### FR-1042: 5.1 Expose Tools as MCP Server




### FR-1043: For Claude Code Users:




### FR-1044: For Tool Chaining (Programmatic):




### FR-1045: Tool Execution Approval




### FR-1046: Input Sanitization




### FR-1047: Output Filtering




### FR-1048: MCP Servers

- Scan configured MCP servers


### FR-1049: Internal API Tools

- Routes in `/v1/*` endpoints


### FR-1050: Runtime Tool Detection

- Monitor file system for tool definitions


### FR-1051: 1. Vector Search (pgvector)




### FR-1052: 2. Full-Text Search (FTS)




### FR-1053: 3. Graph Queries (Knowledge Graph)




### FR-1054: 4. Time-Series Data (Performance History)




### FR-1055: Extensions to Install




### FR-1056: Schema Design




### FR-1057: GitHub

`lm-sys/RouteLLM`


### FR-1058: Status

Production-ready, ICLR 2025 published


### FR-1059: Features

Cost-quality trade-off routing, trained routers, evaluation framework


### FR-1060: Use

Core routing logic, cost optimization


### FR-1061: Integration

Python library, can wrap in gRPC


### FR-1062: GitHub

`aurelio-labs/semantic-router`


### FR-1063: Status

Active, v0.1.9+ (June 2025)


### FR-1064: Features

Vector-based routing, fast decision-making, multi-modal support


### FR-1065: Use

Task classification, semantic matching


### FR-1066: Integration

Python, supports LangChain/LlamaIndex


### FR-1067: GitHub

`Not-Diamond/awesome-ai-model-routing`


### FR-1068: Status

Curated list of routing solutions


### FR-1069: Value

Reference for 20+ routing approaches


### FR-1070: Website

`litellm.ai`


### FR-1071: GitHub

`BerriAI/litellm`


### FR-1072: Status

Production-ready, widely adopted


### FR-1073: Features

100+ providers, cost tracking, load balancing, proxy server


### FR-1074: Use

Provider abstraction, budget tracking, rate limit handling


### FR-1075: Integration

Python SDK + proxy server (can run separately)


### FR-1076: GitHub

`NVIDIA-AI-Blueprints/llm-router`


### FR-1077: Features

Flexible routing policies, fine-tunable routers


### FR-1078: Use

Alternative routing framework


### FR-1079: GitHub

`ml-explore/mlx`


### FR-1080: Status

Official Apple framework, actively maintained


### FR-1081: Features

Optimized for Apple Silicon, Python API, C++/Swift support


### FR-1082: Use

Local 1.5B router inference


### FR-1083: Integration

Python library, can expose via gRPC


### FR-1084: GitHub

`ml-explore/mlx-lm`


### FR-1085: Status

High-level library for MLX


### FR-1086: Features

Model loading, generation, fine-tuning


### FR-1087: Use

Simplified MLX model management


### FR-1088: Website

`ollama.com`


### FR-1089: GitHub

`ollama/ollama`


### FR-1090: Status

Production-ready, easy deployment


### FR-1091: Features

OpenAI-compatible API, model management


### FR-1092: Use

Alternative to MLX for local inference


### FR-1093: GitHub

`vllm-project/vllm`


### FR-1094: Status

Production-ready, high-throughput


### FR-1095: Features

Fast inference, memory efficient, distributed serving


### FR-1096: Use

High-performance inference alternative


### FR-1097: GitHub

`open-compass/opencompass`


### FR-1098: Status

Production-ready, comprehensive


### FR-1099: Features

MMLU, SWEBENCH, GAIA, 100+ benchmarks, leaderboard


### FR-1100: Use

Benchmark evaluation, data collection


### FR-1101: Integration

Python framework


### FR-1102: GitHub

`EleutherAI/lm-evaluation-harness`


### FR-1103: Status

Widely used, comprehensive


### FR-1104: Features

Few-shot evaluation, multiple benchmarks


### FR-1105: Use

Benchmark evaluation framework


### FR-1106: GitHub

`huggingface/datasets`, `huggingface/evaluate`


### FR-1107: Status

Standard library


### FR-1108: Features

Dataset loading, evaluation metrics


### FR-1109: Use

Benchmark data access, metric computation


### FR-1110: GitHub

`lmarena/arena-hard-auto`


### FR-1111: Status

Active


### FR-1112: Features

Automatic LLM benchmarking


### FR-1113: Use

Benchmark automation


### FR-1114: Website

`qdrant.tech`


### FR-1115: GitHub

`qdrant/qdrant`


### FR-1116: Status

Production-ready, Rust-based


### FR-1117: Features

High-performance, Go client available, REST API


### FR-1118: Use

Semantic task matching, embeddings storage


### FR-1119: Integration

Go client + REST API


### FR-1120: Website

`milvus.io`


### FR-1121: GitHub

`milvus-io/milvus`


### FR-1122: Status

Production-ready, scalable


### FR-1123: Features

High-performance, distributed


### FR-1124: Use

Alternative vector DB


### FR-1125: GitHub

`philippgille/chromem-go`


### FR-1126: Status

Embeddable, Go-native


### FR-1127: Features

In-process vector DB, no external dependencies


### FR-1128: Use

Lightweight alternative for smaller deployments


### FR-1129: Website

`neo4j.com`


### FR-1130: Status

Production-ready, enterprise-grade


### FR-1131: Features

Go driver available, graph algorithms, GDS library


### FR-1132: Use

Role-task-model relationships


### FR-1133: Integration

Official Go driver


### FR-1134: Website

`memgraph.com`


### FR-1135: Status

Neo4j-compatible, lighter-weight


### FR-1136: Features

Go client available


### FR-1137: Use

Alternative to Neo4j


### FR-1138: GitHub

`hashicorp/go-retryablehttp`


### FR-1139: Status

Production-ready, widely used


### FR-1140: Features

Exponential backoff, configurable retries


### FR-1141: Use

HTTP retry logic for provider calls


### FR-1142: Integration

Go library


### FR-1143: GitHub

`cenkalti/backoff`


### FR-1144: Status

Production-ready, v5 latest


### FR-1145: Features

Exponential backoff algorithm, configurable


### FR-1146: Use

Generic backoff implementation


### FR-1147: Integration

Go library


### FR-1148: Website

`spacy.io`


### FR-1149: GitHub

`explosion/spacy`


### FR-1150: Status

Production-ready, industry standard


### FR-1151: Features

NER, text classification, fast


### FR-1152: Use

Task classification, prompt analysis


### FR-1153: Integration

Python library


### FR-1154: GitHub

`flairNLP/flair`


### FR-1155: Status

Active, state-of-the-art models


### FR-1156: Features

Sequence labeling, text classification


### FR-1157: Use

Alternative NLP framework


### FR-1158: Website

`sbert.net`


### FR-1159: GitHub

`UKPLab/sentence-transformers`


### FR-1160: Status

Production-ready, widely used


### FR-1161: Features

Semantic embeddings, pre-trained models


### FR-1162: Use

Task embeddings for semantic matching


### FR-1163: Integration

Python library


### FR-1164: GitHub

`sqlc-dev/sqlc`


### FR-1165: Status

Production-ready, Go-native


### FR-1166: Features

Type-safe SQL code generation


### FR-1167: Use

PostgreSQL queries for model registry


### FR-1168: Integration

Go code generation tool


### FR-1169: GitHub

`go-jet/jet`


### FR-1170: Status

Production-ready


### FR-1171: Features

Type-safe SQL builder


### FR-1172: Use

Alternative to sqlc


### FR-1173: GitHub

`pydantic/pydantic-ai`


### FR-1174: Status

Production-ready, modern


### FR-1175: Features

Type-safe agents, LiteLLM integration


### FR-1176: Use

Response quality analysis agent


### FR-1177: Integration

Python framework


### FR-1178: Website

`grpc.io`


### FR-1179: Status

Industry standard


### FR-1180: Features

Multi-language support, high-performance


### FR-1181: Use

Go-Python bridge for MLX router


### FR-1182: Integration

Protocol Buffers + code generation


### FR-1183: RouteLLM (RECOMMENDED)




### FR-1184: Semantic Router (RECOMMENDED)




### FR-1185: Not-Diamond Awesome Routing




### FR-1186: LiteLLM (CRITICAL)




### FR-1187: NVIDIA LLM Router




### FR-1188: MLX (RECOMMENDED for Apple Silicon)




### FR-1189: MLX-LM




### FR-1190: Ollama (ALTERNATIVE)




### FR-1191: vLLM (ALTERNATIVE)




### FR-1192: OpenCompass (RECOMMENDED)




### FR-1193: EleutherAI LM Evaluation Harness




### FR-1194: HuggingFace Datasets & Evaluate




### FR-1195: Arena-Hard-Auto




### FR-1196: Qdrant (RECOMMENDED)




### FR-1197: Milvus (ALTERNATIVE)




### FR-1198: Chromem-Go (LIGHTWEIGHT)




### FR-1199: Neo4j (RECOMMENDED)




### FR-1200: Memgraph (ALTERNATIVE)




### FR-1201: HashiCorp go-retryablehttp (RECOMMENDED)




### FR-1202: cenkalti/backoff (RECOMMENDED)




### FR-1203: spaCy (RECOMMENDED)




### FR-1204: Flair (ALTERNATIVE)




### FR-1205: Sentence-Transformers (RECOMMENDED)




### FR-1206: sqlc (RECOMMENDED)




### FR-1207: go-jet (ALTERNATIVE)




### FR-1208: Pydantic AI (RECOMMENDED)




### FR-1209: gRPC (STANDARD)




### FR-1210: Key Papers on LLM Routing




### FR-1211: Phase 1: Foundation




### FR-1212: Phase 2: Routing




### FR-1213: Phase 3: Data




### FR-1214: Phase 4: Learning




### FR-1215: Phase 5: Integration




### FR-1216: RouteLLM

(ICLR 2025): `arxiv.org/pdf/2406.18665`


### FR-1217: Dynamic LLM Routing

(Feb 2025): `arxiv.org/abs/2502.16696`


### FR-1218: IPR: Intelligent Prompt Routing

(2025): `arxiv.org/pdf/2509.06274`


### FR-1219: Toward Super Agent System

(Apr 2025): `arxiv.org/html/2504.10519v1`


### FR-1220: InferenceDynamics

(May 2025): `arxiv.org/html/2505.16303v1`


### FR-1221: Learning to Route

(Oct 2025): `arxiv.org/html/2510.02388v1`


### FR-1222: Evaluate

RouteLLM + Semantic Router for routing


### FR-1223: Integrate

LiteLLM for provider abstraction


### FR-1224: Setup

MLX or Ollama for local inference


### FR-1225: Configure

OpenCompass for benchmarks


### FR-1226: Deploy

Qdrant + Neo4j for data storage


### FR-1227: Build

gRPC bridge for Go-Python communication


### FR-1228: Create tasks.md:

```markdown



## 7. Non-Functional Requirements


## 8. Features

### 🟡 Accuracy:

93.17%


### 🟡 Latency:

50ms


### 🟡 Output:

Domain + Action (e.g., "programming/code-generation")


### 🟡 Input:

User prompt + context


### 🟡 Abilities:

25-dimensional latent space per model


### 🟡 Formula:

P(success) = sigmoid(∑ a_i · (θ_i - b_i))


### 🟡 Features:

25-dimensional difficulty vector from prompt


### 🟡 Score:

P(success) / cost_per_token


### 🟡 Latency:

15-30ms


### 🟡 For Users Who Want to Get Started




### 🟡 For Developers Who Want to Understand the Code




### 🟠 High-Level Flow




### 🟡 Component Breakdown




### 🟡 Documentation




### 🟡 Source Code




### 🟡 Database




### 🟡 Arch-Router (Task Classification)




### 🟡 MIRT-BERT (Cost-Quality Prediction)




### 🟡 ExecutorRegistry (Model Unification)




### 🟡 FeatureExtractor (Query Analysis)




### 🟡 1. Install Dependencies




### 🟡 2. Set up Database




### 🟡 3. Start MLX-LM Server




### 🟡 4. Run Tests




### 🟡 5. Integrate into CLIProxyAPI




### 🟡 Basic Usage




### 🟡 Testing Components Individually




### 🟡 DualRouter




### 🟡 ExecutorRegistry




### 🟡 MIRT Client




### 🟡 FeatureExtractor




### 🟡 Expected Latency




### 🟡 Run Benchmarks




### 🟡 MLX-LM Server Not Responding




### 🟡 MIRT Checkpoint Not Loading




### 🟡 Feature Extraction Too Slow




### 🟡 Unit Tests




### 🟡 Integration Tests (Pending)




### 🟡 Week 2: MLX-LM Integration




### 🟡 Week 3: Vibeproxy UI




### 🟡 Week 4: Testing & Optimization




### 🟡 Week 5: Production




### 🟡 For Technical Questions




### 🟡 For Integration Issues




### 🟡 For Performance Issues




### 🟡 Read the Overview

→ [DUAL_ROUTER_WEEK1_IMPLEMENTATION.md](./DUAL_ROUTER_WEEK1_IMPLEMENTATION.md)


### 🟡 Follow Setup Guide

→ [DUAL_ROUTER_SETUP_GUIDE.md](./DUAL_ROUTER_SETUP_GUIDE.md)


### 🟡 Check Status

→ [DUAL_ROUTER_IMPLEMENTATION_STATUS.md](./DUAL_ROUTER_IMPLEMENTATION_STATUS.md)


### 🟡 Architecture Review

→ See "System Architecture" below


### 🟡 Code Tour

→ Start with `internal/router/dual_router.go`


### 🟡 Run Tests

→ `go test ./internal/router/... -v`


### 🟡 Check Examples

→ See "Integration Examples" below


### 🟡 Tools Used

LS, Read, Grep tools


### 🟡 Files Analyzed

go.mod, go.sum, README, config.example.yaml, Docker, internal packages


### 🟡 Output

Comprehensive tech stack inventory and architecture map


### 🟡 Cursor Agent

3 official documentation pages fetched


### 🟡 Auggie CLI

3 official documentation pages fetched


### 🟡 Total Sources

6+ official docs, 15+ web research sources


### 🟡 MCP Architecture

Mapped transport methods, capabilities, security models


### 🟡 ACP Protocol

Reviewed Agent Client Protocol standards


### 🟡 CLI Features

Documented all flags, modes, and configurations


### 🟡 Tool Design

Proposed 5 major MCP tools for each CLI


### 🟡 Implementation Phases

4-phase roadmap for each integration


### 🟡 Use Cases

Real-world examples for automation and development


### 🟡 Project Context

`agileplus/project.md`


### 🟡 Cursor Agent Research

`docs/cursor-agent-research.md`


### 🟡 Auggie CLI Research

`docs/auggie-cli-research.md`


### 🟡 This Summary

`docs/RESEARCH_SUMMARY.md`


### 🟡 Total Words Written

12,000+


### 🟡 Code Examples Provided

70+


### 🟡 Tables Created

30+


### 🟡 Research Sources

25+


### 🟡 Hours of Research

~8 hours of focused research


### 🟡 1. Project Context Document




### 🟡 2. Cursor Agent CLI Research




### 🟡 3. Auggie CLI Research




### 🟡 Phase 1: Codebase Analysis




### 🟡 Phase 2: Official Documentation Review




### 🟡 Phase 3: Integration Analysis




### 🟡 Phase 4: Opportunity Identification




### 🟡 About CLIProxyAPI




### 🟡 About Cursor Agent CLI




### 🟡 About Auggie CLI




### 🟡 Integration Opportunities




### 🟡 For AI Assistants (Auggie, Cursor Agent)




### 🟡 For Team Planning




### 🟡 For Community Engagement




### 🟡 Step 1: Team Review (This Week)




### 🟡 Step 2: Proposal Creation (Next Week)




### 🟡 Step 3: Proof of Concept (Weeks 3-4)




### 🟡 Step 4: Implementation (Weeks 5+)




### 🟡 File Locations




### 🟡 Key Statistics




### 🟡 Installation Commands (For Reference)




### 🟡 Quick MCP Overview




### 🟡 Complete Project Context

- Documented conventions, architecture, constraints


### 🟡 Cursor Agent CLI Research

- Integration opportunities via MCP servers


### 🟡 Auggie CLI Research

- Automation and CI/CD integration possibilities


### 🟡 CLIProxyAPI Integration Opportunities

- Vision: Why combine them?


### 🟡 CLIProxyAPI Integration Opportunities

- Vision: Automation and CI/CD focus


### 🟡 Project Onboarding

Reference `agileplus/project.md` for new contributors


### 🟡 Feature Proposals

Use MCP tool designs from research documents


### 🟡 Architecture Decisions

Reference integration patterns from both CLIs


### 🟡 Implementation Roadmaps

Follow 4-phase approach from each research doc


### 🟡 GitHub Issues

Link to research for context on feature requests


### 🟡 PRs

Reference conventions from `project.md`


### 🟡 Discussions

Share research findings for feedback


### 🟡 Documentation

Incorporate findings into official docs


### 🟡 Understands code deeply

- Indexes entire codebases automatically


### 🟡 Executes tools

- Runs shell commands, reads/writes files, uses MCP tools


### 🟡 Integrates everywhere

- Works in standalone terminal, CI/CD, ACP editors


### 🟡 Automates tasks

- Designed for code reviews, issue triage, monitoring, exception handling


### 🟡 Runtime

Node.js 22.x or later


### 🟡 Shell

zsh, bash, or fish


### 🟡 Platforms

macOS, Linux, Windows (WSL)


### 🟡 Authentication

Augment account (free tier available for beta)


### 🟡 Network

Optional (works offline with cached context)


### 🟡 Tools

- Functions agent can call


### 🟡 Resources

- Structured data sources


### 🟡 Prompts

- Pre-built workflows


### 🟡 Roots

- Filesystem/URI boundary checks


### 🟡 Elicitation

- Server-initiated information requests


### 🟡 Universal access

- Same Auggie instance across editors


### 🟡 Consistent behavior

- Same tools and context everywhere


### 🟡 Easy deployment

- Single binary, works in any ACP editor


### 🟡 No custom integration

- Standard ACP protocol handling


### 🟡 Auggie CLI Overview

https://docs.augmentcode.com/cli/overview


### 🟡 CLI Reference

https://docs.augmentcode.com/cli/reference


### 🟡 Integrations & MCP

https://docs.augmentcode.com/cli/integrations


### 🟡 Automation

https://docs.augmentcode.com/cli/automation


### 🟡 ACP Clients

https://docs.augmentcode.com/cli/acp/clients


### 🟡 GitHub Repository

https://github.com/augmentcode/auggie


### 🟡 NPM Package

https://www.npmjs.com/package/@augmentcode/auggie


### 🟡 Blog

https://www.augmentcode.com/blog


### 🟡 MCP Directory

https://www.augmentcode.com/mcp/


### 🟡 ACP Spec

https://agentclientprotocol.com/


### 🟡 MCP Protocol

https://modelcontextprotocol.io/


### 🟡 Augment Code Docs

https://docs.augmentcode.com/


### 🟡 Key Findings




### 🟡 1.1 What is Auggie CLI?




### 🟡 1.2 Core Architecture




### 🟡 1.3 System Requirements




### 🟡 2.1 Interactive Mode




### 🟡 2.2 Print Mode (Automation)




### 🟡 2.3 Quiet Mode




### 🟡 2.4 Compact Mode




### 🟡 2.5 Custom Commands




### 🟡 2.6 Session Management




### 🟡 2.7 Configuration & Customization




### 🟡 3.1 MCP Architecture in Auggie




### 🟡 3.2 MCP Transport Methods




### 🟡 3.3 Configuring MCP Servers




### 🟡 3.4 MCP Capabilities in Auggie




### 🟡 3.5 MCP Overrides




### 🟡 4.1 What is ACP?




### 🟡 4.2 Using Auggie with ACP Editors




### 🟡 4.3 ACP Benefits for CLIProxyAPI Integration




### 🟡 5.1 Supported Native Integrations




### 🟡 5.2 Using Integrations in Commands




### 🟡 6.1 Vision: Why Auggie CLI + CLIProxyAPI?




### 🟡 6.2 Proposed MCP Server Architecture




### 🟡 6.3 Proposed MCP Tools for CLIProxyAPI




### 🟡 6.4 Example Auggie Commands with CLIProxyAPI MCP




### 🟡 6.5 Implementation Phases




### 🟡 7.1 GitHub Actions Integration




### 🟡 7.2 CLI Scripts




### 🟡 7.3 Pipe-based Workflows




### 🟡 7.4 Pre-commit Hooks




### 🟡 8.1 Authentication




### 🟡 8.2 MCP Server Security




### 🟡 8.3 Integration with CLIProxyAPI Security




### 🟡 Key Differentiator




### 🟡 Official Documentation




### 🟡 Community Resources




### 🟡 Related Standards




### 🟡 For CLIProxyAPI Maintainers




### 🟡 For Integration Explorers




### 🟡 Community Engagement




### 🟡 Recommended Path Forward




### 🟡 Review this research

Assess alignment with project roadmap


### 🟡 Create AgilePlus proposal

Formalize MCP server feature


### 🟡 Design MCP interface

Define tool set and security model


### 🟡 Prototype

Build minimal MCP server for proof-of-concept


### 🟡 Test with Auggie

Verify integration works end-to-end


### 🟡 Gather feedback

Community input on proposed tools


### 🟡 Implement

Execute in phases from section 6.5


### 🟡 Install Auggie CLI

`npm install -g @augmentcode/auggie`


### 🟡 Login

`auggie login`


### 🟡 Explore

`auggie "Analyze the CLIProxyAPI codebase"`


### 🟡 Test MCP

Configure a custom `.augment/settings.json`


### 🟡 Create command

Write a custom Auggie command for CLIProxyAPI


### 🟡 Provide feedback

Share findings with team


### 🟡 Better Automation

- Native support in CI/CD and scripting


### 🟡 Natural Language Management

- Conversational provider control


### 🟡 Enterprise Features

- Audit logging, multi-tenant support


### 🟡 Community Alignment

- Both embrace open standards (MCP, ACP)


### 🟡 Novel Use Cases

- Enable scenarios previously impossible


### 🟡 Short term

(1-2 weeks): Create AgilePlus proposal


### 🟡 Medium term

(3-4 weeks): Prototype core MCP tools


### 🟡 Long term

(2+ months): Production release with CI/CD examples


### 🟡 Cursor CLI Overview

https://cursor.com/docs/cli/overview


### 🟡 Using Agent in CLI

https://cursor.com/docs/cli/using


### 🟡 MCP in Cursor

https://cursor.com/docs/context/mcp


### 🟡 Building MCP Servers

https://cursor.com/docs/cookbook/building-mcp-server


### 🟡 MCP Protocol Spec

https://modelcontextprotocol.io/introduction


### 🟡 MCP Directory

https://cursor.com/docs/context/mcp/directory


### 🟡 Cursor Blog

https://cursor.com/blog/cli (Release announcement)


### 🟡 Smithery MCP Hub

https://smithery.ai/ (MCP server directory)


### 🟡 Example MCP Servers

https://github.com/msfeldstein/mcp-test-servers


### 🟡 CursorMCP Hub

https://cursormcp.com/en


### 🟡 Key Findings




### 🟡 1.1 What is Cursor Agent CLI?




### 🟡 1.2 Core Architecture




### 🟡 2.1 Interactive Mode




### 🟡 2.2 Non-Interactive Mode (Print Mode)




### 🟡 2.3 Session Management




### 🟡 2.4 Output Formats




### 🟡 3.1 What is MCP?




### 🟡 3.2 MCP Architecture in Cursor Agent




### 🟡 3.3 MCP Transport Methods




### 🟡 3.4 MCP Capabilities Supported by Cursor Agent




### 🟡 3.5 MCP Configuration




### 🟡 4.1 Rules System




### 🟡 4.2 Codebase Indexing




### 🟡 5.1 Command Approval




### 🟡 5.2 MCP Tool Approval




### 🟡 5.3 Security Best Practices




### 🟡 6.1 Vision: Why Cursor Agent + CLIProxyAPI?




### 🟡 6.2 Proposed Integration Architecture




### 🟡 6.3 Potential MCP Tools for CLIProxyAPI




### 🟡 6.4 Benefits to CLIProxyAPI Users




### 🟡 6.5 Implementation Phases




### 🟡 7.1 Go MCP Server Implementation




### 🟡 7.2 Security Implications




### 🟡 7.3 Performance & Scalability




### 🟡 Cursor Agent vs. Traditional CI/CD




### 🟡 MCP Ecosystem Alternatives




### 🟡 Official Documentation




### 🟡 Key Resources




### 🟡 Community & Examples




### 🟡 For CLIProxyAPI Maintainers




### 🟡 For Integration Explorers




### 🟡 Review this research

Assess alignment with project goals


### 🟡 Create change proposal

Use AgilePlus to formalize MCP server feature


### 🟡 Design MCP interface

Define tool set and protocols


### 🟡 Prototype

Build minimal MCP server for proof-of-concept


### 🟡 Community feedback

Share proposal for community input


### 🟡 Implementation

Execute in phases per section 6.5


### 🟡 Experiment locally

```bash


### 🟡 Test MCP setup

Configure a simple `.cursor/mcp.json` for CLIProxyAPI


### 🟡 Prototype custom tool

Write a minimal MCP server to understand protocol


### 🟡 Provide feedback

Share findings with team and community


### 🟡 Better User Experience

Conversational provider management


### 🟡 Automation

CI/CD-friendly credential and routing management


### 🟡 Innovation

New workflows previously impossible


### 🟡 Community

Aligns with open standards (MCP) and tools (Cursor)


### 🟡 Documentation

Tutorials, examples, API docs


### 🟡 Testing

Additional test coverage, edge cases


### 🟡 Features

Community-requested enhancements


### 🟡 Bug Fixes

Issues from GitHub tracker


### 🟡 Performance

Optimizations and benchmarks


### 🟡 Security

Security audits and improvements


### 🟡 Security patches

Immediate (within 24 hours)


### 🟡 Bug fixes

Weekly


### 🟡 Features

Monthly evaluation


### 🟡 Breaking changes

Evaluated case-by-case


### 🟡 Major releases

Annually or when breaking changes needed


### 🟡 Minor releases

Monthly or when significant features ready


### 🟡 Patch releases

As needed for bugs and security


### 🟡 Documentation

Start with docs in `/docs`


### 🟡 Issues

GitHub issue tracker


### 🟡 Discussions

GitHub discussions for questions


### 🟡 Security

See [SECURITY.md](../SECURITY.md)


### 🟡 Code of Conduct

We maintain a welcoming environment


### 🟡 Communication

Respectful and constructive


### 🟡 Recognition

Contributors acknowledged in releases


### 🟡 Project Background




### 🟡 Project Goals




### 🟡 Relationship with Upstream




### 🟡 Enhanced Features




### 🟡 Configuration Differences




### 🟡 API Differences




### 🟡 Breaking Changes (if any)




### 🟡 For Users of Original CLIProxyAPI




### 🟡 Migration Checklist




### 🟡 Compatibility Matrix




### 🟡 Rollback Plan




### 🟡 Quick Start for Contributors




### 🟡 Areas for Contribution




### 🟡 Contribution Standards




### 🟡 Our Approach




### 🟡 Divergence Documentation




### 🟡 Contributing Back to Upstream




### 🟡 Versioning




### 🟡 Release Schedule




### 🟡 Support Policy




### 🟡 Getting Help




### 🟡 Community




### 🟡 Planned Enhancements




### 🟡 Long-term Vision




### 🟡 Why fork instead of contributing to original?




### 🟡 Will you merge back with the original?




### 🟡 Is this fork production-ready?




### 🟡 How do I report issues?




### 🟡 Can I contribute?




### 🟡 What about licensing?




### 🟡 Original Project




### 🟡 Fork Maintainers




### 🟡 Enhanced Maintenance

Provide more frequent updates and faster response to issues


### 🟡 Community-Driven Development

Enable community features and improvements


### 🟡 Extended Features

Add functionality requested by users but not implemented upstream


### 🟡 Improved Developer Experience

Better documentation, testing, and tooling


### 🟡 Security Focus

Faster security patches and proactive security measures


### 🟡 Prioritize security

Always take security improvements


### 🟡 Preserve fork features

Keep fork-specific enhancements


### 🟡 Document divergence

Update this guide with differences


### 🟡 Test thoroughly

Ensure no regressions


### 🟡 Current

Creating a new connection for each request adds 200-500ms overhead


### 🟡 After

Reusing pooled connections reduces overhead to <5ms


### 🟡 Scale Impact

10 concurrent requests = 2-5 seconds saved per batch


### 🟡 Automatic Connection Reuse

Returns healthy connections from pool


### 🟡 Health Monitoring

Background health checks every 30s


### 🟡 Idle Eviction

Removes unused connections after 5 minutes


### 🟡 Thread-Safe

Safe concurrent access with proper synchronization


### 🟡 Statistics

Track creation, reuse, evictions, and errors


### 🟡 Graceful Shutdown

Proper cleanup on close


### 🟡 Connection Reuse Rate

70-90% of requests (initial plateau at 40%)


### 🟡 Latency Reduction

200-500ms → 5-20ms per request


### 🟡 Throughput Increase

3-5x improvement for concurrent requests


### 🟡 Memory Overhead

~5-10MB per 10 connections


### 🟡 Current

Identical requests are re-executed from scratch


### 🟡 After

Identical requests return cached results in <1ms


### 🟡 Use Cases

Code analysis, documentation lookup, model inference


### 🟡 Intelligent Key Generation

MD5 hash of agent type + input


### 🟡 Size-Based Eviction

LRU eviction when cache full


### 🟡 TTL Management

Auto-expiration with periodic cleanup


### 🟡 Hit Rate Tracking

Monitor cache effectiveness


### 🟡 Thread-Safe

Safe concurrent access


### 🟡 Statistics

Hits, misses, evictions, current size/entries


### 🟡 Cache Hit Rate

40-70% for typical usage


### 🟡 Response Time (Hit)

<1ms


### 🟡 Response Time (Miss)

Original execution time


### 🟡 Memory Overhead

100MB for 100MB cache


### 🟡 Throughput

10-20x improvement for cache-heavy workloads


### 🟠 Current

Polling or batch responses = high latency


### 🟡 After

Real-time streaming with <100ms latency


### 🟡 Use Cases

Live agent output, progress tracking, long-running operations


### 🟡 Real-Time Streaming

Server-Sent Events protocol


### 🟡 Multiple Clients

One stream, many subscribers


### 🟡 Message Buffering

New clients receive recent history


### 🟡 Automatic Heartbeat

Keep-alive every 30s


### 🟡 Thread-Safe

Concurrent client access


### 🟡 Statistics

Messages sent, bytes, clients, errors


### 🟡 Message Latency

<100ms end-to-end


### 🟡 Throughput

Hundreds of messages/second per stream


### 🟡 Memory per Stream

~1-5MB (including buffers)


### 🟡 Connection Overhead

Minimal (HTTP/1.1 keep-alive)


### 🟡 Days 1-2

Copy code, update structs, integrate with session management


### 🟡 Days 3-4

Add HTTP request handling, test concurrent operations


### 🟡 Day 5

Performance testing, monitoring integration


### 🟡 Days 1-2

Copy code, integrate with query handlers


### 🟡 Days 3-4

Add cache invalidation logic, test hit rates


### 🟡 Day 5

Configuration tuning, analytics


### 🟡 Days 1-3

Copy code, HTTP endpoint setup, client testing


### 🟡 Days 4-5

Integration with agent execution, production testing


### 🟡 Unit Tests

All three components


### 🟡 Integration Tests

Pool + Cache + Streaming together


### 🟡 Load Tests

Concurrent connections, throughput, latency


### 🟡 Staging Deployment

Real workload testing


### 🟡 Cause

MaxConnections too low for workload


### 🟡 Solution

Increase MaxConnections config


### 🟡 Cause

MaxIdleTime too short


### 🟡 Solution

Increase MaxIdleTime or reduce connections


### 🟡 Cause

Workload doesn't have repeating requests


### 🟡 Solution

Reduce TTL, focus on specific query patterns


### 🟡 Cause

Entries not expiring, cache full


### 🟡 Solution

Reduce MaxSizeKB or TTL


### 🔴 Cause

Browser doesn't support SSE or firewall blocking


### 🟡 Solution

Use polling fallback, check CORS


### 🟡 Cause

Proxy timeout


### 🟡 Solution

Heartbeat already implemented, check proxy config


### 🟡 Problem Solved




### 🟡 What's Provided




### 🟡 Key Components




### 🟡 Features




### 🟡 Integration Steps




### 🟡 Performance Expectations




### 🟡 Problem Solved




### 🟡 What's Provided




### 🟡 Key Components




### 🟡 Features




### 🟡 Integration Steps




### 🟡 Configuration Strategies




### 🟡 Performance Expectations




### 🟡 Problem Solved




### 🟡 What's Provided




### 🟡 Key Components




### 🟡 Features




### 🟡 HTTP Integration




### 🟡 Client Implementation (JavaScript)




### 🟡 Integration Steps




### 🟡 Performance Expectations




### 🟡 Week 1: Connection Pooling




### 🟡 Week 2: Response Caching




### 🟡 Week 3: SSE Streaming




### 🟡 Week 3+: Testing & Staging




### 🟡 Connection Pooling




### 🟡 Response Caching




### 🟡 SSE Streaming




### 🟡 Performance Metrics




### 🟡 Resource Impact




### 🟡 Connection Pool Issues




### 🟡 Cache Issues




### 🟡 Streaming Issues




### 🟡 Create pool on AgentAPI startup

```go


### 🟡 Use pool in request handlers

```go


### 🟡 Monitor pool health

```go


### 🟡 Create cache on startup

```go


### 🟡 Use cache in query handling

```go


### 🟡 Monitor cache effectiveness

```go


### 🟡 Create stream on operation start

```go


### 🟡 Stream output as it arrives

```go


### 🟡 Set up HTTP endpoints

```go


### 🟡 80% increase in production reliability

- **Reduced MTTR by 50%** (better diagnostics)


### 🟡 Fewer runaway processes

(enforcement)


### 🟡 Zero auth failures

(automatic refresh)


### 🟡 Dynamic model support

(no hardcoding)


### 🟡 Integration

Review PHASE1_IMPLEMENTATION_GUIDE.md


### 🟡 Code details

Check comments in source files


### 🟡 Architecture

Review AGENTAPI_AUGGIE_CURSOR_REVIEW.md


### 🟡 Testing

See PHASE1_IMPLEMENTATION_GUIDE.md testing section


### 🟡 Deployment

Use PHASE1_IMPLEMENTATION_SUMMARY.md checklist


### 🟡 Code Files (5 complete Go modules)




### 🟡 Documentation Files (7 comprehensive guides)




### 🟡 Pre-Integration




### 🟡 Integration (Week 1)




### 🟡 Testing (Week 1)




### 🟡 Deployment (Week 2)




### 🟡 All Code Includes:




### 🟡 Standards Met:




### 🟡 Error Classification




### 🟡 Health Checks




### 🟡 Resource Limits




### 🟡 Token Refresh




### 🟡 Model Discovery




### 🟡 Unit Tests (existing in code examples)




### 🟡 Integration Tests (to add)




### 🟡 E2E Tests (to add)




### 🟡 Load Tests (recommended)




### 🟡 Metrics to Expose




### 🟡 Alerts to Configure




### 🟡 Immediate (Days 1-3 after integration)




### 🟡 Short-term (Week 1)




### 🟡 Medium-term (Weeks 2-4)




### 🟡 Phase 1 Success = All Below True:




### 🟡 Expected Improvement:




### 🟡 agentapi-error-classification.go

(250+ lines)


### 🟡 agentapi-health-check.go

(400+ lines)


### 🟡 agentapi-resource-limits.go

(400+ lines)


### 🟡 agentapi-auggie-token-refresh.go

(350+ lines)


### 🟡 agentapi-cursor-model-discovery.go

(450+ lines)


### 🟡 PHASE1_IMPLEMENTATION_GUIDE.md

- Step-by-step integration guide


### 🟡 PHASE1_IMPLEMENTATION_SUMMARY.md

- Executive summary


### 🟡 DYNAMIC_SERVICE_DISCOVERY_IMPLEMENTATION.md

(from earlier)


### 🟡 AGENTAPI_AUGGIE_CURSOR_REVIEW.md

(from earlier)


### 🟡 AGENTAPI_IMPLEMENTATION_PATTERNS.md

(from earlier)


### 🟡 AGENTAPI_REVIEW_SUMMARY.md

(from earlier)


### 🟡 DOCUMENTATION_INDEX.md

(from earlier)


### 🟡 DYNAMIC_SERVICE_DISCOVERY_IMPLEMENTATION.md

- VibeProxy service discovery


### 🟡 AGENTAPI_AUGGIE_CURSOR_REVIEW.md

- Comprehensive review


### 🟡 AGENTAPI_IMPLEMENTATION_PATTERNS.md

- Code patterns


### 🟡 AGENTAPI_REVIEW_SUMMARY.md

- Executive summary


### 🟡 DOCUMENTATION_INDEX.md

- Navigation guide


### 🟡 Problem

System not fully optimized for target workload


### 🟡 Solution

Systematic performance optimization across all layers


### 🟡 Problem

Basic round-robin doesn't handle complex scenarios


### 🟡 Solution

Sophisticated routing with multiple strategies


### 🟡 Problem

Cache only helps identical queries


### 🟡 Solution

Match semantically similar queries


### 🟡 What It Solves




### 🟡 What It Provides




### 🟡 Optimization Strategies




### 🟡 Integration Steps




### 🟡 Performance Targets & Achievable Results




### 🟡 What It Solves




### 🟡 What It Provides




### 🟡 Advanced Routing Scenarios




### 🟡 Integration Steps




### 🟡 What It Solves




### 🟡 What It Provides




### 🟡 Integration Steps




### 🟡 Architecture




### 🟡 Implementation




### 🟡 Performance Targets




### 🟡 Week 9: Performance Tuning




### 🟡 Week 10: Advanced Routing & Semantic Cache




### 🟡 Week 11: Multi-Region & Final Integration




### 🟡 Phase 4A: Staging Validation (3 days)




### 🟡 Phase 4B: Canary Deployment (3 days)




### 🟡 Phase 4C: Full Rollout (2 days)




### 🟡 Rollback Plan




### 🟡 Key Metrics to Monitor




### 🟡 Alerting Strategy




### 🟡 Performance Tuning

- CPU, memory, and network optimization


### 🟡 Advanced Routing

- Sophisticated load balancing strategies


### 🟡 Semantic Caching

- AI-powered query similarity matching


### 🟡 Multi-Region Deployment

- Geographic distribution and failover


### 🟡 WHEN

request specifies model explicitly


### 🟡 THEN

skip router and use specified model (unless disabled)


### 🟡 WHEN

task is classified as "tool_call"


### 🟡 THEN

rule: "prioritize Claude/GPT-4 → fallback to Gemini if unavailable"


### 🟡 WHEN

model fails on task_type > 30% of time


### 🟡 THEN

auto-generate rule: "avoid [model] for [task_type] → fallback to [better_model]"


### 🟡 Routing Latency

<20ms (with caching)


### 🟡 Cache Hit Rate

Expected 60-80% for repeated requests


### 🟡 Task Classification Accuracy

95%+ (based on feature detection)


### 🟡 Model Selection Accuracy

90%+ (based on cost-quality optimization)


### 🟡 Code Written

~1215 LOC


### 🟡 Files Created

10


### 🟡 API Endpoints

4


### 🟡 Unit Tests

13


### 🟡 Test Coverage

85%+


### 🟡 Routing Latency

<20ms


### 🟡 Week 4: Semantic Router Integration ✅




### 🟡 Week 5: RouteLLM Integration ✅




### 🟡 Week 6: Request Feature Extraction & Caching ✅




### 🟡 Integration & API Layer ✅




### 🟡 Code Files Created (~1215 LOC)




### 🟡 Routing Endpoints




### 🟡 1. Semantic Router




### 🟡 2. RouteLLM Cost-Quality Optimizer




### 🟡 3. Request Parser & Feature Extractor




### 🟡 4. Redis Caching




### 🟡 5. Routing Service




### 🟡 Unit Tests Created




### 🟡 Test Coverage




### 🟡 Route Request




### 🟡 Classify Task




### 🟡 Auggie CLI Docs

https://docs.augmentcode.com/cli/


### 🟡 Augment Code

https://www.augmentcode.com/


### 🟡 CLIProxyAPI Repo

https://github.com/router-for-me/CLIProxyAPI


### 🟡 This Implementation

docs/auggie-integration.md


### 🟡 Phase 1: Core Executor (4 files)




### 🟡 Phase 2: Authentication (4 files)




### 🟡 Phase 3: System Integration (4 files modified)




### 🟡 Phase 4: Documentation (2 files)




### 🟡 Minimal Configuration




### 🟡 Full Configuration




### 🟡 Multi-Instance Load Balancing




### 🟡 Setup




### 🟡 Run Unit Tests




### 🟡 Run Integration Tests




### 🟡 Run All Tests




### 🟡 Local Testing

✅


### 🟡 Configuration

✅


### 🟡 Verification

✅


### 🟡 Production Deployment

✅


### 🟡 Token Expiration

Auggie tokens are long-lived but may expire. Monitor logs for validation failures.


### 🟡 Model List Cache

1-hour TTL means new models may not be visible immediately.


### 🟡 Concurrent Limit

Default 5, can be adjusted but impacts resource usage.


### 🟡 Timeout

Some complex tasks may need timeout adjustment.


### 🟡 SQLite

Persistent local storage (routing decisions, policy cache, execution history)


### 🟡 Redis

High-speed caching layer (model scores, classification results, hot data)


### 🟡 NATS

Real-time event streaming (routing decisions, metrics, alerts)


### 🟡 Prompt Classification Cache

(`arch:{hash(prompt)}` → ArchRouterClassification)


### 🟡 Model Score Cache

(`mirt:{model_count}:{hash(features)}` → ScoreMap)


### 🟡 Executor Registry Cache

(`registry:executors` → [Model])


### 🟡 Routing Decision Cache

(`decision:{hash(prompt)}:{executor}` → SelectedModel)


### 🟡 routing.decision

→ Published for every routing decision


### 🟡 routing.cache

→ Published on cache hits/misses


### 🟡 health.status

→ Published every 30s by health worker


### 🟡 metrics.summary

→ Published every 60s


### 🟡 What We Have




### 🟡 What's Missing




### 🟠 1. Redis Integration (High-Speed Caching)




### 🟡 2. NATS Integration (Real-Time Event Streaming)




### 🟡 3. SQLite Integration (Persistent Local Storage)




### 🟡 Phase 1: Redis Caching (Days 1-2)




### 🟡 Phase 2: NATS Events (Days 3-4)




### 🟡 Phase 3: SQLite Storage (Days 5-6)




### 🟡 Phase 4: Integration & Optimization (Days 7-8)




### 🟡 Microservice Framework

Complete with 6-state lifecycle, health checks, graceful shutdown


### 🟡 Redis/NATS Connections

Basic initialization and lifecycle management added


### 🟡 DualRouter Core

7-step routing pipeline with Arch-Router + MIRT-BERT


### 🟡 PostgreSQL Database

Used for initial data (can coexist with SQLite for specific purposes)


### 🟡 Redis Usage

No caching, no session management, no hot-data persistence


### 🟡 NATS Usage

No event publishing, no distributed messaging, no real-time monitoring


### 🟡 SQLite Usage

Not integrated at all (PostgreSQL is primary DB)


### 🟡 Disable Redis caching

Set `CacheEnabled: false` → routes bypass cache, use source directly


### 🟡 Disable NATS publishing

Set `NATSPublishAsync: false` → fail silently, routing continues


### 🟡 Disable SQLite logging

Set `SQLitePath: ""` → skip logging, routing unaffected


### 🟡 Unit Tests

Cache hits/misses, event publishing, SQLite queries


### 🟡 Integration Tests

Full routing pipeline with all three


### 🟡 Load Tests

Performance improvement measurement


### 🟡 Chaos Tests

Redis/NATS/SQLite failures → verify graceful degradation


### 🟡 Analytics Tests

SQLite query correctness


### 🟡 Accuracy

93.17% (outperforms Claude-Sonnet-3.7 by 7.71%)


### 🟡 Latency

51ms (28x faster than Claude-Sonnet-3.7)


### 🟡 Advantage

Decoupled route selection from model assignment


### 🟡 Relevance

Validates your 1.5B router approach + Domain-Action taxonomy


### 🟡 Savings: 300-425 LOC (67% reduction)

**New Total Custom Code**:


### 🟡 Option 1: sqlc (RECOMMENDED for your use case)




### 🟡 Option 2: GORM




### 🟡 Option 3: Ent




### 🟡 Option 4: Raw database/sql




### 🟡 Option 1: Terraform (RECOMMENDED)




### 🟡 Option 2: Pulumi




### 🟡 Option 3: Docker Compose (LIGHTWEIGHT)




### 🟡 With sqlc + sql-migrate + Terraform:




### 🟡 Database Layer




### 🟡 Infrastructure Layer




### 🟡 sqlc

for model registry queries


### 🟡 sql-migrate

for database migrations


### 🟡 Terraform

for production infrastructure


### 🟡 Docker Compose

for local development


### 🟡 Overall

99%


### 🟡 Pattern Detection

<100ms


### 🟡 Rule Generation

<50ms


### 🟡 Knowledge Graph Query

<10ms


### 🟡 Recommendation Lookup

<5ms


### 🟡 Learning Update

<500ms (hourly)


### 🟡 Code Written

~1390 LOC


### 🟡 Files Created

6


### 🟡 API Endpoints

8


### 🟡 Unit Tests

20


### 🟡 Test Coverage

99%+


### 🟡 Pattern Detection

<100ms


### 🟡 Rule Generation

<50ms


### 🟡 Week 9: Performance Tracking & Pattern Detection ✅




### 🟡 Week 10: Rule Generation & Knowledge Graph ✅




### 🟡 Code Files Created (~1390 LOC)




### 🟡 Learning Endpoints




### 🟡 1. Performance Tracker




### 🟡 2. Pattern Detector




### 🟡 3. Rule Generator




### 🟡 4. Knowledge Graph




### 🟡 5. Learning System (Orchestration)




### 🟡 Unit Tests Created (20 tests)




### 🟡 Test Coverage




### 🟡 Record Performance




### 🟡 Get Detected Patterns




### 🟡 Get Generated Rules




### 🟡 Get Recommendations




### 🟡 Get Learning Stats




### 🟡 Pattern Detection




### 🟡 Rule Generation




### 🟡 Knowledge Graph




### 🟡 Learning Feedback




### 🟡 Semantic Router

Classify task type (tool_call, code_gen, reasoning, etc.)


### 🟡 RouteLLM

Optimize cost-quality trade-off


### 🟡 Fallback Chain

Execute provider-specific fallback rules


### 🟡 Caching

Cache routing decisions for <20ms latency


### 🟡 Gemini Strategy

Exponential backoff (0-10s), max 3 retries


### 🟡 Cerebras Strategy

Indefinite limit detection, 1m+ cooldown


### 🟡 Budget-Based

Track usage, throttle at 85%, block at 100%


### 🟡 Task-Specific

Tool calls prefer Claude/GPT-4, code gen prefers GPT-4


### 🟡 Language

Go 1.21+


### 🟡 Database

PostgreSQL 15 + pgvector + TimescaleDB


### 🟡 ORM

sqlc (SQL code generation)


### 🟡 Migrations

Goose


### 🟡 Caching

Redis


### 🟡 IaC

Pulumi (Go)


### 🟡 Routing

RouteLLM, Semantic Router


### 🟡 Language

Python 3.11+


### 🟡 ML

scikit-learn, pandas, numpy


### 🟡 Vector DB

pgvector (PostgreSQL)


### 🟡 Knowledge Graph

PostgreSQL recursive CTEs


### 🟡 Containerization

Docker


### 🟡 Local Dev

Docker Compose


### 🟡 Production

Pulumi + AWS


### 🟡 Monitoring

Prometheus + Grafana (optional)


### 🟡 Mitigation

Fallback chains, quality analysis, human review


### 🟡 Mitigation

Caching, rate limiting, monitoring


### 🟡 Mitigation

Validation, quality checks, feedback loops


### 🟡 Mitigation

Database optimization, caching, horizontal scaling


### 🟡 1. Model Registry (PostgreSQL)




### 🟡 2. Request Router (Go)




### 🟡 3. Fallback Rules Engine (Go)




### 🟡 4. Learning System (Python)




### 🟡 5. Performance Tracker (PostgreSQL + TimescaleDB)




### 🟡 Backend




### 🟡 ML/Learning




### 🟡 DevOps




### 🟡 Phase 1: Foundation (Weeks 1-3) ✅ COMPLETE




### 🟡 Phase 2: Routing (Weeks 4-6)




### 🟡 Phase 3: Fallback Rules (Weeks 7-8)




### 🟡 Phase 4: Learning (Weeks 9-10)




### 🟡 Phase 5: Production (Weeks 11-12)




### 🟡 Go Code (~3350-4650 LOC)




### 🟡 Python Code (~2200-3150 LOC)




### 🟡 SQL Code (~100-150 LOC)




### 🟡 Infrastructure (~50-75 LOC)




### 🟡 Core Tables




### 🟡 Indexes




### 🟡 Model Management




### 🟡 Routing




### 🟡 Performance




### 🟡 Learning




### 🟡 Routing Accuracy




### 🟡 Cost Optimization




### 🟡 Learning Effectiveness




### 🟡 System Performance




### 🟡 Risk: Routing Errors




### 🟡 Risk: Performance Degradation




### 🟡 Risk: Data Quality




### 🟡 Risk: Scaling Issues




### 🟡 Week 4: Semantic Router Integration




### 🟡 Week 5: RouteLLM Integration




### 🟡 Week 6: Request Feature Extraction & Caching




### 🟡 Week 7: Provider-Specific Strategies




### 🟡 Week 8: Task-Specific Rules & Integration




### 🟡 Week 9: Performance Tracking & Pattern Detection




### 🟡 Week 10: Rule Generation & Knowledge Graph




### 🟡 Week 11: Infrastructure & Monitoring




### 🟡 Week 12: Testing & Deployment




### 🟡 Review

this comprehensive plan


### 🟡 Approve

the architecture and approach


### 🟡 Continue

with Phase 2 (Routing)


### 🟡 Follow

phase-by-phase breakdown


### 🟡 Deploy

to production


### 🟡 Your scale

<1M task embeddings ✅


### 🟡 Performance

Competitive with Qdrant at your scale


### 🟡 Recommendation

USE POSTGRES


### 🟡 Your scale

<10K model descriptions ✅


### 🟡 Performance

Excellent for your scale


### 🟡 Recommendation

USE POSTGRES


### 🟡 Your scale

<100K role-task-model relationships ✅


### 🟡 Performance

1.1s (faster than Neo4j's 3.4s in benchmarks)


### 🟡 Recommendation

USE POSTGRES


### 🟡 Your scale

<10M performance history points ✅


### 🟡 Performance

Excellent compression


### 🟡 Recommendation

USE POSTGRES


### 🟡 BEFORE (Complex Multi-Database)




### 🟡 AFTER (Simplified Single Database)




### 🟡 1. Vector Search (pgvector)




### 🟡 2. Full-Text Search (FTS)




### 🟡 3. Graph Queries (Recursive CTEs)




### 🟡 4. Time-Series Data (TimescaleDB)




### 🟡 With PostgreSQL Only (No Qdrant/Neo4j):




### 🟡 Year 1-2

PostgreSQL + extensions (current)


### 🟡 Year 2-3

Add Qdrant if vectors exceed 10M


### 🟡 Year 3+

Add Neo4j if graph nodes exceed 10M


### 🟡 Latency

500ms → 50ms (10x improvement)


### 🟡 Throughput

2 req/s → 50+ req/s (25x improvement)


### 🟡 Cache Hit Rate

0% → 60%


### 🟡 Connection Pool Efficiency

70%+


### 🟡 Unified Interface

Single API for all providers


### 🟡 Intelligent Routing

Optimal provider selection


### 🟡 Session Management

Multi-user support


### 🟡 Semantic Caching

80%+ hit rate on similar queries


### 🟡 Auto-Scaling

Automatic resource management


### 🟡 Multi-Region

Global failover capability


### 🟡 SLA

99.99% availability


### 🟡 Advanced Features

Enterprise-grade capabilities


### 🟡 Latency P95

< 100ms (target)


### 🟡 Throughput

> 100 req/s (target)


### 🟡 Cache Hit Rate

> 60% (target)


### 🟡 Availability

99.99% (target)


### 🟡 Error Rate

< 0.1%


### 🟡 Automatic Failover

< 1 second


### 🟡 Recovery Time

< 30 seconds


### 🟡 SLA Compliance

99.99%


### 🟡 CPU Usage

< 60% peak


### 🟡 Memory Usage

< 75% peak


### 🟡 Connection Pool Utilization

70%+


### 🟡 Cache Efficiency

60%+ hit rate


### 🟡 Module 1: Connection Pooling




### 🟡 Module 2: Response Caching




### 🟡 Module 3: SSE Streaming




### 🟡 Module 4: Unified Service Provider




### 🟡 Module 5: Intelligent Request Router




### 🟡 Module 6: Session Manager




### 🟡 Module 7: Semantic Cache




### 🟡 Module 8: Performance Tuning




### 🟡 Module 9: Advanced Routing Strategies




### 🟡 Module 10: Multi-Region Deployment




### 🟡 Module 11: Resource Limits & Monitoring




### 🟡 Module 12: Token Refresh & Model Discovery




### 🟡 Phase 2 Results




### 🟡 Phase 3 Results




### 🟡 Phase 4 Results




### 🟡 Phase 2 Integration




### 🟡 Phase 3 Integration




### 🟡 Phase 4 Integration




### 🟡 Phase 2 Testing




### 🟡 Phase 3 Testing




### 🟡 Phase 4 Testing




### 🟡 Pre-Deployment Checklist




### 🟡 Staging Deployment




### 🟡 Production Rollout




### 🟡 Performance Metrics




### 🟡 Reliability Metrics




### 🟡 Operational Metrics




### 🟡 Review

this roadmap


### 🟡 Approve

the implementation plan


### 🟡 Begin

Phase 2 implementation (Days 5-6)


### 🟡 Progress

through Phases 3-4 (Days 7-11)


### 🟡 Deploy

to staging (Day 12)


### 🟡 Validate

performance targets


### 🟡 Release

to production


### 🟡 Fallback Latency

<50ms


### 🟡 Rate Limit Detection

Immediate


### 🟡 Indefinite Limit Detection

5 attempts (Cerebras)


### 🟡 Budget Tracking

Real-time


### 🟡 Task Rule Lookup

<1ms


### 🟡 Code Written

~1380 LOC


### 🟡 Files Created

8


### 🟡 API Endpoints

6


### 🟡 Unit Tests

15


### 🟡 Test Coverage

95%+


### 🟡 Fallback Latency

<50ms


### 🟡 Week 7: Provider-Specific Strategies ✅




### 🟡 Week 8: Task-Specific Rules & Integration ✅




### 🟡 Code Files Created (~1380 LOC)




### 🟡 Fallback Endpoints




### 🟡 1. Gemini Fallback Strategy




### 🟡 2. Cerebras Fallback Strategy




### 🟡 3. Budget-Based Fallback




### 🟡 4. Task-Specific Rules




### 🟡 5. Fallback Engine




### 🟡 Unit Tests Created (15 tests)




### 🟡 Test Coverage




### 🟡 Execute Fallback




### 🟡 Get Fallback Chain




### 🟡 Get Task Rules




### 🟡 Get Strategy Info




### 🟡 Gemini (Exponential Backoff)




### 🟡 Cerebras (Indefinite Detection)




### 🟡 Budget-Based




### 🟡 Task-Specific Rules




### 🟡 Auggie

❌ NO native streaming support - returns 501 (Not Implemented)


### 🟡 Cursor Agent

❌ Currently BLOCKS streaming - returns 501 (Not Implemented)


### 🟡 GeminiCLI

✅ FULL streaming support via Server-Sent Events (SSE)


### 🟡 Solution Needed

Implement streaming workaround for Auggie; enable Cursor Agent streaming


### 🟡 Status

Fully implemented


### 🟡 Method

Spawns local Auggie CLI subprocess via `exec.CommandContext`


### 🟡 Flow

1. Translates OpenAI-compatible request to Auggie JSON format


### 🟡 Current

Hard-coded 501 Not Implemented error


### 🟡 Issue

Auggie CLI itself may not support streaming output format


### 🟡 Evidence

No streaming-specific CLI flags documented (like `--output-format stream-json`)


### 🟡 1. AugieExecutor (`internal/runtime/executor/auggie_executor.go`)




### 🟡 2. CursorAgentExecutor (`internal/runtime/executor/cursor_agent_executor.go`)




### 🟡 3. GeminiCLIExecutor (`internal/runtime/executor/gemini_cli_executor.go`)




### 🟡 Why Auggie Doesn't Support Streaming




### 🟡 Why Cursor Agent SHOULD Support Streaming




### 🟡 Strategy A: Chunked Emission Workaround for Auggie




### 🟡 Strategy B: Streaming Response Format Negotiation




### 🟡 Strategy C: Process Stdout Line Buffering




### 🟡 Phase 1: Enable Cursor Agent Streaming (Quick Win) ✅




### 🟡 Phase 2: Implement Auggie Streaming Workaround




### 🟡 Phase 3: Pre-Research (Optional)




### 🟡 Cursor Agent Streaming (Phase 1)




### 🟡 Auggie Streaming (Phase 2)




### 🟡 For Auggie




### 🟡 For Cursor Agent




### 🟡 CLI-based architecture

Spawns subprocess, limited by Auggie CLI capabilities


### 🟡 Response format

Only supports JSON output (`--output-format json`)


### 🟡 No streaming flags

Unlike cursor-agent, no `--stream` or `--output-format stream-json` flag present


### 🟡 Full buffering

Current implementation buffers entire response before returning


### 🟡 ExecuteStream delegates to Execute()

with `opts.Stream = true`


### 🟡 Execute() then checks opts.Stream and rejects it

with 501


### 🟡 Result

Circular rejection - streaming is hardcoded as unsupported


### 🟡 Auggie CLI Architecture

Subprocess-based, not server-based


### 🟡 No Streaming Output Format

- Auggie CLI only supports `--output-format json` (batch)


### 🟡 Subprocess Limitations

- Cannot spawn incrementally flushed JSON chunks


### 🟡 CLI Supports It

`--output-format stream-json` flag exists


### 🟡 Response Parser Ready

`streamCursorAgentOutput()` method fully implemented


### 🟡 OpenAI Conversion Ready

Builds proper OpenAI streaming chunks


### 🟡 Only Blocker

Hardcoded 501 rejection in Execute()


### 🟡 Word-based

Split on whitespace boundaries (natural)


### 🟡 Token-based

Use token counter if available


### 🟡 Sentence-based

Split on `.!?` followed by space


### 🟡 Fixed-size

Simple character count threshold


### 🟡 Remove hardcoded 501 in Execute()

```go


### 🟡 Route to streaming handler

```go


### 🟡 Fix ExecuteStream delegation

```go


### 🟡 Lines of Code:

1,850+ (production-ready)


### 🟡 Components:

7 core modules


### 🟡 Database Tables:

8 new tables with indices


### 🟡 Tests:

Unit + benchmark tests included


### 🟡 Documentation:

3 comprehensive guides


### 🟡 Baseline

(always GPT-4): $5.00/1M tokens


### 🟡 Random Selection

$3.00/1M tokens


### 🟡 RouteLLM

$2.50/1M tokens


### 🟡 MIRT (expected)

$2.20/1M tokens


### 🟡 Expected Savings

27-56% cost reduction


### 🟡 ✅ Phase 1: Architecture Design




### 🟡 ✅ Phase 2: Database Schema




### 🟡 ✅ Phase 3: Core Go Implementation




### 🟡 ✅ Phase 4: Testing & Documentation




### 🟡 ⏳ Phase 5: MLX-LM Server Integration




### 🟡 ⏳ Phase 6: MIRT Checkpoint Integration




### 🟡 ⏳ Phase 7: Vibeproxy UI Integration




### 🟡 ⏳ Phase 8: Production Deployment




### 🟡 Routing Process Flow




### 🟡 Feature Dimensions (25 Total)




### 🟡 IRT Formula




### 🟡 Database Schema




### 🟡 Lines of Code (Production-Ready)




### 🟡 Test Coverage




### 🟡 Documentation




### 🟡 Latency Breakdown




### 🟡 Cost Projections




### 🟡 Accuracy Projections




### 🟠 High Priority Risks




### 🟠 Medium Priority Risks




### 🟠 Low Priority Risks




### 🟡 Runtime Dependencies




### 🟡 External Services




### 🟡 Week 2: MLX-LM Integration




### 🟡 Week 3: Vibeproxy UI




### 🟡 Week 4: Testing & Optimization




### 🟡 Week 5: Production Rollout




### 🟡 Functional Requirements




### 🟡 Performance Requirements




### 🟡 Quality Requirements




### 🟡 MLX-LM Server Stability

- Risk: Server crashes or OOM


### 🟡 MIRT Checkpoint Compatibility

- Risk: Checkpoint version mismatch


### 🟡 Feature Extraction Accuracy

- Risk: Heuristic rules inaccurate for edge cases


### 🟡 Latency Impact

- Risk: Total routing > 100ms


### 🟠 Database Lock Contention

- Risk: High-traffic scenarios cause bottlenecks


### 🟡 Policy Configuration Errors

- Risk: Incorrect domain-action mappings


### 🟡 Metrics Collection

<1ms


### 🟡 Health Check

<50ms


### 🟡 Logging

<5ms


### 🟡 API Response

<100ms


### 🟡 Database Query

<50ms


### 🟡 Cache Hit

<10ms


### 🟡 Code Written

~550 LOC


### 🟡 Files Created

3


### 🟡 API Endpoints

6 + 3 Kubernetes probes


### 🟡 Monitoring Components

3


### 🟡 Infrastructure Modules

1


### 🟡 Documentation

1 comprehensive guide


### 🟡 Week 11: Infrastructure & Monitoring ✅




### 🟡 Week 12: Testing & Deployment ✅




### 🟡 Code Files Created (~550 LOC)




### 🟡 Monitoring Endpoints




### 🟡 Kubernetes Probes




### 🟡 1. Metrics Collection




### 🟡 2. Structured Logging




### 🟡 3. Health Checks




### 🟡 4. Pulumi Infrastructure




### 🟡 5. Deployment Guide




### 🟡 End-to-End Tests




### 🟡 Load Testing




### 🟡 Security Testing




### 🟡 Sub-1ms latency

for hot classification/scoring


### 🟡 Session management

across distributed instances


### 🟡 Pub/Sub coordination

between services


### 🟡 Request deduplication

(cache recent decisions)


### 🟡 Feature caching

(extracted 25D vectors)


### 🔴 ACID guarantees

for critical data


### 🟡 Time-series analysis

via TimescaleDB


### 🟡 Vector similarity search

via pgvector


### 🟡 Full-text search

for semantic matching


### 🟡 Audit trail

and compliance


### 🟡 Policy rules storage

(domain/action/model relationships)


### 🟡 Learning inference

(infer new routing patterns)


### 🟡 Fallback chains

(variable-length dynamic traversal)


### 🟡 Pattern matching

(find implicit relationships)


### 🟡 Rule engine

(apply business logic)


### 🟡 Real-time observability

(publish routing decisions)


### 🟡 Multi-service coordination

(request-reply pattern)


### 🟡 Event replay

(persistent streams)


### 🟡 Cache invalidation

(distribute updates)


### 🟡 Learning signals

(publish patterns)


### 🟡 Redis

Hot caching for sub-1ms lookups


### 🟡 PostgreSQL

ACID record store + pgvector for semantic search (NO Qdrant needed)


### 🟡 Neo4j

Policy graph + learning inference + dynamic fallback chains


### 🟡 NATS

Real-time events for observability and coordination


### 🟡 Purpose




### 🟡 Data Structures Used




### 🟡 Implementation in Go




### 🟡 Configuration




### 🟡 Performance Impact




### 🟡 Purpose




### 🟡 Schema Enhancements




### 🟡 Query Patterns




### 🟡 Optimization Settings




### 🟡 Backup & Recovery




### 🟡 Purpose




### 🟡 Graph Model




### 🟡 Query Patterns




### 🟡 Implementation in Go




### 🟡 Purpose




### 🟡 Topic Structure




### 🟡 Event Schemas




### 🟡 Implementation in Go




### 🟡 Configuration




### 🟡 Decision: Keep pgvector, Don't Add Qdrant




### 🟡 pgvector Implementation Details




### 🟡 Data Flow Diagram




### 🟡 Sync Diagram: How Layers Talk




### 🟡 Phase 1: Redis Caching (Weeks 1-2, 16 hours)




### 🟡 Phase 2: PostgreSQL Optimization (Weeks 3-4, 12 hours)




### 🟡 Phase 3: Neo4j Implementation (Weeks 5-7, 24 hours)




### 🟡 Phase 4: NATS Event Streaming (Weeks 8-9, 12 hours)




### 🟡 Phase 5: Integration & Optimization (Weeks 10-11, 16 hours)




### 🟡 docker-compose.full-stack.yml (Enhanced)




### 🟡 Performance Baselines




### 🟡 Dashboards (Grafana)




### 🟡 Alerts




### 🟡 Setup Redis locally

(2 hours)


### 🟡 Implement Redis cache layer

(4 hours)


### 🟡 Integration with DualRouter

(5 hours)


### 🟡 Testing & Performance

(5 hours)


### 🟡 Index tuning

(3 hours)


### 🟡 Full-text search

(3 hours)


### 🟡 Advanced queries

(4 hours)


### 🟡 Optimization

(2 hours)


### 🟡 Setup Neo4j

(3 hours)


### 🟡 Graph schema design

(4 hours)


### 🟡 Policy engine implementation

(8 hours)


### 🟡 Learning integration

(6 hours)


### 🟡 Testing & validation

(3 hours)


### 🟡 Setup NATS

(2 hours)


### 🟡 Event publishing

(5 hours)


### 🟡 Subscriptions

(3 hours)


### 🟡 Testing

(2 hours)


### 🟡 Full-stack integration

(6 hours)


### 🟡 Performance optimization

(5 hours)


### 🟡 Learning system maturation

(3 hours)


### 🟡 Documentation & monitoring

(2 hours)


### 🟡 Request Metrics

- Latency (P50/P95/P99)


### 🟡 Cache Performance

- Hit rate by cache type


### 🟡 Neo4j Performance

- Query response time


### 🟡 System Health

- Redis memory usage


### 🟡 Embedding Model

All-MiniLM-L6-v2 (sentence-transformers) for semantic matching


### 🟡 Python Execution

Sandboxed via V8 isolates or Docker


### 🟡 Caching

Redis (existing infrastructure)


### 🟡 Logging

Structured logging with tool execution details


### 🟡 MCP Implementation

Go-based server supporting stdio + HTTP


### 🟡 1.1 Tool Discovery Service




### 🟡 1.2 Tool Schema Registry




### 🟡 1.3 Tool Validation




### 🟡 2.1 Tool Filtering Strategies




### 🟡 2.2 Mid-Prompt Tool Recommendation




### 🟡 3.1 Safe Python DSL Executor




### 🟡 3.2 Tool Orchestrator




### 🟡 4.1 `/v1/tools` Endpoints




### 🟡 5.1 Expose Tools as MCP Server




### 🟡 For Claude Code Users:




### 🟡 For Tool Chaining (Programmatic):




### 🟡 Tool Execution Approval




### 🟡 Input Sanitization




### 🟡 Output Filtering




### 🟡 MCP Servers

- Scan configured MCP servers


### 🟡 Internal API Tools

- Routes in `/v1/*` endpoints


### 🟡 Runtime Tool Detection

- Monitor file system for tool definitions


### 🟡 1. Vector Search (pgvector)




### 🟡 2. Full-Text Search (FTS)




### 🟡 3. Graph Queries (Knowledge Graph)




### 🟡 4. Time-Series Data (Performance History)




### 🟡 Extensions to Install




### 🟡 Schema Design




### 🟡 GitHub

`lm-sys/RouteLLM`


### 🟡 Status

Production-ready, ICLR 2025 published


### 🟡 Features

Cost-quality trade-off routing, trained routers, evaluation framework


### 🟡 Use

Core routing logic, cost optimization


### 🟡 Integration

Python library, can wrap in gRPC


### 🟡 GitHub

`aurelio-labs/semantic-router`


### 🟡 Status

Active, v0.1.9+ (June 2025)


### 🟡 Features

Vector-based routing, fast decision-making, multi-modal support


### 🟡 Use

Task classification, semantic matching


### 🟡 Integration

Python, supports LangChain/LlamaIndex


### 🟡 GitHub

`Not-Diamond/awesome-ai-model-routing`


### 🟡 Status

Curated list of routing solutions


### 🟡 Value

Reference for 20+ routing approaches


### 🟡 Website

`litellm.ai`


### 🟡 GitHub

`BerriAI/litellm`


### 🟡 Status

Production-ready, widely adopted


### 🟡 Features

100+ providers, cost tracking, load balancing, proxy server


### 🟡 Use

Provider abstraction, budget tracking, rate limit handling


### 🟡 Integration

Python SDK + proxy server (can run separately)


### 🟡 GitHub

`NVIDIA-AI-Blueprints/llm-router`


### 🟡 Features

Flexible routing policies, fine-tunable routers


### 🟡 Use

Alternative routing framework


### 🟡 GitHub

`ml-explore/mlx`


### 🟡 Status

Official Apple framework, actively maintained


### 🟡 Features

Optimized for Apple Silicon, Python API, C++/Swift support


### 🟡 Use

Local 1.5B router inference


### 🟡 Integration

Python library, can expose via gRPC


### 🟡 GitHub

`ml-explore/mlx-lm`


### 🟡 Status

High-level library for MLX


### 🟡 Features

Model loading, generation, fine-tuning


### 🟡 Use

Simplified MLX model management


### 🟡 Website

`ollama.com`


### 🟡 GitHub

`ollama/ollama`


### 🟡 Status

Production-ready, easy deployment


### 🟡 Features

OpenAI-compatible API, model management


### 🟡 Use

Alternative to MLX for local inference


### 🟡 GitHub

`vllm-project/vllm`


### 🟠 Status

Production-ready, high-throughput


### 🟡 Features

Fast inference, memory efficient, distributed serving


### 🟡 Use

High-performance inference alternative


### 🟡 GitHub

`open-compass/opencompass`


### 🟡 Status

Production-ready, comprehensive


### 🟡 Features

MMLU, SWEBENCH, GAIA, 100+ benchmarks, leaderboard


### 🟡 Use

Benchmark evaluation, data collection


### 🟡 Integration

Python framework


### 🟡 GitHub

`EleutherAI/lm-evaluation-harness`


### 🟡 Status

Widely used, comprehensive


### 🟡 Features

Few-shot evaluation, multiple benchmarks


### 🟡 Use

Benchmark evaluation framework


### 🟡 GitHub

`huggingface/datasets`, `huggingface/evaluate`


### 🟡 Status

Standard library


### 🟡 Features

Dataset loading, evaluation metrics


### 🟡 Use

Benchmark data access, metric computation


### 🟡 GitHub

`lmarena/arena-hard-auto`


### 🟡 Status

Active


### 🟡 Features

Automatic LLM benchmarking


### 🟡 Use

Benchmark automation


### 🟡 Website

`qdrant.tech`


### 🟡 GitHub

`qdrant/qdrant`


### 🟡 Status

Production-ready, Rust-based


### 🟡 Features

High-performance, Go client available, REST API


### 🟡 Use

Semantic task matching, embeddings storage


### 🟡 Integration

Go client + REST API


### 🟡 Website

`milvus.io`


### 🟡 GitHub

`milvus-io/milvus`


### 🟡 Status

Production-ready, scalable


### 🟡 Features

High-performance, distributed


### 🟡 Use

Alternative vector DB


### 🟡 GitHub

`philippgille/chromem-go`


### 🟡 Status

Embeddable, Go-native


### 🟡 Features

In-process vector DB, no external dependencies


### 🟡 Use

Lightweight alternative for smaller deployments


### 🟡 Website

`neo4j.com`


### 🟡 Status

Production-ready, enterprise-grade


### 🟡 Features

Go driver available, graph algorithms, GDS library


### 🟡 Use

Role-task-model relationships


### 🟡 Integration

Official Go driver


### 🟡 Website

`memgraph.com`


### 🟡 Status

Neo4j-compatible, lighter-weight


### 🟡 Features

Go client available


### 🟡 Use

Alternative to Neo4j


### 🟡 GitHub

`hashicorp/go-retryablehttp`


### 🟡 Status

Production-ready, widely used


### 🟡 Features

Exponential backoff, configurable retries


### 🟡 Use

HTTP retry logic for provider calls


### 🟡 Integration

Go library


### 🟡 GitHub

`cenkalti/backoff`


### 🟡 Status

Production-ready, v5 latest


### 🟡 Features

Exponential backoff algorithm, configurable


### 🟡 Use

Generic backoff implementation


### 🟡 Integration

Go library


### 🟡 Website

`spacy.io`


### 🟡 GitHub

`explosion/spacy`


### 🟡 Status

Production-ready, industry standard


### 🟡 Features

NER, text classification, fast


### 🟡 Use

Task classification, prompt analysis


### 🟡 Integration

Python library


### 🟡 GitHub

`flairNLP/flair`


### 🟡 Status

Active, state-of-the-art models


### 🟡 Features

Sequence labeling, text classification


### 🟡 Use

Alternative NLP framework


### 🟡 Website

`sbert.net`


### 🟡 GitHub

`UKPLab/sentence-transformers`


### 🟡 Status

Production-ready, widely used


### 🟡 Features

Semantic embeddings, pre-trained models


### 🟡 Use

Task embeddings for semantic matching


### 🟡 Integration

Python library


### 🟡 GitHub

`sqlc-dev/sqlc`


### 🟡 Status

Production-ready, Go-native


### 🟡 Features

Type-safe SQL code generation


### 🟡 Use

PostgreSQL queries for model registry


### 🟡 Integration

Go code generation tool


### 🟡 GitHub

`go-jet/jet`


### 🟡 Status

Production-ready


### 🟡 Features

Type-safe SQL builder


### 🟡 Use

Alternative to sqlc


### 🟡 GitHub

`pydantic/pydantic-ai`


### 🟡 Status

Production-ready, modern


### 🟡 Features

Type-safe agents, LiteLLM integration


### 🟡 Use

Response quality analysis agent


### 🟡 Integration

Python framework


### 🟡 Website

`grpc.io`


### 🟡 Status

Industry standard


### 🟠 Features

Multi-language support, high-performance


### 🟡 Use

Go-Python bridge for MLX router


### 🟡 Integration

Protocol Buffers + code generation


### 🟡 RouteLLM (RECOMMENDED)




### 🟡 Semantic Router (RECOMMENDED)




### 🟡 Not-Diamond Awesome Routing




### 🔴 LiteLLM (CRITICAL)




### 🟡 NVIDIA LLM Router




### 🟡 MLX (RECOMMENDED for Apple Silicon)




### 🟡 MLX-LM




### 🟡 Ollama (ALTERNATIVE)




### 🟡 vLLM (ALTERNATIVE)




### 🟡 OpenCompass (RECOMMENDED)




### 🟡 EleutherAI LM Evaluation Harness




### 🟡 HuggingFace Datasets & Evaluate




### 🟡 Arena-Hard-Auto




### 🟡 Qdrant (RECOMMENDED)




### 🟡 Milvus (ALTERNATIVE)




### 🟡 Chromem-Go (LIGHTWEIGHT)




### 🟡 Neo4j (RECOMMENDED)




### 🟡 Memgraph (ALTERNATIVE)




### 🟡 HashiCorp go-retryablehttp (RECOMMENDED)




### 🟡 cenkalti/backoff (RECOMMENDED)




### 🟡 spaCy (RECOMMENDED)




### 🟡 Flair (ALTERNATIVE)




### 🟡 Sentence-Transformers (RECOMMENDED)




### 🟡 sqlc (RECOMMENDED)




### 🟡 go-jet (ALTERNATIVE)




### 🟡 Pydantic AI (RECOMMENDED)




### 🟡 gRPC (STANDARD)




### 🟡 Key Papers on LLM Routing




### 🟡 Phase 1: Foundation




### 🟡 Phase 2: Routing




### 🟡 Phase 3: Data




### 🟡 Phase 4: Learning




### 🟡 Phase 5: Integration




### 🟡 RouteLLM

(ICLR 2025): `arxiv.org/pdf/2406.18665`


### 🟡 Dynamic LLM Routing

(Feb 2025): `arxiv.org/abs/2502.16696`


### 🟡 IPR: Intelligent Prompt Routing

(2025): `arxiv.org/pdf/2509.06274`


### 🟡 Toward Super Agent System

(Apr 2025): `arxiv.org/html/2504.10519v1`


### 🟡 InferenceDynamics

(May 2025): `arxiv.org/html/2505.16303v1`


### 🟡 Learning to Route

(Oct 2025): `arxiv.org/html/2510.02388v1`


### 🟡 Evaluate

RouteLLM + Semantic Router for routing


### 🟡 Integrate

LiteLLM for provider abstraction


### 🟡 Setup

MLX or Ollama for local inference


### 🟡 Configure

OpenCompass for benchmarks


### 🟡 Deploy

Qdrant + Neo4j for data storage


### 🟡 Build

gRPC bridge for Go-Python communication


### 🟡 Create tasks.md:

```markdown



## 9. Architecture Overview

### 2.1 High-Level Architecture

````

┌─────────────────────────────────────────────────────────────────────────────────┐
│ SAIP Architecture │
├─────────────────────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ INGESTION LAYER (Spokes) │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │
│ │ │ HuggingFace │ │ Web Scrape │ │ Git Mining │ │ API Connectors │ │ │
│ │ │ Strategy │ │ Strategy │ │ Strategy │ │ Strategy │ │ │
│ │ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └────────┬────────┘ │ │
│ └─────────┼────────────────┼────────────────┼──────────────────┼───────────┘ │
│ └────────────────┴──────

## 10. Technical Requirements

- Use react
- Use gcp
- Use kubernetes
- Use docker
- Use rust
- Use javascript
- Use sql
- Use azure
- Use typescript
- Use flask

## 11. Integration Points

- **Integration with config**: Integration point with config project
- **Integration with Completion**: Integration point with Completion project
- **Integration with is**: Integration point with is project
- **Integration with better**: Integration point with better project
- **Integration with name**: Integration point with name project
- **Integration with priorities**: Integration point with priorities project
- **Integration with -**: Integration point with - project
- **Integration with 2**: Integration point with 2 project
- **Integration with context**: Integration point with context project
- **Integration with Onboarding**: Integration point with Onboarding project
- **Integration with maintainer**: Integration point with maintainer project
- **Integration with structure**: Integration point with structure project
- **Integration with root**: Integration point with root project
- **Integration with README**: Integration point with README project
- **Integration with Conventions**: Integration point with Conventions project
- **Integration with Context**: Integration point with Context project
- **Integration with goals**: Integration point with goals project
- **Integration with patterns**: Integration point with patterns project
- **Integration with Background**: Integration point with Background project
- **Integration with maintained**: Integration point with maintained project
- **Integration with adheres**: Integration point with adheres project
- **Integration with Index**: Integration point with Index project
- **Integration with 485**: Integration point with 485 project
- **Integration with LOC**: Integration point with LOC project
- **Integration with Vision**: Integration point with Vision project
- **Integration with by**: Integration point with by project
- **Integration with organization**: Integration point with organization project
- **Integration with roadmap**: Integration point with roadmap project
- **Integration with and**: Integration point with and project
- **Integration with Organization**: Integration point with Organization project
- **Integration with 3**: Integration point with 3 project
- **Integration with can**: Integration point with can project
- **Integration with ---**: Integration point with --- project
- **Integration with Structure**: Integration point with Structure project
- **Integration with Overview**: Integration point with Overview project
- **Integration with COMPLETE**: Integration point with COMPLETE project
- **Integration with with**: Integration point with with project
- **Integration with are**: Integration point with are project
- **Integration with overview**: Integration point with overview project
- **Integration with architecture**: Integration point with architecture project
- **Integration with style**: Integration point with style project
- **Integration with conventions**: Integration point with conventions project
- **Integration with success**: Integration point with success project
- **Integration with vllm**: Integration point with vllm project
- **Integration with go**: Integration point with go project
- **Integration with management**: Integration point with management project
- **Integration with remains**: Integration point with remains project
- **Integration with based**: Integration point with based project
- **Integration with when**: Integration point with when project
- **Integration with documentation**: Integration point with documentation project
- **Integration with has**: Integration point with has project
- **Integration with Goals**: Integration point with Goals project

## 12. Timeline & Phases

## 13. Milestones

## 14. Dependencies

## 16. Related Projects

- config
- Completion
- is
- better
- name
- priorities
- -
- 2
- context
- Onboarding
- maintainer
- structure
- root
- README
- Conventions
- Context
- goals
- patterns
- Background
- maintained
- adheres
- Index
- 485
- LOC
- Vision
- by
- organization
- roadmap
- and
- Organization
- 3
- can

---

- Structure
- Overview
- COMPLETE
- with
- are
- overview
- architecture
- style
- conventions
- success
- vllm
- go
- management
- remains
- based
- when
- documentation
- has
- Goals

## 17. Shared Features

- Caching
- Run Tests
- Test Coverage
- Audit Trail
- Status
- Input Sanitization
- Health Checks
- Logging
- Health Monitoring
- Redis Caching
- Documentation
- Issues
- Discussions
- Optimization
- Monitoring
- Unit Tests
- Integration Tests
- Enhanced Features
- Production Deployment
- Advanced Features
- Session Management:
- Security:
- Performance:
- Availability:
- Intelligent Routing
- Features
- Testing
- Go
- GitHub Issues
- Semantic Caching
- Getting Help
- Accuracy:
- Latency:
- Output:
- Input:
- Abilities:
- Formula:
- Score:
- For Users Who Want to Get Started
- For Developers Who Want to Understand the Code
- High-Level Flow
- Component Breakdown
- Source Code
- Database
- Arch-Router (Task Classification)
- MIRT-BERT (Cost-Quality Prediction)
- ExecutorRegistry (Model Unification)
- FeatureExtractor (Query Analysis)
- 1. Install Dependencies
- 2. Set up Database
- 3. Start MLX-LM Server
- 5. Integrate into CLIProxyAPI
- Basic Usage
- Testing Components Individually
- DualRouter
- ExecutorRegistry
- MIRT Client
- FeatureExtractor
- Expected Latency
- Run Benchmarks
- MLX-LM Server Not Responding
- MIRT Checkpoint Not Loading
- Feature Extraction Too Slow
- Integration Tests (Pending)
- Week 2: MLX-LM Integration
- Week 3: Vibeproxy UI
- Week 4: Testing & Optimization
- Week 5: Production
- For Technical Questions
- For Integration Issues
- For Performance Issues
- Read the Overview
- Follow Setup Guide
- Check Status
- Architecture Review
- Code Tour
- Check Examples
- Implementation
- AI Integration
- Validate
- Test Thoroughly
- GitHub
- Budget Tracking
- Resource Limits
- Components
- Learning
- Architecture
- Review
- Implement
- Error Classification
- Configuration
- CLI Reference:
- Community:
- Integrate
- Purpose
- Lines of Code
- MCP Protocol
- Structured Logging
- Metrics Collection
- 4. Docker Compose
- Deploy
- After:
- Check Health
- Current:
- Routing
- PostgreSQL
- NATS
- No performance impact
- Files Created
- Production
- Problem
- Solution
- Result
- Runtime:
- Local Testing:
- Load Tests
- Run All Tests
- Network:
- 3. Tests
- Verification
- Memory usage
- CPU usage
- 🚀 Performance Testing
- Short Term
- Long Term
- Tools
- Cause:
- 4.3 Authentication
- ✅ 2. Pre-commit Hooks
- Shell
- For deployment
- Day 1
- Build
- Kubernetes Probes
- Redis
- Metrics & Performance
- SLA & Compliance
- Performance Targets
- Website
- Setup
- Request Deduplication
- Recommendation:
- File locations:
- 3. DOCUMENTATION_INDEX.md (2.4 KB)
- Cost Optimization
- Pattern matching
- Use Cases
- GitHub Actions Integration
- What is MCP?
- Community Resources
- MCP servers
- Key Resources
- Connection Pooling
- No Breaking Changes
- Latency (p95):
- 4. Use
- Language:
- For DevOps
- Planned Enhancements
- Resources
- **Database Schema**
- **Key Components**
- 🔄 In Progress
- Semantic Router
- Cursor Agent
- MCP Architecture
- CLI Features
- Implementation Phases
- Auggie CLI Research
- This Summary
- Research Sources
- 2. Cursor Agent CLI Research
- For Community Engagement
- CLIProxyAPI Integration Opportunities
- Architecture Decisions
- Platforms
- Automation
- MCP Directory
- Key Findings
- 1.2 Core Architecture
- 1.3 System Requirements
- 2.1 Interactive Mode
- 3.2 MCP Transport Methods
- 8.2 MCP Server Security
- Official Documentation
- For CLIProxyAPI Maintainers
- For Integration Explorers
- Review this research
- Design MCP interface
- Prototype
- Explore
- Provide feedback
- 2.4 Output Formats
- 5.3 Security Best Practices
- Better User Experience
- Bug Fixes
- Communication
- Rollback Plan
- Thread-Safe
- Statistics
- Graceful Shutdown
- Memory Overhead
- TTL Management
- Cache Hit Rate
- Throughput
- Multiple Clients
- Days 1-2
- Staging Deployment
- Problem Solved
- What's Provided
- Integration Steps
- Performance Expectations
- Medium-term (Weeks 2-4)
- DYNAMIC_SERVICE_DISCOVERY_IMPLEMENTATION.md
- AGENTAPI_AUGGIE_CURSOR_REVIEW.md
- AGENTAPI_IMPLEMENTATION_PATTERNS.md
- AGENTAPI_REVIEW_SUMMARY.md
- What It Solves
- What It Provides
- Optimization Strategies
- WHEN
- THEN
- Routing Latency
- Code Written
- API Endpoints
- Week 4: Semantic Router Integration ✅
- Week 5: RouteLLM Integration ✅
- Week 6: Request Feature Extraction & Caching ✅
- Timeout
- What's Missing
- Infrastructure Layer
- sqlc
- Pattern Detection
- Rule Generation
- Week 9: Performance Tracking & Pattern Detection ✅
- Week 10: Rule Generation & Knowledge Graph ✅
- 4. Knowledge Graph
- Unit Tests Created (20 tests)
- RouteLLM
- Fallback Chain
- Budget-Based
- Migrations
- Vector DB
- Mitigation
- Backend
- Week 7: Provider-Specific Strategies
- Week 8: Task-Specific Rules & Integration
- Week 11: Infrastructure & Monitoring
- Week 12: Testing & Deployment
- Approve
- Your scale
- 1. Vector Search (pgvector)
- 2. Full-Text Search (FTS)
- Year 1-2
- Auto-Scaling
- SLA
- Automatic Failover
- Cache Efficiency
- Phase 2 Results
- Phase 2 Integration
- Phase 2 Testing
- Release
- Fallback Latency
- 4. Task-Specific Rules
- Auggie
- Method
- Issue
- Baseline
- Latency Breakdown
- External Services
- Functional Requirements
- End-to-End Tests
- Load Testing
- Security Testing
- Full-text search
- Neo4j
- Query Patterns
- Data Flow Diagram
- Dashboards (Grafana)
- Alerts
- Testing & validation
- Performance optimization
- Cache Performance
- Python Execution
- Phase 1: Foundation
- Configure
