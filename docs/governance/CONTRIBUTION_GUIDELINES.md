# Ante Documentation Contribution Guidelines

## Table of Contents

1. [Welcome Contributors](#welcome-contributors)
2. [Getting Started](#getting-started)
3. [Documentation Style Guide](#documentation-style-guide)
4. [Writing Standards](#writing-standards)
5. [Markdown Formatting Guide](#markdown-formatting-guide)
6. [File Naming & Organization](#file-naming--organization)
7. [Code Examples](#code-examples)
8. [Testing Documentation](#testing-documentation)
9. [Submission & Review Workflow](#submission--review-workflow)
10. [Common Contribution Types](#common-contribution-types)

---

## Welcome Contributors

We appreciate contributions to Ante documentation! Whether you're:

- **Fixing typos and clarifications**: Help improve clarity
- **Adding examples**: Help other developers learn
- **Writing guides**: Share your knowledge
- **Improving organization**: Help users find what they need
- **Reporting issues**: Help us find gaps and errors

You can make Ante documentation better for everyone.

### Types of Contributions We Welcome

- ✅ Typo and grammar corrections
- ✅ Clarifications and rewording
- ✅ New code examples
- ✅ New how-to guides
- ✅ Bug fixes and corrections
- ✅ Process improvements
- ✅ Issue reporting
- ✅ Feedback and suggestions

### Before You Start

**Check if contribution needed**:

1. Search existing documentation for similar content
2. Review open pull requests/issues
3. Check the roadmap for planned documentation
4. Ask in community channels if unsure

---

## Getting Started

### Prerequisites

- GitHub account
- Git installed locally
- Text editor (VS Code, Sublime, etc.)
- Basic markdown knowledge (resources below)

### Set Up Your Environment

#### 1. Fork & Clone Repository

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/ante-docs.git
cd ante-docs

# Add upstream remote for syncing
git remote add upstream https://github.com/AntigmaLabs/ante-docs.git
```

#### 2. Create Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout upstream/main

# Create your branch
git checkout -b docs/your-contribution-name

# Branch naming convention:
# - docs/fix-typo-in-auth
# - docs/add-example-jwt-tokens
# - docs/improve-getting-started
# - docs/new-guide-performance-tuning
```

#### 3. Install Tools

```bash
# Install linting tools
npm install

# Or with yarn
yarn install

# Verify setup
npm run lint:docs
npm run check:links
```

### Local Preview

```bash
# Start local documentation server
npm run docs:serve

# Builds and serves at http://localhost:8000
# Auto-reloads on file changes

# Run validation
npm run docs:validate
npm run docs:test-examples
```

---

## Documentation Style Guide

### Voice & Tone

#### Principles

- **Clear**: Use simple, direct language
- **Helpful**: Assume reader wants to learn
- **Consistent**: Maintain consistent tone throughout
- **Respectful**: Treat all readers as capable learners

#### Voice Guidelines

**Do**:

- Use active voice: "Open the settings menu" (not "The settings menu should be opened")
- Use second person: "You can configure this by..." (not "The user can configure")
- Be direct: "Click the button" (not "It is possible to click the button")
- Use present tense: "The API returns data" (not "The API will return data")

**Don't**:

- Use first person plural: "We recommend" (unless representing Ante team officially)
- Use passive voice: "The file must be created" (use "Create the file")
- Be condescending: Assume reader intelligence
- Use jargon without explanation

#### Tone Examples

**API Reference** (Precise, technical):

```
✅ `authenticate(credentials: Credentials): Promise<Token>`
   Authenticates the user and returns an authentication token.

❌ `authenticate(credentials: Credentials): Promise<Token>`
   This function authenticates a user and returns a token for later use.
```

**How-To Guide** (Practical, encouraging):

```
✅ Set up authentication in three steps:
   1. [Step 1]
   2. [Step 2]
   3. [Step 3]

❌ Authentication setup is a process that involves several steps which you'll follow below.
```

**Conceptual Guide** (Educational, exploratory):

```
✅ Authentication is the process of verifying user identity. In Ante, we use JWT tokens
   because they're stateless and scalable. Here's how they work: [explanation]

❌ In this section we will discuss the concept of authentication and specifically JWT tokens.
```

### Word Choice & Terminology

#### Consistent Terminology

Create and maintain a glossary of terms. Example:

```
- use "configure" consistently (not "set up", "adjust", "modify")
- use "API" not "api" in text
- use "JavaScript" not "Javascript" or "JS" in formal docs
- use "user" not "developer" when generic
```

#### Avoid Ambiguous Terms

| Avoid                         | Use Instead                                     |
| ----------------------------- | ----------------------------------------------- |
| "it" without clear antecedent | Repeat noun or use specific term                |
| "basically", "simply", "just" | Remove - these diminish complexity              |
| "obviously", "clearly"        | These assume reader knowledge - explain instead |
| "can be done"                 | Be specific: "click X" or "use function Y"      |
| "should"                      | Use "must" (required) or "consider" (optional)  |

#### Explanation of Technical Terms

First use of technical term:

```
✅ This uses JSON Web Tokens (JWTs), which are encrypted tokens that contain
   user information. JWTs are stateless, meaning...

❌ This uses JWTs.
```

### Inclusive Language

- Use "they/them" for singular pronouns
- Avoid gendered language: "developer" instead of "he/she"
- Use "blocklist" instead of "blacklist", "allowlist" instead of "whitelist"
- Provide examples showing diverse use cases and contexts

---

## Writing Standards

### Clarity Standards

#### Sentence Length

- **Target**: 15-20 words average
- **Maximum**: 30 words (exceptions for complex syntax)
- **Readability Goal**: Flesch-Kincaid 8.0+

#### Paragraph Structure

- **Opening**: Topic sentence stating main idea
- **Body**: 2-4 supporting sentences
- **Closing**: Transition or summary (optional)
- **Length**: 3-5 sentences typical

#### Complexity Management

For complex concepts:

1. Start with simple explanation
2. Add important caveats
3. Provide concrete example
4. Link to deeper resources

```markdown
# Conceptual Explanation Template

[Simple explanation - 1-2 sentences]

**Important**: [Key distinction or warning]

[Detailed explanation - add complexity here]

**Example**:
[Concrete, runnable example]

**Learn more**:

- [Link to related concept]
- [Link to detailed reference]
```

### Content Completeness

Every documentation section should answer:

- **What**: What is this feature/concept/API?
- **Why**: Why would I use this? What problems does it solve?
- **How**: How do I use it? Step-by-step or example?
- **When**: When should I use this vs. alternatives?
- **Cautions**: What are limitations or common mistakes?

#### Completeness Checklist

```markdown
## Section Completeness Checklist

### Content

- [ ] Opening explains purpose/scope
- [ ] Prerequisites listed
- [ ] All major points covered
- [ ] Examples provided
- [ ] Limitations/cautions noted
- [ ] Key terms explained
- [ ] Related topics linked

### Accuracy

- [ ] Information matches current behavior
- [ ] Code examples tested
- [ ] API signatures correct
- [ ] Warnings/notes accurate

### Clarity

- [ ] No ambiguous pronouns
- [ ] Consistent terminology
- [ ] Sentences clear and concise
- [ ] Logical flow/structure

### Completeness

- [ ] Answers "What/Why/How/When"
- [ ] Addresses common questions
- [ ] Sufficient for target audience
- [ ] No gaps or TODOs
```

---

## Markdown Formatting Guide

### File Headers

Every documentation file must include:

```markdown
---
version: 1.0.0
last_updated: 2026-02-20
status: active
maintained_by: [Your Name]
---

# Document Title

Brief description of what's covered.
```

### Headers & Organization

```markdown
# H1 - Main Title (Only One Per File)

Main concept or section title.

## H2 - Major Sections

Subsections of the main topic.

### H3 - Subsections

Topics within major sections.

#### H4 - Details

Use sparingly; usually prefer H3 or bullet lists.
```

**Guidelines**:

- Only one H1 per document
- Use sequential header levels (no jumping from H2 to H4)
- Make headers descriptive (not "Overview", but "Architecture Overview")
- Headers should be self-contained statements

### Lists

#### Unordered Lists

Use for items without order:

```markdown
Core features:

- Item 1
- Item 2
- Item 3
```

#### Ordered Lists

Use for sequential steps:

```markdown
Steps to configure:

1. Open settings
2. Navigate to auth
3. Set token expiration
4. Save changes
```

#### Nested Lists

```markdown
Main features:

- Feature 1
  - Subfeature 1.1
  - Subfeature 1.2
- Feature 2
```

#### Task Lists

For checklists (especially in guides):

```markdown
## Setup Checklist

- [x] Install Ante
- [ ] Create configuration
- [ ] Run example
- [ ] Deploy to production
```

### Code Blocks

#### Syntax Highlighting

```markdown
\`\`\`javascript
// Language identifier required for syntax highlighting
const result = someFunction();
console.log(result);
\`\`\`

\`\`\`bash

# For shell commands

npm install
npm run build
\`\`\`

\`\`\`yaml

# For configuration files

config:
auth: enabled
timeout: 30
\`\`\`
```

**Supported Languages**: javascript, typescript, python, bash, yaml, json, html, css, sql, java, go, rust, etc.

#### Inline Code

Use backticks for code in text:

```markdown
✅ Use the `authenticate()` function to create a session.

❌ Use the authenticate() function to create a session.
```

#### Diff Blocks

For showing changes:

```markdown
\`\`\`diff
function example() {

- const old = value;

* const new = value;
  return result;
  }
  \`\`\`
```

### Emphasis

```markdown
**Bold** for emphasis on words
_Italic_ for emphasis on concepts

❌ Don't use bold for every important word
```

### Blockquotes & Callouts

#### Standard Quotes

```markdown
> This is a blockquote, useful for quotes or background information.
> Can span multiple lines.
```

#### Important Callouts

```markdown
⚠️ **Warning**: This action cannot be undone.

💡 **Tip**: You can optimize this by using...

ℹ️ **Note**: This feature requires version 1.2+

✅ **Success**: Configuration is complete.

❌ **Error**: Common mistake to avoid.
```

### Links

```markdown
# Internal links

[Related API](./api-reference.md)
[Getting Started Guide](../guides/getting-started.md)

# External links

[Ante Website](https://antigma.ai)

# Auto-linking in references

Use `authenticate()` (links to API reference when available)

# Avoid bare URLs

✅ [Learn about authentication](https://docs.antigma.ai/auth)
❌ See https://docs.antigma.ai/auth
```

**Internal Link Guidelines**:

- Use relative paths: `./file.md` not absolute URLs
- Include file extensions: `.md` not no extension
- Link to relevant sections using anchors when helpful

### Tables

```markdown
| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Data 1.1 | Data 1.2 | Data 1.3 |
| Data 2.1 | Data 2.2 | Data 2.3 |
```

**Guidelines**:

- Keep rows under 3 columns for readability
- For complex data, consider a code block instead
- Use descriptive headers

### Images & Diagrams

**Guidelines for images**:

```markdown
![Alt text describing image](./path/to/image.png)
_Caption under image if needed_
```

**Alt Text Requirements**:

- Describe what the image shows
- Be specific: "Login form with email and password fields" not "form"
- Include relevant context for accessibility

**For Diagrams**:

- Use ASCII art for simple diagrams
- Use code blocks for better formatting
- Consider Mermaid or PlantUML for complex diagrams

```markdown
\`\`\`
┌─────────────┐
│ User │
└──────┬──────┘
│
▼
┌─────────────┐
│ Ante API │
└──────┬──────┘
│
▼
┌─────────────┐
│ Database │
└─────────────┘
\`\`\`
```

---

## File Naming & Organization

### Directory Structure

```
documentation/
├── core/
│   ├── architecture.md
│   ├── concepts.md
│   └── security.md
├── guides/
│   ├── getting-started.md
│   ├── authentication.md
│   └── performance.md
├── api-reference/
│   ├── auth.md
│   ├── config.md
│   └── utils.md
├── examples/
│   ├── basic-setup.js
│   ├── auth-jwt.js
│   └── performance-tuning.js
└── troubleshooting/
    ├── common-issues.md
    └── faq.md
```

### File Naming Conventions

**Markdown Files** (`*.md`):

- Use kebab-case (lowercase with hyphens): `authentication-setup.md`
- Be descriptive: `jwt-implementation.md` not `jwt.md`
- Use verbs for guides: `setup-database.md`, `configure-auth.md`
- Use nouns for reference: `api-reference.md`, `architecture.md`

**Code Examples** (`*.js`, `*.py`, etc.):

- Use kebab-case: `auth-with-jwt.js`
- Include context: `stripe-integration-example.js` not `example.js`
- Use consistent language per section

**Asset Files**:

- Images: `getting-started-diagram.png`
- Data: `sample-config.json`
- No spaces or special characters

### Organizing Content

**Within Directories**:

```
guides/
├── README.md              # Index of all guides
├── getting-started.md
├── basic-setup.md
├── advanced-setup.md
└── troubleshooting.md
```

**Cross-Document Structure**:

```
Core concept documentation → How-to guides → Examples → API reference → Troubleshooting
```

---

## Code Examples

### Example Requirements

Every code example must:

- ✅ Actually run and produce expected output
- ✅ Be relevant and realistic
- ✅ Not require hidden setup or prerequisites
- ✅ Include comments explaining key points
- ✅ Follow the language's conventions

### Writing Runnable Examples

```javascript
/**
 * Example: Authentication with JWT Tokens
 *
 * This example shows how to authenticate a user
 * and use the returned JWT token for subsequent requests.
 *
 * Prerequisites: Ante version 1.2.0+
 * Runtime: Node.js 14+
 */

// 1. Create a new user session
const session = await ante.auth.createSession({
  email: "user@example.com",
  password: "secure-password",
});

// 2. The session includes a JWT token
console.log("Token:", session.token);
// Output: Token: eyJhbGc...

// 3. Use the token in subsequent requests
const data = await ante.api.get("/user/profile", {
  headers: { Authorization: `Bearer ${session.token}` },
});

console.log("User:", data.email);
// Output: User: user@example.com
```

### Example Variations

**Complete Example** (Full, self-contained):

```javascript
// Full working example
// Can run as-is
// ~20 lines typical
```

**Snippet Example** (Focused on one concept):

```javascript
// Shows specific pattern
// May require setup from guide
// ~5 lines typical
```

**Comparison Example** (Show right vs. wrong):

```javascript
// ❌ Don't do this
const result = unsafeApproach();

// ✅ Do this instead
const result = safeApproach();
```

### Example Templates

#### Basic API Usage

```javascript
/**
 * Example: [Feature] - [Use Case]
 */

// Setup (if needed)
const [requirement] = requireSetup();

// Example usage
const result = ante.module.function(params);

// Verify results
console.log(result);
// Expected output: [what to expect]

// Common variations
const variant = ante.module.function(alternateParams);
```

#### Configuration Example

```javascript
/**
 * Example: [Feature] - Configuration
 */

const config = {
  // Required settings
  apiKey: process.env.ANTE_API_KEY,

  // Optional settings
  timeout: 30000,
  retries: 3,
  logLevel: "debug",
};

const ante = new Ante(config);
```

#### Error Handling Example

```javascript
/**
 * Example: [Feature] - Error Handling
 */

try {
  const result = await ante.operation();
  console.log("Success:", result);
} catch (error) {
  if (error.code === "AUTH_FAILED") {
    // Handle authentication error
    console.error("Authentication failed:", error.message);
  } else {
    // Handle other errors
    console.error("Operation failed:", error.message);
  }
}
```

### Example Testing

All examples must be tested before submission:

```bash
# Run example
node examples/your-example.js

# Verify output matches expected
# Output should be readable and make sense
```

**Output Requirements**:

- No errors or stack traces (unless demonstrating error handling)
- Output clearly shows what happened
- Includes expected console output in comments

---

## Testing Documentation

### Before Submitting

#### Code Example Testing

```bash
# Test your code examples
npm run docs:test-examples examples/your-example.js

# Or run manually
node examples/your-example.js
```

#### Link Validation

```bash
# Check all links in your file
npm run check:links documentation/your-file.md
```

#### Markdown Validation

```bash
# Validate markdown syntax
npm run lint:docs documentation/your-file.md
```

#### Style Checking

```bash
# Check for style/tone issues
npm run lint:style documentation/your-file.md
```

#### Full Validation

```bash
# Run all checks
npm run docs:validate
```

### Local Documentation Build

```bash
# Build documentation locally
npm run docs:build

# Serve locally
npm run docs:serve

# Visit http://localhost:8000 to view
# Look for your changes in the appropriate section
```

### Self-Review Checklist

Before submitting your contribution:

```markdown
## Pre-Submission Self-Review Checklist

### Content

- [ ] Information is accurate and current
- [ ] Code examples are tested and working
- [ ] All claims are supported with examples
- [ ] Tone is consistent with guidelines
- [ ] Content is appropriate for target audience

### Completeness

- [ ] Answers "What/Why/How/When"
- [ ] Prerequisites are clear
- [ ] Related topics are linked
- [ ] Examples provided where appropriate

### Writing Quality

- [ ] No typos or grammar errors
- [ ] Sentence length average 15-20 words
- [ ] Headers are clear and logical
- [ ] Terminology is consistent
- [ ] Voice is appropriate for section type

### Formatting

- [ ] Markdown syntax valid
- [ ] Links work and use relative paths
- [ ] Code blocks have syntax highlighting
- [ ] Lists and tables formatted correctly
- [ ] File header included

### Standards Compliance

- [ ] File named correctly
- [ ] File placed in correct directory
- [ ] All validation checks pass
- [ ] Examples run successfully
- [ ] No broken links

### Readiness

- [ ] Ready for technical review
- [ ] Ready for editorial review
- [ ] No outstanding TODOs
- [ ] All tests pass locally
```

---

## Submission & Review Workflow

### Step 1: Prepare Your Contribution

```bash
# Update your branch with latest changes
git fetch upstream
git rebase upstream/main

# Stage your changes
git add documentation/your-file.md

# Commit with clear message
git commit -m "docs: add guide for feature X

- Covers setup, configuration, and common use cases
- Includes 3 working examples
- Tested against version 1.2.3"
```

**Commit Message Format**:

```
docs: [brief description]

[Detailed explanation if needed]

- [Change 1]
- [Change 2]
```

### Step 2: Push & Create Pull Request

```bash
# Push your branch
git push origin docs/your-contribution-name
```

Create pull request on GitHub with:

**Title**: `docs: Brief description of change`

**Description**:

```markdown
## Change Summary

Brief description of what this PR adds or improves.

## Type of Change

- [ ] Typo/grammar fix
- [ ] Clarification
- [ ] New documentation
- [ ] Example/code addition
- [ ] Reorganization

## Related Issues

Closes #[issue number] (if applicable)

## Testing

- [x] Code examples tested
- [x] Links verified
- [x] Markdown validated
- [x] No broken links

## Checklist

- [x] Follows style guide
- [x] Self-reviewed
- [x] Ready for review
```

### Step 3: Review Process

**Timeline**:

- **Simple changes** (typos, small clarifications): 1-3 days
- **Medium changes** (new sections, guides): 3-5 days
- **Complex changes** (major reorganization): 5-10 days

**Review Stages**:

1. **Automated Checks** (Immediate)
   - Markdown validation
   - Link checking
   - Example execution
   - Linting

2. **Technical Review** (SME/Maintainer)
   - Accuracy verification
   - Example testing
   - Completeness check
   - API consistency

3. **Editorial Review** (Content Editor)
   - Clarity assessment
   - Tone consistency
   - Grammar/spelling
   - Organization

### Step 4: Address Feedback

**When you receive review feedback**:

1. Read all comments carefully
2. Respond to questions or clarifications needed
3. Make requested changes
4. Push updates to same branch
5. Mark conversations as resolved

**Common feedback types**:

| Feedback               | How to Respond                               |
| ---------------------- | -------------------------------------------- |
| "Please clarify..."    | Add explanation, example, or linked resource |
| "Can you add example?" | Create working example following guidelines  |
| "Link is broken"       | Test link locally, fix relative path         |
| "Code needs testing"   | Test locally, confirm with output            |
| "Tone seems off"       | Revise to match style guide                  |

### Step 5: Approval & Merge

When approved:

- Maintainer will merge your PR
- Your contribution is now part of Ante documentation
- You'll be added to contributors list (if applicable)

### Step 6: Post-Merge

After merge:

- Changes are deployed to documentation site
- Changes included in next llms.txt generation
- Celebrate your contribution! 🎉

---

## Common Contribution Types

### 1. Fix a Typo or Grammar Error

**Process**:

1. Find the typo/error
2. Edit the file directly
3. Test markdown validation passes
4. Create PR with clear title: `docs: fix typo in [filename]`
5. Maintainer approves and merges

**Example PR**:

```
Title: docs: fix typo in getting-started guide
Description: Changed "configurations" → "configure"
```

### 2. Clarify Existing Documentation

**Process**:

1. Identify unclear section
2. Rewrite for clarity
3. Ensure new version still accurate
4. Test validation passes
5. Create PR: `docs: clarify [topic] in [section]`

**Example PR**:

```
Title: docs: clarify JWT token expiration in auth guide
Description: Added explanation of token lifecycle and refresh mechanism
```

### 3. Add a Code Example

**Process**:

1. Choose appropriate section
2. Write runnable example
3. Test example runs successfully
4. Add to documentation
5. Create PR: `docs: add example for [feature]`

**Checklist**:

- [ ] Example runs without modification
- [ ] Output clearly shows feature works
- [ ] Comments explain key concepts
- [ ] Related to existing documentation

### 4. Write a How-To Guide

**Process**:

1. Choose topic (check if already exists)
2. Plan content structure (What, Why, How, When)
3. Write following style guide
4. Create working examples
5. Test everything runs
6. Create PR: `docs: add how-to guide for [topic]`

**What To Include**:

- Clear objective
- Prerequisites
- Step-by-step instructions
- Working example
- Troubleshooting (if applicable)
- Related documentation links

### 5. Improve Documentation Organization

**Process**:

1. Identify organizational issue
2. Propose new structure
3. Update file paths and links
4. Test all links work
5. Create PR explaining changes

**Example**:

```
Title: docs: reorganize guides by skill level
Description:
- Move advanced guides to advanced/ folder
- Update navigation
- Update all cross-references
- No content changes, organization only
```

### 6. Report a Documentation Issue

**When to report**:

- Inaccurate information
- Broken examples
- Missing documentation
- Confusing explanations
- Outdated content

**How to report**:

Create an issue with template:

```markdown
## Issue: [Brief Title]

**Type**:

- [ ] Inaccuracy
- [ ] Broken example
- [ ] Missing documentation
- [ ] Unclear explanation
- [ ] Outdated content

**Description**:
[Detailed description of problem]

**Location**:
File: [filename]
Section: [section name]

**Example**:
[If applicable, provide example of issue]

**Suggested Fix**:
[Optional suggestion for correction]
```

---

## Getting Help

### Documentation Questions

- **Comment in PR**: Ask questions in pull request comments
- **GitHub Issues**: Create an issue with [question] tag
- **Community Channels**: Ask in community forums/chat

### Contribution Questions

- **Review Guidelines**: See DOCUMENTATION_GOVERNANCE.md
- **Technical Help**: Ask in pull request or create issue
- **Process Questions**: Contact documentation coordinator

### Resources

- [Markdown Guide](https://www.markdownguide.org/)
- [Writing for Tech Documentation](https://developers.google.com/tech-writing)
- [Style Guides](https://github.com/google/styleguide)
- [Ante Documentation](https://docs.antigma.ai)

---

## Recognition

Contributors are recognized:

- In PR merge commit
- In CONTRIBUTORS.md file
- In release notes (for major contributions)
- In documentation site contributor section

### Levels of Contribution

**Level 1 - Typos & Minor Fixes** (1-5 contributions):

- Fixed typos, grammar, formatting
- Small clarifications

**Level 2 - Regular Contributor** (5-20 contributions):

- Added guides
- Improved sections significantly
- Fixed major issues

**Level 3 - Core Contributor** (20+ contributions):

- Multiple guides
- Significant reorganization
- Community leader

---

## Code of Conduct

All contributors agree to:

- Be respectful and inclusive
- Provide constructive feedback
- Accept feedback gracefully
- Follow the documentation standards
- Help create welcoming environment

---

## Thank You!

Thank you for contributing to Ante documentation. Your work helps developers around the world use Ante more effectively. We're grateful for your time and effort!

Have questions? Feel free to:

- Comment on issues
- Ask in pull requests
- Reach out to the maintainers
- Join community discussions

Happy documenting! 📝
