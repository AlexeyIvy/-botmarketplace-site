# Stage 19 — Research Data Pipeline (datasets, reproducibility, realism) — Spec v2.2
**Status:** Draft v2.2 (v2.1 + CI example + chunking wording + tests aligned with project docs)
**Baseline:** `main` after Stage 18 (AI Actions), Stage 16 Settings complete
**Goal:** Сделать Lab/Backtest "research-grade": фиксируем датасеты (dataset freeze), обеспечиваем воспроизводимость на уровне данных (datasetHash + engineVersion), добавляем честную модель исполнения (fees/slippage), вводим data quality, лимиты и ретеншн.

---

## 1) Background & Problem

Сейчас:
- Market data берётся "по запросу" (candles), без гарантии "тот же набор данных".
- Backtest результаты могут плавать из-за live fetch, отсутствия dataset hashing/metadata и отсутствия execution realism.
- Нет формализованного качества данных (gaps/dupes/sanity).
- Нет защиты VPS от бесконечного роста data storage.

---

## 2) Stage 19 Objective (что должно получиться)

1) **Dataset freeze**: backtest/lab использует **datasetId**, а не live-fetch.
2) **Reproducibility**: результаты повторяются при одинаковых:
   - datasetId/datasetHash
   - fee/slippage/fillAt
   - engineVersion
3) **Data quality**: фиксируем gaps/dupes/sanity и принимаем решение READY/PARTIAL/FAILED по правилам.
4) **Execution realism**: fees + slippage применяются по строго заданным формулам.
5) **Limits + retention**: лимиты диапазона и retention 90 дней для хранения candles.
6) **UI transparency**: в Lab результатах показываем datasetHash + quality + execution params + engineVersion.

---

## 3) Key Architecture Decisions (v2.2)

### 3.1 Interval types (CRITICAL)
В проекте уже есть enum `Timeframe` (например M1/M5/M15/H1) для стратегий.
Рыночный слой свечей НЕ должен переиспользовать `Timeframe` напрямую.

Вводим отдельный enum для рыночных свечей:
- `CandleInterval = M1 | M5 | M15 | M30 | H1 | H4 | D1`

Маппинг UI/Terminal интервалов:
- 1 → M1
- 5 → M5
- 15 → M15
- 30 → M30
- 60 → H1
- 240 → H4
- D → D1

Примечание: стратегии могут не иметь M30/H4/D1; такие датасеты создаются через прямой POST /lab/datasets.

### 3.2 engineVersion source (CRITICAL)
В production git sha недоступен. Источник через env:
- `COMMIT_SHA` (инжектится CI/CD при деплое)
Если не задан, fallback: `"unknown"`.

Рекомендуемый способ инъекции:
- Dockerfile:
  - `ARG COMMIT_SHA`
  - `ENV COMMIT_SHA=$COMMIT_SHA`
- CI build:
  - `--build-arg COMMIT_SHA=$(git rev-parse HEAD)`

### 3.3 Market data shared (CRITICAL)
MarketCandle — **общая таблица**, НЕ workspace-scoped.
MarketDataset — workspace-scoped (dataset принадлежит workspace).

---

## 4) Data model (Prisma)

### 4.1 MarketCandle (shared)
- id
- exchange (например BYBIT)
- symbol (BTCUSDT)
- interval (CandleInterval)
- openTimeMs (BIGINT/number) — миллисекунды UTC
- open, high, low, close (DECIMAL/NUMERIC)
- volume (DECIMAL/NUMERIC)
- createdAt

Constraints / Indexes:
- UNIQUE(exchange, symbol, interval, openTimeMs)
- INDEX(exchange, symbol, interval, openTimeMs DESC)

### 4.2 MarketDataset (workspace-scoped snapshot)
- id (datasetId)
- workspaceId (FK)
- exchange
- symbol
- interval (CandleInterval)
- fromTsMs (BIGINT)
- toTsMs (BIGINT)
- fetchedAt
- datasetHash (sha256 hex)
- candleCount
- qualityJson (json)
- engineVersion (from COMMIT_SHA)
- status: READY | PARTIAL | FAILED
- createdAt

Concurrency/dedup:
- UNIQUE(workspaceId, exchange, symbol, interval, fromTsMs, toTsMs)

### 4.3 BacktestResult / Lab result binding (existing table)
В существующую таблицу результата backtest добавить поля:
- datasetId (FK MarketDataset, nullable если legacy)
- datasetHash (string)
- feeBps (int)
- slippageBps (int)
- fillAt (string, default "CLOSE")
- engineVersion (string)

Примечание: существующее поле interval в BacktestResult остаётся как есть для backward-compat; источник интервала для новых прогонов — MarketDataset.interval по datasetId.

---

## 5) datasetHash definition (CRITICAL, deterministic)

datasetHash = SHA256 по **канонической строке**, сформированной так:

1) свечи сортируются по `openTimeMs` ASC
2) на каждой свече формируется строка:

`openTimeMs|open|high|low|close|volume`

где:
- openTimeMs: integer as string
- цены/volume нормализуются:
  - форматирование идёт **от значений, прочитанных из БД** (Prisma.Decimal), а не от промежуточного Number() из fetch
  - для каждого DECIMAL поля использовать `.toFixed(8)`
  - **ровно 8 знаков** после точки

Пример:
`1709251200000|67000.00000000|67120.50000000|66810.25000000|66950.75000000|123.45000000`

3) Все строки join через `\n`, затем sha256(hex).

---

## 6) Candle ingestion + dataset creation

### 6.1 Create dataset flow (transactional)
`POST /api/v1/lab/datasets` (auth + resolveWorkspace)

Input:
- exchange
- symbol
- interval (CandleInterval)
- fromTs (ISO) или fromTsMs
- toTs (ISO) или toTsMs

Flow:
1) validate limits (см. §9)
2) fetch candles from exchange (Bybit helper уже есть)
3) МАППИНГ ВРЕМЕНИ (обязателен):
   - bybitCandles.Candle использует поле `openTime` (ms)
   - при записи в MarketCandle делать: `openTimeMs = candle.openTime`
4) upsert candles into MarketCandle (by unique key)
   - делать батчами (chunked upserts) для снижения пикового потребления памяти
   - важно: chunking внутри одной транзакции НЕ уменьшает длительность lock, поэтому timeout обязателен
5) query candles from DB in [fromTsMs, toTsMs]
6) compute qualityJson + status
7) compute datasetHash (см. §5 — строго от DB Decimal.toFixed(8))
8) upsert MarketDataset по UNIQUE(workspaceId, exchange, symbol, interval, fromTsMs, toTsMs)
9) return datasetId + hash + quality + status

**CRITICAL:** шаги 4–8 выполнять в Prisma `$transaction`.
Для больших объёмов:
- использовать chunked upserts внутри транзакции
- поставить timeout транзакции (например 30s)

### 6.2 Concurrent requests
Два параллельных запроса на тот же dataset:
- должны завершиться одним dataset record (upsert + unique key)
- без дублей

---

## 7) Data quality rules (CRITICAL)

### 7.1 qualityJson schema (фиксированная, без двусмысленности)
`qualityJson` должен быть объектом со следующими полями:

- intervalMs: number
- candleCount: number
- dupeAttempts: number
- gapsCount: number
- maxGapMs: number
- sanityIssuesCount: number
- sanityDetails: array<{ openTimeMs: number, issue: string }>

Пример значения (одной строкой):
`qualityJson = {"intervalMs":900000,"candleCount":1234,"dupeAttempts":0,"gapsCount":2,"maxGapMs":1800000,"sanityIssuesCount":0,"sanityDetails":[{"openTimeMs":1709251200000,"issue":"close_out_of_range"}]}`

### 7.2 READY / PARTIAL / FAILED
- FAILED если:
  - sanityIssuesCount > 0
  - ИЛИ maxGapMs > 5 * intervalMs
- PARTIAL если:
  - sanityIssuesCount == 0
  - но gapsCount > 0 (мелкие пропуски)
- READY если:
  - sanityIssuesCount == 0
  - gapsCount == 0

---

## 8) Execution realism (fees + slippage) — formulas (CRITICAL)

Параметры:
- feeBps (int, default например 6)
- slippageBps (int, default например 2)
- fillAt: фиксируем "CLOSE" (v2.2)

Entry (buy):
- effectiveEntry = fillPrice * (1 + (feeBps + slippageBps)/10000)

Exit (sell):
- effectiveExit = fillPrice * (1 - (feeBps)/10000)

Backward compat:
- если feeBps/slippageBps не переданы → defaults 0/0

---

## 9) Limits + rate limits + retention (CRITICAL)

### 9.1 Hard limits (фиксированные)
- max range: 365 days
- max candles per dataset: 100_000
- retention for MarketCandle: 90 days (configurable)

Legacy backtest:
- текущие legacy лимиты (например MAX_CANDLES=2000) остаются для старого пути backtest без dataset
- лимит 100k относится к dataset creation

### 9.2 Rate limits (API)
- POST /lab/datasets: 10 req/min (per user/workspace)
- GET /lab/datasets/*: 60 req/min
Существующий rate limit для /lab/backtest (например 5/min) не менять в Stage 19.

### 9.3 Retention mechanism
Retention выполняется в существующем цикле botWorker polling loop:
- не чаще 1 раза в час (timestamp-gated)
- удаляем MarketCandle старше 90 дней
- логируем deleted count

---

## 10) Backtest / Lab integration

### 10.1 Dataset-first contract (Stage 19 scope)
В Stage 19 реализуем только datasetId-first.

Backtest endpoint должен принимать:
- datasetId
- execution params (feeBps, slippageBps, fillAt="CLOSE")

Fallback (создавать dataset внутри backtest по range params) — deferred (Stage 20+).

### 10.2 What must be stored in BacktestResult
- datasetId
- datasetHash
- feeBps
- slippageBps
- fillAt="CLOSE"
- engineVersion=COMMIT_SHA

---

## 11) UI transparency (Lab)

В Lab UI добавить блок "Data snapshot":
- datasetId, datasetHash, fetchedAt, candleCount
- quality summary (gapsCount/maxGapMs/dupeAttempts/sanityIssuesCount)
- feeBps, slippageBps, fillAt, engineVersion

Re-run with same dataset: deferred (Stage 20).

---

## 12) Out of scope (NOT in Stage 19)
- orderbook/trades streaming
- HFT engine
- complex execution model (partial fills, latency)
- portfolio multi-asset simulation
- re-run button (Stage 20)

---

## 13) Implementation split (final)

### Stage 19a — Dataset layer (candles) + hashing + quality
- MarketCandle + MarketDataset + migration
- POST/GET /lab/datasets
- datasetHash (DB Decimal.toFixed(8))
- quality rules + status
- transactional upsert + dataset creation (+ chunking + timeout)

### Stage 19b — Reproducibility binding
- BacktestResult migration (datasetId/hash/fee/slip/fillAt/engineVersion)
- backtest запускается по datasetId
- Lab UI показывает dataset snapshot

### Stage 19c — Fees + retention + dataset rate limits
- fee/slippage formulas (defaults 0/0 for legacy)
- retention hook в botWorker (hourly, timestamp-gated)
- rate limits /lab/datasets (10/min POST, 60/min GET)

---

## 14) Acceptance Criteria
1) datasetId + datasetHash exist and stable
2) qualityJson produced; READY/PARTIAL/FAILED follows rules
3) backtest stores datasetId/hash + engineVersion + fee/slippage/fillAt
4) same datasetId + same params → same metrics
5) fees/slippage affect results deterministically
6) limits/rate limits/retention prevent runaway storage
7) UI shows dataset snapshot metadata

---

## 15) Verification & Tests (aligned with project docs)

В проекте "source of truth" по проверкам — `deploy/smoke-test.sh` и подход curl-чеков как в RC checklist.
Stage 19 добавляет новые проверки (Section 19) и manual checks.

### 15.1 Manual curl checks (как в RC checklist стиле)
Переменные:
- BASE=https://botmarketplace.store/api/v1
- TOKEN и WS_ID получены через существующий auth flow

A) Create dataset (expected 201/200 + fields):
- POST /lab/datasets → 201 и поля datasetId, datasetHash, status, qualityJson
- Повтор того же POST → тот же datasetId (или тот же hash) по upsert policy, без дублей

B) Quality schema:
- GET /lab/datasets/:id → qualityJson содержит все 7 полей

C) Limits:
- диапазон >365 дней → 400 "range too large"
- запрос, превышающий 100k свечей → 400 "too many candles"

D) Backtest dataset binding:
- POST /lab/backtest с datasetId → 202
- GET /lab/backtest/:id → поля datasetId/datasetHash/feeBps/slippageBps/fillAt/engineVersion присутствуют

E) Reproducibility:
- повторить backtest на том же datasetId с теми же fee/slip → метрики совпадают (PnL/trades/winrate/DD)

F) Fees effect:
- fee=0 slip=0 vs fee=6 slip=5 → PnL уменьшается

G) Retention:
- вставить свечу older than 90d (или подождать) → botWorker log "deleted N" и запись исчезает

### 15.2 Required additions to deploy/smoke-test.sh (Stage 19)
Добавить новую секцию (например "Section 19 — Datasets & Reproducibility") с проверками:

- 19.1 POST /lab/datasets (BTCUSDT M15 30d) → 201 + datasetId/hash present
- 19.2 повтор POST /lab/datasets с теми же параметрами → тот же dataset record (upsert), hash стабильный
- 19.3 GET /lab/datasets/:id → 200 + qualityJson содержит 7 полей
- 19.4 POST /lab/datasets range >365d → 400
- 19.5 POST /lab/datasets request >100k candles → 400
- 19.6 POST /lab/backtest с datasetId → 202
- 19.7 GET /lab/backtest/:id → datasetId/hash + fee/slip/fillAt/engineVersion присутствуют
- 19.8 (опционально) fee/slip non-zero влияет на PnL (если метрика доступна без флейка)

---

## 16) Deliverables
- docs/steps/19-stage-19-research-data-pipeline.md (this spec)
- migrations + schema updates
- dataset endpoints (POST/GET) + OpenAPI updates
- backtest binding + UI snapshot
- retention + dataset rate limits
- stage report (PR links, verification)
