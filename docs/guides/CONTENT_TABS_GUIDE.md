# Content Tabs Component

The `ContentTabs` component provides tabbed content sections for switching between different content (e.g., different code language examples).

## Features

- Tab buttons with active state management
- Content panels that show/hide based on active tab
- Keyboard navigation (Arrow keys, Home, End)
- Responsive design with horizontal scrolling
- VitePress container plugin support (`::: tabs` syntax)
- Accessibility support (ARIA attributes, focus management)

## Usage

### Vue Component

```vue
<script setup lang="ts">
import { ref } from 'vue'

const tabs = [
  { id: 'python', label: 'Python' },
  { id: 'javascript', label: 'JavaScript' },
  { id: 'typescript', label: 'TypeScript' },
]

const activeTab = ref('python')
</script>

<template>
  <ContentTabs :tabs="tabs" v-model="activeTab">
    <template #tab-python>
      ```python
      print("Hello from Python!")
      ```
    </template>
    <template #tab-javascript>
      ```javascript
      console.log("Hello from JavaScript!");
      ```
    </template>
    <template #tab-typescript>
      ```typescript
      console.log("Hello from TypeScript!");
      ```
    </template>
  </ContentTabs>
</template>
```

### Markdown Container Syntax

Use the `::: tabs` container syntax in markdown files:

```markdown
::: tabs

::: tab python
~~~~python
print("hello")
~~~~
:::

::: tab javascript
~~~~javascript
console.log("hello")
~~~~
:::

::: tab typescript
~~~~typescript
console.log("hello")
~~~~
:::

:::
```

### Keyboard Navigation

- `Arrow Right` / `Arrow Down`: Move to next tab
- `Arrow Left` / `Arrow Up`: Move to previous tab
- `Home`: Jump to first tab
- `End`: Jump to last tab
- `Enter`: Activate focused tab

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `tabs` | `Tab[]` | Auto-detected | Array of tab objects with `id` and `label` |
| `modelValue` | `string` | First tab | Currently active tab ID |

### Tab Interface

```typescript
interface Tab {
  id: string
  label: string
}
```

## Slots

| Slot | Description |
|------|-------------|
| `tab-{id}` | Content for each tab panel |
| `default` | Fallback content if no named slots provided |

## Examples

### Code Examples with Different Languages

::: tabs

::: tab python
```python
def hello(name: str) -> str:
    """Greet the user."""
    return f"Hello, {name}!"


print(hello("World"))
```
:::

::: tab javascript
```javascript
/**
 * Greet the user.
 * @param {string} name - The name to greet
 * @returns {string} The greeting
 */
function hello(name) {
  return `Hello, ${name}!`;
}

console.log(hello("World"));
```
:::

::: tab typescript
```typescript
/**
 * Greet the user.
 * @param name - The name to greet
 * @returns The greeting
 */
function hello(name: string): string {
  return `Hello, ${name}!`;
}

console.log(hello("World"));
```
:::

:::

### Configuration Options Example

::: tabs

::: tab Environment Variables
```bash
# Set API key
export API_KEY="your-api-key"

# Enable debug mode
export DEBUG=true

# Set log level
export LOG_LEVEL=debug
```
:::

::: tab config.yaml
```yaml
# thegent configuration
api_key: ${API_KEY}
debug: ${DEBUG:-false}
log_level: ${LOG_LEVEL:-info}

# Provider settings
providers:
  default: claude
  fallback: gemini
```
:::

::: tab JSON
```json
{
  "api_key": "${API_KEY}",
  "debug": false,
  "log_level": "info",
  "providers": {
    "default": "claude",
    "fallback": "gemini"
  }
}
```
:::

:::
