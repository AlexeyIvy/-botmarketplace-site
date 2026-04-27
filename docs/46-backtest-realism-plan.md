# 46. Backtest Realism Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-27  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (research workflow)

## Контекст

Текущее состояние (проверено по коду):

- Тонкая обёртка `runBacktest(candleData, dslJson, opts: Partial<ExecOpts>, mtfContext?)` (`apps/api/src/lib/backtest.ts:39`) делегирует в `runDslBacktest`.
- `ExecOpts` декларирует **только одно допустимое значение** `fillAt`: `{ feeBps: number; slippageBps: number; fillAt: "CLOSE" }` (`apps/api/src/lib/backtest.ts:24–28`). Docstring явно фиксирует ограничение: "fillAt = "CLOSE" — fill at candle close price (only supported value)" (`apps/api/src/lib/backtest.ts:11`).
- В ядре `DslExecOpts` поле `fillAt` **отсутствует** — оно живёт только на уровне обёртки и не пробрасывается ниже: `export interface DslExecOpts { feeBps: number; slippageBps: number }` (`apps/api/src/lib/dslEvaluator.ts:78–81`).
- Внутри `runDslBacktest` (`apps/api/src/lib/dslEvaluator.ts:822`) на entry хардкод close-fill: `effectiveEntry = c.close * entryMult` (`apps/api/src/lib/dslEvaluator.ts:1134`). На exit аналогично через `last.close * exitMult` (`apps/api/src/lib/dslEvaluator.ts:1185`).
- Slippage применяется **асимметрично**: `entryMult = 1 + (feeBps + slippageBps) / 10_000`, `exitMult = 1 - feeBps / 10_000` (`apps/api/src/lib/dslEvaluator.ts:893–894`). На exit slippage не вычитается — это занижает реальный издержки round-trip-а.
- Fees единым `feeBps` без разделения taker/maker. На текущем этапе все ордера market (taker-only), но раздельные ставки понадобятся при добавлении лимитных входов/выходов.
- Routes-слой: `ALLOWED_FILL_AT = ["CLOSE"] as const`, `type FillAt = typeof ALLOWED_FILL_AT[number]` (`apps/api/src/routes/lab.ts:30–31`); тело запроса `StartBacktestBody.fillAt?: FillAt` (`apps/api/src/routes/lab.ts:54`); валидация по этому списку (`apps/api/src/routes/lab.ts:410–411`); хардкоды `"CLOSE"` в sweep (`apps/api/src/routes/lab.ts:1339, 1349`) и в одиночном backtest (`apps/api/src/routes/lab.ts:1485`); preview (`apps/api/src/routes/lab.ts:564`).
- Frontend: `fillAt` типизирован как `string` и всегда отправляется `"CLOSE"` (`apps/web/src/app/lab/ClassicMode.tsx:80, 541`; `apps/web/src/app/lab/test/page.tsx:54, 1308`); отображается в snapshot-таблице (`apps/web/src/app/lab/ClassicMode.tsx:904`; `apps/web/src/app/lab/test/page.tsx:202`).
- Prisma: поля под realism уже есть, **миграции не требуются**: `BacktestResult.feeBps Int`, `slippageBps Int`, `fillAt String @default("CLOSE")`, `engineVersion String @default("unknown")` (`apps/api/prisma/schema.prisma:598–602`); `BacktestSweep.feeBps Int`, `slippageBps Int` (`apps/api/prisma/schema.prisma:693–694`).
- `engineVersion` уже пишется как `process.env.COMMIT_SHA ?? "unknown"` (`apps/api/src/routes/lab.ts:439, 584, 1307`; `apps/api/src/routes/datasets.ts:143`) — отдельная воспроизводимость уже работает; этот документ её не затрагивает.
- Тесты: основные фикстуры в `apps/api/tests/lib/backtest.test.ts`, `apps/api/tests/lib/dslEvaluator.test.ts`, `apps/api/tests/lib/dcaBacktest.test.ts`, `apps/api/tests/lib/exitEngine.test.ts`. Sweep e2e — `apps/api/tests/routes/lab.test.ts:442–515`.
- `apps/api/src/lib/funding/` существует (`basis.ts`, `fetcher.ts`, `hedgePlanner.ts`, `ingestion.ts`, ...) для live-слоя, но в `runDslBacktest` funding-расходы не учитываются. Это известный gap, **за рамками этого документа** — см. раздел "Не входит в задачу".

## Цель

- Закрыть три самых грубых источника нереалистичности в текущем backtest: (1) только close-fill, (2) асимметричный slippage, (3) объединённый fee без taker/maker.
- Все правки additive: дефолты сохраняют текущее поведение точно бит-в-бит, чтобы существующие записи `BacktestResult` оставались сравнимыми.
- Поднять `fillAt` с уровня обёртки в ядро `DslExecOpts` — это разблокирует docs/47-T3 и docs/48-T5, которые сейчас вынуждены передавать `"CLOSE"` хардкодом.

## Решение по форме fill-policy

Поддерживаемые значения `fillAt`:

- `"CLOSE"` — fill по close сигнальной свечи. Текущее поведение, остаётся default.
- `"OPEN"` — fill по open сигнальной свечи. Полезно для confirmation-style стратегий, где сигнал валиден на открытии следующего периода.
- `"NEXT_OPEN"` — fill по open **следующей** свечи. Это устраняет lookahead на close: сигнал, посчитанный по closed bar, исполняется на open ближайшей будущей свечи. Для стратегий с indicator-сигналами это самый честный режим.

`"NEXT_OPEN"` для exit-сигналов (indicator_exit) аналогично — exit на open следующей свечи. Для SL/TP/trailing stop fillAt **не применяется** — они срабатывают по intra-bar high/low (как сейчас); это явно документируется в комментарии. Funding и partial fills — out of scope (см. ниже).

## Не входит в задачу

- Funding accrual для perpetual датасетов. `apps/api/src/lib/funding/` уже агрегирует rate-историю для live-слоя; интеграция в `runDslBacktest` — отдельный план (`docs/50` или follow-up к этому документу). Причина выноса: требует синхронизации funding-таймсерии с candle-таймсерией, нового `DslBacktestReport.fundingPnlPct`, отдельного UI-блока и e2e фикстур funding-rate. Объём сравним с этим документом целиком.
- Partial fills, queue position, latency model. Out of scope первой версии.
- Order book impact / volume-aware slippage. Текущая модель — фиксированный bps; volume-aware — отдельная задача после стабилизации funding.
- Maker-only / limit-order backtest. После 46-T3 структура полей готова к maker-режиму, но сама логика лимитных входов с очередью/таймаутами — отдельный план.
- Изменение `engineVersion`-логики или ввод `reportVersion` (правило отложено в `docs/49`).
- Изменение поведения SL/TP/trailing — они продолжают срабатывать по intra-bar high/low.
- Изменение MTF-слоя.

---

## Задачи

### 46-T1: Поднять `fillAt` в ядро + поддержать `OPEN` и `NEXT_OPEN`

**Цель:** перенести параметр `fillAt` из обёртки в `DslExecOpts`, расширить enum до трёх значений и реализовать новые режимы fill в `runDslBacktest`.

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts` — расширить `DslExecOpts` (`строка 78`), переписать entry-fill (`строка 1134`), exit-fill для `indicator_exit` и `end_of_data` (`строка 1185`).
- `apps/api/src/lib/backtest.ts` — расширить `ExecOpts` (`строка 24`), пробросить `fillAt` в `runDslBacktest` (`строка 45`), обновить docstring (`строки 10–14`).
- `apps/api/tests/lib/dslEvaluator.test.ts` и `apps/api/tests/lib/backtest.test.ts` — добавить кейсы.

**Шаги реализации:**
1. В `dslEvaluator.ts`:
   ```ts
   export type DslFillAt = "OPEN" | "CLOSE" | "NEXT_OPEN";
   export interface DslExecOpts {
     feeBps: number;
     slippageBps: number;
     fillAt: DslFillAt;
   }
   ```
2. В `runDslBacktest` дефолтить `fillAt = "CLOSE"` при чтении из `opts` (так же, как `feeBps = 0`). Это сохраняет backward compat: старые вызовы без `fillAt` ведут себя ровно как сейчас.
3. Entry-fill (`строка 1134`): заменить хардкод `c.close * entryMult` на:
   - `"CLOSE"` → `c.close * entryMult` (как сейчас).
   - `"OPEN"` → `c.open * entryMult`.
   - `"NEXT_OPEN"` → если `i + 1 < candles.length` → `candles[i+1].open * entryMult` и сдвинуть `entryTime = candles[i+1].openTime`, `entryBarIndex = i+1`. Если `i + 1 >= candles.length` (сигнал на последней свече) → entry **не открывается** (нет следующей свечи для исполнения), `inPosition` остаётся `false`. Записать в `tradeLog` ничего не нужно — entry просто пропускается. Документировать это поведение в комментарии.
4. Exit-fill для `indicator_exit`: при срабатывании сигнала выхода на свече `i` — для `"NEXT_OPEN"` exit исполняется по `candles[i+1].open`, иначе по той же свече (open или close по `fillAt`). Если `i + 1 >= candles.length` для `"NEXT_OPEN"` — exit на close текущей свечи (degraded fallback, чтобы позиция не повисла; задокументировать в комментарии).
5. Exit-fill для `end_of_data` (`строка 1185`): остаётся `last.close` независимо от `fillAt` — это синтетическое закрытие, не реальный exit-сигнал. Зафиксировать в комментарии.
6. SL/TP/trailing срабатывания — НЕ затрагивать. Они идут по intra-bar high/low, `fillAt` к ним не относится. Добавить комментарий перед блоком SL/TP-проверок: "SL/TP/trailing trigger on intra-bar extremes; fillAt applies only to entry and indicator_exit/end_of_data exits."
7. В `backtest.ts`:
   ```ts
   export type FillAt = "OPEN" | "CLOSE" | "NEXT_OPEN";
   export interface ExecOpts { feeBps: number; slippageBps: number; fillAt: FillAt }
   ```
   Пробросить `fillAt: opts.fillAt ?? "CLOSE"` в `runDslBacktest`. Обновить JSDoc и шапку файла (`строки 10–14`) — отразить три значения.

**Тест-план:**
- Существующие тесты `dslEvaluator.test.ts` и `backtest.test.ts` зелёные без правок (default `"CLOSE"` сохраняет поведение).
- Новый кейс на `"OPEN"`: фикстура из 5 свечей с известными `open != close`, простая стратегия с сигналом на свече i. Проверить, что `entryPrice = candles[i].open * entryMult`.
- Новый кейс на `"NEXT_OPEN"`: тот же сигнал на свече i — entry на `candles[i+1].open`, `entryTime = candles[i+1].openTime`.
- Edge: сигнал на последней свече при `"NEXT_OPEN"` → trade не открыт, `tradeLog` без новой записи.
- Edge: indicator_exit на последней свече при `"NEXT_OPEN"` → exit по close (fallback).

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- Новые тест-кейсы зелёные.
- В `backtest.ts` docstring отражает три значения `fillAt`.

---

### 46-T2: Симметричный slippage — учёт на exit

**Цель:** применить slippage и при выходе из позиции, а не только при входе. Сделать это так, чтобы default-поведение для существующих записей не сломалось (`slippageBps = 0` → результат идентичен текущему).

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts` — `entryMult`/`exitMult` (`строки 893–894`).
- `apps/api/tests/lib/dslEvaluator.test.ts` — расширить тест-кейсы.

**Шаги реализации:**
1. Текущая формула:
   ```ts
   const entryMult = 1 + (feeBps + slippageBps) / 10_000;
   const exitMult  = 1 - feeBps / 10_000;
   ```
   Заменить на:
   ```ts
   const entryMult = 1 + (feeBps + slippageBps) / 10_000;
   const exitMult  = 1 - (feeBps + slippageBps) / 10_000;
   ```
   То есть slippage вычитается из proceeds на exit ровно так же, как добавлялся к cost на entry. Для long это означает: и купили дороже, и продали дешевле — двойной slippage cost за round-trip. Для short — симметрично.
2. Backward compatibility: при `slippageBps = 0` формулы идентичны старым — все существующие тесты проходят без правок. При `slippageBps > 0` `pnlPct` уменьшается; это **сознательное** изменение, отражающее реальный round-trip cost.
3. В шапке файла (или над декларацией мультипликаторов) обновить комментарий: "Symmetric slippage: applied at both entry (cost up) and exit (proceeds down)."
4. Обновить шапку `backtest.ts` (`строки 10–14`):
   ```
   *   effectiveEntry = fillPrice * (1 + (feeBps + slippageBps) / 10_000)
   *   effectiveExit  = rawExit  * (1 - (feeBps + slippageBps) / 10_000)
   ```
5. **Важно:** старые `BacktestResult` записи становятся не сравнимы с новыми по абсолютному `pnlPct` при `slippageBps > 0`. Это допустимо — `engineVersion` уже фиксирует версию, существующие записи остаются интерпретируемыми по своему `engineVersion`. Документировать в PR-описании.

**Тест-план:**
- Существующие тесты с `slippageBps = 0` — зелёные без правок.
- Новый кейс: `slippageBps = 50, feeBps = 0`, простая стратегия с одним выигрышным trade (long). Проверить, что новый `pnlPct` меньше старого ровно на величину `2 * slippageBps / 10_000 * 100` процентов от номинала (с поправкой на маленькие расхождения из-за компаундинга по `entryMult`/`exitMult`).
- Кейс short: симметричное снижение pnlPct.
- Кейс с большим количеством сделок: новый `totalPnlPct` должен быть строго ≤ старого при `slippageBps > 0`.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- Новые тесты зелёные.
- Шапка `backtest.ts` и `dslEvaluator.ts` отражают симметричную формулу.

---

### 46-T3: Раздельные `takerFeeBps` / `makerFeeBps` с alias на `feeBps`

**Цель:** подготовить структуру под maker-режим (limit orders), не меняя текущее поведение. Все fills сейчас market → используется taker. Maker fee пишется в опции, но в формулах ещё не участвует — это явный задел.

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts` — `DslExecOpts` (`строка 78`), нормализация в начале `runDslBacktest` (`строка 828`).
- `apps/api/src/lib/backtest.ts` — `ExecOpts` (`строка 24`), проброс полей.
- `apps/api/tests/lib/backtest.test.ts` — тесты на нормализацию.

**Шаги реализации:**
1. В `DslExecOpts` добавить два опциональных поля:
   ```ts
   export interface DslExecOpts {
     feeBps?: number;          // alias for takerFeeBps (backward-compat)
     takerFeeBps?: number;
     makerFeeBps?: number;
     slippageBps: number;
     fillAt: DslFillAt;
   }
   ```
   `feeBps` становится optional (был required) — но это не ломает вызывающие, потому что в самой реализации всегда был fallback `feeBps = 0`.
2. Нормализация при чтении опций:
   ```ts
   const takerFeeBps = opts.takerFeeBps ?? opts.feeBps ?? 0;
   const makerFeeBps = opts.makerFeeBps ?? takerFeeBps; // default: maker = taker (consistent)
   const slippageBps = opts.slippageBps ?? 0;
   const fillAt      = opts.fillAt ?? "CLOSE";
   ```
3. В существующих формулах (`entryMult`, `exitMult`) использовать `takerFeeBps` — все текущие fills market. Поле `makerFeeBps` сохраняется в `opts`, но в расчётах не участвует. Это явно отметить комментарием: "makerFeeBps reserved for limit-order backtest (deferred); current evaluator uses takerFeeBps for all fills".
4. В `backtest.ts` `ExecOpts` отзеркалить:
   ```ts
   export interface ExecOpts {
     feeBps?: number;
     takerFeeBps?: number;
     makerFeeBps?: number;
     slippageBps: number;
     fillAt: FillAt;
   }
   ```
   Пробросить все поля в `runDslBacktest`.
5. Обновить шапку `backtest.ts` — упомянуть alias-поведение.
6. Тип `DslExecOpts.feeBps` помечен deprecated в JSDoc, но остаётся `optional`. Удалять его в этом этапе **не** надо — есть внешние вызывающие в routes/tests, миграция отдельной follow-up задачей.

**Тест-план:**
- `feeBps: 30` → `takerFeeBps = 30, makerFeeBps = 30` (внутренняя нормализация). Существующие тесты — зелёные.
- `takerFeeBps: 30` без `feeBps` → то же самое.
- Оба заданы (`feeBps: 10, takerFeeBps: 30`) → `takerFeeBps = 30` (новое поле приоритетнее).
- `takerFeeBps: 30, makerFeeBps: 10` → `makerFeeBps = 10`, но в формулах используется только `takerFeeBps`. Проверить через специально сконструированный кейс — `pnlPct` тот же, что при `takerFeeBps: 30` без maker.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие вызовы `runDslBacktest({feeBps, slippageBps})` работают без правок.
- Новые поля доступны для опционального использования.
- В JSDoc `feeBps` помечен deprecated с указанием на `takerFeeBps`.

---

### 46-T4: API + UI экспонирование новых полей

**Цель:** позволить пользователю выбрать `fillAt ∈ {OPEN, CLOSE, NEXT_OPEN}` и (опционально) задать `takerFeeBps`/`makerFeeBps` через Lab UI; пробросить значения в `runBacktest` во всех местах, где он сейчас вызывается с хардкодом `"CLOSE"`.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — `ALLOWED_FILL_AT` (`строка 30`), `StartBacktestBody` (`строка 49`), валидация (`строки 410–411`), вызовы `runBacktest` (`строки 564, 1339, 1349, 1485`).
- `apps/web/src/app/lab/ClassicMode.tsx` — типизация `fillAt` (`строка 80`), отправка POST (`строка 541`), снапшот (`строка 904`).
- `apps/web/src/app/lab/test/page.tsx` — `fillAt` (`строки 54, 1308`), снапшот (`строка 202`).
- `apps/api/tests/routes/lab.test.ts` — расширить валидационные тесты.

**Шаги реализации:**
1. Routes: `ALLOWED_FILL_AT = ["OPEN", "CLOSE", "NEXT_OPEN"] as const`. Тип `FillAt` обновится автоматически. Сообщение валидации `"fillAt must be one of: ${ALLOWED_FILL_AT.join(", ")}"` — без правок (формулировка корректна).
2. `StartBacktestBody` — добавить optional `takerFeeBps?: number` и `makerFeeBps?: number`. Сохранить `feeBps?: number` как backward-compat alias (та же стратегия, что в 46-T3). Серверная нормализация: если пришёл `feeBps` без `takerFeeBps` → `takerFeeBps = feeBps`. Записывать в `BacktestResult` поля `feeBps` (для обратной совместимости с существующей колонкой) и при наличии новых — записывать `takerFeeBps`/`makerFeeBps` в `reportJson`-блоке (additive, без миграции).
3. **Решение по схеме Prisma:** новые колонки `takerFeeBps`/`makerFeeBps` **не добавляются** в модель `BacktestResult` в этом этапе. Причина: текущая колонка `feeBps Int @default(0)` адекватна для taker-only режима, новые поля живут в `reportJson` до момента, когда maker-fees станут реально использоваться формулами (то есть до limit-order backtest, который вне scope этого документа). Это явное scope-discipline решение из `docs/44 §Scope discipline`. Документировать в PR-описании.
4. Заменить хардкоды:
   - `apps/api/src/routes/lab.ts:564` (preview) — оставить `fillAt: "CLOSE"` (preview = sanity-check, неизменно). Документировать.
   - `apps/api/src/routes/lab.ts:1339, 1349` (sweep) — пробрасывать `body.fillAt ?? "CLOSE"`.
   - `apps/api/src/routes/lab.ts:1485` (одиночный backtest fire-and-forget) — пробрасывать `body.fillAt ?? "CLOSE"`.
5. UI:
   - `ClassicMode.tsx:80` — тип `fillAt: "OPEN" | "CLOSE" | "NEXT_OPEN"`.
   - `ClassicMode.tsx:541` — заменить хардкод `fillAt: "CLOSE"` на значение из state (новый `<select>` рядом с fee/slippage инпутами); default state value = `"CLOSE"`.
   - `test/page.tsx:1308` — аналогично, добавить `<select>` в форму запуска backtest и пробрасывать значение.
   - Snapshot-таблица (`ClassicMode.tsx:904`, `test/page.tsx:202`) уже отображает `bt.fillAt` — без правок, она просто покажет новые значения.
   - `<select>` подписи: `"On candle close" / "On candle open" / "Next candle open"` для пользовательской ясности.
6. Не вводить отдельный UI для `takerFeeBps`/`makerFeeBps` в этом этапе — текущее единое поле "fee bps" продолжает мапиться в `feeBps` (server нормализует в `takerFeeBps`). UI для двух полей — отдельная задача после внедрения maker-режима.

**Тест-план:**
- e2e: POST с `fillAt: "OPEN"` — принимается, `BacktestResult.fillAt = "OPEN"`.
- e2e: POST с `fillAt: "NEXT_OPEN"` — принимается.
- e2e: POST с `fillAt: "INVALID"` — 400.
- e2e: POST без `fillAt` — default `"CLOSE"` (как сейчас).
- e2e: sweep с `fillAt: "OPEN"` — все runs внутри sweep используют это значение (проверить через `BacktestResult.fillAt` для одной из runs).
- Ручной smoke в Lab → Test:
  - Запуск с `"On candle close"` — pnlPct совпадает с pre-46-T1 значением (golden).
  - Запуск с `"Next candle open"` — pnlPct отличается, snapshot показывает `NEXT_OPEN`.
- preview-эндпоинт продолжает использовать `"CLOSE"` независимо от выбранного значения.

**Критерии готовности:**
- `tsc --noEmit` проходит и в api, и в web.
- Все существующие тесты зелёные.
- Новые e2e тесты зелёные.
- Lab UI golden-path работает в браузере для всех трёх значений `fillAt`.
- Хардкоды `"CLOSE"` в `lab.ts` остались только в preview (обоснованно).

---

### 46-T5: Тесты — golden fixtures и регрессии

**Цель:** убедиться, что нововведения 46-T1..T4 не задевают существующие зелёные тесты, добавить покрытие новых режимов и зафиксировать golden-значения для каждого `fillAt`.

**Файлы для изменения:**
- `apps/api/tests/lib/dslEvaluator.test.ts` — расширить (если задачи T1..T3 не покрыли все сценарии).
- `apps/api/tests/lib/backtest.test.ts` — golden-таблица.
- `apps/api/tests/routes/lab.test.ts` — e2e (если T4 не покрыл).
- (опционально) `apps/api/tests/lib/realism.test.ts` — новый файл, если хочется собрать realism-сценарии в одном месте.

**Шаги реализации:**
1. Зафиксировать golden-фикстуру: 50 свечей с явно заданными OHLC (предпочтительно ramp + sin для разнообразия), один простой DSL-стратегия (например, `crossover SMA(5) / SMA(20)`).
2. Прогнать backtest со всеми комбинациями: `fillAt ∈ {OPEN, CLOSE, NEXT_OPEN}` × `slippageBps ∈ {0, 50}` × `feeBps ∈ {0, 30}`. Получаем 12 запусков. Записать `(trades, totalPnlPct)` в табличный assert. Эти числа фиксируют контракт engine после 46-T1..T3 — изменение любого числа в будущем должно требовать явного обновления golden-таблицы и причины в PR.
3. Граничные кейсы:
   - Сигнал на последней свече при `"NEXT_OPEN"` → trade пропущен (assert `trades` на 1 меньше, чем при `"CLOSE"`).
   - `slippageBps = 0` → новые формулы 46-T2 идентичны старым (assert by golden из pre-46 версии).
   - `takerFeeBps ≠ feeBps` → используется `takerFeeBps` (assert через golden).
4. Не вводить тестов на funding, partial fills, maker fees в формулах — это out of scope.
5. Все тесты детерминированы: фикстуры зашиты, никаких `Date.now()`, никаких PRNG без seed.

**Тест-план:**
- 12-комбинационная golden table проходит зелёной.
- Граничные кейсы проходят.
- e2e блок `lab.test.ts` для `fillAt` (если есть из 46-T4) — зелёный.
- Suite `apps/api` целиком — зелёный.

**Критерии готовности:**
- `npm test` (apps/api) зелёный.
- Golden-таблица зафиксирована в коде с комментарием "do not edit without justification".
- Покрытие новых формул (entryMult/exitMult, fillAt branches) ≥ 90% по строкам (ориентир, не блокирующий).

---

## Порядок выполнения задач

```
46-T1 → 46-T2 → 46-T3 → 46-T4 → 46-T5
```

Каждая задача — отдельный PR.

- T1 первой: вводит fillAt в ядро, разблокирует docs/47-T3 и docs/48-T5.
- T2 после T1: симметричный slippage может затронуть новые fillAt-режимы, удобнее сначала закрепить fill, потом править slippage.
- T3 после T2: alias-нормализация полей независима, но логичнее ввести её, когда формулы уже стабильны.
- T4 после T1..T3: API/UI пробрасывают всё новое.
- T5 — последняя задача или встроена инкрементально.

## Зависимости от других документов

- **`docs/47`** (Strategy Optimizer) — после закрытия 46-T1 нужно вернуться в `docs/47-T3` (sweep) и заменить хардкод `fillAt: "CLOSE"` на проброс из `SweepRequestBody.fillAt`. Это уже учтено в комментарии 47-T3 как условная зависимость.
- **`docs/48`** (Walk-Forward) — после закрытия 46-T1 в `WalkForwardRequestBody` появляется `fillAt?: FillAt` (это уже описано в 48-T5 как условное расширение).
- **`docs/49`** (Backtest Metrics) — независим. 46 и 49 могут идти параллельно.
- **`docs/45`** (Indicator Engine Extraction) — независим.

## Backward compatibility checklist

- Все вызовы `runBacktest({feeBps, slippageBps})` без `fillAt` продолжают работать (default `"CLOSE"`).
- Все вызовы `runBacktest({feeBps, slippageBps, fillAt: "CLOSE"})` дают идентичный результат (бит-в-бит).
- При `slippageBps = 0` формула 46-T2 идентична старой → существующие тесты с дефолтным slippage не падают.
- Поле `feeBps` в `DslExecOpts`/`ExecOpts` остаётся доступным как alias для `takerFeeBps`.
- Prisma схема не меняется — `BacktestResult.feeBps Int`, `slippageBps Int`, `fillAt String @default("CLOSE")` уже совместимы (`apps/api/prisma/schema.prisma:598–602`).
- `engineVersion` уже фиксируется в каждом `BacktestResult` — старые записи интерпретируются по своему `engineVersion`, новые — по новому. Сравнимость абсолютных pnlPct между ними не гарантируется (это ожидаемо при `slippageBps > 0`).
- `reportVersion` не вводится (правило отложено в `docs/49`).
- preview-эндпоинт сохраняет `fillAt: "CLOSE"` — не ломает существующие preview-вызовы.

## Ожидаемый результат

После завершения всех задач:
- Backtest поддерживает три режима fill: `OPEN`, `CLOSE`, `NEXT_OPEN`.
- `NEXT_OPEN` устраняет lookahead-bias на close для indicator-based стратегий — становится рекомендованным режимом для серьёзного research-а.
- Slippage учитывается симметрично на entry и exit — round-trip cost отражает реальность.
- Структура полей готова к maker/taker разделению; формулы пока используют taker (market-only fills).
- Existing UI Lab → Test предлагает выбор `fillAt`; sweep и walk-forward (после 47/48) пробрасывают значение в каждый run.
- Funding и partial fills остаются в follow-up плане; явно зафиксировано в "Не входит в задачу".
