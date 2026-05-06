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
Tier 1 (12 задач) — 1.5-2 рабочих дня. Tier 2 (5 задач) — 2-3 дня. После этого платформа готова к live-торговле.

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
- Await activateRun() последовательно в `for...of` (предпочтительно) или обернуть в `Promise.allSettled`
- В catch: перевести run в FAILED через state machine
- Расширить `timeoutExpiredRuns()` — добавить проверку STARTING и SYNCING states с коротким таймаутом (например, 5 мин вместо 4 часов)

> **Caveat**: `Promise.allSettled` запустит до 5 activateRun() параллельно, каждый делает ~5 Prisma запросов + sleep 2с. При дефолтном connection pool Prisma (5 connections) это создаст contention. Если выбран allSettled — увеличить pool size или ограничить concurrency.

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
| **Effort** | 1.5-2 сессии (backend + frontend token refresh) |
| **Файлы** | `apps/api/src/app.ts`, `apps/api/src/routes/auth.ts`, frontend auth layer |

**Проблема:**
- `app.ts:90`: fallback `"dev-secret-change-in-production-please"` — hardcoded слабый секрет
- `auth.ts:52,85`: `expiresIn: "30d"` — при утечке токена доступ на месяц
- Нет refresh token — пользователь должен логиниться заново при expiry

**Решение:**
- В production (`NODE_ENV=production`): throw если `JWT_SECRET` не задан
- Access token: `expiresIn: "1h"`
- Добавить refresh token endpoint с `expiresIn: "7d"` + rotation

> **Caveat**: фронтенд должен: хранить refresh token (httpOnly cookie), автоматически обновлять access token при 401, корректно обрабатывать expired refresh (редирект на логин). Это не только backend задача.

---

### 4. Fix CORS — whitelist botmarketplace.ru only

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
  ? ["https://botmarketplace.ru"]
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

> **Caveat**: CSP `script-src 'self'` может сломать приложение при использовании inline scripts, CDN-библиотек или Vite dev-mode инъекций. Перед деплоем — проаудировать фронтенд и адаптировать CSP. Начать с `Content-Security-Policy-Report-Only` для безопасного тестирования.

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

### 9. Graceful shutdown — await in-flight poll before exit

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 30 мин |
| **Файлы** | `apps/api/src/server.ts`, `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`server.ts:30-37` — shutdown handler вызывает `stopWorker()` (просто `clearInterval`), затем сразу `prisma.$disconnect()` и `process.exit(0)`. Если poll() сейчас в середине `processIntents()` (размещает ордер на Bybit), disconnect обрывает операцию. Ордер может уйти на биржу, но intent останется в PENDING — при рестарте будет дубликат.

```typescript
// Текущий код (server.ts:30-37):
stopWorker();              // clearInterval — НЕ ждёт текущий poll
await prisma.$disconnect(); // убивает соединения пока poll может работать
process.exit(0);           // жёсткий выход
```

**Решение:**
- `startBotWorker()` должен возвращать не `() => void`, а `() => Promise<void>` — cleanup function, ожидающая завершения текущего poll цикла
- Добавить `isShuttingDown` flag, который poll() проверяет перед каждым шагом
- Установить grace period timeout (например, 30с) — если poll не завершился, force exit с логом

---

### 10. poll() per-step error isolation

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 20 мин |
| **Файлы** | `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`botWorker.ts:1623-1671` — все шаги poll() в одном try/catch. Если `stopRun()` (строка 1643) бросает ошибку (DB timeout), **все последующие шаги пропускаются**: renewLeases, enforceDailyLossLimit, evaluateStrategies, processIntents, reconcilePlacedIntents. На 4 секунды вся торговая логика мертва. При нестабильном DB это каскадирует.

**Решение:**
Обернуть каждый критический шаг индивидуально:
```typescript
// Вместо одного большого try/catch:
await safeStep("stopRuns", () => stopRun(id));
await safeStep("timeoutExpired", () => timeoutExpiredRuns());
await safeStep("renewLeases", () => renewLeases());
// ... и т.д.

async function safeStep(name: string, fn: () => Promise<void>) {
  try { await fn(); }
  catch (err) { workerLog.error({ err }, `poll step "${name}" failed (non-fatal)`); }
}
```

---

### 11. TOCTOU race на создании интентов — добавить UNIQUE constraint

| | |
|---|---|
| **Критичность** | HIGH |
| **Effort** | 20 мин |
| **Файлы** | `prisma/schema.prisma`, `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`botWorker.ts:1348-1406` — классический Time-of-Check-Time-of-Use:
```typescript
const existing = await prisma.botIntent.findFirst({
  where: { botRunId: run.id, intentId },
});
if (existing) continue;
// RACE WINDOW: другой poll цикл может создать intent здесь
await prisma.botIntent.create({ data: { botRunId: run.id, intentId, ... } });
```
Нет `@@unique` constraint на `(botRunId, intentId)`. Два poll цикла могут оба пройти check и создать дубликат. Один сигнал → два ордера на бирже.

**Решение:**
1. Добавить в `schema.prisma`: `@@unique([botRunId, intentId])`
2. Миграция: `npx prisma migrate dev`
3. В botWorker: заменить findFirst+create на `upsert` или try/catch вокруг create с обработкой unique violation (P2002)

---

### 12. Env validation at startup — fail fast

| | |
|---|---|
| **Критичность** | MEDIUM |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/server.ts` или новый `apps/api/src/lib/env.ts` |

**Проблема:**
Приложение стартует без проверки обязательных переменных окружения. `DATABASE_URL` — Prisma падает при первом запросе. `JWT_SECRET` — используется слабый fallback. `SECRET_ENCRYPTION_KEY` — отсутствие обнаруживается только при попытке расшифровать ключи биржи. Приложение может работать минуты, создавая ложное впечатление что всё ок.

**Решение:**
```typescript
function validateEnv() {
  const required = ["DATABASE_URL", "JWT_SECRET"];
  const requiredInProd = ["SECRET_ENCRYPTION_KEY"];
  const missing = required.filter(k => !process.env[k]);
  if (process.env.NODE_ENV === "production") {
    missing.push(...requiredInProd.filter(k => !process.env[k]));
  }
  if (missing.length) {
    throw new Error(`Missing required env vars: ${missing.join(", ")}`);
  }
}
```
Вызвать в самом начале `main()` в `server.ts`, до `buildApp()`.

---

## Tier 2 — Test coverage для торгового ядра + input validation

> **Рекомендация**: начать с #13 (crypto.ts, 30 мин) — encryption layer лежит в основе всего trading flow.
> **Синергия**: #15 (botWorker тесты) лучше делать вместе или сразу после Tier 1 #1 (activateRun fix), т.к. тесты помогут убедиться что fix не сломал state machine flow.

### 13. crypto.ts: тесты encrypt→decrypt roundtrip, wrong key rejection

| | |
|---|---|
| **Effort** | 30 мин |
| **Файлы** | `apps/api/src/lib/crypto.ts`, новый test file |

- Roundtrip: encrypt(plaintext, key) → decrypt(ciphertext, key) === plaintext
- Wrong key: decrypt с другим ключом → throw (GCM auth tag failure)
- Invalid format: tampered ciphertext → throw
- Key validation: non-hex / wrong length → rejected

---

### 14. bybitOrder: тесты на HMAC signing, error handling, status mapping

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/lib/bybitOrder.ts`, новый test file |

- HMAC signing: known-input → known-output
- `mapBybitStatus()`: все Bybit статусы маппятся корректно
- Error classification: retryable vs terminal
- Order status reconciliation: history fallback → realtime fallback

---

### 15. botWorker: тесты на state transitions

| | |
|---|---|
| **Effort** | 1-2 сессии |
| **Файлы** | `apps/api/src/lib/botWorker.ts`, новый test file |

Тесты на QUEUED→RUNNING→STOPPED с mock Prisma. Проверка что ошибки корректно переводят run в FAILED. Проверка что застрявшие ephemeral states обнаруживаются.

---

### 16. Terminal order placement: тесты через app.inject

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/routes/terminal.ts`, новый test file |

Integration tests через Fastify `app.inject()` — без реальных HTTP запросов, но с полным route pipeline.

---

### 17. PATCH /exchanges — добавить валидацию apiKey

| | |
|---|---|
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/routes/exchanges.ts` |

**Проблема:**
POST `/exchanges` валидирует apiKey (required, string). Но PATCH позволяет передать `apiKey: ""` или `apiKey: null` без проверки — прямой путь к непонятным ошибкам при торговле.

**Решение:**
Добавить type/length валидацию для apiKey в PATCH handler, аналогичную POST.

---

## Tier 3 — Live trading reliability

### 18. Расширить /readyz — проверка worker health

| | |
|---|---|
| **Effort** | 30 мин |
| **Файлы** | `apps/api/src/routes/readyz.ts`, `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`readyz.ts` проверяет только `SELECT 1` (DB connectivity). Не проверяет: жив ли worker poll loop, доступен ли encryption key, есть ли застрявшие runs. Health check может отвечать "ok" когда торговое ядро фактически мертво.

**Решение:**
- Экспортировать из botWorker `lastPollTimestamp`
- В /readyz проверять: `Date.now() - lastPollTimestamp < POLL_INTERVAL_MS * 3` (если poll не выполнялся >12с — worker завис)
- Опционально: проверить наличие encryption key, количество stuck runs

---

### 19. WebSocket integration: Bybit orderbook + kline + execution reports

| | |
|---|---|
| **Effort** | 3-4 сессии (уточнено) |

Bybit WS API с reconnection logic, heartbeat, partial message handling. Заменит polling для market data и execution reports — критично для latency.

> **Примечание**: effort увеличен с 2-3 до 3-4 сессий — reconnection logic и edge cases WS API требуют тщательного тестирования.

---

### 20. Optimistic locking для run state transitions

| | |
|---|---|
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/lib/stateMachine.ts` |

Race condition fix. `stateMachine.ts` использует транзакции, но при multi-worker (после #21) race на state transition реален. Добавить version field + optimistic lock.

> **HARD DEPENDENCY**: эта задача **MUST** быть выполнена **до** #21 (worker extraction). Без optimistic locking два worker процесса создадут race conditions на state transitions. Выполнять #21 без #20 запрещено.

---

### 21. Worker extraction: отдельный процесс

| | |
|---|---|
| **Effort** | 1-2 сессии |
| **Depends on** | #20 (optimistic locking) |

Вынести botWorker в отдельный Node.js процесс. Сейчас worker работает в том же процессе что и API — crash worker = crash API.

---

### 22. Dead-letter queue для failed intents

| | |
|---|---|
| **Effort** | 1 сессия |

Сейчас failed intents retry бесконечно. Нужен max retry count + DLQ для ручного разбора.

---

### 23. React ErrorBoundary + error reporting

| | |
|---|---|
| **Effort** | 1 сессия |

Глобальный ErrorBoundary + отправка ошибок на backend для мониторинга.

---

## Tier 4 — Новые фичи (только после Tier 1-3)

| # | Задача | Effort |
|---|--------|--------|
| 24 | proximity_filter и volume_profile — последние compile-only блоки | 1 сессия |
| 25 | Hedge execution UI + API | 2-3 сессии |
| 26 | Notifications (Telegram webhook) | 1-2 сессии |
| 27 | MTF UI в Lab (выбор timeframe для индикатора) | 1 сессия |

> **Примечание**: #26 (Telegram notifications) стоит рассмотреть для переноса в Tier 3, поскольку оповещения о сбоях бота — это reliability feature, а не просто "новая фича".

---

## Дополнительные рекомендации (вне основного Roadmap)

### A. Убрать искусственные sleep в activateRun()

`botWorker.ts:139` (800ms) и `botWorker.ts:148` (1200ms) — 2 секунды на старт каждого бота без функциональной причины. Убрать или сделать configurable.

### B. Structured logging enrichment

Добавить в pino logger context: `runId`, `intentId`, `symbol` на уровне child logger. Сейчас многие ошибки логируются с минимальным контекстом — при дебаге в production это критично.

### C. Prisma connection pool monitoring

Дефолтный pool Prisma — 5 connections. При активных runs (каждый генерирует ~5 запросов за poll цикл) + cron + API routes pool может быть узким горлышком. Рассмотреть: увеличение pool size через `connection_limit` в DATABASE_URL, или мониторинг через `prisma.$metrics`.

---

## Dependency graph

```
#11 (TOCTOU) ← schema migration, делать до тестов Tier 2
#20 (optimistic lock) ← MUST before #21 (worker extraction)
#1 (activateRun fix) → #15 (botWorker тесты) — синергия, лучше вместе
#3 (JWT refresh) → затрагивает frontend auth layer
#9 (graceful shutdown) → #21 (worker extraction) — shutdown logic переедет
```

---

## Сводка effort

| Tier | Задач | Effort | Результат |
|------|-------|--------|-----------|
| Tier 1 | 12 | ~1.5-2 рабочих дня | Безопасная основа для live-торговли |
| Tier 2 | 5 | ~2-3 дня | Тестовое покрытие торгового ядра + input validation |
| Tier 3 | 6 | ~9-12 сессий | Надёжная live-инфраструктура |
| Tier 4 | 4 | ~5-7 сессий | Новая функциональность |

**После Tier 1 + Tier 2 платформа готова к осторожной live-торговле с ограниченными суммами.**
