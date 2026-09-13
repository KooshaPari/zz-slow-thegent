# Context Documentation Creation & Maintenance Process

This document provides step-by-step procedures for creating, updating, and maintaining context documents for technologies integrated with thegent.

---

## Quick Reference

| Task                    | When                                | Owner            | Est. Time |
| ----------------------- | ----------------------------------- | ---------------- | --------- |
| Create new context doc  | Before technology integration       | Tech Owner       | 2-4 hours |
| Update existing doc     | After major version; >90 days stale | Tech Owner       | 1-2 hours |
| Verify accuracy         | Before using in production code     | Implementer      | 30-60 min |
| Refresh staleness dates | Monthly/quarterly review            | Automation       | 5 min     |
| Archive tech doc        | Technology deprecated/superseded    | Deprecation Lead | 15 min    |

---

## When to Create a Context Doc

A context doc is **required** (P0/P1 priority) when:

1. **Starting integration of a new technology**
   - Before writing a single line of integration code
   - Example: Adding Codex support → create `docs/context/codex.md` first

2. **Implementing a new protocol/SDK**
   - If thegent will directly call or wrap the technology
   - Example: FastMCP adoption → create `docs/context/fastmcp.md`

3. **Technology referenced in 3+ places** in the codebase
   - Even if integration is partial, a context doc prevents scattered understanding
   - Use codebase search to count references

4. **During research/spike of new technology**
   - If the spike results in "yes, we'll integrate this", document findings in a context doc
   - Move research notes from `docs/research/` to `docs/context/` as the tech is adopted

---

## Step-by-Step Process: Creating a New Context Doc

### Phase 1: Preparation (15-30 min)

#### Step 1.1: Check if doc already exists

```bash
# Check atomic docs
ls docs/context/{technology}.md

# Check doc sets
ls -la docs/context/{technology}/

# Search for mentions in existing docs
grep -r "{technology}" docs/context/
```

If found: Update existing doc instead (skip to "Updating a Context Doc" section).

#### Step 1.2: Assign ownership

- Identify a **Technology Owner** (the person implementing the integration)
- They will be responsible for initial draft + verification
- Add to ticket/issue: `Tech Owner: @person`

#### Step 1.3: Gather official sources

Collect authoritative reference materials:

- Visit official documentation URL
- Check GitHub repo for README, API docs, architecture
- Download or archive key pages (use webarchive.org if fleeting)
- Note the fetch date (YYYY-MM-DD)

For local tools/SDKs:

- Extract from installed package docs
- Run tool help command
- Check source code for API signatures
- Run local examples to verify behavior

For APIs:

- Download official API reference
- Test endpoints with actual requests (rate-limit aware)
- Document observed behavior vs. stated behavior
- Note any undocumented quirks or gotchas

Save sources in a working directory (e.g., `/tmp/tech-docs/`).

#### Step 1.4: Identify the doc type

Decide: **Atomic doc** (single file) or **Doc set** (directory)?

- **Atomic**: Technology is single-purpose or small API surface area
  - Examples: OpenRouter (API), WorkOS (auth), Nix (package manager)
  - File: `docs/context/{technology}.md`

- **Doc set**: Technology is large or multi-faceted
  - Examples: Ante (agent platform), Claude Code (harness), Codex (IDE)
  - Files: `docs/context/{technology}/index.md` + subdocs
  - When > 2000 words needed, use doc set

Choose atomic unless the technology logically breaks into 4+ major sections.

---

### Phase 2: Information Extraction (45-90 min)

#### Step 2.1: Extract key technical details

Create a working document and extract:

1. **Foundational questions**
   - What problem does it solve?
   - What is it NOT (what shouldn't I use it for)?
   - How does thegent use it?
   - Key architectural patterns?

2. **API/Interface specs** (if applicable)
   - Endpoints, methods, or function signatures
   - Required headers, query params, body fields
   - Response format and error responses
   - Rate limits, quotas, timeouts

3. **Authentication**
   - What credential types? (API key, token, OAuth, cert)
   - Where to obtain? (console URL, command, etc.)
   - Required headers or environment vars
   - Expiration, rotation, or refresh behavior

4. **Concepts & Terminology**
   - Domain-specific terms (e.g., "model routing", "agent turn")
   - Key data structures or enums
   - Important constraints or guarantees

5. **Typical usage patterns**
   - Happy path: How do you normally use this?
   - Error handling: What can go wrong?
   - Async/streaming: Does it support it?
   - Pagination: How to handle large result sets?

#### Step 2.2: Test with real examples

For APIs:

- Get actual response shapes with curl or similar
- Note the response structure, field types, any nested objects
- Save to working docs

For SDKs:

- Test in Python REPL or script
- Check return type
- Inspect fields

For CLIs:

- Run with --help to document flags
- Run example commands and capture output

Save all output to working docs for reference during writing.

#### Step 2.3: Identify gotchas and edge cases

Search docs/repos for:

- "Note:", "Important:", "Gotcha", "Common mistake"
- GitHub issues marked "documentation" or "FAQ"
- StackOverflow questions about common problems

Document these in "Common Patterns" or error handling section of the context doc.

---

### Phase 3: Writing (90-180 min)

#### Step 3.1: Use the governance template

Open `docs/context/GOVERNANCE.md` and follow the required structure:

1. Header (title, description, sources)
2. What is {Technology}
3. Key Concepts
4. API/Interfaces
5. Authentication
6. Code Examples
7. Sources & References
8. Quick Reference

Do not skip sections. Use empty sections if not applicable, but mark them explicitly.

#### Step 3.2: Write each section

**Section 1: Header** - Include title, description, sources with fetch date

**Section 2: What is {Technology}** - Start with definition, explain problem, bullet capabilities, why thegent uses it. Target: 150-300 words.

**Section 3: Key Concepts** - Only if technology has domain-specific terms. Format as `**Term**: definition` or simple table.

**Section 4: API/Interfaces**

For HTTP APIs:

- Endpoint path: `METHOD /path`
- Description of what it does
- Exact request format (headers, body, query params)
- Exact response format (JSON structure, types)
- Status codes (200, 400, 401, 429, 500, etc.)

For SDKs/libraries:

- Class/module name
- Constructor signature and defaults
- Method signatures with type hints
- Return types

For CLIs:

- Command structure: `tool subcommand --flags`
- Required vs optional flags
- Output format
- Exit codes

Be precise with types and fields.

**Section 5: Authentication**

- Type of credential (API key, token, OAuth, etc.)
- Where to get it (URL + steps)
- How to provide it (header, query param, env var)
- Rate limits or quotas
- Any special headers or metadata

**Section 6: Code Examples**

1-3 examples covering main use cases. All examples must be **tested and working**.

**Section 7: Sources & References**

Complete citations with URLs and dates.

**Section 8: Quick Reference**

One-page cheat sheet. Include base URL, auth, rate limits, response format, common patterns, most-used endpoints, common errors.

#### Step 3.3: Cross-check against sources

For each section, verify:

- Every API endpoint exists in official docs
- Every field type is correct
- Every error code is documented
- Every code example is syntactically valid

#### Step 3.4: Run code examples

Before finalizing, test all code examples:

- Python: `python -c "..."`
- Shell: `bash example.sh`
- Node: `node example.js`

Capture actual output and include in doc as comments.

---

### Phase 4: Integration & Verification (30-60 min)

#### Step 4.1: Create the file

If atomic doc:

```bash
cat > docs/context/{technology}.md << 'EOF'
[Full document content]
EOF
```

If doc set:

```bash
mkdir -p docs/context/{technology}
# Create index.md and subdocs
```

#### Step 4.2: Update docs/context/INDEX.md

Add entry to the index table.

#### Step 4.3: Cross-reference with implementation code

If integrating a new technology:

- Add comments linking to context doc sections
- Example: `# See docs/context/openrouter.md - API/Interfaces section`
- Update any README or architecture docs to reference the context doc

#### Step 4.4: Verify against pre-write validation

All required sections should be present:

- Title
- What is section
- Key Concepts (if applicable)
- API section (if applicable)
- Authentication section
- Code Examples
- Sources & References
- Quick Reference

#### Step 4.5: Peer review (if new doc)

- Request review from tech lead and implementer
- Reviewer checks:
  - No hallucination (compare examples against official docs)
  - Clarity and completeness
  - Code examples actually work
  - All API specs are accurate
- Approval required before merge

---

### Phase 5: Completion

#### Step 5.1: Commit message

```
add: context doc for {technology}

Covers:
- API endpoints and authentication
- Key concepts and terminology
- Working code examples
- Quick reference

Closes #{issue}
```

#### Step 5.2: Link from integration PR

If creating doc as part of implementing a feature:

- Reference the context doc in your implementation PR
- Mention in PR description: "See docs/context/{tech}.md for API reference"

#### Step 5.3: Update CHANGELOG

If significant new context doc:

```markdown
## [Unreleased]

### Added

- Context documentation for {Technology} (docs/context/{technology}.md)
  Covers API, authentication, key concepts, and usage patterns.
```

---

## Updating an Existing Context Doc

### When to Update

1. **After major version release** (X.0.0 bump)
2. **After breaking API change** (endpoint removal, field deprecation)
3. **Quarterly staleness check** (every 90 days minimum)
4. **When implementing a feature** and discovering inaccuracies

### Quick Update (Minor)

For small changes (typo, date refresh, minor clarification):

1. Edit `docs/context/{technology}.md` directly
2. Update `Last Verified` date in header
3. If stale banner exists, remove it (if doc is current)
4. Commit: `fix: update {tech} context doc - {brief description}`
5. No review needed for minor updates

### Major Update

If API changed significantly or 6+ months since last update:

1. Fetch latest official docs
2. Update "Sources" section with new URLs and fetch date
3. Update all API sections (new endpoints, removed endpoints, changed fields)
4. Test code examples against latest version
5. Update "Changelog" section (if exists) with changes
6. Request peer review (1 approval required)
7. Commit: `update: {tech} context doc for v{version}`

---

## Creating and Maintaining docs/context/INDEX.md

The index is the **canonical catalog** of all context docs.

### Basic Structure

```markdown
# Context Documentation Index

> Authoritative reference catalog for all technologies integrated with thegent.

## Index by Technology

| Technology  | File           | Category      | Priority | Last Updated | Status     |
| ----------- | -------------- | ------------- | -------- | ------------ | ---------- |
| OpenRouter  | openrouter.md  | API Gateway   | P0       | 2026-02-20   | ✅ Current |
| Claude Code | claude-code.md | Agent Harness | P0       | 2026-02-20   | ✅ Current |

## Index by Category

### Agent Harnesses (P0)

- Ante: ante/index.md
- Claude Code: claude-code.md

### API Gateways & Proxies (P0)

- OpenRouter: openrouter.md
```

### Updating INDEX.md

Every time you:

- **Create** a new context doc: Add row to table
- **Update** a context doc: Update `Last Updated` date and status
- **Mark stale**: Update status to `⚠️ Stale (N days)`
- **Archive** a doc: Remove from main table, add to "Archived" section

---

## Verification Checklist: Before Using a Context Doc

Before referencing a context doc in implementation code, verify accuracy:

### Quick Verification (10-15 min)

- Header has recent fetch date (< 6 months)
- No `⚠️ Possibly stale` banner
- Read "What is {Tech}" section - aligns with your understanding
- Skim code examples - syntax looks correct

### Full Verification (30-60 min)

If integrating a technology for the first time:

- Test 3-5 API examples from context doc against actual API/SDK
- Verify auth setup matches what's documented
- Run at least one code example without modification
- Check that error handling matches real errors
- Spot-check 5 random claims against official docs

**If you find inaccuracies**: File issue and update context doc before proceeding.

---

## Troubleshooting

### Problem: "Context doc exists but has wrong info"

1. Identify what's wrong
2. Check official docs for correct info
3. Update context doc with correct info
4. Add to changelog if applicable
5. Commit: `fix: correct {field} in {tech} context doc`

### Problem: "Technology is P0 but has no context doc"

1. Create issue: `[MISSING] Create context doc for {technology} (P0)`
2. Assign to technology owner
3. Follow "Creating a New Context Doc" process above
4. Update INDEX.md once created

### Problem: "Doc is stale (> 90 days) and technology version changed"

1. Note the version that changed
2. Fetch latest official docs for that version
3. Identify what changed in the API/behavior
4. Update context doc sections that changed
5. Update `Last Verified` date
6. Remove staleness banner if all sections are current
7. Commit: `update: {tech} context doc for v{version}`

### Problem: "I'm implementing a feature and discovered the context doc is wrong"

1. Pause implementation
2. Check official docs to confirm the error
3. File issue: `[INACCURACY] {tech} context doc - {field} is incorrect`
4. Update context doc with correct info
5. Add code comment linking to updated doc
6. Resume implementation

---

## See Also

- `docs/context/GOVERNANCE.md` - Standards and requirements
- `docs/context/INDEX.md` - Catalog of all context docs
- `docs/governance/ARCHITECTURAL_GOVERNANCE.md` - Integration with architecture decisions
