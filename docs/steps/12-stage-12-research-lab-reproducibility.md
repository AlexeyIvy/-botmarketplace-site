# Stage 12 — Research Lab Results & Reproducibility

## Цель

Сделать Research Lab воспроизводимым и пригодным для практической работы:
- запуск replay/backtest с pinned StrategyVersion
- детерминированные результаты на одинаковом наборе данных
- сохранение результатов с reproducibility metadata
- минимальный UI-отчёт (PnL, winrate, drawdown, trades) + engine version badge

## Что было найдено в Stage 5 (baseline)

- `BacktestResult` модель с: `strategyId`, `symbol`, `interval`, `fromTs`, `toTs`, `status`, `reportJson`
- Lab routes: `POST /lab/backtest`, `GET /lab/backtest/:id`, `GET /lab/backtests`
- Детерминированный движок (`backtest.ts`) — pure function, без IO ✓
- Bybit candles fetcher (`bybitCandles.ts`) ✓
- UI с формой, метриками, историей ✓

## Пробелы, закрытые в Stage 12

| Пробел | Решение |
|--------|---------|
| `strategyId` → latest version (не воспроизводимо) | Добавлен `strategyVersionId` (pinned) |
| Нет cross-workspace check на version level | `403` при чужом `strategyVersionId` |
| Нет `engineVersion` в БД | Колонка + поле в `reportJson` |
| Нет endpoint `/result` | `GET /lab/backtest/:id/result` |
| `tradeLog` в reportJson (большой) | Теперь только metrics, без tradeLog |
| UI не показывает reproducibility | Reproducibility badge + Ver колонка в истории |

## Архитектурные решения

### Детерминизм

Гарантируется 3-уровневым фиксированием:
1. **StrategyVersion** — DSL и `riskPct` фиксированы на момент создания версии
2. **Bybit candles** — одинаковый `symbol + interval + fromTs + toTs` → одинаковые данные
3. **Engine** — pure function без state, без randomness; `engineVersion = "1"`

Правило округления:
- `winrate`: `Math.round(x * 10000) / 10000` (4 знака)
- `totalPnlPct`, `maxDrawdownPct`: `Math.round(x * 100) / 100` (2 знака)
- Float rounding допускается до `±0.01%` при сравнении двух прогонов (платформенный float)

### Reproducibility identity

Два прогона считаются воспроизводимыми если совпадают:
- `strategyVersionId` (одинаковый → одинаковый `riskPct`)
- `symbol`, `interval`, `fromTs`, `toTs`
- `engineVersion = "1"`

### Security

Все endpoints: `onRequest: [app.authenticate]` + `resolveWorkspace(request, reply)`

Чужой `strategyVersionId` → `403 Forbidden` (не `404`)

## Файлы, изменённые в Stage 12

```
apps/api/prisma/schema.prisma
apps/api/prisma/migrations/20260223a_stage12_backtest_reproducibility/migration.sql
apps/api/src/routes/lab.ts
apps/web/src/app/lab/page.tsx
docs/openapi/openapi.yaml
docs/steps/12-stage-12-research-lab-reproducibility.md   (этот файл)
```

## API контракты (стабильные после Stage 12)

### POST /api/v1/lab/backtest

```json
{
  "strategyVersionId": "uuid",   // preferred — pinned
  "strategyId": "uuid",          // fallback — latest version
  "symbol": "BTCUSDT",
  "interval": "15",
  "fromTs": "2026-01-01T00:00:00Z",
  "toTs": "2026-02-01T00:00:00Z"
}
```

Ответ: `202 Accepted` → `BacktestResult`

### GET /api/v1/lab/backtest/:id

Полная запись (status + reportJson).

### GET /api/v1/lab/backtest/:id/result

Чистый summary с metrics. `202` если ещё не готово.

### GET /api/v1/lab/backtests

Список последних 50 прогонов для workspace.

## Validation rules

| Условие | Код |
|---------|-----|
| Нет `strategyVersionId` и нет `strategyId` | 400 |
| Чужой `strategyVersionId` или `strategyId` | 403 |
| Невалидный `interval` | 400 |
| `fromTs >= toTs` | 400 |
| Невалидные ISO dates | 400 |
| Без auth header | 401 |
| Чужой backtest ID | 404 |
| Bybit недоступен | status=FAILED + errorMessage |

## Verification commands

```bash
BASE=https://botmarketplace.store
AUTH="Authorization: Bearer <token>"
WS="X-Workspace-Id: <wsId>"

# 1) Create run with strategyVersionId
curl -s -X POST "$BASE/api/v1/lab/backtest" \
  -H "$AUTH" -H "$WS" -H "Content-Type: application/json" \
  -d '{"strategyVersionId":"<versionId>","symbol":"BTCUSDT","interval":"15",
       "fromTs":"2026-01-01T00:00:00Z","toTs":"2026-02-01T00:00:00Z"}'
# → 202, id returned

# 2) Get status
curl -s "$BASE/api/v1/lab/backtest/<id>" -H "$AUTH" -H "$WS"

# 3) Get result summary
curl -s "$BASE/api/v1/lab/backtest/<id>/result" -H "$AUTH" -H "$WS"
# → { engineVersion, metrics: { trades, wins, winrate, totalPnlPct, maxDrawdownPct, candles } }

# 4) Without auth → 401
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/lab/backtest" \
  -H "Content-Type: application/json" -d '{}'

# 5) No strategy ref → 400
curl -s -X POST "$BASE/api/v1/lab/backtest" -H "$AUTH" -H "$WS" \
  -H "Content-Type: application/json" \
  -d '{"fromTs":"2026-01-01T00:00:00Z","toTs":"2026-02-01T00:00:00Z"}'

# 6) Cross-workspace → 403
# (use token from userA, provide strategyVersionId owned by userB)

# 7) Reproducibility: run A and run B same input → same trades/winrate/totalPnlPct
BT_A=$(curl -s -X POST ...) && BT_B=$(curl -s -X POST ...)
# compare metrics manually or via jq
```

## Deferred (не в Stage 12 scope)

- Parameter optimization / hyperparameter search
- Trade log storage (tradeLog исключён из reportJson для компактности)
- Multi-asset backtests
- Candle data caching (каждый прогон запрашивает Bybit заново)
- Dataset hash (детерминизм доказывается идентичными inputs, не hash)
- Deep charting / PnL curve visualization

---

## Handover для Stage 13 — Observability & Ops Baseline

### Стабильные контракты (можно использовать как baseline для мониторинга)

- `BacktestResult.status` enum: `PENDING → RUNNING → DONE | FAILED`
- `reportJson` fields: `{ trades, wins, winrate, totalPnlPct, maxDrawdownPct, candles, engineVersion }`
- `engineVersion = "1"` — текущий алгоритм; при изменении алгоритма bump до "2"

### Точки наблюдаемости для Stage 13

1. **Backtest async failure** — сейчас `status=FAILED + errorMessage` в БД, но нет алертинга
   - Добавить structured log: `{ event: "backtest_failed", btId, error }` с correlation ID

2. **Bybit upstream errors** — `fetchCandles` может бросать network error, это уходит в `errorMessage`
   - Добавить retry с exponential backoff или dead-letter marking

3. **Backtest duration** — нет метрики времени выполнения
   - Добавить `durationMs` в `reportJson` или отдельную колонку

4. **Rate limit** — `POST /lab/backtest` ограничен 5/min per IP
   - В Stage 13 добавить per-workspace rate limit и логирование rejected requests

5. **Candle fetch volume** — каждый прогон запрашивает до 2000 свечей
   - В Stage 13 рассмотреть caching layer (Redis / in-memory) для популярных symbol+interval+range

### Ограничения, которые остаются

- Нет retry при Bybit unavailability (status=FAILED без повтора)
- Нет очереди/приоритизации (все backtests запускаются немедленно в process)
- Нет audit trail для lab runs (кто запустил, когда)
- Нет уведомлений о завершении (polling only)
