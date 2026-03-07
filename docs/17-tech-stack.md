# Tech Stack (MVP v1 + Lab v2 approved additions)

Документ фиксирует технологический стек.
Раздел 1 — базовый MVP стек. Раздел 9 — одобренные дополнения для Lab v2 (добавляются по фазам, не являются полностью реализованными).
Выбор основан на: скорость разработки, единый язык (TypeScript), зрелость библиотек для Bybit/WS/queue, простота деплоя.

## 1) Frontend

- **Next.js 14+** (App Router) + **TypeScript**
- UI: React, CSS Modules / Tailwind (решение финализируется в Stage 1)
- Графики: lightweight-charts (TradingView) или аналог
- State: React Context + SWR/React Query для серверных данных
- i18n: next-intl (RU + EN)

## 2) Backend

- **Fastify** + **TypeScript** (Node.js 20 LTS)
- Валидация: Ajv (JSON Schema, совместимо с `strategy.schema.json`)
- Auth: JWT (access + refresh tokens), fastify-jwt
- WebSocket клиент к Bybit: ws
- HTTP клиент к Bybit: undici / node fetch
- Логирование: **pino** (JSON structured logs)

## 3) Data layer

- **PostgreSQL 16** — основная БД
- **Prisma** — ORM, миграции, type-safe queries
- **Redis 7** — кэш (instruments, tickers), rate-limit counters, pub/sub
- **BullMQ** (на Redis) — очередь задач BotRun, scheduled jobs

## 4) Infrastructure (dev & prod)

- **Docker Compose** — локальная среда (postgres, redis, api, worker, frontend)
- **Nginx** — reverse proxy, TLS termination, static serving
- VPS (Ubuntu 22.04 LTS) — prod deployment
- Let's Encrypt — TLS-сертификаты
- systemd — управление процессами в prod

## 5) Tooling

- **pnpm** — менеджер пакетов (workspaces для monorepo)
- **ESLint + Prettier** — линтинг и форматирование
- **Vitest** — unit/integration тесты
- **Playwright** — e2e тесты (post-MVP)

## 6) Monorepo structure (план)

```
/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # Fastify backend + worker
├── packages/
│   ├── shared/       # types, constants, DSL schema
│   └── bybit-client/ # Bybit REST/WS wrapper
├── docs/             # documentation (this repo)
├── docker-compose.yml
└── pnpm-workspace.yaml
```

## 7) Ограничения и решения

| Вопрос | Решение |
|---|---|
| Один язык frontend + backend | TypeScript everywhere |
| Strategy DSL валидация | Ajv + `strategy.schema.json` (shared) |
| Bybit WS reconnect | ws + custom reconnect с backoff (в `bybit-client`) |
| Queue для BotRun | BullMQ (Redis-based, retries, delayed jobs) |
| Секреты | env vars + Docker secrets, не в репозитории |

## 8) Что НЕ входит в MVP стек

- Kubernetes / Helm (overkill для single-VPS MVP)
- GraphQL (REST + OpenAPI достаточно)
- Kafka / RabbitMQ (BullMQ покрывает потребности)
- Terraform / IaC (ручной деплой на VPS пока достаточно)

---

## 9) Lab v2 — одобренные frontend-зависимости (добавляются по фазам)

> **Статус:** одобрены как архитектурные решения. Добавляются в `package.json` только при старте соответствующей фазы — не заранее.
> Детали применения: `docs/23-lab-v2-ide-spec.md`.

| Библиотека | Версия | Фаза | Назначение |
|---|---|---|---|
| `@xyflow/react` (React Flow v11+) | 11.x+ | Phase 3 | Граф-редактор (canvas, nodes, edges, handles). Зафиксирован как единственный выбор. Альтернативы не рассматриваются. |
| `react-resizable-panels` | latest stable | Phase 1 | Изменяемые панели лабораторного шелла (left / center / right / bottom). |
| `@tanstack/react-virtual` | 3.x | Phase 3 | Виртуализация палитры блоков при большом числе элементов. |
| `zundo` | latest stable | Phase 3 | Zustand `temporal` middleware для undo/redo в `useLabGraphStore`. |

**Ограничения:**
- `@xyflow/react` — **зафиксирован**; замена требует архитектурного решения и пересмотра документа.
- `zundo` заменяет ручной history stack; не дублировать логику.
- `react-resizable-panels` должен быть обёрнут в единый `PanelLayout` компонент, не рассредоточен по всему приложению.

**Что НЕ добавляется в Lab v2:**
- Rete.js или другие граф-редакторы (выбор уже сделан в пользу React Flow).
- Кастомный WebGL canvas (преждевременная оптимизация).
- D3.js для визуализации графа (React Flow покрывает потребность).
