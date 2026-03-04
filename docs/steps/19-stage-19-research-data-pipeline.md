# Stage 19 — Research Data Pipeline (datasets, reproducibility, realism) — Spec v2

**Status:** Draft v2 (reviewed by expert, corrections applied)
**Baseline:** `main` after Stage 18 (AI Actions complete), Stage 16 Settings complete
**Branch:** `claude/stage-19-data-pipeline-doc-Y5XOe`

**Goal:** Сделать research/backtest "research-grade": фиксируем датасеты, обеспечиваем воспроизводимость на уровне данных, добавляем базовый реализм исполнения (fees/slippage), даём пользователю прозрачность "на каких данных считали".

---

## Экспертный аудит v1 → v2: найденные проблемы

Перед спецификацией — перечень критических недоработок оригинального черновика, которые были исправлены в v2.

| # | Проблема | Статус в v2 |
|---|----------|-------------|
| 1 | Тип `interval` в `MarketCandle` не определён (enum vs string, конфликт с `Timeframe`) | Решено: новый enum `CandleInterval` |
| 2 | Формат canonical candle list для `datasetHash` не описан | Решено: точный алгоритм SHA-256 |
| 3 | Источник `engineVersion` не указан | Решено: env var `COMMIT_SHA` |
| 4 | Граница PARTIAL vs FAILED не определена | Решено: конкретные пороги |
| 5 | Изменения в существующей таблице `BacktestResult` не перечислены | Решено: явный ALTER |
| 6 | Модель fees/slippage в движке не формализована | Решено: точные формулы |
| 7 | `fillAt = close \| nextOpen` — не зафиксировано одно значение | Решено: `fillAt = close` |
| 8 | `qualityJson` не имеет схемы | Решено: JSON schema |
| 9 | Конкурентное создание одинакового dataset не обработано | Решено: upsert-стратегия |
| 10 | `MarketCandle` ошибочно может трактоваться как workspace-scoped | Решено: явно shared |
| 11 | Rate limits для новых endpoints отсутствуют | Решено: добавлены |
| 12 | Максимальный диапазон/лимиты не зафиксированы (только "например") | Решено: точные числа |
| 13 | Retention: нет механизма реализации | Решено: в worker polling loop |
| 14 | "Re-run with same dataset" противоречит (mandatory vs deferred) | Решено: явно deferred → Stage 20 |
| 15 | Транзакционность upsert + dataset creation не описана | Решено: Prisma `$transaction` |
| 16 | `fromTs`/`toTs` формат "ISO или ms" — надо выбрать одно | Решено: ISO string в API, DateTime в БД |
| 17 | Индекс по `BacktestResult.datasetId` отсутствует | Решено: добавлен |
| 18 | Список допустимых интервалов Bybit не определён | Решено: явный allowlist |
| 19 | `POST /lab/backtest` изменения body не специфицированы | Решено: явная схема |
| 20 | `MarketDataset` — UNIQUE constraint на concurrent creation | Решено: составной unique |

---

## 1. Background & Problem

Платформа умеет: стратегии/версии, боты и рантайм, Lab/backtest.
Research даёт "плавающие" результаты из-за:

- live-fetch данных при каждом запуске (разные свечи при повторе)
- отсутствия dataset versioning + hash (невозможно доказать воспроизводимость)
- отсутствия data quality проверок (gaps, duplicates, bad OHLCV)
- отсутствия модели комиссий и проскальзывания
- отсутствия прозрачности для пользователя

---

## 2. Stage 19 Objective

1. **Dataset freeze** — backtest использует зафиксированный snapshot (`datasetId` + `datasetHash`), а не live свечи.
2. **Reproducibility** — повторный backtest на том же `datasetId` с теми же параметрами даёт идентичные метрики.
3. **Realism** — учитываются комиссии и проскальзывание.
4. **Data quality** — дедуп, gap detection, sanity OHLCV.
5. **Retention/scale** — VPS не переполняется.
6. **UI transparency** — в Lab показываем `datasetHash`, параметры fees/slippage, `engineVersion`.

---

## 3. Scope (Must-have)

### A. Новые Prisma-модели

#### 3.A.1 Новый enum `CandleInterval`

```prisma
/// Bybit kline intervals supported for ingestion.
/// Separate from Timeframe (bot domain) to allow future additions (D, W).
enum CandleInterval {
  ONE        // "1"   — 1 minute
  FIVE       // "5"   — 5 minutes
  FIFTEEN    // "15"  — 15 minutes
  THIRTY     // "30"  — 30 minutes
  SIXTY      // "60"  — 60 minutes (1 hour)
  TWOFOURTY  // "240" — 4 hours
  DAILY      // "D"   — daily
}
```

**Mapping `CandleInterval` → Bybit interval string:**
```
ONE → "1", FIVE → "5", FIFTEEN → "15", THIRTY → "30",
SIXTY → "60", TWOFOURTY → "240", DAILY → "D"
```

**Mapping `CandleInterval` → intervalMs (для gap detection):**
```
ONE → 60_000, FIVE → 300_000, FIFTEEN → 900_000, THIRTY → 1_800_000,
SIXTY → 3_600_000, TWOFOURTY → 14_400_000, DAILY → 86_400_000
```

#### 3.A.2 `MarketCandle` — SHARED (без workspaceId, общая для всех)

```prisma
/// Raw OHLCV candle data — shared across all workspaces (market data is not user-specific).
/// Use Decimal for financial precision; do NOT use Float.
model MarketCandle {
  id          String         @id @default(uuid())
  exchange    String         // "BYBIT"
  symbol      String         // "BTCUSDT"
  interval    CandleInterval
  openTimeMs  BigInt         // ms since epoch (Bybit returns ms)
  open        Decimal        @db.Decimal(18, 8)
  high        Decimal        @db.Decimal(18, 8)
  low         Decimal        @db.Decimal(18, 8)
  close       Decimal        @db.Decimal(18, 8)
  volume      Decimal        @db.Decimal(24, 8)
  createdAt   DateTime       @default(now())

  @@unique([exchange, symbol, interval, openTimeMs])
  @@index([exchange, symbol, interval, openTimeMs(sort: Desc)])
}
```

> **Важно:** `MarketCandle` не имеет `workspaceId`. Рыночные данные одинаковы для всех воркспейсов — хранить их per-workspace значило бы умножить объём без смысла.

#### 3.A.3 `MarketDataset` — workspace-scoped

```prisma
enum DatasetStatus {
  READY    // quality ok, dataset usable
  PARTIAL  // minor gaps/issues, usable with warning
  FAILED   // critical issues, should not be used
}

/// A named snapshot of candle data for a given workspace + symbol + interval + range.
model MarketDataset {
  id           String        @id @default(uuid())
  workspaceId  String
  exchange     String
  symbol       String
  interval     CandleInterval
  fromTs       DateTime      // inclusive, aligned to candle boundary
  toTs         DateTime      // inclusive, aligned to candle boundary
  fetchedAt    DateTime      @default(now())
  datasetHash  String        // SHA-256 hex (see §3.C for computation)
  candleCount  Int
  qualityJson  Json          // schema: see §3.C.3
  engineVersion String       // value of env COMMIT_SHA at ingestion time
  status       DatasetStatus @default(READY)

  workspace  Workspace        @relation(fields: [workspaceId], references: [id], onDelete: Cascade)
  backtests  BacktestResult[]

  @@unique([workspaceId, exchange, symbol, interval, fromTs, toTs, datasetHash])
  @@index([workspaceId, exchange, symbol, interval, fetchedAt(sort: Desc)])
}
```

#### 3.A.4 Изменения в существующей `BacktestResult`

Добавить новые поля (nullable для обратной совместимости):

```prisma
model BacktestResult {
  // ... existing fields remain unchanged ...

  // Stage 19 additions:
  datasetId    String?        // FK → MarketDataset.id
  datasetHash  String?        // redundant snapshot (for quick display without join)
  engineVersion String?       // git commit at backtest time
  feeBps       Float?         // e.g. 6.0
  slippageBps  Float?         // e.g. 2.0
  fillAt       String?        // fixed: "close"

  dataset      MarketDataset? @relation(fields: [datasetId], references: [id], onDelete: SetNull)

  @@index([datasetId])        // NEW INDEX — add to existing indexes
  // ... keep all existing indexes ...
}
```

> Поле `datasetHash` дублируется в `BacktestResult` намеренно — для быстрого отображения в UI без JOIN. При отображении нужно показывать значение из самого `BacktestResult` (не дёргать dataset endpoint).

#### 3.A.5 Prisma Workspace relation update

```prisma
model Workspace {
  // existing ...
  datasets MarketDataset[]  // NEW
}
```

---

### B. Candle Ingestion + Dataset Creation

#### 3.B.1 Разрешённые интервалы и лимиты

```
Supported intervals: ONE, FIVE, FIFTEEN, THIRTY, SIXTY, TWOFOURTY, DAILY
Max range per request: 365 days (=31_536_000_000 ms)
Max candles per dataset: 100_000
```

При превышении лимитов → `400 Bad Request` с понятным сообщением.

#### 3.B.2 Алгоритм `createDataset(workspaceId, exchange, symbol, interval, fromTs, toTs)`

```
1. Validate:
   - interval ∈ {ONE, FIVE, FIFTEEN, THIRTY, SIXTY, TWOFOURTY, DAILY}
   - toTs - fromTs ≤ 365 days
   - fromTs < toTs

2. Align fromTs/toTs to nearest candle boundary (floor to intervalMs):
   alignedFrom = floor(fromMs / intervalMs) * intervalMs
   alignedTo   = floor(toMs   / intervalMs) * intervalMs

3. Fetch from exchange (bybitCandles.fetchCandles):
   maxCandles = min(100_000, ceil((alignedTo - alignedFrom) / intervalMs) + 1)
   rawCandles = await fetchCandles(symbol, intervalStr, alignedFrom, alignedTo, maxCandles)

4. Upsert into MarketCandle in a single Prisma $transaction:
   for each candle in rawCandles:
     prisma.marketCandle.upsert({
       where: { exchange_symbol_interval_openTimeMs: { exchange, symbol, interval, openTimeMs: BigInt(c.openTime) } },
       create: { ...candle fields... },
       update: {},  // no-op on conflict — data is immutable historical price
     })

5. Re-query from DB to get the authoritative ordered list:
   dbCandles = prisma.marketCandle.findMany({
     where: { exchange, symbol, interval,
              openTimeMs: { gte: BigInt(alignedFrom), lte: BigInt(alignedTo) } },
     orderBy: { openTimeMs: 'asc' },
   })

6. Compute datasetHash (see §3.C.1)

7. Run quality checks (see §3.C.2), produce qualityJson + status

8. Upsert MarketDataset:
   prisma.marketDataset.upsert({
     where: { workspaceId_exchange_symbol_interval_fromTs_toTs_datasetHash: {...} },
     create: { ...all fields... },
     update: { fetchedAt: now() },  // idempotent: same hash = same data
   })

9. Return datasetId, datasetHash, status, qualityJson, candleCount
```

> **Concurrency**: шаг 8 использует upsert по составному unique key (workspaceId + exchange + symbol + interval + fromTs + toTs + datasetHash). Если два параллельных запроса создают одинаковый dataset — второй просто обновляет `fetchedAt`, коллизий нет.

> **Terminal не затрагивается**: `GET /terminal/candles/:symbol` продолжает вызывать `fetchCandles()` напрямую. Dataset-слой работает только для Lab/Research.

---

### C. Data Quality

#### 3.C.1 `datasetHash` — точный алгоритм

Хешируем только candle-данные из БД (авторитетный источник, шаг 5 выше):

```
canonical = JSON.stringify(
  dbCandles.map(c => ({
    t: String(c.openTimeMs),   // BigInt → string
    o: c.open.toFixed(8),      // Decimal → string with 8 decimal places
    h: c.high.toFixed(8),
    l: c.low.toFixed(8),
    c: c.close.toFixed(8),
    v: c.volume.toFixed(8),
  }))
)
datasetHash = crypto.createHash('sha256').update(canonical, 'utf8').digest('hex')
```

**Важно:**
- Ключи объектов в алфавитном порядке (t, o, h, l, c, v)
- Числа как строки с 8 знаками после запятой (избегаем float drift)
- Candles отсортированы по `openTimeMs ASC` (шаг 5 гарантирует это)
- `JSON.stringify` без пробелов (compact)

Любые изменения этого алгоритма → **новая версия хеша**; обратная несовместимость намеренна.

#### 3.C.2 Gap Detection + Sanity Checks

```
intervalMs = intervalMsMap[interval]  // из §3.A.1

dupeAttempts = rawCandles.length - dbCandles.length  // разница до/после dedupe

// Gap detection (по dbCandles, отсортированным)
gapsCount = 0
maxGapMs  = 0
for i in [1 .. dbCandles.length - 1]:
  delta = dbCandles[i].openTimeMs - dbCandles[i-1].openTimeMs
  if delta > intervalMs * 1.5:   // tolerance 50% (учитываем DST и биржевые паузы)
    gapsCount++
    maxGapMs = max(maxGapMs, delta)

// Sanity OHLC
sanityIssues = []
for each candle c in dbCandles:
  if c.low > c.open or c.low > c.close: sanityIssues.push({ t: c.openTimeMs, issue: "low>oc" })
  if c.high < c.open or c.high < c.close: sanityIssues.push({ t: c.openTimeMs, issue: "high<oc" })
  if c.volume < 0: sanityIssues.push({ t: c.openTimeMs, issue: "vol<0" })
  if c.low <= 0 or c.open <= 0 or c.high <= 0 or c.close <= 0:
    sanityIssues.push({ t: c.openTimeMs, issue: "zero_price" })

// Статус
if sanityIssues.length > 0 or (gapsCount > 0 and maxGapMs > 5 * intervalMs):
  status = FAILED
elif gapsCount > 0:
  status = PARTIAL
else:
  status = READY
```

#### 3.C.3 `qualityJson` schema

```json
{
  "gapsCount": 0,
  "maxGapMs": 0,
  "dupeAttempts": 0,
  "sanityIssuesCount": 0,
  "sanityDetails": [
    { "t": 1700000000000, "issue": "low>oc" }
  ]
}
```

> `sanityDetails` ограничить первыми 50 записями (truncate при логировании).

---

### D. Reproducibility Contract

Для каждого `BacktestResult` фиксировать (все поля nullable, null = pre-Stage-19 backtest):

| Поле | Источник |
|------|----------|
| `datasetId` | `MarketDataset.id` |
| `datasetHash` | `MarketDataset.datasetHash` (snapshot) |
| `engineVersion` | `process.env.COMMIT_SHA ?? 'unknown'` |
| `feeBps` | input parameter |
| `slippageBps` | input parameter |
| `fillAt` | `"close"` (hardcoded v1) |

**Гарантия воспроизводимости:** при одинаковых `datasetId` + `feeBps` + `slippageBps` + `riskPct` → идентичные метрики. Это возможно потому что:
1. `dbCandles` загружаются строго по `datasetId` (а не live-fetch)
2. Движок `runBacktest` — pure function без side effects
3. Все числа — детерминированы (Decimal → number → fixed точность)

---

### E. Backtest Realism (Fees + Slippage)

#### 3.E.1 Параметры

```
feeBps     — комиссия биржи, basis points (1 bps = 0.01%). Default: 6.0 (Bybit maker ~0.02%, taker ~0.06%)
slippageBps — проскальзывание, basis points. Default: 5.0
fillAt     — "close" (зафиксировано; nextOpen — deferred)
```

#### 3.E.2 Формулы применения в `runBacktest`

Fees применяются при **входе** и **выходе**. Slippage — только при **входе** (пессимистичная модель: вошли дороже, вышли по цене).

```
// Entry
fillPrice    = close[i]  (candle signal)
effectiveEntry = fillPrice * (1 + (feeBps + slippageBps) / 10_000)

// SL exit
effectiveSlExit = slPrice * (1 - feeBps / 10_000)

// TP exit
effectiveTpExit = tpPrice * (1 - feeBps / 10_000)

// NEUTRAL exit (end of data)
effectiveNeutralExit = lastClose * (1 - feeBps / 10_000)

// PnL calculation (all exits)
pnlPct = ((effectiveExit - effectiveEntry) / effectiveEntry) * 100
```

**Изменение в `backtest.ts`:**
Сигнатура функции расширяется до:
```typescript
interface BacktestParams {
  riskPct: number;
  feeBps: number;     // default 0 для обратной совместимости
  slippageBps: number; // default 0
}

export function runBacktest(candleData: Candle[], params: BacktestParams): BacktestReport
```

> `BacktestReport` должен включать: `feeBps`, `slippageBps`, `fillAt` в метаданных (не в tradeLog).

#### 3.E.3 `TradeRecord` изменения

```typescript
export interface TradeRecord {
  entryTime: number;
  exitTime: number;
  entryPrice: number;        // fillPrice (до комиссий — для отладки)
  effectiveEntryPrice: number; // NEW: с fees+slippage
  exitPrice: number;         // target price (SL/TP/last)
  effectiveExitPrice: number;  // NEW: с fees
  slPrice: number;
  tpPrice: number;
  outcome: "WIN" | "LOSS" | "NEUTRAL";
  pnlPct: number;            // считается от effectiveEntry → effectiveExit
}
```

---

### F. UI Transparency (Lab)

В карточке результата Lab отображать (если поля не null):

```
Dataset:  abc123...def456  (первые 8 символов hash + копировать)
Fetched:  2024-01-15 14:32 UTC  (fetchedAt)
Candles:  8640  (candleCount)
Quality:  ✓ READY | ⚠ PARTIAL (N gaps) | ✗ FAILED
Fees:     6 bps | Slippage: 5 bps | Fill: close
Engine:   a1b2c3d4  (engineVersion, первые 8 символов)
```

**"Re-run with same dataset"** — явно deferred → Stage 20. В v1 не реализуется.

---

### G. Retention / Limits

#### 3.G.1 Лимиты при создании dataset

```
MAX_DATASET_DAYS    = 365        // env DATASET_MAX_DAYS, default 365
MAX_DATASET_CANDLES = 100_000   // env DATASET_MAX_CANDLES, default 100_000
```

Проверяется в `createDataset()` до fetch. Нарушение → `400 Bad Request`.

#### 3.G.2 Retention policy для MarketCandle

```
CANDLE_RETENTION_DAYS = 90   // env, default 90
```

Реализация: добавить в **существующий** bot worker polling loop (`botWorker.ts`) ежечасную задачу:

```
каждые 60 итераций цикла (≈ раз в 4 минуты * 60 = раз в ~4 часа):
  DELETE FROM "MarketCandle"
  WHERE "createdAt" < NOW() - INTERVAL '${CANDLE_RETENTION_DAYS} days'
  LIMIT 10_000  // batched delete, не блокировать БД
```

> Prisma: `prisma.marketCandle.deleteMany({ where: { createdAt: { lt: cutoff } }, take: 10_000 })`

---

## 4. Out of Scope (NOT Stage 19)

- WebSocket streaming данных
- Orderbook/trades ingestion (real-time)
- HFT microstructure engine
- Distributed storage / data warehouse
- Partial fills, queue position, latency model
- Multi-asset portfolio simulation
- "Re-run with same dataset" кнопка в UI
- Dataset sharing между workspaces

---

## 5. API Changes

### 5.A Новые endpoints (workspace-scoped, auth + resolveWorkspace required)

#### `POST /api/v1/lab/datasets`

**Rate limit:** 10 req/min per workspace

**Request body:**
```json
{
  "exchange": "BYBIT",
  "symbol": "BTCUSDT",
  "interval": "FIFTEEN",
  "fromTs": "2024-01-01T00:00:00.000Z",
  "toTs": "2024-06-30T23:59:59.999Z"
}
```

**Validation:**
- `exchange`: только `"BYBIT"` (v1)
- `symbol`: string, 1–20 chars, uppercase
- `interval`: строго из enum `CandleInterval` (ONE|FIVE|FIFTEEN|THIRTY|SIXTY|TWOFOURTY|DAILY)
- `fromTs`, `toTs`: ISO 8601 datetime string
- `toTs - fromTs` ≤ 365 days

**Response 201:**
```json
{
  "datasetId": "uuid",
  "datasetHash": "sha256hex",
  "status": "READY",
  "candleCount": 8640,
  "qualityJson": {
    "gapsCount": 0,
    "maxGapMs": 0,
    "dupeAttempts": 0,
    "sanityIssuesCount": 0,
    "sanityDetails": []
  },
  "fetchedAt": "2024-07-01T12:00:00.000Z"
}
```

**Errors:**
- `400` — validation failure (bad interval, range > 365d, etc.)
- `400` — candle count would exceed 100_000 (с подсчётом expected)
- `502` — Bybit API недоступен
- `401/403` — auth/workspace

---

#### `GET /api/v1/lab/datasets/:id`

**Rate limit:** 60 req/min per workspace

**Response 200:**
```json
{
  "datasetId": "uuid",
  "exchange": "BYBIT",
  "symbol": "BTCUSDT",
  "interval": "FIFTEEN",
  "fromTs": "2024-01-01T00:00:00.000Z",
  "toTs": "2024-06-30T23:59:59.999Z",
  "fetchedAt": "2024-07-01T12:00:00.000Z",
  "datasetHash": "sha256hex",
  "candleCount": 8640,
  "qualityJson": { ... },
  "engineVersion": "a1b2c3d4",
  "status": "READY"
}
```

**Errors:**
- `404` — dataset не найден или принадлежит другому workspace

---

#### `GET /api/v1/lab/datasets` (optional, для списка)

**Rate limit:** 30 req/min per workspace

**Query:** `?symbol=BTCUSDT&interval=FIFTEEN&limit=20&offset=0`

**Response 200:**
```json
{
  "items": [ ...dataset objects... ],
  "total": 42
}
```

---

### 5.B Изменения в `POST /api/v1/lab/backtest`

**Добавить в request body (все поля опциональны):**
```json
{
  "strategyId": "uuid",
  "symbol": "BTCUSDT",
  "interval": "15",
  "fromTs": "...",
  "toTs": "...",

  // Stage 19 additions:
  "datasetId": "uuid",          // если задан — использовать этот dataset (игнорирует fromTs/toTs/symbol/interval)
  "feeBps": 6.0,                // default 0.0
  "slippageBps": 5.0,           // default 0.0
  "autoCreateDataset": true     // default false; если true и datasetId не задан — создать dataset автоматически
}
```

**Логика:**
```
if datasetId provided:
  load dataset, verify workspaceId ownership
  fetch candles from DB by datasetId
elif autoCreateDataset = true:
  dataset = createDataset(workspaceId, symbol, interval, fromTs, toTs)
  if dataset.status = FAILED → return 400 ("Dataset quality FAILED: cannot run backtest")
  use dataset candles
else:
  // legacy path: live fetch (unchanged)
  fetch candles live via fetchCandles()
  datasetId = null, datasetHash = null
```

**В `BacktestResult` записывать** (при использовании dataset):
```
datasetId, datasetHash, engineVersion, feeBps, slippageBps, fillAt = "close"
```

---

## 6. Implementation Split

### Stage 19a — Dataset Layer + Hashing + Quality

**Задачи:**
1. Prisma миграция: `CandleInterval` enum, `MarketCandle`, `MarketDataset`, `DatasetStatus` enum
2. `apps/api/src/lib/datasetService.ts` — функция `createDataset()` (ingestion + upsert + hash + quality)
3. Маршруты `/api/v1/lab/datasets` (POST, GET :id, GET list)
4. Unit тест `datasetHash` (детерминизм)
5. Integration test: создать dataset → повторить → hash совпадает

**Acceptance 19a:**
- `POST /lab/datasets` для BTCUSDT FIFTEEN за 7 дней → статус READY, `candleCount > 0`
- Повтор с тем же диапазоном → тот же `datasetHash`
- БД не дублирует свечи (проверить COUNT)
- `qualityJson` содержит корректные поля

---

### Stage 19b — Backtest Reproducibility + UI

**Задачи:**
1. Prisma миграция: новые поля `BacktestResult` (`datasetId`, `datasetHash`, `engineVersion`, `feeBps`, `slippageBps`, `fillAt`)
2. Обновить `POST /lab/backtest` — поддержка `datasetId` + `autoCreateDataset`
3. Обновить backtest route: загружать candles из DB по `datasetId`
4. Записывать metadata в `BacktestResult`
5. Lab UI: отображать dataset metadata в карточке результата

**Acceptance 19b:**
- Backtest A с `datasetId` + Backtest B с тем же `datasetId` и параметрами → идентичные PnL/winrate/DD
- UI отображает `datasetHash` (первые 8 символов), `engineVersion`, `fetchedAt`, `candleCount`, quality status

---

### Stage 19c — Realism (Fees + Slippage) + Retention

**Задачи:**
1. Обновить `backtest.ts`: `runBacktest(candles, params: BacktestParams)`
2. Применить формулы fees/slippage к entry/exit
3. Обновить `TradeRecord` с `effectiveEntryPrice`, `effectiveExitPrice`
4. Включить `feeBps`, `slippageBps`, `fillAt` в `BacktestReport`
5. Retention job в `botWorker.ts` polling loop
6. Env vars: `COMMIT_SHA`, `DATASET_MAX_DAYS`, `DATASET_MAX_CANDLES`, `CANDLE_RETENTION_DAYS`

**Acceptance 19c:**
- Backtest с feeBps=0/slippageBps=0 vs feeBps=6/slippageBps=5 → totalPnlPct хуже при fees > 0
- Запрос диапазона > 365 дней → 400 с понятной ошибкой
- Запрос > 100_000 candles → 400 с понятной ошибкой

---

## 7. Security Requirements

- Все новые endpoints: `authenticate` + `resolveWorkspace` (как существующие `/lab/*`)
- `MarketDataset` принадлежит workspace → проверять `workspaceId` при каждом GET
- `MarketCandle` — только чтение через dataset layer; прямого API нет
- Никаких exchange credentials в dataset layer (market data = public)
- Логи содержат только: `datasetId`, `datasetHash` (первые 16 символов), `candleCount` — НЕ сырые данные свечей
- Rate limits на все новые endpoints (см. §5.A)
- `sanityDetails` в логах — truncate до 10 записей

---

## 8. Acceptance Criteria (Stage 19 overall)

| # | Критерий | Проверяется |
|---|----------|-------------|
| AC-1 | `POST /lab/datasets` возвращает `datasetId` + `datasetHash` + `status` | Manual / API test |
| AC-2 | Повтор того же dataset → тот же `datasetHash` | §9.A |
| AC-3 | `qualityJson` содержит `gapsCount`, `maxGapMs`, `dupeAttempts`, `sanityIssuesCount` | Manual |
| AC-4 | Backtest на одном `datasetId` дважды → одинаковые метрики | §9.B |
| AC-5 | feeBps=6/slippageBps=5 → PnL хуже чем feeBps=0 | §9.C |
| AC-6 | Запрос >365 дней → 400 с message | §9.D |
| AC-7 | UI показывает datasetHash, engineVersion, fees, quality | Manual |
| AC-8 | BUILD проходит, тесты зелёные | CI |
| AC-9 | Свечи в MarketCandle не дублируются (UNIQUE constraint) | DB check |
| AC-10 | `BacktestResult` содержит `datasetId`, `datasetHash`, `feeBps`, `slippageBps` | DB check |

---

## 9. Verification (manual, reproducible)

### 9.A Dataset Creation & Hash Stability

```bash
# Step 1: Create dataset
curl -X POST https://localhost:3001/api/v1/lab/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exchange":"BYBIT","symbol":"BTCUSDT","interval":"FIFTEEN","fromTs":"2024-01-01T00:00:00Z","toTs":"2024-01-07T23:59:59Z"}'

# Expected: status=READY, candleCount=672 (7 days * 24h * 4 candles/h = 672), datasetHash=<sha256>

# Step 2: Repeat same request
# Expected: same datasetHash

# Step 3: Check DB
SELECT COUNT(*) FROM "MarketCandle" WHERE symbol='BTCUSDT' AND interval='FIFTEEN';
# Should match candleCount (no duplicates)
```

### 9.B Backtest Reproducibility

```bash
# Run A
curl -X POST .../lab/backtest -d '{"strategyId":"...","datasetId":"<id>","feeBps":6,"slippageBps":5}'
# Run B (same params)
curl -X POST .../lab/backtest -d '{"strategyId":"...","datasetId":"<id>","feeBps":6,"slippageBps":5}'

# Compare: trades, wins, winrate, totalPnlPct, maxDrawdownPct must be IDENTICAL
```

### 9.C Fees/Slippage Effect

```bash
# No fees
curl -X POST .../lab/backtest -d '{"strategyId":"...","datasetId":"<id>","feeBps":0,"slippageBps":0}'
# With fees
curl -X POST .../lab/backtest -d '{"strategyId":"...","datasetId":"<id>","feeBps":6,"slippageBps":5}'

# Check: totalPnlPct(with fees) < totalPnlPct(no fees)
```

### 9.D Limits

```bash
# Range > 365 days
curl -X POST .../lab/datasets -d '{"...","fromTs":"2022-01-01T00:00:00Z","toTs":"2024-01-01T00:00:00Z"}'
# Expected: 400 {"error":"Range exceeds maximum of 365 days"}
```

---

## 10. Deliverables

| Артефакт | Путь | Стадия |
|----------|------|--------|
| Этот документ (финальный) | `docs/steps/19-stage-19-research-data-pipeline.md` | — |
| Prisma migration 19a | `apps/api/prisma/migrations/...` | 19a |
| `datasetService.ts` | `apps/api/src/lib/datasetService.ts` | 19a |
| Dataset routes | `apps/api/src/routes/datasets.ts` | 19a |
| Updated `backtest.ts` | `apps/api/src/lib/backtest.ts` | 19c |
| Updated backtest route | `apps/api/src/routes/lab.ts` | 19b |
| Prisma migration 19b | `apps/api/prisma/migrations/...` | 19b |
| Lab UI dataset display | `apps/web/src/...` | 19b |
| Retention in botWorker | `apps/api/src/lib/botWorker.ts` | 19c |
| PR links, verification report | PR description | — |

---

## 11. Env Variables (новые)

| Переменная | Описание | Default |
|------------|----------|---------|
| `COMMIT_SHA` | Git commit hash, инжектируется CI/CD при деплое | `"unknown"` |
| `DATASET_MAX_DAYS` | Максимальный диапазон dataset в днях | `365` |
| `DATASET_MAX_CANDLES` | Максимальное число свечей в dataset | `100000` |
| `CANDLE_RETENTION_DAYS` | Возраст свечей для удаления (retention) | `90` |

Добавить в `.env.example`:
```
COMMIT_SHA=unknown
DATASET_MAX_DAYS=365
DATASET_MAX_CANDLES=100000
CANDLE_RETENTION_DAYS=90
```

---

## Экспертное резюме

### Оценка выполнимости

**Stage 19a** — Высокая. Prisma-модели просты, `bybitCandles.ts` уже решает задачу fetch+paginate. Единственная нетривиальная часть — детерминированный `datasetHash`, но алгоритм выше полностью специфицирован. Оценка: 2–3 дня.

**Stage 19b** — Высокая. Механическое связывание `BacktestResult` с `MarketDataset`. Изменения в route + UI. Оценка: 1–2 дня.

**Stage 19c** — Высокая. Формулы fees/slippage просты и уже специфицированы. Retention — одна строка в polling loop. Оценка: 1–2 дня.

**Итого: 5–7 дней** для всех трёх стадий последовательно.

### Архитектурные решения

1. **`MarketCandle` без `workspaceId`** — правильное решение. Рыночные данные публичны и одинаковы для всех workspace. Хранить per-workspace умножало бы объём данных в N раз без смысла.

2. **`Decimal` для OHLCV** — обязательно. Float даст drift на суммировании PnL. Пример: `0.1 + 0.2 = 0.30000000000000004` в float, `0.10000000` + `0.20000000` = `0.30000000` в Decimal.

3. **`fillAt = close` (не `nextOpen`)** — консервативный, правильный выбор для v1. `nextOpen` усложняет логику без существенного выигрыша в реализме для дневных/часовых свечей.

4. **Retention в worker loop** — допустимо для VPS-решения. Production-grade требовал бы pg-cron или внешнего scheduler. Для текущей аудитории — достаточно.

### Риски

- **Bybit rate limits** при создании большого dataset (365 дней DAILY = 365 свечей, нет риска; 365 дней 1m = 525_600 свечей — превысит `MAX_DATASET_CANDLES`). Лимит 100_000 candles решает это.
- **Длительность fetch** для больших диапазонов (напр. 90 дней 1m = 129_600 запросов к Bybit). Рекомендуется: для Stage 19 ограничить минимальный interval до FIFTEEN (15m), либо предупреждать пользователя о времени ожидания через response с polling.
- **Hash алгоритм изменился** — если кто-то уже хранит датасеты с другим хешем (не ожидается на Stage 19, но стоит зафиксировать в docs как breaking change).
