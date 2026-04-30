# 53. Adaptive Regime Bot Activation

Статус: draft  
Владелец: core trading  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Связанные spec'и: `docs/strategies/03-adaptive-regime-bot.md`, `docs/strategies/03a-adaptive-regime-bot-e2e-flow.md`

## Контекст

Adaptive Regime Bot — flagship #2 (`docs/strategies/01-flagship-overview.md`). Логика режимов из spec'а:

- `ADX(14) > 25` → **TREND**: SuperTrend(ATR=55, factor=2.0) на 5m + EMA(200) на 1H. Вход long при `close > EMA200(1H)` и `SuperTrend.direction = up`. Stop loss = swing-low; take profit = SuperTrend flip ИЛИ `3 × ATR`.
- `ADX(14) < 20` → **RANGE**: Bollinger(20, 2σ) + RSI(3). Long при `close < bb.lower` и `RSI(3) < 30`. Short при `close > bb.upper` и `RSI(3) > 70`.
- `20 ≤ ADX ≤ 25` → **TRANSITION**: новых сделок нет, существующие позиции управляются по правилам своего режима.

Что есть в коде:

- 33 примитивных DSL-блока supported (capability matrix `docs/strategies/08-strategy-capability-matrix.md`).
- `compare`, `cross`, `and_gate`, `or_gate`, `enter_adaptive` блоки достаточны для composite-логики (`docs/50 §A3`).
- MTF-runtime готов после `docs/52` (`apps/api/src/lib/mtf/`).
- Preset-инфраструктура готова после `docs/51`.
- Walk-forward: `docs/48` (роут `POST /lab/walk-forward`).
- `Timeframe` enum `apps/api/prisma/schema.prisma:89` — M1/M5/M15/H1. **Timeframe primary = M5, context = H1** — оба покрыты enum'ом.
- Тестовые fixtures для DSL уже используются (`apps/api/tests/fixtures/`).

## Цель

Активировать Adaptive Regime Bot как первый end-to-end флагман:
1. Выразить логику spec'а через DSL (33 блока, никаких новых).
2. Зафиксировать DSL как golden-fixture.
3. Пройти walk-forward acceptance gate (`docs/50 §A5`).
4. Запустить 30-минутный demo smoke в DEMO-аккаунте.
5. Опубликовать как `StrategyPreset(visibility=PUBLIC)` в галерее.

## Не входит

- Расширение evaluator-а под `supertrend_direction` или `bb_rsi_reversion` высокоуровневые имена — всё через примитивы.
- Параметры дисциплины (ATR, factor, RSI period) подбираются вручную из spec'а; sweep-оптимизация — отдельная задача после релиза.
- Multi-symbol параллельный запуск — preset фиксируется на BTCUSDT, пользователь меняет symbol после instantiate.
- Auto-режим переключения параметров (например, factor=1.5 при low-vol vs 2.5 при high-vol) — фиксированные параметры из spec'а.

## Архитектурные решения

### A1. Three-mode DSL через `enter_adaptive`

`enter_adaptive` (один из 33 блоков) принимает branches с условиями. Используем три ветки:
1. `trend_long`: `compare(adx14, ">", 25)` AND `compare(close, ">", ema200_h1)` AND `cross(close, supertrend_55_2, "above")`.
2. `trend_short`: симметрично с `<` и `below`.
3. `range_long`: `compare(adx14, "<", 20)` AND `compare(close, "<", bb_lower_20_2)` AND `compare(rsi3, "<", 30)`.
4. `range_short`: симметрично.

`TRANSITION` (20 ≤ ADX ≤ 25) — это просто **отсутствие** активной ветки: ни одно из 4 условий не сработает. Никакой явной "ничего не делать" ветки не нужно.

### A2. Exit DSL — отдельный набор условий

Spec'и trend и range различают exit-логику. Используем `or_gate` exit:
- Trend-exit: `cross(close, supertrend_55_2, "below")` OR `compare(unrealizedPnlPct, ">", 3*atr_pct)`.
- Range-exit: long: `cross(close, bb_middle_20, "above")`; short: `cross(close, bb_middle_20, "below")`.
- Stop loss: spec говорит "swing-low/high"; в DSL берём фиксированный `compare(low, "<", entry_price - 1.5*atr)` как практичный прокси, документируем в release-checklist'е как trade-off.

### A3. MTF через `sourceTimeframe="H1"` для EMA200

EMA200 — context-индикатор: `{ name: "ema", params: { period: 200 }, sourceTimeframe: "H1" }`. Adaptive Regime требует `datasetBundle = { M5, H1 }` — это первый prod-потребитель `docs/52`.

---

## Задачи

### 53-T1: Golden DSL fixture

**Цель:** один canonical JSON, который компилируется без ошибок и evaluator на синтетических свечах даёт ожидаемые сигналы.

**Файлы:**
- `apps/api/tests/fixtures/strategies/adaptive-regime-btc-5m.json` (new) — DSL.
- `apps/api/tests/fixtures/strategies/adaptive-regime-btc-5m.candles.json` (new) — синтетические свечи M5 + H1.
- `apps/api/tests/strategies/adaptive-regime.test.ts` (new) — golden-test.

**Шаги:**
1. Написать DSL по схеме из A1/A2. Indicators: `adx(14)`, `ema(200)@H1`, `supertrend(55, 2.0)`, `bb(20, 2)`, `rsi(3)`, `atr(14)`.
2. Свечной fixture: 4 сегмента по ~50 баров каждый, чтобы все 4 ветки сработали хотя бы раз: (1) восходящий тренд → trend_long; (2) нисходящий тренд → trend_short; (3) расширенный боковик с touch нижней BB → range_long; (4) с touch верхней BB → range_short. Между сегментами — `TRANSITION` зоны (контролируемая ADX).
3. Тест:
   - `compileDsl(dsl)` — без ошибок (использует существующий compiler `apps/api/src/lib/compiler/index.ts`).
   - `runBacktest(candles, dsl, { feeBps: 10, slippageBps: 5, fillAt: "CLOSE", bundle })` — `report.tradeLog` содержит ровно ожидаемое количество сделок (например, 4: по одной на сегмент).
   - Каждый trade имеет ожидаемый side (long/short) и ожидаемый bar-index entry/exit (deterministic, ±1 бар toleranсe).
4. Bundle создаётся через `createCandleBundle({ M5: candlesM5, H1: candlesH1 })` (mtf-helper уже есть).

**Тест-план:**
- Compile passes.
- 4 ожидаемых сделки в trade log.
- Detereministic prices: fixture зашит, рандом отсутствует.
- Edge: при отсутствии H1-bundle тест падает с понятной ошибкой (gating MTF).

**DoD:** golden-test зелёный; fixture committed.

---

### 53-T2: Walk-forward acceptance run

**Цель:** проверить, что DSL даёт `pnlPct > 0`, `sharpe > 0.3`, `maxDrawdownPct > -25%` на real BTCUSDT 5m+1H данных через `WalkForwardRun`.

**Файлы:** `docs/strategies/release-checklist.md` (расширить из `docs/51-T5`); никаких production-кода правок — операция research-only.

**Шаги:**
1. Создать MarketDataset для BTCUSDT M5 (12 месяцев) и H1 (12 месяцев) — через существующий `/datasets`-flow.
2. Запустить `POST /lab/walk-forward` с:
   - `strategyVersionId` из локального инстанса DSL (через `/lab` UI или прямо `POST /strategies`).
   - `datasetId` = M5 dataset.
   - `datasetBundleJson` = `{"M5": "<m5_id>", "H1": "<h1_id>"}` (`docs/52-T4`).
   - `foldConfig`: `{ isBars: 12000, oosBars: 3000, step: 3000, anchored: false }` → ≥ 6 folds.
3. Дождаться завершения; зафиксировать `aggregateJson` в release-checklist'е — отдельный markdown-блок:
   ```
   ## Adaptive Regime BTC 5m
   - Period: 2025-04..2026-04
   - Folds: 6
   - Median PnL%: ...
   - Median Sharpe: ...
   - Worst-fold drawdown: ...
   - Pass: yes/no
   ```
4. Если результат не проходит acceptance — итерировать параметры (sweep `docs/47` через UI), но **результат не считается gate-пройденным**, пока spec не проходит на консервативных параметрах из `docs/strategies/03-adaptive-regime-bot.md` без существенных правок.

**Тест-план:** не unit-тест, а research-run. Артефакт — `WalkForwardRun.id` + скопированный `aggregateJson` в release-checklist.

**DoD:** один из двух исходов:
- (a) Gate прошёл → continue T3.
- (b) Gate не прошёл → создать issue в `docs/strategies/release-checklist.md` с пометкой `BLOCKED: walk-forward acceptance`. T3..T5 откладываются. Это здоровый исход — пайплайн отработал.

---

### 53-T3: Seed StrategyPreset(adaptive-regime-btc-5m)

**Файлы:** `apps/api/prisma/seed/presets/adaptive-regime-btc-5m.json` (new), `apps/api/prisma/seed.ts`.

**Шаги:**
1. Скопировать DSL из 53-T1 fixture в seed-файл (источник истины — fixture, seed читает один файл).
2. Compile через runtime compiler → `executionPlanJson`.
3. Upsert preset:
   ```
   slug: "adaptive-regime-btc-5m"
   name: "Adaptive Regime — BTC 5m"
   description: "Auto-switching trend/range bot per ADX(14). SuperTrend 55/2.0 on 5m, EMA 200 on 1H, BB+RSI(3) in range."
   category: "adaptive"
   symbol: "BTCUSDT"
   timeframe: M5
   defaultDatasetBundleJson: { "M5": true, "H1": true }
   visibility: PRIVATE  (PUBLIC ставится только после T2 gate'а — manual flip)
   defaultRiskPct: 1.0
   tagsJson: ["mtf", "adaptive", "btc"]
   ```
4. После 53-T2 acceptance pass — отдельной миграцией/admin-вызовом перевести `visibility = PUBLIC`. Это explicit gate-control.

**Тест-план:**
- `prisma db seed` создаёт preset.
- `POST /lab/presets/adaptive-regime-btc-5m/instantiate` создаёт Bot c `datasetBundleJson = { M5: true, H1: true }`.

**DoD:** seed зелёный; instantiate-test зелёный.

---

### 53-T4: Demo smoke run + release-checklist row

**Цель:** 30 минут DEMO-runtime без падений.

**Файлы:** `docs/strategies/release-checklist.md` (запись).

**Шаги:**
1. Instantiate preset через UI Lab Library (`docs/51-T4`) или `POST /lab/presets/.../instantiate`.
2. Привязать DEMO ExchangeConnection (Bybit testnet ключи; sandbox).
3. Перевести бот в `ACTIVE`, запустить.
4. Мониторить 30+ минут: Sentry без unhandled rejections; не более 1 circuit-breaker трипа; нет paniс-логов в `botWorker`.
5. Зафиксировать в release-checklist:
   ```
   ## Adaptive Regime — Demo Smoke
   - Date: 2026-MM-DD
   - Duration: 32 min
   - Trades opened: 1 (closed +0.4%)
   - Sentry incidents: 0
   - Circuit breaker trips: 0
   - Pass: yes
   ```

**Тест-план:** observable через Sentry + `BotEvent` log.

**DoD:** запись в release-checklist пометана `Pass: yes`; иначе T3 visibility остаётся `PRIVATE`.

---

### 53-T5: Capability matrix update + visibility flip

**Файлы:** `docs/strategies/08-strategy-capability-matrix.md`, prod admin-операция (`PATCH /lab/presets/adaptive-regime-btc-5m`).

**Шаги:**
1. Обновить matrix: строка `Adaptive Regime` → `released: yes`, `presetSlug: adaptive-regime-btc-5m`.
2. `PATCH /lab/presets/adaptive-regime-btc-5m { visibility: "PUBLIC" }` — публикация в галерею.

**DoD:** preset виден в Lab Library любому новому пользователю; matrix актуален.

---

## Порядок выполнения

```
53-T1 → 53-T2 → 53-T3 → 53-T4 → 53-T5
```

Каждая задача — gate перед следующей: T2 не запускается без T1 (нужен валидный DSL); T4 не запускается без T3 (нужен seeded preset для instantiate); T5 не делается без T4 pass.

## Зависимости от других документов

- `docs/51-T2`, `docs/51-T3`, `docs/51-T4` — preset CRUD + instantiate + UI.
- `docs/52-T1`–`docs/52-T4` — multi-interval bundle в Bot/sweep/walk-forward + runtime.
- `docs/47` — опциональный sweep при не-прохождении T2 acceptance (для подбора параметров без расширения spec'а).
- `docs/48-T*` — walk-forward инфраструктура (уже закрыта).
- `docs/49` — расширенный report (sharpe, profitFactor) для acceptance-gate.

## Backward compatibility

- Никаких production-кода правок вне seed/fixture/checklist (instantiate-логика и multi-TF runtime приходят из 51/52).
- Preset стартует в `PRIVATE` — публичная галерея не меняется до явного flip'а.

## Ожидаемый результат

- Один публичный preset `adaptive-regime-btc-5m` в галерее.
- Golden DSL-fixture в repo, тест зелёный на CI.
- Walk-forward acceptance row в release-checklist'е.
- Demo smoke row в release-checklist'е.
- Capability matrix обновлена.
- Пайплайн `preset → instantiate → walk-forward → demo smoke → publish` обкатан end-to-end на одной стратегии — это шаблон для `docs/54`.
