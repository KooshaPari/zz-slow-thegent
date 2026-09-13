# SPEC: Routing System

## Table of Contents

1. Overview
2. Architecture
3. HTTP Routing
4. Middleware
5. Load Balancing
6. Examples

## Overview

Layer 7 HTTP routing with middleware support and load balancing.

## Architecture

```
Request
├── Middleware Chain
│   ├── Logging
│   ├── Authentication
│   └── Rate Limiting
└── Handler
    └── Response
```

## HTTP Routing

```go
router := core.NewRouter()
router.Handle("GET", "/api/users", getUsersHandler)
router.Handle("POST", "/api/users", createUserHandler)
```

## Middleware

```go
func LoggingMiddleware(next HandlerFunc) HandlerFunc {
    return func(c Context) error {
        start := time.Now()
        err := next(c)
        slog.Info("request", "duration", time.Since(start))
        return err
    }
}
```

## Load Balancing

```go
lb := core.NewRoundRobin()
backend := lb.Select(backends)
```

## Examples

```go
// Create router
r := core.NewRouter()

// Add middleware
r.Use(core.LoggingMiddleware())
r.Use(core.AuthMiddleware())

// Add routes
r.GET("/health", healthHandler)
r.GET("/api/*", apiHandler)

// Start server
http.ListenAndServe(":8080", r)
```

---

_Specification Version: 1.0_
_Last Updated: 2026-04-05_
