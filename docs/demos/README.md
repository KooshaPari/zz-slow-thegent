# Demo Scripts for VitePress Documentation

This directory contains demo scripts that are automatically converted to GIFs for the VitePress documentation.

## Structure

- `cli/` - VHS tape files (`.tape`) for terminal recordings
- `web/` - Playwright test scripts (`.ts`) for browser recordings

## Usage

Run the generation script:

```bash
./scripts/generate-demo-gifs.sh
```

Generated GIFs will be placed in `docs/public/assets/demos/` and can be referenced in documentation using the `<DemoGif>` component:

```vue
<DemoGif src="cli-demo.gif" alt="CLI Demo" caption="Running thegent commands" />
```

## VHS Tape Format

Create `.tape` files in `cli/` directory:

```tape
Output cli-demo.gif
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

Type "thegent run codex 'Hello world'"
Sleep 500ms
Enter
Sleep 2s
```

## Playwright Scripts

Create `.ts` files in `web/` directory:

```typescript
import { test } from "@playwright/test";

test("demo", async ({ page }) => {
  await page.goto("https://example.com");
  // ... record interactions
});
```

---

## See Also

- [VITEPRESS_RICH_DOCUMENTATION_IMPLEMENTATION_PLAN.md](../research/VITEPRESS_RICH_DOCUMENTATION_IMPLEMENTATION_PLAN.md) - Full implementation plan
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
