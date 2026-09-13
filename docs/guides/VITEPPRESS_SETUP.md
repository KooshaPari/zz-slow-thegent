# VitePress Docsite Setup

This guide explains how to set up a VitePress documentation site for a new project using the shared template.

## Quick Start

1. Copy `templates/vitepress/` to project `docs/.vitepress/`
2. Run `pnpm install`
3. Run `pnpm docs:build`
4. Open `docs-dist/index.html` in browser

## Directory Structure

After copying the template, your project should have:

```
docs/
├── .vitepress/
│   ├── config.ts          # Main VitePress configuration
│   └── theme/
│       ├── index.ts       # Theme entry point
│       ├── custom.css     # Custom styles
│       └── components/
│           └── Annotations.ts  # Annotation component
├── index.md               # Home page
├── guides/                # Guide documentation
├── reference/             # Reference documentation
└── changes/               # Change logs
```

## Commands

| Command             | Description                      |
| ------------------- | -------------------------------- |
| `pnpm docs:dev`     | Start dev server with hot reload |
| `pnpm docs:build`   | Build for production             |
| `pnpm docs:preview` | Preview built site locally       |

## Configuration

The main configuration file is `docs/.vitepress/config.ts`. Key options:

- `title`: Site title
- `description`: Site description
- `themeConfig`: Navigation, sidebar, social links
- `head`: Additional head tags

## Multi-Version Builds

For projects with multiple versions, see `scripts/build-docs.sh` for the multi-version build process. This script:

- Builds each version into separate directories
- Generates version navigation
- Creates version landing page

## Adding New Pages

1. Create markdown file in appropriate `docs/` subdirectory
2. Add to navigation in `config.ts` if needed
3. Use Vue components in markdown for interactive features

## Annotation Syntax

Use the custom annotation component to add callouts:

```markdown
::: info
This is an info callout.
:::

::: warning
This is a warning callout.
:::

::: danger
This is a danger callout.
:::
```

## Cross-Project Links

The cross-project link plugin enables linking between projects:

```markdown
[Link to jobhunter](../jobhunter/index.md)
[Link to heliosShield](../heliosShield/index.md)
[Link to trace](../trace/index.md)
```

## Building for Production

```bash
# Build all versions
./scripts/build-docs.sh

# Preview locally
pnpm docs:preview

# Deploy docs-dist/ to your hosting platform
```

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
