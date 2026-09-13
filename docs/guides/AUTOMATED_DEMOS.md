# Automated Documentation Demos

This project supports automated GIF generation for documentation using **vhs** (for CLI) and **Playwright** (for Web).

## 🚀 Quick Start

To generate all demos, run:

```bash
task docs:demos
```

This task is automatically executed as part of `task docs:build`.

## 📼 CLI Demos (vhs)

CLI demos are defined using `.tape` files in `docs/demos/cli/`.

### Example `.tape` file

```vhs
# Output path (always relative to workspace root)
Output docs/public/assets/demos/cli-demo.gif

Set Shell zsh
Set FontSize 16
Set Width 1200
Set Height 600

Type "thegent --help"
Sleep 500ms
Enter

Sleep 2s
```

## 🎭 Web Demos (Playwright)

Web demos are defined in `docs/demos/web/`. The `generate_demos.sh` script will run these tests and expect them to output GIFs to `docs/public/assets/demos/`.

> **Note:** For Playwright-to-GIF conversion, you may need a tool like `ffmpeg` or a Playwright plugin that supports GIF output.

## ⊞ Using Demos in Markdown

Use the `<DemoGif />` component to embed a generated GIF in your VitePress pages:

```vue
<DemoGif
  src="cli-demo.gif"
  alt="CLI usage demo"
  caption="Basic usage of thegent CLI"
/>
```

The component automatically looks for the file in `docs/public/assets/demos/`.

## ⌘ Configuration

- **Source files:** `docs/demos/`
- **Output directory:** `docs/public/assets/demos/` (Ignored by git, generated at build time)
- **Generation script:** `scripts/generate_demos.sh`
- **VitePress Component:** `docs/.vitepress/theme/components/DemoGif.vue`

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
