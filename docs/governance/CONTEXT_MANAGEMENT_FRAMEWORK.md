# Ante Context Management Framework

## Table of Contents

1. [Overview](#overview)
2. [Context Architecture](#context-architecture)
3. [Context Types & Lifecycle](#context-types--lifecycle)
4. [Versioning & Preservation](#versioning--preservation)
5. [Integration with Agent Systems](#integration-with-agent-systems)
6. [Relevance & Freshness Policies](#relevance--freshness-policies)
7. [Storage & Retrieval](#storage--retrieval)
8. [Performance & Optimization](#performance--optimization)
9. [Context Updates & Synchronization](#context-updates--synchronization)
10. [Monitoring & Metrics](#monitoring--metrics)

---

## Overview

### Purpose

The Context Management Framework ensures LLMs and agents have access to accurate, current, relevant documentation and context about the Ante system. This framework manages the lifecycle of context from creation through archival.

### Context Principles

- **Accuracy**: All context must be verified as current and correct
- **Completeness**: Context includes all necessary information for effective use
- **Efficiency**: Context optimized for LLM processing without noise
- **Versioning**: Context tied to specific Ante versions
- **Traceability**: Source and currency of all context documented

### Context Consumers

- **Claude & Other LLMs**: Via llms.txt and API feeds
- **Ante Agents**: Via context injection during execution
- **Documentation Systems**: Via context database
- **Search Systems**: Via indexed context
- **Users**: Via documentation portal

---

## Context Architecture

### Context Hierarchy

```
┌─ Core Context (Always Included)
│  ├─ System Overview
│  ├─ Architecture Fundamentals
│  ├─ Core Concepts & Terminology
│  └─ Getting Started
│
├─ API Context
│  ├─ Public API Reference
│  ├─ Function Signatures
│  ├─ Type Definitions
│  └─ Common Patterns
│
├─ Feature Context
│  ├─ Feature-Specific APIs
│  ├─ How-To Guides
│  ├─ Examples & Use Cases
│  └─ Configuration Options
│
├─ Advanced Context (Optional)
│  ├─ Architecture Deep Dives
│  ├─ Performance Tuning
│  ├─ Troubleshooting Guides
│  └─ Design Patterns
│
└─ Auxiliary Context
   ├─ Known Issues & Limitations
   ├─ Deprecation Notices
   ├─ Migration Guides
   └─ FAQ & Common Questions
```

### Context Layers

#### Layer 1: Minimal Context (10-20 KB)

For quick reference and API summaries:

```
- Feature matrix (what Ante can do)
- Core API list with signatures
- Getting started checklist
- FAQ quick answers
```

**Usage**: Initial context for task planning

#### Layer 2: Standard Context (100-200 KB)

For typical development tasks:

```
- Core documentation
- Common APIs with examples
- Basic how-to guides
- Common use cases
- Known limitations
```

**Usage**: Standard agent context, initial LLM context

#### Layer 3: Comprehensive Context (500-1000 KB)

For complex tasks and deep understanding:

```
- All public APIs
- All guides and how-tos
- Architecture documentation
- Advanced patterns
- Complete examples
- Troubleshooting guides
```

**Usage**: Complex agents, full-context LLM interactions

#### Layer 4: Extended Context (1000+ KB)

For research and specialized work:

```
- Comprehensive documentation
- Design documents
- Implementation details
- Historical context
- Design decisions
- Performance data
```

**Usage**: Deep research, architecture work, optimization

### Context Metadata

Every context package includes:

```yaml
metadata:
  version: "1.2.3"              # Ante version
  release_date: "2026-02-20"
  context_version: "1.0.0"      # Framework version
  generated_date: "2026-02-20"
  expiry_date: "2026-03-20"     # Typically 30 days
  size_bytes: 524288
  checksum: "sha256:..."
  
coverage:
  apis:
    public: 100
    experimental: 5
    documented: 105
  
features:
    documented: 23
    total: 25
    coverage: 92%
  
quality:
    broken_links: 0
    tested_examples: 98%
    last_audit: "2026-02-20"
```

---

## Context Types & Lifecycle

### Context Type Categories

#### 1. Static Context

Information that changes infrequently (usually per release):

- Architecture overview
- Core concepts
- API reference
- Configuration options
- Feature capabilities matrix

**Update Frequency**: On release (typically quarterly)  
**Validation**: Full audit  
**Archival**: Keep previous 4 versions

#### 2. Dynamic Context

Information that changes frequently during development:

- Known issues and bugs
- Performance metrics
- Deprecation notices
- In-progress features
- Community activity

**Update Frequency**: Weekly or as needed  
**Validation**: Spot checks  
**Archival**: Keep current + previous 4 weeks

#### 3. Operational Context

Real-time information about Ante state:

- Current service status
- Active issues
- Performance indicators
- Usage statistics
- Change notifications

**Update Frequency**: Real-time (polls every 1-5 minutes)  
**Validation**: Automated validation  
**Retention**: Current only + last 30 days

#### 4. Agent-Specific Context

Context customized for specific agents or use cases:

- Restricted API access (based on permissions)
- Task-specific examples
- Custom system prompts
- Filtered guides (by skill level)
- Performance tuning parameters

**Update Frequency**: Per deployment  
**Validation**: Role-based access control  
**Archival**: With agent version

### Lifecycle Stages

#### Stage 1: Creation (T-0 days)

**Trigger**: New documentation or feature

**Process**:
1. Documentation authored and reviewed
2. Content quality verified
3. Examples tested
4. Context entry created
5. Metadata added
6. Indexed for search
7. Marked "ready for inclusion"

**Owner**: Documentation team

#### Stage 2: Integration (T-1 days)

**Trigger**: Context bundle generation

**Process**:
1. Select context appropriate for layers
2. Format for LLM consumption
3. Add context-specific metadata
4. Compress if needed
5. Validate completeness
6. Sign for integrity

**Owner**: Context coordinator

#### Stage 3: Distribution (T-0 hours)

**Trigger**: Release or scheduled update

**Process**:
1. Deploy to documentation site
2. Publish llms.txt
3. Update API feeds
4. Notify consumers
5. Monitor adoption
6. Track usage metrics

**Owner**: Operations team

#### Stage 4: Maintenance (T+1 to T+30 days)

**Trigger**: Ongoing access and usage

**Process**:
1. Monitor for issues
2. Collect feedback
3. Fix errors discovered
4. Update metrics
5. Track freshness
6. Note any clarifications

**Owner**: Documentation team

#### Stage 5: Archival (T+6 months to T+3 years)

**Trigger**: Context superseded or deprecated

**Process**:
1. Mark as deprecated (3-6 months before)
2. Link to replacement context
3. Move to archive storage
4. Maintain accessibility
5. Eventually delete per retention policy

**Owner**: Documentation lead

---

## Versioning & Preservation

### Version Alignment

Context versions align with Ante release versions:

```
Ante Version: 1.2.3
  ↓
Context Version: 1.2.3-context.1
                 └─ "context" indicates documentation set
                    "1" indicates patch to context
```

### Breaking Changes & Migration

When Ante makes breaking changes:

```markdown
# Breaking Change: Context Version 1.2.3

## What Changed
[Description of change]

## Migration Path
[How to update to new pattern]

## Temporary Support
Context from 1.1.x still available in archive.
Migration guide: [link]

## Deprecation Timeline
- 1.2.3: Warning in context
- 1.3.0: Deprecation notice
- 1.4.0: Removed from standard context
```

### Version Archive Storage

```
context-archive/
├── v1.0.0/
│  ├── llms.txt
│  ├── api-reference.md
│  ├── metadata.yaml
│  └── checksum.sha256
├── v1.1.0/
│  └── ...
└── current/ → v1.2.3/  (symlink)
```

### Preservation Policy

| Context Age | Policy |
|---|---|
| Current (< 1 month) | Active distribution |
| Recent (1-6 months) | Available but not promoted |
| Historical (6 months - 2 years) | Archived, available on request |
| Very Old (> 2 years) | Archived, lower priority |

---

## Integration with Agent Systems

### Agent Context Injection

#### Standard Flow

```
Agent Request
    ↓
[Load Agent Profile & Permissions]
    ↓
[Determine Context Requirements]
    ↓
[Load Appropriate Context Layer]
    ↓
[Filter by Permissions/Role]
    ↓
[Inject into Agent Prompt]
    ↓
[Execute Task]
```

#### Context Selection Logic

```python
def select_context(agent_profile):
    """Select appropriate context based on agent needs"""
    
    base_layer = "standard"  # Default
    
    # Adjust based on agent type
    if agent.type == "expert":
        base_layer = "comprehensive"
    elif agent.type == "simple":
        base_layer = "minimal"
    
    # Adjust based on task complexity
    if task.complexity > 0.7:
        base_layer = "comprehensive"
    
    # Filter based on permissions
    context = load_layer(base_layer)
    context = filter_by_permissions(context, agent.role)
    context = filter_by_apis(context, agent.allowed_apis)
    
    return context
```

### Agent-Specific Context Customization

#### Role-Based Filtering

```yaml
roles:
  basic:
    context_layer: minimal
    apis: [core, basic-features]
    guides: [getting-started, common-patterns]
    examples: [basic-use-cases]
    
  advanced:
    context_layer: comprehensive
    apis: [all-public]
    guides: [all]
    examples: [all]
    
  expert:
    context_layer: extended
    apis: [all-public, experimental]
    guides: [all]
    examples: [all]
    details: [architecture, internals]
```

#### Task-Specific Context

```yaml
task_contexts:
  "debugging":
    include: [troubleshooting-guide, known-issues, debug-apis]
    exclude: [getting-started]
    
  "optimization":
    include: [performance-guide, benchmarks, tuning-parameters]
    exclude: [basic-guides]
    
  "migration":
    include: [migration-guide, breaking-changes, upgrade-path]
    exclude: [new-feature-guides]
```

### System Prompt Enhancement

```markdown
## Ante Documentation Context

You have access to comprehensive Ante documentation.

### Available APIs
- [List of available APIs based on role/task]

### Documentation Layers
You can reference:
- API reference for exact signatures
- How-to guides for common patterns
- Examples for working solutions

### Known Limitations
- [List of documented limitations]

### Context Metadata
- Ante Version: 1.2.3
- Context Generated: 2026-02-20
- Validity: Until next release (2026-03-20)
```

---

## Relevance & Freshness Policies

### Freshness Metrics

#### Documentation Freshness

**Definition**: How recently documentation reflects current Ante behavior

**Measurement**:
```
Fresh = (today - last_verified_date) < acceptable_age
```

**Acceptable Age by Type**:
| Type | Max Age | Verify By |
|---|---|---|
| API Reference | 1 month | Running tests |
| How-To Guide | 3 months | Spot testing |
| Architecture | 6 months | Design review |
| Examples | 2 weeks | Execution |

**Action on Stale Content**:
```
If last_updated > max_age:
  1. Mark as "needs refresh"
  2. Assign to SME
  3. If > 2x max_age: Remove from standard context
  4. Archive to historical section
```

#### Context Relevance

**Definition**: Relevance of context to agent task

**Factors**:
- Task type match (debugging, building, etc.)
- Feature match (which APIs needed)
- Skill level match (basic, advanced, expert)
- Context size vs. task complexity

**Scoring Algorithm**:
```
relevance_score = 
  0.4 * task_match +
  0.3 * feature_match +
  0.2 * skill_match +
  0.1 * recency_score
```

**Usage**: Load context only if score > 0.6

### Staleness Detection & Refresh

#### Automated Staleness Check

```bash
# Daily staleness audit
npm run context:check-freshness

Output:
- Fresh: 156 items
- Stale: 12 items
- Very Stale: 3 items

Actions:
- Flag stale for review
- Alert owners of very stale
- Remove from context if > threshold
```

#### Refresh Process

```
Item Marked Stale
    ↓
[Owner Notified]
    ↓
[Review Current Behavior] 
    ↓
[Update Documentation]
    ↓
[Test Examples]
    ↓
[Mark as Fresh]
    ↓
[Regenerate Context]
```

### Context Expiry Management

#### Expiry Dates

Each context bundle includes expiry:

```
Generated: 2026-02-20
Valid Until: 2026-03-20 (30 days typical)
Hard Expiry: 2026-03-27 (7 day grace period)
```

**Action on Expiry**:
1. Stop serving to new requests
2. Warn existing consumers
3. Provide link to new version
4. Archive old context

#### Refresh Schedule

| Context Type | Refresh Interval |
|---|---|
| Static (API ref) | On Ante release |
| Dynamic (known issues) | Weekly |
| Operational (status) | Real-time to daily |
| Agent-specific | Per deployment |

---

## Storage & Retrieval

### Storage Infrastructure

```
context-store/
├── active/
│   ├── v1.2.3-context.1/
│   │   ├── llms.txt
│   │   ├── api-reference.md
│   │   ├── guides.tar.gz
│   │   ├── metadata.yaml
│   │   └── index.json
│   └── v1.2.3-context.2/
│       └── ...
├── archive/
│   ├── v1.1.0-context.final/
│   └── v1.0.0-context.final/
└── metadata/
    ├── version-manifest.yaml
    ├── freshness-log.json
    └── usage-metrics.json
```

### Retrieval API

#### llms.txt Download

```bash
# Get latest context
curl https://docs.antigma.ai/llms.txt

# Get specific version
curl https://docs.antigma.ai/llms.txt?version=1.2.3

# Get specific context layer
curl https://docs.antigma.ai/llms.txt?layer=standard
```

#### Agent Context Endpoint

```bash
# Request context for agent
curl -X POST https://api.antigma.ai/context/inject \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "agent_id": "agent-123",
    "role": "advanced",
    "task": "debugging",
    "version": "1.2.3"
  }'

# Response: Custom context for agent
```

#### Search API

```bash
# Search documentation in context
curl https://api.antigma.ai/context/search \
  -d '{"q": "authentication patterns", "version": "1.2.3"}'

# Returns: Matching sections with metadata
```

### Caching Strategy

#### Multi-Level Cache

```
User Request
    ↓
[Check Browser Cache - 24 hours]
    ↓
[Check CDN Cache - 6 hours]
    ↓
[Check App Cache - 1 hour]
    ↓
[Fetch from Origin]
    ↓
[Populate Caches]
```

**Cache Headers**:
```
llms.txt: Cache-Control: public, max-age=3600 (1 hour)
Version-manifest: Cache-Control: public, max-age=86400 (1 day)
Archive content: Cache-Control: immutable, max-age=31536000 (1 year)
```

---

## Performance & Optimization

### Context Size Optimization

#### Size Targets

| Layer | Target Size | Real Max |
|---|---|---|
| Minimal | 10-20 KB | 50 KB |
| Standard | 100-200 KB | 300 KB |
| Comprehensive | 500-1000 KB | 1.5 MB |
| Extended | 1000+ KB | 3 MB |

#### Compression Techniques

1. **Content Deduplication**
   ```
   - Remove redundant explanations
   - Link to canonical versions
   - Use references instead of copy-paste
   ```

2. **Structural Optimization**
   ```
   - Remove navigation markup
   - Flatten unnecessary nesting
   - Use concise formatting
   ```

3. **Format Optimization**
   ```
   - Use gzip compression (typically 60-70% reduction)
   - Remove images (convert to descriptions)
   - Compact markdown formatting
   ```

#### Size Measurement

```bash
# Measure context sizes
npm run context:measure-size

Output:
- llms.txt (gzipped): 142 KB / 412 KB uncompressed
- Standard layer: 167 KB / 521 KB uncompressed
- Comprehensive layer: 897 KB / 2.3 MB uncompressed

Recommendations:
- Current usage: optimal
- Trend: +2% per release (monitor)
```

### LLM Token Efficiency

#### Token Counting

```python
# Estimate tokens for context
def estimate_tokens(context_text):
    """Rough estimate: 1 token ≈ 4 characters"""
    tokens = len(context_text) / 4
    return tokens


# Example:
# Standard layer: 170 KB = 170,000 * 8 bits = 42,500 tokens
# Reasonable for most LLM context windows
```

#### Token Optimization

**Strategy**:
1. For production agents: Use "minimal" layer + task-specific APIs
2. For research: Use "comprehensive" layer
3. For LLMs: Use "standard" layer by default
4. Cache token estimates in metadata

### Delivery Optimization

#### CDN Distribution

```
global-cdn/
├── cdn1.region1.com → llms.txt
├── cdn2.region2.com → llms.txt
└── cdn3.region3.com → llms.txt
```

**Latency Targets**:
- P50: < 50ms
- P95: < 200ms
- P99: < 500ms

#### Parallel Fetching

For agents requiring multiple context layers:

```javascript
// Fetch multiple context sources in parallel
const contexts = await Promise.all([
  fetch('/llms.txt?layer=core'),
  fetch('/llms.txt?layer=feature&feature=auth'),
  fetch('/llms.txt?layer=examples')
]);
```

---

## Context Updates & Synchronization

### Update Triggers

```
Scheduled Update (Weekly)
    ↓
Feature Release (On-release)
    ↓
Critical Issue (As-needed)
    ↓
[Generate Context]
    ↓
[Validate]
    ↓
[Deploy]
```

### Synchronization Process

#### Step 1: Collection

```python
# Gather all documentation updates
1. Scan documentation directory for changes
2. Extract new/modified content
3. Identify deprecated items
4. Gather metrics and metadata
```

#### Step 2: Processing

```python
# Process into context format
1. Format for LLM consumption
2. Remove redundancy
3. Add cross-references
4. Compress assets
5. Generate search index
```

#### Step 3: Validation

```python
# Validate context quality
1. Test code examples
2. Verify all links
3. Check for broken references
4. Validate metadata
5. Test search functionality
```

#### Step 4: Deployment

```python
# Deploy context updates
1. Generate version manifest
2. Deploy to CDN/storage
3. Update API endpoints
4. Notify consumers
5. Monitor usage
```

#### Step 5: Monitoring

```python
# Monitor after deployment
1. Check for errors/issues
2. Monitor usage metrics
3. Track performance
4. Gather feedback
5. Plan improvements
```

### Update Notification

**Notification Channels**:

1. **For LLM Users**: Include version info in system prompt
2. **For Agents**: Include in context metadata headers
3. **For API Consumers**: Webhook notifications
4. **For Documentation Site**: In-app notifications

**Notification Format**:

```
New Ante context available
- Version: 1.2.3
- Size: 142 KB
- New Features: 3
- Improvements: 12
- Updated: 2026-02-20

Get latest: https://docs.antigma.ai/llms.txt
```

---

## Monitoring & Metrics

### Context Metrics

#### Quality Metrics

```yaml
quality_metrics:
  broken_links_count: 0              # Target: 0
  tested_examples_pass_rate: 98%     # Target: > 95%
  freshness_score: 8.2/10            # Target: > 8.0
  completeness_score: 92%            # Target: > 90%
  clarity_score: 7.8/10              # Target: > 7.0
  
  by_section:
    api_reference: 100%
    guides: 94%
    examples: 98%
    troubleshooting: 85%
```

#### Usage Metrics

```yaml
usage_metrics:
  daily_downloads: 1247
  api_requests: 8934
  unique_consumers: 342
  top_accessed:
    - /llms.txt: 45%
    - /api-reference: 23%
    - /guides: 18%
    - /examples: 14%
```

#### Performance Metrics

```yaml
performance_metrics:
  generation_time: 2.3s             # Target: < 5s
  file_size_uncompressed: 2.1 MB
  file_size_gzipped: 412 KB
  cdn_latency_p50: 42ms             # Target: < 50ms
  cdn_latency_p95: 156ms            # Target: < 200ms
```

### Monitoring Dashboard

Key metrics displayed on monitoring dashboard:

1. **Content Health**
   - Broken links
   - Stale content
   - Missing documentation
   - Quality score

2. **Performance**
   - Generation time
   - Delivery latency
   - Cache hit rate
   - Size trend

3. **Usage**
   - Daily/weekly downloads
   - API requests
   - Unique consumers
   - Popular sections

4. **Issues**
   - Reported errors
   - User complaints
   - Failed validations
   - SLA breaches

### Alerting

**Alert Thresholds**:

| Metric | Threshold | Action |
|---|---|---|
| Broken Links | > 0 | Page on-call |
| Quality Score | < 8.0 | Create issue |
| Stale Content | > 10% | Alert team |
| Generation Failure | Any | Page on-call |
| Latency P95 | > 500ms | Investigate |

### Reporting Schedule

| Report | Frequency | Owner |
|---|---|---|
| Quality Audit | Weekly | QA |
| Usage Report | Weekly | Product |
| Performance Report | Daily | Ops |
| Comprehensive Review | Monthly | Lead |
| Strategic Review | Quarterly | Steering |

---

## Appendices

### A. Context Bundle Checklist

```markdown
## Pre-Release Context Bundle Checklist

### Content Coverage
- [ ] All public APIs documented
- [ ] Recent features included
- [ ] Known issues documented
- [ ] Deprecation notices included
- [ ] Examples for major features

### Quality Assurance
- [ ] No broken links
- [ ] All code examples tested
- [ ] Metadata complete
- [ ] Version correct
- [ ] Search index built

### Optimization
- [ ] Size within targets
- [ ] Compression applied
- [ ] Redundancy removed
- [ ] Token count estimated
- [ ] Cache headers set

### Validation
- [ ] Security scan passed
- [ ] Format validation passed
- [ ] Integration test passed
- [ ] Performance targets met
- [ ] User feedback reviewed

### Deployment
- [ ] Version tagged
- [ ] CDN pre-warmed
- [ ] Notifications prepared
- [ ] Rollback plan ready
- [ ] Monitoring configured

### Sign-Off
- [ ] Technical lead approval
- [ ] Operations approval
- [ ] Product approval
```

### B. Context Quality Scorecard

```yaml
quality_scorecard:
  accuracy:
    weight: 0.3
    sub_scores:
      api_correctness: 10/10
      example_accuracy: 9/10
      metadata_completeness: 9/10
    score: 9.3/10
  
  completeness:
    weight: 0.25
    sub_scores:
      api_coverage: 9/10
      guide_coverage: 8/10
      example_coverage: 9/10
    score: 8.7/10
  
  clarity:
    weight: 0.25
    sub_scores:
      readability: 8/10
      organization: 8/10
      navigation: 7/10
    score: 7.7/10
  
  freshness:
    weight: 0.2
    sub_scores:
      age_score: 9/10
      test_currency: 9/10
    score: 9.0/10
  
  overall_score: 8.55/10 (Target: > 8.0)
```

### C. Consumer Integration Checklist

For each consumer integrating context:

```markdown
## Consumer Integration Checklist

### Setup
- [ ] API credentials obtained
- [ ] Access level configured
- [ ] Cache strategy defined
- [ ] Update frequency planned

### Integration
- [ ] Fetch endpoint integrated
- [ ] Version handling implemented
- [ ] Error handling implemented
- [ ] Logging configured

### Testing
- [ ] Happy path tested
- [ ] Error cases tested
- [ ] Performance validated
- [ ] Load testing completed

### Deployment
- [ ] Staging deployment successful
- [ ] Production deployment plan ready
- [ ] Rollback plan documented
- [ ] Monitoring configured

### Ongoing
- [ ] Usage metrics tracked
- [ ] Quality feedback provided
- [ ] Version upgrades planned
- [ ] Issue reporting process established
```
