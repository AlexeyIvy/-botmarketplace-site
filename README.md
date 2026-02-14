# BotMarketplace

Trading terminal, AI strategy lab & bot factory for Bybit (demo-first).

## Quick start

### Prerequisites

- Node.js 20+ (`node -v`)
- pnpm 10+ (`pnpm -v`)
- Docker + Docker Compose (for Postgres and Redis)

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (port 5432) and Redis (port 6379).

### 2. Configure environment

```bash
cp .env.example .env
```

### 3. Install dependencies

```bash
pnpm install
```

### 4. Run database migrations

```bash
pnpm db:migrate
```

### 5. Start development servers

In separate terminals:

```bash
pnpm dev:api    # Backend API on http://localhost:4000
pnpm dev:web    # Frontend on http://localhost:3000
```

### 6. Verify

```bash
curl http://localhost:4000/api/healthz          # {"status":"ok"}
curl http://localhost:4000/api/readyz            # {"status":"ok"}
curl -X POST http://localhost:4000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123"}'
```

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

## Documentation

See [docs/README.md](docs/README.md) for full project documentation.
