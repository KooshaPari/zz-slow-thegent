# Core Library

This directory contains intentionally minimal shared utilities for the landing page.

## Purpose

Provides basic site configuration utilities used across the landing page application:

- `site.ts` - Base path configuration and site path helpers

## Design Philosophy

This lib is intentionally minimal by design. Landing pages have different concerns than application code and should remain lightweight. Avoid adding heavy dependencies or complex utilities here.

## Usage

```typescript
import { BASE_PATH, sitePath } from "@/lib";

const absolutePath = sitePath("/features");
// => '/features' or '/landing/features' depending on deployment
```

## Adding New Utilities

Before adding any new utility:

1. Consider if it belongs here or in a shared package
2. If it's only for the landing page, add it here
3. If it could be reused elsewhere, consider creating a shared package
4. Keep dependencies minimal - avoid adding runtime dependencies
