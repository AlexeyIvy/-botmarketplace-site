# Stability Roadmap V3 — Pre-Production Hardening

> **Статус**: активный план, создан 2026-04-04
> **Контекст**: полный аудит кодовой базы после завершения Stages 1-8 и Roadmap V2.
> Проект архитектурно зрелый (модульная структура, pure functions, idempotent intents, audit trail через BotEvent), но **execution layer отстаёт от data layer** по надёжности.
>
> **Цель документа**: зафиксировать конкретные баги и техдолг, блокирующие live-торговлю, с приоритизацией по реальному риску.

---

## Общая оценка

| Аспект | Оценка |
|--------|--------|
| Архитектура | Хорошо: модули, state machine, DSL, intents |
| Data layer | Сильно: тесты, чистый код, Prisma schema |
| Execution layer | Слабо: botWorker без тестов, silent failures, race conditions |
| Security | Средне: encryption есть, но JWT/CORS/rate-limit требуют доработки |
| Observability | Базовая: pino логи есть, метрик и alerting нет |

**Главный вывод**: прежде чем строить новые фичи, нужно укрепить фундамент.
Tier 1 (8 задач) — 1 рабочий день. Tier 2 (4 задачи) — 2-3 дня. После этого платформа готова к live-торговле.

---

## Tier 1 — Стабилизация (обязательно перед реальной торговлей)

### 1. Fix activateRun() — await + error handling + run pausing on failure

| | |
|---|---|
| **Критичность** | CRITICAL |
| **Effort** | 45 мин |
| **Файлы** | `apps/api/src/lib/botWorker.ts` |

**Проблема (тройная):**

1. **Fire-and-forget** (`botWorker.ts:1633`):
   ```typescript
   for (const { id } of queued) {
     activateRun(id); // fire-and-forget, don't await
   }
   ```
   Unhandled promise rejection может убить весь worker process. `poll()` не знает об ошибке.

2. **Catch только логирует** (`botWorker.ts:362-365`):
   ```typescript
   } catch (err) {
     workerLog.error({ err, runId }, "activateRun error");
   }
   ```
   Run остаётся в промежуточном состоянии (STARTING / SYNCING) навсегда.

3. **timeoutExpiredRuns() слепа к ephemeral states** (`botWorker.ts:388`):
   Проверяет только `state: "RUNNING"`. Runs застрявшие в STARTING или SYNCING из-за ошибки activateRun() — **зависнут навсегда**.

**Решение:**
- Await activateRun() (или обернуть в `Promise.allSettled` для параллельного запуска с error handling)
- В catch: перевести run в FAILED через state machine
- Расширить `timeoutExpiredRuns()` — добавить проверку STARTING и SYNCING states с коротким таймаутом (например, 5 мин вместо 4 часов)

---

### 2. Fix encryption key missing — crash/pause run, not silently skip

| | |
|---|---|
| **Критичность** | CRITICAL |
| **Effort** | 20 мин |
| **Файлы** | `apps/api/src/lib/crypto.ts`, `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`getEncryptionKeyRaw()` (`crypto.ts:44-48`) возвращает `null` при отсутствии `SECRET_ENCRYPTION_KEY`. В botWorker при декрипте секретов Bybit это приведёт к silent skip — бот будет "работать", но не сможет подписывать ордера. Пользователь не узнает почему.

**Решение:**
- При отсутствии ключа — throw с явным сообщением
- В botWorker — catch → перевод run в FAILED с BotEvent, объясняющим причину

---

### 3. JWT: throw on default secret in production, reduce expiry to 1h + refresh token

| | |
|---|---|
| **Критичность** | CRITICAL |
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/app.ts`, `apps/api/src/routes/auth.ts` |

**Проблема:**
- `app.ts:90`: fallback `"dev-secret-change-in-production-please"` — hardcoded слабый секрет
- `auth.ts:52,85`: `expiresIn: "30d"` — при утечке токена доступ на месяц
- Нет refresh token — пользователь должен логиниться заново при expiry

**Решение:**
- В production (`NODE_ENV=production`): throw если `JWT_SECRET` не задан
- Access token: `expiresIn: "1h"`
- Добавить refresh token endpoint с `expiresIn: "7d"` + rotation

---

### 4. Fix CORS — whitelist botmarketplace.store only

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/app.ts` |

**Проблема:**
`app.ts:74`: `origin: true` — разрешает запросы с любого домена.

**Решение:**
```typescript
origin: process.env.NODE_ENV === "production"
  ? ["https://botmarketplace.store"]
  : true
```

---

### 5. Fix PrismaClient duplication — использовать shared singleton

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 10 мин |
| **Файлы** | `apps/api/src/server.ts`, `apps/api/src/lib/prisma.ts` |

**Проблема:**
`server.ts:22` создаёт `new PrismaClient()`, при этом singleton уже существует в `lib/prisma.ts`. Два connection pool к одной БД → фрагментация, потенциальный connection exhaustion.

**Решение:**
Заменить `const prisma = new PrismaClient()` на `import { prisma } from "./lib/prisma.js"`.

---

### 6. Add trustProxy: "127.0.0.1" to Fastify

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 5 мин |
| **Файлы** | `apps/api/src/app.ts` |

**Проблема:**
Без trustProxy Fastify за nginx видит IP nginx вместо клиента. Все rate limits применяются к одному IP → бесполезны.

**Решение:**
Добавить в конфигурацию Fastify: `trustProxy: "127.0.0.1"`.

---

### 7. Nginx: add HSTS + basic CSP

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 15 мин |
| **Файлы** | Nginx config на VPS |

**Решение:**
```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
```

---

### 8. Login rate limit: 5 req/15 min

| | |
|---|---|
| **Критичность** | MEDIUM |
| **Effort** | 10 мин |
| **Файлы** | `apps/api/src/routes/auth.ts` |

**Проблема:**
Сейчас глобальный лимит 100 req/min. Login endpoint не имеет отдельного rate limit → brute force возможен.

**Решение:**
Добавить route-level rate limit на `/auth/login` и `/auth/register`: 5 req / 15 мин per IP.

---

## Tier 2 — Test coverage для торгового ядра

> **Рекомендация**: начать с #11 (crypto.ts, 30 мин) — encryption layer лежит в основе всего trading flow.

### 9. botWorker: тесты на state transitions

| | |
|---|---|
| **Effort** | 1-2 сессии |
| **Файлы** | `apps/api/src/lib/botWorker.ts`, новый test file |

Тесты на QUEUED→RUNNING→STOPPED с mock Prisma. Проверка что ошибки корректно переводят run в FAILED. Проверка что застрявшие ephemeral states обнаруживаются.

---

### 10. bybitOrder: тесты на HMAC signing, error handling, status mapping

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/lib/bybitOrder.ts`, новый test file |

- HMAC signing: known-input → known-output
- `mapBybitStatus()`: все Bybit статусы маппятся корректно
- Error classification: retryable vs terminal
- Order status reconciliation: history fallback → realtime fallback

---

### 11. crypto.ts: тесты encrypt→decrypt roundtrip, wrong key rejection

| | |
|---|---|
| **Effort** | 30 мин |
| **Файлы** | `apps/api/src/lib/crypto.ts`, новый test file |

- Roundtrip: encrypt(plaintext, key) → decrypt(ciphertext, key) === plaintext
- Wrong key: decrypt с другим ключом → throw (GCM auth tag failure)
- Invalid format: tampered ciphertext → throw
- Key validation: non-hex / wrong length → rejected

---

### 12. Terminal order placement: тесты через app.inject

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/routes/terminal.ts`, новый test file |

Integration tests через Fastify `app.inject()` — без реальных HTTP запросов, но с полным route pipeline.

---

## Tier 3 — Live trading reliability

### 13. WebSocket integration: Bybit orderbook + kline + execution reports

| | |
|---|---|
| **Effort** | 3-4 сессии (уточнено) |

Bybit WS API с reconnection logic, heartbeat, partial message handling. Заменит polling для market data и execution reports — критично для latency.

> **Примечание**: effort увеличен с 2-3 до 3-4 сессий — reconnection logic и edge cases WS API требуют тщательного тестирования.

---

### 14. Optimistic locking для run state transitions

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/lib/stateMachine.ts` |

Race condition fix. `stateMachine.ts` использует транзакции, но при multi-worker (после #15) race на state transition реален. Добавить version field + optimistic lock.

> **Примечание**: если планируется multi-worker (#15), эта задача должна быть выполнена **до** или **одновременно** с #15.

---

### 15. Worker extraction: отдельный процесс

| | |
|---|---|
| **Effort** | 1-2 сессии |

Вынести botWorker в отдельный Node.js процесс. Сейчас worker работает в том же процессе что и API — crash worker = crash API.

---

### 16. Dead-letter queue для failed intents

| | |
|---|---|
| **Effort** | 1 сессия |

Сейчас failed intents retry бесконечно. Нужен max retry count + DLQ для ручного разбора.

---

### 17. React ErrorBoundary + error reporting

| | |
|---|---|
| **Effort** | 1 сессия |

Глобальный ErrorBoundary + отправка ошибок на backend для мониторинга.

---

## Tier 4 — Новые фичи (только после Tier 1-3)

| # | Задача | Effort |
|---|--------|--------|
| 18 | proximity_filter и volume_profile — последние compile-only блоки | 1 сессия |
| 19 | Hedge execution UI + API | 2-3 сессии |
| 20 | Notifications (Telegram webhook) | 1-2 сессии |
| 21 | MTF UI в Lab (выбор timeframe для индикатора) | 1 сессия |

> **Примечание**: #20 (Telegram notifications) стоит рассмотреть для переноса в Tier 3, поскольку оповещения о сбоях бота — это reliability feature, а не просто "новая фича".

---

## Дополнительные рекомендации (вне основного Roadmap)

### A. Graceful shutdown

При SIGTERM worker должен дождаться текущих intent executions, а не обрывать mid-flight. Без этого незавершённый ордер может остаться в неконсистентном состоянии.

### B. Health check endpoint

`/healthz` — для мониторинга что API и worker poll loop работают. Критично при systemd + nginx — без health check нет автоматического рестарта при зависании worker loop.

### C. Убрать искусственные sleep в activateRun()

`botWorker.ts:139` (800ms) и `botWorker.ts:148` (1200ms) — 2 секунды на старт каждого бота без функциональной причины. Убрать или сделать configurable.

---

## Сводка effort

| Tier | Задач | Effort | Результат |
|------|-------|--------|-----------|
| Tier 1 | 8 | ~1 рабочий день | Безопасная основа для live-торговли |
| Tier 2 | 4 | ~2-3 дня | Тестовое покрытие торгового ядра |
| Tier 3 | 5 | ~8-11 сессий | Надёжная live-инфраструктура |
| Tier 4 | 4 | ~5-7 сессий | Новая функциональность |

**После Tier 1 + Tier 2 платформа готова к осторожной live-торговле с ограниченными суммами.**
