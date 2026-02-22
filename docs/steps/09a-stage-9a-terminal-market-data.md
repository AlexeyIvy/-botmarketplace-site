# Stage 9a — Terminal Market Data Flow (read-only)

## Status: DONE

## 1) Scope

- `GET /terminal/ticker?symbol=...` — live ticker (lastPrice, bid/ask, 24h stats)
- `GET /terminal/candles?symbol=...&interval=...&limit=...` — OHLCV candles
- Both endpoints: `authenticate` (JWT required), **no workspace** (Bybit data is public)
- Stable error handling via Problem Details (RFC 9457):
  - 400 — missing/invalid query params
  - 401 — no/invalid JWT
  - 422 — unknown symbol
  - 502 — upstream Bybit error
- Terminal UI page: symbol selector, interval selector, ticker grid, candles table
  (loading / error / success states)
- `fetchTicker()` added to `bybitCandles.ts`
- OpenAPI contract updated: `Ticker` + `Candle` schemas, two new path entries

## 2) Scope boundaries (что НЕ сделано)

- Нет размещения ордеров (Stage 9b)
- Нет SL/TP
- Нет WebSocket streaming
- Нет symbol search / instruments catalogue
- Нет workspace enforcement на market data (публичные данные, не нужно)
- Нет UI charts (только таблица candles)
- Нет интеграции с ExchangeConnection (Stage 9b)

## 3) Security decision (market data vs workspace)

`/terminal/ticker` и `/terminal/candles` — **authenticated, not workspace-scoped**.

Обоснование:
- Биржевые market data — публичный API Bybit; данные не принадлежат workspace.
- Обязательная аутентификация (JWT) соответствует общему паттерну приложения:
  только залогиненные пользователи работают с терминалом.
- Stage 9b (orders) будет workspace-scoped, так как ордера выполняются через
  `ExchangeConnection` конкретного workspace.

## 4) Файлы изменений

| Файл | Тип |
|------|-----|
| `apps/api/src/lib/bybitCandles.ts` | добавлен `fetchTicker()` + `Ticker` interface |
| `apps/api/src/routes/terminal.ts` | новый: `/terminal/ticker` + `/terminal/candles` |
| `apps/api/src/app.ts` | регистрация `terminalRoutes` |
| `apps/web/src/app/terminal/page.tsx` | полная замена заглушки на market data UI |
| `docs/openapi/openapi.yaml` | добавлены endpoints + схемы `Ticker`, `Candle` |
| `docs/steps/09a-stage-9a-terminal-market-data.md` | этот файл |

## 5) Verification commands

### Предварительно

```sh
export BASE=http://localhost:3000/api/v1

# Получить токен
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}' | jq -r '.accessToken')
```

### Ticker — valid symbol → 200

```sh
curl -s "$BASE/terminal/ticker?symbol=BTCUSDT" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 200, {symbol, lastPrice, bidPrice, askPrice, price24hPcnt, ...}
```

### Candles — valid params → 200

```sh
curl -s "$BASE/terminal/candles?symbol=BTCUSDT&interval=15&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 200, array of {openTime, open, high, low, close, volume}
```

### Ticker — missing symbol → 400

```sh
curl -s "$BASE/terminal/ticker" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 400, Problem Details: "Query parameter 'symbol' is required"
```

### Candles — invalid interval → 400

```sh
curl -s "$BASE/terminal/candles?symbol=BTCUSDT&interval=999" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 400, Problem Details: "Invalid 'interval'. Allowed values: 1, 5, 15, 30, 60, 240, D"
```

### Candles — invalid limit → 400

```sh
curl -s "$BASE/terminal/candles?symbol=BTCUSDT&limit=9999" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 400, Problem Details: "Invalid 'limit'. Must be an integer between 1 and 1000"
```

### Ticker — invalid/unknown symbol → 422

```sh
curl -s "$BASE/terminal/ticker?symbol=FAKESYMBOLABC" \
  -H "Authorization: Bearer $TOKEN" | jq .
# → 422, Problem Details: "Unknown symbol..."
```

### Without auth → 401

```sh
curl -s "$BASE/terminal/ticker?symbol=BTCUSDT" | jq .
# → 401, Problem Details: "Valid Bearer token required"
```

### Cross-workspace — N/A (endpoint не workspace-scoped по дизайну)

## 6) Acceptance checklist (Stage 9a)

- [x] Read-only market flow реализован (ticker + candles)
- [x] Выбор инструмента/symbol flow определён (query param + UI input)
- [x] Ошибки обрабатываются стабильно (400/401/422/502 с Problem Details)
- [x] OpenAPI обновлён (Ticker, Candle schemas + endpoints)
- [x] Нет scope creep в ордеры/SL/TP
- [x] Handover notes для Stage 9b добавлены (см. раздел 7)
- [x] Verification воспроизводим (curl команды выше)

## 7) Handover для Stage 9b (Terminal Manual Order Flow)

### Что готово после Stage 9a

- `GET /terminal/ticker?symbol=...` — live market price (обязательно для order form)
- `GET /terminal/candles?symbol=...&interval=...&limit=...` — candle data
- UI `/terminal` — symbol selector + ticker + candles table готовы к расширению

### Как использовать ExchangeConnection из Stage 8 в ордерном flow

```typescript
// В Stage 9b route handler (e.g. POST /terminal/orders):
import { prisma } from "../lib/prisma.js";
import { decrypt } from "../lib/crypto.js";

// 1. resolveWorkspace(request, reply) — обязательно для ордеров
const workspace = await resolveWorkspace(request, reply);
if (!workspace) return;

// 2. Получить connectionId из body
const conn = await prisma.exchangeConnection.findUnique({
  where: { id: request.body.connectionId },
});
if (!conn || conn.workspaceId !== workspace.id) {
  return problem(reply, 404, "Not Found", "Exchange connection not found");
}

// 3. Расшифровать секрет
const key = Buffer.from(process.env.SECRET_ENCRYPTION_KEY!, "hex");
const secret = decrypt(conn.encryptedSecret, key);

// 4. Вызвать Bybit SDK/API с conn.apiKey + secret
// e.g. POST /v5/order/create (Bybit Unified Trading Account)
```

### Что делать в Stage 9b (без повторения Stage 9a)

- `POST /terminal/orders` — создание Market/Limit ордера через Bybit API
  - body: `{ connectionId, symbol, side, type, qty, price? }`
  - Требует: `authenticate` + `resolveWorkspace`
  - Дешифрует `encryptedSecret`, вызывает `POST /v5/order/create`
- `GET /terminal/orders?connectionId=...` — список открытых ордеров/позиций
- `GET /terminal/position?connectionId=...&symbol=...` — текущая позиция
- UI: order form (side/type/qty/price), order list/status panel
- Обновить `status` ExchangeConnection на `CONNECTED` после первого успешного ордерного вызова
  (это также заменит demo-first заглушку в `POST /exchanges/:id/test`)

### Ограничения, остающиеся к Stage 9b

- `POST /exchanges/:id/test` всё ещё demo-first (без реального биржевого вызова)
- `apiKey` хранится plain text (deferred production improvement)

## 8) Deviations

Нет отклонений от Stage 9a scope.

Одно архитектурное решение задокументировано явно:
- `/terminal/ticker` и `/terminal/candles` — **authenticated, not workspace-scoped**
  (поскольку market data публично, workspace enforcement был бы избыточным coupling'ом).
  Это явно описано в разделе 3 и соответствует архитектуре проекта.
