# 52. Multi-Interval Dataset Bundle

Статус: draft  
Владелец: core trading / data  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`

## Контекст

- MTF-инфраструктура runtime уже работает: `apps/api/src/lib/mtf/intervalAlignment.ts` (определяет `CandleBundle`, `createCandleBundle`), `apps/api/src/lib/mtf/mtfIndicatorResolver.ts` (резолвер индикаторов с `sourceTimeframe`). Это slice 1+2 из issue #134.
- DSL-evaluator принимает `bundle: CandleBundle` (`apps/api/src/lib/dslEvaluator.ts:749`); `DslIndicatorRef.sourceTimeframe` (`:134`) — supported.
- Что **не подключено**:
  - `BacktestSweep.datasetId` — single (`apps/api/prisma/schema.prisma:691`).
  - `WalkForwardRun.datasetId` — single (`:741`).
  - `Bot.timeframe: Timeframe` — единичный (`:147`).
  - `botWorker` загружает свечи только primary TF: `prisma.marketCandle.findMany({ where: { symbol } })` (`apps/api/src/lib/botWorker.ts:1467`) — без фильтра по interval, без bundle. Это значит: даже если DSL ссылается на 1H через `sourceTimeframe`, runtime не получает 1H-свечей.
- `MarketCandle` имеет `interval CandleInterval` (`apps/api/prisma/schema.prisma:518`) — данные доступны.
- `Timeframe` enum (`:89`): M1/M5/M15/H1. `CandleInterval` enum (`:497`): M1/M5/M15/M30/H1/H4/D1.

## Цель

Соединить уже существующий MTF-runtime с продакшен-путём загрузки данных. Добавить `datasetBundleJson Json?` в `Bot`, `BacktestSweep`, `WalkForwardRun`. Расширить `botWorker` и `runBacktest` так, чтобы при наличии bundle грузились multi-TF свечи и передавались в evaluator. Single-TF путь остаётся default (bundle = `null`).

## Не входит

- Новая таблица `DatasetBundle` (см. `docs/50 §A2` — отдельная таблица в v1 не нужна).
- Расширение `Timeframe` enum или Bot multi-TF API на верхнем уровне (Bot.timeframe = primary TF, остальное в bundle).
- Изменения в `mtf/*` модулях — они уже корректные.
- Streaming/incremental подгрузка свечей по WS для context TF — берём с MarketCandle table; обновление context-TF в realtime — follow-up.
- UI выбора bundle в Lab → Build (DSL author указывает `sourceTimeframe`, mapping interval→datasetId — техническая деталь runtime; для пресетов задаётся в `docs/53`/`docs/54`).

## Архитектурные решения

### A1. Bundle = `Record<CandleInterval, datasetId>` для backtest, `Record<CandleInterval, true>` для runtime

Backtest нуждается в snapshot (datasetId привязан к immutable окну). Runtime бот тянет live MarketCandle и может работать просто со списком интервалов: `{"M5": true, "H1": true}`. Чтобы не плодить две схемы, используем единый формат `Record<string, string | true>`:

- В `BacktestSweep.datasetBundleJson` и `WalkForwardRun.datasetBundleJson` значения = `datasetId`.
- В `Bot.datasetBundleJson` значения = `true` (live-режим).

Primary TF дублируется: для backtest равен `datasetId` (исторический snapshot), для бота — равен `true` (берётся primary timeframe из `bot.timeframe`).

### A2. Single source of truth для primary

`Bot.timeframe` остаётся primary TF. `BacktestSweep.datasetId` остаётся primary dataset. Bundle — это **дополнение**: если ключ в bundle совпадает с primary — это noop, primary не дублируется в загрузке.

### A3. Lazy load для context-TF

В `botWorker.ts` context-TF свечи запрашиваются только когда DSL содержит хотя бы один `sourceTimeframe != primary` (определяется через статический анализ DSL — `extractRequiredIntervals(dsl)`). Это избавляет single-TF боты от лишних DB-запросов.

---

## Задачи

### 52-T1: Prisma — добавить `datasetBundleJson`

**Файлы:** `apps/api/prisma/schema.prisma`, новая миграция.

**Шаги:**
1. Добавить колонку в три модели:
   - `Bot.datasetBundleJson Json?` рядом с `timeframe` (`:147`).
   - `BacktestSweep.datasetBundleJson Json?` рядом с `datasetId` (`:691`).
   - `WalkForwardRun.datasetBundleJson Json?` рядом с `datasetId` (`:741`).
2. Все nullable, без default — отсутствие = single-TF.
3. `prisma migrate dev --name add_dataset_bundle` — additive, без backfill.
4. Документировать формат в JSDoc-комментах рядом с каждой колонкой:
   ```
   /// Optional MTF bundle. Backtest: { interval: datasetId }.
   /// Runtime: { interval: true }. Primary TF can be omitted.
   ```

**Тест-план:** миграция чистая; существующие тесты зелёные.

**DoD:** миграция применилась локально и в CI.

---

### 52-T2: Helper `extractRequiredIntervals(dsl)` + загрузчик multi-TF свечей

**Цель:** одна точка истины для определения, какие intervals нужны DSL'у.

**Файлы:** `apps/api/src/lib/mtf/extractRequiredIntervals.ts` (new), `apps/api/src/lib/mtf/loadMultiTfCandles.ts` (new), тесты в `apps/api/tests/lib/mtf/`.

**Шаги:**
1. `extractRequiredIntervals(dsl, primaryTf)`: обходит DSL JSON, собирает все `sourceTimeframe` из `DslIndicatorRef`. Возвращает `Set<CandleInterval>` без primary (primary всегда нужен и не повторяется).
2. `loadMultiTfCandles(opts)`:
   ```ts
   {
     symbol: string;
     primaryInterval: CandleInterval;
     contextIntervals: Set<CandleInterval>;
     barsPerInterval: number; // default 200
     source: 'live' | { datasetMap: Record<CandleInterval, string> };
   }
   ```
   Live: `prisma.marketCandle.findMany({ symbol, interval })` для каждого + primary. Backtest: `prisma.candle.findMany({ datasetId })` (или существующий путь через `MarketDataset`/`Candle` — следовать тому, что использует `runBacktest` сейчас).
3. На выходе — `CandleBundle` (через `createCandleBundle` из `mtf/intervalAlignment.ts`).
4. Если context-interval запрошен, но в БД < 2 баров → log warn + не включать в bundle (DSL fall back на primary через `mtfIndicatorResolver.ts`).

**Тест-план:**
- Unit `extractRequiredIntervals`: DSL без `sourceTimeframe` → пустой set; DSL с двумя разными context TF → set длины 2; primary не включается.
- Unit `loadMultiTfCandles` с моком prisma: возвращает bundle с тремя ключами (primary + 2 context).
- Edge: context-TF без данных → warn, bundle без этого TF.

**DoD:** `tsc --noEmit` зелёный; новые тесты зелёные.

---

### 52-T3: Интегрировать в `botWorker`

**Файлы:** `apps/api/src/lib/botWorker.ts`, `apps/api/tests/botWorker/*`.

**Шаги:**
1. Перед загрузкой свечей (`botWorker.ts:1467`):
   - Прочитать `bot.datasetBundleJson` (новое поле).
   - Вызвать `extractRequiredIntervals(dsl, bot.timeframe)` → `contextIntervals`.
   - Если `bot.datasetBundleJson` отсутствует **и** `contextIntervals` пуст → старый путь (single-TF), без правок.
   - Иначе: `loadMultiTfCandles({ symbol: bot.symbol, primaryInterval: bot.timeframe, contextIntervals, barsPerInterval: 200, source: 'live' })`.
2. Передать полученный `bundle` в `evaluateEntry` / `evaluateExit` (через существующее опциональное поле — проверить сигнатуру в `signalEngine.ts`/`exitEngine.ts`; если bundle ещё не пробрасывается до evaluator-а — добавить optional param и пробросить).
3. **Bug-фикс** (попутно): добавить `interval: bot.timeframe` в `prisma.marketCandle.findMany` (`botWorker.ts:1467`). Сейчас фильтр только по symbol — нелатентный риск засорения свечами не из primary TF. Это закрывается одной строкой в этой же задаче.
4. Логирование: при первом контекст-TF запросе на runId — info-лог `bot=<id> mtf-intervals=[M5,H1]`.

**Тест-план:**
- Unit с моком prisma: `bot.datasetBundleJson = null`, DSL без `sourceTimeframe` → один запрос свечей с фильтром `{ symbol, interval }`.
- Unit: DSL с `sourceTimeframe="H1"` → два запроса (M5, H1), bundle передан в evaluator.
- Регресс: существующий happy-path test без MTF проходит без правок.

**DoD:** существующие botWorker-тесты зелёные; новые покрывают MTF-ветвь; latency single-TF не вырос (bundle = null short-circuit'ит логику).

---

### 52-T4: Интегрировать в `runBacktest` + `runSweepAsync` + `runWalkForwardAsync`

**Файлы:** `apps/api/src/lib/backtest.ts`, `apps/api/src/routes/lab.ts`, `apps/api/tests/`.

**Шаги:**
1. `runBacktest(candles, dsl, opts)` — расширить `opts.bundle?: CandleBundle`. Если передан — пробросить в evaluator. Если нет — текущее поведение (только primary). Сигнатура additive.
2. В `POST /lab/backtest` принимать optional `datasetBundleJson` в body. При наличии — `loadMultiTfCandles({ source: { datasetMap } })` → `createCandleBundle` → `runBacktest({ ..., bundle })`.
3. В `POST /lab/backtest/sweep` (`apps/api/src/routes/lab.ts:838`) и `POST /lab/walk-forward` принимать `datasetBundleJson` рядом с `datasetId`. Сохранять в соответствующие колонки. В `runSweepAsync` (`:1258`) и `runWalkForwardAsync` — load bundle ровно один раз перед циклом (как сейчас грузятся primary candles, `:1281`).
4. Валидация: ключи `datasetBundleJson` должны быть валидными `CandleInterval`; primary TF может быть включён или опущен — нормализатор всегда добавляет primary в bundle при недостатке.

**Тест-план:**
- e2e: backtest с одним interval — без правок ответа.
- e2e: backtest с bundle (M5 primary + H1 context) — `report` корректен; вызов `extractRequiredIntervals` подтверждается mock-spy.
- e2e: sweep с bundle — `BacktestSweep.datasetBundleJson` сохранён; runs используют один и тот же bundle.
- Walk-forward: каждый fold использует тот же bundle (датасеты уже привязаны к id, не к окну — окна режутся внутри fold-а).
- Validation: невалидный interval-ключ → 400; primary-only bundle → принимается как noop.

**DoD:** все e2e и unit-тесты зелёные; capability matrix не меняется; `tsc --noEmit` зелёный.

---

### 52-T5: UI — отображение bundle (read-only) + расширение preset instantiate

**Файлы:** `apps/web/src/app/lab/test/*` (отображение в результатах backtest), `apps/api/src/routes/presets.ts` (расширить из `docs/51-T2`).

**Шаги:**
1. В `StrategyPreset.dslJson` уже могут быть `sourceTimeframe`. Расширить `StrategyPreset` колонкой `defaultDatasetBundleJson Json?` (additive миграция в этой же задаче). Это нужно для пресетов SMC/Adaptive/MTF Scalper, которые требуют конкретные TF.
2. В `presets.ts /instantiate` копировать `preset.defaultDatasetBundleJson` в `Bot.datasetBundleJson` (для live runtime значения должны быть `true`-маркеры; преобразование `datasetId → true` делается на момент instantiate, чтобы preset мог быть привязан к историческому датасету для backtest, а бот в runtime брал live).
3. В Lab → Test (results panel) при наличии bundle отображать список TF, например: `MTF: M5 (primary) + H1 (context)`. Без редактирования.
4. Build-страница (Lab) — без изменений: `sourceTimeframe` уже редактируется на уровне DSL-блоков.

**Тест-план:**
- Unit `presets.ts` instantiate: bundle с `datasetId` → бот получает bundle с `true`.
- Manual: preset с bundle инстанцируется → бот в `/factory/bots/[id]` показывает MTF-метку.

**DoD:** `npm run typecheck` зелёный; smoke в браузере прошёл.

---

## Порядок выполнения

```
52-T1 → 52-T2 → 52-T3 → 52-T4 → 52-T5
```

T2 не зависит от T1 (helper'ы — pure functions), но идёт после, чтобы избежать merge-конфликтов в schema. T3 и T4 параллелизуются после T2. T5 — после T4 (и зависит от `docs/51-T2`).

## Зависимости от других документов

- `docs/51-T2` — instantiate-эндпоинт; T5 расширяет его.
- `docs/53` — первый потребитель (Adaptive Regime требует M5 + H1).
- `docs/54` — потребитель (SMC, MTF Scalper требуют multi-TF).

## Backward compatibility

- Все Prisma-миграции additive (новая nullable колонка в трёх таблицах + одна в `StrategyPreset`).
- Существующие боты, sweep'ы, walk-forward — bundle = null → старый путь без изменений.
- `runBacktest(candles, dsl, opts)` — bundle optional, default behavior сохранён.
- `signalEngine`/`exitEngine` — optional bundle param (если ещё не есть — добавить как additive).
- Bug-фикс interval-фильтра в botWorker (52-T3 шаг 3) — поведение становится строже, но в проде уже есть только один interval-set per (symbol, exchange) под конкретный таймфрейм бота, так что регрессий не ожидается. Если test-fixtures полагаются на отсутствие фильтра — обновить.

## Ожидаемый результат

- DSL с `sourceTimeframe` работает в продакшене (не только в unit-тестах).
- Backtest, sweep, walk-forward могут принимать multi-interval bundle.
- Preset может задавать дефолтный bundle (используется в `docs/53` и `docs/54`).
- Single-TF код-путь не деградирует: bundle = null short-circuit + helper `extractRequiredIntervals` возвращает пустой set.
