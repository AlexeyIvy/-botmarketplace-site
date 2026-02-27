# Release Notes — BotMarketplace v0.1.0-rc1

**Тип релиза:** Release Candidate (demo-first)
**Статус:** RC — не для production с реальными деньгами
**Дата:** 2026-02-27
**Git тег:** `v0.1.0-rc1`

---

## Что в этом релизе

### Стек пользовательских сценариев (Stage 7–13)

| Модуль | Статус | Примечания |
|--------|--------|------------|
| Auth/Register/Login | ✅ Ready | JWT, workspace авто-создание, rate limiting |
| Workspace Isolation | ✅ Ready | 403/404 при cross-workspace доступе |
| Exchange Connections | ✅ Ready | CRUD + test endpoint; секреты зашифрованы AES-256 |
| Terminal Market Data | ✅ Ready | Ticker/candles с Bybit; реальные рыночные данные |
| Terminal Manual Order | ✅ Ready (demo-first) | Market/Limit ордера через ExchangeConnection |
| Strategy Authoring | ✅ Ready | DSL v1, JSON Schema validation, версионирование |
| Bot Factory | ✅ Ready (demo-first) | Создание ботов из версий стратегий; старт/стоп/таймаут |
| Bot Runtime | ✅ Ready (demo-first) | In-process worker; simulated fills в demo-режиме |
| Research Lab | ✅ Ready | Backtest API + UI с trade log; результаты сохраняются |
| Observability | ✅ Ready | Correlation IDs, structured logging (pino), enhanced /healthz |

---

## Ключевые возможности

### Auth
- Регистрация создаёт пользователя + workspace автоматически
- JWT (24h) через Authorization Bearer
- Rate limiting: 5 req/15 min на `/auth/register`

### Exchange Connections
- Хранение API-секретов в зашифрованном виде (`SECRET_ENCRYPTION_KEY` → AES-256-CBC)
- API никогда не возвращает `apiKey`, `secret`, `encryptedSecret`
- Endpoint `/exchanges/:id/test` — проверка подключения без раскрытия секретов

### Strategy DSL
- DSL v1 (зафиксирован, не меняется в RC)
- Валидация через JSON Schema 2020-12 с field-level указателями ошибок
- Иммутабельное версионирование стратегий

### Bot Factory
- Бот привязан к конкретной версии стратегии (иммутабельный снимок)
- Run lifecycle: QUEUED → STARTING → SYNCING → RUNNING → STOPPING → STOPPED / TIMED_OUT / FAILED
- Single-active-run per bot (409 при попытке параллельного запуска)
- `durationMinutes` — авто-остановка бота по времени
- DSL enforcement: `enabled: false` → worker отменяет PENDING intents
- Risk guard: `risk.dailyLossLimitUsd` → авто-стоп при превышении лимита

### Observability
- `X-Request-Id` на каждом ответе (auto UUID или echo клиентского)
- Structured logging в botWorker через pino
- Global error handler: 5xx → RFC 9457 Problem Details (без stack trace в production)
- `/healthz` с `uptime` и `timestamp`

---

## Известные ограничения (demo-first)

| Ограничение | Причина | Deferred |
|-------------|---------|----------|
| Bот worker — in-process (не отдельный процесс) | MVP simplicity | Stage 15+ |
| Real-money execution не рекомендован | Только demo/simulation Bybit mode | Отдельное решение |
| `execution.maxSlippageBps` не проверяется real-time | Требует WebSocket/polling для цены | Stage 15+ |
| `entry.signal = "webhook"` не реализован | Scope был deferred в Stage 12 | Stage 15+ |
| Нет refresh token / logout | MVP auth baseline | Stage 15+ |
| Нет RBAC (одна роль: owner) | MVP multi-tenant не нужен | Stage 15+ |
| Нет централизованного log-агрегатора | journald достаточно для RC | Stage 15+ |
| Нет Prometheus /metrics | Observability baseline достаточен | Stage 15+ |
| DSL v1 только | dslVersion > 1 deferred | По необходимости |
| Research Lab: простой buy-hold backtest | Production backtester требует отдельного этапа | Stage 15+ |

---

## Breaking Changes

**Нет** — все endpoint-контракты сохраняют обратную совместимость с Stage 9–13.

---

## Env vars (обязательные для RC)

| Переменная | Описание | Обязательна? |
|-----------|----------|--------------|
| `DATABASE_URL` | PostgreSQL connection string | Да |
| `JWT_SECRET` | Секрет для подписи JWT | Да |
| `SECRET_ENCRYPTION_KEY` | 32-байтный HEX-ключ для шифрования API-секретов | Да |
| `BOT_WORKER_SECRET` | Секрет для worker-to-API machine-to-machine вызовов | Да (production) |
| `BYBIT_API_KEY` | Bybit API ключ (для terminal market data) | Нет (market data публичный) |

---

## Как деплоить этот RC

```bash
# На VPS (тегированный деплой)
cd /opt/-botmarketplace-site
git fetch --tags
git checkout v0.1.0-rc1
pnpm install --frozen-lockfile
pnpm run db:migrate
pnpm run build:api && pnpm run build:web
systemctl restart botmarket-api botmarket-web

# Валидация
bash deploy/smoke-test.sh
```

Подробнее: см. `docs/runbooks/RUNBOOK.md`.

---

## Что проверено перед RC

- ✅ Smoke suite (90+ тестов) — все проходят
- ✅ E2E happy paths по всем модулям (Auth → Exchange → Terminal → Strategy → Bot → Lab)
- ✅ Cross-workspace isolation (403/404 на чужих ресурсах)
- ✅ Отсутствие утечки секретов в API-ответах
- ✅ Rate limiting 429 (не 500)
- ✅ Worker endpoint auth в production-режиме

---

*BotMarketplace v0.1.0-rc1 — Stage 14 Release Candidate Pack*
