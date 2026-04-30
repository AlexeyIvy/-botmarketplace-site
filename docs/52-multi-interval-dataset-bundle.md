# 52. Multi-Interval Dataset Bundle

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Дорожка: A (research → trading workflow)

## Контекст

Текущее состояние (проверено по коду):

- `MarketDataset` — single-interval (поле `interval CandleInterval`, `apps/api/prisma/schema.prisma:497` enum `CandleInterval { M1 M5 M15 M30 H1 H4 D1 }`); один dataset = одна пара `(symbol, interval)`.
- `MarketCandle` хранит свечи по полям `symbol`, `interval`, `openTime` (`schema.prisma`). Уникальность по `(datasetId, openTime)`.
- `botWorker.ts:1467` — load свечей: `prisma.marketCandle.findMany({ where: { symbol } })` — **без фильтра по `interval`**. Это означает, что прямо сейчас runtime тянет свечи всех загруженных интервалов символа, а отбор на стороне применения индикаторов происходит post-factum / неявно. Для multi-TF стратегий это не работает: indicator должен видеть конкретный TF.
- `apps/api/src/lib/mtf/intervalAlignment.ts` — содержит `CandleBundle` тип и helper'ы выравнивания (HTF свеча → набор LTF свечей в её окне). Это инфраструктура уже есть.
- `apps/api/src/lib/mtf/mtfIndicatorResolver.ts` — резолвер индикатора по `sourceTimeframe`.
- `apps/api/src/lib/dslEvaluator.ts:749` — `evaluateExpression` уже принимает `bundle?: CandleBundle` (опционально). DSL-узел `DslIndicatorRef.sourceTimeframe` (`apps/api/src/lib/dslEvaluator.ts:134`) — supported.
- Иными словами: **MTF-инфраструктура в evaluator готова**, но runtime/backtest её не используют — они кормят evaluator одним массивом свечей.
- `BacktestSweep` (`schema.prisma:686`) и `WalkForwardRun` принимают единственный `datasetId`. Lab UI Test/Optimise/Walk-Forward (`apps/web/src/app/lab/test/*`, `apps/web/src/app/lab/walk-forward/*`) — single-dataset селектор.
- Spec MTF Scalper (`docs/strategies/05-mtf-scalper.md`) и Adaptive Regime (`docs/strategies/03-adaptive-regime-bot.md`) явно требуют 2-3 интервала.

## Цель

- Ввести `datasetBundleJson: Record<CandleInterval, datasetId | true>` как additive nullable колонку на `Bot`, `BacktestSweep`, `WalkForwardRun`. Значение `true` означает «использовать любой/первый dataset для этого symbol+interval» (для runtime, где dataset как объект не нужен — нужны просто свечи); явный `datasetId` обязателен для backtest/walk-forward (там ровно конкретные данные нужны).
- Перевести runtime `botWorker.ts` на загрузку bundle (всех нужных TF), передачу `CandleBundle` в `dslEvaluator`. Сохранить старый single-TF режим как fallback, если `datasetBundleJson === null`.
- Перевести backtest `runBacktest` на приём bundle, чтобы acceptance/walk-forward тесты могли запускаться на multi-TF фикстурах.
- Расширить Lab UI селектор с одного dataset до набора (1..N выбранных интервалов из существующих datasets workspace'а).
- Сохранить полную backward compatibility: все существующие single-interval вызовы остаются рабочими.

## Не входит в задачу

- **Введение модели `DatasetBundle` как Prisma-сущности.** Это первое, что напрашивается, и явно отвергается в `docs/50 §Решение 2`: bundle — логическая JSON-структура, не таблица. Меньше миграций, меньше двусторонних связей, меньше каскадных операций.
- **Resampling «на лету».** Если для requested interval нет dataset'а — это ошибка (400 на backtest, runtime fallback на single-TF). Никаких автоматических `M1 → M5` агрегаций в этом документе.
- **Cross-symbol bundles.** Bundle всегда — про один `symbol`. Корзины и портфели — отдельная архитектура.
- **Изменения формата `MarketCandle` или `MarketDataset`.** Только additive поля на `Bot/BacktestSweep/WalkForwardRun`.
- **Ускорение candle loader'а.** Текущий `findMany` остаётся; кэш — простой in-memory LRU (52-T2), без Redis/Bull.
- **Изменение DSL-формата.** `sourceTimeframe` уже есть. Никаких новых DSL-узлов.
- **Mixed-TF execution (open intent on M5, manage on M1).** Order management остаётся на основном TF бота; multi-TF используется только для **сигналов** и **фильтров**, не для exit timing.

## Архитектурные решения

### Решение 1: Bundle = Json field, не отдельная таблица

`Bot.datasetBundleJson Json?` — формат:
```ts
type DatasetBundle = Partial<Record<CandleInterval, string | true>>;
// например:
//   { M5: "ds_abc", H1: "ds_def" }   — backtest / walk-forward (явные id)
//   { M5: true, H1: true }           — runtime (просто список нужных интервалов)
```

Полу-структурированный JSON позволяет в одном поле выразить и режим runtime (где конкретный dataset не нужен — нужны свежие свечи из таблицы `MarketCandle`), и backtest-режим (где конкретные исторические данные обязательны). Альтернатива — два разных поля — делает схему шире без выгоды.

### Решение 2: Bot имеет primary timeframe + bundle

В `Bot.timeframe` остаётся «основной TF» (entry/exit timing). `datasetBundleJson` — **дополнительные** TF, которые подгружаются для evaluator'а, чтобы DSL-блоки с `sourceTimeframe` могли резолвить свои индикаторы. Если `datasetBundleJson` есть, `bot.timeframe` обязан в нём присутствовать.

### Решение 3: `botWorker` не меняет state machine — расширяется только candle-loader

`BotRunState` enum, polling cadence, intent emission — всё остаётся. Единственное изменение — в одном месте (`botWorker.ts:1467`) `findMany({ where: { symbol } })` заменяется на `loadCandleBundle(symbol, datasetBundleJson, lookbackBars)`, который возвращает `CandleBundle`. Дальше `evaluateDsl(dsl, latestCandle, bundle)` — bundle уже supported в evaluator (см. Контекст).

### Решение 4: Backtest получает bundle опционально, default — single-TF

`runBacktest(candles, dsl, opts)` остаётся как есть. Добавляется новая overload `runBacktest({ bundle, dsl, opts })`, где bundle — `Map<CandleInterval, MarketCandle[]>`. Внутри ядра выбирается primary TF (первый ключ или specified в opts.primaryInterval); итерация — по primary candles; в evaluator передаётся bundle с подкачкой LTF/HTF на каждом баре через уже существующий `intervalAlignment.ts` helper.

### Решение 5: UI — pre-existing single-dataset select остаётся, добавляется «advanced»

В Lab Test / Optimise / Walk-Forward панелях текущий dataset-select сохраняется как «primary». Появляется опциональная секция "+ Add timeframe" (раскрывающийся блок), где можно добавить ещё 1-2 интервала с явным `datasetId`. Минимум изменений UI; пользователь, не использующий MTF, не замечает разницы.

---

## Задачи

### 52-T1: Поле `datasetBundleJson` в `Bot`, `BacktestSweep`, `WalkForwardRun`

**Цель:** ввести nullable Json-колонку `datasetBundleJson` на трёх моделях. Чисто схема + миграция, без логики.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — модели `Bot`, `BacktestSweep`, `WalkForwardRun`.
- `apps/api/prisma/migrations/<timestamp>_dataset_bundle/migration.sql`.
- `apps/api/src/types/datasetBundle.ts` (создать) — общий TS-тип + zod-схема + helper-валидация.
- `apps/api/tests/types/datasetBundle.test.ts`.

**Шаги реализации:**
1. В `schema.prisma` каждой из трёх моделей добавить:
   ```prisma
   datasetBundleJson Json?
   ```
2. Миграция: `ALTER TABLE "Bot" ADD COLUMN "datasetBundleJson" JSONB;` + аналогично для `BacktestSweep`, `WalkForwardRun`. Existing rows получают `NULL`.
3. `types/datasetBundle.ts`:
   ```ts
   import { z } from "zod";
   const CANDLE_INTERVALS = ["M1","M5","M15","M30","H1","H4","D1"] as const;
   export const DatasetBundleSchema = z.record(
     z.enum(CANDLE_INTERVALS),
     z.union([z.string().min(1), z.literal(true)]),
   ).refine(b => Object.keys(b).length >= 1 && Object.keys(b).length <= 4,
     { message: "bundle must contain 1..4 intervals" });
   export type DatasetBundle = z.infer<typeof DatasetBundleSchema>;
   ```
   Лимит 4 интервала — практический потолок (большинство TF combos из spec'ов: 2-3); защищает от потенциально дорогих join'ов в loader.
4. Хелперы:
   - `bundleHasInterval(b, i)`, `bundleIntervals(b)`, `bundlePrimaryDatasetId(b, primaryInterval)`.
   - `validateBundleAgainstPrimary(b, primaryInterval)` — проверяет, что primary TF присутствует в bundle.
5. **Никаких backfill'ов.** Все existing rows работают в legacy single-TF режиме.

**Тест-план:**
- `DatasetBundleSchema.parse({ M5: "ds_a", H1: "ds_b" })` → ok.
- `parse({ M5: true })` → ok (runtime-форма).
- `parse({})` → 0 keys, ошибка.
- `parse({ M1:"a", M5:"b", M15:"c", M30:"d", H1:"e" })` → 5 keys, ошибка.
- `parse({ X1: "ds" })` → unknown enum, ошибка.
- `validateBundleAgainstPrimary({ M5: true }, "H1")` → ошибка (primary не в bundle).

**Критерии готовности:**
- Миграция additive, проходит на staging.
- `tsc --noEmit` зелёный.
- Existing тесты `Bot`/`BacktestSweep`/`WalkForwardRun` зелёные без правок.
- Тип `DatasetBundle` экспортирован и используется во всех последующих T-задачах.

---

### 52-T2: Multi-interval candle loader + cache

**Цель:** одна функция `loadCandleBundle(symbol, bundle, lookbackBars)`, возвращающая `CandleBundle` (`Map<CandleInterval, MarketCandle[]>`). Используется и runtime, и backtest.

**Файлы для изменения:**
- `apps/api/src/lib/mtf/loadCandleBundle.ts` (создать).
- `apps/api/src/lib/mtf/intervalAlignment.ts` — экспортировать тип `CandleBundle` если ещё нет.
- `apps/api/tests/lib/mtf/loadCandleBundle.test.ts`.

**Шаги реализации:**
1. Сигнатура:
   ```ts
   export async function loadCandleBundle(args: {
     symbol: string;
     bundle: DatasetBundle;
     lookbackBars: number;          // сколько свечей на TF загрузить (head)
     mode: "runtime" | "backtest";  // runtime → значения true OK; backtest → все ключи должны быть string
     until?: Date;                   // для backtest — верхняя граница; runtime — undefined ⇒ now()
   }): Promise<CandleBundle>;
   ```
2. Валидация: для `mode=backtest` каждое значение в bundle обязано быть string (datasetId). Для `mode=runtime` допустимы оба формата.
3. Реализация:
   - Для каждого `(interval, value) ∈ bundle`:
     - `runtime` + `value=true`: `prisma.marketCandle.findMany({ where: { symbol, interval }, orderBy: { openTime: "desc" }, take: lookbackBars })`. Развернуть в ASC.
     - `runtime` + `value=string`: то же + `datasetId: value`.
     - `backtest`: `prisma.marketCandle.findMany({ where: { datasetId: value, openTime: { lte: until } }, orderBy: { openTime: "desc" }, take: lookbackBars })`.
   - Параллельные запросы (`Promise.all`).
4. **In-memory cache** (LRU, max 64 entries, TTL 30s для runtime; для backtest — без TTL, ключ включает `until` миллисекундами): защищает от спама на одну и ту же пару `(symbol, interval)` со множества ботов на одном symbol.
5. Возврат: `Map<CandleInterval, MarketCandle[]>`. Для пустого результата интервала — пустой массив (downstream сам решит, fail-fast или skip).
6. Лог-точка: `logger.debug({ symbol, intervals, totalCandles })` на каждый load — чтобы можно было увидеть в проде, что boтов реально использует MTF.

**Тест-план:**
- `runtime` + bundle `{M5: true, H1: true}` + symbol с свечами обоих интервалов → возвращает Map с двумя ключами, длины ≤ lookbackBars.
- `backtest` + bundle `{M5: "ds_a", H1: "ds_b"}` → возвращает свечи именно из этих datasets, отсортированные ASC, верхняя граница `until` соблюдена.
- `backtest` с bundle, где значение `true` → 400/throw.
- Cache: два последовательных runtime-вызова с одинаковыми args в пределах 30s → вторая БД-операция не выполняется (mock prisma → assert call count).
- Empty interval (нет свечей) → пустой массив, не throw.

**Критерии готовности:**
- Тесты зелёные.
- Параллельные запросы реально параллельны (мок `findMany` с задержкой → суммарное время ≈ max, не sum).
- Cache key корректно учитывает `until` для backtest.

---

### 52-T3: Runtime — `botWorker` загружает bundle и прокидывает в `dslEvaluator`

**Цель:** `botWorker.ts` загружает `CandleBundle` (если `bot.datasetBundleJson != null`) и передаёт его в evaluator. Иначе — старое поведение.

**Файлы для изменения:**
- `apps/api/src/botWorker.ts` — заменить candle-load в районе строки 1467.
- `apps/api/src/lib/signalEngine.ts`, `exitEngine.ts` — расширить вход `bundle?` если ещё не расширены.
- `apps/api/src/lib/dslEvaluator.ts:749` — уже принимает bundle (см. Контекст), правок не требует.
- `apps/api/tests/botWorker/multiTfBundle.test.ts` (создать) — integration.

**Шаги реализации:**
1. В `botWorker.ts` заменить:
   ```ts
   const candles = await prisma.marketCandle.findMany({ where: { symbol } });
   ```
   на:
   ```ts
   const bundle = bot.datasetBundleJson
     ? await loadCandleBundle({
         symbol: bot.symbol,
         bundle: DatasetBundleSchema.parse(bot.datasetBundleJson),
         lookbackBars: 500, // existing constant or config
         mode: "runtime",
       })
     : null;

   const primaryCandles = bundle
     ? bundle.get(bot.timeframe) ?? []
     : await prisma.marketCandle.findMany({ where: { symbol, interval: bot.timeframe }, orderBy: { openTime: "desc" }, take: 500 }).then(rows => rows.reverse());
   ```
   Заметка: ставим `interval: bot.timeframe` даже в legacy-ветке — это **bugfix** существующего поведения (текущий код не фильтрует по interval вообще, что уже неправильно). Bugfix локализован: behaviour single-TF ботов становится строже-корректным; в редких случаях, когда у symbol было несколько интервалов в `MarketCandle` и стратегия молча работала на смешанных данных, это начинает падать или возвращать пусто. Отметить отдельным риском в PR-описании, дать миграционную инструкцию (запустить datasource sync для нужного TF).
2. Передача в evaluator: `signalEngine.evaluate({ candles: primaryCandles, bundle, dsl, ...rest })`. `bundle` — необязательный аргумент; если evaluator его не получает (старый вызов), DSL-узлы с `sourceTimeframe ≠ bot.timeframe` должны фейлить с явной ошибкой "indicator requires multi-TF bundle" (это уже должно быть в evaluator; если нет — добавить охранник).
3. Аналогично — `exitEngine.evaluate(...)` и `positionManager` (если он трогает индикаторы).
4. Polling cadence: bundle перезагружается каждый tick (current cadence); cache из 52-T2 предотвращает БД-нагрузку при множественных ботов.
5. Если `loadCandleBundle` throws (например, нет свечей для одного из TF) — bot run помечается `ERRORED` через существующий `errorClassifier` flow; не падает безмолвно.

**Тест-план:**
- Bot без `datasetBundleJson` → legacy-ветка, поведение идентично текущему (после фикса interval-фильтра).
- Bot с bundle `{M5: true, H1: true}`, `timeframe=M5` → evaluator получает bundle, MTF-индикаторы резолвятся корректно.
- Bot с bundle, в котором нет `bot.timeframe` → ошибка валидации на старте (не запускается).
- Bot с bundle, в котором отсутствуют свечи для H1 (например, H1-датасорс отключён) → bot run → ERRORED, понятный message.

**Критерии готовности:**
- `botWorker.ts` тесты зелёные.
- Multi-TF integration test зелёный.
- Legacy single-TF боты работают без изменений (одна оговорка про interval-фильтр выше).
- В логах появляются bundle-метаданные (можно отключить с `LOG_LEVEL=info`).

---

### 52-T4: Backtest — `runBacktest` принимает bundle

**Цель:** `runBacktest` поддерживает bundle-режим. Sweep / walk-forward / lab-test endpoints прокидывают bundle сквозь.

**Файлы для изменения:**
- `apps/api/src/lib/backtest/runBacktest.ts` — overload + новая ветка.
- `apps/api/src/routes/lab.ts` — `POST /lab/backtest`, `POST /lab/backtest/sweep`, `POST /lab/walk-forward` принимают `datasetBundleJson` опционально.
- `apps/api/tests/lib/backtest/multiTf.test.ts`.

**Шаги реализации:**
1. Сигнатура `runBacktest`:
   ```ts
   // legacy:
   runBacktest(candles: MarketCandle[], dsl, opts): Promise<DslBacktestReport>
   // new:
   runBacktest({ bundle, primaryInterval, dsl, opts }: {
     bundle: CandleBundle;
     primaryInterval: CandleInterval;
     dsl: DslJson;
     opts: DslExecOpts;
   }): Promise<DslBacktestReport>
   ```
   Различение через discriminated tuple (массив-аргумент = legacy; объект = new). Внутри новой ветки итерация — по `bundle.get(primaryInterval)`; для каждой primary-свечи в evaluator передаётся snapshot bundle, обрезанный по `openTime <= primary.openTime`. Реализация обрезки — через существующий `intervalAlignment.ts` helper (важно: HTF свеча может быть «незакрыта» относительно primary; правило закрытия HTF на момент primary-bar — `htf.openTime + htfDuration <= primary.openTime`; иначе берётся last closed HTF candle).
2. **Look-ahead bias guard.** Каждый шаг evaluator должен видеть только закрытые HTF candles. Это критическая корректность для backtest и walk-forward; добавить unit-тест с фикстурой, где «открытая» HTF candle сознательно содержит «будущие» данные — evaluator не должен их видеть.
3. `routes/lab.ts`:
   - `POST /lab/backtest`: если body содержит `datasetBundleJson`, валидировать через `DatasetBundleSchema`, проверить `validateBundleAgainstPrimary(bundle, primaryInterval)`, загрузить через `loadCandleBundle(mode="backtest")` и вызвать новый overload. Если нет — старая ветка.
   - `POST /lab/backtest/sweep` (`apps/api/src/routes/lab.ts:838`): сохранить `datasetBundleJson` в `BacktestSweep`. В `runSweepAsync` для каждой комбинации параметров — если bundle задан, `loadCandleBundle` один раз перед циклом (как сейчас делается для single dataset, см. `docs/47 §47-T3 шаг 1`), затем `runBacktest({ bundle, ... })`. Это ровно тот же паттерн, что у текущего кода — bundle-load заменяет single dataset-load.
   - `POST /lab/walk-forward`: аналогично, `datasetBundleJson` передаётся в `WalkForwardRun.create`, fold-runner подгружает bundle с обрезанным `until` per-fold.
4. Backward compat: ни один существующий клиент не ломается — `datasetBundleJson` опционален во всех body.

**Тест-план:**
- Single-TF backtest: legacy-вызов работает без правок.
- Multi-TF backtest на готовой fixture (например, M5+H1 для AdaptiveRegime sample) → результат детерминирован, метрики совпадают с golden run.
- Look-ahead guard: фикстура с «загрязнённой» HTF candle → evaluator не видит её, метрики совпадают с теми, что без загрязнения.
- Sweep с bundle → все runs используют тот же bundle, результаты различны только по параметрам.
- Walk-forward с bundle: каждый fold honors `until` boundary.

**Критерии готовности:**
- Multi-TF tests зелёные.
- Существующие single-TF тесты `lab.test.ts` зелёные.
- В `BacktestSweep` / `WalkForwardRun` записях `datasetBundleJson` корректно сохраняется и читается обратно.

---

### 52-T5: Lab UI — мульти-датасет селектор для Test / Optimise / Walk-Forward

**Цель:** на страницах Lab Test / Optimise / Walk-Forward добавить опциональный multi-interval селектор поверх существующего single-dataset селекта.

**Файлы для изменения:**
- `apps/web/src/app/lab/test/TestPanel.tsx` (или эквивалент).
- `apps/web/src/app/lab/test/OptimisePanel.tsx`.
- `apps/web/src/app/lab/walk-forward/WalkForwardPanel.tsx` (см. `docs/48-T6`).
- `apps/web/src/app/lab/_shared/DatasetBundleSelector.tsx` (создать) — переиспользуемый компонент.

**Шаги реализации:**
1. `DatasetBundleSelector`:
   - Props: `primaryDatasetId: string`, `bundle: DatasetBundle | null`, `onChange(bundle: DatasetBundle | null): void`, `availableDatasets: { id, symbol, interval }[]`.
   - Стандартное состояние: `bundle === null` (legacy single-TF).
   - При клике "+ Add timeframe" появляется строка с двумя селектами: interval и dataset (отфильтрованный по `symbol === primaryDataset.symbol && interval === selected`).
   - Максимум 3 строк дополнительных TF (4 total включая primary).
   - При первом добавлении автоматически создаётся bundle: `{ [primary.interval]: primary.id, [newInterval]: newDatasetId }`.
2. В `TestPanel` подключить selector рядом с существующим dataset-select. Кнопка "Run backtest" отправляет `datasetBundleJson` в body, если bundle != null; иначе — старый `datasetId`.
3. В `OptimisePanel` — то же. Sweep с bundle сохраняется в `BacktestSweep.datasetBundleJson`, переотображается на load.
4. В `WalkForwardPanel` — то же.
5. UX-требования:
   - Если у пользователя нет datasets для нужного `(symbol, interval)` — селектор интервалов помечает их disabled с подсказкой "No dataset available for this TF. Sync M5/H1/etc data first."
   - Все `availableDatasets` грузятся через существующий API, без новых endpoints.
6. Никаких изменений в Library page (51-T5) — там `datasetBundleHintJson` пресета используется чисто как информационная подсказка для пользователя, фактический bundle для бота настраивается на странице бота.

**Тест-план:**
- Ручной smoke: запустить backtest на single TF — поведение прежнее.
- Добавить второй TF, dataset для него существует — backtest стартует, в logs API видно `loadCandleBundle` с двумя ключами.
- Добавить второй TF, dataset не существует → кнопка disabled.
- Walk-forward с bundle → folds корректно используют bundle (см. 52-T4 тесты).

**Критерии готовности:**
- TS-проверка фронта зелёная.
- Существующие e2e (если есть) зелёные.
- Smoke в браузере подтверждён в PR-описании.

---

### 52-T6: Тесты — unit + e2e на multi-TF strategy

**Цель:** объединённое покрытие — unit для loader, evaluator с bundle, look-ahead guard; интеграционный e2e «реальная стратегия с MTF DSL → backtest → ожидаемые метрики».

**Файлы для изменения:**
- `apps/api/tests/lib/mtf/loadCandleBundle.test.ts` (создан в T2).
- `apps/api/tests/lib/backtest/multiTf.test.ts` (создан в T4).
- `apps/api/tests/integration/multiTfBacktestFlow.test.ts` (создать) — e2e через `POST /lab/backtest`.
- `apps/api/tests/lib/dslEvaluator/bundleSourceTimeframe.test.ts` (создать или дополнить).

**Шаги реализации:**
1. **Look-ahead guard fixture.** Сгенерировать M5 свечи на 1 день (288 candles) и H1 (24). Для каждой пары (M5_i, H1_j) проверить: `evaluateExpression(...)` на M5_i видит только те H1_j, у которых `closeTime <= M5_i.openTime`. Тест-кейс — индикатор `RSI(14) on H1`: его значение в момент M5_42 должно совпадать с тем, что было бы посчитано на «обрезанном» H1-наборе.
2. **MTF strategy e2e.** Минимальный DSL с двумя блоками:
   ```json
   {
     "enter_when": {
       "and_gate": [
         { "compare": { "left": { "indicator": "rsi", "sourceTimeframe": "M5" }, "op": "<", "right": 30 } },
         { "compare": { "left": { "indicator": "ema", "params": {"period": 200}, "sourceTimeframe": "H1" }, "op": "<", "right": { "candle": "close" } } }
       ]
     },
     "exit_when": { "compare": { "left": { "indicator": "rsi", "sourceTimeframe": "M5" }, "op": ">", "right": 70 } }
   }
   ```
   Backtest на фикстуре с известным числом сигналов → проверить `report.tradeCount` и сравнить с golden value.
3. **Backward-compat suite.** Тот же DSL без `sourceTimeframe` (всё на primary TF) → backtest работает без bundle, метрики совпадают с pre-52 backtest того же DSL на тех же candles.
4. Все фикстуры — статические JSON, в репо. Никаких HTTP-вызовов / времени выполнения.

**Тест-план:**
- `npm test` (apps/api) проходит локально и в CI.
- Существующие тесты (`lab.test.ts`, `botWorker/*.test.ts`, `dslEvaluator/*.test.ts`) — зелёные.
- Покрытие новых файлов ≥ 80%.

**Критерии готовности:**
- Все новые тесты зелёные.
- Look-ahead guard — отдельный явный тест-кейс с комментарием, ссылающимся на этот документ.
- E2E `multiTfBacktestFlow.test.ts` — golden numbers зашиты, регрессия сразу красит.

---

## Порядок выполнения задач

```
52-T1 ──→ 52-T2 ──┬──→ 52-T3 ──┐
                  ├──→ 52-T4 ──┤
                  │             ├──→ 52-T6
                  └──→ 52-T5 ──┘
```

- 52-T1 (схема + типы) — первая.
- 52-T2 (loader) — после T1, потому что loader использует `DatasetBundleSchema`.
- 52-T3 (runtime) и 52-T4 (backtest) — независимы между собой, но оба требуют T2.
- 52-T5 (UI) — может стартовать параллельно с T3/T4, но интеграция с реальным backendom требует T4.
- 52-T6 (тесты) — встраивается инкрементально + финальный e2e в конце.

Каждая T-задача — отдельный PR. T3 и T4 поджимаются по приоритету: T4 нужнее для acceptance gate в `docs/53`/`docs/54` (walk-forward на multi-TF), поэтому идёт раньше T3 если дефицит времени.

## Зависимости от других документов

- `docs/50` — родительский. Особенно `§Решение 2`: bundle = JSON, не таблица.
- `docs/51-strategy-preset-system.md` — независим. `StrategyPreset.datasetBundleHintJson` — просто метаданные пресета; сам preset-flow не требует 52.
- `docs/53-adaptive-regime-bot-activation.md` — потребитель. Adaptive Regime использует bundle `{M5: ..., H1: ...}`.
- `docs/54-flagship-rollout.md` — потребитель. MTF Scalper использует `{M1, M5, M15}`, SMC — `{M15, H1, H4}`. DCA — single-TF, не требует 52.
- `docs/47-strategy-optimizer-plan.md` — закрыт. Sweep с bundle = небольшое расширение `runSweepAsync` (см. 52-T4 §3).
- `docs/48-walk-forward-plan.md` — закрыт. Fold-runner с bundle = аналогично, расширение `WalkForwardRun` без правки логики split.
- `docs/strategies/05-mtf-scalper.md`, `docs/strategies/03-adaptive-regime-bot.md` — concept-доки потребителей.

## Backward compatibility checklist

- Все Prisma миграции — additive nullable Json колонки. Existing rows получают `NULL`.
- `Bot.datasetBundleJson === null` → legacy single-TF поведение. Все существующие боты живут без правок.
- `BacktestSweep.datasetBundleJson === null` → старый sweep на одном dataset.
- `WalkForwardRun.datasetBundleJson === null` → старый walk-forward.
- `runBacktest(candles, dsl, opts)` — legacy сигнатура остаётся работать. Новая overload вызывается явно объектным аргументом.
- `dslEvaluator` — bundle всегда был optional, никаких ломающих правок.
- Lab UI без раскрытия "+ Add timeframe" работает идентично текущему — тот же single-dataset-select, тот же flow.
- Замена `findMany({ where: { symbol } })` → `findMany({ where: { symbol, interval } })` в `botWorker.ts` — это **bugfix**, может изменить поведение в редких случаях; помечено отдельным риском в PR-описании 52-T3.
- `MarketCandle`, `MarketDataset`, `BotIntent`, `BotRunState` — без изменений.

## Ожидаемый результат

После закрытия 52-T1..52-T6:

- DSL-стратегии могут декларировать `sourceTimeframe` на любом блоке, и это работает в runtime, в `runBacktest`, в sweep, в walk-forward.
- Bot/BacktestSweep/WalkForwardRun хранят bundle в одном Json-поле; миграций не больше, чем нужно.
- Look-ahead bias guard явно протестирован — multi-TF backtest корректен даже на стрессовых фикстурах.
- Lab UI позволяет добавить до 3 дополнительных интервалов к выбранному dataset одной кнопкой.
- Adaptive Regime, MTF Scalper, SMC Liquidity Sweep получают рабочий слой данных, на котором их acceptance gates имеет смысл (без bundle их нельзя честно протестировать).
- Single-TF DCA Momentum (`docs/54`) — никак не затронут; bundle не вводится в его flow.
