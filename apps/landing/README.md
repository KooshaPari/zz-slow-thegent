# thegent landing

Production landing page at `thegent.kooshapari.com` for [KooshaPari/thegent](https://github.com/KooshaPari/thegent), the Python agent runtime and orchestration system in the Phenotype ecosystem.

## Purpose

`apps/landing` is the repo-owned Tier-2 brand surface for theGent. It gives the runtime a stable domain, pulls public project metadata at build time, and exposes path-based microfrontends for docs, QA, observability, and pull-request previews.

The site can still be mirrored to GitHub Pages at `https://kooshapari.github.io/thegent/`; links are generated through `src/lib/site.ts` so the Vercel custom-domain build and Pages base-path build both work.

## Architecture

- **Frontend:** Astro 6 static site
- **Styling:** Tailwind CSS 4 with Phenotype CSS tokens
- **Deployment:** Vercel plus GitHub Pages mirror
- **Domain:** `thegent.kooshapari.com` via Cloudflare CNAME
- **Data sources:** GitHub API, committed QA snapshots, PhenoObservability UI

## Local Development

### Prerequisites

- `bun` 1.0+
- Node.js 20+
- `git`

### Setup

```bash
task landing:install
task landing:dev
```

Local dev serves at `http://localhost:4321`.

### Build

```bash
task landing:build
task landing:preview
```

## Path Microfrontends

Per Phenotype org-pages policy, `thegent.kooshapari.com` hosts these surfaces:

| Path             | Status                        | Purpose                                                 |
| ---------------- | ----------------------------- | ------------------------------------------------------- |
| `/`              | Active                        | theGent overview, GitHub metadata, runtime proof panel  |
| `/docs`          | Active with fallback          | Renders thegent `docs/` tree from GitHub                |
| `/otel`          | Active, env-gated             | Embeds a public PhenoObservability UI                   |
| `/qa`            | Active with snapshot fallback | Shows project coverage, lint, and FR trace reports      |
| `/preview/<pr#>` | Active with fallback          | Canonical static redirect pages for landing PR previews |

## Environment Variables

```bash
# GitHub API, optional but recommended for build-time rate limits.
GITHUB_TOKEN=

# Observability iframe source for /otel.
PHENO_OTLP_UI_URL=

# Accepted alias for the same public PhenoObservability UI.
PHENO_OBSERVABILITY_UI_URL=
```

## Editing

- Main landing content: `src/pages/index.astro`
- Base-path URL helper: `src/lib/site.ts`
- Docs microfrontend: `src/pages/docs/[...slug].astro`
- OTel embed: `src/pages/otel/index.astro`
- QA dashboard: `src/pages/qa/index.astro`
- PR preview redirects: `src/pages/preview/[prNumber].astro`
- Shared design tokens: `src/styles/globals.css`

The shared visual base is GMK Arch teal (`#7ebab5`), aligned with the wider Phenotype landing-page family.

## Deployment

Vercel builds the custom-domain site from `main` with the project root set to `apps/landing`.

```bash
vercel --prod
```

Cloudflare DNS should point:

```text
CNAME thegent -> cname.vercel-dns.com
```

If a GitHub Pages mirror is kept, build with `GITHUB_PAGES=true`, which makes Astro emit URLs under `/thegent/`.

## Related

- [theGent](https://github.com/KooshaPari/thegent)
- [projects.kooshapari.com](https://github.com/KooshaPari/portfolio)
- [Site infrastructure](docs/governance/site-infrastructure.md)
