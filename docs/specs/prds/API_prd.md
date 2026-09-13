# Product Requirements Document: API

**Version:** 1.0.0  
**Created:** 2026-02-18

## 1. Overview

Argis is a production-grade, intelligent LLM orchestration platform that unifies access to 18+ language model providers through a single, high-performance gateway. Built with Byzantine ensemble routing, semantic caching, and automatic tool discovery, Argis delivers **93%+ routing accuracy**, **85% cost reduction**, and **<5ms semantic fast-path response times**.

## 2. Objectives

## 3. Success Metrics

## 4. Stakeholders

## 5. Target Users

- admin
- Admin
- user

## 6. Functional Requirements

### FR-1: Intelligent Routing

Byzantine ensemble voting (10 diverse voters)

### FR-2: Cost Savings

Semantic caching + smart provider selection = 85% cost reduction

### FR-3: Speed

Sub-5ms cache lookups via ModernBERT embeddings + HNSW indices

### FR-4: Reliability

Automatic provider failover and distributed request handling

### FR-5: Tool Integration

1000+ MCP tools with automatic semantic discovery

### FR-6: Multi-LLM Support

18+ language model providers unified under one API

### FR-7: Type

HTTP Gateway

### FR-8: Features

OpenAI-compatible API, semantic cache, provider routing, GraphQL API

### FR-9: Performance

<100ms p99 response time

### FR-10: Providers

18+ LLM providers integrated

### FR-11: Docs

See `../argisroute/README.md`

### FR-12: Type

MCP Server

### FR-13: Features

Byzantine ensemble, tool registry, state hierarchy

### FR-14: Testing

78% unit test coverage (283/310 tests passing)

### FR-15: Async

Full async/await support

### FR-16: Docs

See `/argisexec/README.md`

### FR-17: Type

Monitoring & control API

### FR-18: Features

Configuration management, deployment orchestration, metrics

### FR-19: API

GraphQL + REST endpoints

### FR-20: Docs

See `/argisgate/docs/API_REFERENCE.md`

### FR-21: Type

macOS menu bar application

### FR-22: Features

Service lifecycle management, local request forwarding, configuration

### FR-23: Platform

macOS 10.15+

### FR-24: Docs

See `/argisagent/README.md`

### FR-25: Python

PEP 8, type hints, docstrings (Sphinx format)

### FR-26: Go

Effective Go, gofmt, golint

### FR-27: Rust

clippy, rustfmt

### FR-28: Test Coverage

> 80% for critical paths

### FR-29: File Size

≤500 lines per module (target ≤350)

### FR-30: Documentation

Update docs/ for all changes

### FR-31: Documentation

https://docs.argis.io

### FR-32: GitHub Issues

https://github.com/argis-io/argis/issues

### FR-33: Discord Community

https://discord.gg/argis

### FR-34: Email Support

support@argis.io

### FR-35: Office Hours

Every Wednesday at 10am PT

### FR-36: What is Argis?

### FR-37: Key Benefits

### FR-38: Prerequisites

### FR-39: Installation (5 minutes)

### FR-40: Verify Setup (Optional but Recommended)

### FR-41: First Request (30 seconds)

### FR-42: 4-Tier Architecture Diagram

### FR-43: Data Flow: Request Processing

### FR-44: 10+ Sub-Projects Overview

### FR-45: Component Details

### FR-46: Intelligent Routing

### FR-47: Semantic Caching

### FR-48: Tool Discovery

### FR-49: State Management

### FR-50: 1. Environment Setup

### FR-51: 2. Python Services (ArgisExec, ArgisGate)

### FR-52: 3. Go Services (ArgisRoute, ArgisHub)

### FR-53: 4. Rust Library (ArgisCores)

### FR-54: 5. Dashboard & Wizard

### FR-55: 6. Docker Deployment

### FR-56: Request Processing Pipeline

### FR-57: State Hierarchy Flow

### FR-58: Environment Variables

### FR-59: Service Configuration Files

### FR-60: Health Checks

### FR-61: Monitoring Dashboards

### FR-62: Metrics Available

### FR-63: OpenAI-Compatible Endpoints

### FR-64: GraphQL API (Advanced)

### FR-65: Setting Up Development Environment

### FR-66: Testing Strategy

### FR-67: Contribution Workflow

### FR-68: Code Standards

### FR-69: Common Issues

### FR-70: Debug Commands

### FR-71: Development Roadmap

### FR-72: Getting Help

### FR-73: Quick Links

### FR-74: License

### FR-75: Acknowledgments

### FR-76: Fork

the repository

### FR-77: Create

feature branch: `git checkout -b feature/xyz`

### FR-78: Make

changes following code style

### FR-79: Test

thoroughly: `pytest tests/`

### FR-80: Commit

with clear messages: `git commit -m "Add feature xyz"`

### FR-81: Push

to fork: `git push origin feature/xyz`

### FR-82: Create

pull request to main branch

### FR-83: Agent Management

Register, monitor, and control distributed host agents

### FR-84: Service Monitoring

Real-time health tracking and performance metrics

### FR-85: Alert System

Rule-based anomaly detection with multi-channel notifications

### FR-86: SLA Tracking

Uptime and availability monitoring for critical services

### FR-87: Authentication & Authorization

JWT-based auth with RBAC

### FR-88: WebSocket Support

Real-time status updates and log streaming

### FR-89: Infrastructure Health

Database, cache, and service dependency monitoring

### FR-90: Kubernetes Probes

Liveness (`/health/live`) and readiness (`/health/ready`)

### FR-91: Detailed Health

`/health` endpoint with database, cache, and service status

### FR-92: Service-Level Monitoring

Per-service health status and error rates

### FR-93: Email

SMTP-based notifications

### FR-94: Slack

Channel and direct message integration

### FR-95: Webhooks

Custom HTTP endpoints

### FR-96: System

In-app notifications

### FR-97: PostgreSQL

Persistent data storage (agents, alerts, configurations)

### FR-98: Redis

Session cache, service registry, pub/sub messaging

### FR-99: Prometheus

Metrics collection and monitoring

### FR-100: OpenTelemetry

Distributed tracing and observability

### FR-101: Slack

Alert notifications

### FR-102: DataDog

Log aggregation and APM

### FR-103: Line length

100 characters

### FR-104: Formatter

Black

### FR-105: Linter

Ruff

### FR-106: Type checker

mypy

### FR-107: Docstrings

Google style (see examples below)

### FR-108: [API Reference](docs/API_REFERENCE.md)

- Complete endpoint documentation

### FR-109: [Architecture Guide](docs/ARCHITECTURE.md)

- System design and patterns

### FR-110: [Deployment Guide](docs/DEPLOYMENT.md)

- Production deployment steps

### FR-111: [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

- Common issues and solutions

### FR-112: Issues

Report bugs and request features on GitHub

### FR-113: Discussions

Ask questions and discuss ideas

### FR-114: Email

team@argisgate.dev

### FR-115: Key Capabilities

### FR-116: Prerequisites

### FR-117: Local Development Setup

### FR-118: Quick Verification

### FR-119: 1. Agent Management

### FR-120: 2. Health Monitoring

### FR-121: 3. Alert System

### FR-122: 4. Anomaly Detection

### FR-123: 5. SLA Tracking

### FR-124: 6. Real-Time Updates via WebSocket

### FR-125: 7. Notification Channels

### FR-126: Three-Layer Design

### FR-127: Data Flow

### FR-128: Component Diagram

### FR-129: Health & Status

### FR-130: Agent Management

### FR-131: Metrics & Performance

### FR-132: Alerts & Monitoring

### FR-133: SLA & Compliance

### FR-134: Authentication

### FR-135: Infrastructure

### FR-136: WebSocket (Real-Time)

### FR-137: Environment Variables

### FR-138: Loading Configuration

### FR-139: Quick Test Run

### FR-140: Test Categories

### FR-141: Test Coverage

### FR-142: Writing Tests

### FR-143: Docker

### FR-144: Kubernetes

### FR-145: Production Checklist

### FR-146: Common Issues

### FR-147: Debugging

### FR-148: Key Integrations

### FR-149: Development Workflow

### FR-150: Code Style

### FR-151: Test Requirements

### FR-152: Pull Request Process

### FR-153: Documentation

### FR-154: Community

### FR-155: Performance Targets

### FR-156: Current Version: 0.1.0

### FR-157: Fork and clone

the repository

### FR-158: Create a feature branch

`git checkout -b feature/your-feature`

### FR-159: Install dev dependencies

`uv pip install -e ".[dev]"`

### FR-160: Make changes

following code style (see below)

### FR-161: Run tests

`pytest --cov=argisgate`

### FR-162: Run linting

`ruff check src/` and `mypy src/`

### FR-163: Format code

`black src/` and `ruff format src/`

### FR-164: Commit with clear message

`git commit -m "feat: description"`

### FR-165: Push and create PR

Target `main` branch

### FR-166: System Requirements Validation

- Detects OS, CPU cores, RAM, and validates compatibility

### FR-167: Host Registration

- Hostname input, agent type selection, and service configuration

### FR-168: Local Service Detection

- Automatically detects installed services (Ollama, PostgreSQL, Redis, etc.)

### FR-169: Cloud Provider Configuration

- Optional secure credential management for Supabase, Neo4j Aura, Upstash Redis, and Synadia NATS

### FR-170: Gateway Connection

- Gateway URL configuration with API key/OAuth/local-only authentication

### FR-171: Verification & Summary

- Final review and agent creation on the gateway

### FR-172: File Size

All components < 350 lines (target 300)

### FR-173: Initial Load

< 2 seconds on 4G

### FR-174: Step Navigation

Instant (client-side state)

### FR-175: API Calls

2 async operations (gateway health check, agent creation)

### FR-176: Memory

< 50MB footprint

### FR-177: Directory Structure

### FR-178: Type System

### FR-179: State Management

### FR-180: Basic Setup

### FR-181: API Integration

### FR-182: Design Tokens

### FR-183: Credential Encryption

### FR-184: Best Practices

### FR-185: Port Already in Use

### FR-186: Build Issues

### FR-187: Type Errors

### FR-188: 🎛️ Real-Time Agent Monitoring

- Live status updates, metrics visualization, and service lifecycle management

### FR-189: 📊 Advanced Analytics

- Uptime trends, service reliability scoring, resource heatmaps, cost estimation

### FR-190: 🚨 Intelligent Alerting System

- Rule-based alerts with channels, routing, deduplication, and throttling

### FR-191: 🎨 Custom Dashboard Widgets

- Drag-and-drop dashboard builder with 12+ widget types

### FR-192: 👥 RBAC (Role-Based Access Control)

- 4 roles (Admin, Viewer, Member, Guest) with 16 fine-grained permissions

### FR-193: 🌐 Workspace Management

- Create isolated workspaces with templates, layout customization, and state preservation

### FR-194: ⚡ Performance Optimized

- IndexedDB caching, request batching (70-90% reduction), virtual scrolling, WebSocket real-time updates

### FR-195: 🌓 Theme Support

- Dark and light mode with CSS variable-based customization

### FR-196: Node.js

18.0+

### FR-197: TypeScript

4.9+

### FR-198: React

18.0+

### FR-199: Python 3.10+

(for backend API)

### FR-200: Line Limit

500 lines per file (target 350)

### FR-201: TypeScript

Strict mode enforced

### FR-202: Browser Support

Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### FR-203: Performance

<500ms initial load, <100MB memory usage

### FR-204: Quick Start

`QUICK_START.md` - Phase 1 quick start

### FR-205: Phase 2 Guide

`PHASE2_QUICK_START.md` - Phase 2 features

### FR-206: Implementation Details

`DASHBOARD_IMPLEMENTATION.md` - Phase 1 architecture

### FR-207: Phase 2 Summary

`PHASE2_IMPLEMENTATION_SUMMARY.md` - Complete Phase 2 documentation

### FR-208: Main README

See `/Users/kooshapari/temp-PRODVERCEL/485/API/README.md`

### FR-209: API Reference

See `argisgate/docs/API_REFERENCE.md`

### FR-210: Backend Docs

See `argisexec/docs/`

### FR-211: [argisexec](/argisexec/)

- Python MCP server with Byzantine routing

### FR-212: [argisgate](/argisgate/)

- Python FastAPI gateway with monitoring

### FR-213: [argisroute](../argisroute/README.md)

- Go cloud API gateway (100K LOC)

### FR-214: [argisagent](/argisagent/)

- Swift macOS menu bar app

### FR-215: [argis-wizard](/argis-wizard/)

- Next.js setup wizard

### FR-216: Website

https://argis.io

### FR-217: Documentation

https://docs.argis.io

### FR-218: Email

support@argis.io

### FR-219: GitHub

https://github.com/argis-io/argis

### FR-220: Core Capabilities

### FR-221: Phase Breakdown

### FR-222: Prerequisites

### FR-223: Setup

### FR-224: Environment Variables

### FR-225: 1. Initialize Dashboard Service

### FR-226: 2. Use the Dashboard Component

### FR-227: 3. Or Use Components Individually

### FR-228: AgentGrid

### FR-229: AgentDetailPanel

### FR-230: MetricsChart

### FR-231: LogsViewer

### FR-232: ServiceControls

### FR-233: SettingsPanel

### FR-234: Workspace Management

### FR-235: Advanced Analytics

### FR-236: Intelligent Alerting

### FR-237: Custom Dashboard Widgets

### FR-238: Role-Based Access Control (RBAC)

### FR-239: IndexedDB Caching

### FR-240: Request Batching

### FR-241: Request Deduplication

### FR-242: Virtual Scrolling

### FR-243: Performance Targets

### FR-244: Key API Endpoints

### FR-245: Key Slices

### FR-246: Redux Hooks

### FR-247: Theme Variables

### FR-248: Switch Themes

### FR-249: useAgentData

### FR-250: useMetrics

### FR-251: useLogs

### FR-252: useOptimizedWebSocket

### FR-253: Run Tests

### FR-254: Test Structure

### FR-255: Code Quality

### FR-256: Project Constraints

### FR-257: Code Organization

### FR-258: Security Features

### FR-259: Building Desktop

### FR-260: Quick References

### FR-261: External Documentation

### FR-262: WebSocket Connection Issues

### FR-263: Metrics Not Loading

### FR-264: Performance Problems

### FR-265: Redux DevTools

### FR-266: Follow TypeScript

Use strict types, no `any`

### FR-267: Keep Files Small

Target 350 lines, max 500

### FR-268: Test Coverage

Aim for >80% on critical paths

### FR-269: Component Memoization

Use React.memo for performance

### FR-270: Redux Patterns

Use Redux Toolkit, avoid mutations

### FR-271: Type Safety

Leverage type system fully

### FR-272: Accessibility

Follow WCAG 2.1 AA standards

### FR-273: Service modules

(argis\*, separated by domain)

### FR-274: Documentation

(docs/, with good subdirectory structure)

### FR-275: Research/references

(research/, isolated by project)

### FR-276: Infrastructure

(infrastructure configs scattered)

### FR-277: Delete

`Makefile.bak` (use git history)

### FR-278: Move

`smartcp-docs-archive.tar.gz` → `docs/archive/`

### FR-279: Remove

all three (not needed)

### FR-280: Start here:

`docs/getting-started/`

### FR-281: Understand architecture:

`docs/architecture/`

### FR-282: Run project:

Root `Makefile` and `README.md`

### FR-283: Build guides:

`docs/guides/`

### FR-284: API reference:

`docs/api/`

### FR-285: Service code:

`argis<service>/src/`

### FR-286: Deployment:

`docs/operations/`

### FR-287: Infrastructure code:

`config/` (Docker, Postgres, Prometheus)

### FR-288: Monitoring:

`monitoring/` and `config/prometheus/`

### FR-289: Design docs:

`docs/design-docs/`

### FR-290: Reference implementations:

`research/`

### FR-291: Session tracking:

`docs/sessions/`

### FR-292: Agent patterns:

`docs/agent-guide/`

### FR-293: Session tracking:

`docs/sessions/<YYYYMMDD-name>/`

### FR-294: Codebase structure:

This report + `README.md`

### FR-295: Size:

20,787 files, 728MB

### FR-296: Cause:

Includes node_modules and build artifacts

### FR-297: Recommendation:

Add `.gitignore` patterns; consider separate build process

### FR-298: Size:

21,620 files, 6.5GB

### FR-299: Cause:

Multiple full reference implementations

### FR-300: Options:

1. Keep as reference (current)

### FR-301: Status:

Good separation by directory

### FR-302: Concern:

Cross-service dependencies need documentation

### FR-303: Recommendation:

Create dependency matrix in docs/

### FR-304: mypy_cache:

195MB

### FR-305: Recommendation:

Verify .gitignore; rebuild on clone

### FR-306: Note:

These are development-only, should not be committed

### FR-307: Immediate (Phase 1):

Cleanup (few hours)

### FR-308: Short-term (Phase 2):

Configuration organization (1-2 days)

### FR-309: Medium-term (Phase 3):

Documentation consolidation (2-3 days)

### FR-310: Ongoing (Phase 4):

Maintenance and governance

### FR-311: Current State (As of Jan 31, 2026)

### FR-312: Root Level Inventory

### FR-313: 2.1 Service Modules (Primary Components)

### FR-314: 2.2 Documentation & Knowledge

### FR-315: 2.3 Infrastructure & Configuration

### FR-316: 2.4 Cache & Build Artifacts (TO BE EXCLUDED)

### FR-317: 2.5 Empty/Stale Directories

### FR-318: 3.1 Current Organization Status

### FR-319: 3.2 Identified Organizational Improvements

### FR-320: 4.1 Root-Level Empty Directories

### FR-321: 4.2 Cache Directories (Should Be .gitignored)

### FR-322: 4.3 Build Artifacts

### FR-323: 4.4 Documentation Archives

### FR-324: Phase 1: Immediate Cleanup (Low Risk)

### FR-325: Phase 2: Configuration Organization (Medium Risk)

### FR-326: Phase 3: Documentation Consolidation (Medium-High Risk)

### FR-327: Phase 4: Research Organization (Low Priority)

### FR-328: 6.1 File Placement Guidelines

### FR-329: 6.2 Governance Policies

### FR-330: 6.3 Git Commit Strategy

### FR-331: 6.4 Documentation Updates Needed

### FR-332: For Different User Types

### FR-333: Common Navigation Paths

### FR-334: Final Metrics

### FR-335: Service Distribution

### FR-336: Documentation Distribution

### FR-337: Issue: Documentation Site Too Large

### FR-338: Issue: Research Directory Very Large

### FR-339: Issue: Service Isolation

### FR-340: Issue: Cache Directory Size

### FR-341: Remove empty directories:

````bash


### FR-342: Remove backup files:

```bash


### FR-343: Verify .gitignore covers cache:

```bash


### FR-344: Move archive file:

```bash


### FR-345: Create config structure:

```bash


### FR-346: Move configuration files:

```bash


### FR-347: Update references:

- Update `.github/workflows/` to new paths


### FR-348: Create symlinks (optional) for backward compatibility:

```bash


### FR-349: Consolidate documentation:

```bash


### FR-350: Organize session documentation:

- Prune old sessions (>90 days) to archive


### FR-351: Audit codex-upstream docs:

- Check if should be in main docs or stay isolated


### FR-352: Document research structure:

- Create `research/README.md` explaining each subdirectory


### FR-353: Consider extracting:

- Heavy dependencies (kilocode, goose) might be in separate repos


### FR-354: Keep root clean:

- Only: `.env*`, `README.md`, `CLAUDE.md`, core `Makefile`


### FR-355: Documentation standards:

- Every feature needs docs (in appropriate `docs/` subdirectory)


### FR-356: Service isolation:

- Services self-contained within `argis<service>/`


### FR-357: Regular maintenance:

- **Quarterly:** Review empty directories


### FR-358: Cleanup

- Remove empty directories and backup files


### FR-359: Consolidation

- Centralize configuration and documentation


### FR-360: Maintenance

- Establish ongoing governance policies


### FR-361: Navigation

- Make it easy for users to find what they need


### FR-362: Full Report:

`docs/FINAL_ORGANIZATION_REPORT.md` - Comprehensive analysis


### FR-363: Architecture:

`docs/architecture/` - System design documents


### FR-364: Guides:

`docs/guides/` - Feature-specific documentation


### FR-365: Getting Started:

`docs/getting-started/` - Onboarding materials


### FR-366: "How do I get started?"




### FR-367: "Where is the agent code?"




### FR-368: "Where is the execution engine?"




### FR-369: "Where are the API routes?"




### FR-370: "Where is the web dashboard?"




### FR-371: "Where are configuration files?"




### FR-372: "Where is documentation?"




### FR-373: "Where do I track agent work?"




### FR-374: "Where are tests?"




### FR-375: "Where is the design documentation?"




### FR-376: "Where are operations guides?"




### FR-377: Main Categories




### FR-378: New Contributor




### FR-379: Feature Developer




### FR-380: DevOps/Operations




### FR-381: Researcher




### FR-382: Agent/Automation




### FR-383: Service Code:

182,673 files (11.4 GB)


### FR-384: Documentation:

591 files (10 MB)


### FR-385: Research/References:

21,620 files (6.5 GB)


### FR-386: Infrastructure:

1,923 files (117 MB)


### FR-387: Build/Cache:

6,496 files (196 MB)


### FR-388: Sessions (work tracking):

150 files


### FR-389: Archive (legacy):

123 files


### FR-390: Specifications:

55 files


### FR-391: Architecture:

19 files


### FR-392: Reference:

18 files


### FR-393: Development guides:

17 files


### FR-394: Analysis:

13 files


### FR-395: Operations:

7 files


### FR-396: Feature guides:

6 files


### FR-397: File locations:

See `ORGANIZATION_QUICK_GUIDE.md`


### FR-398: Organization changes:

See "Implementation Roadmap" above


### FR-399: Documentation navigation:

See `DOCUMENTATION_INDEX.md`


### FR-400: Detailed analysis:

See `FINAL_ORGANIZATION_REPORT.md`


### FR-401: 1. FINAL_ORGANIZATION_REPORT.md (20 KB)




### FR-402: 2. ORGANIZATION_QUICK_GUIDE.md (7.4 KB)




### FR-403: 3. DOCUMENTATION_INDEX.md (2.4 KB)




### FR-404: Repository Composition




### FR-405: Main Services




### FR-406: Documentation by Category




### FR-407: Issue #1: Root-Level File Clutter




### FR-408: Issue #2: Empty Directories




### FR-409: Issue #3: Backup Files




### FR-410: Issue #4: Documentation Fragmentation




### FR-411: Phase 1: Immediate Cleanup (0.5-1 hours)




### FR-412: Phase 2: Configuration Organization (2-3 hours)




### FR-413: Phase 3: Documentation Consolidation (4-8 hours)




### FR-414: Phase 4: Ongoing Maintenance (ongoing)




### FR-415: New Developer




### FR-416: Feature Developer




### FR-417: DevOps/Operations




### FR-418: Agent/Automation




### FR-419: Finding Things




### FR-420: Common Commands




### FR-421: Read the appropriate guide:

- Quick overview? → `ORGANIZATION_QUICK_GUIDE.md`


### FR-422: Understand current structure:

- Review service layout in `ORGANIZATION_QUICK_GUIDE.md`


### FR-423: Plan changes (if applicable):

- Follow "Next Steps" section in `FINAL_ORGANIZATION_REPORT.md`


### FR-424: Maintain organization:

- Follow guidelines in Section 6 of full report


### FR-425: atoms

→ `build` and `check` commands per repo.


### FR-426: zen

→ `status` + `logs` quick diagnostics.


### FR-427: morph

→ `config` migration/generation + `init` workflows.


### FR-428: Intelligent Model Routing

- ML-powered selection of optimal models for tasks


### FR-429: Tool Integration

- Seamless integration with external services and APIs


### FR-430: Agent Framework

- Build sophisticated autonomous agents


### FR-431: Cost Optimization

- Minimize API costs through intelligent routing


### FR-432: Complete Observability

- Monitor performance, costs, and system health


### FR-433: Enterprise Security

- Role-based access control, audit logging, and compliance


### FR-434: [System Overview](architecture-diagrams/01_SYSTEM_OVERVIEW.md)

- High-level architecture


### FR-435: [Data Flow](architecture-diagrams/02_DATA_FLOW.md)

- How data moves through the system


### FR-436: [Microservices](architecture/MICROSERVICES_ARCHITECTURE.md)

- Service architecture


### FR-437: [Database Design](architecture-diagrams/06_DATABASE_ARCHITECTURE.md)

- Data persistence


### FR-438: [API Patterns](agent-guide/api-patterns.md)

- API design best practices


### FR-439: [Database Patterns](agent-guide/database-patterns.md)

- Data access patterns


### FR-440: [Testing Guide](agent-guide/testing-patterns.md)

- Testing strategies


### FR-441: [Async Patterns](agent-guide/async-patterns.md)

- Async/await best practices


### FR-442: [Agent Development](agent-guide/AGENTS.md)

- Building agents


### FR-443: [SmartCP API](reference/SMARTCP_INTERNAL_API.md)

- Core API specification


### FR-444: [Tool Optimization](reference/TOOL_CALL_OPTIMIZATION.md)

- Performance optimization


### FR-445: [Tool Discovery](reference/TOOL_DISCOVERY_COLD_START.md)

- Discovery mechanisms


### FR-446: [Analytics](reference/ANALYTICS_SYSTEM_ARCHITECTURE.md)

- Analytics system


### FR-447: [Master Specification](unified-specifications/MASTER_SPECIFICATION_2025.md)

- 2025 unified spec


### FR-448: [Epic PRDs](unified-specifications/)

- 50 detailed epic specifications (E1-E50)


### FR-449: [Implementation Checklist](unified-specifications/IMPLEMENTATION_CHECKLIST.md)

- Tracking


### FR-450: [Critical Gaps Analysis](research/CRITICAL_GAPS_ANALYSIS.md)

- System gaps and recommendations


### FR-451: [Comparative Analysis](research/DEEP_COMPARISON_ANALYSIS.md)

- Feature comparisons


### FR-452: [Cost Optimization](research/2025-agentic-ai-cost-optimization.md)

- Cost optimization research


### FR-453: Search

Use the search box at the top to find topics by keyword


### FR-454: Navigation Menu

Browse by category using the left sidebar


### FR-455: Breadcrumbs

See your location in the documentation hierarchy


### FR-456: Table of Contents

Navigate within documents using the right sidebar


### FR-457: Total Documentation

100+ comprehensive guides


### FR-458: Architecture Diagrams

7 detailed system diagrams


### FR-459: Development Patterns

8 major pattern guides


### FR-460: Product Specifications

50 detailed epic PRDs


### FR-461: Code Examples

50+ working code examples


### FR-462: Search Coverage

Full-text indexing of all content


### FR-463: Documentation Version

2.0


### FR-464: Last Updated

2025-01-31


### FR-465: Platform Version

Latest


### FR-466: Theme

Material for MkDocs


### FR-467: For Users (5 minutes)




### FR-468: For Developers (30 minutes)




### FR-469: For Operations (30-60 minutes)




### FR-470: Intelligent Routing




### FR-471: Tool Integration




### FR-472: Agent Framework




### FR-473: Architecture




### FR-474: Development




### FR-475: API Reference




### FR-476: Product Specifications




### FR-477: Research & Analysis




### FR-478: Documentation




### FR-479: Architecture




### FR-480: Development




### FR-481: Deployment & Operations




### FR-482: Product & Specifications




### FR-483: Research




### FR-484: Basic API Call




### FR-485: Using Tools




### FR-486: Building an Agent




### FR-487: How do I get started?




### FR-488: How do I deploy to production?




### FR-489: How do I build agents?




### FR-490: Where is the API reference?




### FR-491: How do I integrate external tools?




### FR-492: How do I optimize costs?




### FR-493: [Quick Start Guide](getting-started/quickstart.md)

- Get running in 5 minutes


### FR-494: [Installation Guide](INSTALLATION_END_USER_GUIDE.md)

- Detailed setup instructions


### FR-495: [First API Call](getting-started/quickstart.md#step-4-make-your-first-api-call-1-minute)

- Make your first request


### FR-496: [Architecture Overview](architecture/README.md)

- Understand the system design


### FR-497: [Development Guides](agent-guide/README.md)

- Learn development patterns


### FR-498: [API Reference](reference/SMARTCP_INTERNAL_API.md)

- Complete API documentation


### FR-499: [Code Examples](agent-guide/api-patterns.md)

- Practical examples


### FR-500: [Deployment Guide](DEPLOYMENT_GUIDE.md)

- Production deployment steps


### FR-501: [Security Setup](security/SECURITY_DEPLOYMENT_GUIDE.md)

- Secure configuration


### FR-502: [Configuration Guide](CLIENT_HOST_CONFIG.md)

- System configuration


### FR-503: [Monitoring](reference/ANALYTICS_SYSTEM_ARCHITECTURE.md)

- System monitoring


### FR-504: Report Issues

Found an error? Report it in your issue tracker


### FR-505: Suggest Improvements

Have an idea? Share your feedback


### FR-506: Add Examples

Help other developers with code examples


### FR-507: Improve Clarity

Help make documentation clearer


### FR-508: Search

the documentation using the search box


### FR-509: Browse

the [Getting Started](getting-started/overview.md) section


### FR-510: Check

relevant guides and examples


### FR-511: Review

the [FAQ](#faq) section above


### FR-512: Overwhelming?

→ Start with `ORGANIZATION_QUICK_GUIDE.md`


### FR-513: Need full details?

→ Read `FINAL_ORGANIZATION_REPORT.md`


### FR-514: Looking for something specific?

→ Use sections below


### FR-515: New to the project?

→ Start with `getting-started/`


### FR-516: FINAL_ORGANIZATION_REPORT.md

- Complete organizational analysis


### FR-517: ORGANIZATION_QUICK_GUIDE.md

- Fast reference guide


### FR-518: DOCUMENTATION_INDEX.md

- This file


### FR-519: New Contributor




### FR-520: Feature Developer




### FR-521: DevOps Engineer




### FR-522: Researcher/Agent




### FR-523: Exploration

Test multiple implementation approaches without fear of losing working code


### FR-524: Learning

Allow Claude to attempt complex refactorings with easy rollback


### FR-525: Experimentation

Try aggressive optimizations knowing you can instantly revert


### FR-526: Safety Net

Provides confidence for more ambitious AI-assisted changes


### FR-527: Frontend development

while another handles **backend API** implementation


### FR-528: Test writing

concurrent with **implementation**


### FR-529: Documentation generation

parallel to **code refactoring**


### FR-530: 5 sessions locally

in terminal (each with own git checkout)


### FR-531: 5-10 sessions

on Anthropic's web platform


### FR-532: 193-file refactors

consolidating 3 status fields into 1


### FR-533: State machine simplification

reducing 40 states to 5 across dozens of files


### FR-534: API signature changes

propagated across entire codebase


### FR-535: Pattern matching

Finding similar code structures


### FR-536: Semantic search

Understanding meaning and intent


### FR-537: Call hierarchy

Tracing function usage


### FR-538: Type relationships

Following type definitions and usage


### FR-539: Jump to definitions

Navigate to symbol definitions instantly


### FR-540: Find references

Locate all usage sites of functions/types


### FR-541: Type information

Access real-time type data


### FR-542: Error detection

See type errors immediately after edits


### FR-543: Symbol information

Hover-like info on demand


### FR-544: Traditional text search

~45 seconds to find all call sites


### FR-545: LSP-powered search

~50ms for same operation


### FR-546: Improvement

900x faster


### FR-547: 15-20 concurrent sessions

during active development


### FR-548: Separate git checkouts

for each local session (not branches/worktrees)


### FR-549: Team CLAUDE.md files

in git repositories document:


### FR-550: claude-code-workflows

Production workflows from AI-native startup


### FR-551: claude-code-spec-workflow

Spec-driven development automation


### FR-552: claude-code-action

GitHub PR/issue automation


### FR-553: Cursor

Claude Code extension enables "best of both worlds"—Cursor's IDE features + Claude's reasoning depth


### FR-554: Windsurf

Full Claude Code integration


### FR-555: VSCodium

Complete compatibility


### FR-556: Cursor

Wins on simplicity


### FR-557: Claude Code

Wins on reasoning depth


### FR-558: Windsurf

Wins on autonomy


### FR-559: OpenTelemetry Integration

For real-time metrics export


### FR-560: claude-code-otel

Comprehensive observability solution (OpenTelemetry-based)


### FR-561: Claude-Code-Usage-Monitor

Real-time usage monitor with predictions and warnings


### FR-562: Charts and visualizations

- **Forms for data input**


### FR-563: Dashboards

- **Interactive controls**


### FR-564: Built-in agents

Explore, Plan, general-purpose


### FR-565: Custom agents

Any from `.claude/agents/`


### FR-566: fork

Skill runs in isolation


### FR-567: inherit

Shares main agent context


### FR-568: Overview




### FR-569: Key Features




### FR-570: Design Philosophy




### FR-571: Use Cases




### FR-572: Practical Impact




### FR-573: Overview




### FR-574: Architecture




### FR-575: Parallel Execution Capabilities




### FR-576: Real-World Workflow




### FR-577: Performance Impact




### FR-578: Overview




### FR-579: Capabilities




### FR-580: Workflow Integration




### FR-581: Developer Experience




### FR-582: Key Design Principle




### FR-583: Overview




### FR-584: Core Capabilities




### FR-585: The Explore Sub-Agent




### FR-586: Search Strategies




### FR-587: Performance




### FR-588: Overview




### FR-589: Supported Languages (11 Total)




### FR-590: Key Capabilities




### FR-591: Performance Revolution




### FR-592: Setup Process




### FR-593: Community Ecosystem




### FR-594: Impact on Agentic Coding




### FR-595: Overview




### FR-596: Best Practices from Claude Code Creator (Boris Cherny)




### FR-597: Automation Capabilities




### FR-598: Community Frameworks




### FR-599: Philosophy




### FR-600: Overview




### FR-601: Supported Terminals




### FR-602: Setup Experience




### FR-603: Design Philosophy




### FR-604: Key Workflow Enhancement




### FR-605: Overview




### FR-606: VS Code Integration




### FR-607: JetBrains Support




### FR-608: VS Code Derivatives




### FR-609: Competitive Landscape (2026)




### FR-610: GitHub Actions Integration




### FR-611: Display Mode




### FR-612: Overview




### FR-613: Custom System Prompts




### FR-614: Hooks System




### FR-615: Configuration Levels




### FR-616: Key Hook Events




### FR-617: Real-World Examples




### FR-618: System Prompt Repository




### FR-619: Overview




### FR-620: API Endpoint




### FR-621: Key Metrics




### FR-622: Data Characteristics




### FR-623: Alternative Monitoring Options




### FR-624: Third-Party Tools




### FR-625: Use Cases




### FR-626: Overview




### FR-627: What is MCP?




### FR-628: MCP Apps (January 2026)




### FR-629: Claude Code Plugin Integration




### FR-630: Plugin Components




### FR-631: Example MCP Integrations




### FR-632: Discovery & Installation




### FR-633: Technical Architecture




### FR-634: Overview




### FR-635: Core Capabilities




### FR-636: Evolution Timeline




### FR-637: Architecture




### FR-638: Session Management




### FR-639: Integration Frameworks




### FR-640: Practical Usage Patterns




### FR-641: Real-World Examples




### FR-642: Overview




### FR-643: Major Update (January 2026)




### FR-644: Skills Architecture




### FR-645: Invocation Modes




### FR-646: Sub-Agent Integration




### FR-647: Advanced Features




### FR-648: Practical Examples




### FR-649: Discovery & Management




### FR-650: Community Resources




### FR-651: Output Styles

Persistent, file-based configurations


### FR-652: Prompt Appending

Add to Claude Code's default prompt


### FR-653: Fully Custom Prompts

Complete control over agent behavior


### FR-654: Command Hooks

(`type: "command"`): Run shell commands


### FR-655: Prompt Hooks

(`type: "prompt"`): Single-turn LLM evaluation


### FR-656: Agent Hooks

(`type: "agent"`): Spawn sub-agent with tools (Read, Grep, Glob)


### FR-657: Slash commands

Custom commands for workflows


### FR-658: Sub-agents

Specialized agents for domain tasks


### FR-659: MCP servers

Integrations to tools and data sources


### FR-660: Hooks

Workflow behavior modifications


### FR-661: Root-level files:

18 total (down from initial clutter)


### FR-662: Documentation files created:

5 comprehensive guides


### FR-663: Empty directories identified:

2-3 (ready for cleanup)


### FR-664: Potential cleanup items:

4-5 files


### FR-665: Status:

Ready for Phase 1 implementation


### FR-666: Current Size:

0 bytes (empty)


### FR-667: Type:

Cache directory


### FR-668: Justification:

- Empty/unused cache directory


### FR-669: Git Command:

`git rm -r --cached .mcp_token_cache/ 2>/dev/null || true && rmdir .mcp_token_cache/`


### FR-670: Risk Level:

NONE


### FR-671: Impact:

Root cleaner, no functional impact


### FR-672: Current Size:

992 KB archive


### FR-673: Type:

Legacy documentation archive


### FR-674: Current Location:

Root (not found in current state)


### FR-675: Recommendation:

- If present: Move to `docs/archive/` or delete


### FR-676: Justification:

Archive files clutter root; should be in versioned directory


### FR-677: Risk Level:

LOW (historical backup)


### FR-678: Impact:

Better organization, reclaim space


### FR-679: Phase 1:

Remove empty directories, improve .gitignore


### FR-680: Phase 2:

Consolidate configuration files to config/ directory


### FR-681: Phase 3:

Organize and index documentation


### FR-682: Key Metrics




### FR-683: Root Directory Analysis




### FR-684: Detailed Cleanup Impact




### FR-685: Already Moved (From Initial Organization)




### FR-686: Planned Moves (Phase 2 - Not Yet Implemented)




### FR-687: Already Deleted (Pre-Cleanup)




### FR-688: Planned Deletions (Phase 1 - Ready to Implement)




### FR-689: Items to Exclude (Not Delete)




### FR-690: Current Root Files (18 Total)




### FR-691: Visual Root Structure (Target State)




### FR-692: Current Structure (26 directories at root)




### FR-693: Planned Structure (After Cleanup)




### FR-694: Directory Count Changes




### FR-695: Empty/Placeholder Directories (Ready for Cleanup)




### FR-696: Prerequisites




### FR-697: Phase 1: Immediate Cleanup (Ready Now)




### FR-698: Phase 2: Optional Configuration Consolidation (2-3 weeks)




### FR-699: Phase 3: Documentation Consolidation (Optional - 4-8 hours)




### FR-700: Pull Request Creation




### FR-701: Quick Verification (5 minutes)




### FR-702: Comprehensive Verification (15 minutes)




### FR-703: Post-Cleanup Validation




### FR-704: Git Verification




### FR-705: Immediate Actions (This Week)




### FR-706: Short-term (2-4 weeks)




### FR-707: Medium-term (This month)




### FR-708: Phase 1 Risk Matrix




### FR-709: Phase 2 Risk Matrix




### FR-710: Phase 3 Risk Matrix




### FR-711: Rollback Procedure




### FR-712: Files Created During Analysis




### FR-713: Key Resources




### FR-714: Cleanup Success Criteria




### FR-715: Documentation Success Criteria




### FR-716: Repository Composition




### FR-717: Service Breakdown




### FR-718: Cleanup Impact




### FR-719: Q: Why create organization documents if the cleanup isn't implemented?




### FR-720: Q: What if implementation breaks something?




### FR-721: Q: How long does Phase 1 cleanup take?




### FR-722: Q: What's the priority order for implementation?




### FR-723: Q: Who should implement these changes?




### FR-724: Q: Are there any service disruptions?




### FR-725: Questions About Cleanup




### FR-726: Reporting Issues




### FR-727: Pre-Implementation




### FR-728: Phase 1 Execution




### FR-729: Phase 2 Execution




### FR-730: Phase 3 Execution




### FR-731: Post-Implementation




### FR-732: FINAL_ORGANIZATION_REPORT.md

- From: Root directory (generated Jan 31)


### FR-733: ORGANIZATION_QUICK_GUIDE.md

- From: Root directory (generated Jan 31)


### FR-734: README_ORGANIZATION.md

- From: Root directory (generated Jan 31)


### FR-735: DOCUMENTATION_INDEX.md

- From: Root directory (generated Jan 31)


### FR-736: Review Documentation

(20 minutes)


### FR-737: Approve Cleanup Plan

(Team decision)


### FR-738: Execute Phase 1

(30 minutes - if approved)


### FR-739: Plan Phase 2

(Configuration consolidation)


### FR-740: Execute Phase 2

(2-3 hours - if approved)


### FR-741: Complete Phase 3

(Documentation)


### FR-742: Ongoing Maintenance

- [ ] Quarterly directory review


### FR-743: Phase 1 (High):

Remove empty dirs, improve .gitignore


### FR-744: Phase 2 (Medium):

Consolidate configuration files


### FR-745: Phase 3 (Low):

Archive and reorganize documentation


### FR-746: Client (Laptop)




### FR-747: Hybrid Monolith (Default)




### FR-748: Cloud Distributed




### FR-749: Responsibility

primary purpose of the folder.


### FR-750: Exposes

interfaces/APIs produced here.


### FR-751: Consumes

external/internal services it depends on.


### FR-752: Responsibility

Stateless MCP server; validates requests, forwards to Bifrost.


### FR-753: Key subfolders

(representative; follow hexagonal layering):


### FR-754: Exposes

MCP server, health endpoint.


### FR-755: Consumes

Bifrost GraphQL/gRPC; Supabase Auth JWKs; optional local SLM runtime addresses for capability discovery.


### FR-756: Responsibility

Customizations layered on official Bifrost.


### FR-757: Highlights

- `server/`, `services/`: Extension resolvers (executor, memory, state) and router logic.


### FR-758: Exposes

GraphQL/gRPC endpoints (through Bifrost), routing hooks.


### FR-759: Consumes

Supabase (cloud), optional local Postgres, Redis/NATS/Neo4j (cloud-first), local SLMs.


### FR-760: Responsibility

Upstream Bifrost core (do not modify here).


### FR-761: Useful subdirs

`framework/` (plugin system), `core/` (routing), `transports/` (GraphQL/gRPC), `plugins/` (example integrations), `ui/` (reference UI), `helm-charts/` (deploys).


### FR-762: Exposes

GraphQL/gRPC; plugin contracts used by bifrost-extensions.


### FR-763: Responsibility

Installer/bundling and management UI. Acts as presentation layer; bundles SmartCP client and config profiles.


### FR-764: Exposes

Desktop UI, feature selection during install (SmartCP, Bifrost, local Postgres, Redis, SLMs), management console post-install.


### FR-765: Consumes

SmartCP endpoint, Bifrost endpoint, Cloudflare Tunnel config, local OS for service control.


### FR-766: Responsibility

Upstream Go services for agent/CLI access. Imported as modules; avoid code changes.


### FR-767: Exposes

REST/gRPC per upstream; no persistence locally.


### FR-768: Consumes

Bifrost, Supabase Auth, logging/metrics stacks.


### FR-769: Responsibility

SQL migrations, policies, and config scaffolding for the Supabase cloud project (auth + Postgres + pgvector).


### FR-770: Exposes

Schema, RLS policies, seed data.


### FR-771: Consumes

Supabase cloud instance.


### FR-772: docs/

Source markdowns, architecture notes, sessions.


### FR-773: docs-site/

Node-based static site build; uses `package.json` scripts for generation.


### FR-774: Responsibility

Research/reference repository (not runtime code). Use as knowledge base.


### FR-775: Responsibility

Helper shell/Node scripts for lint/format/build.


### FR-776: Responsibility

Planning artifacts and workstreams.


### FR-777: Primary Role

Reserved for shared utilities and common code used across multiple Argis components


### FR-778: Intended Use

- Common constants and configurations


### FR-779: Empty

Yes, no files currently present


### FR-780: Has Hidden Files

No (confirmed via `ls -lah`)


### FR-781: Referenced In

Makefile (indirectly through project structure), documentation


### FR-782: Should Keep

✅ **YES**


### FR-783: Primary Role

Reserved directory for compiled artifacts and build outputs


### FR-784: Intended Use

- Python wheel distributions (`.whl` files)


### FR-785: Empty

Yes, no files currently present


### FR-786: Has Hidden Files

No (confirmed via `ls -lah`)


### FR-787: Referenced In

Documentation, implied in Makefile build targets


### FR-788: Should Keep

✅ **YES**


### FR-789: Rebranding Complete

`docs/development/migration/REBRANDING_COMPLETE_SUMMARY.md`


### FR-790: Final Report

`docs/development/migration/REBRANDING_FINAL_REPORT.md`


### FR-791: Rebranding Success

`docs/development/migration/REBRANDING_SUCCESS.md`


### FR-792: `argis/`

Reserved for cross-component shared utilities


### FR-793: `argis-build/`

Reserved for build artifacts and compiled outputs


### FR-794: 1. `/argis/` - Shared Utilities Directory




### FR-795: 2. `/argis-build/` - Build Artifacts Directory




### FR-796: Python Distributions




### FR-797: Go Binaries




### FR-798: Build Metadata




### FR-799: Docker Images




### FR-800: Immediate Actions




### FR-801: Verification Commands




### FR-802: Related Documentation




### FR-803: `/Users/kooshapari/temp-PRODVERCEL/485/API/argis/`

2. **`/Users/kooshapari/temp-PRODVERCEL/485/API/argis-build/`**


### FR-804: Do NOT delete

either directory - they serve important architectural purposes


### FR-805: Add `.gitkeep`

to both directories to ensure they're tracked in git


### FR-806: Add documentation

explaining their intended purpose


### FR-807: Add `.gitignore`

to `argis-build/` to prevent accidental commits of build artifacts


### FR-808: Update

CI/CD pipelines to use `argis-build/` for artifact staging if not already configured


### FR-809: 18+ LLM Providers

OpenAI, Claude, Gemini, Vertex AI, Cohere, Anthropic, Mistral, and more


### FR-810: OpenAI-Compatible API

Drop-in replacement for OpenAI SDK via `/v1/chat/completions` endpoint


### FR-811: Semantic Caching

Cache LLM responses by semantic similarity, reducing costs and latency


### FR-812: GraphQL API

Full GraphQL support for complex queries alongside REST


### FR-813: Intelligent Routing

ML-based provider selection based on cost, latency, and quality


### FR-814: Zero Vendor Lock-in

Consumes Bifrost as an unmodified Go module


### FR-815: Production Deployment

Built-in support for Fly.io, Vercel, Railway, Render, and Homebox


### FR-816: Go 1.24.3+

- **PostgreSQL 15+** (for session/cache storage)


### FR-817: Redis 7+

(optional, for distributed caching)


### FR-818: Docker

(optional, for local development)


### FR-819: Cost

Minimize expenses by selecting cheapest suitable provider


### FR-820: Latency

Route to fastest providers for real-time applications


### FR-821: Model Availability

Fall back to alternative providers if primary unavailable


### FR-822: Quality

Use fine-tuned models for specialized tasks


### FR-823: User Preferences

Honor model/provider selections


### FR-824: Rate Limits

Distribute load across providers


### FR-825: Token counting

Know exact token usage before API calls


### FR-826: Cost tracking

Understand spending per user/organization


### FR-827: Rate limiting

Enforce usage quotas


### FR-828: Audit logging

Complete history of API calls


### FR-829: Multi-tenancy

Support multiple orgs/teams with isolation


### FR-830: Metrics

Prometheus-compatible metrics endpoint


### FR-831: Logging

Structured JSON logging with request tracing


### FR-832: Tracing

OpenTelemetry integration (coming soon)


### FR-833: Dashboards

Pre-built Grafana dashboards


### FR-834: Documentation

[docs/README.md](docs/README.md)


### FR-835: Issues

[GitHub Issues](https://github.com/kooshapari/argisroute/issues)


### FR-836: Discussions

[GitHub Discussions](https://github.com/kooshapari/argisroute/discussions)


### FR-837: Email

support@example.com


### FR-838: [Bifrost](https://github.com/maximhq/bifrost)

- Core LLM gateway (upstream)


### FR-839: [Cliproxy](https://github.com/kooshapari/cliproxy)

- CLI proxy abstraction


### FR-840: [API Module](../API/)

- Main API layer (Python/FastAPI)


### FR-841: Key Characteristics




### FR-842: Prerequisites




### FR-843: Local Development




### FR-844: Docker Development




### FR-845: System Design




### FR-846: Clean Extension Layer Pattern




### FR-847: 1. OpenAI-Compatible API




### FR-848: 2. Semantic Caching




### FR-849: 3. Intelligent Routing




### FR-850: 4. GraphQL API




### FR-851: 5. Research & Evaluation Tools




### FR-852: 6. Session Management




### FR-853: 7. Observability




### FR-854: Environment Variables




### FR-855: Configuration File (YAML)




### FR-856: Chat Completion (OpenAI-Compatible)




### FR-857: Embeddings




### FR-858: GraphQL Query




### FR-859: List Models




### FR-860: Health Check




### FR-861: Fly.io (Recommended)




### FR-862: Docker




### FR-863: Kubernetes




### FR-864: Vercel (Serverless)




### FR-865: Building




### FR-866: Testing




### FR-867: Database




### FR-868: Code Quality




### FR-869: Built-in Plugins




### FR-870: Custom Plugins




### FR-871: Prometheus Metrics




### FR-872: Structured Logging




### FR-873: Health Checks




### FR-874: Common Issues




### FR-875: Intelligent Router

- ML-based provider selection


### FR-876: Learning

- Continuously learn from provider performance


### FR-877: Smart Fallback

- Automatic failover with retry logic


### FR-878: Registry Cache

- Cache provider configurations


### FR-879: Passing Tests

283/310 unit tests (91% pass rate)


### FR-880: Coverage

78% (1,204/1,543 lines covered)


### FR-881: Gap

339 lines to cover


### FR-882: Target Gap

~150 lines (to reach 85%)


### FR-883: Tests Missing

~100-150 tests needed


### FR-884: Phase 3

Integration tests (80 tests) - Multi-module workflows


### FR-885: Phase 4

E2E tests (65 tests) - Full system workflows


### FR-886: Approach




### FR-887: Files to Enhance (Priority Order)




### FR-888: Task 1: Enhance test_namespace.py




### FR-889: Task 2: Enhance test_sandbox_extended.py




### FR-890: Task 3: Enhance test_scope_storage_extended.py




### FR-891: Task 4: Enhance test_scope_manager.py




### FR-892: Task 5: Enhance test_mcp_manager.py




### FR-893: Task 6: Enhance test_events_bus.py




### FR-894: Task 7: Enhance test_background.py




### FR-895: Task 8: Enhance test_execute.py




### FR-896: Task 9: Enhance test_middleware.py




### FR-897: Task 10: Enhance test_core.py




### FR-898: Step 1: Run Baseline Coverage




### FR-899: Step 2: Implement Task 1-10 in Order




### FR-900: Step 3: Re-run Full Coverage After Each Task




### FR-901: Step 4: Verify 85%+ Coverage Achieved




### FR-902: tests/unit/runtime/test_namespace.py

(8 → 15 tests)


### FR-903: tests/unit/runtime/test_sandbox_extended.py

(40+ → 50+ tests)


### FR-904: tests/unit/runtime/test_scope_storage_extended.py

(60+ → 75+ tests)


### FR-905: tests/unit/runtime/test_scope_manager.py

(20 → 30 tests)


### FR-906: tests/unit/runtime/test_mcp_manager.py

(15 → 25 tests)


### FR-907: tests/unit/runtime/test_events_bus.py

(10 → 20 tests)


### FR-908: tests/unit/runtime/test_background.py

(10 → 20 tests)


### FR-909: tests/unit/tools/test_execute.py

(12 → 20 tests)


### FR-910: tests/unit/auth/test_middleware.py

(15 → 25 tests)


### FR-911: tests/unit/runtime/test_core.py

(10 → 18 tests)


### FR-912: Protocol

FastMCP 2.13 (stateless HTTP)


### FR-913: Purpose

MCP protocol frontend


### FR-914: Entry Point

`ArgisExecServer.create()`


### FR-915: Tools

Single `execute` tool that uses AgentRuntime


### FR-916: Framework

FastAPI


### FR-917: Purpose

REST API endpoints for tool routing, search, etc.


### FR-918: Entry Point

`app` (FastAPI application)


### FR-919: Endpoints

`/health`, `/route`, `/tools`, `/semantic-search`


### FR-920: Purpose

GraphQL client for Bifrost backend delegation


### FR-921: Used By

Both `server.py` and `main.py`


### FR-922: Default URL

`http://localhost:8080/graphql`


### FR-923: MCP Server (`server.py`)




### FR-924: HTTP API (`main.py`)




### FR-925: Bifrost Client (`bifrost_client.py`)




### FR-926: `server.py`

- MCP Server (FastMCP protocol)


### FR-927: `main.py`

- FastAPI HTTP API (REST endpoints)


### FR-928: Overall Coverage

71.1%


### FR-929: Tests Collected

642


### FR-930: Tests Passing

~252-320 (post-asyncio fix)


### FR-931: Critical Infrastructure Fixed

pytest-asyncio plugin registration


### FR-932: Problem

Async test methods in classes were not being recognized


### FR-933: Root Cause

pytest.ini in tests/ subdirectory was overriding root pytest.ini


### FR-934: Solution

- Moved pytest.ini to project root


### FR-935: runtime/namespace

Need 8-10 tests (currently few)


### FR-936: runtime/events/background

Need 10-12 tests


### FR-937: runtime/events/bus

Need 10-12 tests


### FR-938: runtime/scope/storage

Need 25-30 tests (largest module)


### FR-939: runtime/sandbox

Need 20-25 tests


### FR-940: runtime/mcp/manager

Need 8-10 tests


### FR-941: runtime/core

Need 10-12 tests


### FR-942: runtime/events/api

Need 8-10 tests


### FR-943: runtime/mcp/api

Need 6-8 tests


### FR-944: tools/execute

Need 8-10 tests


### FR-945: runtime/scope/api

Need 8-10 tests


### FR-946: runtime/scope/manager

Need 12-15 tests


### FR-947: 1. pytest-asyncio Plugin Registration




### FR-948: 2. Pytest Version Compatibility




### FR-949: Critical Path Modules (0-40% coverage) - HIGHEST PRIORITY




### FR-950: Medium Coverage Modules (40-80%) - SECONDARY PRIORITY




### FR-951: Well-Covered Modules (80-100%) - MAINTAIN




### FR-952: Current Distribution Estimate




### FR-953: Required Test Breakdown by Coverage Zone




### FR-954: 1. **runtime/namespace** (26.6%)




### FR-955: 2. **runtime/events/background** (29.5%)




### FR-956: 3. **runtime/events/bus** (33.3%)




### FR-957: 4. **runtime/scope/storage** (36.1%) - LARGEST GAP




### FR-958: 5. **runtime/scope/manager** (37.0%)




### FR-959: 6. **runtime/sandbox** (37.3%)




### FR-960: 7. **runtime/mcp/manager** (38.5%)




### FR-961: 8. **runtime/core** (50.0%)




### FR-962: Phase 1: Fix Failing Tests (Target: 95%+ pass rate)




### FR-963: Phase 2: Unit Tests for Critical Path (0-40% coverage)




### FR-964: Phase 3: Unit Tests for Medium Coverage (40-80%)




### FR-965: Phase 4: Integration & E2E Tests




### FR-966: Identify all failing tests

```bash


### FR-967: Categorize failures

- Missing mock implementations


### FR-968: Fix by category

(prioritize):


### FR-969: Validation

```bash


### FR-970: Immediate

(now):


### FR-971: Hour 1-3

- Fix all AsyncIO test issues (DONE)


### FR-972: Hour 4-11

- Implement unit tests for critical path modules


### FR-973: Hour 12-21

- Implement unit tests for medium coverage modules


### FR-974: Validation

- Run full coverage report


### FR-975: Zero Startup Latency

No code generation or heavy initialization


### FR-976: RequestDirector

Stateless HTTP request building using openapi-core


### FR-977: Pre-calculated Schemas

All complex processing done during parsing


### FR-978: Single Code Path

All components use RequestDirector consistently


### FR-979: No Fallbacks

Simplified architecture without hybrid complexity


### FR-980: Performance First

Optimized for cold starts and serverless deployments


### FR-981: openapi-core Integration

Leverages proven library for parameter serialization


### FR-982: Full Feature Support

Complete OpenAPI 3.0/3.1 support including deepObject


### FR-983: Error Handling

Comprehensive HTTP error mapping to MCP errors


### FR-984: Advantages

Zero latency, robust, comprehensive OpenAPI support


### FR-985: Advantages

High performance, simplified architecture, reliable error handling


### FR-986: Automatic Suffixing

Colliding parameters get location-based suffixes


### FR-987: Example

`id` in path and body becomes `id__path` and `id`


### FR-988: Transparent

LLMs see suffixed parameters, implementation routes correctly


### FR-989: Native Support

Generated client handles all deepObject variations


### FR-990: Explode Handling

Proper support for explode=true/false


### FR-991: Complex Objects

Nested object serialization works correctly


### FR-992: Status Code Mapping

HTTP errors mapped to appropriate MCP errors


### FR-993: Structured Responses

Error details preserved in tool results


### FR-994: Timeout Handling

Network timeouts handled gracefully


### FR-995: Parameter Validation

Invalid parameters caught during request building


### FR-996: Schema Validation

openapi-core validates all OpenAPI constraints


### FR-997: Graceful Degradation

Missing optional parameters handled smoothly


### FR-998: Connection Pooling

HTTP connections reused across requests


### FR-999: Client Caching

Generated clients cached for performance


### FR-1000: Async Support

Full async/await throughout


### FR-1001: Pre-calculated Schemas

All complex processing done during initialization


### FR-1002: Parameter Mapping

Collision resolution handled upfront


### FR-1003: Zero Latency

No runtime code generation or complex schema processing


### FR-1004: Same Interface

Public API unchanged from legacy implementation


### FR-1005: Performance Improvement

Significantly faster initialization


### FR-1006: No Breaking Changes

Existing code works without modification


### FR-1007: RequestDirector Initialization

Success/failure of RequestDirector setup


### FR-1008: Schema Pre-calculation

Pre-calculated schema and parameter map status


### FR-1009: Request Building

Parameter mapping and URL construction details


### FR-1010: Performance Metrics

Request timing and error rates


### FR-1011: Core Components




### FR-1012: Key Architecture Principles




### FR-1013: RequestDirector-Based Components




### FR-1014: `FastMCPOpenAPI` Class




### FR-1015: Component Creation Logic




### FR-1016: Stateless Request Building




### FR-1017: 1. Enhanced Parameter Handling




### FR-1018: 2. Robust Error Handling




### FR-1019: 3. Performance Optimizations




### FR-1020: Server Options




### FR-1021: Route Mapping Customization




### FR-1022: Test Structure




### FR-1023: Testing Philosophy




### FR-1024: Example Test Pattern




### FR-1025: From Legacy Implementation




### FR-1026: Backward Compatibility




### FR-1027: Logging




### FR-1028: Key Log Messages




### FR-1029: Debugging Common Issues




### FR-1030: Planned Features




### FR-1031: Performance Improvements




### FR-1032: `server.py`

- `FastMCPOpenAPI` main server class with RequestDirector integration


### FR-1033: `components.py`

- Simplified component implementations using RequestDirector


### FR-1034: `routing.py`

- Route mapping and component selection logic


### FR-1035: Spec Parsing

OpenAPI spec parsed to `HTTPRoute` models with pre-calculated schemas


### FR-1036: RequestDirector Setup

openapi-core Spec initialized for request building


### FR-1037: Component Creation

Create components with RequestDirector reference


### FR-1038: Request Building

RequestDirector builds HTTP request from flat parameters


### FR-1039: Request Execution

Execute request with httpx client


### FR-1040: Response Processing

Return structured MCP response


### FR-1041: Real Integration

Test with real OpenAPI specs and HTTP clients


### FR-1042: Minimal Mocking

Only mock external API endpoints


### FR-1043: Behavioral Focus

Test behavior, not implementation details


### FR-1044: Performance Focus

Test that initialization is fast and stateless


### FR-1045: Eliminated Startup Latency

Zero code generation overhead (100-200ms improvement)


### FR-1046: Better OpenAPI Compliance

openapi-core handles all OpenAPI features correctly


### FR-1047: Serverless Friendly

Perfect for cold-start environments


### FR-1048: Simplified Architecture

Single RequestDirector approach eliminates complexity


### FR-1049: Enhanced Reliability

No dynamic code generation failures


### FR-1050: RequestDirector Initialization Fails

- Check OpenAPI spec validity with `openapi-core`


### FR-1051: Parameter Issues

- Enable debug logging for parameter processing


### FR-1052: Performance Issues

- Monitor RequestDirector request building timing


### FR-1053: Advanced Caching

Intelligent response caching with TTL


### FR-1054: Streaming Support

Handle streaming API responses


### FR-1055: Batch Operations

Optimize multiple operation calls


### FR-1056: Enhanced Monitoring

Detailed metrics and health checks


### FR-1057: Configuration Management

Dynamic configuration updates


### FR-1058: Enhanced Schema Caching

More aggressive schema pre-calculation


### FR-1059: Parallel Processing

Concurrent operation execution


### FR-1060: Memory Optimization

Further reduce memory footprint


### FR-1061: Request Optimization

Smart request batching and deduplication


### FR-1062: Schema Pre-calculation

Combined schemas calculated once during parsing


### FR-1063: Parameter Mapping

Collision resolution mapping calculated upfront


### FR-1064: Zero Runtime Overhead

All complex processing done during initialization


### FR-1065: No Code Generation

Eliminates 100-200ms startup latency


### FR-1066: Serverless Friendly

Ideal for cold-start environments


### FR-1067: Minimal Dependencies

Uses lightweight `openapi-core` instead of full client generation


### FR-1068: Parameter Collisions

Intelligent collision resolution with suffixing


### FR-1069: DeepObject Style

Full support for deepObject parameters with explode=true/false


### FR-1070: Complex Schemas

Handles nested objects, arrays, and all OpenAPI types


### FR-1071: Pre-calculated Mapping

Parameter location mapping done upfront for performance


### FR-1072: Pre-calculated Schemas

Combined parameter and body schemas calculated once


### FR-1073: Collision-aware

Automatically handles parameter name collisions


### FR-1074: Type Safety

Full Pydantic model validation


### FR-1075: Performance

Zero runtime schema processing overhead


### FR-1076: Real Objects

Use real HTTPRoute models and OpenAPI specifications


### FR-1077: Minimal Mocking

Only mock external HTTP endpoints


### FR-1078: Performance Focus

Test that initialization is fast and stateless


### FR-1079: Behavioral Testing

Verify OpenAPI compliance without implementation details


### FR-1080: Cold Start

Zero latency penalty for serverless deployments


### FR-1081: Memory Usage

Lower memory footprint without generated client code


### FR-1082: Reliability

No dynamic code generation failures


### FR-1083: Maintainability

Simpler architecture with fewer moving parts


### FR-1084: Core Components




### FR-1085: Key Architecture Principles




### FR-1086: Initialization Process




### FR-1087: Request Processing




### FR-1088: 1. High-Performance Request Building




### FR-1089: 2. Comprehensive Parameter Support




### FR-1090: 3. Enhanced Error Handling




### FR-1091: 4. Advanced Schema Processing




### FR-1092: Server Components (`/server/openapi_new/`)




### FR-1093: RequestDirector Integration




### FR-1094: Basic Server Setup




### FR-1095: Direct RequestDirector Usage




### FR-1096: Test Categories




### FR-1097: Testing Philosophy




### FR-1098: From Legacy Implementation




### FR-1099: Performance Improvements




### FR-1100: Planned Features




### FR-1101: Performance Improvements




### FR-1102: Common Issues




### FR-1103: Debugging




### FR-1104: `director.py`

- `RequestDirector` for stateless HTTP request building


### FR-1105: `parser.py`

- OpenAPI spec parsing and route extraction with pre-calculated schemas


### FR-1106: `schemas.py`

- Schema processing with parameter mapping for collision handling


### FR-1107: `models.py`

- Enhanced data models with pre-calculated fields for performance


### FR-1108: `formatters.py`

- Response formatting and processing utilities


### FR-1109: Input

Raw OpenAPI specification (dict)


### FR-1110: Parsing

Extract operations to `HTTPRoute` models


### FR-1111: Pre-calculation

Generate combined schemas and parameter maps during parsing


### FR-1112: Director Setup

Create `RequestDirector` with `SchemaPath` for request building


### FR-1113: Tool Invocation

FastMCP receives tool call with parameters


### FR-1114: Request Building

RequestDirector builds HTTP request using parameter map


### FR-1115: Parameter Handling

openapi-core handles all OpenAPI serialization rules


### FR-1116: Response Processing

Parse response into structured format with proper error handling


### FR-1117: `OpenAPITool`

- Simplified tool implementation using RequestDirector


### FR-1118: `OpenAPIResource`

- Resource implementation with RequestDirector


### FR-1119: `OpenAPIResourceTemplate`

- Resource template with RequestDirector support


### FR-1120: `FastMCPOpenAPI`

- Main server class with stateless request building


### FR-1121: Core Functionality

- `test_server.py` - Server initialization and RequestDirector integration


### FR-1122: OpenAPI Features

- `test_parameter_collisions.py` - Parameter name collision handling


### FR-1123: Import Changes

```python


### FR-1124: Constructor

Same interface, no changes needed


### FR-1125: Automatic Benefits

- Eliminates startup latency (100-200ms improvement)


### FR-1126: Response Streaming

Handle streaming API responses


### FR-1127: Enhanced Authentication

More auth provider integrations


### FR-1128: Advanced Metrics

Detailed request/response monitoring


### FR-1129: Schema Validation

Enhanced input/output validation


### FR-1130: Batch Operations

Optimized multi-operation requests


### FR-1131: Schema Caching

More aggressive schema pre-calculation


### FR-1132: Memory Optimization

Further reduce memory footprint


### FR-1133: Request Batching

Smart batching for bulk operations


### FR-1134: Connection Optimization

Enhanced connection pooling strategies


### FR-1135: RequestDirector Initialization Fails

- Check OpenAPI spec validity with `jsonschema-path`


### FR-1136: Parameter Mapping Issues

- Check parameter collision resolution in debug logs


### FR-1137: Request Building Errors

- Check network connectivity to target API


### FR-1138: Zero Startup Latency

No code generation or heavy initialization


### FR-1139: RequestDirector

Stateless HTTP request building using openapi-core


### FR-1140: Pre-calculated Schemas

All complex processing done during parsing


### FR-1141: Single Code Path

All components use RequestDirector consistently


### FR-1142: No Fallbacks

Simplified architecture without hybrid complexity


### FR-1143: Performance First

Optimized for cold starts and serverless deployments


### FR-1144: openapi-core Integration

Leverages proven library for parameter serialization


### FR-1145: Full Feature Support

Complete OpenAPI 3.0/3.1 support including deepObject


### FR-1146: Error Handling

Comprehensive HTTP error mapping to MCP errors


### FR-1147: Advantages

Zero latency, robust, comprehensive OpenAPI support


### FR-1148: Advantages

High performance, simplified architecture, reliable error handling


### FR-1149: Automatic Suffixing

Colliding parameters get location-based suffixes


### FR-1150: Example

`id` in path and body becomes `id__path` and `id`


### FR-1151: Transparent

LLMs see suffixed parameters, implementation routes correctly


### FR-1152: Native Support

Generated client handles all deepObject variations


### FR-1153: Explode Handling

Proper support for explode=true/false


### FR-1154: Complex Objects

Nested object serialization works correctly


### FR-1155: Status Code Mapping

HTTP errors mapped to appropriate MCP errors


### FR-1156: Structured Responses

Error details preserved in tool results


### FR-1157: Timeout Handling

Network timeouts handled gracefully


### FR-1158: Parameter Validation

Invalid parameters caught during request building


### FR-1159: Schema Validation

openapi-core validates all OpenAPI constraints


### FR-1160: Graceful Degradation

Missing optional parameters handled smoothly


### FR-1161: Connection Pooling

HTTP connections reused across requests


### FR-1162: Client Caching

Generated clients cached for performance


### FR-1163: Async Support

Full async/await throughout


### FR-1164: Pre-calculated Schemas

All complex processing done during initialization


### FR-1165: Parameter Mapping

Collision resolution handled upfront


### FR-1166: Zero Latency

No runtime code generation or complex schema processing


### FR-1167: Same Interface

Public API unchanged from legacy implementation


### FR-1168: Performance Improvement

Significantly faster initialization


### FR-1169: No Breaking Changes

Existing code works without modification


### FR-1170: RequestDirector Initialization

Success/failure of RequestDirector setup


### FR-1171: Schema Pre-calculation

Pre-calculated schema and parameter map status


### FR-1172: Request Building

Parameter mapping and URL construction details


### FR-1173: Performance Metrics

Request timing and error rates


### FR-1174: Core Components




### FR-1175: Key Architecture Principles




### FR-1176: RequestDirector-Based Components




### FR-1177: `FastMCPOpenAPI` Class




### FR-1178: Component Creation Logic




### FR-1179: Stateless Request Building




### FR-1180: 1. Enhanced Parameter Handling




### FR-1181: 2. Robust Error Handling




### FR-1182: 3. Performance Optimizations




### FR-1183: Server Options




### FR-1184: Route Mapping Customization




### FR-1185: Test Structure




### FR-1186: Testing Philosophy




### FR-1187: Example Test Pattern




### FR-1188: From Legacy Implementation




### FR-1189: Backward Compatibility




### FR-1190: Logging




### FR-1191: Key Log Messages




### FR-1192: Debugging Common Issues




### FR-1193: Planned Features




### FR-1194: Performance Improvements




### FR-1195: `server.py`

- `FastMCPOpenAPI` main server class with RequestDirector integration


### FR-1196: `components.py`

- Simplified component implementations using RequestDirector


### FR-1197: `routing.py`

- Route mapping and component selection logic


### FR-1198: Spec Parsing

OpenAPI spec parsed to `HTTPRoute` models with pre-calculated schemas


### FR-1199: RequestDirector Setup

openapi-core Spec initialized for request building


### FR-1200: Component Creation

Create components with RequestDirector reference


### FR-1201: Request Building

RequestDirector builds HTTP request from flat parameters


### FR-1202: Request Execution

Execute request with httpx client


### FR-1203: Response Processing

Return structured MCP response


### FR-1204: Real Integration

Test with real OpenAPI specs and HTTP clients


### FR-1205: Minimal Mocking

Only mock external API endpoints


### FR-1206: Behavioral Focus

Test behavior, not implementation details


### FR-1207: Performance Focus

Test that initialization is fast and stateless


### FR-1208: Eliminated Startup Latency

Zero code generation overhead (100-200ms improvement)


### FR-1209: Better OpenAPI Compliance

openapi-core handles all OpenAPI features correctly


### FR-1210: Serverless Friendly

Perfect for cold-start environments


### FR-1211: Simplified Architecture

Single RequestDirector approach eliminates complexity


### FR-1212: Enhanced Reliability

No dynamic code generation failures


### FR-1213: RequestDirector Initialization Fails

- Check OpenAPI spec validity with `openapi-core`


### FR-1214: Parameter Issues

- Enable debug logging for parameter processing


### FR-1215: Performance Issues

- Monitor RequestDirector request building timing


### FR-1216: Advanced Caching

Intelligent response caching with TTL


### FR-1217: Streaming Support

Handle streaming API responses


### FR-1218: Batch Operations

Optimize multiple operation calls


### FR-1219: Enhanced Monitoring

Detailed metrics and health checks


### FR-1220: Configuration Management

Dynamic configuration updates


### FR-1221: Enhanced Schema Caching

More aggressive schema pre-calculation


### FR-1222: Parallel Processing

Concurrent operation execution


### FR-1223: Memory Optimization

Further reduce memory footprint


### FR-1224: Request Optimization

Smart request batching and deduplication


### FR-1225: Schema Pre-calculation

Combined schemas calculated once during parsing


### FR-1226: Parameter Mapping

Collision resolution mapping calculated upfront


### FR-1227: Zero Runtime Overhead

All complex processing done during initialization


### FR-1228: No Code Generation

Eliminates 100-200ms startup latency


### FR-1229: Serverless Friendly

Ideal for cold-start environments


### FR-1230: Minimal Dependencies

Uses lightweight `openapi-core` instead of full client generation


### FR-1231: Parameter Collisions

Intelligent collision resolution with suffixing


### FR-1232: DeepObject Style

Full support for deepObject parameters with explode=true/false


### FR-1233: Complex Schemas

Handles nested objects, arrays, and all OpenAPI types


### FR-1234: Pre-calculated Mapping

Parameter location mapping done upfront for performance


### FR-1235: Pre-calculated Schemas

Combined parameter and body schemas calculated once


### FR-1236: Collision-aware

Automatically handles parameter name collisions


### FR-1237: Type Safety

Full Pydantic model validation


### FR-1238: Performance

Zero runtime schema processing overhead


### FR-1239: Real Objects

Use real HTTPRoute models and OpenAPI specifications


### FR-1240: Minimal Mocking

Only mock external HTTP endpoints


### FR-1241: Performance Focus

Test that initialization is fast and stateless


### FR-1242: Behavioral Testing

Verify OpenAPI compliance without implementation details


### FR-1243: Core Components




### FR-1244: Key Architecture Principles




### FR-1245: Initialization Process




### FR-1246: Request Processing




### FR-1247: 1. High-Performance Request Building




### FR-1248: 2. Comprehensive Parameter Support




### FR-1249: 3. Enhanced Error Handling




### FR-1250: 4. Advanced Schema Processing




### FR-1251: Server Components (`/server/openapi/`)




### FR-1252: RequestDirector Integration




### FR-1253: Basic Server Setup




### FR-1254: Direct RequestDirector Usage




### FR-1255: Test Categories




### FR-1256: Testing Philosophy




### FR-1257: Planned Features




### FR-1258: Performance Improvements




### FR-1259: Common Issues




### FR-1260: Debugging




### FR-1261: `director.py`

- `RequestDirector` for stateless HTTP request building


### FR-1262: `parser.py`

- OpenAPI spec parsing and route extraction with pre-calculated schemas


### FR-1263: `schemas.py`

- Schema processing with parameter mapping for collision handling


### FR-1264: `models.py`

- Enhanced data models with pre-calculated fields for performance


### FR-1265: `formatters.py`

- Response formatting and processing utilities


### FR-1266: Input

Raw OpenAPI specification (dict)


### FR-1267: Parsing

Extract operations to `HTTPRoute` models


### FR-1268: Pre-calculation

Generate combined schemas and parameter maps during parsing


### FR-1269: Director Setup

Create `RequestDirector` with `SchemaPath` for request building


### FR-1270: Tool Invocation

FastMCP receives tool call with parameters


### FR-1271: Request Building

RequestDirector builds HTTP request using parameter map


### FR-1272: Parameter Handling

openapi-core handles all OpenAPI serialization rules


### FR-1273: Response Processing

Parse response into structured format with proper error handling


### FR-1274: `OpenAPITool`

- Simplified tool implementation using RequestDirector


### FR-1275: `OpenAPIResource`

- Resource implementation with RequestDirector


### FR-1276: `OpenAPIResourceTemplate`

- Resource template with RequestDirector support


### FR-1277: `FastMCPOpenAPI`

- Main server class with stateless request building


### FR-1278: Core Functionality

- `test_server.py` - Server initialization and RequestDirector integration


### FR-1279: OpenAPI Features

- `test_parameter_collisions.py` - Parameter name collision handling


### FR-1280: Response Streaming

Handle streaming API responses


### FR-1281: Enhanced Authentication

More auth provider integrations


### FR-1282: Advanced Metrics

Detailed request/response monitoring


### FR-1283: Schema Validation

Enhanced input/output validation


### FR-1284: Batch Operations

Optimized multi-operation requests


### FR-1285: Schema Caching

More aggressive schema pre-calculation


### FR-1286: Memory Optimization

Further reduce memory footprint


### FR-1287: Request Batching

Smart batching for bulk operations


### FR-1288: Connection Optimization

Enhanced connection pooling strategies


### FR-1289: RequestDirector Initialization Fails

- Check OpenAPI spec validity with `jsonschema-path`


### FR-1290: Parameter Mapping Issues

- Check parameter collision resolution in debug logs


### FR-1291: Request Building Errors

- Check network connectivity to target API


### FR-1292: [Installation Guide](https://vllm-semantic-router.com/docs/installation/)

- Complete setup instructions


### FR-1293: [System Architecture](https://vllm-semantic-router.com/docs/overview/architecture/system-architecture/)

- Technical deep dive


### FR-1294: [Model Training](https://vllm-semantic-router.com/docs/training/training-overview/)

- How classification models work


### FR-1295: [API Reference](https://vllm-semantic-router.com/docs/api/router/)

- Complete API documentation


### FR-1296: [Dashboard](https://vllm-semantic-router.com/docs/overview/dashboard)

- vLLM Semantic Router Dashboard


### FR-1297: First Tuesday of the month

9:00-10:00 AM EST (accommodates US EST, EU, and Asia Pacific contributors)


### FR-1298: Third Tuesday of the month

1:00-2:00 PM EST (accommodates US EST and California contributors)


### FR-1299: Intelligent Routing 🧠




### FR-1300: Enterprise Security 🔒




### FR-1301: vLLM Semantic Router Dashboard 💬




### FR-1302: Community Meetings 📅




### FR-1303: Code Generation:

Kilo can generate code using natural language.


### FR-1304: Task Automation:

Kilo can automate repetitive coding tasks.


### FR-1305: Automated Refactoring:

Kilo can refactor and improve existing code.


### FR-1306: MCP Server Marketplace

Kilo can easily find, and use MCP servers to extend the agent capabilities.


### FR-1307: Multi Mode

Plan with Architect, Code with Coder, and Debug with Debugger, and make your own custom modes.


### FR-1308: 80% reduction in input tokens

- Dramatically lower costs and faster responses


### FR-1309: Self-learning

- Automatically discovers and categorizes API response patterns


### FR-1310: Smart filtering

- Pins important fields, removes noise, ghosts redundant data


### FR-1311: Drop-in replacement

- Works with existing MCP servers (Node.js-based)


### FR-1312: Community-driven

- Share your learned schemas in `registry.json`


### FR-1313: Pinned

📌 - Essential fields always included (e.g., `id`, `title`, `state`)


### FR-1314: Noise

🔇 - Redundant fields removed (e.g., `_links`, `imageUrl`, `descriptor`)


### FR-1315: Ghosts

👻 - Fields summarized or count-only (e.g., long lists, nested objects)


### FR-1316: Key Benefits




### FR-1317: 1. Install Dependencies




### FR-1318: 2. Configure Servers




### FR-1319: 3. Set Up Claude Desktop Integration




### FR-1320: 4. Start Using




### FR-1321: Current Support




### FR-1322: Coming Soon




### FR-1323: servers.json Structure




### FR-1324: registry.json Structure




### FR-1325: Application-Scoped Components




### FR-1326: Request-Scoped Components




### FR-1327: 1. `get_feature_extractor_dep()`




### FR-1328: 2. `RequestContext`




### FR-1329: 3. `get_request_context()`




### FR-1330: Example 1: Basic FastAPI Route Integration




### FR-1331: Example 2: Direct FeatureExtractor Usage




### FR-1332: Example 3: Advanced Context with Metadata




### FR-1333: Example 4: Integration with Existing Routes




### FR-1334: FeatureExtractor (Application-Scoped)




### FR-1335: RequestContext (Request-Scoped)




### FR-1336: Unit Test Example




### FR-1337: Integration Test Example




### FR-1338: From Old Dependencies (prediction.ml_models)




### FR-1339: Benefits of Migration




### FR-1340: Common Issues




### FR-1341: Automatic Singleton Management

- No manual global state


### FR-1342: Request-Scoped Caching

- Features computed once per request


### FR-1343: FastAPI Integration

- Native dependency injection


### FR-1344: Thread-Safety

- Built-in fine-grained locking


### FR-1345: Performance Tracking

- Automatic timing and metrics


### FR-1346: Better Testing

- Easy to mock and test


### FR-1347: Always initialize context early:

```python


### FR-1348: Extract features once per request:

```python


### FR-1349: Store routing metadata:

```python


### FR-1350: Log comprehensive context:

```python


### FR-1351: Use for performance tracking:

```python


### FR-1352: 70% ML Predictor

- Learned from historical performance


### FR-1353: 30% Thompson Sampling Bandit

- Exploration/exploitation


### FR-1354: Live Request Simulation

- Test different routing strategies with pre-configured prompts


### FR-1355: Cost Comparison

- Visualize cost savings across different routing strategies


### FR-1356: Performance Analysis

- Compare model performance metrics


### FR-1357: Model Routing

- See how different task types are routed to optimal models


### FR-1358: Cost Reduction:

85-90% vs. direct premium model usage (vs 70-85% rule-based)


### FR-1359: Latency (p95):

<3000ms (including ML prediction + routing)


### FR-1360: Success Rate:

99%+ with fallback


### FR-1361: Quality Retention:

95-99% (vs 90-95% baseline)


### FR-1362: Fallback Rate:

5-10% (vs 10-20% baseline)


### FR-1363: Prediction Accuracy:

85-90% (XGBoost)


### FR-1364: Bandit Exploration:

30% of decisions


### FR-1365: Training Data:

30-90 days historical


### FR-1366: Retraining Frequency:

Weekly (automated)


### FR-1367: Not Diamond

- Model selection recommendation


### FR-1368: OpenRouter

- Multi-provider aggregation


### FR-1369: FastAPI

- Modern Python web framework


### FR-1370: Pydantic

- Data validation


### FR-1371: All LLM providers

- Making AI accessible


### FR-1372: [KROUTE.md](./KROUTE.md)

- Architecture Blueprint


### FR-1373: [PLAN.md](./PLAN.md)

- Master Planning Document


### FR-1374: Key Features




### FR-1375: 1. Clone and Configure




### FR-1376: 2. Start with Docker Compose




### FR-1377: 3. Verify




### FR-1378: 4. Use




### FR-1379: Proxy Mode (Direct OpenRouter)




### FR-1380: Unified CLI workflow




### FR-1381: Quick Start with ML




### FR-1382: How It Works




### FR-1383: Expected Impact




### FR-1384: ML System Components




### FR-1385: Primary Documents




### FR-1386: ML & Analytics Documentation ✅ **NEW**




### FR-1387: Implementation Reports




### FR-1388: Research & Analysis




### FR-1389: Milestone Reports




### FR-1390: Implementation Tracking




### FR-1391: Examples




### FR-1392: Prerequisites




### FR-1393: Installation




### FR-1394: Usage




### FR-1395: Configuration




### FR-1396: Free-First Policy




### FR-1397: Full-Spectrum Policy




### FR-1398: Advanced Reasoning




### FR-1399: Web Search Integration




### FR-1400: Combined Features




### FR-1401: High-Level Flow (with ML)




### FR-1402: Directory Structure




### FR-1403: Phase 1: Core System ✅ COMPLETE




### FR-1404: Phase 2: ML Optimization ✅ COMPLETE




### FR-1405: Phase 3: Future Enhancements 🔮




### FR-1406: Running the Demo




### FR-1407: Demo Features




### FR-1408: Demo Endpoint




### FR-1409: Key Metrics




### FR-1410: Usage Analytics




### FR-1411: ML Metrics & Insights




### FR-1412: Metrics Database




### FR-1413: [PLAN.md](./PLAN.md)

- Master Planning Document ✅ **COMPLETE**


### FR-1414: [KROUTE.md](./KROUTE.md)

- Complete Architecture Blueprint


### FR-1415: [DEPLOYMENT.md](./DEPLOYMENT.md)

- Production Deployment Guide ✅


### FR-1416: [METRICS_SYSTEM_COMPLETE.md](./METRICS_SYSTEM_COMPLETE.md)

- ML System Overview ✅ **NEW**


### FR-1417: [METRICS_ANALYSIS_SPEC.md](./METRICS_ANALYSIS_SPEC.md)

- Technical Specification ✅ **NEW**


### FR-1418: [METRICS_QUICKSTART.md](./METRICS_QUICKSTART.md)

- Quick Start Guide ✅ **NEW**


### FR-1419: [docs/OPENROUTER_RESPONSES_API.md](./docs/OPENROUTER_RESPONSES_API.md)

- Responses API Alpha ✅ **NEW**


### FR-1420: [docs/METRICS_SYSTEM_DIAGRAM.md](./docs/METRICS_SYSTEM_DIAGRAM.md)

- Architecture Diagrams ✅ **NEW**


### FR-1421: [WEEK2_PROGRESS.md](./WEEK2_PROGRESS.md)

- Analysis Implementation ✅ **NEW**


### FR-1422: [WEEK3_COMPLETE.md](./WEEK3_COMPLETE.md)

- ML Implementation ✅ **NEW**


### FR-1423: [ROUTELLM_ANALYSIS.md](./ROUTELLM_ANALYSIS.md)

- RouteLLM Integration ✅


### FR-1424: [METRICS_RESEARCH.md](./METRICS_RESEARCH.md)

- Metrics Research ✅ **NEW**


### FR-1425: Milestone Completion Reports

✅ **ALL COMPLETE**


### FR-1426: [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)

- Complete WBS ✅ **100% COMPLETE**


### FR-1427: [METRICS_IMPLEMENTATION_STATUS.md](./METRICS_IMPLEMENTATION_STATUS.md)

- ML System Status ✅ **NEW**


### FR-1428: [examples/basic_usage.py](./examples/basic_usage.py)

- Usage Examples ✅


### FR-1429: Minimum:

NVIDIA Volta (V100, compute 7.0+)


### FR-1430: Recommended:

NVIDIA Ampere (A10G, A100, compute 8.0+)


### FR-1431: CUDA Version:

12.0+


### FR-1432: PyTorch Version:

2.0+


### FR-1433: Language:

English only (non-English may produce unreliable results)


### FR-1434: Length:

1-512 tokens (longer prompts truncated)


### FR-1435: Encoding:

UTF-8


### FR-1436: Format:

Plain text (markdown/code formatting preserved)


### FR-1437: GPU:

NVIDIA Volta (V100) or newer, compute 7.0+


### FR-1438: CUDA:

12.0+


### FR-1439: Python:

3.10+


### FR-1440: PyTorch:

2.0+


### FR-1441: Transformers:

4.30+


### FR-1442: Memory:

4 GB GPU VRAM (FP16, batch 1)


### FR-1443: GPU:

NVIDIA Ampere (A10G, A100)


### FR-1444: CUDA:

12.2+


### FR-1445: Python:

3.11


### FR-1446: PyTorch:

2.2+


### FR-1447: Memory:

8 GB GPU VRAM (FP16, batch 32)


### FR-1448: LOCAL

(1-5ms, $0): On-device models, fastest, lowest quality


### FR-1449: FAST

(5-50ms, baseline cost): Cloud models with minimal latency


### FR-1450: BALANCED

(50-500ms, 2x cost): Balanced performance and accuracy


### FR-1451: QUALITY

(100ms+, 5x cost): High-quality models, best accuracy


### FR-1452: REASONING

(500ms+, 10x cost): Extended reasoning models


### FR-1453: 1. RoutingTier (Enum)




### FR-1454: 2. ProviderCapabilities (Enum)




### FR-1455: 3. CapabilityLevel (Enum)




### FR-1456: 4. ModelSpec (Dataclass)




### FR-1457: 5. RoutingConstraints (Dataclass)




### FR-1458: 6. UnifiedRoutingDecision (Dataclass)




### FR-1459: 7. CapabilitySupport (Dataclass)




### FR-1460: Example 1: Model Selection




### FR-1461: Example 2: Fallback Strategy




### FR-1462: Example 3: Cost Analysis




### FR-1463: 1. Replacing Old Decision Types




### FR-1464: 2. Replacing Capability Checks




### FR-1465: 3. Constraint Validation




### FR-1466: Single Source of Truth

All routing types defined in one module


### FR-1467: Type Safety

Full type hints throughout


### FR-1468: Immutability

Frozen dataclasses where appropriate


### FR-1469: Composition

Complex types built from simpler ones


### FR-1470: Validation

Post-init validation for invariants


### FR-1471: Serialization

`.to_dict()` methods for logging/APIs


### FR-1472: Extensibility

`metadata` fields for future use


### FR-1473: Documentation

Comprehensive docstrings and examples


### FR-1474: CI/CD Dashboard:

Workflow success rates, execution times


### FR-1475: Test Dashboard:

Test counts, coverage trends, flaky tests


### FR-1476: Performance Dashboard:

Response times, throughput, resource usage


### FR-1477: Deployment Dashboard:

Frequency, success rate, rollbacks


### FR-1478: Documentation:

`/docs` directory


### FR-1479: Slack:

#router-ci-cd


### FR-1480: Team Wiki:

https://wiki.internal/router/cicd


### FR-1481: GitHub Issues:

Report bugs/feature requests


### FR-1482: On-call:

https://pagerduty.com/schedules/router-oncall


### FR-1483: Tech Lead:

@tech-lead


### FR-1484: DevOps Team:

@devops


### FR-1485: Security Team:

security@example.com


### FR-1486: For Developers




### FR-1487: For DevOps




### FR-1488: ✅ Automated Testing




### FR-1489: 🔒 Security & Quality




### FR-1490: ⚡ Performance




### FR-1491: 🔄 Compatibility




### FR-1492: 🚀 Deployment




### FR-1493: 📢 Notifications




### FR-1494: Getting Started




### FR-1495: Setup & Configuration




### FR-1496: Operations




### FR-1497: Run Tests Locally




### FR-1498: Run Workflows Locally




### FR-1499: Trigger Workflows Manually




### FR-1500: Check Workflow Status




### FR-1501: Key Metrics




### FR-1502: Dashboards




### FR-1503: Required Secrets




### FR-1504: Security Features




### FR-1505: For Developers




### FR-1506: For DevOps




### FR-1507: Common Issues




### FR-1508: Get Help




### FR-1509: Planned Enhancements




### FR-1510: Workflow Changes




### FR-1511: Documentation




### FR-1512: Resources




### FR-1513: Contacts




### FR-1514: Run tests locally before pushing

```bash


### FR-1515: Keep PRs small and focused

- Single feature/fix per PR


### FR-1516: Watch CI results

```bash


### FR-1517: Fix failures immediately

- Don't merge with failing tests


### FR-1518: Monitor CI/CD health

- Weekly review of failed workflows


### FR-1519: Maintain baselines

- Update after optimizations


### FR-1520: Deploy safely

- Always to staging first


### FR-1521: Communicate

- Notify team of deployments


### FR-1522: Check documentation:

[Troubleshooting Guide](docs/CI_CD_TROUBLESHOOTING.md)


### FR-1523: Search logs:

`gh run view --log | grep ERROR`


### FR-1524: Ask team:

#router-ci-cd Slack channel


### FR-1525: Page on-call:

For production issues


### FR-1526: `models`

Core model information (ID, name, provider, tier, context length)


### FR-1527: `pricing`

Real-time pricing data from OpenRouter


### FR-1528: `capabilities`

Model capabilities (tool use, vision, code, reasoning)


### FR-1529: `benchmarks`

Performance benchmarks and scores


### FR-1530: `ai_research`

Community sentiment and research insights


### FR-1531: `historical_performance`

Historical performance data


### FR-1532: `local_performance`

Local model performance metrics


### FR-1533: 🆓 Free Tier

`$0.00/1M tokens` (local models, OpenRouter free models)


### FR-1534: 💵 Budget Tier

`$0.18-$2.50/1M tokens` (very cheap OpenRouter models)


### FR-1535: 💎 Premium Tier

`$3.00-$18.00/1M tokens` (high-quality models)


### FR-1536: Small Tasks

(≤32K context): Local models preferred for speed


### FR-1537: Large Tasks

(>32K context): Cloud models preferred for quality


### FR-1538: Niche Tasks

Local models with specific capabilities


### FR-1539: Real-time pricing

Always uses current OpenRouter prices


### FR-1540: Budget-aware selection

Automatically stays within cost limits


### FR-1541: Tier-based escalation

Tries free → budget → premium models


### FR-1542: Capability matching

Selects models with required capabilities


### FR-1543: Performance weighting

Considers benchmarks and historical data


### FR-1544: Local optimization

Properly weights local vs cloud models


### FR-1545: Fallback support

Falls back to static registry if database fails


### FR-1546: Error handling

Graceful degradation on API failures


### FR-1547: Caching

Reduces database queries with intelligent caching


### FR-1548: **Database Schema**




### FR-1549: **Key Components**




### FR-1550: **1. Install Dependencies**




### FR-1551: **2. Set Environment Variables**




### FR-1552: **3. Run Migration**




### FR-1553: **4. Update KRouter Configuration**




### FR-1554: **Cost-Based Selection**




### FR-1555: **Task-Specific Optimization**




### FR-1556: **Local Model Weighting**




### FR-1557: **Database Configuration**




### FR-1558: **Sync Configuration**




### FR-1559: **Cost Optimization**




### FR-1560: **Quality Optimization**




### FR-1561: **Reliability**




### FR-1562: **Logs**




### FR-1563: **Database Queries**




### FR-1564: **Model Information**




### FR-1565: **Custom Model Selection**




### FR-1566: **Custom Policies**




### FR-1567: **Benchmark Integration**




### FR-1568: **Common Issues**




### FR-1569: **Performance Issues**




### FR-1570: **DynamicRegistryService**




### FR-1571: **PolicyGenerator**




### FR-1572: **DynamicRouter**




### FR-1573: ❌ Outdated Model Lists

Hardcoded models become outdated quickly


### FR-1574: ❌ Incorrect Pricing

Static prices don't reflect real-time OpenRouter pricing


### FR-1575: ❌ Poor Local Model Weighting

Local models not properly weighted for different use cases


### FR-1576: ❌ No Dynamic Selection

Policies can't adapt to model availability changes


### FR-1577: `OpenRouterClient`

Fetches real-time model data and pricing


### FR-1578: `PolicyGenerator`

Generates dynamic policies based on database queries


### FR-1579: `DynamicRegistryService`

Main service for model selection and management


### FR-1580: `DynamicRouter`

Integration layer with existing KRouter system


### FR-1581: Database Connection Failed

```bash


### FR-1582: OpenRouter API Errors

```bash


### FR-1583: No Models Available

```bash


### FR-1584: Slow Queries

- Check database indexes


### FR-1585: High Memory Usage

- Reduce sync frequency


### FR-1586: Backup existing configuration

2. **Run migration script**


### FR-1587: Update routing service imports

4. **Test with existing requests**


### FR-1588: Monitor performance and adjust

## 📝 **Contributing**


### FR-1589: Scraper (`src/components/scraper.py`)




### FR-1590: Parser (`src/components/parser.py`)




### FR-1591: Formatter (`src/components/formatter.py`)




### FR-1592: Config (`src/components/config.py`)




### FR-1593: Logger (`src/components/logger.py`)




### FR-1594: `agentapi server`




### FR-1595: `agentapi attach`




### FR-1596: Splitting terminal output into messages




### FR-1597: Removing TUI elements from agent messages




### FR-1598: What will happen when Claude Code, Goose, Aider, or Codex update their TUI?




### FR-1599: Supported models




### FR-1600: Cursor Agent CLI support

via local subprocess invocation


### FR-1601: Koosha Paridehpour

- Fork maintainer and contributor


### FR-1602: Luis Pater

- Original author


### FR-1603: Router-For.ME

- Project maintainer


### FR-1604: Z.ai

- Supporting the project with their GLM CODING PLAN


### FR-1605: Auggie CLI Automated Setup




### FR-1606: Cursor Agent Setup




### FR-1607: Additional Documentation




### FR-1608: [vibeproxy](https://github.com/automazeio/vibeproxy)




### FR-1609: [Subtitle Translator](https://github.com/VjayC/SRT-Subtitle-Translator-Validator)




### FR-1610: Fork Maintainer




### FR-1611: Original Authors




### FR-1612: Original Sponsors




### FR-1613: [Unified Interface](https://docs.getbifrost.ai/features/unified-interface)

- Single OpenAI-compatible API for all providers


### FR-1614: [Multi-Provider Support](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration)

- OpenAI, Anthropic, AWS Bedrock, Google Vertex, Azure, Cerebras, Cohere, Mistral, Ollama, Groq, and more


### FR-1615: [Automatic Fallbacks](https://docs.getbifrost.ai/features/fallbacks)

- Seamless failover between providers and models with zero downtime


### FR-1616: [Load Balancing](https://docs.getbifrost.ai/features/fallbacks)

- Intelligent request distribution across multiple API keys and providers


### FR-1617: [Model Context Protocol (MCP)](https://docs.getbifrost.ai/features/mcp)

- Enable AI models to use external tools (filesystem, web search, databases)


### FR-1618: [Semantic Caching](https://docs.getbifrost.ai/features/semantic-caching)

- Intelligent response caching based on semantic similarity to reduce costs and latency


### FR-1619: [Multimodal Support](https://docs.getbifrost.ai/quickstart/gateway/streaming)

- Support for text,images, audio, and streaming, all behind a common interface.


### FR-1620: [Custom Plugins](https://docs.getbifrost.ai/enterprise/custom-plugins)

- Extensible middleware architecture for analytics, monitoring, and custom logic


### FR-1621: [Governance](https://docs.getbifrost.ai/features/governance)

- Usage tracking, rate limiting, and fine-grained access control


### FR-1622: [Budget Management](https://docs.getbifrost.ai/features/governance)

- Hierarchical cost control with virtual keys, teams, and customer budgets


### FR-1623: [SSO Integration](https://docs.getbifrost.ai/features/sso-with-google-github)

- Google and GitHub authentication support


### FR-1624: [Observability](https://docs.getbifrost.ai/features/observability)

- Native Prometheus metrics, distributed tracing, and comprehensive logging


### FR-1625: [Vault Support](https://docs.getbifrost.ai/enterprise/vault-support)

- Secure API key management with HashiCorp Vault integration


### FR-1626: [Zero-Config Startup](https://docs.getbifrost.ai/quickstart/gateway/setting-up)

- Start immediately with dynamic provider configuration


### FR-1627: [Drop-in Replacement](https://docs.getbifrost.ai/features/drop-in-replacement)

- Replace OpenAI/Anthropic/GenAI APIs with one line of code


### FR-1628: [SDK Integrations](https://docs.getbifrost.ai/integrations/what-is-an-integration)

- Native support for popular AI SDKs with zero code changes


### FR-1629: [Configuration Flexibility](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration)

- Web UI, API-driven, or file-based configuration options


### FR-1630: Perfect Success Rate

- 100% request success rate even at 5k RPS


### FR-1631: Minimal Overhead

- Less than 15 µs additional latency per request


### FR-1632: Efficient Queuing

- Sub-microsecond average wait times


### FR-1633: Fast Key Selection

- ~10 ns to pick weighted API keys


### FR-1634: Core Infrastructure




### FR-1635: Advanced Features




### FR-1636: Enterprise & Security




### FR-1637: Developer Experience




### FR-1638: 1. Gateway (HTTP API)




### FR-1639: 2. Go SDK




### FR-1640: 3. Drop-in Replacement




### FR-1641: Quick Start




### FR-1642: Features




### FR-1643: Integrations




### FR-1644: Enterprise




### FR-1645: Apple's [CodeAct](https://machinelearning.apple.com/research/codeact)

"Your LLM Agent Acts Better when Generating Code."


### FR-1646: Anthropic's [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

"Building more efficient agents."


### FR-1647: Cloudflare's [Code Mode](https://blog.cloudflare.com/code-mode/)

"LLMs are better at writing code to call MCP, than at calling MCP directly."


### FR-1648: Docker's [Dynamic MCPs](https://www.docker.com/blog/dynamic-mcps-stop-hardcoding-your-agents-world/)

"Stop Hardcoding Your Agents’ World."


### FR-1649: Docker MCP Gateway

Manages containers beautifully, but still streams **all tool schemas** into Claude's context. No token optimization.


### FR-1650: Cloudflare Code Mode

V8 isolates are fast, but you **can't proxy your existing MCP servers** (Serena, Wolfram, custom tools). Platform lock-in.


### FR-1651: Academic Papers

Describe Anthropic's discovery pattern, but provide **no hardened implementation**.


### FR-1652: Proofs of Concept

Skip security (no rootless), skip persistence (cold starts), skip proxying edge cases.


### FR-1653: Constant 200-token overhead

regardless of server count


### FR-1654: Proxy any stdio MCP server

into rootless containers


### FR-1655: Fuzzy search across servers

without preloading schemas


### FR-1656: Production-hardened

with capability dropping and security isolation


### FR-1657: Ad-Hoc Tools

Need a script to scrape a site or parse a file? Just write it and run it. No need to deploy a new MCP server.


### FR-1658: Composability

Pipe outputs between commands, save intermediate results to files, and use standard Unix tools.


### FR-1659: Safety

Unlike giving an agent raw shell access to your machine, this server runs everything in a secure, rootless container. You get the power of "Bash/Code" without the risk.


### FR-1660: Lazy Runtime Detection

Starts up instantly even if Podman/Docker isn't ready. Checks for runtime only when code execution is requested.


### FR-1661: Self-Reference Prevention

Automatically detects and skips configurations that would launch the bridge recursively.


### FR-1662: Noise Filtering

Ignores benign JSON parse errors (like blank lines) from chatty MCP clients.


### FR-1663: Smart Volume Sharing

Probes Podman VMs to ensure volume sharing works, even on older versions.


### FR-1664: Rootless containers

- No privileged helpers required


### FR-1665: Network isolation

- No network access


### FR-1666: Read-only filesystem

- Immutable root


### FR-1667: Dropped capabilities

- No system access


### FR-1668: Unprivileged user

- Runs as UID 65534


### FR-1669: Resource limits

- Memory, PIDs, CPU, time


### FR-1670: Auto-cleanup

- Temporary IPC directories


### FR-1671: Persistent clients

- MCP servers stay warm


### FR-1672: Context efficiency

- 95%+ reduction vs traditional MCP


### FR-1673: Async execution

- Proper resource management


### FR-1674: Single tool

- Only `run_python` in Claude's context


### FR-1675: Multiple access patterns

```python


### FR-1676: Top-level await

- Modern Python patterns


### FR-1677: Type-safe

- Proper signatures and docs


### FR-1678: Compact responses

- Plain-text output by default with optional TOON blocks when requested


### FR-1679: Default (compact)

– responses render as plain text plus a minimal `structuredContent` payload containing only non-empty fields. `stdout`/`stderr` lines stay intact, so prompts remain lean without sacrificing content.


### FR-1680: Optional TOON

– set `MCP_BRIDGE_OUTPUT_MODE=toon` to emit [Token-Oriented Object Notation](https://github.com/toon-format/toon) blocks. We still drop empty fields and mirror the same structure in `structuredContent`; TOON is handy when you want deterministic tokenisation for downstream prompts.


### FR-1681: Fallback JSON

– if the TOON encoder is unavailable we automatically fall back to pretty JSON blocks while preserving the trimmed payload.


### FR-1682: README.md

- This file, quick start


### FR-1683: [GUIDE.md](GUIDE.md)

- Comprehensive user guide


### FR-1684: [ARCHITECTURE.md](ARCHITECTURE.md)

- Technical deep dive


### FR-1685: [HISTORY.md](HISTORY.md)

- Evolution and lessons


### FR-1686: [STATUS.md](STATUS.md)

- Current state and roadmap


### FR-1687: Why This vs. JS "Code Mode"?




### FR-1688: The Pain: MCP Token Bankruptcy




### FR-1689: Why Existing "Solutions" Fail




### FR-1690: The Fix: Discovery-First Architecture




### FR-1691: Architecture: How It Differs




### FR-1692: Comparison At A Glance




### FR-1693: Vs. Dynamic Toolsets (Speakeasy)




### FR-1694: Vs. OneMCP (Gentoro)




### FR-1695: Unique Features




### FR-1696: Who This Helps




### FR-1697: Philosophy: The "No-MCP" Approach




### FR-1698: 🛡️ Robustness & Reliability




### FR-1699: 🔒 Security First




### FR-1700: ⚡ Performance




### FR-1701: 🔧 Developer Experience




### FR-1702: Response Formats




### FR-1703: Discovery Workflow




### FR-1704: 1. Prerequisites (macOS or Linux)




### FR-1705: 2. Install Dependencies




### FR-1706: 3. Launch Bridge




### FR-1707: 4. Register with Your Agent




### FR-1708: 5. Execute Code




### FR-1709: Load Servers Explicitly




### FR-1710: Zero-Context Discovery




### FR-1711: Environment Variables




### FR-1712: Server Discovery




### FR-1713: Docker MCP Gateway Integration




### FR-1714: State Directory & Volume Sharing




### FR-1715: File Processing




### FR-1716: Data Pipeline




### FR-1717: Multi-System Workflow




### FR-1718: Inspect Available Servers




### FR-1719: Container Constraints




### FR-1720: Capabilities Matrix




### FR-1721: External




### FR-1722: ✅ Implemented




### FR-1723: 🔄 In Progress




### FR-1724: 📋 Roadmap




### FR-1725: Search

"Find tools for GitHub issues"


### FR-1726: Describe

"Get schema for `create_issue`"


### FR-1727: Execute

"Call `create_issue`"


### FR-1728: Code

"Import `mcp_github`, search for 'issues', and create one if missing."


### FR-1729: Two-stage discovery

– `discovered_servers()` reveals what exists; `query_tool_docs(name)` loads only the schemas you need.


### FR-1730: Fuzzy search across servers

– let the model find tools without memorising catalog names:


### FR-1731: Zero-copy proxying

– every tool call stays within the sandbox, mirrored over stdio with strict timeouts.


### FR-1732: Rootless by default

– Podman/Docker containers run with `--cap-drop=ALL`, read-only root, no-new-privileges, and explicit memory/PID caps.


### FR-1733: Compact + TOON output

– minimal plain-text responses for most runs, with deterministic TOON blocks available via `MCP_BRIDGE_OUTPUT_MODE=toon`.


### FR-1734: build

- Default, full access agent for development work


### FR-1735: plan

- Read-only agent for analysis and code exploration


### FR-1736: Installation




### FR-1737: Agents




### FR-1738: Documentation




### FR-1739: Contributing




### FR-1740: Building on OpenCode




### FR-1741: FAQ




### FR-1742: 6 Major Reasoning Datasets

MMLU-Pro, ARC, GPQA, TruthfulQA, CommonsenseQA, HellaSwag


### FR-1743: Router vs vLLM Comparison

Side-by-side performance evaluation


### FR-1744: Multiple Evaluation Modes

NR (neutral), XC (explicit CoT), NR_REASONING (auto-reasoning)


### FR-1745: Research-Ready Output

CSV files and publication-quality plots


### FR-1746: Dataset-Agnostic Architecture

Easy to extend with new datasets


### FR-1747: CLI Tools

Simple command-line interface for common operations


### FR-1748: CSV Files

Detailed per-question results and aggregated metrics


### FR-1749: Master CSV

Combined results across all test runs


### FR-1750: Plots

Accuracy and token usage comparisons


### FR-1751: Summary Reports

Markdown reports with key findings


### FR-1752: Documentation

https://vllm-semantic-router.com


### FR-1753: GitHub

https://github.com/vllm-project/semantic-router


### FR-1754: Issues

https://github.com/vllm-project/semantic-router/issues


### FR-1755: PyPI

https://pypi.org/project/vllm-semantic-router-bench/


### FR-1756: GitHub Issues

Bug reports and feature requests


### FR-1757: Documentation

Comprehensive guides and API reference


### FR-1758: Community

Join our discussions and get help from other users


### FR-1759: Installation




### FR-1760: Basic Usage




### FR-1761: Python API




### FR-1762: Custom Evaluation Script




### FR-1763: Plotting Results




### FR-1764: Example Output Structure




### FR-1765: Local Installation




### FR-1766: Adding New Datasets




### FR-1767: Dependencies




### FR-1768: Common Contributions




### FR-1769: Dark theme by default

with neon blue/green accents


### FR-1770: Glassmorphism effects

with backdrop blur and transparency


### FR-1771: Gradient backgrounds

and animated hover effects


### FR-1772: Responsive design

optimized for all devices


### FR-1773: Mermaid diagram support

with dark theme optimization


### FR-1774: Advanced code highlighting

with multiple language support


### FR-1775: Interactive navigation

with smooth animations


### FR-1776: Search functionality

(ready for Algolia integration)


### FR-1777: Fast loading

with optimized builds


### FR-1778: Accessible design

following WCAG guidelines


### FR-1779: Mobile-first

responsive layout


### FR-1780: SEO optimized

with proper meta tags


### FR-1781: Live Preview

http://localhost:3000 (when running)


### FR-1782: Docusaurus Docs

https://docusaurus.io/docs


### FR-1783: Main Project

../README.md


### FR-1784: Prerequisites




### FR-1785: Development




### FR-1786: Production Build




### FR-1787: Preview Production Build




### FR-1788: ✨ Modern Tech-Inspired Design




### FR-1789: 🔧 Enhanced Functionality




### FR-1790: 📱 User Experience




### FR-1791: Themes and Colors




### FR-1792: Navigation




### FR-1793: Site Configuration




### FR-1794: 00-client-request-test.py

✅ - Complete client request validation and smart routing


### FR-1795: 01-envoy-extproc-test.py

✅ - Envoy ExtProc interaction and processing tests


### FR-1796: 02-router-classification-test.py

✅ - Router classification and model selection tests


### FR-1797: 03-classification-api-test.py

✅ - Standalone Classification API service tests


### FR-1798: Development Workflow (LLM Katan - Recommended)




### FR-1799: Future: Production Testing (Real vLLM)




### FR-1800: 00-client-request-test.py

- Basic client request tests ✅


### FR-1801: 01-envoy-extproc-test.py

- Envoy ExtProc interaction tests ✅


### FR-1802: 02-router-classification-test.py

- Router classification tests ✅


### FR-1803: 03-classification-api-test.py

- Classification API tests ✅


### FR-1804: 04-model-routing-test.py

- TBD (To Be Developed)


### FR-1805: 04-cache-test.py

- TBD (To Be Developed)


### FR-1806: 05-e2e-category-test.py

- TBD (To Be Developed)


### FR-1807: 06-metrics-test.py

- TBD (To Be Developed)


### FR-1808: React 18

with TypeScript for type safety


### FR-1809: Vite 5

for fast development and optimized builds


### FR-1810: React Router v6

for client-side routing


### FR-1811: CSS Modules

for scoped styling with theme support (dark/light mode)


### FR-1812: Landing

(`/`): Intro landing with animated terminal demo and quick links


### FR-1813: Monitoring

(`/monitoring`): Grafana dashboard embedding with custom path input


### FR-1814: Config

(`/config`): Real-time configuration viewer with editable panels and save support


### FR-1815: Topology

(`/topology`): Visual topology of request flow and model selection using React Flow


### FR-1816: Playground

(`/playground`): Open WebUI interface for testing


### FR-1817: Dashboard

http://localhost:8700


### FR-1818: Grafana

(direct access): http://localhost:3000 (admin/admin)


### FR-1819: Prometheus

(direct access): http://localhost:9090


### FR-1820: Multi-architecture support

The Dockerfile supports both AMD64 and ARM64 architectures.


### FR-1821: Pre-built images

Available at `ghcr.io/vllm-project/semantic-router/dashboard` with tags for releases and latest.


### FR-1822: Frontend (React + TypeScript + Vite)




### FR-1823: Backend (Go HTTP Server)




### FR-1824: Method 1: Start with Docker Compose (Recommended)




### FR-1825: Method 2: Local Development Mode




### FR-1826: Method 3: Rebuild Dashboard Only




### FR-1827: Docker Compose Integration Notes




### FR-1828: Dockerfile Build




### FR-1829: Grafana Embedding Support




### FR-1830: Health Check




### FR-1831: Kubernetes deployment




### FR-1832: Profiles

Define deployment environments and configurations


### FR-1833: Test Cases

Reusable test logic that can be shared across profiles


### FR-1834: Framework

Core infrastructure for test execution and reporting


### FR-1835: ai-gateway

Tests Semantic Router with Envoy AI Gateway integration


### FR-1836: aibrix

Tests Semantic Router with vLLM AIBrix integration


### FR-1837: dynamic-config

Tests Semantic Router with Kubernetes CRD-based configuration (IntelligentRoute/IntelligentPool)


### FR-1838: istio

Tests Semantic Router with Istio service mesh integration


### FR-1839: production-stack

Tests vLLM Production Stack configurations


### FR-1840: llm-d

Tests Semantic Router with LLM-D distributed inference


### FR-1841: dynamo

Tests with Nvidia Dynamo (future)


### FR-1842: Automatic cluster lifecycle management

Creates and cleans up Kind clusters


### FR-1843: Docker image building and loading

Builds images and loads them into Kind


### FR-1844: Helm deployment automation

Deploys required Helm charts


### FR-1845: Automatic port forwarding cleanup

Each test case cleans up its port forwarding


### FR-1846: Detailed logging

Provides comprehensive test output


### FR-1847: Test reporting

Generates JSON and Markdown reports


### FR-1848: Resource cleanup

Ensures proper cleanup even on failures


### FR-1849: Istio-Specific Features:

- Istio sidecar injection and health


### FR-1850: Semantic Router Features (through Istio):

- Chat completions API and stress testing


### FR-1851: Supported Profiles




### FR-1852: Basic Functionality Tests




### FR-1853: Classification and Feature Tests




### FR-1854: Signal-Decision Engine Tests




### FR-1855: Install dependencies (optional)




### FR-1856: Run all tests with default profile (ai-gateway)




### FR-1857: Run specific profile




### FR-1858: Run specific test cases




### FR-1859: Run with custom options




### FR-1860: Debug mode




### FR-1861: Advanced Workflows




### FR-1862: Test Reports




### FR-1863: Profile vs Test Case Separation




### FR-1864: Service Configuration




### FR-1865: Embedding Signal Routing




### FR-1866: Adding a New Test Case




### FR-1867: Adding a New Profile




### FR-1868: Istio Profile




### FR-1869: Istio Control Plane

(`istio-system` namespace):


### FR-1870: Semantic Router

(`semantic-router` namespace):


### FR-1871: Istio Resources

- `Gateway` - Configures ingress gateway on port 80


### FR-1872: Component Benchmarks

Fast Go benchmarks for individual components (classification, decision engine, cache)


### FR-1873: E2E Performance Tests

Full-stack load testing integrated with the e2e framework


### FR-1874: Profiling

pprof integration for CPU, memory, and goroutine profiling


### FR-1875: Baseline Comparison

Automated regression detection against performance baselines


### FR-1876: CI/CD Integration

Performance tests run on every PR with regression blocking


### FR-1877: Running Benchmarks




### FR-1878: Profiling




### FR-1879: Baseline Comparison




### FR-1880: Regression Detection




### FR-1881: Classification Benchmarks




### FR-1882: Decision Engine Benchmarks




### FR-1883: Cache Benchmarks




### FR-1884: Tracked Metrics




### FR-1885: Performance Thresholds




### FR-1886: Performance Test Config (`config/perf.yaml`)




### FR-1887: Thresholds Config (`config/thresholds.yaml`)




### FR-1888: Benchmarks fail to run




### FR-1889: Models not found




### FR-1890: High variance in results




### FR-1891: Memory profiling shows high allocations




### FR-1892: PR Opened

→ Run component benchmarks (5 min)


### FR-1893: Compare Against Baseline

→ Calculate % changes


### FR-1894: Post Results to PR

→ Automatic comment with metrics table


### FR-1895: Block if Regression

→ Fail CI if thresholds exceeded


### FR-1896: Always warm up

- Run warmup iterations before measuring


### FR-1897: Report allocations

- Use `b.ReportAllocs()` to track memory


### FR-1898: Reset timer

- Use `b.ResetTimer()` after setup


### FR-1899: Use realistic data

- Test with production-like inputs


### FR-1900: Control variance

- Use fixed seeds for random data


### FR-1901: Measure what matters

- Focus on user-facing metrics


### FR-1902: Worker Node

The local `${PROJECT_ROOT}/models` directory is mounted to `/mnt/models` inside the worker node container


### FR-1903: PersistentVolume

Kubernetes PV uses `hostPath: /mnt/models` to access the models


### FR-1904: Init Container

Checks if models exist; if not, downloads them (requires internet connection)


### FR-1905: 1. Generate Kind Configuration




### FR-1906: 2. Create Kind Cluster




### FR-1907: 3. Load Docker Images (for offline/local images)




### FR-1908: 4. Deploy Semantic Router




### FR-1909: 5. Verify Deployment




### FR-1910: Path Auto-Detection




### FR-1911: Model Mounting




### FR-1912: Resource Configuration




### FR-1913: Models Not Found in Pod




### FR-1914: Regenerate Configuration




### FR-1915: ImagePullBackOff




### FR-1916: Using a Different Models Directory




### FR-1917: Multiple Worker Nodes




### FR-1918: Intelligent Model Selection

Automatically routes requests to the best model based on semantic understanding


### FR-1919: PII Detection & Protection

Blocks or redacts sensitive information before sending to models


### FR-1920: Prompt Guard

Detects and blocks jailbreak attempts


### FR-1921: Semantic Caching

Reduces latency and costs through intelligent response caching


### FR-1922: Category-Specific Prompts

Injects domain-specific system prompts for better results


### FR-1923: Tools Auto-Selection

Automatically selects relevant tools for function calling


### FR-1924: Category Classification

Train custom models at [Category Classifier Training](../../src/training/classifier_model_fine_tuning/)


### FR-1925: PII Detection

Train custom models at [PII Detection Training](../../src/training/pii_model_fine_tuning/)


### FR-1926: Prompt Guard

Train custom models at [Prompt Guard Training](../../src/training/prompt_guard_fine_tuning/)


### FR-1927: [Category Classifier Training](../../src/training/classifier_model_fine_tuning/)

- Train custom category classification models


### FR-1928: [PII Detector Training](../../src/training/pii_model_fine_tuning/)

- Train custom PII detection models


### FR-1929: [Prompt Guard Training](../../src/training/prompt_guard_fine_tuning/)

- Train custom jailbreak detection models


### FR-1930: [OpenShift Deployment](../openshift/)

- Deploy with standalone vLLM containers (not KServe)


### FR-1931: Main Project

https://github.com/vllm-project/semantic-router


### FR-1932: Full Documentation

https://vllm-semantic-router.com


### FR-1933: KServe Docs

https://kserve.github.io/website/


### FR-1934: Step 1: Verify InferenceService




### FR-1935: Step 2: Configure Router Settings




### FR-1936: Step 3: Deploy Resources




### FR-1937: Step 4: Wait for Ready




### FR-1938: Check Deployment Status




### FR-1939: View Logs




### FR-1940: Metrics




### FR-1941: Pod Not Starting




### FR-1942: Router Container Crashing




### FR-1943: Cannot Connect to InferenceService




### FR-1944: Within This Repository




### FR-1945: Other Deployment Options




### FR-1946: External Resources




### FR-1947: OpenShift Cluster

with OpenShift AI (RHOAI) installed


### FR-1948: KServe InferenceService

already deployed and running


### FR-1949: OpenShift CLI (oc)

installed and logged in


### FR-1950: Cluster admin or namespace admin

permissions


### FR-1951: Memory

3Gi request, 6Gi limit


### FR-1952: CPU

1 core request, 2 cores limit


### FR-1953: Storage

10Gi for model storage


### FR-1954: Prerequisites




### FR-1955: One-Click Full Deployment (Recommended)




### FR-1956: Minimal Deployment (Core Only)




### FR-1957: Command Line Options




### FR-1958: Manual Deployment (Advanced)




### FR-1959: Why Binary Build?




### FR-1960: Updating Dashboard




### FR-1961: Get Route URLs




### FR-1962: Dashboard Playground




### FR-1963: Example Usage




### FR-1964: Security Context




### FR-1965: Networking




### FR-1966: Storage




### FR-1967: Check Deployment Status




### FR-1968: Metrics




### FR-1969: Quick Cleanup




### FR-1970: Cleanup Options




### FR-1971: What Gets Cleaned Up




### FR-1972: Manual Cleanup




### FR-1973: Common Issues




### FR-1974: Resource Requirements




### FR-1975: Create namespace:

```bash


### FR-1976: Build llm-katan image:

```bash


### FR-1977: Deploy resources:

```bash


### FR-1978: Note:

You'll need to manually configure ClusterIPs in `config-openshift.yaml`


### FR-1979: URL

http://localhost:3002


### FR-1980: Database

MongoDB for conversation persistence


### FR-1981: API Integration

Routes through Envoy proxy for OpenAI-compatible API calls


### FR-1982: Configuration

- `OPENAI_BASE_URL=http://envoy-proxy:8801/v1` (routes through Envoy)


### FR-1983: URL

http://localhost:9090


### FR-1984: Configuration

`./addons/prometheus.yaml`


### FR-1985: Data Retention

15 days


### FR-1986: Storage

Persistent volume `prometheus-data`


### FR-1987: URL

http://localhost:3000


### FR-1988: Credentials

admin/admin


### FR-1989: Configuration

- Datasources: Prometheus and Jaeger


### FR-1990: URL

http://localhost:16686


### FR-1991: OTLP Endpoint

http://localhost:4318 (gRPC)


### FR-1992: Configuration

OTLP collector enabled


### FR-1993: Integration

Semantic Router sends traces via OTLP


### FR-1994: Environment Variables




### FR-1995: Prometheus




### FR-1996: Grafana




### FR-1997: Jaeger (Distributed Tracing)




### FR-1998: Prerequisites




### FR-1999: Install




### FR-2000: Verify Installation




### FR-2001: Access the Application




### FR-2002: Development Environment




### FR-2003: Production Environment




### FR-2004: Custom Configuration




### FR-2005: Installation & Management




### FR-2006: Development




### FR-2007: Testing & Debugging




### FR-2008: Port Forwarding




### FR-2009: Rollback & Cleanup




### FR-2010: Help




### FR-2011: In-Place Upgrade




### FR-2012: Rollback




### FR-2013: Example 1: Custom Endpoints




### FR-2014: Example 2: Enable Ingress




### FR-2015: Example 3: Enable Auto-scaling




### FR-2016: Example 4: Custom Security Context




### FR-2017: Pods Stuck in Pending




### FR-2018: Init Container Fails




### FR-2019: Service Not Accessible




### FR-2020: GitHub Actions Example




### FR-2021: GitLab CI Example




### FR-2022: ArgoCD Example




### FR-2023: Use Version Control

Keep your `values.yaml` files in version control


### FR-2024: Environment Separation

Use different namespaces and values files for different environments


### FR-2025: Resource Limits

Always set appropriate resource limits based on your workload


### FR-2026: Monitoring

Enable metrics and set up monitoring


### FR-2027: Security

Use security contexts and network policies


### FR-2028: Backups

Regularly backup your PVC data


### FR-2029: Testing

Test upgrades in dev/staging before production



## 7. Non-Functional Requirements


## 8. Features

### 🟡 Intelligent Routing

Byzantine ensemble voting (10 diverse voters)


### 🟡 Cost Savings

Semantic caching + smart provider selection = 85% cost reduction


### 🟡 Speed

Sub-5ms cache lookups via ModernBERT embeddings + HNSW indices


### 🟡 Reliability

Automatic provider failover and distributed request handling


### 🟡 Tool Integration

1000+ MCP tools with automatic semantic discovery


### 🟡 Multi-LLM Support

18+ language model providers unified under one API


### 🟡 Type

HTTP Gateway


### 🟡 Features

OpenAI-compatible API, semantic cache, provider routing, GraphQL API


### 🟡 Performance

<100ms p99 response time


### 🟡 Providers

18+ LLM providers integrated


### 🟡 Docs

See `../argisroute/README.md`


### 🟡 Type

MCP Server


### 🟡 Features

Byzantine ensemble, tool registry, state hierarchy


### 🟡 Testing

78% unit test coverage (283/310 tests passing)


### 🟡 Async

Full async/await support


### 🟡 Docs

See `/argisexec/README.md`


### 🟡 Type

Monitoring & control API


### 🟡 Features

Configuration management, deployment orchestration, metrics


### 🟡 API

GraphQL + REST endpoints


### 🟡 Docs

See `/argisgate/docs/API_REFERENCE.md`


### 🟡 Type

macOS menu bar application


### 🟡 Features

Service lifecycle management, local request forwarding, configuration


### 🟡 Platform

macOS 10.15+


### 🟡 Docs

See `/argisagent/README.md`


### 🟡 Python

PEP 8, type hints, docstrings (Sphinx format)


### 🟡 Go

Effective Go, gofmt, golint


### 🟡 Rust

clippy, rustfmt


### 🔴 Test Coverage

>80% for critical paths


### 🟡 File Size

≤500 lines per module (target ≤350)


### 🟡 Documentation

Update docs/ for all changes


### 🟡 Documentation

https://docs.argis.io


### 🟡 GitHub Issues

https://github.com/argis-io/argis/issues


### 🟡 Discord Community

https://discord.gg/argis


### 🟡 Email Support

support@argis.io


### 🟡 Office Hours

Every Wednesday at 10am PT


### 🟡 What is Argis?




### 🟡 Key Benefits




### 🟡 Prerequisites




### 🟡 Installation (5 minutes)




### 🟡 Verify Setup (Optional but Recommended)




### 🟡 First Request (30 seconds)




### 🟡 4-Tier Architecture Diagram




### 🟡 Data Flow: Request Processing




### 🟡 10+ Sub-Projects Overview




### 🟡 Component Details




### 🟡 Intelligent Routing




### 🟡 Semantic Caching




### 🟡 Tool Discovery




### 🟡 State Management




### 🟡 1. Environment Setup




### 🟡 2. Python Services (ArgisExec, ArgisGate)




### 🟡 3. Go Services (ArgisRoute, ArgisHub)




### 🟡 4. Rust Library (ArgisCores)




### 🟡 5. Dashboard & Wizard




### 🟡 6. Docker Deployment




### 🟡 Request Processing Pipeline




### 🟡 State Hierarchy Flow




### 🟡 Environment Variables




### 🟡 Service Configuration Files




### 🟡 Health Checks




### 🟡 Monitoring Dashboards




### 🟡 Metrics Available




### 🟡 OpenAI-Compatible Endpoints




### 🟡 GraphQL API (Advanced)




### 🟡 Setting Up Development Environment




### 🟡 Testing Strategy




### 🟡 Contribution Workflow




### 🟡 Code Standards




### 🟡 Common Issues




### 🟡 Debug Commands




### 🟡 Development Roadmap




### 🟡 Getting Help




### 🟡 Quick Links




### 🟡 License




### 🟡 Acknowledgments




### 🟡 Fork

the repository


### 🟡 Create

feature branch: `git checkout -b feature/xyz`


### 🟡 Make

changes following code style


### 🟡 Test

thoroughly: `pytest tests/`


### 🟡 Commit

with clear messages: `git commit -m "Add feature xyz"`


### 🟡 Push

to fork: `git push origin feature/xyz`


### 🟡 Create

pull request to main branch


### 🟡 Agent Management

Register, monitor, and control distributed host agents


### 🟡 Service Monitoring

Real-time health tracking and performance metrics


### 🟡 Alert System

Rule-based anomaly detection with multi-channel notifications


### 🔴 SLA Tracking

Uptime and availability monitoring for critical services


### 🟡 Authentication & Authorization

JWT-based auth with RBAC


### 🟡 WebSocket Support

Real-time status updates and log streaming


### 🟡 Infrastructure Health

Database, cache, and service dependency monitoring


### 🟡 Kubernetes Probes

Liveness (`/health/live`) and readiness (`/health/ready`)


### 🟡 Detailed Health

`/health` endpoint with database, cache, and service status


### 🟡 Service-Level Monitoring

Per-service health status and error rates


### 🟡 Email

SMTP-based notifications


### 🟡 Slack

Channel and direct message integration


### 🟡 Webhooks

Custom HTTP endpoints


### 🟡 System

In-app notifications


### 🟡 PostgreSQL

Persistent data storage (agents, alerts, configurations)


### 🟡 Redis

Session cache, service registry, pub/sub messaging


### 🟡 Prometheus

Metrics collection and monitoring


### 🟡 OpenTelemetry

Distributed tracing and observability


### 🟡 Slack

Alert notifications


### 🟡 DataDog

Log aggregation and APM


### 🟡 Line length

100 characters


### 🟡 Formatter

Black


### 🟡 Linter

Ruff


### 🟡 Type checker

mypy


### 🟡 Docstrings

Google style (see examples below)


### 🟡 [API Reference](docs/API_REFERENCE.md)

- Complete endpoint documentation


### 🟡 [Architecture Guide](docs/ARCHITECTURE.md)

- System design and patterns


### 🟡 [Deployment Guide](docs/DEPLOYMENT.md)

- Production deployment steps


### 🟡 [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

- Common issues and solutions


### 🟡 Issues

Report bugs and request features on GitHub


### 🟡 Discussions

Ask questions and discuss ideas


### 🟡 Email

team@argisgate.dev


### 🟡 Key Capabilities




### 🟡 Prerequisites




### 🟡 Local Development Setup




### 🟡 Quick Verification




### 🟡 1. Agent Management




### 🟡 2. Health Monitoring




### 🟡 3. Alert System




### 🟡 4. Anomaly Detection




### 🟡 5. SLA Tracking




### 🟡 6. Real-Time Updates via WebSocket




### 🟡 7. Notification Channels




### 🟡 Three-Layer Design




### 🟡 Data Flow




### 🟡 Component Diagram




### 🟡 Health & Status




### 🟡 Agent Management




### 🟡 Metrics & Performance




### 🟡 Alerts & Monitoring




### 🟡 SLA & Compliance




### 🟡 Authentication




### 🟡 Infrastructure




### 🟡 WebSocket (Real-Time)




### 🟡 Environment Variables




### 🟡 Loading Configuration




### 🟡 Quick Test Run




### 🟡 Test Categories




### 🟡 Test Coverage




### 🟡 Writing Tests




### 🟡 Docker




### 🟡 Kubernetes




### 🟡 Production Checklist




### 🟡 Common Issues




### 🟡 Debugging




### 🟡 Key Integrations




### 🟡 Development Workflow




### 🟡 Code Style




### 🟡 Test Requirements




### 🟡 Pull Request Process




### 🟡 Documentation




### 🟡 Community




### 🟡 Performance Targets




### 🟡 Current Version: 0.1.0




### 🟡 Fork and clone

the repository


### 🟡 Create a feature branch

`git checkout -b feature/your-feature`


### 🟡 Install dev dependencies

`uv pip install -e ".[dev]"`


### 🟡 Make changes

following code style (see below)


### 🟡 Run tests

`pytest --cov=argisgate`


### 🟡 Run linting

`ruff check src/` and `mypy src/`


### 🟡 Format code

`black src/` and `ruff format src/`


### 🟡 Commit with clear message

`git commit -m "feat: description"`


### 🟡 Push and create PR

Target `main` branch


### 🟡 System Requirements Validation

- Detects OS, CPU cores, RAM, and validates compatibility


### 🟡 Host Registration

- Hostname input, agent type selection, and service configuration


### 🟡 Local Service Detection

- Automatically detects installed services (Ollama, PostgreSQL, Redis, etc.)


### 🟡 Cloud Provider Configuration

- Optional secure credential management for Supabase, Neo4j Aura, Upstash Redis, and Synadia NATS


### 🟡 Gateway Connection

- Gateway URL configuration with API key/OAuth/local-only authentication


### 🟡 Verification & Summary

- Final review and agent creation on the gateway


### 🟡 File Size

All components < 350 lines (target 300)


### 🟡 Initial Load

< 2 seconds on 4G


### 🟡 Step Navigation

Instant (client-side state)


### 🟡 API Calls

2 async operations (gateway health check, agent creation)


### 🟡 Memory

< 50MB footprint


### 🟡 Directory Structure




### 🟡 Type System




### 🟡 State Management




### 🟡 Basic Setup




### 🟡 API Integration




### 🟡 Design Tokens




### 🟡 Credential Encryption




### 🟡 Best Practices




### 🟡 Port Already in Use




### 🟡 Build Issues




### 🟡 Type Errors




### 🟡 🎛️ Real-Time Agent Monitoring

- Live status updates, metrics visualization, and service lifecycle management


### 🟡 📊 Advanced Analytics

- Uptime trends, service reliability scoring, resource heatmaps, cost estimation


### 🟡 🚨 Intelligent Alerting System

- Rule-based alerts with channels, routing, deduplication, and throttling


### 🟡 🎨 Custom Dashboard Widgets

- Drag-and-drop dashboard builder with 12+ widget types


### 🟡 👥 RBAC (Role-Based Access Control)

- 4 roles (Admin, Viewer, Member, Guest) with 16 fine-grained permissions


### 🟡 🌐 Workspace Management

- Create isolated workspaces with templates, layout customization, and state preservation


### 🟡 ⚡ Performance Optimized

- IndexedDB caching, request batching (70-90% reduction), virtual scrolling, WebSocket real-time updates


### 🟡 🌓 Theme Support

- Dark and light mode with CSS variable-based customization


### 🟡 Node.js

18.0+


### 🟡 TypeScript

4.9+


### 🟡 React

18.0+


### 🟡 Python 3.10+

(for backend API)


### 🟡 Line Limit

500 lines per file (target 350)


### 🟡 TypeScript

Strict mode enforced


### 🟡 Browser Support

Chrome 90+, Firefox 88+, Safari 14+, Edge 90+


### 🟡 Performance

<500ms initial load, <100MB memory usage


### 🟡 Quick Start

`QUICK_START.md` - Phase 1 quick start


### 🟡 Phase 2 Guide

`PHASE2_QUICK_START.md` - Phase 2 features


### 🟡 Implementation Details

`DASHBOARD_IMPLEMENTATION.md` - Phase 1 architecture


### 🟡 Phase 2 Summary

`PHASE2_IMPLEMENTATION_SUMMARY.md` - Complete Phase 2 documentation


### 🟡 Main README

See `/Users/kooshapari/temp-PRODVERCEL/485/API/README.md`


### 🟡 API Reference

See `argisgate/docs/API_REFERENCE.md`


### 🟡 Backend Docs

See `argisexec/docs/`


### 🟡 [argisexec](/argisexec/)

- Python MCP server with Byzantine routing


### 🟡 [argisgate](/argisgate/)

- Python FastAPI gateway with monitoring


### 🟡 [argisroute](../argisroute/README.md)

- Go cloud API gateway (100K LOC)


### 🟡 [argisagent](/argisagent/)

- Swift macOS menu bar app


### 🟡 [argis-wizard](/argis-wizard/)

- Next.js setup wizard


### 🟡 Website

https://argis.io


### 🟡 Documentation

https://docs.argis.io


### 🟡 Email

support@argis.io


### 🟡 GitHub

https://github.com/argis-io/argis


### 🟡 Core Capabilities




### 🟡 Phase Breakdown




### 🟡 Prerequisites




### 🟡 Setup




### 🟡 Environment Variables




### 🟡 1. Initialize Dashboard Service




### 🟡 2. Use the Dashboard Component




### 🟡 3. Or Use Components Individually




### 🟡 AgentGrid




### 🟡 AgentDetailPanel




### 🟡 MetricsChart




### 🟡 LogsViewer




### 🟡 ServiceControls




### 🟡 SettingsPanel




### 🟡 Workspace Management




### 🟡 Advanced Analytics




### 🟡 Intelligent Alerting




### 🟡 Custom Dashboard Widgets




### 🟡 Role-Based Access Control (RBAC)




### 🟡 IndexedDB Caching




### 🟡 Request Batching




### 🟡 Request Deduplication




### 🟡 Virtual Scrolling




### 🟡 Performance Targets




### 🟡 Key API Endpoints




### 🟡 Key Slices




### 🟡 Redux Hooks




### 🟡 Theme Variables




### 🟡 Switch Themes




### 🟡 useAgentData




### 🟡 useMetrics




### 🟡 useLogs




### 🟡 useOptimizedWebSocket




### 🟡 Run Tests




### 🟡 Test Structure




### 🟡 Code Quality




### 🟡 Project Constraints




### 🟡 Code Organization




### 🟡 Security Features




### 🟡 Building Desktop




### 🟡 Quick References




### 🟡 External Documentation




### 🟡 WebSocket Connection Issues




### 🟡 Metrics Not Loading




### 🟡 Performance Problems




### 🟡 Redux DevTools




### 🟡 Follow TypeScript

Use strict types, no `any`


### 🟡 Keep Files Small

Target 350 lines, max 500


### 🔴 Test Coverage

Aim for >80% on critical paths


### 🟡 Component Memoization

Use React.memo for performance


### 🟡 Redux Patterns

Use Redux Toolkit, avoid mutations


### 🟡 Type Safety

Leverage type system fully


### 🟡 Accessibility

Follow WCAG 2.1 AA standards


### 🟡 Service modules

(argis*, separated by domain)


### 🟡 Documentation

(docs/, with good subdirectory structure)


### 🟡 Research/references

(research/, isolated by project)


### 🟡 Infrastructure

(infrastructure configs scattered)


### 🟡 Delete

`Makefile.bak` (use git history)


### 🟡 Move

`smartcp-docs-archive.tar.gz` → `docs/archive/`


### 🟡 Remove

all three (not needed)


### 🟡 Start here:

`docs/getting-started/`


### 🟡 Understand architecture:

`docs/architecture/`


### 🟡 Run project:

Root `Makefile` and `README.md`


### 🟡 Build guides:

`docs/guides/`


### 🟡 API reference:

`docs/api/`


### 🟡 Service code:

`argis<service>/src/`


### 🟡 Deployment:

`docs/operations/`


### 🟡 Infrastructure code:

`config/` (Docker, Postgres, Prometheus)


### 🟡 Monitoring:

`monitoring/` and `config/prometheus/`


### 🟡 Design docs:

`docs/design-docs/`


### 🟡 Reference implementations:

`research/`


### 🟡 Session tracking:

`docs/sessions/`


### 🟡 Agent patterns:

`docs/agent-guide/`


### 🟡 Session tracking:

`docs/sessions/<YYYYMMDD-name>/`


### 🟡 Codebase structure:

This report + `README.md`


### 🟡 Size:

20,787 files, 728MB


### 🟡 Cause:

Includes node_modules and build artifacts


### 🟡 Recommendation:

Add `.gitignore` patterns; consider separate build process


### 🟡 Size:

21,620 files, 6.5GB


### 🟡 Cause:

Multiple full reference implementations


### 🟡 Options:

1. Keep as reference (current)


### 🟡 Status:

Good separation by directory


### 🟡 Concern:

Cross-service dependencies need documentation


### 🟡 Recommendation:

Create dependency matrix in docs/


### 🟡 mypy_cache:

195MB


### 🟡 Recommendation:

Verify .gitignore; rebuild on clone


### 🟡 Note:

These are development-only, should not be committed


### 🟡 Immediate (Phase 1):

Cleanup (few hours)


### 🟡 Short-term (Phase 2):

Configuration organization (1-2 days)


### 🟡 Medium-term (Phase 3):

Documentation consolidation (2-3 days)


### 🟡 Ongoing (Phase 4):

Maintenance and governance


### 🟡 Current State (As of Jan 31, 2026)




### 🟡 Root Level Inventory




### 🟡 2.1 Service Modules (Primary Components)




### 🟡 2.2 Documentation & Knowledge




### 🟡 2.3 Infrastructure & Configuration




### 🟡 2.4 Cache & Build Artifacts (TO BE EXCLUDED)




### 🟡 2.5 Empty/Stale Directories




### 🟡 3.1 Current Organization Status




### 🟡 3.2 Identified Organizational Improvements




### 🟡 4.1 Root-Level Empty Directories




### 🟡 4.2 Cache Directories (Should Be .gitignored)




### 🟡 4.3 Build Artifacts




### 🟡 4.4 Documentation Archives




### 🟡 Phase 1: Immediate Cleanup (Low Risk)




### 🟡 Phase 2: Configuration Organization (Medium Risk)




### 🟠 Phase 3: Documentation Consolidation (Medium-High Risk)




### 🟠 Phase 4: Research Organization (Low Priority)




### 🟡 6.1 File Placement Guidelines




### 🟡 6.2 Governance Policies




### 🟡 6.3 Git Commit Strategy




### 🟡 6.4 Documentation Updates Needed




### 🟡 For Different User Types




### 🟡 Common Navigation Paths




### 🟡 Final Metrics




### 🟡 Service Distribution




### 🟡 Documentation Distribution




### 🟡 Issue: Documentation Site Too Large




### 🟡 Issue: Research Directory Very Large




### 🟡 Issue: Service Isolation




### 🟡 Issue: Cache Directory Size




### 🟡 Remove empty directories:

```bash


### 🟡 Remove backup files:

```bash


### 🟡 Verify .gitignore covers cache:

```bash


### 🟡 Move archive file:

```bash


### 🟡 Create config structure:

```bash


### 🟡 Move configuration files:

```bash


### 🟡 Update references:

- Update `.github/workflows/` to new paths


### 🟡 Create symlinks (optional) for backward compatibility:

```bash


### 🟡 Consolidate documentation:

```bash


### 🟡 Organize session documentation:

- Prune old sessions (>90 days) to archive


### 🟡 Audit codex-upstream docs:

- Check if should be in main docs or stay isolated


### 🟡 Document research structure:

- Create `research/README.md` explaining each subdirectory


### 🟡 Consider extracting:

- Heavy dependencies (kilocode, goose) might be in separate repos


### 🟡 Keep root clean:

- Only: `.env*`, `README.md`, `CLAUDE.md`, core `Makefile`


### 🟡 Documentation standards:

- Every feature needs docs (in appropriate `docs/` subdirectory)


### 🟡 Service isolation:

- Services self-contained within `argis<service>/`


### 🟡 Regular maintenance:

- **Quarterly:** Review empty directories


### 🟡 Cleanup

- Remove empty directories and backup files


### 🟡 Consolidation

- Centralize configuration and documentation


### 🟡 Maintenance

- Establish ongoing governance policies


### 🟡 Navigation

- Make it easy for users to find what they need


### 🟡 Full Report:

`docs/FINAL_ORGANIZATION_REPORT.md` - Comprehensive analysis


### 🟡 Architecture:

`docs/architecture/` - System design documents


### 🟡 Guides:

`docs/guides/` - Feature-specific documentation


### 🟡 Getting Started:

`docs/getting-started/` - Onboarding materials


### 🟡 "How do I get started?"




### 🟡 "Where is the agent code?"




### 🟡 "Where is the execution engine?"




### 🟡 "Where are the API routes?"




### 🟡 "Where is the web dashboard?"




### 🟡 "Where are configuration files?"




### 🟡 "Where is documentation?"




### 🟡 "Where do I track agent work?"




### 🟡 "Where are tests?"




### 🟡 "Where is the design documentation?"




### 🟡 "Where are operations guides?"




### 🟡 Main Categories




### 🟡 New Contributor




### 🟡 Feature Developer




### 🟡 DevOps/Operations




### 🟡 Researcher




### 🟡 Agent/Automation




### 🟡 Service Code:

182,673 files (11.4 GB)


### 🟡 Documentation:

591 files (10 MB)


### 🟡 Research/References:

21,620 files (6.5 GB)


### 🟡 Infrastructure:

1,923 files (117 MB)


### 🟡 Build/Cache:

6,496 files (196 MB)


### 🟡 Sessions (work tracking):

150 files


### 🟡 Archive (legacy):

123 files


### 🟡 Specifications:

55 files


### 🟡 Architecture:

19 files


### 🟡 Reference:

18 files


### 🟡 Development guides:

17 files


### 🟡 Analysis:

13 files


### 🟡 Operations:

7 files


### 🟡 Feature guides:

6 files


### 🟡 File locations:

See `ORGANIZATION_QUICK_GUIDE.md`


### 🟡 Organization changes:

See "Implementation Roadmap" above


### 🟡 Documentation navigation:

See `DOCUMENTATION_INDEX.md`


### 🟡 Detailed analysis:

See `FINAL_ORGANIZATION_REPORT.md`


### 🟡 1. FINAL_ORGANIZATION_REPORT.md (20 KB)




### 🟡 2. ORGANIZATION_QUICK_GUIDE.md (7.4 KB)




### 🟡 3. DOCUMENTATION_INDEX.md (2.4 KB)




### 🟡 Repository Composition




### 🟡 Main Services




### 🟡 Documentation by Category




### 🟡 Issue #1: Root-Level File Clutter




### 🟡 Issue #2: Empty Directories




### 🟡 Issue #3: Backup Files




### 🟡 Issue #4: Documentation Fragmentation




### 🟡 Phase 1: Immediate Cleanup (0.5-1 hours)




### 🟡 Phase 2: Configuration Organization (2-3 hours)




### 🟡 Phase 3: Documentation Consolidation (4-8 hours)




### 🟡 Phase 4: Ongoing Maintenance (ongoing)




### 🟡 New Developer




### 🟡 Feature Developer




### 🟡 DevOps/Operations




### 🟡 Agent/Automation




### 🟡 Finding Things




### 🟡 Common Commands




### 🟡 Read the appropriate guide:

- Quick overview? → `ORGANIZATION_QUICK_GUIDE.md`


### 🟡 Understand current structure:

- Review service layout in `ORGANIZATION_QUICK_GUIDE.md`


### 🟡 Plan changes (if applicable):

- Follow "Next Steps" section in `FINAL_ORGANIZATION_REPORT.md`


### 🟡 Maintain organization:

- Follow guidelines in Section 6 of full report


### 🟡 atoms

→ `build` and `check` commands per repo.


### 🟡 zen

→ `status` + `logs` quick diagnostics.


### 🟡 morph

→ `config` migration/generation + `init` workflows.


### 🟡 Intelligent Model Routing

- ML-powered selection of optimal models for tasks


### 🟡 Tool Integration

- Seamless integration with external services and APIs


### 🟡 Agent Framework

- Build sophisticated autonomous agents


### 🟡 Cost Optimization

- Minimize API costs through intelligent routing


### 🟡 Complete Observability

- Monitor performance, costs, and system health


### 🟡 Enterprise Security

- Role-based access control, audit logging, and compliance


### 🟠 [System Overview](architecture-diagrams/01_SYSTEM_OVERVIEW.md)

- High-level architecture


### 🟡 [Data Flow](architecture-diagrams/02_DATA_FLOW.md)

- How data moves through the system


### 🟡 [Microservices](architecture/MICROSERVICES_ARCHITECTURE.md)

- Service architecture


### 🟡 [Database Design](architecture-diagrams/06_DATABASE_ARCHITECTURE.md)

- Data persistence


### 🟡 [API Patterns](agent-guide/api-patterns.md)

- API design best practices


### 🟡 [Database Patterns](agent-guide/database-patterns.md)

- Data access patterns


### 🟡 [Testing Guide](agent-guide/testing-patterns.md)

- Testing strategies


### 🟡 [Async Patterns](agent-guide/async-patterns.md)

- Async/await best practices


### 🟡 [Agent Development](agent-guide/AGENTS.md)

- Building agents


### 🟡 [SmartCP API](reference/SMARTCP_INTERNAL_API.md)

- Core API specification


### 🟡 [Tool Optimization](reference/TOOL_CALL_OPTIMIZATION.md)

- Performance optimization


### 🟡 [Tool Discovery](reference/TOOL_DISCOVERY_COLD_START.md)

- Discovery mechanisms


### 🟡 [Analytics](reference/ANALYTICS_SYSTEM_ARCHITECTURE.md)

- Analytics system


### 🟡 [Master Specification](unified-specifications/MASTER_SPECIFICATION_2025.md)

- 2025 unified spec


### 🟡 [Epic PRDs](unified-specifications/)

- 50 detailed epic specifications (E1-E50)


### 🟡 [Implementation Checklist](unified-specifications/IMPLEMENTATION_CHECKLIST.md)

- Tracking


### 🔴 [Critical Gaps Analysis](research/CRITICAL_GAPS_ANALYSIS.md)

- System gaps and recommendations


### 🟡 [Comparative Analysis](research/DEEP_COMPARISON_ANALYSIS.md)

- Feature comparisons


### 🟡 [Cost Optimization](research/2025-agentic-ai-cost-optimization.md)

- Cost optimization research


### 🟡 Search

Use the search box at the top to find topics by keyword


### 🟡 Navigation Menu

Browse by category using the left sidebar


### 🟡 Breadcrumbs

See your location in the documentation hierarchy


### 🟡 Table of Contents

Navigate within documents using the right sidebar


### 🟡 Total Documentation

100+ comprehensive guides


### 🟡 Architecture Diagrams

7 detailed system diagrams


### 🟡 Development Patterns

8 major pattern guides


### 🟡 Product Specifications

50 detailed epic PRDs


### 🟡 Code Examples

50+ working code examples


### 🟡 Search Coverage

Full-text indexing of all content


### 🟡 Documentation Version

2.0


### 🟡 Last Updated

2025-01-31


### 🟡 Platform Version

Latest


### 🟡 Theme

Material for MkDocs


### 🟡 For Users (5 minutes)




### 🟡 For Developers (30 minutes)




### 🟡 For Operations (30-60 minutes)




### 🟡 Intelligent Routing




### 🟡 Tool Integration




### 🟡 Agent Framework




### 🟡 Architecture




### 🟡 Development




### 🟡 API Reference




### 🟡 Product Specifications




### 🟡 Research & Analysis




### 🟡 Documentation




### 🟡 Architecture




### 🟡 Development




### 🟡 Deployment & Operations




### 🟡 Product & Specifications




### 🟡 Research




### 🟡 Basic API Call




### 🟡 Using Tools




### 🟡 Building an Agent




### 🟡 How do I get started?




### 🟡 How do I deploy to production?




### 🟡 How do I build agents?




### 🟡 Where is the API reference?




### 🟡 How do I integrate external tools?




### 🟡 How do I optimize costs?




### 🟡 [Quick Start Guide](getting-started/quickstart.md)

- Get running in 5 minutes


### 🟡 [Installation Guide](INSTALLATION_END_USER_GUIDE.md)

- Detailed setup instructions


### 🟡 [First API Call](getting-started/quickstart.md#step-4-make-your-first-api-call-1-minute)

- Make your first request


### 🟡 [Architecture Overview](architecture/README.md)

- Understand the system design


### 🟡 [Development Guides](agent-guide/README.md)

- Learn development patterns


### 🟡 [API Reference](reference/SMARTCP_INTERNAL_API.md)

- Complete API documentation


### 🟡 [Code Examples](agent-guide/api-patterns.md)

- Practical examples


### 🟡 [Deployment Guide](DEPLOYMENT_GUIDE.md)

- Production deployment steps


### 🟡 [Security Setup](security/SECURITY_DEPLOYMENT_GUIDE.md)

- Secure configuration


### 🟡 [Configuration Guide](CLIENT_HOST_CONFIG.md)

- System configuration


### 🟡 [Monitoring](reference/ANALYTICS_SYSTEM_ARCHITECTURE.md)

- System monitoring


### 🟡 Report Issues

Found an error? Report it in your issue tracker


### 🟡 Suggest Improvements

Have an idea? Share your feedback


### 🟡 Add Examples

Help other developers with code examples


### 🟡 Improve Clarity

Help make documentation clearer


### 🟡 Search

the documentation using the search box


### 🟡 Browse

the [Getting Started](getting-started/overview.md) section


### 🟡 Check

relevant guides and examples


### 🟡 Review

the [FAQ](#faq) section above


### 🟡 Overwhelming?

→ Start with `ORGANIZATION_QUICK_GUIDE.md`


### 🟡 Need full details?

→ Read `FINAL_ORGANIZATION_REPORT.md`


### 🟡 Looking for something specific?

→ Use sections below


### 🟡 New to the project?

→ Start with `getting-started/`


### 🟡 FINAL_ORGANIZATION_REPORT.md

- Complete organizational analysis


### 🟡 ORGANIZATION_QUICK_GUIDE.md

- Fast reference guide


### 🟡 DOCUMENTATION_INDEX.md

- This file


### 🟡 New Contributor




### 🟡 Feature Developer




### 🟡 DevOps Engineer




### 🟡 Researcher/Agent




### 🟡 Exploration

Test multiple implementation approaches without fear of losing working code


### 🟡 Learning

Allow Claude to attempt complex refactorings with easy rollback


### 🟡 Experimentation

Try aggressive optimizations knowing you can instantly revert


### 🟡 Safety Net

Provides confidence for more ambitious AI-assisted changes


### 🟡 Frontend development

while another handles **backend API** implementation


### 🟡 Test writing

concurrent with **implementation**


### 🟡 Documentation generation

parallel to **code refactoring**


### 🟡 5 sessions locally

in terminal (each with own git checkout)


### 🟡 5-10 sessions

on Anthropic's web platform


### 🟡 193-file refactors

consolidating 3 status fields into 1


### 🟡 State machine simplification

reducing 40 states to 5 across dozens of files


### 🟡 API signature changes

propagated across entire codebase


### 🟡 Pattern matching

Finding similar code structures


### 🟡 Semantic search

Understanding meaning and intent


### 🟡 Call hierarchy

Tracing function usage


### 🟡 Type relationships

Following type definitions and usage


### 🟡 Jump to definitions

Navigate to symbol definitions instantly


### 🟡 Find references

Locate all usage sites of functions/types


### 🟡 Type information

Access real-time type data


### 🟡 Error detection

See type errors immediately after edits


### 🟡 Symbol information

Hover-like info on demand


### 🟡 Traditional text search

~45 seconds to find all call sites


### 🟡 LSP-powered search

~50ms for same operation


### 🟡 Improvement

900x faster


### 🟡 15-20 concurrent sessions

during active development


### 🟡 Separate git checkouts

for each local session (not branches/worktrees)


### 🟡 Team CLAUDE.md files

in git repositories document:


### 🟡 claude-code-workflows

Production workflows from AI-native startup


### 🟡 claude-code-spec-workflow

Spec-driven development automation


### 🟡 claude-code-action

GitHub PR/issue automation


### 🟡 Cursor

Claude Code extension enables "best of both worlds"—Cursor's IDE features + Claude's reasoning depth


### 🟡 Windsurf

Full Claude Code integration


### 🟡 VSCodium

Complete compatibility


### 🟡 Cursor

Wins on simplicity


### 🟡 Claude Code

Wins on reasoning depth


### 🟡 Windsurf

Wins on autonomy


### 🟡 OpenTelemetry Integration

For real-time metrics export


### 🟡 claude-code-otel

Comprehensive observability solution (OpenTelemetry-based)


### 🟡 Claude-Code-Usage-Monitor

Real-time usage monitor with predictions and warnings


### 🟡 Charts and visualizations

- **Forms for data input**


### 🟡 Dashboards

- **Interactive controls**


### 🟡 Built-in agents

Explore, Plan, general-purpose


### 🟡 Custom agents

Any from `.claude/agents/`


### 🟡 fork

Skill runs in isolation


### 🟡 inherit

Shares main agent context


### 🟡 Overview




### 🟡 Key Features




### 🟡 Design Philosophy




### 🟡 Use Cases




### 🟡 Practical Impact




### 🟡 Overview




### 🟡 Architecture




### 🟡 Parallel Execution Capabilities




### 🟡 Real-World Workflow




### 🟡 Performance Impact




### 🟡 Overview




### 🟡 Capabilities




### 🟡 Workflow Integration




### 🟡 Developer Experience




### 🟡 Key Design Principle




### 🟡 Overview




### 🟡 Core Capabilities




### 🟡 The Explore Sub-Agent




### 🟡 Search Strategies




### 🟡 Performance




### 🟡 Overview




### 🟡 Supported Languages (11 Total)




### 🟡 Key Capabilities




### 🟡 Performance Revolution




### 🟡 Setup Process




### 🟡 Community Ecosystem




### 🟡 Impact on Agentic Coding




### 🟡 Overview




### 🟡 Best Practices from Claude Code Creator (Boris Cherny)




### 🟡 Automation Capabilities




### 🟡 Community Frameworks




### 🟡 Philosophy




### 🟡 Overview




### 🟡 Supported Terminals




### 🟡 Setup Experience




### 🟡 Design Philosophy




### 🟡 Key Workflow Enhancement




### 🟡 Overview




### 🟡 VS Code Integration




### 🟡 JetBrains Support




### 🟡 VS Code Derivatives




### 🟡 Competitive Landscape (2026)




### 🟡 GitHub Actions Integration




### 🟡 Display Mode




### 🟡 Overview




### 🟡 Custom System Prompts




### 🟡 Hooks System




### 🟡 Configuration Levels




### 🟡 Key Hook Events




### 🟡 Real-World Examples




### 🟡 System Prompt Repository




### 🟡 Overview




### 🟡 API Endpoint




### 🟡 Key Metrics




### 🟡 Data Characteristics




### 🟡 Alternative Monitoring Options




### 🟡 Third-Party Tools




### 🟡 Use Cases




### 🟡 Overview




### 🟡 What is MCP?




### 🟡 MCP Apps (January 2026)




### 🟡 Claude Code Plugin Integration




### 🟡 Plugin Components




### 🟡 Example MCP Integrations




### 🟡 Discovery & Installation




### 🟡 Technical Architecture




### 🟡 Overview




### 🟡 Core Capabilities




### 🟡 Evolution Timeline




### 🟡 Architecture




### 🟡 Session Management




### 🟡 Integration Frameworks




### 🟡 Practical Usage Patterns




### 🟡 Real-World Examples




### 🟡 Overview




### 🟡 Major Update (January 2026)




### 🟡 Skills Architecture




### 🟡 Invocation Modes




### 🟡 Sub-Agent Integration




### 🟡 Advanced Features




### 🟡 Practical Examples




### 🟡 Discovery & Management




### 🟡 Community Resources




### 🟡 Output Styles

Persistent, file-based configurations


### 🟡 Prompt Appending

Add to Claude Code's default prompt


### 🟡 Fully Custom Prompts

Complete control over agent behavior


### 🟡 Command Hooks

(`type: "command"`): Run shell commands


### 🟡 Prompt Hooks

(`type: "prompt"`): Single-turn LLM evaluation


### 🟡 Agent Hooks

(`type: "agent"`): Spawn sub-agent with tools (Read, Grep, Glob)


### 🟡 Slash commands

Custom commands for workflows


### 🟡 Sub-agents

Specialized agents for domain tasks


### 🟡 MCP servers

Integrations to tools and data sources


### 🟡 Hooks

Workflow behavior modifications


### 🟡 Root-level files:

18 total (down from initial clutter)


### 🟡 Documentation files created:

5 comprehensive guides


### 🟡 Empty directories identified:

2-3 (ready for cleanup)


### 🟡 Potential cleanup items:

4-5 files


### 🟡 Status:

Ready for Phase 1 implementation


### 🟡 Current Size:

0 bytes (empty)


### 🟡 Type:

Cache directory


### 🟡 Justification:

- Empty/unused cache directory


### 🟡 Git Command:

`git rm -r --cached .mcp_token_cache/ 2>/dev/null || true && rmdir .mcp_token_cache/`


### 🟡 Risk Level:

NONE


### 🟡 Impact:

Root cleaner, no functional impact


### 🟡 Current Size:

992 KB archive


### 🟡 Type:

Legacy documentation archive


### 🟡 Current Location:

Root (not found in current state)


### 🟡 Recommendation:

- If present: Move to `docs/archive/` or delete


### 🟡 Justification:

Archive files clutter root; should be in versioned directory


### 🟡 Risk Level:

LOW (historical backup)


### 🟡 Impact:

Better organization, reclaim space


### 🟡 Phase 1:

Remove empty directories, improve .gitignore


### 🟡 Phase 2:

Consolidate configuration files to config/ directory


### 🟡 Phase 3:

Organize and index documentation


### 🟡 Key Metrics




### 🟡 Root Directory Analysis




### 🟡 Detailed Cleanup Impact




### 🟡 Already Moved (From Initial Organization)




### 🟡 Planned Moves (Phase 2 - Not Yet Implemented)




### 🟡 Already Deleted (Pre-Cleanup)




### 🟡 Planned Deletions (Phase 1 - Ready to Implement)




### 🟡 Items to Exclude (Not Delete)




### 🟡 Current Root Files (18 Total)




### 🟡 Visual Root Structure (Target State)




### 🟡 Current Structure (26 directories at root)




### 🟡 Planned Structure (After Cleanup)




### 🟡 Directory Count Changes




### 🟡 Empty/Placeholder Directories (Ready for Cleanup)




### 🟡 Prerequisites




### 🟡 Phase 1: Immediate Cleanup (Ready Now)




### 🟡 Phase 2: Optional Configuration Consolidation (2-3 weeks)




### 🟡 Phase 3: Documentation Consolidation (Optional - 4-8 hours)




### 🟡 Pull Request Creation




### 🟡 Quick Verification (5 minutes)




### 🟡 Comprehensive Verification (15 minutes)




### 🟡 Post-Cleanup Validation




### 🟡 Git Verification




### 🟡 Immediate Actions (This Week)




### 🟡 Short-term (2-4 weeks)




### 🟡 Medium-term (This month)




### 🟡 Phase 1 Risk Matrix




### 🟡 Phase 2 Risk Matrix




### 🟡 Phase 3 Risk Matrix




### 🟡 Rollback Procedure




### 🟡 Files Created During Analysis




### 🟡 Key Resources




### 🟡 Cleanup Success Criteria




### 🟡 Documentation Success Criteria




### 🟡 Repository Composition




### 🟡 Service Breakdown




### 🟡 Cleanup Impact




### 🟡 Q: Why create organization documents if the cleanup isn't implemented?




### 🟡 Q: What if implementation breaks something?




### 🟡 Q: How long does Phase 1 cleanup take?




### 🟠 Q: What's the priority order for implementation?




### 🟡 Q: Who should implement these changes?




### 🟡 Q: Are there any service disruptions?




### 🟡 Questions About Cleanup




### 🟡 Reporting Issues




### 🟡 Pre-Implementation




### 🟡 Phase 1 Execution




### 🟡 Phase 2 Execution




### 🟡 Phase 3 Execution




### 🟡 Post-Implementation




### 🟡 FINAL_ORGANIZATION_REPORT.md

- From: Root directory (generated Jan 31)


### 🟡 ORGANIZATION_QUICK_GUIDE.md

- From: Root directory (generated Jan 31)


### 🟡 README_ORGANIZATION.md

- From: Root directory (generated Jan 31)


### 🟡 DOCUMENTATION_INDEX.md

- From: Root directory (generated Jan 31)


### 🟡 Review Documentation

(20 minutes)


### 🟡 Approve Cleanup Plan

(Team decision)


### 🟡 Execute Phase 1

(30 minutes - if approved)


### 🟡 Plan Phase 2

(Configuration consolidation)


### 🟡 Execute Phase 2

(2-3 hours - if approved)


### 🟡 Complete Phase 3

(Documentation)


### 🟡 Ongoing Maintenance

- [ ] Quarterly directory review


### 🟠 Phase 1 (High):

Remove empty dirs, improve .gitignore


### 🟡 Phase 2 (Medium):

Consolidate configuration files


### 🟡 Phase 3 (Low):

Archive and reorganize documentation


### 🟡 Client (Laptop)




### 🟡 Hybrid Monolith (Default)




### 🟡 Cloud Distributed




### 🟡 Responsibility

primary purpose of the folder.


### 🟡 Exposes

interfaces/APIs produced here.


### 🟡 Consumes

external/internal services it depends on.


### 🟡 Responsibility

Stateless MCP server; validates requests, forwards to Bifrost.


### 🟡 Key subfolders

(representative; follow hexagonal layering):


### 🟡 Exposes

MCP server, health endpoint.


### 🟡 Consumes

Bifrost GraphQL/gRPC; Supabase Auth JWKs; optional local SLM runtime addresses for capability discovery.


### 🟡 Responsibility

Customizations layered on official Bifrost.


### 🟡 Highlights

- `server/`, `services/`: Extension resolvers (executor, memory, state) and router logic.


### 🟡 Exposes

GraphQL/gRPC endpoints (through Bifrost), routing hooks.


### 🟡 Consumes

Supabase (cloud), optional local Postgres, Redis/NATS/Neo4j (cloud-first), local SLMs.


### 🟡 Responsibility

Upstream Bifrost core (do not modify here).


### 🟡 Useful subdirs

`framework/` (plugin system), `core/` (routing), `transports/` (GraphQL/gRPC), `plugins/` (example integrations), `ui/` (reference UI), `helm-charts/` (deploys).


### 🟡 Exposes

GraphQL/gRPC; plugin contracts used by bifrost-extensions.


### 🟡 Responsibility

Installer/bundling and management UI. Acts as presentation layer; bundles SmartCP client and config profiles.


### 🟡 Exposes

Desktop UI, feature selection during install (SmartCP, Bifrost, local Postgres, Redis, SLMs), management console post-install.


### 🟡 Consumes

SmartCP endpoint, Bifrost endpoint, Cloudflare Tunnel config, local OS for service control.


### 🟡 Responsibility

Upstream Go services for agent/CLI access. Imported as modules; avoid code changes.


### 🟡 Exposes

REST/gRPC per upstream; no persistence locally.


### 🟡 Consumes

Bifrost, Supabase Auth, logging/metrics stacks.


### 🟡 Responsibility

SQL migrations, policies, and config scaffolding for the Supabase cloud project (auth + Postgres + pgvector).


### 🟡 Exposes

Schema, RLS policies, seed data.


### 🟡 Consumes

Supabase cloud instance.


### 🟡 docs/

Source markdowns, architecture notes, sessions.


### 🟡 docs-site/

Node-based static site build; uses `package.json` scripts for generation.


### 🟡 Responsibility

Research/reference repository (not runtime code). Use as knowledge base.


### 🟡 Responsibility

Helper shell/Node scripts for lint/format/build.


### 🟡 Responsibility

Planning artifacts and workstreams.


### 🟡 Primary Role

Reserved for shared utilities and common code used across multiple Argis components


### 🟡 Intended Use

- Common constants and configurations


### 🟡 Empty

Yes, no files currently present


### 🟡 Has Hidden Files

No (confirmed via `ls -lah`)


### 🟡 Referenced In

Makefile (indirectly through project structure), documentation


### 🟡 Should Keep

✅ **YES**


### 🟡 Primary Role

Reserved directory for compiled artifacts and build outputs


### 🟡 Intended Use

- Python wheel distributions (`.whl` files)


### 🟡 Empty

Yes, no files currently present


### 🟡 Has Hidden Files

No (confirmed via `ls -lah`)


### 🟡 Referenced In

Documentation, implied in Makefile build targets


### 🟡 Should Keep

✅ **YES**


### 🟡 Rebranding Complete

`docs/development/migration/REBRANDING_COMPLETE_SUMMARY.md`


### 🟡 Final Report

`docs/development/migration/REBRANDING_FINAL_REPORT.md`


### 🟡 Rebranding Success

`docs/development/migration/REBRANDING_SUCCESS.md`


### 🟡 `argis/`

Reserved for cross-component shared utilities


### 🟡 `argis-build/`

Reserved for build artifacts and compiled outputs


### 🟡 1. `/argis/` - Shared Utilities Directory




### 🟡 2. `/argis-build/` - Build Artifacts Directory




### 🟡 Python Distributions




### 🟡 Go Binaries




### 🟡 Build Metadata




### 🟡 Docker Images




### 🟡 Immediate Actions




### 🟡 Verification Commands




### 🟡 Related Documentation




### 🟡 `/Users/kooshapari/temp-PRODVERCEL/485/API/argis/`

2. **`/Users/kooshapari/temp-PRODVERCEL/485/API/argis-build/`**


### 🟠 Do NOT delete

either directory - they serve important architectural purposes


### 🟡 Add `.gitkeep`

to both directories to ensure they're tracked in git


### 🟡 Add documentation

explaining their intended purpose


### 🟡 Add `.gitignore`

to `argis-build/` to prevent accidental commits of build artifacts


### 🟡 Update

CI/CD pipelines to use `argis-build/` for artifact staging if not already configured


### 🟡 18+ LLM Providers

OpenAI, Claude, Gemini, Vertex AI, Cohere, Anthropic, Mistral, and more


### 🟡 OpenAI-Compatible API

Drop-in replacement for OpenAI SDK via `/v1/chat/completions` endpoint


### 🟡 Semantic Caching

Cache LLM responses by semantic similarity, reducing costs and latency


### 🟡 GraphQL API

Full GraphQL support for complex queries alongside REST


### 🟡 Intelligent Routing

ML-based provider selection based on cost, latency, and quality


### 🟡 Zero Vendor Lock-in

Consumes Bifrost as an unmodified Go module


### 🟡 Production Deployment

Built-in support for Fly.io, Vercel, Railway, Render, and Homebox


### 🟡 Go 1.24.3+

- **PostgreSQL 15+** (for session/cache storage)


### 🟡 Redis 7+

(optional, for distributed caching)


### 🟡 Docker

(optional, for local development)


### 🟡 Cost

Minimize expenses by selecting cheapest suitable provider


### 🟡 Latency

Route to fastest providers for real-time applications


### 🟡 Model Availability

Fall back to alternative providers if primary unavailable


### 🟡 Quality

Use fine-tuned models for specialized tasks


### 🟡 User Preferences

Honor model/provider selections


### 🟡 Rate Limits

Distribute load across providers


### 🟡 Token counting

Know exact token usage before API calls


### 🟡 Cost tracking

Understand spending per user/organization


### 🟡 Rate limiting

Enforce usage quotas


### 🟡 Audit logging

Complete history of API calls


### 🟡 Multi-tenancy

Support multiple orgs/teams with isolation


### 🟡 Metrics

Prometheus-compatible metrics endpoint


### 🟡 Logging

Structured JSON logging with request tracing


### 🟡 Tracing

OpenTelemetry integration (coming soon)


### 🟡 Dashboards

Pre-built Grafana dashboards


### 🟡 Documentation

[docs/README.md](docs/README.md)


### 🟡 Issues

[GitHub Issues](https://github.com/kooshapari/argisroute/issues)


### 🟡 Discussions

[GitHub Discussions](https://github.com/kooshapari/argisroute/discussions)


### 🟡 Email

support@example.com


### 🟡 [Bifrost](https://github.com/maximhq/bifrost)

- Core LLM gateway (upstream)


### 🟡 [Cliproxy](https://github.com/kooshapari/cliproxy)

- CLI proxy abstraction


### 🟡 [API Module](../API/)

- Main API layer (Python/FastAPI)


### 🟡 Key Characteristics




### 🟡 Prerequisites




### 🟡 Local Development




### 🟡 Docker Development




### 🟡 System Design




### 🟡 Clean Extension Layer Pattern




### 🟡 1. OpenAI-Compatible API




### 🟡 2. Semantic Caching




### 🟡 3. Intelligent Routing




### 🟡 4. GraphQL API




### 🟡 5. Research & Evaluation Tools




### 🟡 6. Session Management




### 🟡 7. Observability




### 🟡 Environment Variables




### 🟡 Configuration File (YAML)




### 🟡 Chat Completion (OpenAI-Compatible)




### 🟡 Embeddings




### 🟡 GraphQL Query




### 🟡 List Models




### 🟡 Health Check




### 🟡 Fly.io (Recommended)




### 🟡 Docker




### 🟡 Kubernetes




### 🟡 Vercel (Serverless)




### 🟡 Building




### 🟡 Testing




### 🟡 Database




### 🟡 Code Quality




### 🟡 Built-in Plugins




### 🟡 Custom Plugins




### 🟡 Prometheus Metrics




### 🟡 Structured Logging




### 🟡 Health Checks




### 🟡 Common Issues




### 🟡 Intelligent Router

- ML-based provider selection


### 🟡 Learning

- Continuously learn from provider performance


### 🟡 Smart Fallback

- Automatic failover with retry logic


### 🟡 Registry Cache

- Cache provider configurations


### 🟡 Passing Tests

283/310 unit tests (91% pass rate)


### 🟡 Coverage

78% (1,204/1,543 lines covered)


### 🟡 Gap

339 lines to cover


### 🟡 Target Gap

~150 lines (to reach 85%)


### 🟡 Tests Missing

~100-150 tests needed


### 🟡 Phase 3

Integration tests (80 tests) - Multi-module workflows


### 🟡 Phase 4

E2E tests (65 tests) - Full system workflows


### 🟡 Approach




### 🟠 Files to Enhance (Priority Order)




### 🟡 Task 1: Enhance test_namespace.py




### 🟡 Task 2: Enhance test_sandbox_extended.py




### 🟡 Task 3: Enhance test_scope_storage_extended.py




### 🟡 Task 4: Enhance test_scope_manager.py




### 🟡 Task 5: Enhance test_mcp_manager.py




### 🟡 Task 6: Enhance test_events_bus.py




### 🟡 Task 7: Enhance test_background.py




### 🟡 Task 8: Enhance test_execute.py




### 🟡 Task 9: Enhance test_middleware.py




### 🟡 Task 10: Enhance test_core.py




### 🟡 Step 1: Run Baseline Coverage




### 🟡 Step 2: Implement Task 1-10 in Order




### 🟡 Step 3: Re-run Full Coverage After Each Task




### 🟡 Step 4: Verify 85%+ Coverage Achieved




### 🟡 tests/unit/runtime/test_namespace.py

(8 → 15 tests)


### 🟡 tests/unit/runtime/test_sandbox_extended.py

(40+ → 50+ tests)


### 🟡 tests/unit/runtime/test_scope_storage_extended.py

(60+ → 75+ tests)


### 🟡 tests/unit/runtime/test_scope_manager.py

(20 → 30 tests)


### 🟡 tests/unit/runtime/test_mcp_manager.py

(15 → 25 tests)


### 🟡 tests/unit/runtime/test_events_bus.py

(10 → 20 tests)


### 🟡 tests/unit/runtime/test_background.py

(10 → 20 tests)


### 🟡 tests/unit/tools/test_execute.py

(12 → 20 tests)


### 🟡 tests/unit/auth/test_middleware.py

(15 → 25 tests)


### 🟡 tests/unit/runtime/test_core.py

(10 → 18 tests)


### 🟡 Protocol

FastMCP 2.13 (stateless HTTP)


### 🟡 Purpose

MCP protocol frontend


### 🟡 Entry Point

`ArgisExecServer.create()`


### 🟡 Tools

Single `execute` tool that uses AgentRuntime


### 🟡 Framework

FastAPI


### 🟡 Purpose

REST API endpoints for tool routing, search, etc.


### 🟡 Entry Point

`app` (FastAPI application)


### 🟡 Endpoints

`/health`, `/route`, `/tools`, `/semantic-search`


### 🟡 Purpose

GraphQL client for Bifrost backend delegation


### 🟡 Used By

Both `server.py` and `main.py`


### 🟡 Default URL

`http://localhost:8080/graphql`


### 🟡 MCP Server (`server.py`)




### 🟡 HTTP API (`main.py`)




### 🟡 Bifrost Client (`bifrost_client.py`)




### 🟡 `server.py`

- MCP Server (FastMCP protocol)


### 🟡 `main.py`

- FastAPI HTTP API (REST endpoints)


### 🟡 Overall Coverage

71.1%


### 🟡 Tests Collected

642


### 🟡 Tests Passing

~252-320 (post-asyncio fix)


### 🔴 Critical Infrastructure Fixed

pytest-asyncio plugin registration


### 🟡 Problem

Async test methods in classes were not being recognized


### 🟡 Root Cause

pytest.ini in tests/ subdirectory was overriding root pytest.ini


### 🟡 Solution

- Moved pytest.ini to project root


### 🟡 runtime/namespace

Need 8-10 tests (currently few)


### 🟡 runtime/events/background

Need 10-12 tests


### 🟡 runtime/events/bus

Need 10-12 tests


### 🟡 runtime/scope/storage

Need 25-30 tests (largest module)


### 🟡 runtime/sandbox

Need 20-25 tests


### 🟡 runtime/mcp/manager

Need 8-10 tests


### 🟡 runtime/core

Need 10-12 tests


### 🟡 runtime/events/api

Need 8-10 tests


### 🟡 runtime/mcp/api

Need 6-8 tests


### 🟡 tools/execute

Need 8-10 tests


### 🟡 runtime/scope/api

Need 8-10 tests


### 🟡 runtime/scope/manager

Need 12-15 tests


### 🟡 1. pytest-asyncio Plugin Registration




### 🟡 2. Pytest Version Compatibility




### 🔴 Critical Path Modules (0-40% coverage) - HIGHEST PRIORITY




### 🟠 Medium Coverage Modules (40-80%) - SECONDARY PRIORITY




### 🟡 Well-Covered Modules (80-100%) - MAINTAIN




### 🟡 Current Distribution Estimate




### 🟡 Required Test Breakdown by Coverage Zone




### 🟡 1. **runtime/namespace** (26.6%)




### 🟡 2. **runtime/events/background** (29.5%)




### 🟡 3. **runtime/events/bus** (33.3%)




### 🟡 4. **runtime/scope/storage** (36.1%) - LARGEST GAP




### 🟡 5. **runtime/scope/manager** (37.0%)




### 🟡 6. **runtime/sandbox** (37.3%)




### 🟡 7. **runtime/mcp/manager** (38.5%)




### 🟡 8. **runtime/core** (50.0%)




### 🟡 Phase 1: Fix Failing Tests (Target: 95%+ pass rate)




### 🔴 Phase 2: Unit Tests for Critical Path (0-40% coverage)




### 🟡 Phase 3: Unit Tests for Medium Coverage (40-80%)




### 🟡 Phase 4: Integration & E2E Tests




### 🟡 Identify all failing tests

```bash


### 🟡 Categorize failures

- Missing mock implementations


### 🟡 Fix by category

(prioritize):


### 🟡 Validation

```bash


### 🟡 Immediate

(now):


### 🟡 Hour 1-3

- Fix all AsyncIO test issues (DONE)


### 🔴 Hour 4-11

- Implement unit tests for critical path modules


### 🟡 Hour 12-21

- Implement unit tests for medium coverage modules


### 🟡 Validation

- Run full coverage report


### 🟡 Zero Startup Latency

No code generation or heavy initialization


### 🟡 RequestDirector

Stateless HTTP request building using openapi-core


### 🟡 Pre-calculated Schemas

All complex processing done during parsing


### 🟡 Single Code Path

All components use RequestDirector consistently


### 🟡 No Fallbacks

Simplified architecture without hybrid complexity


### 🟡 Performance First

Optimized for cold starts and serverless deployments


### 🟡 openapi-core Integration

Leverages proven library for parameter serialization


### 🟡 Full Feature Support

Complete OpenAPI 3.0/3.1 support including deepObject


### 🟡 Error Handling

Comprehensive HTTP error mapping to MCP errors


### 🟡 Advantages

Zero latency, robust, comprehensive OpenAPI support


### 🟡 Advantages

High performance, simplified architecture, reliable error handling


### 🟡 Automatic Suffixing

Colliding parameters get location-based suffixes


### 🟡 Example

`id` in path and body becomes `id__path` and `id`


### 🟡 Transparent

LLMs see suffixed parameters, implementation routes correctly


### 🟡 Native Support

Generated client handles all deepObject variations


### 🟡 Explode Handling

Proper support for explode=true/false


### 🟡 Complex Objects

Nested object serialization works correctly


### 🟡 Status Code Mapping

HTTP errors mapped to appropriate MCP errors


### 🟡 Structured Responses

Error details preserved in tool results


### 🟡 Timeout Handling

Network timeouts handled gracefully


### 🟡 Parameter Validation

Invalid parameters caught during request building


### 🟡 Schema Validation

openapi-core validates all OpenAPI constraints


### 🟡 Graceful Degradation

Missing optional parameters handled smoothly


### 🟡 Connection Pooling

HTTP connections reused across requests


### 🟡 Client Caching

Generated clients cached for performance


### 🟡 Async Support

Full async/await throughout


### 🟡 Pre-calculated Schemas

All complex processing done during initialization


### 🟡 Parameter Mapping

Collision resolution handled upfront


### 🟡 Zero Latency

No runtime code generation or complex schema processing


### 🟡 Same Interface

Public API unchanged from legacy implementation


### 🟡 Performance Improvement

Significantly faster initialization


### 🟡 No Breaking Changes

Existing code works without modification


### 🟡 RequestDirector Initialization

Success/failure of RequestDirector setup


### 🟡 Schema Pre-calculation

Pre-calculated schema and parameter map status


### 🟡 Request Building

Parameter mapping and URL construction details


### 🟡 Performance Metrics

Request timing and error rates


### 🟡 Core Components




### 🟡 Key Architecture Principles




### 🟡 RequestDirector-Based Components




### 🟡 `FastMCPOpenAPI` Class




### 🟡 Component Creation Logic




### 🟡 Stateless Request Building




### 🟡 1. Enhanced Parameter Handling




### 🟡 2. Robust Error Handling




### 🟡 3. Performance Optimizations




### 🟡 Server Options




### 🟡 Route Mapping Customization




### 🟡 Test Structure




### 🟡 Testing Philosophy




### 🟡 Example Test Pattern




### 🟡 From Legacy Implementation




### 🟡 Backward Compatibility




### 🟡 Logging




### 🟡 Key Log Messages




### 🟡 Debugging Common Issues




### 🟡 Planned Features




### 🟡 Performance Improvements




### 🟡 `server.py`

- `FastMCPOpenAPI` main server class with RequestDirector integration


### 🟡 `components.py`

- Simplified component implementations using RequestDirector


### 🟡 `routing.py`

- Route mapping and component selection logic


### 🟡 Spec Parsing

OpenAPI spec parsed to `HTTPRoute` models with pre-calculated schemas


### 🟡 RequestDirector Setup

openapi-core Spec initialized for request building


### 🟡 Component Creation

Create components with RequestDirector reference


### 🟡 Request Building

RequestDirector builds HTTP request from flat parameters


### 🟡 Request Execution

Execute request with httpx client


### 🟡 Response Processing

Return structured MCP response


### 🟡 Real Integration

Test with real OpenAPI specs and HTTP clients


### 🟡 Minimal Mocking

Only mock external API endpoints


### 🟡 Behavioral Focus

Test behavior, not implementation details


### 🟡 Performance Focus

Test that initialization is fast and stateless


### 🟡 Eliminated Startup Latency

Zero code generation overhead (100-200ms improvement)


### 🟡 Better OpenAPI Compliance

openapi-core handles all OpenAPI features correctly


### 🟡 Serverless Friendly

Perfect for cold-start environments


### 🟡 Simplified Architecture

Single RequestDirector approach eliminates complexity


### 🟡 Enhanced Reliability

No dynamic code generation failures


### 🟡 RequestDirector Initialization Fails

- Check OpenAPI spec validity with `openapi-core`


### 🟡 Parameter Issues

- Enable debug logging for parameter processing


### 🟡 Performance Issues

- Monitor RequestDirector request building timing


### 🟡 Advanced Caching

Intelligent response caching with TTL


### 🟡 Streaming Support

Handle streaming API responses


### 🟡 Batch Operations

Optimize multiple operation calls


### 🟡 Enhanced Monitoring

Detailed metrics and health checks


### 🟡 Configuration Management

Dynamic configuration updates


### 🟡 Enhanced Schema Caching

More aggressive schema pre-calculation


### 🟡 Parallel Processing

Concurrent operation execution


### 🟡 Memory Optimization

Further reduce memory footprint


### 🟡 Request Optimization

Smart request batching and deduplication


### 🟡 Schema Pre-calculation

Combined schemas calculated once during parsing


### 🟡 Parameter Mapping

Collision resolution mapping calculated upfront


### 🟡 Zero Runtime Overhead

All complex processing done during initialization


### 🟡 No Code Generation

Eliminates 100-200ms startup latency


### 🟡 Serverless Friendly

Ideal for cold-start environments


### 🟡 Minimal Dependencies

Uses lightweight `openapi-core` instead of full client generation


### 🟡 Parameter Collisions

Intelligent collision resolution with suffixing


### 🟡 DeepObject Style

Full support for deepObject parameters with explode=true/false


### 🟡 Complex Schemas

Handles nested objects, arrays, and all OpenAPI types


### 🟡 Pre-calculated Mapping

Parameter location mapping done upfront for performance


### 🟡 Pre-calculated Schemas

Combined parameter and body schemas calculated once


### 🟡 Collision-aware

Automatically handles parameter name collisions


### 🟡 Type Safety

Full Pydantic model validation


### 🟡 Performance

Zero runtime schema processing overhead


### 🟡 Real Objects

Use real HTTPRoute models and OpenAPI specifications


### 🟡 Minimal Mocking

Only mock external HTTP endpoints


### 🟡 Performance Focus

Test that initialization is fast and stateless


### 🟡 Behavioral Testing

Verify OpenAPI compliance without implementation details


### 🟡 Cold Start

Zero latency penalty for serverless deployments


### 🟡 Memory Usage

Lower memory footprint without generated client code


### 🟡 Reliability

No dynamic code generation failures


### 🟡 Maintainability

Simpler architecture with fewer moving parts


### 🟡 Core Components




### 🟡 Key Architecture Principles




### 🟡 Initialization Process




### 🟡 Request Processing




### 🟠 1. High-Performance Request Building




### 🟡 2. Comprehensive Parameter Support




### 🟡 3. Enhanced Error Handling




### 🟡 4. Advanced Schema Processing




### 🟡 Server Components (`/server/openapi_new/`)




### 🟡 RequestDirector Integration




### 🟡 Basic Server Setup




### 🟡 Direct RequestDirector Usage




### 🟡 Test Categories




### 🟡 Testing Philosophy




### 🟡 From Legacy Implementation




### 🟡 Performance Improvements




### 🟡 Planned Features




### 🟡 Performance Improvements




### 🟡 Common Issues




### 🟡 Debugging




### 🟡 `director.py`

- `RequestDirector` for stateless HTTP request building


### 🟡 `parser.py`

- OpenAPI spec parsing and route extraction with pre-calculated schemas


### 🟡 `schemas.py`

- Schema processing with parameter mapping for collision handling


### 🟡 `models.py`

- Enhanced data models with pre-calculated fields for performance


### 🟡 `formatters.py`

- Response formatting and processing utilities


### 🟡 Input

Raw OpenAPI specification (dict)


### 🟡 Parsing

Extract operations to `HTTPRoute` models


### 🟡 Pre-calculation

Generate combined schemas and parameter maps during parsing


### 🟡 Director Setup

Create `RequestDirector` with `SchemaPath` for request building


### 🟡 Tool Invocation

FastMCP receives tool call with parameters


### 🟡 Request Building

RequestDirector builds HTTP request using parameter map


### 🟡 Parameter Handling

openapi-core handles all OpenAPI serialization rules


### 🟡 Response Processing

Parse response into structured format with proper error handling


### 🟡 `OpenAPITool`

- Simplified tool implementation using RequestDirector


### 🟡 `OpenAPIResource`

- Resource implementation with RequestDirector


### 🟡 `OpenAPIResourceTemplate`

- Resource template with RequestDirector support


### 🟡 `FastMCPOpenAPI`

- Main server class with stateless request building


### 🟡 Core Functionality

- `test_server.py` - Server initialization and RequestDirector integration


### 🟡 OpenAPI Features

- `test_parameter_collisions.py` - Parameter name collision handling


### 🟡 Import Changes

```python


### 🟡 Constructor

Same interface, no changes needed


### 🟡 Automatic Benefits

- Eliminates startup latency (100-200ms improvement)


### 🟡 Response Streaming

Handle streaming API responses


### 🟡 Enhanced Authentication

More auth provider integrations


### 🟡 Advanced Metrics

Detailed request/response monitoring


### 🟡 Schema Validation

Enhanced input/output validation


### 🟡 Batch Operations

Optimized multi-operation requests


### 🟡 Schema Caching

More aggressive schema pre-calculation


### 🟡 Memory Optimization

Further reduce memory footprint


### 🟡 Request Batching

Smart batching for bulk operations


### 🟡 Connection Optimization

Enhanced connection pooling strategies


### 🟡 RequestDirector Initialization Fails

- Check OpenAPI spec validity with `jsonschema-path`


### 🟡 Parameter Mapping Issues

- Check parameter collision resolution in debug logs


### 🟡 Request Building Errors

- Check network connectivity to target API


### 🟡 Zero Startup Latency

No code generation or heavy initialization


### 🟡 RequestDirector

Stateless HTTP request building using openapi-core


### 🟡 Pre-calculated Schemas

All complex processing done during parsing


### 🟡 Single Code Path

All components use RequestDirector consistently


### 🟡 No Fallbacks

Simplified architecture without hybrid complexity


### 🟡 Performance First

Optimized for cold starts and serverless deployments


### 🟡 openapi-core Integration

Leverages proven library for parameter serialization


### 🟡 Full Feature Support

Complete OpenAPI 3.0/3.1 support including deepObject


### 🟡 Error Handling

Comprehensive HTTP error mapping to MCP errors


### 🟡 Advantages

Zero latency, robust, comprehensive OpenAPI support


### 🟡 Advantages

High performance, simplified architecture, reliable error handling


### 🟡 Automatic Suffixing

Colliding parameters get location-based suffixes


### 🟡 Example

`id` in path and body becomes `id__path` and `id`


### 🟡 Transparent

LLMs see suffixed parameters, implementation routes correctly


### 🟡 Native Support

Generated client handles all deepObject variations


### 🟡 Explode Handling

Proper support for explode=true/false


### 🟡 Complex Objects

Nested object serialization works correctly


### 🟡 Status Code Mapping

HTTP errors mapped to appropriate MCP errors


### 🟡 Structured Responses

Error details preserved in tool results


### 🟡 Timeout Handling

Network timeouts handled gracefully


### 🟡 Parameter Validation

Invalid parameters caught during request building


### 🟡 Schema Validation

openapi-core validates all OpenAPI constraints


### 🟡 Graceful Degradation

Missing optional parameters handled smoothly


### 🟡 Connection Pooling

HTTP connections reused across requests


### 🟡 Client Caching

Generated clients cached for performance


### 🟡 Async Support

Full async/await throughout


### 🟡 Pre-calculated Schemas

All complex processing done during initialization


### 🟡 Parameter Mapping

Collision resolution handled upfront


### 🟡 Zero Latency

No runtime code generation or complex schema processing


### 🟡 Same Interface

Public API unchanged from legacy implementation


### 🟡 Performance Improvement

Significantly faster initialization


### 🟡 No Breaking Changes

Existing code works without modification


### 🟡 RequestDirector Initialization

Success/failure of RequestDirector setup


### 🟡 Schema Pre-calculation

Pre-calculated schema and parameter map status


### 🟡 Request Building

Parameter mapping and URL construction details


### 🟡 Performance Metrics

Request timing and error rates


### 🟡 Core Components




### 🟡 Key Architecture Principles




### 🟡 RequestDirector-Based Components




### 🟡 `FastMCPOpenAPI` Class




### 🟡 Component Creation Logic




### 🟡 Stateless Request Building




### 🟡 1. Enhanced Parameter Handling




### 🟡 2. Robust Error Handling




### 🟡 3. Performance Optimizations




### 🟡 Server Options




### 🟡 Route Mapping Customization




### 🟡 Test Structure




### 🟡 Testing Philosophy




### 🟡 Example Test Pattern




### 🟡 From Legacy Implementation




### 🟡 Backward Compatibility




### 🟡 Logging




### 🟡 Key Log Messages




### 🟡 Debugging Common Issues




### 🟡 Planned Features




### 🟡 Performance Improvements




### 🟡 `server.py`

- `FastMCPOpenAPI` main server class with RequestDirector integration


### 🟡 `components.py`

- Simplified component implementations using RequestDirector


### 🟡 `routing.py`

- Route mapping and component selection logic


### 🟡 Spec Parsing

OpenAPI spec parsed to `HTTPRoute` models with pre-calculated schemas


### 🟡 RequestDirector Setup

openapi-core Spec initialized for request building


### 🟡 Component Creation

Create components with RequestDirector reference


### 🟡 Request Building

RequestDirector builds HTTP request from flat parameters


### 🟡 Request Execution

Execute request with httpx client


### 🟡 Response Processing

Return structured MCP response


### 🟡 Real Integration

Test with real OpenAPI specs and HTTP clients


### 🟡 Minimal Mocking

Only mock external API endpoints


### 🟡 Behavioral Focus

Test behavior, not implementation details


### 🟡 Performance Focus

Test that initialization is fast and stateless


### 🟡 Eliminated Startup Latency

Zero code generation overhead (100-200ms improvement)


### 🟡 Better OpenAPI Compliance

openapi-core handles all OpenAPI features correctly


### 🟡 Serverless Friendly

Perfect for cold-start environments


### 🟡 Simplified Architecture

Single RequestDirector approach eliminates complexity


### 🟡 Enhanced Reliability

No dynamic code generation failures


### 🟡 RequestDirector Initialization Fails

- Check OpenAPI spec validity with `openapi-core`


### 🟡 Parameter Issues

- Enable debug logging for parameter processing


### 🟡 Performance Issues

- Monitor RequestDirector request building timing


### 🟡 Advanced Caching

Intelligent response caching with TTL


### 🟡 Streaming Support

Handle streaming API responses


### 🟡 Batch Operations

Optimize multiple operation calls


### 🟡 Enhanced Monitoring

Detailed metrics and health checks


### 🟡 Configuration Management

Dynamic configuration updates


### 🟡 Enhanced Schema Caching

More aggressive schema pre-calculation


### 🟡 Parallel Processing

Concurrent operation execution


### 🟡 Memory Optimization

Further reduce memory footprint


### 🟡 Request Optimization

Smart request batching and deduplication


### 🟡 Schema Pre-calculation

Combined schemas calculated once during parsing


### 🟡 Parameter Mapping

Collision resolution mapping calculated upfront


### 🟡 Zero Runtime Overhead

All complex processing done during initialization


### 🟡 No Code Generation

Eliminates 100-200ms startup latency


### 🟡 Serverless Friendly

Ideal for cold-start environments


### 🟡 Minimal Dependencies

Uses lightweight `openapi-core` instead of full client generation


### 🟡 Parameter Collisions

Intelligent collision resolution with suffixing


### 🟡 DeepObject Style

Full support for deepObject parameters with explode=true/false


### 🟡 Complex Schemas

Handles nested objects, arrays, and all OpenAPI types


### 🟡 Pre-calculated Mapping

Parameter location mapping done upfront for performance


### 🟡 Pre-calculated Schemas

Combined parameter and body schemas calculated once


### 🟡 Collision-aware

Automatically handles parameter name collisions


### 🟡 Type Safety

Full Pydantic model validation


### 🟡 Performance

Zero runtime schema processing overhead


### 🟡 Real Objects

Use real HTTPRoute models and OpenAPI specifications


### 🟡 Minimal Mocking

Only mock external HTTP endpoints


### 🟡 Performance Focus

Test that initialization is fast and stateless


### 🟡 Behavioral Testing

Verify OpenAPI compliance without implementation details


### 🟡 Core Components




### 🟡 Key Architecture Principles




### 🟡 Initialization Process




### 🟡 Request Processing




### 🟠 1. High-Performance Request Building




### 🟡 2. Comprehensive Parameter Support




### 🟡 3. Enhanced Error Handling




### 🟡 4. Advanced Schema Processing




### 🟡 Server Components (`/server/openapi/`)




### 🟡 RequestDirector Integration




### 🟡 Basic Server Setup




### 🟡 Direct RequestDirector Usage




### 🟡 Test Categories




### 🟡 Testing Philosophy




### 🟡 Planned Features




### 🟡 Performance Improvements




### 🟡 Common Issues




### 🟡 Debugging




### 🟡 `director.py`

- `RequestDirector` for stateless HTTP request building


### 🟡 `parser.py`

- OpenAPI spec parsing and route extraction with pre-calculated schemas


### 🟡 `schemas.py`

- Schema processing with parameter mapping for collision handling


### 🟡 `models.py`

- Enhanced data models with pre-calculated fields for performance


### 🟡 `formatters.py`

- Response formatting and processing utilities


### 🟡 Input

Raw OpenAPI specification (dict)


### 🟡 Parsing

Extract operations to `HTTPRoute` models


### 🟡 Pre-calculation

Generate combined schemas and parameter maps during parsing


### 🟡 Director Setup

Create `RequestDirector` with `SchemaPath` for request building


### 🟡 Tool Invocation

FastMCP receives tool call with parameters


### 🟡 Request Building

RequestDirector builds HTTP request using parameter map


### 🟡 Parameter Handling

openapi-core handles all OpenAPI serialization rules


### 🟡 Response Processing

Parse response into structured format with proper error handling


### 🟡 `OpenAPITool`

- Simplified tool implementation using RequestDirector


### 🟡 `OpenAPIResource`

- Resource implementation with RequestDirector


### 🟡 `OpenAPIResourceTemplate`

- Resource template with RequestDirector support


### 🟡 `FastMCPOpenAPI`

- Main server class with stateless request building


### 🟡 Core Functionality

- `test_server.py` - Server initialization and RequestDirector integration


### 🟡 OpenAPI Features

- `test_parameter_collisions.py` - Parameter name collision handling


### 🟡 Response Streaming

Handle streaming API responses


### 🟡 Enhanced Authentication

More auth provider integrations


### 🟡 Advanced Metrics

Detailed request/response monitoring


### 🟡 Schema Validation

Enhanced input/output validation


### 🟡 Batch Operations

Optimized multi-operation requests


### 🟡 Schema Caching

More aggressive schema pre-calculation


### 🟡 Memory Optimization

Further reduce memory footprint


### 🟡 Request Batching

Smart batching for bulk operations


### 🟡 Connection Optimization

Enhanced connection pooling strategies


### 🟡 RequestDirector Initialization Fails

- Check OpenAPI spec validity with `jsonschema-path`


### 🟡 Parameter Mapping Issues

- Check parameter collision resolution in debug logs


### 🟡 Request Building Errors

- Check network connectivity to target API


### 🟡 [Installation Guide](https://vllm-semantic-router.com/docs/installation/)

- Complete setup instructions


### 🟡 [System Architecture](https://vllm-semantic-router.com/docs/overview/architecture/system-architecture/)

- Technical deep dive


### 🟡 [Model Training](https://vllm-semantic-router.com/docs/training/training-overview/)

- How classification models work


### 🟡 [API Reference](https://vllm-semantic-router.com/docs/api/router/)

- Complete API documentation


### 🟡 [Dashboard](https://vllm-semantic-router.com/docs/overview/dashboard)

- vLLM Semantic Router Dashboard


### 🟡 First Tuesday of the month

9:00-10:00 AM EST (accommodates US EST, EU, and Asia Pacific contributors)


### 🟡 Third Tuesday of the month

1:00-2:00 PM EST (accommodates US EST and California contributors)


### 🟡 Intelligent Routing 🧠




### 🟡 Enterprise Security 🔒




### 🟡 vLLM Semantic Router Dashboard 💬




### 🟡 Community Meetings 📅




### 🟡 Code Generation:

Kilo can generate code using natural language.


### 🟡 Task Automation:

Kilo can automate repetitive coding tasks.


### 🟡 Automated Refactoring:

Kilo can refactor and improve existing code.


### 🟡 MCP Server Marketplace

Kilo can easily find, and use MCP servers to extend the agent capabilities.


### 🟡 Multi Mode

Plan with Architect, Code with Coder, and Debug with Debugger, and make your own custom modes.


### 🟡 80% reduction in input tokens

- Dramatically lower costs and faster responses


### 🟡 Self-learning

- Automatically discovers and categorizes API response patterns


### 🟠 Smart filtering

- Pins important fields, removes noise, ghosts redundant data


### 🟡 Drop-in replacement

- Works with existing MCP servers (Node.js-based)


### 🟡 Community-driven

- Share your learned schemas in `registry.json`


### 🟡 Pinned

📌 - Essential fields always included (e.g., `id`, `title`, `state`)


### 🟡 Noise

🔇 - Redundant fields removed (e.g., `_links`, `imageUrl`, `descriptor`)


### 🟡 Ghosts

👻 - Fields summarized or count-only (e.g., long lists, nested objects)


### 🟡 Key Benefits




### 🟡 1. Install Dependencies




### 🟡 2. Configure Servers




### 🟡 3. Set Up Claude Desktop Integration




### 🟡 4. Start Using




### 🟡 Current Support




### 🟡 Coming Soon




### 🟡 servers.json Structure




### 🟡 registry.json Structure




### 🟡 Application-Scoped Components




### 🟡 Request-Scoped Components




### 🟡 1. `get_feature_extractor_dep()`




### 🟡 2. `RequestContext`




### 🟡 3. `get_request_context()`




### 🟡 Example 1: Basic FastAPI Route Integration




### 🟡 Example 2: Direct FeatureExtractor Usage




### 🟡 Example 3: Advanced Context with Metadata




### 🟡 Example 4: Integration with Existing Routes




### 🟡 FeatureExtractor (Application-Scoped)




### 🟡 RequestContext (Request-Scoped)




### 🟡 Unit Test Example




### 🟡 Integration Test Example




### 🟡 From Old Dependencies (prediction.ml_models)




### 🟡 Benefits of Migration




### 🟡 Common Issues




### 🟡 Automatic Singleton Management

- No manual global state


### 🟡 Request-Scoped Caching

- Features computed once per request


### 🟡 FastAPI Integration

- Native dependency injection


### 🟡 Thread-Safety

- Built-in fine-grained locking


### 🟡 Performance Tracking

- Automatic timing and metrics


### 🟡 Better Testing

- Easy to mock and test


### 🟡 Always initialize context early:

```python


### 🟡 Extract features once per request:

```python


### 🟡 Store routing metadata:

```python


### 🟡 Log comprehensive context:

```python


### 🟡 Use for performance tracking:

```python


### 🟡 70% ML Predictor

- Learned from historical performance


### 🟡 30% Thompson Sampling Bandit

- Exploration/exploitation


### 🟡 Live Request Simulation

- Test different routing strategies with pre-configured prompts


### 🟡 Cost Comparison

- Visualize cost savings across different routing strategies


### 🟡 Performance Analysis

- Compare model performance metrics


### 🟡 Model Routing

- See how different task types are routed to optimal models


### 🟡 Cost Reduction:

85-90% vs. direct premium model usage (vs 70-85% rule-based)


### 🟡 Latency (p95):

<3000ms (including ML prediction + routing)


### 🟡 Success Rate:

99%+ with fallback


### 🟡 Quality Retention:

95-99% (vs 90-95% baseline)


### 🟡 Fallback Rate:

5-10% (vs 10-20% baseline)


### 🟡 Prediction Accuracy:

85-90% (XGBoost)


### 🟡 Bandit Exploration:

30% of decisions


### 🟡 Training Data:

30-90 days historical


### 🟡 Retraining Frequency:

Weekly (automated)


### 🟡 Not Diamond

- Model selection recommendation


### 🟡 OpenRouter

- Multi-provider aggregation


### 🟡 FastAPI

- Modern Python web framework


### 🟡 Pydantic

- Data validation


### 🟡 All LLM providers

- Making AI accessible


### 🟡 [KROUTE.md](./KROUTE.md)

- Architecture Blueprint


### 🟡 [PLAN.md](./PLAN.md)

- Master Planning Document


### 🟡 Key Features




### 🟡 1. Clone and Configure




### 🟡 2. Start with Docker Compose




### 🟡 3. Verify




### 🟡 4. Use




### 🟡 Proxy Mode (Direct OpenRouter)




### 🟡 Unified CLI workflow




### 🟡 Quick Start with ML




### 🟡 How It Works




### 🟡 Expected Impact




### 🟡 ML System Components




### 🟡 Primary Documents




### 🟡 ML & Analytics Documentation ✅ **NEW**




### 🟡 Implementation Reports




### 🟡 Research & Analysis




### 🟡 Milestone Reports




### 🟡 Implementation Tracking




### 🟡 Examples




### 🟡 Prerequisites




### 🟡 Installation




### 🟡 Usage




### 🟡 Configuration




### 🟡 Free-First Policy




### 🟡 Full-Spectrum Policy




### 🟡 Advanced Reasoning




### 🟡 Web Search Integration




### 🟡 Combined Features




### 🟠 High-Level Flow (with ML)




### 🟡 Directory Structure




### 🟡 Phase 1: Core System ✅ COMPLETE




### 🟡 Phase 2: ML Optimization ✅ COMPLETE




### 🟡 Phase 3: Future Enhancements 🔮




### 🟡 Running the Demo




### 🟡 Demo Features




### 🟡 Demo Endpoint




### 🟡 Key Metrics




### 🟡 Usage Analytics




### 🟡 ML Metrics & Insights




### 🟡 Metrics Database




### 🟡 [PLAN.md](./PLAN.md)

- Master Planning Document ✅ **COMPLETE**


### 🟡 [KROUTE.md](./KROUTE.md)

- Complete Architecture Blueprint


### 🟡 [DEPLOYMENT.md](./DEPLOYMENT.md)

- Production Deployment Guide ✅


### 🟡 [METRICS_SYSTEM_COMPLETE.md](./METRICS_SYSTEM_COMPLETE.md)

- ML System Overview ✅ **NEW**


### 🟡 [METRICS_ANALYSIS_SPEC.md](./METRICS_ANALYSIS_SPEC.md)

- Technical Specification ✅ **NEW**


### 🟡 [METRICS_QUICKSTART.md](./METRICS_QUICKSTART.md)

- Quick Start Guide ✅ **NEW**


### 🟡 [docs/OPENROUTER_RESPONSES_API.md](./docs/OPENROUTER_RESPONSES_API.md)

- Responses API Alpha ✅ **NEW**


### 🟡 [docs/METRICS_SYSTEM_DIAGRAM.md](./docs/METRICS_SYSTEM_DIAGRAM.md)

- Architecture Diagrams ✅ **NEW**


### 🟡 [WEEK2_PROGRESS.md](./WEEK2_PROGRESS.md)

- Analysis Implementation ✅ **NEW**


### 🟡 [WEEK3_COMPLETE.md](./WEEK3_COMPLETE.md)

- ML Implementation ✅ **NEW**


### 🟡 [ROUTELLM_ANALYSIS.md](./ROUTELLM_ANALYSIS.md)

- RouteLLM Integration ✅


### 🟡 [METRICS_RESEARCH.md](./METRICS_RESEARCH.md)

- Metrics Research ✅ **NEW**


### 🟡 Milestone Completion Reports

✅ **ALL COMPLETE**


### 🟡 [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)

- Complete WBS ✅ **100% COMPLETE**


### 🟡 [METRICS_IMPLEMENTATION_STATUS.md](./METRICS_IMPLEMENTATION_STATUS.md)

- ML System Status ✅ **NEW**


### 🟡 [examples/basic_usage.py](./examples/basic_usage.py)

- Usage Examples ✅


### 🟡 Minimum:

NVIDIA Volta (V100, compute 7.0+)


### 🟡 Recommended:

NVIDIA Ampere (A10G, A100, compute 8.0+)


### 🟡 CUDA Version:

12.0+


### 🟡 PyTorch Version:

2.0+


### 🟡 Language:

English only (non-English may produce unreliable results)


### 🟡 Length:

1-512 tokens (longer prompts truncated)


### 🟡 Encoding:

UTF-8


### 🟡 Format:

Plain text (markdown/code formatting preserved)


### 🟡 GPU:

NVIDIA Volta (V100) or newer, compute 7.0+


### 🟡 CUDA:

12.0+


### 🟡 Python:

3.10+


### 🟡 PyTorch:

2.0+


### 🟡 Transformers:

4.30+


### 🟡 Memory:

4 GB GPU VRAM (FP16, batch 1)


### 🟡 GPU:

NVIDIA Ampere (A10G, A100)


### 🟡 CUDA:

12.2+


### 🟡 Python:

3.11


### 🟡 PyTorch:

2.2+


### 🟡 Memory:

8 GB GPU VRAM (FP16, batch 32)


### 🟡 LOCAL

(1-5ms, $0): On-device models, fastest, lowest quality


### 🟡 FAST

(5-50ms, baseline cost): Cloud models with minimal latency


### 🟡 BALANCED

(50-500ms, 2x cost): Balanced performance and accuracy


### 🟠 QUALITY

(100ms+, 5x cost): High-quality models, best accuracy


### 🟡 REASONING

(500ms+, 10x cost): Extended reasoning models


### 🟡 1. RoutingTier (Enum)




### 🟡 2. ProviderCapabilities (Enum)




### 🟡 3. CapabilityLevel (Enum)




### 🟡 4. ModelSpec (Dataclass)




### 🟡 5. RoutingConstraints (Dataclass)




### 🟡 6. UnifiedRoutingDecision (Dataclass)




### 🟡 7. CapabilitySupport (Dataclass)




### 🟡 Example 1: Model Selection




### 🟡 Example 2: Fallback Strategy




### 🟡 Example 3: Cost Analysis




### 🟡 1. Replacing Old Decision Types




### 🟡 2. Replacing Capability Checks




### 🟡 3. Constraint Validation




### 🟡 Single Source of Truth

All routing types defined in one module


### 🟡 Type Safety

Full type hints throughout


### 🟡 Immutability

Frozen dataclasses where appropriate


### 🟡 Composition

Complex types built from simpler ones


### 🟡 Validation

Post-init validation for invariants


### 🟡 Serialization

`.to_dict()` methods for logging/APIs


### 🟡 Extensibility

`metadata` fields for future use


### 🟡 Documentation

Comprehensive docstrings and examples


### 🟡 CI/CD Dashboard:

Workflow success rates, execution times


### 🟡 Test Dashboard:

Test counts, coverage trends, flaky tests


### 🟡 Performance Dashboard:

Response times, throughput, resource usage


### 🟡 Deployment Dashboard:

Frequency, success rate, rollbacks


### 🟡 Documentation:

`/docs` directory


### 🟡 Slack:

#router-ci-cd


### 🟡 Team Wiki:

https://wiki.internal/router/cicd


### 🟡 GitHub Issues:

Report bugs/feature requests


### 🟡 On-call:

https://pagerduty.com/schedules/router-oncall


### 🟡 Tech Lead:

@tech-lead


### 🟡 DevOps Team:

@devops


### 🟡 Security Team:

security@example.com


### 🟡 For Developers




### 🟡 For DevOps




### 🟡 ✅ Automated Testing




### 🟡 🔒 Security & Quality




### 🟡 ⚡ Performance




### 🟡 🔄 Compatibility




### 🟡 🚀 Deployment




### 🟡 📢 Notifications




### 🟡 Getting Started




### 🟡 Setup & Configuration




### 🟡 Operations




### 🟡 Run Tests Locally




### 🟡 Run Workflows Locally




### 🟡 Trigger Workflows Manually




### 🟡 Check Workflow Status




### 🟡 Key Metrics




### 🟡 Dashboards




### 🟡 Required Secrets




### 🟡 Security Features




### 🟡 For Developers




### 🟡 For DevOps




### 🟡 Common Issues




### 🟡 Get Help




### 🟡 Planned Enhancements




### 🟡 Workflow Changes




### 🟡 Documentation




### 🟡 Resources




### 🟡 Contacts




### 🟡 Run tests locally before pushing

```bash


### 🟡 Keep PRs small and focused

- Single feature/fix per PR


### 🟡 Watch CI results

```bash


### 🟡 Fix failures immediately

- Don't merge with failing tests


### 🟡 Monitor CI/CD health

- Weekly review of failed workflows


### 🟡 Maintain baselines

- Update after optimizations


### 🟡 Deploy safely

- Always to staging first


### 🟡 Communicate

- Notify team of deployments


### 🟡 Check documentation:

[Troubleshooting Guide](docs/CI_CD_TROUBLESHOOTING.md)


### 🟡 Search logs:

`gh run view --log | grep ERROR`


### 🟡 Ask team:

#router-ci-cd Slack channel


### 🟡 Page on-call:

For production issues


### 🟡 `models`

Core model information (ID, name, provider, tier, context length)


### 🟡 `pricing`

Real-time pricing data from OpenRouter


### 🟡 `capabilities`

Model capabilities (tool use, vision, code, reasoning)


### 🟡 `benchmarks`

Performance benchmarks and scores


### 🟡 `ai_research`

Community sentiment and research insights


### 🟡 `historical_performance`

Historical performance data


### 🟡 `local_performance`

Local model performance metrics


### 🟡 🆓 Free Tier

`$0.00/1M tokens` (local models, OpenRouter free models)


### 🟡 💵 Budget Tier

`$0.18-$2.50/1M tokens` (very cheap OpenRouter models)


### 🟠 💎 Premium Tier

`$3.00-$18.00/1M tokens` (high-quality models)


### 🟡 Small Tasks

(≤32K context): Local models preferred for speed


### 🟡 Large Tasks

(>32K context): Cloud models preferred for quality


### 🟡 Niche Tasks

Local models with specific capabilities


### 🟡 Real-time pricing

Always uses current OpenRouter prices


### 🟡 Budget-aware selection

Automatically stays within cost limits


### 🟡 Tier-based escalation

Tries free → budget → premium models


### 🟡 Capability matching

Selects models with required capabilities


### 🟡 Performance weighting

Considers benchmarks and historical data


### 🟡 Local optimization

Properly weights local vs cloud models


### 🟡 Fallback support

Falls back to static registry if database fails


### 🟡 Error handling

Graceful degradation on API failures


### 🟡 Caching

Reduces database queries with intelligent caching


### 🟡 **Database Schema**




### 🟡 **Key Components**




### 🟡 **1. Install Dependencies**




### 🟡 **2. Set Environment Variables**




### 🟡 **3. Run Migration**




### 🟡 **4. Update KRouter Configuration**




### 🟡 **Cost-Based Selection**




### 🟡 **Task-Specific Optimization**




### 🟡 **Local Model Weighting**




### 🟡 **Database Configuration**




### 🟡 **Sync Configuration**




### 🟡 **Cost Optimization**




### 🟡 **Quality Optimization**




### 🟡 **Reliability**




### 🟡 **Logs**




### 🟡 **Database Queries**




### 🟡 **Model Information**




### 🟡 **Custom Model Selection**




### 🟡 **Custom Policies**




### 🟡 **Benchmark Integration**




### 🟡 **Common Issues**




### 🟡 **Performance Issues**




### 🟡 **DynamicRegistryService**




### 🟡 **PolicyGenerator**




### 🟡 **DynamicRouter**




### 🟡 ❌ Outdated Model Lists

Hardcoded models become outdated quickly


### 🟡 ❌ Incorrect Pricing

Static prices don't reflect real-time OpenRouter pricing


### 🟡 ❌ Poor Local Model Weighting

Local models not properly weighted for different use cases


### 🟡 ❌ No Dynamic Selection

Policies can't adapt to model availability changes


### 🟡 `OpenRouterClient`

Fetches real-time model data and pricing


### 🟡 `PolicyGenerator`

Generates dynamic policies based on database queries


### 🟡 `DynamicRegistryService`

Main service for model selection and management


### 🟡 `DynamicRouter`

Integration layer with existing KRouter system


### 🟡 Database Connection Failed

```bash


### 🟡 OpenRouter API Errors

```bash


### 🟡 No Models Available

```bash


### 🟡 Slow Queries

- Check database indexes


### 🟠 High Memory Usage

- Reduce sync frequency


### 🟡 Backup existing configuration

2. **Run migration script**


### 🟡 Update routing service imports

4. **Test with existing requests**


### 🟡 Monitor performance and adjust

## 📝 **Contributing**


### 🟡 Scraper (`src/components/scraper.py`)




### 🟡 Parser (`src/components/parser.py`)




### 🟡 Formatter (`src/components/formatter.py`)




### 🟡 Config (`src/components/config.py`)




### 🟡 Logger (`src/components/logger.py`)




### 🟡 `agentapi server`




### 🟡 `agentapi attach`




### 🟡 Splitting terminal output into messages




### 🟡 Removing TUI elements from agent messages




### 🟡 What will happen when Claude Code, Goose, Aider, or Codex update their TUI?




### 🟡 Supported models




### 🟡 Cursor Agent CLI support

via local subprocess invocation


### 🟡 Koosha Paridehpour

- Fork maintainer and contributor


### 🟡 Luis Pater

- Original author


### 🟡 Router-For.ME

- Project maintainer


### 🟡 Z.ai

- Supporting the project with their GLM CODING PLAN


### 🟡 Auggie CLI Automated Setup




### 🟡 Cursor Agent Setup




### 🟡 Additional Documentation




### 🟡 [vibeproxy](https://github.com/automazeio/vibeproxy)




### 🟡 [Subtitle Translator](https://github.com/VjayC/SRT-Subtitle-Translator-Validator)




### 🟡 Fork Maintainer




### 🟡 Original Authors




### 🟡 Original Sponsors




### 🟡 [Unified Interface](https://docs.getbifrost.ai/features/unified-interface)

- Single OpenAI-compatible API for all providers


### 🟡 [Multi-Provider Support](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration)

- OpenAI, Anthropic, AWS Bedrock, Google Vertex, Azure, Cerebras, Cohere, Mistral, Ollama, Groq, and more


### 🟡 [Automatic Fallbacks](https://docs.getbifrost.ai/features/fallbacks)

- Seamless failover between providers and models with zero downtime


### 🟡 [Load Balancing](https://docs.getbifrost.ai/features/fallbacks)

- Intelligent request distribution across multiple API keys and providers


### 🟡 [Model Context Protocol (MCP)](https://docs.getbifrost.ai/features/mcp)

- Enable AI models to use external tools (filesystem, web search, databases)


### 🟡 [Semantic Caching](https://docs.getbifrost.ai/features/semantic-caching)

- Intelligent response caching based on semantic similarity to reduce costs and latency


### 🟡 [Multimodal Support](https://docs.getbifrost.ai/quickstart/gateway/streaming)

- Support for text,images, audio, and streaming, all behind a common interface.


### 🟡 [Custom Plugins](https://docs.getbifrost.ai/enterprise/custom-plugins)

- Extensible middleware architecture for analytics, monitoring, and custom logic


### 🟡 [Governance](https://docs.getbifrost.ai/features/governance)

- Usage tracking, rate limiting, and fine-grained access control


### 🟡 [Budget Management](https://docs.getbifrost.ai/features/governance)

- Hierarchical cost control with virtual keys, teams, and customer budgets


### 🟡 [SSO Integration](https://docs.getbifrost.ai/features/sso-with-google-github)

- Google and GitHub authentication support


### 🟡 [Observability](https://docs.getbifrost.ai/features/observability)

- Native Prometheus metrics, distributed tracing, and comprehensive logging


### 🟡 [Vault Support](https://docs.getbifrost.ai/enterprise/vault-support)

- Secure API key management with HashiCorp Vault integration


### 🟡 [Zero-Config Startup](https://docs.getbifrost.ai/quickstart/gateway/setting-up)

- Start immediately with dynamic provider configuration


### 🟡 [Drop-in Replacement](https://docs.getbifrost.ai/features/drop-in-replacement)

- Replace OpenAI/Anthropic/GenAI APIs with one line of code


### 🟡 [SDK Integrations](https://docs.getbifrost.ai/integrations/what-is-an-integration)

- Native support for popular AI SDKs with zero code changes


### 🟡 [Configuration Flexibility](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration)

- Web UI, API-driven, or file-based configuration options


### 🟡 Perfect Success Rate

- 100% request success rate even at 5k RPS


### 🟡 Minimal Overhead

- Less than 15 µs additional latency per request


### 🟡 Efficient Queuing

- Sub-microsecond average wait times


### 🟡 Fast Key Selection

- ~10 ns to pick weighted API keys


### 🟡 Core Infrastructure




### 🟡 Advanced Features




### 🟡 Enterprise & Security




### 🟡 Developer Experience




### 🟡 1. Gateway (HTTP API)




### 🟡 2. Go SDK




### 🟡 3. Drop-in Replacement




### 🟡 Quick Start




### 🟡 Features




### 🟡 Integrations




### 🟡 Enterprise




### 🟡 Apple's [CodeAct](https://machinelearning.apple.com/research/codeact)

"Your LLM Agent Acts Better when Generating Code."


### 🟡 Anthropic's [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

"Building more efficient agents."


### 🟡 Cloudflare's [Code Mode](https://blog.cloudflare.com/code-mode/)

"LLMs are better at writing code to call MCP, than at calling MCP directly."


### 🟡 Docker's [Dynamic MCPs](https://www.docker.com/blog/dynamic-mcps-stop-hardcoding-your-agents-world/)

"Stop Hardcoding Your Agents’ World."


### 🟡 Docker MCP Gateway

Manages containers beautifully, but still streams **all tool schemas** into Claude's context. No token optimization.


### 🟡 Cloudflare Code Mode

V8 isolates are fast, but you **can't proxy your existing MCP servers** (Serena, Wolfram, custom tools). Platform lock-in.


### 🟡 Academic Papers

Describe Anthropic's discovery pattern, but provide **no hardened implementation**.


### 🟡 Proofs of Concept

Skip security (no rootless), skip persistence (cold starts), skip proxying edge cases.


### 🟡 Constant 200-token overhead

regardless of server count


### 🟡 Proxy any stdio MCP server

into rootless containers


### 🟡 Fuzzy search across servers

without preloading schemas


### 🟡 Production-hardened

with capability dropping and security isolation


### 🟡 Ad-Hoc Tools

Need a script to scrape a site or parse a file? Just write it and run it. No need to deploy a new MCP server.


### 🟡 Composability

Pipe outputs between commands, save intermediate results to files, and use standard Unix tools.


### 🟡 Safety

Unlike giving an agent raw shell access to your machine, this server runs everything in a secure, rootless container. You get the power of "Bash/Code" without the risk.


### 🟡 Lazy Runtime Detection

Starts up instantly even if Podman/Docker isn't ready. Checks for runtime only when code execution is requested.


### 🟡 Self-Reference Prevention

Automatically detects and skips configurations that would launch the bridge recursively.


### 🟡 Noise Filtering

Ignores benign JSON parse errors (like blank lines) from chatty MCP clients.


### 🟡 Smart Volume Sharing

Probes Podman VMs to ensure volume sharing works, even on older versions.


### 🟡 Rootless containers

- No privileged helpers required


### 🟡 Network isolation

- No network access


### 🟡 Read-only filesystem

- Immutable root


### 🟡 Dropped capabilities

- No system access


### 🟡 Unprivileged user

- Runs as UID 65534


### 🟡 Resource limits

- Memory, PIDs, CPU, time


### 🟡 Auto-cleanup

- Temporary IPC directories


### 🟡 Persistent clients

- MCP servers stay warm


### 🟡 Context efficiency

- 95%+ reduction vs traditional MCP


### 🟡 Async execution

- Proper resource management


### 🟡 Single tool

- Only `run_python` in Claude's context


### 🟡 Multiple access patterns

```python


### 🟡 Top-level await

- Modern Python patterns


### 🟡 Type-safe

- Proper signatures and docs


### 🟡 Compact responses

- Plain-text output by default with optional TOON blocks when requested


### 🟡 Default (compact)

– responses render as plain text plus a minimal `structuredContent` payload containing only non-empty fields. `stdout`/`stderr` lines stay intact, so prompts remain lean without sacrificing content.


### 🟡 Optional TOON

– set `MCP_BRIDGE_OUTPUT_MODE=toon` to emit [Token-Oriented Object Notation](https://github.com/toon-format/toon) blocks. We still drop empty fields and mirror the same structure in `structuredContent`; TOON is handy when you want deterministic tokenisation for downstream prompts.


### 🟡 Fallback JSON

– if the TOON encoder is unavailable we automatically fall back to pretty JSON blocks while preserving the trimmed payload.


### 🟡 README.md

- This file, quick start


### 🟡 [GUIDE.md](GUIDE.md)

- Comprehensive user guide


### 🟡 [ARCHITECTURE.md](ARCHITECTURE.md)

- Technical deep dive


### 🟡 [HISTORY.md](HISTORY.md)

- Evolution and lessons


### 🟡 [STATUS.md](STATUS.md)

- Current state and roadmap


### 🟡 Why This vs. JS "Code Mode"?




### 🟡 The Pain: MCP Token Bankruptcy




### 🟡 Why Existing "Solutions" Fail




### 🟡 The Fix: Discovery-First Architecture




### 🟡 Architecture: How It Differs




### 🟡 Comparison At A Glance




### 🟡 Vs. Dynamic Toolsets (Speakeasy)




### 🟡 Vs. OneMCP (Gentoro)




### 🟡 Unique Features




### 🟡 Who This Helps




### 🟡 Philosophy: The "No-MCP" Approach




### 🟡 🛡️ Robustness & Reliability




### 🟡 🔒 Security First




### 🟡 ⚡ Performance




### 🟡 🔧 Developer Experience




### 🟡 Response Formats




### 🟡 Discovery Workflow




### 🟡 1. Prerequisites (macOS or Linux)




### 🟡 2. Install Dependencies




### 🟡 3. Launch Bridge




### 🟡 4. Register with Your Agent




### 🟡 5. Execute Code




### 🟡 Load Servers Explicitly




### 🟡 Zero-Context Discovery




### 🟡 Environment Variables




### 🟡 Server Discovery




### 🟡 Docker MCP Gateway Integration




### 🟡 State Directory & Volume Sharing




### 🟡 File Processing




### 🟡 Data Pipeline




### 🟡 Multi-System Workflow




### 🟡 Inspect Available Servers




### 🟡 Container Constraints




### 🟡 Capabilities Matrix




### 🟡 External




### 🟡 ✅ Implemented




### 🟡 🔄 In Progress




### 🟡 📋 Roadmap




### 🟡 Search

"Find tools for GitHub issues"


### 🟡 Describe

"Get schema for `create_issue`"


### 🟡 Execute

"Call `create_issue`"


### 🟡 Code

"Import `mcp_github`, search for 'issues', and create one if missing."


### 🟡 Two-stage discovery

– `discovered_servers()` reveals what exists; `query_tool_docs(name)` loads only the schemas you need.


### 🟡 Fuzzy search across servers

– let the model find tools without memorising catalog names:


### 🟡 Zero-copy proxying

– every tool call stays within the sandbox, mirrored over stdio with strict timeouts.


### 🟡 Rootless by default

– Podman/Docker containers run with `--cap-drop=ALL`, read-only root, no-new-privileges, and explicit memory/PID caps.


### 🟡 Compact + TOON output

– minimal plain-text responses for most runs, with deterministic TOON blocks available via `MCP_BRIDGE_OUTPUT_MODE=toon`.


### 🟡 build

- Default, full access agent for development work


### 🟡 plan

- Read-only agent for analysis and code exploration


### 🟡 Installation




### 🟡 Agents




### 🟡 Documentation




### 🟡 Contributing




### 🟡 Building on OpenCode




### 🟡 FAQ




### 🟡 6 Major Reasoning Datasets

MMLU-Pro, ARC, GPQA, TruthfulQA, CommonsenseQA, HellaSwag


### 🟡 Router vs vLLM Comparison

Side-by-side performance evaluation


### 🟡 Multiple Evaluation Modes

NR (neutral), XC (explicit CoT), NR_REASONING (auto-reasoning)


### 🟡 Research-Ready Output

CSV files and publication-quality plots


### 🟡 Dataset-Agnostic Architecture

Easy to extend with new datasets


### 🟡 CLI Tools

Simple command-line interface for common operations


### 🟡 CSV Files

Detailed per-question results and aggregated metrics


### 🟡 Master CSV

Combined results across all test runs


### 🟡 Plots

Accuracy and token usage comparisons


### 🟡 Summary Reports

Markdown reports with key findings


### 🟡 Documentation

https://vllm-semantic-router.com


### 🟡 GitHub

https://github.com/vllm-project/semantic-router


### 🟡 Issues

https://github.com/vllm-project/semantic-router/issues


### 🟡 PyPI

https://pypi.org/project/vllm-semantic-router-bench/


### 🟡 GitHub Issues

Bug reports and feature requests


### 🟡 Documentation

Comprehensive guides and API reference


### 🟡 Community

Join our discussions and get help from other users


### 🟡 Installation




### 🟡 Basic Usage




### 🟡 Python API




### 🟡 Custom Evaluation Script




### 🟡 Plotting Results




### 🟡 Example Output Structure




### 🟡 Local Installation




### 🟡 Adding New Datasets




### 🟡 Dependencies




### 🟡 Common Contributions




### 🟡 Dark theme by default

with neon blue/green accents


### 🟡 Glassmorphism effects

with backdrop blur and transparency


### 🟡 Gradient backgrounds

and animated hover effects


### 🟡 Responsive design

optimized for all devices


### 🟡 Mermaid diagram support

with dark theme optimization


### 🟡 Advanced code highlighting

with multiple language support


### 🟡 Interactive navigation

with smooth animations


### 🟡 Search functionality

(ready for Algolia integration)


### 🟡 Fast loading

with optimized builds


### 🟡 Accessible design

following WCAG guidelines


### 🟡 Mobile-first

responsive layout


### 🟡 SEO optimized

with proper meta tags


### 🟡 Live Preview

http://localhost:3000 (when running)


### 🟡 Docusaurus Docs

https://docusaurus.io/docs


### 🟡 Main Project

../README.md


### 🟡 Prerequisites




### 🟡 Development




### 🟡 Production Build




### 🟡 Preview Production Build




### 🟡 ✨ Modern Tech-Inspired Design




### 🟡 🔧 Enhanced Functionality




### 🟡 📱 User Experience




### 🟡 Themes and Colors




### 🟡 Navigation




### 🟡 Site Configuration




### 🟡 00-client-request-test.py

✅ - Complete client request validation and smart routing


### 🟡 01-envoy-extproc-test.py

✅ - Envoy ExtProc interaction and processing tests


### 🟡 02-router-classification-test.py

✅ - Router classification and model selection tests


### 🟡 03-classification-api-test.py

✅ - Standalone Classification API service tests


### 🟡 Development Workflow (LLM Katan - Recommended)




### 🟡 Future: Production Testing (Real vLLM)




### 🟡 00-client-request-test.py

- Basic client request tests ✅


### 🟡 01-envoy-extproc-test.py

- Envoy ExtProc interaction tests ✅


### 🟡 02-router-classification-test.py

- Router classification tests ✅


### 🟡 03-classification-api-test.py

- Classification API tests ✅


### 🟡 04-model-routing-test.py

- TBD (To Be Developed)


### 🟡 04-cache-test.py

- TBD (To Be Developed)


### 🟡 05-e2e-category-test.py

- TBD (To Be Developed)


### 🟡 06-metrics-test.py

- TBD (To Be Developed)


### 🟡 React 18

with TypeScript for type safety


### 🟡 Vite 5

for fast development and optimized builds


### 🟡 React Router v6

for client-side routing


### 🟡 CSS Modules

for scoped styling with theme support (dark/light mode)


### 🟡 Landing

(`/`): Intro landing with animated terminal demo and quick links


### 🟡 Monitoring

(`/monitoring`): Grafana dashboard embedding with custom path input


### 🟡 Config

(`/config`): Real-time configuration viewer with editable panels and save support


### 🟡 Topology

(`/topology`): Visual topology of request flow and model selection using React Flow


### 🟡 Playground

(`/playground`): Open WebUI interface for testing


### 🟡 Dashboard

http://localhost:8700


### 🟡 Grafana

(direct access): http://localhost:3000 (admin/admin)


### 🟡 Prometheus

(direct access): http://localhost:9090


### 🟡 Multi-architecture support

The Dockerfile supports both AMD64 and ARM64 architectures.


### 🟡 Pre-built images

Available at `ghcr.io/vllm-project/semantic-router/dashboard` with tags for releases and latest.


### 🟡 Frontend (React + TypeScript + Vite)




### 🟡 Backend (Go HTTP Server)




### 🟡 Method 1: Start with Docker Compose (Recommended)




### 🟡 Method 2: Local Development Mode




### 🟡 Method 3: Rebuild Dashboard Only




### 🟡 Docker Compose Integration Notes




### 🟡 Dockerfile Build




### 🟡 Grafana Embedding Support




### 🟡 Health Check




### 🟡 Kubernetes deployment




### 🟡 Profiles

Define deployment environments and configurations


### 🟡 Test Cases

Reusable test logic that can be shared across profiles


### 🟡 Framework

Core infrastructure for test execution and reporting


### 🟡 ai-gateway

Tests Semantic Router with Envoy AI Gateway integration


### 🟡 aibrix

Tests Semantic Router with vLLM AIBrix integration


### 🟡 dynamic-config

Tests Semantic Router with Kubernetes CRD-based configuration (IntelligentRoute/IntelligentPool)


### 🟡 istio

Tests Semantic Router with Istio service mesh integration


### 🟡 production-stack

Tests vLLM Production Stack configurations


### 🟡 llm-d

Tests Semantic Router with LLM-D distributed inference


### 🟡 dynamo

Tests with Nvidia Dynamo (future)


### 🟡 Automatic cluster lifecycle management

Creates and cleans up Kind clusters


### 🟡 Docker image building and loading

Builds images and loads them into Kind


### 🟡 Helm deployment automation

Deploys required Helm charts


### 🟡 Automatic port forwarding cleanup

Each test case cleans up its port forwarding


### 🟡 Detailed logging

Provides comprehensive test output


### 🟡 Test reporting

Generates JSON and Markdown reports


### 🟡 Resource cleanup

Ensures proper cleanup even on failures


### 🟡 Istio-Specific Features:

- Istio sidecar injection and health


### 🟡 Semantic Router Features (through Istio):

- Chat completions API and stress testing


### 🟡 Supported Profiles




### 🟡 Basic Functionality Tests




### 🟡 Classification and Feature Tests




### 🟡 Signal-Decision Engine Tests




### 🟡 Install dependencies (optional)




### 🟡 Run all tests with default profile (ai-gateway)




### 🟡 Run specific profile




### 🟡 Run specific test cases




### 🟡 Run with custom options




### 🟡 Debug mode




### 🟡 Advanced Workflows




### 🟡 Test Reports




### 🟡 Profile vs Test Case Separation




### 🟡 Service Configuration




### 🟡 Embedding Signal Routing




### 🟡 Adding a New Test Case




### 🟡 Adding a New Profile




### 🟡 Istio Profile




### 🟡 Istio Control Plane

(`istio-system` namespace):


### 🟡 Semantic Router

(`semantic-router` namespace):


### 🟡 Istio Resources

- `Gateway` - Configures ingress gateway on port 80


### 🟡 Component Benchmarks

Fast Go benchmarks for individual components (classification, decision engine, cache)


### 🟡 E2E Performance Tests

Full-stack load testing integrated with the e2e framework


### 🟡 Profiling

pprof integration for CPU, memory, and goroutine profiling


### 🟡 Baseline Comparison

Automated regression detection against performance baselines


### 🔴 CI/CD Integration

Performance tests run on every PR with regression blocking


### 🟡 Running Benchmarks




### 🟡 Profiling




### 🟡 Baseline Comparison




### 🟡 Regression Detection




### 🟡 Classification Benchmarks




### 🟡 Decision Engine Benchmarks




### 🟡 Cache Benchmarks




### 🟡 Tracked Metrics




### 🟡 Performance Thresholds




### 🟡 Performance Test Config (`config/perf.yaml`)




### 🟡 Thresholds Config (`config/thresholds.yaml`)




### 🟡 Benchmarks fail to run




### 🟡 Models not found




### 🟠 High variance in results




### 🟠 Memory profiling shows high allocations




### 🟡 PR Opened

→ Run component benchmarks (5 min)


### 🟡 Compare Against Baseline

→ Calculate % changes


### 🟡 Post Results to PR

→ Automatic comment with metrics table


### 🟡 Block if Regression

→ Fail CI if thresholds exceeded


### 🟡 Always warm up

- Run warmup iterations before measuring


### 🟡 Report allocations

- Use `b.ReportAllocs()` to track memory


### 🟡 Reset timer

- Use `b.ResetTimer()` after setup


### 🟡 Use realistic data

- Test with production-like inputs


### 🟡 Control variance

- Use fixed seeds for random data


### 🟡 Measure what matters

- Focus on user-facing metrics


### 🟡 Worker Node

The local `${PROJECT_ROOT}/models` directory is mounted to `/mnt/models` inside the worker node container


### 🟡 PersistentVolume

Kubernetes PV uses `hostPath: /mnt/models` to access the models


### 🟡 Init Container

Checks if models exist; if not, downloads them (requires internet connection)


### 🟡 1. Generate Kind Configuration




### 🟡 2. Create Kind Cluster




### 🟡 3. Load Docker Images (for offline/local images)




### 🟡 4. Deploy Semantic Router




### 🟡 5. Verify Deployment




### 🟡 Path Auto-Detection




### 🟡 Model Mounting




### 🟡 Resource Configuration




### 🟡 Models Not Found in Pod




### 🟡 Regenerate Configuration




### 🟡 ImagePullBackOff




### 🟡 Using a Different Models Directory




### 🟡 Multiple Worker Nodes




### 🟡 Intelligent Model Selection

Automatically routes requests to the best model based on semantic understanding


### 🟡 PII Detection & Protection

Blocks or redacts sensitive information before sending to models


### 🟡 Prompt Guard

Detects and blocks jailbreak attempts


### 🟡 Semantic Caching

Reduces latency and costs through intelligent response caching


### 🟡 Category-Specific Prompts

Injects domain-specific system prompts for better results


### 🟡 Tools Auto-Selection

Automatically selects relevant tools for function calling


### 🟡 Category Classification

Train custom models at [Category Classifier Training](../../src/training/classifier_model_fine_tuning/)


### 🟡 PII Detection

Train custom models at [PII Detection Training](../../src/training/pii_model_fine_tuning/)


### 🟡 Prompt Guard

Train custom models at [Prompt Guard Training](../../src/training/prompt_guard_fine_tuning/)


### 🟡 [Category Classifier Training](../../src/training/classifier_model_fine_tuning/)

- Train custom category classification models


### 🟡 [PII Detector Training](../../src/training/pii_model_fine_tuning/)

- Train custom PII detection models


### 🟡 [Prompt Guard Training](../../src/training/prompt_guard_fine_tuning/)

- Train custom jailbreak detection models


### 🟡 [OpenShift Deployment](../openshift/)

- Deploy with standalone vLLM containers (not KServe)


### 🟡 Main Project

https://github.com/vllm-project/semantic-router


### 🟡 Full Documentation

https://vllm-semantic-router.com


### 🟡 KServe Docs

https://kserve.github.io/website/


### 🟡 Step 1: Verify InferenceService




### 🟡 Step 2: Configure Router Settings




### 🟡 Step 3: Deploy Resources




### 🟡 Step 4: Wait for Ready




### 🟡 Check Deployment Status




### 🟡 View Logs




### 🟡 Metrics




### 🟡 Pod Not Starting




### 🟡 Router Container Crashing




### 🟡 Cannot Connect to InferenceService




### 🟡 Within This Repository




### 🟡 Other Deployment Options




### 🟡 External Resources




### 🟡 OpenShift Cluster

with OpenShift AI (RHOAI) installed


### 🟡 KServe InferenceService

already deployed and running


### 🟡 OpenShift CLI (oc)

installed and logged in


### 🟡 Cluster admin or namespace admin

permissions


### 🟡 Memory

3Gi request, 6Gi limit


### 🟡 CPU

1 core request, 2 cores limit


### 🟡 Storage

10Gi for model storage


### 🟡 Prerequisites




### 🟡 One-Click Full Deployment (Recommended)




### 🟡 Minimal Deployment (Core Only)




### 🟡 Command Line Options




### 🟡 Manual Deployment (Advanced)




### 🟡 Why Binary Build?




### 🟡 Updating Dashboard




### 🟡 Get Route URLs




### 🟡 Dashboard Playground




### 🟡 Example Usage




### 🟡 Security Context




### 🟡 Networking




### 🟡 Storage




### 🟡 Check Deployment Status




### 🟡 Metrics




### 🟡 Quick Cleanup




### 🟡 Cleanup Options




### 🟡 What Gets Cleaned Up




### 🟡 Manual Cleanup




### 🟡 Common Issues




### 🟡 Resource Requirements




### 🟡 Create namespace:

```bash


### 🟡 Build llm-katan image:

```bash


### 🟡 Deploy resources:

```bash


### 🟡 Note:

You'll need to manually configure ClusterIPs in `config-openshift.yaml`


### 🟡 URL

http://localhost:3002


### 🟡 Database

MongoDB for conversation persistence


### 🟡 API Integration

Routes through Envoy proxy for OpenAI-compatible API calls


### 🟡 Configuration

- `OPENAI_BASE_URL=http://envoy-proxy:8801/v1` (routes through Envoy)


### 🟡 URL

http://localhost:9090


### 🟡 Configuration

`./addons/prometheus.yaml`


### 🟡 Data Retention

15 days


### 🟡 Storage

Persistent volume `prometheus-data`


### 🟡 URL

http://localhost:3000


### 🟡 Credentials

admin/admin


### 🟡 Configuration

- Datasources: Prometheus and Jaeger


### 🟡 URL

http://localhost:16686


### 🟡 OTLP Endpoint

http://localhost:4318 (gRPC)


### 🟡 Configuration

OTLP collector enabled


### 🟡 Integration

Semantic Router sends traces via OTLP


### 🟡 Environment Variables




### 🟡 Prometheus




### 🟡 Grafana




### 🟡 Jaeger (Distributed Tracing)




### 🟡 Prerequisites




### 🟡 Install




### 🟡 Verify Installation




### 🟡 Access the Application




### 🟡 Development Environment




### 🟡 Production Environment




### 🟡 Custom Configuration




### 🟡 Installation & Management




### 🟡 Development




### 🟡 Testing & Debugging




### 🟡 Port Forwarding




### 🟡 Rollback & Cleanup




### 🟡 Help




### 🟡 In-Place Upgrade




### 🟡 Rollback




### 🟡 Example 1: Custom Endpoints




### 🟡 Example 2: Enable Ingress




### 🟡 Example 3: Enable Auto-scaling




### 🟡 Example 4: Custom Security Context




### 🟡 Pods Stuck in Pending




### 🟡 Init Container Fails




### 🟡 Service Not Accessible




### 🟡 GitHub Actions Example




### 🟡 GitLab CI Example




### 🟡 ArgoCD Example




### 🟡 Use Version Control

Keep your `values.yaml` files in version control


### 🟡 Environment Separation

Use different namespaces and values files for different environments


### 🟡 Resource Limits

Always set appropriate resource limits based on your workload


### 🟡 Monitoring

Enable metrics and set up monitoring


### 🟡 Security

Use security contexts and network policies


### 🟡 Backups

Regularly backup your PVC data


### 🟡 Testing

Test upgrades in dev/staging before production



## 9. Architecture Overview

Architecture details to be documented.


## 10. Technical Requirements

- Use react
- Use gcp
- Use vue
- Use kubernetes
- Use docker
- Use rust
- Use javascript
- Use sql
- Use azure
- Use mysql

## 11. Integration Points

- **Integration with development**: Integration point with development project
- **Integration with Simply**: Integration point with Simply project
- **Integration with README**: Integration point with README project
- **Integration with Jupyter**: Integration point with Jupyter project
- **Integration with goals**: Integration point with goals project
- **Integration with 485**: Integration point with 485 project
- **Integration with environments**: Integration point with environments project
- **Integration with environment**: Integration point with environment project
- **Integration with officially**: Integration point with officially project
- **Integration with in**: Integration point with in project
- **Integration with semantic-router**: Integration point with semantic-router project
- **Integration with entry**: Integration point with entry project
- **Integration with build**: Integration point with build project
- **Integration with Structure**: Integration point with Structure project
- **Integration with readme**: Integration point with readme project
- **Integration with metadata**: Integration point with metadata project
- **Integration with actually**: Integration point with actually project
- **Integration with planning**: Integration point with planning project
- **Integration with -**: Integration point with - project
- **Integration with uses**: Integration point with uses project
- **Integration with now**: Integration point with now project
- **Integration with maintainer**: Integration point with maintainer project
- **Integration with navigation**: Integration point with navigation project
- **Integration with skills**: Integration point with skills project
- **Integration with well**: Integration point with well project
- **Integration with root**: Integration point with root project
- **Integration with bifrost-extensions**: Integration point with bifrost-extensions project
- **Integration with that**: Integration point with that project
- **Integration with progresses**: Integration point with progresses project
- **Integration with configuration**: Integration point with configuration project
- **Integration with lead**: Integration point with lead project
- **Integration with from**: Integration point with from project
- **Integration with ArgisGate**: Integration point with ArgisGate project
- **Integration with Overview**: Integration point with Overview project
- **Integration with This**: Integration point with This project
- **Integration with overview**: Integration point with overview project
- **Integration with manifest**: Integration point with manifest project
- **Integration with vllm-semantic-router-bench**: Integration point with vllm-semantic-router-bench project
- **Integration with has**: Integration point with has project
- **Integration with is**: Integration point with is project
- **Integration with name**: Integration point with name project
- **Integration with setup**: Integration point with setup project
- **Integration with context**: Integration point with context project
- **Integration with Management**: Integration point with Management project
- **Integration with already**: Integration point with already project
- **Integration with includes**: Integration point with includes project
- **Integration with structure**: Integration point with structure project
- **Integration with or**: Integration point with or project
- **Integration with cd**: Integration point with cd project
- **Integration with summary**: Integration point with summary project
- **Integration with production-stack**: Integration point with production-stack project
- **Integration with Status**: Integration point with Status project
- **Integration with lifecycle**: Integration point with lifecycle project
- **Integration with Managers**: Integration point with Managers project
- **Integration with Documentation**: Integration point with Documentation project
- **Integration with architecture**: Integration point with architecture project
- **Integration with ArgisHub**: Integration point with ArgisHub project
- **Integration with while**: Integration point with while project
- **Integration with Constraints**: Integration point with Constraints project
- **Integration with scope**: Integration point with scope project
- **Integration with based**: Integration point with based project
- **Integration with CLIs**: Integration point with CLIs project
- **Integration with documentation**: Integration point with documentation project
- **Integration with templates**: Integration point with templates project
- **Integration with argis**: Integration point with argis project
- **Integration with status**: Integration point with status project
- **Integration with docs**: Integration point with docs project
- **Integration with Hooks**: Integration point with Hooks project
- **Integration with by**: Integration point with by project
- **Integration with session**: Integration point with session project
- **Integration with freeact**: Integration point with freeact project
- **Integration with license**: Integration point with license project
- **Integration with with**: Integration point with with project
- **Integration with are**: Integration point with are project
- **Integration with at**: Integration point with at project
- **Integration with health**: Integration point with health project
- **Integration with directory**: Integration point with directory project

## 12. Timeline & Phases

### Phase 1: min: Create and merge PR

### Q: What's the priority order for implementation?

**A:** Recommended priority:
1. **Phase 1 (High):** Remove empty dirs, improve .gitignore
2. **Phase 2 (Medium):** Consolidate configuration files
3. **Phase 3 (Low):** Archive and reorganize documentation

### Q: Who should implement these changes?

**A:** Recommended roles:
- DevOps/Infrastructure owner: Phase 1-2 (config consolidation)
- Technical lead: Approval and oversight
- Documentation owner: Phase 3 (doc organization)

### Q: Are

### Phase 2: min: Test locally




## 13. Milestones


## 14. Dependencies


## 16. Related Projects

- development
- Simply
- README
- Jupyter
- goals
- 485
- environments
- environment
- officially
- in
- semantic-router
- entry
- build
- Structure
- readme
- metadata
- actually
- planning
- -
- uses
- now
- maintainer
- navigation
- skills
- well
- root
- bifrost-extensions
- that
- progresses
- configuration
- lead
- from
- ArgisGate
- Overview
- This
- overview
- manifest
- vllm-semantic-router-bench
- has
- is
- name
- setup
- context
- Management
- already
- includes
- structure
- or
- cd
- summary
- production-stack
- Status
- lifecycle
- Managers
- Documentation
- architecture
- ArgisHub
- while
- Constraints
- scope
- based
- CLIs
- documentation
- templates
- argis
- status
- docs
- Hooks
- by
- session
- freeact
- license
- with
- are
- at
- health
- directory

## 17. Shared Features

- Caching
- Key Capabilities
- Core Components
- Common Issues
- Debug Mode
- Validation
- Installation
- Install Dev Dependencies
- Run Tests
- Code Style
- Test Coverage
- Cleanup
- Status
- Audit Logging
- Rate Limiting
- Health Checks
- Metrics
- Logging
- Health Monitoring
- GraphQL API
- WebSocket Support
- Prometheus Metrics
- Advanced Analytics
- Documentation
- Issues
- Discussions
- Data Flow
- 2. Environment Variables
- Monitoring
- Production Deployment
- Docker Deployment
- Kubernetes Deployment
- Advanced Features
- Pull Request Process
- Build for production:
- Session Management:
- Security:
- Performance:
- Intelligent Routing
- Cost Savings
- Speed
- Reliability
- Tool Integration
- Multi-LLM Support
- Type
- Features
- Providers
- Docs
- Testing
- Async
- API
- Platform
- Python
- Go
- Rust
- File Size
- GitHub Issues
- Discord Community
- Email Support
- Office Hours
- What is Argis?
- Key Benefits
- Prerequisites
- Installation (5 minutes)
- Verify Setup (Optional but Recommended)
- First Request (30 seconds)
- 4-Tier Architecture Diagram
- Data Flow: Request Processing
- 10+ Sub-Projects Overview
- Component Details
- Semantic Caching
- Tool Discovery
- State Management
- 1. Environment Setup
- 2. Python Services (ArgisExec, ArgisGate)
- 3. Go Services (ArgisRoute, ArgisHub)
- 4. Rust Library (ArgisCores)
- 5. Dashboard & Wizard
- Request Processing Pipeline
- State Hierarchy Flow
- Service Configuration Files
- Monitoring Dashboards
- Metrics Available
- OpenAI-Compatible Endpoints
- GraphQL API (Advanced)
- Setting Up Development Environment
- Testing Strategy
- Contribution Workflow
- Code Standards
- Debug Commands
- Development Roadmap
- Getting Help
- Quick Links
- License
- Acknowledgments
- Fork
- Create
- Make
- Test
- Commit
- Push
- Latency:
- Input:
- High-Level Flow
- Database
- 1. Install Dependencies
- Basic Usage
- For Performance Issues
- Examples
- Overview
- AI Integration
- Backward Compatibility
- Python API
- Update References
- Dependencies
- Enterprise
- GitHub
- Success Rate
- Key Features
- ✅ Workspace Management
- Debugging
- Resource Limits
- Cost Tracking
- infrastructure
- GitHub Actions Example
- Theme Support
- Constructor
- External
- Quality
- Impact
- Key Metrics
- Example
- Dashboard
- Best Practices
- Learning
- CI/CD Integration
- Email
- Slack
- Architecture
- Coverage
- Review
- Verify
- Root Cause
- Error Handling
- Configuration
- Understand the architecture
- Community:
- README.md
- Update
- Purpose
- Logs
- CLI Tools
- Compatibility
- Structured Logging
- React Router
- Local
- ✅ Advantages
- View Logs
- Check Health
- Phase 1
- Immediate
- KV storage
- Development
- Run Migration
- PostgreSQL
- Grafana
- observability
- No performance impact
- Development Workflow
- ✅ Implemented
- 📋 Recommended
- Docker
- Quick Start
- Problem
- Solution
- Pydantic AI
- Reference
- Entry Point
- 3. Service Configuration
- Rollback
- Port already in use
- Operations
- Node.js
- Custom Configuration
- 🛡️ Production-hardened
- Memory usage
- Usage Example
- Single Source of Truth
- Code Quality
- Approach:
- Tools
- Size:
- Use version control
- Cause:
- 4.3 Authentication
- 6.3 Maintainability
- Common Commands
- Developer Experience
- 📊 Expected Impact
- 2. Schema Validation ✅
- For deployment
- Type Safety
- 22 tests passing
- 7. Infrastructure & Configuration
- URL:
- Local Development
- Maintenance
- How It Works
- Review documentation
- Code
- Production Environment
- Build
- API Reference
- 📚 Getting Started
- Agent Management
- Alert System
- SLA Tracking
- Authentication & Authorization
- Kubernetes Probes
- Webhooks
- System
- Redis
- Prometheus
- OpenTelemetry
- 4. Anomaly Detection
- 7. Notification Channels
- Health & Status
- Metrics & Performance
- Alerts & Monitoring
- SLA & Compliance
- Loading Configuration
- Test Categories
- Kubernetes
- Production Checklist
- Performance Targets
- Memory
- Directory Structure
- Type System
- API Integration
- 🎨 Custom Dashboard Widgets
- 👥 RBAC (Role-Based Access Control)
- ⚡ Performance Optimized
- TypeScript
- React
- Implementation Details
- Phase 2 Summary
- Main README
- Website
- Core Capabilities
- Setup
- Request Batching
- Request Deduplication
- Test Structure
- Code Organization
- Security Features
- Quick References
- Performance Problems
- Accessibility
- Research/references
- Start here:
- Service code:
- Infrastructure code:
- Session tracking:
- Recommendation:
- Options:
- Note:
- Consolidation
- Navigation
- Full Report:
- Guides:
- "How do I get started?"
- New Contributor
- Feature Developer
- DevOps/Operations
- Agent/Automation
- Analysis:
- File locations:
- 1. FINAL_ORGANIZATION_REPORT.md (20 KB)
- 2. ORGANIZATION_QUICK_GUIDE.md (7.4 KB)
- 3. DOCUMENTATION_INDEX.md (2.4 KB)
- Repository Composition
- atoms
- Intelligent Model Routing
- Agent Framework
- Cost Optimization
- Enterprise Security
- Search
- Product Specifications
- Code Examples
- Last Updated
- Theme
- Research & Analysis
- Research
- DevOps Engineer
- Pattern matching
- Semantic search
- Cursor
- Windsurf
- Claude Code
- Dashboards
- Design Philosophy
- Use Cases
- Capabilities
- Workflow Integration
- GitHub Actions Integration
- Real-World Examples
- What is MCP?
- Community Resources
- Slash commands
- MCP servers
- Hooks
- Current Size:
- Justification:
- Risk Level:
- Immediate Actions (This Week)
- Short-term (2-4 weeks)
- Phase 1 Risk Matrix
- Key Resources
- Phase 1 Execution
- Execute Phase 1
- Responsibility
- Exposes
- Consumes
- Primary Role
- Intended Use
- Empty
- Has Hidden Files
- Referenced In
- Should Keep
- Final Report
- Immediate Actions
- OpenAI-Compatible API
- Cost
- Rate Limits
- Token counting
- Multi-tenancy
- Tracing
- System Design
- Embeddings
- Gap
- Framework
- Used By
- `server.py`
- Zero Startup Latency
- RequestDirector
- Pre-calculated Schemas
- Single Code Path
- No Fallbacks
- Performance First
- openapi-core Integration
- Full Feature Support
- Automatic Suffixing
- Transparent
- Native Support
- Explode Handling
- Complex Objects
- Status Code Mapping
- Structured Responses
- Timeout Handling
- Parameter Validation
- Graceful Degradation
- Connection Pooling
- Client Caching
- Async Support
- Parameter Mapping
- Zero Latency
- Same Interface
- Performance Improvement
- No Breaking Changes
- RequestDirector Initialization
- Schema Pre-calculation
- Request Building
- Key Architecture Principles
- RequestDirector-Based Components
- `FastMCPOpenAPI` Class
- Component Creation Logic
- Stateless Request Building
- 1. Enhanced Parameter Handling
- 2. Robust Error Handling
- 3. Performance Optimizations
- Server Options
- Route Mapping Customization
- Testing Philosophy
- Example Test Pattern
- From Legacy Implementation
- Key Log Messages
- Debugging Common Issues
- Planned Features
- Performance Improvements
- `components.py`
- `routing.py`
- Spec Parsing
- RequestDirector Setup
- Component Creation
- Request Execution
- Response Processing
- Real Integration
- Minimal Mocking
- Behavioral Focus
- Performance Focus
- Eliminated Startup Latency
- Better OpenAPI Compliance
- Serverless Friendly
- Simplified Architecture
- Enhanced Reliability
- RequestDirector Initialization Fails
- Parameter Issues
- Advanced Caching
- Streaming Support
- Batch Operations
- Enhanced Monitoring
- Configuration Management
- Enhanced Schema Caching
- Parallel Processing
- Memory Optimization
- Request Optimization
- Zero Runtime Overhead
- No Code Generation
- Minimal Dependencies
- Parameter Collisions
- DeepObject Style
- Complex Schemas
- Pre-calculated Mapping
- Collision-aware
- Real Objects
- Behavioral Testing
- Initialization Process
- Request Processing
- 1. High-Performance Request Building
- 2. Comprehensive Parameter Support
- 3. Enhanced Error Handling
- 4. Advanced Schema Processing
- RequestDirector Integration
- Basic Server Setup
- Direct RequestDirector Usage
- `director.py`
- `parser.py`
- `schemas.py`
- `models.py`
- `formatters.py`
- Parsing
- Pre-calculation
- Director Setup
- Tool Invocation
- Parameter Handling
- `OpenAPITool`
- `OpenAPIResource`
- `OpenAPIResourceTemplate`
- `FastMCPOpenAPI`
- Core Functionality
- OpenAPI Features
- Response Streaming
- Enhanced Authentication
- Advanced Metrics
- Schema Caching
- Connection Optimization
- Parameter Mapping Issues
- Request Building Errors
- Drop-in replacement
- Unit Test Example
- Integration Test Example
- Cost Comparison
- Model Routing
- Cost Reduction:
- Latency (p95):
- Fallback Rate:
- OpenRouter
- [KROUTE.md](./KROUTE.md)
- [PLAN.md](./PLAN.md)
- 4. Use
- Usage
- Usage Analytics
- Minimum:
- Language:
- Encoding:
- Format:
- GPU:
- CUDA:
- PyTorch:
- FAST
- Immutability
- Composition
- Serialization
- Extensibility
- Performance Dashboard:
- Tech Lead:
- DevOps Team:
- For Developers
- For DevOps
- ✅ Automated Testing
- 📢 Notifications
- Planned Enhancements
- Resources
- `models`
- `benchmarks`
- **Database Schema**
- **Key Components**
- **Database Queries**
- **DynamicRegistryService**
- **PolicyGenerator**
- **DynamicRouter**
- Core Infrastructure
- 2. Go SDK
- Integrations
- Fuzzy search across servers
- Safety
- Async execution
- Type-safe
- 🔒 Security First
- Data Pipeline
- 🔄 In Progress
- 📋 Roadmap
- Execute
- plan
- Agents
- Contributing
- Responsive design
- Interactive navigation
- Search functionality
- Main Project
- 📱 User Experience
- 00-client-request-test.py
- 01-envoy-extproc-test.py
- 02-router-classification-test.py
- 03-classification-api-test.py
- Vite 5
- Profiles
- Resource cleanup
- Semantic Router
- E2E Performance Tests
- Profiling
- Baseline Comparison
- Regression Detection
- Tracked Metrics
- Performance Thresholds
- PR Opened
- 5. Verify Deployment
- Prompt Guard
- Full Documentation
- Check Deployment Status
- External Resources
- CPU
- Networking
- Resource Requirements
- Install
- Verify Installation
- Help
````
