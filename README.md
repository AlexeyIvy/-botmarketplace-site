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

### Database migrations

After pulling new changes that include Prisma schema updates, regenerate the
client and apply migrations:

```bash
pnpm --filter @botmarketplace/api db:generate
pnpm --filter @botmarketplace/api db:migrate
```

`db:migrate` runs `prisma migrate deploy`, which applies all pending migrations
in order. If you need to create a **new** migration during development, use
`npx prisma migrate dev --name <name>` inside `apps/api/`.

### Strategy versioning

`StrategyVersion` rows are **immutable**. To update a strategy's DSL or
execution plan, create a new `StrategyVersion` with an incremented `version`
integer. This keeps a full audit trail and allows rollback.

### Bot aggregate

`Bot` is the executable unit that ties together a workspace, a specific
`StrategyVersion`, a symbol (e.g. BTCUSDT), and a timeframe. Each `BotRun`
belongs to a `Bot`. Deleting a `StrategyVersion` that is referenced by a bot is
blocked (`onDelete: Restrict`), while deleting a bot cascades to its runs.

### Bot runtime constraint

Only **one active bot run** is allowed per (workspace, symbol) pair. This is
enforced at the database level via a partial unique index on `BotRun` where
`state IN ('CREATED','QUEUED','STARTING','SYNCING','RUNNING')`. Attempting to
insert a second active run for the same workspace + symbol will raise a unique
violation error.

### API routing (dev vs prod)

**Dev:** The Next.js frontend on `:3000` proxies `/api/*` requests to the
Fastify API on `:4000` via `rewrites()` in `next.config.ts`. This avoids CORS
issues and lets the frontend use relative paths (`/api/v1/...`).

**Prod:** The rewrite is disabled (`NODE_ENV=production`). A reverse proxy
(nginx, Caddy, or cloud ingress) must route `/api/*` to the API service.
Example nginx config:

```nginx
server {
    listen 80;

    location /api/ {
        proxy_pass http://api:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://web:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

The frontend `api.ts` always uses relative paths (`/api/v1/...`), so no
`NEXT_PUBLIC_API_URL` is needed in production — just ensure the reverse proxy
routes correctly.

### pnpm `ignoredBuiltDependencies`

`pnpm-workspace.yaml` lists `@prisma/client`, `@prisma/engines`, `esbuild`,
`prisma`, and `sharp` in `ignoredBuiltDependencies`. This prevents pnpm from
running their post-install build scripts automatically, which avoids slow
installs and platform-specific compilation issues in CI. Prisma client
generation is handled explicitly via `pnpm --filter @botmarketplace/api db:generate`.

## Documentation

See [docs/README.md](docs/README.md) for full project documentation.
