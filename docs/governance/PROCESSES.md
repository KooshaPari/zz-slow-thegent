# Ante Documentation Operational Processes

## Table of Contents

1. [Process Overview](#process-overview)
2. [Release Documentation Process](#release-documentation-process)
3. [Web Archive Collection & Processing](#web-archive-collection--processing)
4. [Adding Feature Documentation](#adding-feature-documentation)
5. [Markdown Wiki Maintenance](#markdown-wiki-maintenance)
6. [llms.txt Generation & Updates](#llmstxt-generation--updates)
7. [Documentation Validation & Testing](#documentation-validation--testing)
8. [Emergency Updates & Hotfixes](#emergency-updates--hotfixes)

---

## Process Overview

### Key Responsibilities

Documentation processes are maintained by:

- **Documentation Coordinator**: Overall process management
- **Technical Leads**: Feature documentation and accuracy
- **Content Team**: Writing, editing, formatting
- **QA Team**: Validation and testing

### Documentation Calendar

**Typical Release Cycle**:

- **T-12 weeks**: Release planning, documentation assessment
- **T-8 weeks**: Feature documentation begins
- **T-4 weeks**: Feature documentation complete, review begins
- **T-2 weeks**: Documentation freeze, critical fixes only
- **T-0**: Release published with documentation
- **T+1 week**: Post-release updates, corrections

---

## Release Documentation Process

### Pre-Release Phase (T-12 to T-4 weeks)

#### Step 1: Release Planning & Documentation Audit

**Trigger**: Release planning meeting

**Process**:

1. **Identify Documentation Scope**

   ```
   For each feature/change in release:
   - Is documentation needed? (APIs, user-facing changes, behavior)
   - What type? (API reference, guide, migration guide)
   - Who is the SME?
   - Where does it belong?
   ```

2. **Audit Existing Documentation**
   - Run `documentation-validator` tool
   - Check for broken links
   - Verify code examples run
   - Check freshness dates
   - List items needing updates

3. **Create Documentation Plan**

   ```markdown
   # Release X.Y.Z Documentation Plan

   ## New Documentation Needed

   - [ ] Feature A - API Reference (Owner: Name)
   - [ ] Feature B - How-To Guide (Owner: Name)
   - [ ] Breaking Change C - Migration Guide (Owner: Name)

   ## Documentation Updates

   - [ ] Update API index
   - [ ] Update feature matrix
   - [ ] Refresh examples

   ## Deprecations

   - [ ] Archive feature X docs
   - [ ] Create migration guide for feature Y

   ## Timeline

   - Draft deadline: T-6 weeks
   - Review deadline: T-4 weeks
   - Final approval: T-2 weeks
   ```

4. **Assign Owners**
   - Technical SME reviews for accuracy
   - Documentation writer handles content
   - Editor handles style and clarity

**Outputs**: Documentation plan, assignment matrix

**Responsible Party**: Documentation Lead

#### Step 2: Feature Documentation Development

**Trigger**: Feature code freeze

**Process**:

1. **Establish Information Requirements**
   - Review feature specification
   - Identify user workflows
   - Document API signatures
   - Create example scenarios

2. **Prepare Documentation**

   ```
   For each required documentation piece:
   - Create file in appropriate directory
   - Include all required headers
   - Write technical content
   - Create working examples
   - Add cross-references
   - Self-review against checklist
   ```

3. **Create Working Examples**
   - Write code examples that run
   - Test against actual implementation
   - Document any prerequisites
   - Include expected output
   - Provide troubleshooting tips

4. **Build Documentation Set**

   ```
   Example: New Authentication Feature

   ├── api-reference/
   │   ├── auth-session.md       (API reference)
   │   ├── auth-token.md          (API reference)
   │   └── auth-refresh.md        (API reference)
   ├── guides/
   │   ├── auth-setup.md          (How-to guide)
   │   ├── auth-patterns.md       (Conceptual)
   │   └── auth-troubleshooting.md
   └── examples/
       ├── auth-basic.js
       ├── auth-jwt.js
       └── auth-session-mgmt.js
   ```

5. **Link Related Documentation**
   - Cross-reference in existing docs
   - Update feature index
   - Update examples index
   - Add to navigation

**Outputs**: Complete feature documentation set

**Responsible Party**: Technical SME + Content Writer

#### Step 3: Documentation Review

**Trigger**: Feature documentation draft complete

**Process**:

1. **Technical Review** (2-3 days)
   - SME reviews against implementation
   - Test all code examples
   - Verify API accuracy
   - Check completeness
   - Verify examples match current behavior

2. **Editorial Review** (2-3 days)
   - Content editor reviews clarity
   - Check style consistency
   - Verify formatting
   - Proofread for errors
   - Check readability

3. **Address Feedback**
   - Incorporate SME feedback
   - Revise for clarity
   - Update examples if needed
   - Verify changes with reviewers

4. **Final Approval**
   - SME sign-off on accuracy
   - Editor sign-off on quality
   - Ready for release preparation

**Outputs**: Approved documentation, merged to main

**Responsible Party**: Maintainers + Editors

### Release Freeze Phase (T-2 weeks to T-0)

#### Step 4: Documentation Freeze & Final Checks

**Trigger**: Release freeze date

**Process**:

1. **Documentation Freeze**
   - No new documentation accepted
   - Only critical fixes allowed
   - Code freeze aligned with doc freeze
   - All feature docs should be merged

2. **Final Validation** (Checklist)

   ```markdown
   ## Release Documentation Validation

   ### Completeness

   - [ ] All new features documented
   - [ ] All APIs with examples
   - [ ] All breaking changes documented
   - [ ] Migration guides prepared

   ### Accuracy

   - [ ] Code examples tested against build
   - [ ] API signatures match implementation
   - [ ] Examples use correct syntax
   - [ ] Warnings/notes accurate

   ### Quality

   - [ ] No broken links
   - [ ] Consistent formatting
   - [ ] Consistent terminology
   - [ ] Proper headers/metadata

   ### Readiness

   - [ ] Changelog finalized
   - [ ] Release notes prepared
   - [ ] Deprecated items archived
   - [ ] Navigation updated
   ```

3. **Generate Release Documentation**
   - Create release notes
   - Create migration guide (if breaking changes)
   - Create deprecation notices
   - Prepare announcement

4. **Prepare Distribution**
   - Generate llms.txt
   - Create web archive bundle
   - Update search index
   - Prepare context packages

**Outputs**: Release documentation bundle, llms.txt

**Responsible Party**: Documentation Coordinator

### Release Day

#### Step 5: Documentation Release

**Trigger**: Code release

**Process**:

1. **Publish Documentation**
   - Deploy documentation to website
   - Update version numbers
   - Refresh search index
   - Distribute llms.txt
   - Update context systems

2. **Announce Updates**
   - Post release notes to channels
   - Update status pages
   - Notify documentation subscribers
   - Share on community forums

3. **Monitor Impact**
   - Watch for documentation issues
   - Respond to user questions
   - Fix critical errors immediately
   - Document any clarifications

**Outputs**: Live documentation, published release

**Responsible Party**: Documentation Team

### Post-Release Phase (T+1 week to T+4 weeks)

#### Step 6: Documentation Maintenance

**Trigger**: Release published

**Process**:

1. **Collect Feedback**
   - Monitor issues and questions
   - Track documentation bugs
   - Collect user feedback
   - Identify missing information

2. **Make Corrections**
   - Fix errors found by users
   - Clarify confusing sections
   - Add missing examples
   - Update incorrect information

3. **Plan Next Iteration**
   - Document lessons learned
   - Identify improvements needed
   - Plan documentation enhancements
   - Update processes based on feedback

**Outputs**: Corrections applied, feedback recorded

**Responsible Party**: Documentation Team + Contributors

---

## Web Archive Collection & Processing

### Purpose

Collect and maintain official Ante documentation from all available sources for inclusion in LLM context and local reference.

### Archive Sources

1. **Official Ante Documentation** (Primary)
   - docs.antigma.ai
   - GitHub wiki
   - API reference docs

2. **Release Assets**
   - Release notes
   - Migration guides
   - Deprecation notices

3. **Community Resources** (Curated)
   - Blog posts about features
   - Official tutorials
   - Case studies

### Collection Process

#### Step 1: Identify & Catalog Sources

**Process**:

1. **Maintain Source Registry**

   ```yaml
   sources:
     - name: "Official Docs"
       url: "https://docs.antigma.ai"
       type: "primary"
       frequency: "on-release"
       last_collected: "2026-02-20"

     - name: "API Reference"
       url: "https://api.antigma.ai/docs"
       type: "primary"
       frequency: "on-release"
       last_collected: "2026-02-20"
   ```

2. **Verify Access**
   - Test each URL is accessible
   - Check for authentication requirements
   - Note any access restrictions
   - Document any rate limits

#### Step 2: Download & Archive

**Process**:

1. **Execute Collection**

   ```bash
   # Archive official docs
   wget -m -np -k \
     --user-agent="Ante-Archiver/1.0" \
     -P archive/docs/ \
     https://docs.antigma.ai

   # Archive release assets
   curl -s https://api.github.com/repos/AntigmaLabs/ante/releases/latest \
     | jq -r '.assets[].browser_download_url' \
     | xargs -I {} wget {} -P archive/releases/
   ```

2. **Verify Download**
   - Check file sizes reasonable
   - Spot-check HTML integrity
   - Verify asset links preserved
   - Check no rate limiting occurred

3. **Store Archive**
   ```
   archive/
   ├── docs/
   │   ├── 2026-02-20/        # Date-stamped
   │   │   ├── index.html
   │   │   ├── api/
   │   │   ├── guides/
   │   │   └── ...
   │   └── latest/            # Symlink to current
   └── releases/
       ├── v1.2.3/
       │   ├── RELEASE_NOTES.md
       │   ├── MIGRATION_GUIDE.md
       │   └── ...
   ```

#### Step 3: Convert to Markdown

**Process**:

1. **Convert HTML to Markdown**

   ```bash
   # Using pandoc
   pandoc archive/docs/latest/index.html \
     -f html -t markdown \
     -o documentation/raw/docs_index.md
   ```

2. **Post-Process Markdown**

   ```python
   # Clean up conversion artifacts
   - Fix relative links
   - Remove navigation cruft
   - Standardize headers
   - Verify code blocks syntax-highlighted
   - Add source attribution
   ```

3. **Structure Output**
   ```
   documentation/
   ├── archived-web/
   │   ├── api-reference.md
   │   ├── core-guides.md
   │   ├── feature-matrix.md
   │   └── changelog.md
   ```

#### Step 4: Index & Catalog

**Process**:

1. **Create Index**

   ```markdown
   # Ante Documentation Archive

   **Archive Date**: 2026-02-20  
   **Source Version**: 1.2.3  
   **Archive Status**: Complete

   ## Contents

   - [API Reference](./api-reference.md)
   - [Getting Started Guide](./getting-started.md)
   - [Architecture Overview](./architecture.md)
   ```

2. **Add Metadata**

   ```yaml
   archive_metadata:
     date: 2026-02-20
     source_version: 1.2.3
     collection_method: "wget-snapshot"
     files_count: 127
     total_size: "45.3 MB"
     completeness: "100%"
     verification: "passed"
   ```

3. **Document Links**
   - Map web URLs to archive locations
   - Create redirect mappings
   - Document any broken links
   - Note any missing content

### Archive Maintenance Schedule

| Task                        | Frequency  | Owner       |
| --------------------------- | ---------- | ----------- |
| Verify source accessibility | Weekly     | Tech Lead   |
| Collect new releases        | On-release | Coordinator |
| Update archive              | Biweekly   | Tech Lead   |
| Clean old archives          | Monthly    | Ops         |
| Full re-collection          | Quarterly  | Coordinator |

---

## Adding Feature Documentation

### When to Add Feature Documentation

Create documentation when:

- [ ] New public API added
- [ ] User-facing behavior changed
- [ ] New architectural component added
- [ ] Previously undocumented feature gains adoption
- [ ] Breaking changes made to existing API

### Feature Documentation Workflow

#### Step 1: Plan Documentation

```markdown
# Feature Documentation Plan: [Feature Name]

## Feature Overview

- What the feature does
- Who uses it
- What problems it solves

## Documentation Requirements

- [ ] API Reference - required/optional
- [ ] How-to Guide - required/optional
- [ ] Conceptual Guide - required/optional
- [ ] Migration Guide - required/optional
- [ ] Code Examples - required/optional

## Acceptance Criteria

- [ ] All APIs documented with examples
- [ ] Common use cases covered
- [ ] Examples tested and working
- [ ] Cross-references complete
- [ ] Ready for user consumption

## Owner & Timeline

- Technical SME: [Name]
- Writer: [Name]
- Deadline: [Date]
```

#### Step 2: Create API Reference

Create `api-reference/[feature].md`:

```markdown
---
version: 1.0.0
last_updated: 2026-02-20
status: active
---

# [Feature] API Reference

## Functions

### function_name(param1, param2)

**Description**: What the function does.

**Parameters**:

- `param1` (type): Description
- `param2` (type): Description

**Returns**: (type) Description

**Throws**:

- `ErrorType`: When this occurs
- `ErrorType`: When this occurs

**Stability**: stable/experimental/deprecated

**Example**:
\`\`\`javascript
// Example code that runs
const result = function_name(arg1, arg2);
console.log(result); // Output: ...
\`\`\`

**See Also**:

- [Related Function](../api-reference/other.md)
- [How-To Guide](../guides/feature-usage.md)
```

#### Step 3: Create How-To Guide

Create `guides/[feature]-setup.md`:

```markdown
---
version: 1.0.0
last_updated: 2026-02-20
status: active
---

# How to [Feature]

## Prerequisites

Before starting, ensure you have:

- [ ] Ante version X.Y.Z or later
- [ ] Required permission/access
- [ ] Basic understanding of [concept]

## Step-by-Step Guide

### Step 1: [Setup]

Description of what this step accomplishes.

\`\`\`javascript
// Code example
\`\`\`

### Step 2: [Configuration]

Description of what this step accomplishes.

\`\`\`javascript
// Code example
\`\`\`

## Common Use Cases

### Use Case 1: [Specific Scenario]

Complete working example with explanation.

\`\`\`javascript
// Full example
\`\`\`

## Troubleshooting

| Problem | Cause | Solution |
| ------- | ----- | -------- |
| Error X | Cause | Fix      |

## See Also

- [API Reference](../api-reference/feature.md)
- [Conceptual Guide](../guides/feature-concepts.md)
```

#### Step 4: Create Examples

Create `examples/[feature]-[use-case].js`:

```javascript
/**
 * Example: [Feature] - [Use Case]
 *
 * This example demonstrates how to [specific task]
 *
 * Prerequisites: Ante version X.Y.Z+
 */

// Complete, runnable example
// Should execute without modification
// Output explained in comments
```

#### Step 5: Submit for Review

```markdown
## Documentation Submission

**Feature**: [Name]
**Type**: [API Reference / Guide / Examples]

### Changes Made

- [ ] API reference created/updated
- [ ] How-to guide created/updated
- [ ] Examples created/tested
- [ ] Cross-references added
- [ ] Related docs updated

### Testing Checklist

- [ ] Code examples tested
- [ ] Links verified
- [ ] Formatting validated
- [ ] Tone consistent

### Review Checklist

- [ ] Technically accurate
- [ ] Complete for feature scope
- [ ] Clear and understandable
- [ ] Style consistent

**Ready for review**: [Date]
```

---

## Markdown Wiki Maintenance

### Wiki Structure

```
documentation/
├── README.md                  # Index & navigation
├── GLOSSARY.md               # Terminology
├── QUICK_START.md            # Getting started
├── ARCHITECTURE.md           # System design
├── API_INDEX.md              # API overview
├── CONTRIBUTING.md           # Contribution guide
└── _sidebar.md               # Navigation sidebar
```

### Regular Maintenance Tasks

#### Weekly Tasks

1. **Monitor for Issues** (1 hour)

   ```
   - Check for reported documentation bugs
   - Review new issues/questions
   - Triage and assign to maintainers
   ```

2. **Fix Typos/Errors** (30 min)
   ```
   - Apply simple fixes
   - Maintain changelog
   - Update version numbers if changed
   ```

#### Monthly Tasks

1. **Link Validation** (2 hours)

   ```bash
   # Run link checker
   markdown-link-check documentation/**/*.md

   # Fix broken links
   # Update redirects if needed
   ```

2. **Freshness Review** (2 hours)

   ```
   - Check documents haven't been updated in > 6 months
   - Verify information is still accurate
   - Update last_updated dates
   - Plan updates if needed
   ```

3. **Search Index Update** (1 hour)

   ```bash
   # Rebuild search index
   npm run docs:build-search

   # Test search functionality
   # Verify results relevant
   ```

#### Quarterly Tasks

1. **Documentation Audit** (4 hours)
   - Check completeness against features
   - Identify gaps and outdated sections
   - Assess quality metrics
   - Plan improvements

2. **Navigation Review** (2 hours)
   - Review sidebar and navigation
   - Ensure logical organization
   - Check for orphaned pages
   - Improve discoverability

3. **Archive Old Content** (2 hours)
   - Move deprecated docs
   - Update cross-references
   - Maintain archive accessibility
   - Verify migration guides

### Common Maintenance Issues

| Issue                 | Solution                                          |
| --------------------- | ------------------------------------------------- |
| Broken links          | Run link checker, update URLs or create redirects |
| Outdated examples     | Test against current version, update code         |
| Unclear writing       | Request editorial review, revise for clarity      |
| Missing documentation | Create issue, assign to feature owner             |
| Orphaned pages        | Move to archive or delete if truly unused         |

---

## llms.txt Generation & Updates

### Purpose

Generate `llms.txt` file for consumption by LLM systems, containing curated documentation.

### File Format

`llms.txt` contains:

- Core documentation
- API reference
- Examples
- Best practices
- Current state information

### Generation Process

#### Step 1: Select Content

```
Content Selection Criteria:
- Official APIs and public functions ✓
- Best practices and patterns ✓
- Architecture overview ✓
- Common use cases and examples ✓
- Configuration options ✓
- Known limitations ✓

Exclude:
- Internal implementation details ✗
- Deprecated APIs (link to migration) ✗
- Unreleased features ✗
- Incomplete documentation ✗
```

#### Step 2: Prepare Documentation

```markdown
# Ante Documentation for LLMs

**Version**: 1.2.3  
**Generated**: 2026-02-20  
**Valid Until**: Next release or update

## Core Documentation

[Include overview of Ante, architecture, core concepts]

## API Reference

[Include all public APIs with signatures and examples]

## Best Practices

[Include recommended patterns and approaches]

## Examples

[Include common use cases and solutions]

## Limitations & Constraints

[Document known limitations and workarounds]
```

#### Step 3: Optimize for LLMs

```python
# Optimization steps:
1. Remove navigation/metadata
2. Flatten hierarchy to appropriate depth
3. Remove images (convert to descriptions)
4. Optimize code examples
5. Compress whitespace
6. Add structure markers for parsing
7. Limit total size (~500KB ideal)
```

#### Step 4: Generate File

```bash
# Build llms.txt from documentation
node scripts/generate-llms-txt.js

# Outputs:
# - llms.txt (main file)
# - llms.txt.metadata (stats and checksums)
# - llms.txt.index (searchable index)

# Verify file
wc -w llms.txt               # Check size
head -100 llms.txt           # Check structure
grep -c "##" llms.txt        # Check organization
```

#### Step 5: Validate Content

```markdown
## llms.txt Validation Checklist

### Coverage

- [ ] All public APIs included
- [ ] Examples for major features
- [ ] Architecture described
- [ ] Limitations documented

### Accuracy

- [ ] All information current
- [ ] Code examples correct
- [ ] API signatures match
- [ ] No broken references

### Format

- [ ] Structure clear and consistent
- [ ] Headers hierarchical
- [ ] Code blocks properly marked
- [ ] Links working

### Optimization

- [ ] File size acceptable
- [ ] No redundant content
- [ ] Navigation removed
- [ ] Structure parseable
```

### Update Schedule

| Event        | Action                                |
| ------------ | ------------------------------------- |
| New release  | Regenerate complete                   |
| Minor update | Update affected sections              |
| New API      | Add to reference section              |
| Deprecation  | Add migration info                    |
| Monthly      | Check freshness, regenerate if needed |

---

## Documentation Validation & Testing

### Automated Validation

#### Daily Validation

```bash
# Run automated checks
npm run docs:validate

Checks:
- Markdown syntax valid
- No broken links (internal/external)
- YAML frontmatter valid
- Code block syntax highlighting correct
- File encodings correct
```

#### Code Example Testing

```bash
# Test all code examples
npm run docs:test-examples

Process:
1. Extract all code examples from markdown
2. Execute each example
3. Verify output matches expected
4. Report failures
```

**Test Framework**:

```markdown
\`\`\`javascript
// Example: Feature - Use Case
// EXPECTED: [description of expected output]

const result = someFunction();
console.log(result);
\`\`\`
```

### Manual Validation

#### Before Release

```markdown
## Pre-Release Documentation Validation

### Spot Checks (Sample 20% of documentation)

- [ ] Examples still work
- [ ] APIs match implementation
- [ ] Screenshots/diagrams current
- [ ] Tone consistent

### Critical Path Verification

- [ ] All new features documented
- [ ] All breaking changes documented
- [ ] All deprecations documented
- [ ] Release notes complete

### User Testing

- [ ] Run through getting started guide
- [ ] Test major workflows
- [ ] Verify examples work as written
- [ ] Check clarification questions
```

#### Quarterly Comprehensive Audit

```bash
# Full documentation audit
npm run docs:audit

Audit Covers:
1. Completeness - all public APIs documented
2. Accuracy - examples work, info matches code
3. Consistency - style, terminology, format
4. Currency - no outdated information
5. Accessibility - clarity, readability

Output:
- Audit report with findings
- List of issues to address
- Recommendations for improvement
```

### Issue Tracking

**Documentation Bug Template**:

```markdown
**Title**: [Section] - [Brief Issue]

**Type**:

- [ ] Broken Link
- [ ] Incorrect Information
- [ ] Missing Documentation
- [ ] Unclear Wording
- [ ] Broken Example

**Description**:
[Detailed description of issue]

**Expected Behavior**:
[What should be correct]

**Affected Documentation**:

- Link to affected page
- Version: X.Y.Z

**Suggested Fix**:
[Optional suggested correction]
```

---

## Emergency Updates & Hotfixes

### When to Use Hotfixes

Use hotfix process for:

- Critical security documentation
- Breaking changes not caught before release
- Incorrect API documentation
- Completely broken examples
- Safety/compliance issues

### Hotfix Process

```
Issue Reported
    ↓
[Severity Assessment]
    ↓
Critical → Emergency Review (1 hour)
Urgent  → Fast Review (4 hours)
Normal  → Standard Review (24 hours)
    ↓
[Fix Documentation]
    ↓
[Rapid Review & Approval]
    ↓
[Deploy Immediately]
    ↓
[Communicate Changes]
```

### Emergency Review SLA

| Severity | Review Time | Approval   | Deploy     |
| -------- | ----------- | ---------- | ---------- |
| Critical | 1 hour      | Lead       | Immediate  |
| Urgent   | 4 hours     | Maintainer | ASAP       |
| Normal   | 24 hours    | Maintainer | Next batch |

### Post-Hotfix

1. **Document Root Cause**
   - What was wrong
   - How it was missed
   - How to prevent recurrence

2. **Update Process**
   - Improve validation
   - Enhance review checklist
   - Add to test suite

3. **Communicate Learnings**
   - Share in team meeting
   - Update documentation
   - Improve processes

---

## Tools & Automation

### Recommended Tools

| Tool                  | Purpose           | Command                          |
| --------------------- | ----------------- | -------------------------------- |
| `markdown-lint`       | Validate markdown | `npm run lint:docs`              |
| `markdown-link-check` | Verify links      | `npm run check:links`            |
| `vale`                | Style checking    | `npm run lint:style`             |
| `pandoc`              | Convert formats   | `pandoc input.html -o output.md` |
| `doctoc`              | Generate TOCs     | `doctoc docs/`                   |

### Automation Scripts

Maintain scripts in `scripts/`:

- `generate-llms-txt.js` - Generate LLM context file
- `validate-docs.js` - Run all validation checks
- `test-examples.js` - Test code examples
- `collect-archives.sh` - Collect web archives
- `build-search-index.js` - Build search functionality

---

## Contact & Escalation

- **Documentation Issues**: File in documentation repository
- **Process Questions**: Reach out to Documentation Coordinator
- **Emergency**: Page on-call Documentation Lead
- **Feedback**: Use feedback form on documentation site
