# BotMarketplace

Trading terminal, AI strategy lab & bot factory for Bybit (demo-first).

## Quick start

### Prerequisites

- Node.js 20+ (`node -v`)
- pnpm 10+ (`pnpm -v`)
- Docker + Docker Compose (for Postgres and Redis)

### 1. Install dependencies

```bash
pnpm i
```

### 2. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (port 5432) and Redis (port 6379).

### 3. Configure environment

```bash
cp .env.example .env
```

### 4. Generate Prisma client & run migrations

```bash
pnpm --filter @botmarketplace/api db:generate
pnpm --filter @botmarketplace/api db:migrate
```

### 5. Start development servers

In separate terminals:

```bash
pnpm --filter @botmarketplace/api dev    # Backend API on http://localhost:4000
pnpm --filter @botmarketplace/web dev    # Frontend on http://localhost:3000
```

### 6. Smoke checks

```bash
# Versioned endpoints (preferred)
curl http://localhost:4000/api/v1/healthz          # {"status":"ok"}
curl http://localhost:4000/api/v1/readyz            # {"status":"ok"}

# Auth stub
curl -X POST http://localhost:4000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123"}'
```

Legacy `/api/*` paths (without `/v1`) still work for backward compatibility
but will be removed in a future version.

Open http://localhost:3000 in browser to see the frontend.

## Project structure

```
apps/
  api/      Fastify backend (TypeScript)
  web/      Next.js frontend (TypeScript)
packages/
  shared/   Shared types and constants
docs/       Project documentation
```

## Notes

### pnpm `ignoredBuiltDependencies`

`pnpm-workspace.yaml` lists `@prisma/client`, `@prisma/engines`, `esbuild`,
`prisma`, and `sharp` in `ignoredBuiltDependencies`. This prevents pnpm from
running their post-install build scripts automatically, which avoids slow
installs and platform-specific compilation issues in CI. Prisma client
generation is handled explicitly via `pnpm --filter @botmarketplace/api db:generate`.

## Documentation

See [docs/README.md](docs/README.md) for full project documentation.
