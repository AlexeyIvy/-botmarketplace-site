# 49. Backtest Metrics Expansion Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-23  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (основной путь, шаг 2)

## Контекст

Текущее состояние (проверено по коду):

- `DslBacktestReport` (`dslEvaluator.ts:68`) содержит: `trades`, `wins`, `winrate`, `totalPnlPct`, `maxDrawdownPct`, `candles`, `tradeLog`. Других метрик нет.
- `DslTradeRecord` (`dslEvaluator.ts:50`) предоставляет: `entryTime`, `exitTime`, `side`, `entryPrice`, `exitPrice`, `slPrice`, `tpPrice`, `outcome`, `pnlPct`, `exitReason`, `barsHeld`, `dcaSafetyOrdersFilled?`, `dcaAvgEntry?`. Эти поля достаточны для вычисления Sharpe / Profit Factor / Expectancy без расширения trade-структуры.
- **Sharpe уже частично реализован** в `apps/api/src/routes/lab.ts:1420` (`computeSharpe`), но:
  - живёт в route handler, а не в engine;
  - использует жёстко `Math.sqrt(252)` (предполагает 1 сделку в день — некорректно для intraday);
  - результат пишется только в `SweepRow.sharpe` (`lab.ts:1251`), а **в `reportJson` не попадает**;
  - delta в compare (`lab.ts:661`) читает `reportA.sharpe` / `reportB.sharpe` из `reportJson` — этих полей там нет, всегда возвращает `null`;
  - тестовая фикстура `apps/api/tests/routes/lab.test.ts:550` подменяет `reportJson` объектом с полем `sharpe: 1.24` — расхождение с production-поведением.
- `AdaptiveBacktestReport` (`adaptiveStrategy.ts:79`) дублирует структуру `DslBacktestReport` и тоже не содержит расширенных метрик.
- UI `MetricsTab` (`apps/web/src/app/lab/test/page.tsx:222`) отображает 4 метрики: Total PnL, Win Rate, Max Drawdown, Trades. Sharpe/PF/Expectancy не показаны.
- Поле `engineVersion` (`prisma/schema.prisma:603`, default `"unknown"`) уже есть на `BacktestResult` — частично закрывает задачу версионирования, но `reportJson` не имеет внутреннего `reportVersion`.

## Цель

- Вынести расчёт метрик в отдельный pure-модуль `apps/api/src/lib/metrics/`.
- Добавить в `DslBacktestReport` поля: `sharpe?`, `profitFactor?`, `expectancy?`, `avgWinPct?`, `avgLossPct?`, `payoffRatio?` — все additive, optional.
- Исправить bug: Sharpe должен попадать в `reportJson` и быть единственным источником истины.
- Сделать Sharpe bar-frequency-aware (factor выводится из медианного интервала свечей).
- Зафиксировать контракт `reportVersion` для будущих breaking-изменений (без введения самого поля сейчас).

## Решение по `reportVersion`

В этой задаче **поле `reportVersion` НЕ вводится**. Все новые метрики — optional additive. Документ только фиксирует правила его будущего появления:

1. `reportVersion: number` вводится только при первом несовместимом изменении (переименование/удаление существующего поля или изменение его типа).
2. До введения отсутствие поля интерпретируется как `reportVersion === 1`.
3. После введения — все потребители обязаны проверять версию перед чтением полей.

Это согласуется с правилом из `docs/44 §Backward compatibility`.

## Решение по выбору метрик

Включаются: **Sharpe, Profit Factor, Expectancy, Avg Win %, Avg Loss %, Payoff Ratio**.

Не включаются (вторая волна): Sortino, Calmar, MAR, recovery factor, time-in-market, exposure-adjusted metrics. Обоснование: первая волна покрывает ~80% типовых сравнительных решений с минимальным API-surface.

## Решение по аннуализации Sharpe

Текущий `computeSharpe` использует `sqrt(252)` — некорректно для не-daily стратегий. Новая реализация:

1. Выводит интервал бара из медианной разницы `candles[i+1].openTime - candles[i].openTime`.
2. `tradesPerYear = (365 * 24 * 3600 * 1000) / medianBarMs / avgBarsHeld`, где `avgBarsHeld = mean(tradeLog[].barsHeld)`.
3. Sharpe annualization factor = `sqrt(tradesPerYear)`.
4. Если `tradeLog.length < 2` или `stdDev === 0` — `sharpe = null` (как сейчас).

Альтернатива (отвергнута): принимать interval как параметр `runBacktest` — увеличивает API-surface ради того, что выводится из данных.

## Не входит в задачу

- Sortino, Calmar, MAR, recovery factor (вторая волна).
- Trade-level breakdown по `exitReason` или `side` (требует UI-работы вне scope).
- Изменение формы `DslTradeRecord` — все новые метрики выводимы из существующих полей.
- Удаление/переименование любых текущих полей `DslBacktestReport`.
- Walk-forward-специфичные метрики (out-of-sample Sharpe, IS/OOS ratio) — это `docs/48`.
- Equity curve как массив — это диагностический формат, не метрика; вторая волна.
- Изменение `engineVersion` логики.

---

## Задачи

### 49-T1: Создать pure-модуль `lib/metrics/`

**Цель:** реализовать чистые функции расчёта метрик в одном переиспользуемом месте.

**Файлы для изменения:**
- Создать `apps/api/src/lib/metrics/index.ts`
- Создать `apps/api/src/lib/metrics/sharpe.ts`
- Создать `apps/api/src/lib/metrics/profitFactor.ts`
- Создать `apps/api/src/lib/metrics/expectancy.ts`
- Создать `apps/api/src/lib/metrics/payoff.ts`
- Создать `apps/api/tests/metrics/sharpe.test.ts`
- Создать `apps/api/tests/metrics/profitFactor.test.ts`
- Создать `apps/api/tests/metrics/expectancy.test.ts`
- Создать `apps/api/tests/metrics/payoff.test.ts`

**Шаги реализации:**
1. `sharpe.ts`:
   ```ts
   export function calcSharpe(
     pnlPcts: number[],
     annualizationFactor: number,
   ): number | null
   ```
   - Возвращает `null` если `pnlPcts.length < 2` или `stdDev === 0`.
   - `(mean / stdDev) * annualizationFactor`, округление до 2 знаков.
2. `profitFactor.ts`:
   ```ts
   export function calcProfitFactor(pnlPcts: number[]): number | null
   ```
   - `sum(positive) / abs(sum(negative))`.
   - Если нет losses — возвращает `Infinity` представляется как `null` (для JSON-serializability).
   - Если нет trades — `null`.
3. `expectancy.ts`:
   ```ts
   export function calcExpectancy(tradeLog: { pnlPct: number; outcome: "WIN" | "LOSS" | "NEUTRAL" }[]): number | null
   ```
   - `winrate * avgWin + (1 - winrate) * avgLoss` (avgLoss < 0).
   - Если нет trades — `null`.
4. `payoff.ts`:
   ```ts
   export function calcAvgWinLoss(tradeLog: ...): { avgWinPct: number | null; avgLossPct: number | null; payoffRatio: number | null }
   ```
   - `avgWinPct` = mean PnL по WIN.
   - `avgLossPct` = mean PnL по LOSS (отрицательное число).
   - `payoffRatio = avgWinPct / abs(avgLossPct)`, `null` если нет losses.
5. `index.ts`:
   ```ts
   export { calcSharpe } from "./sharpe.js";
   export { calcProfitFactor } from "./profitFactor.js";
   export { calcExpectancy } from "./expectancy.js";
   export { calcAvgWinLoss } from "./payoff.js";
   export { inferBarIntervalMs, calcAnnualizationFactor } from "./annualization.js";
   ```
6. Создать `annualization.ts` с:
   - `inferBarIntervalMs(candles: Candle[]): number` — медианная разница `openTime`.
   - `calcAnnualizationFactor(barIntervalMs: number, avgBarsHeld: number): number` — `sqrt(yearMs / barIntervalMs / avgBarsHeld)`.

**Тест-план:**
- Известный массив PnL → известный Sharpe (фикстура с calculator-verified значениями).
- Profit Factor: `[10, -5, 5, -3]` → `15 / 8 = 1.875`.
- Expectancy: `[10, -5, 10, -5]` → `0.5 * 10 + 0.5 * (-5) = 2.5`.
- Все три: пустой массив → `null`.
- Sharpe: одинаковые значения (stdDev = 0) → `null`.
- Profit Factor: только wins → `null` (документировано как "no losses").
- `inferBarIntervalMs`: фикстура с равномерным шагом 900_000 ms → `900_000`. С пропуском → медиана корректна.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- 100% покрытие новых функций unit-тестами.
- Каждая функция — pure (без side-effects, без зависимостей от внешнего state).

---

### 49-T2: Интегрировать метрики в `DslBacktestReport`

**Цель:** добавить optional поля в отчёт; вычислять их в `runDslBacktest` через новый модуль.

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts`
- `apps/api/tests/lib/dslEvaluator.test.ts`

**Шаги реализации:**
1. Расширить `DslBacktestReport` (`dslEvaluator.ts:68`) additive-полями:
   ```ts
   export interface DslBacktestReport {
     trades: number;
     wins: number;
     winrate: number;
     totalPnlPct: number;
     maxDrawdownPct: number;
     candles: number;
     tradeLog: DslTradeRecord[];
     // — additive (49-T2)
     sharpe?: number | null;
     profitFactor?: number | null;
     expectancy?: number | null;
     avgWinPct?: number | null;
     avgLossPct?: number | null;
     payoffRatio?: number | null;
   }
   ```
2. В `runDslBacktest` (`dslEvaluator.ts:1192–1207`):
   - После сборки `tradeLog` импортировать `calcSharpe`, `calcProfitFactor`, `calcExpectancy`, `calcAvgWinLoss`, `inferBarIntervalMs`, `calcAnnualizationFactor` из `./metrics/index.js`.
   - Вычислить `barIntervalMs = inferBarIntervalMs(candles)`.
   - `avgBarsHeld = trades > 0 ? sum(barsHeld) / trades : 1`.
   - `annFactor = calcAnnualizationFactor(barIntervalMs, avgBarsHeld)`.
   - Заполнить новые поля.
3. Округление для отчёта: Sharpe — 2 знака, profitFactor — 2 знака, expectancy / avgWin / avgLoss / payoffRatio — 4 знака.
4. Empty-report ветка (`dslEvaluator.ts:853`) тоже устанавливает новые поля в `null`.

**Тест-план:**
- Существующие тесты `dslEvaluator.test.ts` должны пройти без изменений (старые поля не меняются).
- Новый тест: фикстура с известным набором сделок → проверить численные значения всех новых метрик.
- Граничный случай: 0 сделок → все новые поля = `null`.
- Граничный случай: 1 сделка → Sharpe = `null` (stdDev требует ≥2), expectancy и PF могут быть валидны.
- Детерминизм: два прогона с одинаковыми входами дают bit-exact одинаковые метрики.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- Новые поля корректно заполнены в отчёте.
- Форма отчёта остаётся backward-compatible: потребители, читающие только старые поля, не затронуты.

---

### 49-T3: Удалить дублированный `computeSharpe` из `lab.ts`, исправить compare-bug

**Цель:** убрать legacy-реализацию Sharpe и unify источник истины.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts`
- `apps/api/tests/routes/lab.test.ts`

**Шаги реализации:**
1. Удалить функцию `computeSharpe` (`lab.ts:1419–1427`).
2. В sweep-runner (`lab.ts:1357–1358`): заменить `const sharpe = computeSharpe(...)` на `const sharpe = report.sharpe ?? null` — теперь читаем из отчёта.
3. В `SweepRow.sharpe` (`lab.ts:1251`): значение по-прежнему пишется, но источник — `report.sharpe`.
4. В compare-delta (`lab.ts:661–662`): теперь `reportA.sharpe` и `reportB.sharpe` действительно есть в `reportJson` — баг компенсируется автоматически.
5. Обновить тестовую фикстуру `tests/routes/lab.test.ts:550`: `sharpe: 1.24` уже корректна, но нужно убедиться, что весь `reportJson` соответствует новой форме (добавить остальные новые поля либо подтвердить, что их отсутствие = `null` через optional-семантику).

**Тест-план:**
- Существующие тесты `lab.test.ts` зелёные.
- Новый тест на compare endpoint: два прогона с разными Sharpe → `delta.sharpeDelta` не `null` и равен ожидаемой разнице.
- Sweep тест: `SweepRow.sharpe` для каждого прогона совпадает с `report.sharpe` соответствующего `BacktestResult`.

**Критерии готовности:**
- `computeSharpe` удалён из `lab.ts` (grep подтверждает).
- compare endpoint возвращает корректный `sharpeDelta`.
- sweep results используют значение из engine.
- Покрытие тестами не уменьшилось.

---

### 49-T4: Mirror новые метрики в `AdaptiveBacktestReport`

**Цель:** избежать расхождения между двумя backtest-движками.

**Файлы для изменения:**
- `apps/api/src/lib/adaptiveStrategy.ts`
- `apps/api/tests/e2e/adaptiveRegimeBot.test.ts` (если затронуто)

**Шаги реализации:**
1. Расширить `AdaptiveBacktestReport` (`adaptiveStrategy.ts:79`) теми же optional полями: `sharpe?`, `profitFactor?`, `expectancy?`, `avgWinPct?`, `avgLossPct?`, `payoffRatio?`.
2. В adaptive backtest runner (`adaptiveStrategy.ts:156`+): после сборки tradeLog вызвать те же функции из `lib/metrics/`.
3. Empty-report ветка (`adaptiveStrategy.ts:159`): новые поля = `null`.

**Тест-план:**
- Существующие adaptive-тесты зелёные.
- Новый тест: adaptive backtest с известной фикстурой → метрики совпадают с тем же расчётом через DSL evaluator на эквивалентных trade'ах.

**Критерии готовности:**
- `AdaptiveBacktestReport` структурно совместим с `DslBacktestReport` по новым полям.
- Регрессии нет.

---

### 49-T5: Минимальная UI-интеграция в `MetricsTab`

**Цель:** показать новые метрики в Lab UI.

**Файлы для изменения:**
- `apps/web/src/app/lab/ClassicMode.tsx`
- `apps/web/src/app/lab/test/page.tsx`

**Шаги реализации:**
1. В `BacktestReport` interface (page.tsx:61, ClassicMode.tsx:54) добавить optional поля: `sharpe?: number | null`, `profitFactor?: number | null`, `expectancy?: number | null`, `avgWinPct?: number | null`, `avgLossPct?: number | null`, `payoffRatio?: number | null`.
2. В `MetricsTab` (`page.tsx:222`) добавить вторую секцию `<div>` с MetricCard для Sharpe / Profit Factor / Expectancy / Payoff Ratio. Формат: 2 знака после запятой, "—" если `null`.
3. Сохранить существующий layout — добавление снизу, не reflow.

**Тест-план:**
- Ручная: открыть отчёт, проверить отображение новых метрик и null-значений.
- Smoke: рендер `MetricsTab` с минимальным `report` без новых полей — не падает (optional-semantic).

**Критерии готовности:**
- Все новые метрики видны в UI.
- Старые отчёты (без новых полей) рендерятся корректно без ошибок.

---

## Порядок выполнения задач

```
49-T1 (метрики module + tests)
  └── 49-T2 (integrate in DslBacktestReport)
        ├── 49-T3 (cleanup lab.ts computeSharpe + compare bug)
        ├── 49-T4 (mirror in AdaptiveBacktestReport)
        └── 49-T5 (UI MetricsTab)
```

T3 / T4 / T5 могут идти параллельно после T2 — они затрагивают разные файлы.

## Зависимости от других документов

- **docs/46** (Backtest realism) — НЕ блокирует, но рекомендуется выполнить перед metrics, чтобы Sharpe считался на реалистичных PnL значениях.
- **docs/45** (Indicator extraction) — НЕ зависит.
- **docs/47** (Strategy optimizer) — зависит от этого документа: optimizer ranking требует метрики Sharpe / PF / Expectancy в едином формате.
- **docs/48** (Walk-forward) — зависит от этого документа: walk-forward report использует те же per-fold метрики.

## Backward compatibility checklist

- [x] Все новые поля — optional (`?`).
- [x] Существующие поля `DslBacktestReport` не переименовываются и не меняют тип.
- [x] `DslTradeRecord` не меняется.
- [x] `exitReason` enum не расширяется.
- [x] `reportVersion` не вводится (правило отложенного введения зафиксировано выше).
- [x] Адаптивный отчёт обновляется параллельно для согласованности.

## Ожидаемый результат

После завершения всех задач:
- Backtest engine возвращает Sharpe, Profit Factor, Expectancy, Avg Win/Loss, Payoff Ratio как часть единого отчёта.
- `lab.ts` не содержит дублированной логики метрик.
- Sharpe корректно annualized в зависимости от bar interval и avg bars held.
- Compare-delta и sweep-results используют единый источник истины.
- UI Lab отображает расширенный набор метрик.
- Зафиксирован контракт для будущего `reportVersion`.
