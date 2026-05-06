# Stability Roadmap V3 — Post-Review Follow-up Tasks

> **Статус**: активный план, создан 2026-04-08
> **Контекст**: экспертное code review после завершения всех 27 задач + 3 рекомендаций Roadmap V3.
> **Общая оценка реализации**: 4.1/5. Архитектура правильная, основные риски — тестовые gaps и edge cases.
>
> **Цель документа**: зафиксировать конкретные доработки, выявленные при ревью, с приоритизацией.

---

## Общая оценка по тирам

| Tier | Оценка | Ключевая проблема |
|------|--------|-------------------|
| Tier 1 (Stability) | 4.3/5 | auth routes — 0 тестов; graceful shutdown без таймаута |
| Tier 2 (Test coverage) | 4.2/5 | botWorker test покрывает только state transitions |
| Tier 3 (Live reliability) | 4.5/5 | stateMachine — эталон; readyz пороги произвольны |
| Tier 4 (New features) | 3.8/5 | hedges.ts — хрупкая логика; notify cache invalidation |

---

## Tier A — Критические доработки (блокируют production confidence)

### A1. Тесты для auth routes (JWT refresh, expired token, race conditions)

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 1-2 сессии |
| **Файлы** | новый `apps/api/tests/routes/auth.test.ts`, `apps/api/src/routes/auth.ts` |

**Проблема:**
`auth.ts` содержит complex token flows (refresh с httpOnly cookies, double-issue race, user deletion race, expired token handling). **Ни одного теста.** При изменении логики регрессию невозможно обнаружить.

**Что покрыть:**
- Login: success, wrong password, nonexistent user, rate limit (6-й запрос → 429)
- Register: success, duplicate email, weak password
- Refresh: success (new access + refresh tokens), expired refresh → 401 + clear cookie
- Refresh race: два одновременных запроса с одним refresh token
- User deletion: user deleted между verify и findUnique в refresh handler
- Token type validation: access token в refresh endpoint → rejected

---

### A2. Graceful shutdown timeout

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/server.ts` |

**Проблема:**
Если `stopWorker()` повисает (deadlock в Prisma, зависший poll цикл, сетевой таймаут Bybit), процесс никогда не завершится. SIGTERM от systemd через 90с сделает hard kill, но за это время могут накопиться orphaned ресурсы.

**Решение:**
```typescript
const SHUTDOWN_TIMEOUT_MS = 30_000;

process.once(signal, async () => {
  const forceTimer = setTimeout(() => {
    logger.error("Graceful shutdown timeout — forcing exit");
    process.exit(1);
  }, SHUTDOWN_TIMEOUT_MS);
  forceTimer.unref();

  fundingCron.stop();
  stopPoolMetricsLogging();
  if (stopWorker) await stopWorker();
  await app.close();
  await prisma.$disconnect();
  process.exit(0);
});
```

Также: защита от двойного сигнала (SIGINT + SIGTERM) — добавить `isShuttingDown` guard.

---

### A3. Notify cache invalidation при обновлении настроек

| | |
|---|---|
| **Приоритет** | HIGH |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/lib/notify.ts`, `apps/api/src/routes/notifications.ts` |

**Проблема:**
После `PUT /user/notifications` кеш в `notify.ts` (TTL 5 мин) не инвалидируется. Пользователь сохраняет Telegram config → до 5 минут не получает уведомлений. Пользователь думает что не работает.

**Решение:**
1. Экспортировать `invalidateNotifyCache(workspaceId)` из `notify.ts`
2. В PUT handler: после upsert — определить workspace через userId → membership, вызвать invalidate
3. Альтернатива (проще): экспортировать `clearAllNotifyCache()` и вызвать при любом PUT

---

## Tier B — Важные доработки (улучшают надёжность)

### B1. Валидация exit quantity в hedge routes

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 20 мин |
| **Файлы** | `apps/api/src/routes/hedges.ts` |

**Проблема:**
`hedges.ts:207` — exit quantity берётся из `spotLeg?.quantity`. Если spot leg ещё не заполнен (статус OPENING, но legs пусты), `exitQty` будет `0`. Оба exit intent'а создадутся с `qty: 0` — бессмысленные ордера.

**Решение:**
```typescript
const exitQty = request.body?.quantity ?? spotLeg?.quantity ?? 0;
if (exitQty <= 0) {
  return problem(reply, 400, "Bad Request", "Cannot determine exit quantity — no filled entry legs");
}
```

---

### B2. CORS_ORIGIN и TRUST_PROXY через env

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/app.ts` |

**Проблема:**
- CORS: `["https://botmarketplace.ru"]` захардкожен. Staging/dev домены не пройдут.
- trustProxy: `"127.0.0.1"` захардкожен. За cloud load balancer (10.x.x.x) rate-limit ломается.

**Решение:**
```typescript
// CORS
const corsOrigin = process.env.CORS_ORIGIN
  ? process.env.CORS_ORIGIN.split(",")
  : (process.env.NODE_ENV === "production" ? ["https://botmarketplace.ru"] : true);

// trustProxy
trustProxy: process.env.TRUST_PROXY || "127.0.0.1",
```

---

### B3. Тесты для processIntents / executeIntent / reconcilePlacedIntents

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 1-2 сессии |
| **Файлы** | `apps/api/tests/lib/botWorker.test.ts` |

**Проблема:**
`botWorker.test.ts` покрывает только state transitions (activateRun, stopRun, timeoutExpired). Три ключевые функции торгового ядра — `processIntents()`, `executeIntent()`, `reconcilePlacedIntents()` — **ноль тестов**.

**Что покрыть:**
- executeIntent: demo mode (simulated fill), live mode (mock bybitPlaceOrder)
- executeIntent: retry на transient error, dead-letter на permanent error
- processIntents: strategy disabled → intent cancelled
- reconcilePlacedIntents: partial fill → PARTIALLY_FILLED, full fill → FILLED
- reconcilePlacedIntents: order CANCELLED on exchange → intent CANCELLED

---

### B4. Cleanup для in-memory maps в botWorker

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 20 мин |
| **Файлы** | `apps/api/src/lib/botWorker.ts` |

**Проблема:**
`trailingStopStates` и `lastTradeCloseTimes` — Map'ы, которые никогда не чистятся для завершённых runs. При длительной работе сервера (~1000+ runs за неделю) будут расти бесконечно. Не критично для памяти (маленькие объекты), но грязно.

**Решение:**
В `stopRun()` после перехода в STOPPED:
```typescript
trailingStopStates.delete(runId);
lastTradeCloseTimes.delete(runId);
```
То же в `timeoutExpiredRuns()` после перехода в FAILED/TIMED_OUT.

---

## Tier C — Косметические доработки (nice-to-have)

### C1. Token revocation mechanism для auth

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 1 сессия |
| **Файлы** | `apps/api/src/routes/auth.ts`, `prisma/schema.prisma` |

**Проблема:**
Нет механизма инвалидации refresh token. Если cookie скомпрометирован, атакер может использовать его 7 дней. Logout не убивает серверный токен — только клиентскую cookie.

**Решение:**
- Добавить `RefreshToken` модель (jti, userId, expiresAt, revoked)
- При refresh: проверить что jti не revoked, выпустить новый, revoke старый (rotation)
- При logout: revoke текущий token
- Cron: чистить expired tokens

---

### C2. Structured logging для DCA и safety guards

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 30 мин |
| **Файлы** | `apps/api/src/lib/botWorker.ts` |

**Проблема:**
Child loggers (Rec B) добавлены для activateRun, executeIntent, reconcile. Но `enforceDailyLossLimit()`, `enforceErrorPause()`, и DCA operations логируют через `workerLog` без контекста run/symbol.

**Решение:**
Добавить child loggers внутри циклов `for (const run of runningRuns)` в enforcement functions.

---

### C3. Rate limit для /client-errors endpoint

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 10 мин |
| **Файлы** | `apps/api/src/routes/clientErrors.ts`, `apps/api/src/app.ts` |

**Проблема:**
`POST /client-errors` — публичный endpoint (без auth). Rate limit в app.ts (`withRateLimit(clientErrorRoutes, 10, "1 minute")`) есть, но 10 req/min per IP может быть много для спам-ботов. Если фронтенд попадёт в error loop, 10 ошибок/мин на N пользователей = N×10 записей в логах.

**Решение:**
Уменьшить до 3 req/min. Или добавить in-memory deduplication (не логировать одинаковые ошибки чаще 1 раз/мин).

---

### C4. Telegram chatId format validation

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 10 мин |
| **Файлы** | `apps/api/src/routes/notifications.ts` |

**Проблема:**
`chatId` принимает любую строку до 50 символов. Telegram chatId — числовой ID (иногда отрицательный для групп) или `@username`. Без валидации формата пользователь может ввести произвольный текст и получить непонятную ошибку от Telegram API.

**Решение:**
```typescript
if (!/^-?\d+$/.test(tg.chatId) && !/^@[a-zA-Z0-9_]+$/.test(tg.chatId)) {
  return "notifyJson.telegram.chatId must be a numeric ID or @username";
}
```

---

### C5. Pool metrics threshold configurability

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 10 мин |
| **Файлы** | `apps/api/src/routes/readyz.ts` |

**Проблема:**
`waitCount < 5` — произвольный порог без обоснования и env override. При увеличении connection pool (через `connection_limit` в DATABASE_URL) порог может быть неадекватным.

**Решение:**
```typescript
const POOL_WAIT_THRESHOLD = parseInt(process.env.POOL_WAIT_THRESHOLD || "5", 10);
```

---

## Dependency graph

```
A1 (auth тесты) — независимая, можно начинать сразу
A2 (shutdown timeout) — независимая, 15 мин
A3 (notify cache) — независимая, 15 мин
B1 (hedge qty validation) — независимая, 20 мин
B2 (CORS/trustProxy env) — независимая, 15 мин
B3 (worker intent тесты) — независимая, 1-2 сессии
B4 (map cleanup) — независимая, 20 мин
C1 (token revocation) — зависит от A1 (сначала тесты для auth)
C2-C5 — независимые, по 10-30 мин
```

Все задачи независимы (кроме C1 → A1). Можно параллелить.

---

## Сводка effort

| Tier | Задач | Effort | Результат |
|------|-------|--------|-----------|
| Tier A | 3 | ~3-4 сессии | Production confidence |
| Tier B | 4 | ~2-3 сессии | Надёжность edge cases |
| Tier C | 5 | ~2-3 часа | Cosmetic polish |

**После Tier A платформа полностью production-ready с confidence.**
**Tier B закрывает edge cases. Tier C — по желанию.**
