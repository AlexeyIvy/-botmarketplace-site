# 49. Backtest Metrics Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-27  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (research workflow)

## Контекст

Текущее состояние (проверено по коду):

- `DslBacktestReport` сейчас содержит **только базовые** метрики: `trades`, `wins`, `winrate`, `totalPnlPct`, `maxDrawdownPct`, `candles`, `tradeLog` (`apps/api/src/lib/dslEvaluator.ts:68–76`). Нет `sharpe`, `profitFactor`, `expectancy`.
- Sharpe считается **локально** в роутере sweep-а: `function computeSharpe(pnlPcts: number[]): number | null` (`apps/api/src/routes/lab.ts:1420–1427`). Реализация: mean/stdDev по trade-pnl, аннуализация `Math.sqrt(252)`. Используется единственный раз — в `runSweepAsync` (`apps/api/src/routes/lab.ts:1358`).
- `SweepRow.sharpe: number | null` (`apps/api/src/routes/lab.ts:1251`) пишется из локального `computeSharpe`, не из `report`.
- Compare-эндпоинт `/lab/compare` уже читает `reportA.sharpe` / `reportB.sharpe` из `reportJson` (`apps/api/src/routes/lab.ts:661`), но в текущем `DslBacktestReport` поля `sharpe` **нет** — соответственно `reportJson.sharpe` всегда `undefined`, и `sharpeDelta` всегда `null`. Это скрытая мёртвая ветка.
- `apps/api/src/lib/metrics.ts` — Prometheus-only (`Registry`, `collectDefaultMetrics`, `Counter`, `Histogram`); экспортирует runtime-counters, импортируется в 8 местах (`app.ts`, `botWorker.ts`, `periodicReconciler.ts`, `worker/intentExecutor.ts`, `routes/intents.ts`, `routes/metrics.ts`, тесты). К backtest-метрикам отношения не имеет — переименовывать его в этом этапе **не будем** (см. "Решение по неймингу").
- `maxDrawdownPct` уже корректно вычисляется в `runDslBacktest` через `cumulativePnl/peakPnl/maxDrawdownPct` (`apps/api/src/lib/dslEvaluator.ts:917–919` и далее по коду) — оставляется без правок.
- `DslTradeRecord.pnlPct` (`apps/api/src/lib/dslEvaluator.ts:50–66`) — единственный источник для всех trade-level метрик.
- Тесты: ядро покрыто `apps/api/tests/lib/dslEvaluator.test.ts`, sweep — `apps/api/tests/routes/lab.test.ts:442–515`. Тестов на sharpe/profitFactor/expectancy в текущей кодобазе **нет**.

## Цель

- Вынести вычисление backtest-метрик из роутера в pure-модуль рядом с `dslEvaluator`.
- Расширить `DslBacktestReport` дополнительными полями `sharpe`, `profitFactor`, `expectancy` (additive, optional на уровне типа для backward compat — но всегда заполняется ядром).
- Удалить локальный `computeSharpe` из `lab.ts`; sweep и compare читают значения напрямую из отчёта.
- Зафиксировать политику относительно `reportVersion` — здесь принимается решение, не в `docs/44` (там правило про "вводить, если нельзя дополнить additive" обозначено, но триггер не определён).
- Подготовить наполнение для `rankBy` в `docs/47-T4`: `sharpe`, `profitFactor`, `expectancy` должны существовать на уровне отчёта.

## Решение по неймингу модуля

Существующий `apps/api/src/lib/metrics.ts` (Prometheus, 8 importer-ов) **не переименовывается** — это отдельный домен (HTTP/runtime observability), переименование вне scope этого документа и потребовало бы trivial-massnetuptan правок во всех importer-ах ради семантики.

Новый модуль: **`apps/api/src/lib/backtestMetrics/`** (директория). Имя устраняет коллизию с `metrics.ts` и однозначно описывает домен (статистики по результатам backtest-а). Альтернативы (`stats/`, `perfMetrics/`, `reportMetrics/`) рассмотрены и отклонены: они менее самодокументируемы.

Структура:

```
apps/api/src/lib/backtestMetrics/
  index.ts          // re-exports
  sharpe.ts         // sharpeRatio(returns, periodsPerYear)
  profitFactor.ts   // profitFactor(returns)
  expectancy.ts     // expectancy(returns)
  types.ts          // shared MetricInput type if needed
```

## Решение по `reportVersion`

`reportVersion` **не вводится в этом этапе**. Триггер для введения:

> Поле или семантика существующего поля `DslBacktestReport` или `DslTradeRecord` меняется несовместимо (переименование, изменение типа, изменение единиц измерения, изменение знака). Additive (новые опциональные поля) — НЕ триггер.

Текущие изменения 49-T2 — additive (новые поля `sharpe`, `profitFactor`, `expectancy`). Поэтому `reportVersion` не нужен. Когда триггер сработает (первое несовместимое изменение) — вводится поле `reportVersion: 1` в `DslBacktestReport`, существующие записи без поля интерпретируются как `reportVersion: 0`. Это решение фиксируется в `docs/44 §Backward compatibility` отдельной правкой шапки документа в рамках 49-T2.

## Не входит в задачу

- Sortino, Calmar, Omega, MAR ratio, Tail ratio. Sortino и Calmar — наиболее ценные follow-up (после стабилизации sharpe/PF/expectancy); добавляются отдельным PR.
- Per-side метрики (long-only / short-only sharpe, etc.).
- Equity curve / drawdown timeseries в отчёте (сейчас только `maxDrawdownPct` скаляр; timeseries требует значительного увеличения размера `reportJson` и хранения — отдельный план).
- Confidence intervals, bootstrap, statistical significance — out of scope.
- Реализация UI-визуализации новых метрик за пределами уже существующих snapshot/compare таблиц.
- Изменения формы `DslTradeRecord` — все метрики строятся над уже существующим `pnlPct`.
- Переименование `apps/api/src/lib/metrics.ts` или его importer-ов.
- Изменения Prometheus-метрик. Этот документ **не** про observability.

---

## Задачи

### 49-T1: Создать модуль `backtestMetrics/` с pure-функциями

**Цель:** вынести вычисление статистик в изолированный модуль с unit-покрытием. Без зависимостей от БД, Express, dslEvaluator.

**Файлы для изменения:**
- Создать `apps/api/src/lib/backtestMetrics/sharpe.ts`.
- Создать `apps/api/src/lib/backtestMetrics/profitFactor.ts`.
- Создать `apps/api/src/lib/backtestMetrics/expectancy.ts`.
- Создать `apps/api/src/lib/backtestMetrics/index.ts`.
- Создать `apps/api/tests/lib/backtestMetrics/sharpe.test.ts`.
- Создать `apps/api/tests/lib/backtestMetrics/profitFactor.test.ts`.
- Создать `apps/api/tests/lib/backtestMetrics/expectancy.test.ts`.

**Шаги реализации:**
1. `sharpe.ts`:
   ```ts
   /**
    * Annualized Sharpe ratio over per-trade pnl percentages.
    * Mirrors the existing computeSharpe implementation in lab.ts:1420 bit-for-bit
    * to preserve numerical compatibility with prior sweep results.
    */
   export function sharpeRatio(pnlPcts: number[], periodsPerYear = 252): number | null {
     if (pnlPcts.length < 2) return null;
     const mean = pnlPcts.reduce((s, v) => s + v, 0) / pnlPcts.length;
     const variance = pnlPcts.reduce((s, v) => s + (v - mean) ** 2, 0) / (pnlPcts.length - 1);
     const stdDev = Math.sqrt(variance);
     if (stdDev === 0) return null;
     return Math.round((mean / stdDev) * Math.sqrt(periodsPerYear) * 100) / 100;
   }
   ```
   Параметр `periodsPerYear` — default 252 (соответствует существующему хардкоду). Документировать ограничение: "treats per-trade returns as if they were daily; a more accurate annualization requires per-bar returns and is left as future work".
2. `profitFactor.ts`:
   ```ts
   /**
    * Profit factor = sum(positive pnl%) / |sum(negative pnl%)|.
    * Conventions:
    *   - Empty array → null.
    *   - All wins, no losses → +Infinity (consumers must handle this explicitly,
    *     e.g. ranking treats Infinity as "best").
    *   - All losses → 0.
    */
   export function profitFactor(pnlPcts: number[]): number | null {
     if (pnlPcts.length === 0) return null;
     let gross = 0;
     let loss = 0;
     for (const v of pnlPcts) { if (v > 0) gross += v; else if (v < 0) loss += -v; }
     if (loss === 0 && gross === 0) return null;
     if (loss === 0) return Number.POSITIVE_INFINITY;
     return Math.round((gross / loss) * 100) / 100;
   }
   ```
3. `expectancy.ts`:
   ```ts
   /**
    * Per-trade expectancy in percent units:
    *   E = winRate * avgWin - lossRate * avgLoss
    * where avgWin = mean(positive pnl%), avgLoss = mean(|negative pnl%|).
    * Empty array → null. Single trade → returns its own pnl% (degenerate case).
    */
   export function expectancy(pnlPcts: number[]): number | null {
     if (pnlPcts.length === 0) return null;
     const wins = pnlPcts.filter(v => v > 0);
     const losses = pnlPcts.filter(v => v < 0).map(v => -v);
     const winRate = wins.length / pnlPcts.length;
     const lossRate = losses.length / pnlPcts.length;
     const avgWin = wins.length ? wins.reduce((s, v) => s + v, 0) / wins.length : 0;
     const avgLoss = losses.length ? losses.reduce((s, v) => s + v, 0) / losses.length : 0;
     return Math.round((winRate * avgWin - lossRate * avgLoss) * 100) / 100;
   }
   ```
4. `index.ts`:
   ```ts
   export { sharpeRatio } from "./sharpe.js";
   export { profitFactor } from "./profitFactor.js";
   export { expectancy } from "./expectancy.js";
   ```
5. Никаких side-effects, никаких импортов из `dslEvaluator`, БД, Express.

**Тест-план:**
- `sharpe`: пустой, 1-элемент → null. Constant series → null (stdDev=0). Известная синтетика (mean=1, stdDev=1, n=10, periodsPerYear=252) → assert на ожидаемое число. Negative mean → отрицательный sharpe.
- `sharpe`: bit-for-bit совпадение со старой `computeSharpe` из `lab.ts:1420` на 5 фикстурах разной формы (см. 49-T3 — там сверка обязательна).
- `profitFactor`: пустой → null. Все wins → `+Infinity`. Все losses → 0. Mixed: 2 wins по +5% и 1 loss -5% → 2.0.
- `expectancy`: пустой → null. 50/50 win/loss с одинаковыми абс. величинами → 0. Asymmetric: 60% wins по +2, 40% losses по -1 → 1.2 - 0.4 = 0.80.
- Numerical edge cases: `NaN`/`Infinity` на входе — поведение не специфицируется (assume callers пропускают их). Документировать в JSDoc.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все unit-тесты зелёные.
- Никаких импортов из `dslEvaluator`, БД, Express.
- `sharpeRatio` бит-в-бит соответствует существующей `computeSharpe` (golden test).

---

### 49-T2: Расширить `DslBacktestReport` метриками; заполнять в `runDslBacktest`

**Цель:** добавить optional поля `sharpe`, `profitFactor`, `expectancy` в отчёт, заполнять их через утилиты из 49-T1. Изменение строго additive.

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts` — `DslBacktestReport` (`строка 68`), финальный `return` (`строка 1198`).
- `apps/api/tests/lib/dslEvaluator.test.ts` — расширить тест-кейсы.
- `docs/44-strategy-engine-overview.md` — внести правило о триггере `reportVersion` в `§Backward compatibility` (см. "Решение по `reportVersion`" в этом документе).

**Шаги реализации:**
1. Расширить тип:
   ```ts
   export interface DslBacktestReport {
     trades: number;
     wins: number;
     winrate: number;
     totalPnlPct: number;
     maxDrawdownPct: number;
     candles: number;
     tradeLog: DslTradeRecord[];
     // additive (49-T2)
     sharpe: number | null;
     profitFactor: number | null;
     expectancy: number | null;
   }
   ```
   Поля required (не optional) — это упрощает использование на стороне consumer-ов (`rankBy` в 47-T4, aggregate в 48-T3, sweep в 49-T3). `null` явно используется для "нельзя вычислить" (мало сделок, stdDev=0, и т.п.).
2. **Backward compat**: чтобы не сломать существующих consumer-ов, которые могут читать `reportJson` старых записей (где новых полей нет), TypeScript-тип внешнего API (`BacktestReport` re-export в `backtest.ts:22`) сохраняется тот же, но при чтении из `reportJson` нужно обрабатывать `undefined` → `null`. Это уже частично сделано в compare-эндпоинте (`apps/api/src/routes/lab.ts:650` через хелпер `num`).
3. В `runDslBacktest` после построения `tradeLog` и до `return`:
   ```ts
   const pnlPcts = tradeLog.map(t => t.pnlPct);
   const sharpe = sharpeRatio(pnlPcts);
   const pf = profitFactor(pnlPcts);
   const exp = expectancy(pnlPcts);
   ```
   Импортировать из `./backtestMetrics/index.js`.
4. Возвращаемый объект:
   ```ts
   return {
     trades, wins,
     winrate: Math.round(winrate * 10000) / 10000,
     totalPnlPct: Math.round(totalPnlPct * 100) / 100,
     maxDrawdownPct: Math.round(maxDrawdownPct * 100) / 100,
     candles: candles.length,
     tradeLog,
     sharpe,
     profitFactor: pf,
     expectancy: exp,
   };
   ```
5. `emptyReport` (`строка 853`) тоже обновить:
   ```ts
   const emptyReport: DslBacktestReport = {
     trades: 0, wins: 0, winrate: 0, totalPnlPct: 0, maxDrawdownPct: 0,
     candles: candles.length, tradeLog: [],
     sharpe: null, profitFactor: null, expectancy: null,
   };
   ```
6. Обновить `docs/44 §Backward compatibility`: добавить пункт "reportVersion введётся при первом несовместимом изменении формы DslBacktestReport / DslTradeRecord (rename, type change, unit change). Additive optional/required-with-null поля — НЕ триггер." Это явное закрепление правила, цитируется из `docs/49`.

**Тест-план:**
- Существующие тесты `dslEvaluator.test.ts` зелёные с минимальной правкой (добавить новые поля в expected fixtures, или использовать `expect.objectContaining` для частичного match-а).
- Новый кейс: backtest с известным winrate/avg-pnl → `sharpe`, `profitFactor`, `expectancy` совпадают с тем, что вернёт прямой вызов утилит на тех же `pnlPct`.
- Empty backtest (нет сделок) → `sharpe = null`, `profitFactor = null`, `expectancy = null`.
- 1 сделка → `sharpe = null` (нужно ≥ 2 для stdDev), `profitFactor` и `expectancy` определены.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- Новые поля присутствуют в каждом возвращённом отчёте.
- `docs/44` обновлён правилом `reportVersion`.

---

### 49-T3: Удалить локальный `computeSharpe`; sweep и compare читают `report.sharpe`

**Цель:** убрать дублирование. После 49-T2 `report.sharpe` доступен из ядра — локальный `computeSharpe` больше не нужен. Заодно проверяем, что compare-эндпоинт корректно читает новые поля.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — удалить функцию (`строки 1420–1427`), заменить вызов в sweep (`строка 1358`), обновить delta в compare (`строки 661–663`).
- `apps/api/tests/routes/lab.test.ts` — расширить sweep тесты для проверки `SweepRow.sharpe`.

**Шаги реализации:**
1. В `runSweepAsync` (`строка 1358`): заменить
   ```ts
   const sharpe = computeSharpe(report.tradeLog.map((t) => t.pnlPct));
   ```
   на
   ```ts
   const sharpe = report.sharpe;
   ```
   Поведение идентично — `report.sharpe` после 49-T2 заполняется через `sharpeRatio(...)`, которая бит-в-бит копия `computeSharpe` (см. 49-T1 шаг 1 docstring).
2. Удалить функцию `computeSharpe` (`строки 1420–1427`) полностью. Никаких `_computeSharpe`-комментариев и backwards-compat шимов — функция нигде кроме `runSweepAsync` не используется (проверено: `grep -rn "computeSharpe" apps/api`).
3. В compare-эндпоинте (`строки 647–663`): добавить `profitFactorDelta` и `expectancyDelta`:
   ```ts
   profitFactorDelta: num(reportA.profitFactor) !== null && num(reportB.profitFactor) !== null
     ? (num(reportA.profitFactor)! - num(reportB.profitFactor)!) : null,
   expectancyDelta: num(reportA.expectancy) !== null && num(reportB.expectancy) !== null
     ? (num(reportA.expectancy)! - num(reportB.expectancy)!) : null,
   ```
   `sharpeDelta` остаётся как есть — после 49-T2 `reportA.sharpe` будет ненулевым для новых записей.
4. **Старые `BacktestResult` без новых полей**: `num()` хелпер возвращает `null` для `undefined` — это уже корректное поведение, дельта = `null`. Никаких миграций reportJson-блоков делать **не надо**.
5. Расширить `SweepRow` и схему ответа sweep — `profitFactor: number | null`, `expectancy: number | null` — additive поля. Для backward compat с UI: новые поля optional на TS-уровне; UI показывает их при наличии. Это подготавливает почву для `rankBy ∈ {profitFactor, expectancy}` в `docs/47-T4`.

**Тест-план:**
- Sweep e2e: новый запрос → `SweepRow.sharpe` совпадает с тем, что вернул бы прежний `computeSharpe` на тех же trade-pnl-ах. Использовать golden-тест с известной фикстурой свечей.
- Sweep e2e: `SweepRow.profitFactor` и `SweepRow.expectancy` присутствуют в ответе.
- Compare endpoint: два BacktestResult-а после 49-T2 → `sharpeDelta`, `profitFactorDelta`, `expectancyDelta` ненулевые при разных reportJson-ах.
- Compare endpoint: один из BacktestResult-ов pre-49 (старый reportJson без `sharpe`) → дельты возвращают `null` без ошибок.
- `grep "computeSharpe" apps/api` — пусто (функция удалена).

**Критерии готовности:**
- `tsc --noEmit` проходит.
- `computeSharpe` удалён.
- Существующие sweep тесты зелёные (с обновлёнными expected-полями).
- Compare-эндпоинт работает на смеси старых и новых BacktestResult-ов.

---

### 49-T4: Тесты и golden values

**Цель:** зафиксировать численные контракты utilities + report-shape + интеграцию с sweep/compare.

**Файлы для изменения:**
- `apps/api/tests/lib/backtestMetrics/*.test.ts` (созданы в 49-T1) — расширить если нужно.
- `apps/api/tests/lib/dslEvaluator.test.ts` — golden report shape.
- `apps/api/tests/routes/lab.test.ts` — sweep golden + compare smoke.

**Шаги реализации:**
1. Добавить файл `apps/api/tests/lib/backtestMetrics/_fixtures.ts` с 5 эталонными массивами `pnlPcts`:
   - `EMPTY: []`
   - `SINGLE_WIN: [3.5]`
   - `MIXED_BALANCED: [2, -1, 3, -2, 1]`
   - `ALL_WINS: [1.5, 2.0, 0.5]`
   - `ALL_LOSSES: [-1, -2, -0.5]`
   Для каждой — заранее посчитанные expected `sharpe`, `profitFactor`, `expectancy` (можно посчитать в Python/калькуляторе и зашить как комментарий с формулой).
2. Прогнать каждую утилиту по фикстурам, assert на ожидаемые значения.
3. **Bit-for-bit regression vs old `computeSharpe`**: сохранить копию старой функции `computeSharpe` в `apps/api/tests/lib/backtestMetrics/_legacySharpe.ts` как archived reference; тест проверяет, что для каждой фикстуры `sharpeRatio(x) === _legacySharpe(x)`. Файл `_legacySharpe.ts` помечен deprecated, удаляется через 1 minor release или после явного решения core-команды.
4. В `dslEvaluator.test.ts`: golden фикстура с известным `tradeLog` → проверить, что `report.sharpe`, `report.profitFactor`, `report.expectancy` совпадают с прямым вызовом утилит на `tradeLog.map(t => t.pnlPct)`.
5. В `lab.test.ts`:
   - Sweep golden: запуск sweep на синтетической стратегии → `SweepRow[i].sharpe` за 1 row совпадает с прямым `sharpeRatio(...)`.
   - Compare smoke: создать 2 BacktestResult с разными reportJson → `sharpeDelta`, `profitFactorDelta`, `expectancyDelta` корректны.
   - Compare back-compat: один reportJson pre-49 (без новых полей) → дельты null, нет 500.
6. Все тесты детерминированы: фикстуры зашиты, никаких `Date.now()`, никаких PRNG.

**Тест-план:**
- `npm test` (apps/api) полностью зелёный.
- Bit-for-bit regression vs `_legacySharpe.ts` зелёный.
- Compare smoke на смеси записей зелёный.

**Критерии готовности:**
- Все новые тесты зелёные.
- `_legacySharpe.ts` присутствует с пометкой "deprecated, planned for removal".
- Golden-таблица фикстур закоммичена с комментарием "do not edit without justification".

---

## Порядок выполнения задач

```
49-T1 → 49-T2 → 49-T3 → 49-T4
```

Каждая задача — отдельный PR.

- T1 первой: pure utilities, без зависимостей.
- T2 после T1: использует утилиты, расширяет публичный отчёт. Также правит `docs/44` (правило `reportVersion`).
- T3 после T2: миграция consumer-ов на новые поля.
- T4 — последняя задача или встроена инкрементально в T1..T3.

## Зависимости от других документов

- **`docs/47-T4`** (rankBy multi-metric) — становится исполнимым только после 49-T2 (поля `sharpe`, `profitFactor`, `expectancy` появляются в `DslBacktestReport`). Если 47-T4 запускается до 49-T2 — реализуется только `rankBy="pnlPct"`-ветка с 400 для остальных значений (см. 47-T4 шаг 2).
- **`docs/48-T3`** (walk-forward aggregate) — использует `report.sharpe`. До 49-T2 использует временный `_localSharpe.ts` helper (см. 48-T3 шаг 3); после 49-T2 follow-up PR удаляет helper.
- **`docs/44`** — обновляется в 49-T2 (правило `reportVersion`).
- **`docs/46`** — независим. 46 и 49 могут идти параллельно.
- **`docs/45`** — независим.

## Backward compatibility checklist

- `DslBacktestReport`-расширение additive: добавлены `sharpe`, `profitFactor`, `expectancy` (required, могут быть `null`).
- Существующие `BacktestResult.reportJson` записи без новых полей — корректно обрабатываются: `num(reportA.sharpe)` возвращает `null`, дельты в compare возвращают `null`. Никаких миграций reportJson-блоков.
- `computeSharpe` удалён, но его поведение бит-в-бит сохранено в `sharpeRatio` (см. 49-T1 + 49-T4 regression test).
- `engineVersion` уже фиксирует версию engine — старые записи интерпретируются по своему `engineVersion`.
- `SweepRow.sharpe` сохраняет тот же тип `number | null` и те же численные значения, что были до 49-T3 (regression test обязателен).
- `reportVersion` **не вводится** — все правки additive.
- `apps/api/src/lib/metrics.ts` (Prometheus) не затрагивается.
- Frontend snapshot/compare-таблицы продолжают работать на старых записях; новые поля показываются как "—" при `null`.

## Ожидаемый результат

После завершения всех задач:
- Backtest-метрики `sharpe`, `profitFactor`, `expectancy` доступны прямо в `DslBacktestReport`, а не вычисляются локально в роутерах.
- `apps/api/src/lib/backtestMetrics/` — изолированный модуль с pure-функциями и unit-тестами.
- `lab.ts` стал чище: локальный `computeSharpe` удалён, sweep и compare читают значения из единого источника.
- `docs/47-T4` готов к полноценной реализации `rankBy ∈ {sharpe, profitFactor, expectancy}`.
- `docs/48-T3` после follow-up PR удаляет временный `_localSharpe.ts`.
- Правило для будущего `reportVersion` зафиксировано в `docs/44` — будущие изменения формы отчёта имеют чёткий триггер.
