# 46. Backtest Realism Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-23  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (основной путь, шаг 1)

## Контекст

Текущее состояние (проверено по коду):

- `apps/api/src/lib/backtest.ts:11` и `backtest.ts:27` фиксируют `fillAt: "CLOSE"` как единственный поддерживаемый вариант.
- `apps/api/src/routes/lab.ts:30` — `ALLOWED_FILL_AT = ["CLOSE"] as const` — валидация запроса допускает только это значение.
- `apps/api/prisma/schema.prisma:601` — поле `fillAt String @default("CLOSE")` у `BacktestRun` уже является текстовым и не ограничено на уровне БД.
- Entry-исполнение в `dslEvaluator.ts:1134`: `effectiveEntry = c.close * entryMult`, где `c = candles[i]` — тот же бар, на котором срабатывает сигнал. Сигнал и фактический fill используют `candles[i].close` одновременно.
- `entryMult = 1 + (feeBps + slippageBps) / 10_000` (`dslEvaluator.ts:893`), `exitMult = 1 - feeBps / 10_000` (строка 894) — комиссия и slippage применяются мультипликативно.
- SL/TP exits проверяются intrabar против `c.low`/`c.high` (строки 1012, 1018, 1077, 1082); fill идёт на уровне `slPrice`/`tpPrice`. Приоритет intrabar-выходов фиксирован: SL → trailing → indicator → TP → time (порядок в `dslEvaluator.ts:1009–1099`).
- End-of-data выход использует `last.close` (строка 1190).
- Индикаторы `calcSMA`/`calcEMA`/`calcRSI`/`calcBollingerBands` читают `candles[j]` только при `j ≤ i` — forward-peek отсутствует. Явной проверки этого инварианта в тестах нет.

Основные ограничения текущей модели:

1. **Same-bar-close fill**. Сигнал вычисляется на закрытии бара `i` и исполняется по цене закрытия того же бара `i`. В реальном исполнении order placement после наблюдения close(i) попадает в бар `i+1`.
2. **Отсутствие альтернативного режима исполнения** — модель одна, assumptions не переключаемы.
3. **Отсутствие автоматической проверки отсутствия lookahead** в индикаторах.

## Цель

- Ввести второй режим исполнения `NEXT_BAR_OPEN` (fill по `candles[i+1].open` при сигнале на баре `i`).
- Сохранить `CLOSE` как режим по умолчанию для обратной совместимости.
- Документировать execution assumptions явно (комментарий в `backtest.ts` + README блок).
- Добавить guard-тест, гарантирующий отсутствие forward-peek в базовых индикаторах.

## Решение по scope режимов

В этой задаче добавляется только один новый режим — `NEXT_BAR_OPEN`. Другие варианты (`NEXT_BAR_CLOSE`, VWAP-fill, market impact model) выносятся во вторую волну и не рассматриваются здесь.

Обоснование: `NEXT_BAR_OPEN` — стандартный anti-lookahead режим, поддерживаемый большинством open-source бэктестеров; он даёт максимальный выигрыш в реализме при минимальной сложности реализации.

## Совместимость отчёта

Изменения этой задачи **не требуют** `reportVersion`:

- форма `DslBacktestReport` и `DslTradeRecord` не меняется;
- `entryPrice`/`exitPrice` остаются `number`;
- enum `exitReason` не расширяется;
- меняются только численные значения полей для стратегий, запущенных в режиме `NEXT_BAR_OPEN`.

Потребители отчёта (UI `ClassicMode.tsx:80`, `test/page.tsx:54`) получают `fillAt: string` и уже отображают его как snapshot-значение — добавление нового значения не ломает их.

## Не входит в задачу

- Partial fills, order book simulation.
- Slippage model, зависящий от объёма или волатильности (остаётся фиксированный `slippageBps`).
- Изменение приоритета intrabar-выходов (SL → trailing → indicator → TP → time остаётся как есть).
- Изменение `CLOSE`-поведения.
- Режимы `NEXT_BAR_CLOSE`, VWAP-fill, mid-price — вторая волна.
- Изменения exchange execution layer, worker orchestration.
- Изменения UI Lab beyond добавления fillAt-селектора (минимальная интеграция).
- Изменения Prisma-схемы (поле `fillAt` уже существует как `String`).

---

## Задачи

### 46-T1: Расширить тип `FillAt` и `ExecOpts`

**Цель:** подготовить типовую основу для нового режима, не меняя runtime-поведение.

**Файлы для изменения:**
- `apps/api/src/lib/backtest.ts`
- `apps/api/src/lib/dslEvaluator.ts`
- `apps/api/src/routes/lab.ts`

**Шаги реализации:**
1. В `backtest.ts`: расширить `ExecOpts.fillAt` с литерала `"CLOSE"` до union `"CLOSE" | "NEXT_BAR_OPEN"`.
2. В `dslEvaluator.ts`: добавить поле `fillAt?: "CLOSE" | "NEXT_BAR_OPEN"` в `DslExecOpts`, default `"CLOSE"`. Runtime-ветвление пока не реализуем — только типы.
3. В `lab.ts`: обновить `ALLOWED_FILL_AT = ["CLOSE", "NEXT_BAR_OPEN"] as const`.
4. Обновить JSDoc в `backtest.ts:11` — перечислить оба режима.

**Тест-план:**
- Существующие тесты `dslEvaluator.test.ts` должны пройти без изменений (поведение не меняется).
- Добавить тест валидации запроса `/lab/backtest`: отправка `fillAt: "NEXT_BAR_OPEN"` проходит валидацию; отправка `fillAt: "INVALID"` возвращает 400.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- API принимает оба значения `fillAt`, но runtime всё ещё исполняет `CLOSE`-модель (NEXT_BAR_OPEN прокидывается, но игнорируется).

---

### 46-T2: Реализовать `NEXT_BAR_OPEN` execution

**Цель:** добавить ветку в `runDslBacktest`, где entry fill происходит на открытии следующего бара.

**Файлы для изменения:**
- `apps/api/src/lib/dslEvaluator.ts`

**Шаги реализации:**
1. В `runDslBacktest` прокинуть `fillAt` из `opts` в локальную переменную (default `"CLOSE"`).
2. В entry-блоке (`dslEvaluator.ts:1103–1178`):
   - При `fillAt === "CLOSE"` — сохранить текущее поведение: `effectiveEntry = c.close * entryMult`.
   - При `fillAt === "NEXT_BAR_OPEN"` — если `i + 1 >= candles.length`, сигнал игнорируется (нет бара для fill). Иначе: `entryBarIndex = i + 1`, `entryTime = candles[i+1].openTime`, `effectiveEntry = candles[i+1].open * entryMult`.
3. Exit-логика (SL/TP/trailing/indicator/time/end_of_data) остаётся без изменений — она работает от `entryBarIndex` и не зависит от режима входа.
4. В `end_of_data`-ветке (`dslEvaluator.ts:1181–1191`): логика остаётся прежней; для `NEXT_BAR_OPEN` позиция, открытая на последнем баре, просто не открывается (см. пункт 2).

**Тест-план:**
- Golden-тест `CLOSE`-режима: существующие фикстуры должны давать идентичный отчёт (bit-exact).
- Новый тест `NEXT_BAR_OPEN`:
  - Фикстура на 10 свечей, сигнал срабатывает на баре 3.
  - Режим `CLOSE`: `entryPrice` = `candles[3].close * entryMult`.
  - Режим `NEXT_BAR_OPEN`: `entryPrice` = `candles[4].open * entryMult`, `entryTime` = `candles[4].openTime`.
- Граничный случай: сигнал срабатывает на последнем баре. В режиме `NEXT_BAR_OPEN` сделка не открывается (`trades === 0`).
- DCA-сценарий: базовый ордер открывается по `candles[i+1].open`, safety orders продолжают триггериться по `c.low`/`c.high` на последующих барах.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные (проверка отсутствия регрессии `CLOSE`).
- Два новых теста на `NEXT_BAR_OPEN` зелёные.
- Детерминизм: два прогона с одинаковыми входами дают bit-exact одинаковые отчёты.

---

### 46-T3: Guard-тест на отсутствие forward-peek в индикаторах

**Цель:** зафиксировать инвариант «индикатор на баре `i` использует только `candles[0..i]`» в виде автоматического теста.

**Файлы для изменения:**
- Создать `apps/api/tests/indicators/lookaheadGuard.test.ts`

**Шаги реализации:**
1. Для каждого экспортируемого индикатора (`calcSMA`, `calcEMA`, `calcRSI`, `calcBollingerBands`, `calcATR`, `calcVWAP`, `calcADX`, `calcSuperTrend`, `calcMACD`):
   - Сгенерировать фикстуру на N свечей.
   - Вычислить индикатор на полном массиве.
   - Для каждого `i` в диапазоне `[0, N)`: вычислить индикатор на срезе `candles.slice(0, i+1)` и сверить, что значение на позиции `i` совпадает с full-run.
2. Тест не меняет production-код, только добавляет регрессионный guard.

**Зависимость от docs/45:** тест можно писать **сразу после 45-T1..T3**, когда SMA/EMA/RSI/Bollinger уже экспортируются через `indicators/index.ts`. Если 45 ещё не завершён, тест временно импортирует приватные функции через test-only re-export или ограничивается уже публичными (`calcATR`, `calcVWAP`, `calcADX`, `calcSuperTrend`, `calcMACD`).

**Тест-план:**
- Тест зелёный для всех перечисленных индикаторов.
- Моделирующий антитест (исключён из CI, закомментирован): искусственно сломанная функция `calcSMAWithPeek`, читающая `candles[i+1]`, должна падать — подтверждение что guard действительно ловит forward-peek.

**Критерии готовности:**
- Тест зелёный в CI.
- Покрыты все 9 экспортируемых индикаторов (или подмножество, актуальное на момент выполнения, с явным TODO-списком недостающих).

---

### 46-T4: Wire up `fillAt` в UI Lab (минимальная интеграция)

**Цель:** дать пользователю возможность выбрать `fillAt` в Lab UI; по умолчанию — `CLOSE`.

**Файлы для изменения:**
- `apps/web/src/app/lab/ClassicMode.tsx`
- `apps/web/src/app/lab/test/page.tsx`

**Шаги реализации:**
1. В `ClassicMode.tsx:541` заменить хардкод `fillAt: "CLOSE"` на значение из локального state; добавить простой `<select>` с двумя опциями.
2. В `test/page.tsx:1308` — аналогично.
3. Snapshot-строка `<SnapshotRow label="Fill at" value={bt.fillAt} />` уже отображает значение из отчёта — менять не нужно.
4. Верстка селектора — минимальная (одна строка рядом с fees/slippage inputs), без нового дизайна.

**Тест-план:**
- Ручная проверка: в Lab UI переключить `fillAt` на `NEXT_BAR_OPEN`, запустить backtest, убедиться что `bt.fillAt` в snapshot показывает выбранное значение.
- E2E-тест на Lab (если есть в проекте) расширяется одним кейсом: запуск с `fillAt: "NEXT_BAR_OPEN"` возвращает валидный отчёт.

**Критерии готовности:**
- UI позволяет выбрать `fillAt` из двух значений.
- Default остаётся `CLOSE` для существующих флоу.
- Snapshot корректно отображает выбранный режим.

---

## Порядок выполнения задач

```
46-T1 → 46-T2 → 46-T3 (параллельно с T2) → 46-T4
```

- **46-T1** — базовая типовая развязка, минимальный риск.
- **46-T2** — ядро изменения, должно следовать после T1.
- **46-T3** — независимый тест, может быть написан параллельно с T2 (не блокирует и не блокируется).
- **46-T4** — UI-слой, последний.

Каждая задача — отдельный PR.

## Зависимости от других документов

- **docs/45** (Indicator engine extraction) — желательно, но не обязательно завершён до 46-T3. Если 45 не завершён, T3 покрывает только индикаторы, уже доступные через публичный API.
- **docs/49** (Backtest metrics expansion) — НЕ зависит от 46. Метрики считаются поверх `tradeLog`, форма которого не меняется.
- **docs/48** (Walk-forward) — строится поверх 46. Walk-forward split должен работать с любым `fillAt`.
- **docs/47** (Strategy optimizer) — косвенно зависит от 46: optimizer должен принимать `fillAt` как часть execution-config и передавать в каждый прогон.

## Ожидаемый результат

После завершения всех задач:
- Backtest поддерживает два режима исполнения: `CLOSE` и `NEXT_BAR_OPEN`.
- Lookahead в индикаторах защищён автоматическим тестом.
- API, UI и отчёт консистентно передают выбранный `fillAt`.
- `DslBacktestReport` не меняет форму — `reportVersion` не требуется.
- Документированы execution assumptions для обоих режимов.
