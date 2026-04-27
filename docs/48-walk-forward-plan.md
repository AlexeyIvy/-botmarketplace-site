# 48. Walk-Forward Validation Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-26  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (research workflow)

## Контекст

Текущее состояние (проверено по коду):

- Walk-forward в кодовой базе **отсутствует** (`grep -r "walkForward\|walk-forward\|fold\|isBars" apps/api/src apps/web/src` пусто). Этот документ — план первой реализации.
- Точка входа в backtest: `runDslBacktest(candles, dslJson, opts: Partial<DslExecOpts>, mtfContext?)` (`apps/api/src/lib/dslEvaluator.ts:822`); тонкая обёртка `runBacktest(candleData, dslJson, opts, mtfContext?)` (`apps/api/src/lib/backtest.ts:39`).
- Тип отчёта: `DslBacktestReport` (`apps/api/src/lib/dslEvaluator.ts:68`); тип сделки: `DslTradeRecord` (`apps/api/src/lib/dslEvaluator.ts:50`).
- Опции исполнения: `DslExecOpts: { feeBps, slippageBps }` (`apps/api/src/lib/dslEvaluator.ts:78`); после `docs/46-T1` к ним добавится `fillAt`. Маппинг на `ExecOpts` в `apps/api/src/lib/backtest.ts:24`.
- Паттерн загрузки candles из БД, который повторно используем: `prisma.marketCandle.findMany({ where: { ..., openTimeMs: { gte, lte } }, orderBy: { openTimeMs: "asc" } })` — один раз на запуск (`apps/api/src/routes/lab.ts:1281`); конвертация `hours → fromTsMs/toTsMs` (`apps/api/src/routes/lab.ts:534`).
- Шаблон fire-and-forget run-эндпоинта со статусной БД-моделью: sweep — `runSweepAsync` (`apps/api/src/routes/lab.ts:1258`), статусы `PENDING|RUNNING|DONE|FAILED` (`apps/api/prisma/schema.prisma:677`). Walk-forward повторяет этот паттерн.
- Структурный шаблон Prisma модели: `BacktestSweep` (`apps/api/prisma/schema.prisma:686–708`) — поля `id`, `workspaceId`, `strategyVersionId`, `datasetId`, `status`, `progress`, `*Json`. Walk-forward Prisma модель повторяет ту же структуру.
- Хранилище per-fold отчётов: можно использовать существующую `BacktestResult` (`apps/api/prisma/schema.prisma:578–619`) как референс структуры; в первом этапе храним fold-отчёты как JSON внутри родительской записи, без отдельной таблицы.
- Метрики: `apps/api/src/lib/metrics.ts` сейчас содержит только Prometheus (`Registry`, `collectDefaultMetrics`, `Counter`, `Histogram`) и не относится к backtest-метрикам. Папка `apps/api/src/lib/backtestMetrics/` ещё **не создана** — она появится в `docs/49-T1` и принесёт pure-функции `sharpeRatio`, `profitFactor`, `expectancy`. `maxDrawdownPct` остаётся в `dslEvaluator.ts` (уже вычисляется там через `cumulativePnl/peakPnl`). Walk-forward aggregate использует утилиты из `backtestMetrics/` и поля `report.sharpe` / `report.profitFactor` / `report.expectancy` (появляются в `DslBacktestReport` после `docs/49-T2`).
- В `apps/web/src/app/lab/` walk-forward UI отсутствует.

## Цель

- Реализовать walk-forward validation как новый research-режим: набор fold-ов с разделением на in-sample (IS) / out-of-sample (OOS), per-fold backtest, агрегация метрик.
- Поддержать оба режима окна: **rolling** (двигается и начало, и конец) и **anchored** (начало = 0, двигается только конец).
- Минимальная UI: панель в Lab → Test рядом с `OptimisePanel`.
- Без изменений ядра execution: `runBacktest` / `dslEvaluator` остаются как есть.

## Решение по форме fold-конфигурации

Конфигурация fold-ов задаётся в условиях **bars** (числу свечей), а не времени, потому что текущий research-стек оперирует датасетами в свечах (см. sweep candle load — `findMany({ orderBy: openTimeMs })`). Это даёт детерминизм независимо от gap-ов в данных.

```ts
type FoldConfig = {
  isBars: number;       // длина IS окна
  oosBars: number;      // длина OOS окна
  step: number;         // шаг сдвига (обычно = oosBars для непересекающихся OOS)
  anchored: boolean;    // true: IS всегда от 0; false: rolling
};
```

`split(candles, foldCfg)` — pure функция: для `i = 0,1,2,...` возвращает массив fold-ов до тех пор, пока следующий OOS-блок целиком помещается в данные. Лимит: `foldCount ≤ 20` (тот же порядок, что у sweep, чтобы не переусложнять in-process executor).

## Не входит в задачу

- Параметрическая оптимизация внутри IS окна (выбор лучшего параметра по IS, проверка на OOS) — это **walk-forward optimization**, отдельная задача после интеграции с `docs/47`.
- Multi-asset / portfolio-level walk-forward.
- Persisted per-fold candle slices в отдельной таблице — храним fold-результаты как JSON.
- Distributed execution, worker pool, BullMQ — fire-and-forget in-process.
- Введение `reportVersion` (правило отложено в `docs/49`).
- Изменения `runBacktest` / `dslEvaluator` ядра.
- UI для визуализации equity-кривой fold-by-fold (только табличный вывод в первой версии).
- Кросс-валидация на shuffled-блоках, purging, embargo (advanced techniques) — out of scope.

---

## Задачи

### 48-T1: Pure функция `split` — генерация fold-ов

**Цель:** реализовать чистую детерминированную функцию разбиения массива свечей на IS/OOS fold-ы по `FoldConfig`. Без вызова backtest, без I/O.

**Файлы для изменения:**
- Создать `apps/api/src/lib/walkForward/split.ts`.
- Создать `apps/api/src/lib/walkForward/types.ts` — общие типы (`FoldConfig`, `Fold`).
- Создать `apps/api/tests/lib/walkForward/split.test.ts`.

**Шаги реализации:**
1. В `types.ts` определить:
   ```ts
   export type FoldConfig = { isBars: number; oosBars: number; step: number; anchored: boolean };
   export type FoldRange = { fromIndex: number; toIndex: number; fromTsMs: number; toTsMs: number };
   export type Fold = {
     foldIndex: number;
     isSlice: Candle[];
     oosSlice: Candle[];
     isRange: FoldRange;
     oosRange: FoldRange;
   };
   ```
2. Реализовать `split(candles: Candle[], cfg: FoldConfig): Fold[]`:
   - Валидация: `isBars > 0`, `oosBars > 0`, `step > 0`, `candles.length ≥ isBars + oosBars`. Иначе бросать `Error` с понятным сообщением.
   - Для `i = 0, 1, 2, ...`:
     - `oosStart = isBars + i * step` (для anchored) ИЛИ `oosStart = isBars + i * step` с `isStart = i * step` (для rolling).
     - `isStart = anchored ? 0 : i * step`.
     - `oosEnd = oosStart + oosBars`.
     - Если `oosEnd > candles.length` → break.
     - Создать срезы (использовать `Array.prototype.slice`, не мутировать исходный массив).
     - Заполнить `isRange.fromTsMs/toTsMs` из `candles[isStart].openTimeMs` и `candles[oosEnd-1].openTimeMs` (то же для OOS).
3. Обеспечить, что для anchored все fold-ы имеют общий начальный индекс 0; для rolling — одинаковую длину IS.
4. Документировать в JSDoc формулу для каждого режима — это критично для воспроизводимости.

**Тест-план:**
- 100 свечей, `isBars=50, oosBars=10, step=10, anchored=false` → 5 fold-ов: `[0..50)+[50..60)`, `[10..60)+[60..70)`, ..., `[40..90)+[90..100)`.
- Тот же набор с `anchored=true` → 5 fold-ов: `[0..50)+[50..60)`, `[0..60)+[60..70)`, ..., `[0..90)+[90..100)` (IS растёт, OOS длиной 10).
- 100 свечей, `isBars=80, oosBars=30, step=10` → 0 fold-ов (`isBars+oosBars = 110 > 100`) — выбросить ошибку.
- Граничный: `isBars+oosBars = candles.length` ровно → 1 fold.
- Иммутабельность: `candles` после `split` не изменён (deep equality).
- Детерминизм: одинаковый input → одинаковый output (повторный запуск).

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все unit-тесты зелёные.
- Никаких импортов из `dslEvaluator`, `runBacktest`, БД, Express — pure функция.

---

### 48-T2: `runWalkForward` — per-fold backtest без агрегации

**Цель:** реализовать pure-ish функцию, которая для каждого fold-а из 48-T1 запускает `runBacktest` на IS и на OOS, возвращая полный набор отчётов. Без БД, без HTTP — только in-memory.

**Файлы для изменения:**
- Создать `apps/api/src/lib/walkForward/run.ts`.
- Дополнить `apps/api/src/lib/walkForward/types.ts` (`FoldReport`, `WalkForwardReport`).
- Создать `apps/api/tests/lib/walkForward/run.test.ts`.

**Шаги реализации:**
1. В `types.ts` добавить:
   ```ts
   export type FoldReport = {
     foldIndex: number;
     isReport: DslBacktestReport;
     oosReport: DslBacktestReport;
     isRange: FoldRange;
     oosRange: FoldRange;
   };
   export type WalkForwardReport = {
     folds: FoldReport[];
     // aggregate добавляется в 48-T3
   };
   ```
2. Реализовать `runWalkForward(candles, dslJson, opts: Partial<DslExecOpts>, foldCfg: FoldConfig, onProgress?: (done: number, total: number) => void): WalkForwardReport`:
   - Получить `folds = split(candles, foldCfg)` (через 48-T1).
   - Для каждого fold-а: `isReport = runBacktest(fold.isSlice, dslJson, opts, undefined)`, затем `oosReport = runBacktest(fold.oosSlice, dslJson, opts, undefined)` — два независимых вызова.
   - `mtfContext` оставляем `undefined` в первой версии. Поддержка MTF в walk-forward — отдельная follow-up задача (требует нарезки MTF-контекста синхронно с базовыми свечами).
   - После каждого fold-а вызывать `onProgress?.(foldIndex + 1, folds.length)` для прогресса в БД-обёртке (48-T5).
3. `opts.fillAt` пробрасывается как есть; до закрытия `docs/46-T1` поле может отсутствовать в типе и не передаваться.
4. Обеспечить детерминизм: порядок fold-ов фиксирован (48-T1), `runBacktest` сам по себе детерминирован (по `docs/44`).

**Тест-план:**
- Smoke: 100 свечей, `isBars=50, oosBars=10, step=10, rolling`, простой DSL-стратегия (например, "buy на каждой N-й свече") → 5 fold-ов в `report.folds`, каждый содержит непустой `isReport.tradeLog` и `oosReport.tradeLog`.
- Иммутабельность входов: `candles` и `dslJson` после `runWalkForward` не изменены.
- Прогресс: `onProgress` вызван `folds.length` раз с правильными аргументами.
- Сравнение: `runBacktest(folds[0].isSlice, dsl, opts)` = `report.folds[0].isReport` (per-fold вызов независим).

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Unit-тесты зелёные.
- Никаких side-effects кроме вызовов `runBacktest`.
- Импорты: `split` (48-T1), `runBacktest`, типы из `dslEvaluator`. Без БД, без Express.

---

### 48-T3: Aggregate metrics для `WalkForwardReport`

**Цель:** добавить в `WalkForwardReport` поле `aggregate` со сводными метриками по fold-ам, используя метрические утилиты из `docs/49`.

**Файлы для изменения:**
- `apps/api/src/lib/walkForward/aggregate.ts` (создать).
- `apps/api/src/lib/walkForward/run.ts` — заполнять `aggregate` после прохода всех fold-ов.
- Дополнить `apps/api/src/lib/walkForward/types.ts` (`WalkForwardAggregate`).
- `apps/api/tests/lib/walkForward/aggregate.test.ts` (создать).

**Шаги реализации:**
1. В `types.ts` добавить:
   ```ts
   export type WalkForwardAggregate = {
     foldCount: number;
     avgIsPnlPct: number;
     avgOosPnlPct: number;
     totalOosPnlPct: number;     // суммарный PnL по OOS-блокам, как индикатор реальной выживаемости
     avgIsSharpe: number | null;
     avgOosSharpe: number | null;
     isOosPnlRatio: number | null;  // avgOosPnlPct / avgIsPnlPct, null если знаменатель 0
     oosWinFoldShare: number;    // доля fold-ов с OOS pnlPct > 0
   };
   ```
2. Реализовать `aggregate(folds: FoldReport[]): WalkForwardAggregate` как чистую функцию:
   - `avgIsPnlPct = mean(folds.map(f => f.isReport.pnlPct))`.
   - `avgOosPnlPct = mean(folds.map(f => f.oosReport.pnlPct))`.
   - `totalOosPnlPct = sum(folds.map(f => f.oosReport.pnlPct))` (простая сумма; в первой версии не реинвестируем — отметить в комментарии как ограничение).
   - `avgIsSharpe / avgOosSharpe` — берём `report.sharpe` (после `docs/49-T2`); пропускаем `null`-значения; если все `null` → `null`.
   - `oosWinFoldShare = count(f => f.oosReport.pnlPct > 0) / folds.length`.
3. До завершения `docs/49-T2` (когда `report.sharpe` ещё не существует на уровне ядра): использовать локальный fallback — копировать функцию из текущего `computeSharpe` (`apps/api/src/routes/lab.ts:1357`) во временный helper `apps/api/src/lib/walkForward/_localSharpe.ts`. Этот helper удаляется в follow-up PR после `docs/49-T2` — задокументировать TODO в файле.
4. В `run.ts` в конце `runWalkForward` вызывать `aggregate(folds)` и присвоить результату.

**Тест-план:**
- Фиксированные фикстуры `FoldReport[]`: 3 fold-а с известными `pnlPct` → проверить все поля aggregate.
- Все `oosReport.pnlPct = 0` → `oosWinFoldShare = 0`.
- Все sharpe null → `avgOosSharpe = null`.
- `avgIsPnlPct = 0` → `isOosPnlRatio = null` (избежать деления на 0).

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Unit-тесты зелёные.
- TODO про `_localSharpe.ts` зафиксирован в файле и в PR-описании.
- Aggregate чисто функционален (нет I/O).

---

### 48-T4: Prisma модель `WalkForwardRun`

**Цель:** добавить таблицу для хранения запусков walk-forward по структурному шаблону `BacktestSweep`.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma`.
- Новая миграция в `apps/api/prisma/migrations/<timestamp>_add_walk_forward_run/`.

**Шаги реализации:**
1. В `schema.prisma` добавить enum рядом с `SweepStatus`:
   ```prisma
   enum WalkForwardStatus {
     PENDING
     RUNNING
     DONE
     FAILED
   }
   ```
2. Добавить модель (структурный аналог `BacktestSweep`):
   ```prisma
   model WalkForwardRun {
     id                 String              @id @default(cuid())
     workspaceId        String
     strategyVersionId  String
     datasetId          String
     status             WalkForwardStatus   @default(PENDING)
     foldConfigJson     Json
     foldCount          Int                 @default(0)
     progress           Float               @default(0) // 0..1
     foldsJson          Json?               // массив FoldReport (без полных tradeLog'ов — см. шаг 4)
     aggregateJson      Json?
     error              String?
     createdAt          DateTime            @default(now())
     updatedAt          DateTime            @updatedAt
     // Индексы по аналогии с BacktestSweep
     @@index([workspaceId, createdAt])
     @@index([strategyVersionId])
   }
   ```
3. Связи (`workspace`, `strategyVersion`, `dataset`) — определить так же, как в `BacktestSweep`. Если у этих моделей есть `relation`-поля на родительские стороны — добавить аналогичные (например, `WorkspaceRelation` `walkForwardRuns WalkForwardRun[]`).
4. Размер `foldsJson`: per-fold отчёт включает `tradeLog`. Для 20 fold-ов с сотнями сделок JSON-объект может стать большим. **Решение для первой версии:** хранить в `foldsJson` усечённую форму — без `tradeLog` каждого fold-а, только метрики (`pnlPct`, `winRate`, `maxDrawdownPct`, `tradeCount`, `sharpe`, ranges, foldIndex). Полный `tradeLog` доступен только в момент исполнения и не сохраняется. Если в будущем понадобится — отдельная задача.
5. Сгенерировать миграцию (`prisma migrate dev --name add_walk_forward_run`), убедиться, что она additive: только `CREATE TABLE` и `CREATE INDEX`, никаких изменений существующих таблиц.

**Тест-план:**
- Миграция применяется на чистой БД и на БД со всеми существующими данными — без ошибок.
- `prisma generate` без warnings.
- Smoke insert: создание `WalkForwardRun` через `prisma.walkForwardRun.create({ data: {...} })` работает.

**Критерии готовности:**
- Миграция additive.
- Schema проходит lint Prisma.
- Структура повторяет `BacktestSweep` для консистентности.

---

### 48-T5: HTTP эндпоинты — `POST /lab/backtest/walk-forward` и `GET /lab/backtest/walk-forward/:id`

**Цель:** обернуть `runWalkForward` в fire-and-forget эндпоинт по аналогии со sweep, плюс эндпоинт опроса статуса.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — добавить два новых хэндлера и одну `runWalkForwardAsync`-обёртку.
- `apps/api/tests/routes/lab.test.ts` — e2e тесты.

**Шаги реализации:**
1. Определить тело запроса:
   ```ts
   type WalkForwardRequestBody = {
     datasetId: string;
     strategyVersionId: string;
     fold: { isBars: number; oosBars: number; step: number; anchored: boolean };
     feeBps?: number;
     slippageBps?: number;
     fillAt?: "OPEN" | "CLOSE" | "NEXT_OPEN";   // только если docs/46-T1 закрыт
   };
   ```
2. `POST /lab/backtest/walk-forward`:
   - Те же rate limits и concurrency, что у sweep (5/min, max 2 concurrent per workspace) — переиспользовать тот же middleware/счётчик.
   - Валидировать `fold`: позитивные числа, `isBars + oosBars ≤ candles.length` (после загрузки candles).
   - **Pre-flight foldCount check:** загрузить candles один раз (то же `findMany` что и у sweep, `apps/api/src/routes/lab.ts:1281–1298`), вызвать `split(candles, fold)`, проверить `folds.length ≤ 20`. Если больше или меньше 1 — 400 с понятным сообщением.
   - Создать `WalkForwardRun` со `status: PENDING`, `foldCount = folds.length`, `foldConfigJson = fold`, `progress = 0`. Вернуть `{ id }`.
   - Запустить `runWalkForwardAsync(id, candles, ...)` через `setImmediate` или эквивалент (как `runSweepAsync`, `apps/api/src/routes/lab.ts:1258`) — fire-and-forget, без `await` в обработчике.
3. `runWalkForwardAsync(id, candles, dslJson, opts, fold)`:
   - Установить `status: RUNNING`.
   - Вызвать `runWalkForward(candles, dslJson, opts, fold, onProgress)` где `onProgress(done, total)` обновляет `progress = done / total` в БД (батч-обновление — раз в N fold-ов, чтобы не флудить транзакциями).
   - После завершения: усечённую форму `folds` (см. 48-T4 шаг 4) сохранить в `foldsJson`, `aggregate` — в `aggregateJson`, `status: DONE`.
   - При исключении: `status: FAILED`, `error = e.message`. Не пробрасывать ошибку выше (fire-and-forget).
4. `GET /lab/backtest/walk-forward/:id`:
   - Те же auth-проверки, что у `GET /lab/backtest/sweep/:id` (`apps/api/src/routes/lab.ts:935`) — workspace ownership.
   - Возвращать полный объект записи: `{ id, status, progress, foldCount, fold, folds, aggregate, error, createdAt, updatedAt }`.
5. (Опционально) `GET /lab/backtest/walk-forwards` — list endpoint по аналогии со sweep, если есть запрос со стороны UI; иначе отложить.

**Тест-план:**
- e2e: POST с валидным fold-конфигом → 201 с `id`; повторный GET через короткий интервал → `status: RUNNING|DONE`; финально `DONE` с непустым `aggregate`.
- e2e: POST с `isBars + oosBars > candles.length` → 400.
- e2e: POST с конфигом, дающим `foldCount > 20` → 400.
- e2e: POST другим workspace + GET с этим workspace → 403/404.
- e2e: при синтетической ошибке внутри `runBacktest` (моком) → запись имеет `status: FAILED, error: "..."`.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- e2e тесты зелёные.
- Rate limit и concurrency делятся со sweep корректно.
- Хэндлер не блокирует event loop (fire-and-forget).

---

### 48-T6: Минимальный UI — `WalkForwardPanel`

**Цель:** добавить в Lab → Test панель walk-forward рядом с `OptimisePanel`. Запуск, polling, табличный вывод fold-by-fold + сводка.

**Файлы для изменения:**
- Создать `apps/web/src/app/lab/test/WalkForwardPanel.tsx`.
- `apps/web/src/app/lab/test/page.tsx` (или текущий контейнер Test-вкладки) — подключить новую панель.

**Шаги реализации:**
1. Поля формы: `isBars`, `oosBars`, `step`, `anchored` (toggle), `feeBps`, `slippageBps`, (после `docs/46-T1`) `fillAt`. Дефолты подобрать так, чтобы для типичного датасета на 1000 свечей получалось 4–8 fold-ов (например, `isBars=400, oosBars=100, step=100, anchored=false`).
2. Превью: до отправки показывать "примерное число fold-ов" — для этого UI не вызывает `split` (она серверная), а считает по той же формуле локально: `floor((N - isBars - oosBars) / step) + 1`. Если значение `> 20` — кнопка disabled с подсказкой.
3. Запуск: `POST /lab/backtest/walk-forward` → получаем `id` → polling `GET /lab/backtest/walk-forward/:id` каждые `POLL_INTERVAL_MS = 2000` ms (та же константа, что у `OptimisePanel`).
4. Состояния: `idle | running | done | failed`. Прогрессбар = `progress * 100%`.
5. Таблица fold-by-fold (после `done`): колонки `Fold #`, `IS range`, `OOS range`, `IS pnl%`, `OOS pnl%`, `OOS winRate`, `OOS maxDD%`, `OOS sharpe` (если есть). Источник — поля из `foldsJson`.
6. Aggregate-блок: показывать `avgIsPnlPct`, `avgOosPnlPct`, `totalOosPnlPct`, `oosWinFoldShare`, `isOosPnlRatio` со всех fold-ов.
7. Без графика equity (явно out of scope первой версии).

**Тест-план:**
- Ручной smoke в браузере:
  - Корректный конфиг → запуск → polling → таблица + aggregate.
  - `(N - isBars - oosBars) / step + 1 > 20` → кнопка disabled, подсказка показана.
  - `isBars + oosBars > N` (видим из preview) → кнопка disabled.
  - Failed run (синтетический) → видим `error` в UI.
- Не вводит регрессий в `OptimisePanel` (общая страница рендерится).

**Критерии готовности:**
- TypeScript-проверка фронтенда проходит.
- Lab UI рендерится, golden-path запуска и polling работает в браузере.
- Никаких изменений `OptimisePanel.tsx` или общих компонентов.

---

### 48-T7: Тесты — split, run, aggregate, e2e

**Цель:** покрыть слой walk-forward тестами на трёх уровнях: pure split, pure runner, e2e endpoint.

**Файлы для изменения:**
- `apps/api/tests/lib/walkForward/split.test.ts` (создать в 48-T1, расширить тут при необходимости).
- `apps/api/tests/lib/walkForward/run.test.ts` (создать в 48-T2).
- `apps/api/tests/lib/walkForward/aggregate.test.ts` (создать в 48-T3).
- `apps/api/tests/routes/lab.test.ts` — добавить блок тестов `/lab/backtest/walk-forward` рядом с существующим блоком sweep (`строки 442–515`).

**Шаги реализации:**
1. Свести unit-тесты split/run/aggregate в единый зелёный набор. Убедиться, что фикстуры свечей (например, синтетический ramp/sin) одинаковые между файлами — вынести в `apps/api/tests/lib/walkForward/_fixtures.ts`.
2. e2e блок в `lab.test.ts` (паттерн копировать со sweep, `строки 442–515`):
   - happy-path POST + polling до `DONE` + проверка `aggregateJson`.
   - validation 400 (см. 48-T5 тест-план).
   - workspace isolation 403.
   - failed-run: подменить `runBacktest` мок-ошибкой, проверить `status=FAILED`.
3. Все тесты детерминированы: фикстуры зашиты, никаких `Date.now()` без явного контроля, никаких PRNG без seed.
4. Если walk-forward использует `_localSharpe.ts` (см. 48-T3 шаг 3) — отдельный unit на него; после удаления helper-а в follow-up удалить и этот тест.

**Тест-план:**
- `npm test` в `apps/api` зелёный.
- Все тесты walk-forward проходят локально и на CI.
- Smoke time: e2e тест walk-forward не превышает разумного времени (ориентир: <5s на маленькой фикстуре свечей; жёсткого порога не выставляем).

**Критерии готовности:**
- Все новые тесты зелёные.
- Существующие тесты sweep остаются зелёными (изменений в их коде нет).
- Walk-forward слой имеет покрытие unit-тестами на каждом уровне (split, run, aggregate) + e2e на эндпоинте.

---

## Порядок выполнения задач

```
48-T1 → 48-T2 → 48-T3 → 48-T4 → 48-T5 → 48-T6 → 48-T7
```

- 48-T1 первым: pure функция, без зависимостей.
- 48-T2 после T1: использует `split`.
- 48-T3 после T2: использует `FoldReport` тип.
- 48-T4 параллельно с T2/T3 возможно, но удобнее делать последовательно.
- 48-T5 требует T1–T4 (использует `runWalkForward`, Prisma модель).
- 48-T6 после T5 (UI вызывает эндпоинт).
- 48-T7 — последняя задача или встроена инкрементально в каждую предыдущую.

Каждая задача — отдельный PR.

## Зависимости от других документов

- `docs/49` — метрические утилиты (`sharpe`, `profitFactor`, `expectancy`, `maxDrawdownPct`) для `WalkForwardAggregate`. До закрытия `docs/49-T2` aggregate использует временный `_localSharpe.ts` helper (см. 48-T3 шаг 3). Это явный технический долг, удаляется follow-up PR-ом.
- `docs/46-T1` — поле `fillAt` в `DslExecOpts`. Косвенная: до закрытия `docs/46-T1` `runWalkForward` не передаёт `fillAt` (его в типе нет). После — добавляется в `WalkForwardRequestBody` и пробрасывается.
- **НЕ зависит от `docs/47`** — walk-forward сам по себе без оптимизации параметров. Walk-forward optimization (комбинация двух) — отдельная задача после стабилизации обоих.

## Backward compatibility checklist

- Walk-forward — полностью новый функционал. Никаких существующих API не модифицируется.
- Prisma миграция additive (только `CREATE TABLE` для `WalkForwardRun` и нового enum-а).
- `runBacktest`, `runDslBacktest`, `DslBacktestReport`, `DslTradeRecord`, `DslExecOpts` не изменяются.
- `apps/web/src/app/lab/` — добавляется новый компонент, существующие компоненты не изменяются.
- `reportVersion` не вводится (правило отложено в `docs/49`).
- Метрические утилиты не дублируются вне walk-forward слоя — после `docs/49-T2` локальный sharpe удаляется.

## Ожидаемый результат

После завершения всех задач:
- Walk-forward доступен как новый research-режим в Lab → Test.
- Поддерживаются оба режима окна (rolling, anchored), задаваемые в bars.
- Лимит `foldCount ≤ 20` соблюдён, fire-and-forget без BullMQ/worker pool.
- Per-fold метрики и сводный aggregate сохранены в БД и доступны через poll-эндпоинт.
- UI позволяет запустить walk-forward, отслеживать прогресс и видеть результаты fold-by-fold.
- Ядро execution (`runBacktest`, `dslEvaluator`) не изменено.
- Слой walk-forward готов к интеграции с `docs/47` (walk-forward optimization) как отдельная follow-up задача.
