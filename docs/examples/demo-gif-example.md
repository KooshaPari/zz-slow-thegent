# Demo GIF Examples

This page demonstrates how to use the DemoGif component.

---

## CLI Demo

<DemoGif
  src="cli-demo.gif"
  alt="CLI Demo"
  caption="Running thegent CLI commands"
/>

---

## Web Demo

<DemoGif
  src="web-demo.gif"
  alt="Web Interface Demo"
  caption="Using thegent web interface"
/>

---

## Creating Demo GIFs

### Using VHS (Terminal Recordings)

1. Create a `.tape` file in `docs/demos/cli/`:

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

2. Generate GIF:

```bash
./scripts/generate-demo-gifs.sh
```

### Using Playwright (Browser Recordings)

1. Create a `.ts` file in `docs/demos/web/`:

```typescript
import { test } from "@playwright/test";

test("demo", async ({ page }) => {
  await page.goto("https://example.com");
  // ... record interactions
});
```

2. Generate GIF:

```bash
npx playwright test --gif
```

---

**See Also**:

- [VITEPRESS_USAGE_GUIDE.md](../guides/VITEPRESS_USAGE_GUIDE.md)
- [AUTOMATED_DEMOS.md](../guides/AUTOMATED_DEMOS.md)
