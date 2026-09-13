# Playwright Recording Setup for VitePress

This guide explains how to set up and use Playwright for browser recording and automation in VitePress documentation. Capture interactive feature demonstrations, create visual walkthroughs, and automate screenshot generation.

## Overview

**PlaywrightRecorder** provides a high-level wrapper around Playwright that simplifies:

- Browser automation (launch, navigation, interactions)
- Video recording with configurable quality
- Screenshot capture
- Error recovery and timeout handling
- Multi-browser support (Chromium, Firefox, WebKit)

Recordings are saved to `docs/recordings/outputs/` with accompanying metadata JSON files.

## Installation

Playwright is already included in the project dependencies:

```bash
# Already in pyproject.toml
pip install playwright>=1.50.0
```

Install browser binaries (run once):

```bash
python3 -m playwright install
```

For development:

```bash
# Install Node dependencies (VitePress, Playwright test)
bun install

# Or with pnpm/npm
pnpm install
# npm install
```

## Quick Start

### 1. Start VitePress Development Server

Open a terminal and start the dev server (keep it running):

```bash
bun run docs:dev
# Or: pnpm docs:dev, npm run docs:dev
```

This starts the VitePress dev server at `http://localhost:5173`

### 2. Record a Demo

Create a Python script to record interactions:

```python
import asyncio
from pathlib import Path
from thegent.doc_tools import PlaywrightRecorder, RecordingConfig


async def record_demo():
    config = RecordingConfig(
        base_url="http://localhost:5173",
        output_dir=Path("docs/recordings/outputs"),
    )

    async with PlaywrightRecorder(config) as recorder:
        result = await recorder.record_feature(
            feature_name="my-feature",
            route="/guides/my-feature/",
            interactions=[
                ("click", "button#start"),
                ("type", "input#query", "example text"),
                ("wait", 1000),
            ],
        )

        if result.success:
            print(f"Success! Screenshots: {result.screenshot_paths}")
        else:
            print(f"Failed: {result.error}")


# Run the recording
asyncio.run(record_demo())
```

### 3. View Results

Recordings are saved to `docs/recordings/outputs/` with:

- **Screenshots**: `screenshot_*.png`
- **Videos**: `video_*.webm` (if enabled)
- **Metadata**: JSON files with recording details

## API Reference

### RecordingConfig

Configuration class for recording sessions.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | `http://localhost:5173` | Base URL for navigation |
| `browser` | str | `chromium` | Browser engine (chromium, firefox, webkit) |
| `headless` | bool | `False` | Run browser headless mode |
| `viewport_width` | int | 1280 | Viewport width (px) |
| `viewport_height` | int | 720 | Viewport height (px) |
| `device_scale_factor` | float | 1.0 | DPI/scale factor |
| `locale` | str | `en-US` | Browser locale |
| `timezone_id` | str | `America/New_York` | Browser timezone |
| `output_dir` | Path | `docs/recordings` | Output directory for recordings |

**Example:**

```python
config = RecordingConfig(
    browser="firefox",
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    output_dir=Path("docs/recordings/custom"),
)
```

### PlaywrightRecorder

Main class for browser automation and recording.

#### Initialization

```python
async with PlaywrightRecorder(config) as recorder:
    # Use recorder here
    pass
```

#### Interaction Methods

**Navigation:**

```python
await recorder.navigate("/path/to/page")
await recorder.navigate("http://example.com/page")
```

**Click:**

```python
await recorder.click("button#submit")
await recorder.click(".dialog-button", button="right")
```

**Type/Fill Text:**

```python
await recorder.type_text("input#username", "john_doe")
await recorder.fill("input[name='email']", "john@example.com")
```

**Press Keys:**

```python
await recorder.press("input#search", "Enter")
await recorder.press("input#query", "Escape")
```

**Wait for Elements:**

```python
await recorder.wait_for_selector("button.ready")
await recorder.wait_for_function("() => document.querySelectorAll('[data-ready]').length > 0")
```

**Wait for Time:**

```python
await recorder.wait(1000)  # Wait 1000ms
```

**Evaluate JavaScript:**

```python
result = await recorder.evaluate("document.title")
text = await recorder.get_text_content("span.status")
```

**Take Screenshots:**

```python
path = await recorder.screenshot()
path = await recorder.screenshot("step-one")
```

#### High-Level Recording Methods

**Record Single Feature:**

```python
result = await recorder.record_feature(
    feature_name="seed-detection",
    route="/guides/seed-detection/",
    interactions=[
        ("click", "button#start"),
        ("type", "input#seed", "example_seed"),
        ("wait", "span.results"),
    ],
    initial_wait_ms=2000,
    description="Seed detection workflow",
)

print(f"Success: {result.success}")
print(f"Screenshots: {result.screenshot_paths}")
print(f"Duration: {result.duration}s")
```

**Record Multi-Step Workflow:**

```python
result = await recorder.record_page_flow(
    flow_name="checkout",
    description="E-commerce checkout workflow",
    steps=[
        {
            "navigate": "/checkout",
            "wait_ms": 1000,
        },
        {
            "actions": [
                ("fill", "input[name='email']", "user@example.com"),
                ("fill", "input[name='address']", "123 Main St"),
            ],
            "screenshot": "checkout-form",
        },
        {
            "actions": [
                ("click", "button.continue"),
                ("wait", "[data-step='payment']"),
            ],
            "screenshot": "payment-step",
        },
    ],
)
```

#### Recording Results

```python
# Result contains:
result.success  # bool - Did recording succeed?
result.video_path  # Optional[Path] - Path to recorded video
result.screenshot_paths  # list[Path] - Screenshot file paths
result.metadata  # dict - Recording metadata
result.error  # Optional[str] - Error message if failed
result.duration  # float - Recording duration in seconds
result.timestamp  # str - ISO timestamp

# Export as JSON
json_str = result.to_json()
result.to_json(Path("recordings/result.json"))  # Save to file
```

## Examples

### Example 1: Simple Button Click

```python
from pathlib import Path
from thegent.doc_tools import PlaywrightRecorder, RecordingConfig


async def simple_demo():
    config = RecordingConfig(output_dir=Path("docs/recordings/outputs"))

    async with PlaywrightRecorder(config) as recorder:
        await recorder.navigate("/demo")
        await recorder.click("button.start")
        await recorder.wait(2000)
        screenshot = await recorder.screenshot("button-clicked")
        print(f"Screenshot: {screenshot}")


# Run with: asyncio.run(simple_demo())
```

### Example 2: Form Filling

```python
async def form_demo():
    config = RecordingConfig(output_dir=Path("docs/recordings/outputs"))

    async with PlaywrightRecorder(config) as recorder:
        result = await recorder.record_feature(
            feature_name="form-submission",
            route="/contact",
            interactions=[
                ("fill", "input[name='name']", "John Doe"),
                ("fill", "input[name='email']", "john@example.com"),
                ("type", "textarea[name='message']", "Hello world!", None),
                ("click", "button[type='submit']"),
                ("wait", ".success-message"),
                ("sleep", "1000"),
            ],
        )

        if result.success:
            result.to_json(Path("docs/recordings/form-demo.json"))
```

### Example 3: Multi-Browser Recording

```python
from thegent.doc_tools import RecordingConfig


async def record_all_browsers():
    for browser in ["chromium", "firefox", "webkit"]:
        config = RecordingConfig(
            browser=browser,
            output_dir=Path(f"docs/recordings/outputs/{browser}"),
        )

        async with PlaywrightRecorder(config) as recorder:
            result = await recorder.record_feature(
                feature_name=f"demo-{browser}",
                route="/demo",
                interactions=[
                    ("click", "button.start"),
                    ("wait", 2000),
                ],
            )
            print(f"{browser}: {result.success}")
```

## Playwright Config

The `playwright.config.ts` file configures Playwright test runner:

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './recordings',
  webServer: {
    command: 'bun run docs:dev',
    url: 'http://localhost:5173',
  },
  use: {
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
})
```

Run Playwright tests:

```bash
# Run all tests
npx playwright test

# Run specific test
npx playwright test recordings/example.spec.ts

# Run in debug mode
npx playwright test --debug

# Generate new tests
npx playwright codegen http://localhost:5173
```

## VitePress Integration

The `docs/.vitepress/config.ts` is already configured with necessary plugins:

```typescript
import { OramaPlugin } from '@orama/plugin-vitepress'
import { imagetools } from 'vite-imagetools'

// In defineConfig:
vite: {
  plugins: [
    OramaPlugin(),  // Search
    imagetools(),   // Image optimization
  ],
}
```

To embed recorded videos in documentation:

```markdown
<video width="100%" controls>
  <source src="/recordings/demo.webm" type="video/webm">
  Your browser does not support the video tag.
</video>
```

## Troubleshooting

### Browser Not Found

```bash
# Install browser binaries
python3 -m playwright install
```

### Connection Refused

Make sure VitePress dev server is running:

```bash
bun run docs:dev
```

### Timeout Errors

Increase timeout in config:

```python
config = RecordingConfig(
    http_timeout=60000,  # 60 seconds
    navigation_timeout=60000,  # 60 seconds
)
```

### Selector Not Found

Wait for the element before interacting:

```python
await recorder.wait_for_selector("button.dynamic")
await recorder.click("button.dynamic")
```

### Video Not Recording

Videos are only saved when context closes. Check output directory:

```bash
ls -la docs/recordings/outputs/
```

## Best Practices

1. **Start VitePress first**: Always run `bun run docs:dev` before recording
2. **Use descriptive names**: Use clear feature names like "seed-detection-workflow"
3. **Add waits**: Use `wait_for_selector` or `wait_ms` to handle dynamic content
4. **Save metadata**: Export recording metadata with `result.to_json()`
5. **Test locally first**: Use `headless=False` to see what the browser is doing
6. **Clean output**: Regularly remove old recordings from `docs/recordings/outputs/`

## Next Steps

- See [example_seed_detection.py](../../recordings/example_seed_detection.py) for complete working examples
- Review [Playwright documentation](https://playwright.dev/python/) for advanced features
- Check [VitePress documentation](https://vitepress.dev/) for embedding videos

## Related Documentation

- [VitePress Setup Guide](./VITEPPRESS_SETUP.md)
- [Documentation Index](../index.md)
