# 00 — Implementation Foundation

## 1. Final Technology Stack (Fixed, No Ambiguity)

### Core Platform (Production Runtime)

Frontend:
- Next.js (React)
- TypeScript

Backend API:
- Node.js 20+
- TypeScript
- Fastify
- Zod (validation)

Database:
- PostgreSQL
- Prisma ORM

Queue / Background Jobs:
- Redis
- BullMQ

Realtime Layer:
- Backend WebSocket (ws)
- Frontend never connects directly to Bybit

Logging:
- pino (JSON logs)

Deployment:
- Docker Compose
- Nginx reverse proxy

Exchange Mode:
- DEMO and REAL supported in architecture
- MVP: REAL is disabled via feature flag

---

## 2. System Responsibility Boundaries

Core Platform Responsibilities:
- Bybit REST/WS integration
- Order execution
- Idempotency
- Reconciliation after reconnect
- Bot state machine execution
- Persisting BotRuns / BotEvents / Orders / Trades

Laboratory Responsibilities:
- Strategy research
- Backtesting
- Statistical analysis
- Parameter optimization
- Generating strategy recommendations

Laboratory does NOT:
- Execute live orders
- Connect directly to exchange

---

## 3. Data Contract for Laboratory

Core guarantees persistence of:
- Bot
- BotRun
- BotEvent
- Order
- Trade
- PositionSnapshot
- StrategyVersion

Laboratory reads data in read-only mode.

---

## 4. Bot Runtime FSM (Mandatory States)

States:
- CREATED
- RUNNING
- SIGNAL_GENERATED
- ORDER_PENDING
- ORDER_FILLED
- RECONCILING
- STOPPED
- ERROR
- TIMEOUT

Transitions must be explicit and validated.

---

## 5. Risk Policy (MVP)

- Max leverage (configurable)
- Max notional per bot
- Max concurrent bots per user
- Hard stop on abnormal state

---

## 6. Market Data Policy

- Core is single source of truth
- Laboratory never fetches exchange data directly

---

## 7. Architecture Principle

Core must remain minimal and stable.
Research environment may evolve independently.

This document freezes implementation decisions and enables direct development without architectural ambiguity.
