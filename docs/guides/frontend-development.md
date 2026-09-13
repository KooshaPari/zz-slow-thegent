# Frontend Development Guide

## Technology Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Next.js 16 App Router (Vercel)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React 19 + TypeScript 5.8                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ App Router  │  │  tRPC 11.7  │  │  Zustand    │  │  React     │  │   │
│  │  │ (Pages)     │  │  (API RPC)  │  │  (State)    │  │  Query 5   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         UI Layer                                     │   │
│  │  Shadcn/Radix UI + Tailwind CSS 3.4 + Framer Motion                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Supabase    │           │   WorkOS      │           │   Upstash     │
│  (PostgreSQL) │           │  (Auth SSO)   │           │   (Redis)     │
└───────────────┘           └───────────────┘           └───────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐           ┌───────────────┐
│ AtomsAgent    │           │ Google Vertex │
│ (FastAPI)     │           │ (AI/OCR)      │
└───────────────┘           └───────────────┘
```

## Key Architectural Features

- **Framework:** Next.js 16 with App Router, React 19, TypeScript 5.8.3
- **Styling:** Tailwind CSS 3.4.17 with Shadcn/Radix UI components
- **State Management:** Zustand 5.0.3 (client) + TanStack React Query 5.74 (server)
- **API Layer:** tRPC 11.7.1 for type-safe RPC
- **Database:** Supabase (PostgreSQL) with Row-Level Security (RLS)
- **Authentication:** WorkOS AuthKit 2.11.1 (Enterprise SSO/SAML)
- **Caching:** Upstash Redis (REST API) + Next.js Cache Components

## Project Structure

```
/src: Source Code
├── /app: Next.js App Router Pages
│   ├── /(auth): Authentication related pages
│   │   ├── /login - Login page
│   │   ├── /signup - Sign up page
│   │   ├── /auth - Auth flow pages
│   │   └── [other auth pages...]
│   │
│   ├── /(public): Public facing pages
│   │   └── [Public marketing and landing pages]
│   │
│   ├── /(protected): Protected routes requiring authentication
│   │   ├── /home - Dashboard/Home page
│   │   ├── /org - Organization pages
│   │   ├── /atomsagent - AtomsAgent interface
│   │   ├── /admin - Organization admin
│   │   ├── /marketplace - MCP server marketplace
│   │   └── [other protected routes...]
│   │
│   └── /api: API endpoints for AI processing
│       ├── /auth - Authentication endpoints
│       ├── /trpc - tRPC RPC endpoint
│       ├── /chat/v1 - Chat API endpoints
│       └── [other API routes...]
│
├── /components: UI Components (553 files)
│   ├── /custom: Custom UI components
│   │   ├── /chat - Chat/messaging UI
│   │   ├── /dashboard - Dashboard components
│   │   ├── /admin - Admin interface components
│   │   └── [other custom components...]
│   └── /ui: Shadcn/Radix UI primitives
│
├── /hooks: Custom React hooks (101 files)
│   ├── useAuth.ts - Authentication state
│   ├── useOrgDashboard.ts - Organization dashboard data
│   ├── useVertexOcr.ts - Google Vertex OCR
│   └── [other custom hooks...]
│
├── /lib: Utility functions and libraries
│   ├── /auth - Authentication utilities
│   ├── /cache - Cache/memoization patterns
│   ├── /database - Database query builders
│   ├── /trpc - tRPC client/server setup
│   └── [other utilities...]
│
├── /store: Zustand state management
│   ├── auth.store.ts - Auth state
│   ├── ui.store.ts - UI state (modals, panels)
│   ├── domain.store.ts - Domain data (org/project)
│   └── [other stores...]
│
├── /types: TypeScript type definitions
│   ├── /base - Base/primitive types
│   ├── /api - API response types
│   ├── /database - Database schema types
│   └── [other type definitions...]
│
├── /server: Server-side Logic (Node.js)
│   ├── /trpc - tRPC router setup
│   ├── /repositories - Data access layer
│   ├── /services - Business logic
│   └── [other server logic...]
│
└── /styles: Global CSS/Tailwind styles
```

## Development Setup

### Prerequisites

- Node.js 18+ (via Bun 1.2.22 package manager)
- PostgreSQL 13+ (via Supabase Cloud)

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/atoms-tech/atoms.tech.git
   cd atoms.tech
   ```

2. **Install dependencies**

   ```bash
   bun install
   ```

3. **Environment Setup**
   Copy environment variables from Coda (see onboarding checklist) into `.env.local`

   **Required Environment Variables:**
   - WorkOS credentials (WORKOS_API_KEY, WORKOS_CLIENT_ID, WORKOS_COOKIE_PASSWORD)
   - Supabase (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY)
   - Google Vertex AI (GCP_PROJECT_ID, GCP_REGION)
   - Redis (UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN)
   - AtomsAgent (ATOMSAGENT_BASE_URL)

4. **Run development server**

   ```bash
   bun dev
   ```

   Server runs on http://localhost:3000

5. **Code Quality**
   ```bash
   bun run lint
   bun prettier src --write
   ```

## Available npm Scripts

**Development:**

- `bun run dev` - Start dev server
- `bun run dev:clean` - Clean .next and start dev
- `bun run dev:log` - Dev with logging to file

**Building & Deployment:**

- `bun run build` - Production build
- `bun run build:analyze` - Build with bundle analysis
- `bun run start` - Start production server

**Code Quality:**

- `bun run lint` - Run ESLint
- `bun run lint:strict` - Lint with zero warnings
- `bun run type-check` - TypeScript type checking
- `bun run format` - Prettier formatting

**Testing:**

- `bun run test` - Run all tests
- `bun run test:unit` - Unit tests with Vitest + coverage
- `bun run test:e2e` - E2E tests with Playwright

## State Management with Zustand

Store structure for client-side state:

```typescript
// auth.store.ts - Authentication state
export const useAuthStore = create((set) => ({
  user: null,
  organization: null,
  permissions: [],
  setUser: (user) => set({ user }),
  // ...
}));

// ui.store.ts - UI state (modals, panels)
export const useUIStore = create((set) => ({
  isModalOpen: false,
  activeSidebar: null,
  // ...
}));

// domain.store.ts - Business domain state
export const useDomainStore = create((set) => ({
  currentProject: null,
  documents: [],
  // ...
}));
```

## API Integration with tRPC

Type-safe RPC calls:

```typescript
// Server-side procedure
export const appRouter = router({
  chat: {
    send: publicProcedure
      .input(z.object({ message: z.string() }))
      .mutation(async ({ input, ctx }) => {
        // Server logic
        return response;
      }),
  },
});

// Client-side usage
const { mutate } = trpc.chat.send.useMutation();
mutate({ message: "Hello!" });
```

## UI Components

Built on Shadcn/Radix UI with Tailwind CSS and Framer Motion:

- Form components (inputs, selects, checkboxes)
- Dialog/Modal components
- Navigation components
- Data display (tables, lists, cards)
- Feedback components (toasts, alerts)

## Deployment

Deployed on Vercel with automatic deployments from Git:

1. Push to main branch triggers deployment
2. Preview deployments for pull requests
3. Production builds optimized for performance

---

**Content merged from:** technical-documentation-frontend.md
