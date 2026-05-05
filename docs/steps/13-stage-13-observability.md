# Stage 13 — Observability & Ops Baseline

## Status: DONE

## 1) Scope

- **Correlation IDs** — `X-Request-Id` на каждом запросе/ответе (reuse client header или auto UUID)
- **Enhanced `/healthz`** — добавлены поля `uptime` и `timestamp`
- **Structured logging в botWorker** — все `console.log`/`console.error` заменены на pino с именованными полями
- **Global error handler** — `setErrorHandler`: логирует 5xx структурированно, возвращает RFC 9457 Problem Details; 4xx пропускает без изменений
- **Smoke tests** — Section 13 (4 теста), итого 83

Нет новых DB-миграций. Нет новых npm-зависимостей (`pino` уже в deps; `node:crypto` — встроенный).

## 2) Scope Boundaries (что НЕ входит в Stage 13)

- Нет централизованного log-агрегатора (Loki, Datadog и т.п.) — только journald
- Нет distributed tracing (OpenTelemetry) — только header-based correlation
- Нет метрик (Prometheus / `/metrics` endpoint)
- Нет alerting-правил
- Нет structured logging в API route handlers (только botWorker)
- Нет worker-процесса в отдельном systemd unit (по-прежнему in-process)

## 3) Files Changed

| Файл | Изменение |
|------|-----------|
| `apps/api/src/app.ts` | `randomUUID` import; `genReqId`; `onSend` hook; `setErrorHandler` |
| `apps/api/src/routes/healthz.ts` | добавлены `uptime` и `timestamp` в ответ |
| `apps/api/src/lib/botWorker.ts` | pino `workerLog`; все 16 `console.*` заменены структурированными вызовами |
| `deploy/smoke-test.sh` | Section 13 (4 проверки) |
| `docs/steps/13-stage-13-observability.md` | NEW — этот файл |

## 4) Детали реализации

### Correlation IDs (`app.ts`)

```typescript
import { randomUUID } from "node:crypto";

const app = Fastify({
  logger: { ... },
  genReqId: (req) =>
    (req.headers["x-request-id"] as string) || randomUUID(),
});

// Echo ID back on every response (including errors)
app.addHook("onSend", async (request, reply) => {
  reply.header("X-Request-Id", request.id);
});
```

Клиент может задать свой ID (`X-Request-Id: my-trace-42`) — он сохраняется сквозь весь цикл запроса и возвращается в ответе. Если клиент не задал — генерируется UUID v4.

### Global Error Handler (`app.ts`)

```typescript
app.setErrorHandler((error: Error & { statusCode?: number; status?: number }, request, reply) => {
  const statusCode = error.statusCode ?? error.status ?? 500;
  if (statusCode < 500) {
    // rate-limit 429, validation 400 и т.п. — пропускаем как есть
    void reply.status(statusCode).send(error);
    return;
  }
  request.log.error({ err: error, reqId: request.id }, "Unhandled error");
  void reply.status(500).send({
    type: "about:blank",
    title: "Internal Server Error",
    status: 500,
    detail: process.env.NODE_ENV === "production"
      ? "An unexpected error occurred"
      : error.message,
  });
});
```

**Найденный баг:** `@fastify/rate-limit` направляет ошибки 429 через `setErrorHandler`. Без проверки `statusCode < 500` они превращались в 500. Исправлено pass-through для всех 4xx.

### Enhanced `/healthz` (`healthz.ts`)

```typescript
return reply.send({
  status: "ok",
  uptime: process.uptime(),     // секунд с момента старта процесса
  timestamp: new Date().toISOString(),
});
```

### Structured Logging в botWorker (`botWorker.ts`)

```typescript
import pino from "pino";
const workerLog = pino({
  name: "botWorker",
  transport: process.env.NODE_ENV !== "production"
    ? { target: "pino-pretty" }
    : undefined,
});
```

Заменены все 16 вызовов:

| Было | Стало |
|------|-------|
| `console.log('[botWorker] started ...')` | `workerLog.info({ workerId, interval }, 'botWorker started')` |
| `console.log('[botWorker] run X timed out ...')` | `workerLog.info({ runId, elapsed, maxDurationMs }, 'run timed out')` |
| `console.log('[botWorker] run X stopping ...')` | `workerLog.info({ runId, estimatedDailyLoss, dailyLossLimitUsd }, 'daily loss limit exceeded, stopping run')` |
| `console.log('[botWorker] intent X simulated ...')` | `workerLog.info({ intentId }, 'intent simulated (demo mode)')` |
| `console.log('[botWorker] intent X placed ...')` | `workerLog.info({ intentId, orderId }, 'intent placed')` |
| `console.log('[botWorker] intent X cancelled ...')` | `workerLog.info({ intentId }, 'intent cancelled — strategy disabled')` |
| `console.error(...)` × 10 | `workerLog.error({ err, runId/intentId/botId }, 'описание')` |

## 5) Security

Нет изменений в auth / workspace isolation. В production `detail` в 500-ответе не содержит raw error message. Все новые hooks не расширяют поверхность атаки.

## 6) Verification Commands

```bash
# Enhanced healthz
curl -s https://botmarketplace.ru/api/v1/healthz | jq .
# Expected: { "status": "ok", "uptime": <number>, "timestamp": "<ISO>" }

# X-Request-Id автогенерация
curl -sI https://botmarketplace.ru/api/v1/healthz | grep -i x-request-id
# Expected: x-request-id: <uuid>

# Клиентский ID возвращается эхом
curl -sI https://botmarketplace.ru/api/v1/healthz -H "X-Request-Id: my-trace-42" | grep -i x-request-id
# Expected: x-request-id: my-trace-42

# Rate-limit возвращает 429 (не 500)
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST https://botmarketplace.ru/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"rl_${i}_$(date +%s)@x.com\",\"password\":\"Test1234!\"}"
done
# Ожидаем: 201 201 201 429 429 429

# Трассировка запроса через логи
REQ_ID=$(curl -sI https://botmarketplace.ru/api/v1/healthz | grep -i x-request-id | awk '{print $2}' | tr -d '\r')
sudo journalctl -u botmarket-api --since "5 minutes ago" | grep "$REQ_ID"

# Полный smoke test (83 теста, после сброса rate-limit window ~15 мин)
bash deploy/smoke-test.sh
```

## 7) Runbook

### Трассировка запроса

1. Взять `X-Request-Id` из заголовков ответа.
2. `sudo journalctl -u botmarket-api --since "1 hour ago" | grep "<req-id>"` — все записи этого запроса.
3. Клиент может задать свой ID (`-H "X-Request-Id: my-id"`) — он сохраняется сквозь весь цикл.

### При ошибке 500 в API

1. Взять `X-Request-Id` из заголовков ответа.
2. `sudo journalctl -u botmarket-api -n 500 | grep "<req-id>"` — найти запись с `"msg":"Unhandled error"`.
3. Поле `err` содержит `message` + `stack`.
4. В dev-окружении `detail` в теле ответа также содержит `error.message`.

### Чтение логов botWorker

```bash
# Поток в реальном времени
sudo journalctl -u botmarket-api -f | grep botWorker

# Только ошибки (level=50)
sudo journalctl -u botmarket-api --since "1 hour ago" | grep '"level":50'
```

Ключевые поля в логах worker: `workerId`, `runId`, `intentId`, `botId`, `err`.

## 8) Acceptance Checklist (Stage 13)

- [x] `GET /healthz` возвращает `{ status, uptime, timestamp }`
- [x] Каждый HTTP-ответ содержит заголовок `X-Request-Id` (auto UUID)
- [x] Клиентский `X-Request-Id` возвращается эхом без изменений
- [x] Rate-limit 429 корректно проходит через error handler (не превращается в 500)
- [x] botWorker: все 16 `console.*` заменены на pino с именованными полями
- [x] Global error handler: 5xx логируются структурированно, 4xx пропускаются
- [x] `pnpm build:api` — компилируется без ошибок TypeScript
- [x] `systemctl is-active botmarket-api` → `active` после деплоя
- [x] Smoke test Section 13: 4/4 проверки проходят
- [x] Нет новых DB-миграций
- [x] Нет новых npm-зависимостей
- [x] Нет scope creep

## 9) Handover для Stage 14

### Отложенные задачи

| Feature | Target Stage |
|---|---|
| Централизованный log-агрегатор (Loki / Datadog) | Stage 14+ |
| Distributed tracing (OpenTelemetry) | Stage 14+ |
| Prometheus `/metrics` endpoint | Stage 14+ |
| Alerting (PagerDuty / Telegram) | Stage 14+ |
| Structured logging в API route handlers | Stage 14+ |
| Worker как отдельный systemd unit | Stage 14+ |
| `execution.maxSlippageBps` enforcement (real-time price) | Stage 13+ |
| `entry.signal = "webhook"` routing to RUNNING bot | Stage 13+ |

### Стабильные контракты для Stage 14

| Контракт | Статус |
|---|---|
| `X-Request-Id` header на каждом ответе | Stable |
| `GET /healthz` → `{ status, uptime, timestamp }` | Stable |
| botWorker pino logger: `workerLog.info/error({ ...fields }, msg)` | Stable |
| Global error handler: 5xx → RFC 9457, 4xx pass-through | Stable |
| Smoke test 83 тестов (sections 1–13) | Stable |

## 10) Deviations

Ни одного. Весь scope Stage 13 реализован как запланировано.

**Bonus fix:** В процессе реализации обнаружен баг — `@fastify/rate-limit` маршрутизирует ошибки 429 через `setErrorHandler`, из-за чего они превращались в 500 Internal Server Error. Исправлено в рамках Stage 13 (`statusCode < 500` → pass-through).
