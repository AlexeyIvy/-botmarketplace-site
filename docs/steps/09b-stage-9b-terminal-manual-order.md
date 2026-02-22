# Stage 9b — Terminal Manual Order Flow (demo-first)

## Status: DONE

## 1) Scope

- `POST /terminal/orders` — place Market or Limit order via ExchangeConnection (Stage 8)
- `GET /terminal/orders/:id` — get order status; syncs live from Bybit for open orders
- `GET /terminal/orders` — list last 50 orders for workspace
- All order endpoints: `authenticate` + `resolveWorkspace()` enforcement
- Bybit V5 private API call (`POST /v5/order/create`, HMAC-SHA256 signed)
- Live status sync via `GET /v5/order/history` + `GET /v5/order/realtime`
- ExchangeConnection status updated to `CONNECTED` after first successful order
- `TerminalOrder` DB model (Prisma + PostgreSQL migration)
- Stable error handling: 400/401/403/404/422/502 via Problem Details
- OpenAPI contract updated: `CreateOrderRequest` + `TerminalOrderView` schemas + 3 new paths
- Terminal UI: order form (connection selector, BUY/SELL toggle, Market/Limit, qty, price)
- Handover notes for Stage 10

## 2) Scope boundaries (что НЕ сделано)

- Нет SL/TP (deferred — не существует простого пути без scope creep)
- Нет WebSocket streaming (deferred)
- Нет advanced order types (stop/conditional/post-only — deferred)
- Нет production-grade signature verification (key versioning, rotation — deferred)
- Нет symbol/qty/price validation против exchange lot size filters (deferred)
- Нет order amendment/cancel endpoint (deferred — Stage 10)
- Нет open positions endpoint (deferred — Stage 10)
- `POST /exchanges/:id/test` всё ещё demo-first (credential check без реального биржевого вызова)
  — Stage 9b заменяет это kosвенно: успешный `POST /terminal/orders` обновляет статус в CONNECTED

## 3) Architecture decisions

### Order execution model
Stage 9b использует **Вариант A** (реальный Bybit API вызов):
- `bybitPlaceOrder()` — HMAC-SHA256 подпись + `POST /v5/order/create`
- `bybitGetOrderStatus()` — сначала `/v5/order/history`, fallback на `/v5/order/realtime`
- Категория: `linear` (perpetual). Spot и inverse — deferred.

### Status sync
`GET /terminal/orders/:id` делает live-sync если `status === SUBMITTED || PARTIALLY_FILLED`:
- обновляет DB запись при изменении статуса
- non-fatal: возвращает stored статус если Bybit недоступен

### MARKET vs LIMIT contract
- `MARKET + price set` → `400 Bad Request` (clean contract, не игнорируем)
- `LIMIT + no price` → `400 Validation Error`
- `qty <= 0` → `400 Validation Error`
- `unknown exchangeConnectionId` → `404 Not Found`
- `cross-workspace connection` → `404 Not Found` (не раскрываем существование)

## 4) Файлы изменений

| Файл | Тип |
|------|-----|
| `apps/api/prisma/schema.prisma` | добавлены enums + модель `TerminalOrder`, relation в `Workspace` и `ExchangeConnection` |
| `apps/api/prisma/migrations/20260222a_add_terminal_orders/migration.sql` | новая миграция |
| `apps/api/src/lib/bybitOrder.ts` | новый: Bybit V5 private API (placeOrder, getOrderStatus, mapBybitStatus, sanitizeBybitError) |
| `apps/api/src/routes/terminal.ts` | добавлены `POST /terminal/orders`, `GET /terminal/orders/:id`, `GET /terminal/orders` |
| `apps/web/src/app/terminal/page.tsx` | добавлен order panel (connection selector, BUY/SELL, MARKET/LIMIT, qty, price, submit, status row) |
| `docs/openapi/openapi.yaml` | добавлены `CreateOrderRequest` + `TerminalOrderView` schemas + 3 новых path entry |
| `docs/steps/09b-stage-9b-terminal-manual-order.md` | этот файл |

## 5) Verification commands

### Предварительно

```sh
export BASE=http://localhost:3000/api/v1

# Получить токен
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}' | jq -r '.accessToken')

WORKSPACE_ID=<your-workspace-id>
CONN_ID=<exchange-connection-id>  # из GET /exchanges
```

### Create MARKET order → 201

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"type\":\"MARKET\",\"qty\":0.001}" | jq .
# → 201, {id, symbol, side:"BUY", type:"MARKET", status:"SUBMITTED", exchangeOrderId:"...", НЕТ apiKey/secret/encryptedSecret}
```

### Create LIMIT order → 201

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"SELL\",\"type\":\"LIMIT\",\"qty\":0.001,\"price\":100000}" | jq .
# → 201, {id, symbol, side:"SELL", type:"LIMIT", price:"100000", status:"SUBMITTED", ...}
```

### LIMIT без price → 400

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"type\":\"LIMIT\",\"qty\":0.001}" | jq .
# → 400, Problem Details, errors:[{field:"price", message:"price is required..."}]
```

### MARKET с price → 400

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"type\":\"MARKET\",\"qty\":0.001,\"price\":60000}" | jq .
# → 400, "price must not be set for MARKET orders"
```

### Invalid qty → 400

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"type\":\"MARKET\",\"qty\":-1}" | jq .
# → 400, errors:[{field:"qty", message:"qty must be a positive number"}]
```

### Invalid symbol → 422

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"FAKEXYZ999\",\"side\":\"BUY\",\"type\":\"MARKET\",\"qty\":0.001}" | jq .
# → 422, "Exchange rejected order: Bybit API error ..."
```

### Without auth → 401

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .
# → 401
```

### Cross-workspace connection → 404

```sh
curl -s -X POST $BASE/terminal/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: <OTHER_WORKSPACE_ID>" \
  -H "Content-Type: application/json" \
  -d "{\"exchangeConnectionId\":\"$CONN_ID\",\"symbol\":\"BTCUSDT\",\"side\":\"BUY\",\"type\":\"MARKET\",\"qty\":0.001}" | jq .
# → 403 (resolveWorkspace rejects the workspace) or 404 (connection belongs to other workspace)
```

### No apiKey/secret/encryptedSecret in response

```sh
curl -s -X POST $BASE/terminal/orders ... | jq 'has("apiKey"), has("secret"), has("encryptedSecret")'
# → false false false
```

### Get order status → 200 (with live Bybit sync for SUBMITTED)

```sh
ORDER_ID=<id from create response>
curl -s "$BASE/terminal/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" | jq .
# → 200, {id, status:"FILLED"|"SUBMITTED"|..., exchangeOrderId:"...", ...}
```

### List orders → 200

```sh
curl -s "$BASE/terminal/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" | jq 'length, .[0].status'
# → number, "FILLED"|...
```

## 6) Acceptance checklist (Stage 9b)

- [x] Manual order flow реализован (Market/Limit)
- [x] Используется ExchangeConnection из Stage 8
- [x] Все endpoints защищены `authenticate`
- [x] Везде используется `resolveWorkspace()`
- [x] Ошибки обрабатываются стабильно (Problem Details 400/401/403/404/422/502)
- [x] Секреты не возвращаются в API (`orderView()` projection — без apiKey/encryptedSecret)
- [x] OpenAPI обновлён (CreateOrderRequest, TerminalOrderView, 3 пути)
- [x] Нет scope creep в SL/TP/advanced orders
- [x] Handover notes добавлены (раздел 7)
- [x] Verification воспроизводим (curl команды выше)

## 7) Handover для Stage 10 (Strategy Authoring UX) / дальнейшего terminal flow

### Что готово после Stage 9b

**Backend:**
- `POST /terminal/orders` — полный Market/Limit ордерный flow через Bybit V5
- `GET /terminal/orders/:id` — live status sync (SUBMITTED/PARTIALLY_FILLED → Bybit)
- `GET /terminal/orders` — список последних 50 ордеров workspace
- `TerminalOrder` DB модель (`id`, `workspaceId`, `exchangeConnectionId`, `symbol`, `side`, `type`, `qty`, `price`, `status`, `exchangeOrderId`, `error`, timestamps)
- `apps/api/src/lib/bybitOrder.ts` — reusable Bybit private API client (sign, place, getStatus)

**Frontend:**
- Order panel в `/terminal`: connection selector, BUY/SELL toggle, MARKET/LIMIT, qty, price, submit, status row с Refresh

### Что осталось для расширения terminal flow

Deferred items (для Stage 10+):

1. **Order cancel** — `DELETE /terminal/orders/:id` → `POST /v5/order/cancel`
2. **Open positions** — `GET /terminal/positions?symbol=...&connectionId=...` → `/v5/position/list`
3. **SL/TP** — можно добавить в `POST /terminal/orders` body (`stopLoss`, `takeProfit`)
   после согласования contract расширения
4. **Symbol/lot-size validation** — pre-validate qty/price против Bybit instrument info
   (`GET /v5/market/instruments-info`) перед отправкой
5. **Spot/Inverse categories** — сейчас только `linear` (perpetuals)
6. **`POST /exchanges/:id/test`** — заменить demo-first stub на реальный `GET /v5/account/info`
7. **Order history pagination** — `GET /terminal/orders` сейчас возвращает last 50; добавить cursor

### Ограничения demo-first (остаются)

- `apiKey` хранится plain text (deferred production improvement)
- Нет ротации ключей
- `POST /exchanges/:id/test` всё ещё demo-first stub (Stage 9b обходит через реальный ордер)
- Категория `linear` hardcoded (spot/inverse — deferred)

## 8) Deviations

Одно отклонение от spec:

**MARKET + price → 400 (отклоняем, не игнорируем)**
Задача допускала оба варианта: "либо игнорировать, либо 400".
Выбрано: **400 Bad Request** (`"price must not be set for MARKET orders"`).
Обоснование: clean contract важнее удобства — клиент не должен предполагать, что биржа
проигнорирует нежелательный параметр. Задокументировано в spec (раздел 3).

Нет других отклонений от Stage 9b scope.
