# thegent landing /health spec

## Status: draft 2026-06-09

## Endpoint

### GET /health

- returns 200 {status: "ok", version: <pkg.version>}
- works in Vercel edge runtime
- uses Astro endpoint (apps/landing/src/pages/health.ts)
- reads version from `import { version } from "../../package.json" with { type: "json" }`
- static site (no SSR adapter in astro.config.mjs), so endpoint is pre-rendered to a JSON file at build time
- `Cache-Control: public, max-age=0, must-revalidate` to keep probes fresh

## Implementation

```ts
// apps/landing/src/pages/health.ts
import { version } from "../../package.json" with { type: "json" };
import type { APIRoute } from "astro";

export const prerender = true;

export const GET: APIRoute = () =>
  new Response(JSON.stringify({ status: "ok", version }), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "cache-control": "public, max-age=0, must-revalidate",
    },
  });
```

## Test plan

- curl https://thegent.kooshapari.com/health
- expect 200, content-type application/json, body `{"status":"ok","version":"0.1.0"}`
- local: `cd apps/landing && pnpm dev` then `curl localhost:4321/health`
