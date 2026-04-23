# 45. Indicator Engine Extraction Plan

Статус: draft  
Владелец: core trading  
Последнее обновление: 2026-04-23  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: B (архитектурный refactoring, параллельная)

## Контекст

Текущее состояние (проверено по коду):

- `apps/api/src/lib/indicators/index.ts` экспортирует: `calcATR`, `trueRange`, `calcVWAP`, `calcADX`, `calcSuperTrend`, `calcMACD` и соответствующие типы.
- Внутри `dslEvaluator.ts` находятся **приватные** функции `calcSMA` (строка 244), `calcEMA` (строка 260), `calcRSI` (строка 279), `calcBollingerBands` (строка 311), а также вспомогательные `getBollingerBands` и `getVolumeProfileCached`.
- SMC primitives (`fair_value_gap`, `liquidity_sweep`, `order_block`, `market_structure_shift`) вызываются из `dslEvaluator.ts` через `runtime/patternEngine.ts` — они уже вынесены в отдельный модуль, но не экспортируются через публичный `indicators/index.ts`.
- `dslEvaluator.ts` содержит 1207 строк; уменьшение его размера улучшит тестируемость и переиспользование.

## Цель

- Вынести `calcSMA`, `calcEMA`, `calcRSI`, `calcBollingerBands` в `apps/api/src/lib/indicators/`.
- Добавить их в публичный экспорт через `indicators/index.ts`.
- Заменить приватные вызовы в `dslEvaluator.ts` на импорты из `indicators/`.
- Принять явное решение по SMC primitives (критерий см. в задаче 45-T4).

## Решение по SMC primitives

SMC primitives (`fvgSeries`, `sweepSeries`, `orderBlockSeries`, `mssSeries`) уже вынесены в `lib/runtime/patternEngine.ts` и вызываются из `dslEvaluator.ts`. Публичного потребителя вне evaluator/runtime сейчас нет.

Правило из `docs/44`:
> Если в рамках этапа появляется более одного нового публичного потребителя SMC-логики вне `dslEvaluator.ts` / runtime-слоя, вынос выполняется в этом этапе; иначе — вторая волна.

На старте задачи 45-T4 исполнитель проверяет наличие новых потребителей и фиксирует решение в PR-описании.

## Не входит в задачу

- Изменение логики вычислений в любом из индикаторов.
- Рефакторинг `getIndicatorValues`, `IndicatorCache` или `createIndicatorCache` — только замена приватных функций на импорты.
- Изменения `DslBacktestReport`, `DslTradeRecord` или `exitReason`.
- Изменения backtest execution logic.
- Изменения MTF-слоя.
- Изменения exchange layer или worker.

---

## Задачи

### 45-T1: Вынести `calcSMA` и `calcEMA` в `indicators/sma.ts` и `indicators/ema.ts`

**Цель:** создать два новых файла-индикатора и экспортировать их публично.

**Файлы для изменения:**
- Создать `apps/api/src/lib/indicators/sma.ts`
- Создать `apps/api/src/lib/indicators/ema.ts`
- Изменить `apps/api/src/lib/indicators/index.ts` — добавить экспорт `calcSMA`, `calcEMA`
- Изменить `apps/api/src/lib/dslEvaluator.ts` — удалить приватные `calcSMA`, `calcEMA`, добавить импорты

**Шаги реализации:**
1. Создать `sma.ts` с функцией `calcSMA(candles: Candle[], length: number): (number | null)[]`. Сигнатура и логика — точная копия из `dslEvaluator.ts` строка 244. Импортировать `Candle` из `./types.js`.
2. Создать `ema.ts` с функцией `calcEMA(candles: Candle[], length: number): (number | null)[]`. Сигнатура и логика — точная копия из `dslEvaluator.ts` строка 260.
3. Добавить в `indicators/index.ts`: `export { calcSMA } from "./sma.js"` и `export { calcEMA } from "./ema.js"`.
4. В `dslEvaluator.ts`: удалить приватные объявления `calcSMA` и `calcEMA`, добавить импорты `import { calcSMA } from "./indicators/sma.js"` и `import { calcEMA } from "./indicators/ema.js"`.
5. Убедиться, что TypeScript-компиляция проходит без ошибок.

**Тест-план:**
- Существующие тесты на `dslEvaluator` должны пройти без изменений — логика не меняется.
- Добавить unit-тест для `calcSMA`: массив из N свечей, проверить значение на последней позиции и null для warm-up.
- Добавить unit-тест для `calcEMA`: проверить seed (первое значение = SMA), проверить сходимость.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- `calcSMA` и `calcEMA` доступны через `import { calcSMA, calcEMA } from "../indicators/index.js"`.
- Приватные объявления удалены из `dslEvaluator.ts`.

---

### 45-T2: Вынести `calcRSI` в `indicators/rsi.ts`

**Цель:** создать файл `rsi.ts` и экспортировать `calcRSI` публично.

**Файлы для изменения:**
- Создать `apps/api/src/lib/indicators/rsi.ts`
- Изменить `apps/api/src/lib/indicators/index.ts` — добавить экспорт `calcRSI`
- Изменить `apps/api/src/lib/dslEvaluator.ts` — удалить приватную `calcRSI`, добавить импорт

**Шаги реализации:**
1. Создать `rsi.ts` с функцией `calcRSI(candles: Candle[], length: number): (number | null)[]`. Логика — точная копия из `dslEvaluator.ts` строка 279.
2. Добавить в `indicators/index.ts`: `export { calcRSI } from "./rsi.js"`.
3. В `dslEvaluator.ts`: удалить приватное объявление `calcRSI`, добавить `import { calcRSI } from "./indicators/rsi.js"`.

**Тест-план:**
- Существующие тесты зелёные.
- Unit-тест: массив свечей с известными ценами, проверить значение RSI на `length`-й позиции, null для warm-up.
- Граничный случай: все свечи растут — RSI должен быть близок к 100; avgLoss = 0 → RSI = 100.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- `calcRSI` доступна через `indicators/index.ts`.
- Приватное объявление удалено из `dslEvaluator.ts`.

---

### 45-T3: Вынести `calcBollingerBands` в `indicators/bollingerBands.ts`

**Цель:** создать `bollingerBands.ts`, экспортировать `calcBollingerBands` и тип `BollingerBandsResult` публично.

**Файлы для изменения:**
- Создать `apps/api/src/lib/indicators/bollingerBands.ts`
- Изменить `apps/api/src/lib/indicators/index.ts` — добавить экспорт `calcBollingerBands` и `BollingerBandsResult`
- Изменить `apps/api/src/lib/dslEvaluator.ts` — удалить приватные `calcBollingerBands`, `getBollingerBands`, переместить `BollingerBandsResult` в новый файл, добавить импорты

**Шаги реализации:**
1. Создать `bollingerBands.ts`:
   - Перенести `export interface BollingerBandsResult` из `dslEvaluator.ts`.
   - Перенести `calcBollingerBands(candles, period, stdDevMult)` — логика без изменений.
   - Перенести `getBollingerBands(params, candles, cache)` как внутреннюю вспомогательную функцию (не экспортировать публично — она использует `IndicatorCache`, который остаётся в `dslEvaluator.ts`; альтернатива: оставить `getBollingerBands` в `dslEvaluator.ts` и импортировать только `calcBollingerBands`).
2. Рекомендованный вариант: экспортировать только `calcBollingerBands` и `BollingerBandsResult`; `getBollingerBands` остаётся в `dslEvaluator.ts` как приватная обёртка над `calcBollingerBands`.
3. Добавить в `indicators/index.ts`: `export { calcBollingerBands } from "./bollingerBands.js"` и `export type { BollingerBandsResult } from "./bollingerBands.js"`.
4. В `dslEvaluator.ts`: удалить объявление `BollingerBandsResult` и `calcBollingerBands`, добавить импорты из `./indicators/bollingerBands.js`.

**Тест-план:**
- Существующие тесты зелёные.
- Unit-тест: массив свечей, проверить что `middle[i]` совпадает с SMA, `upper[i] > middle[i]`, `lower[i] < middle[i]`.
- Граничный случай: все цены одинаковы — stdDev = 0, upper = lower = middle.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- `BollingerBandsResult` и `calcBollingerBands` доступны через `indicators/index.ts`.
- Объявления удалены из `dslEvaluator.ts`.

---

### 45-T4: Решение по SMC primitives + обновление `indicators/index.ts`

**Цель:** зафиксировать и исполнить решение по SMC primitives, финализировать публичный API индикаторов.

**Файлы для изменения (минимальный вариант — только обновление index.ts):**
- `apps/api/src/lib/indicators/index.ts`

**Файлы для изменения (если SMC выносится в этом этапе):**
- `apps/api/src/lib/indicators/index.ts`
- `apps/api/src/lib/runtime/patternEngine.ts` (проверить, нужен ли реэкспорт)

**Шаги реализации:**
1. Проверить наличие новых публичных потребителей SMC-логики вне `dslEvaluator.ts` / `runtime/patternEngine.ts`.
2. Если потребителей > 1 → добавить реэкспорт SMC-функций через `indicators/index.ts`:
   ```ts
   export { fvgSeries, sweepSeries, orderBlockSeries, mssSeries } from "../runtime/patternEngine.js";
   ```
3. Если потребителей ≤ 1 → добавить комментарий в `indicators/index.ts` о статусе SMC: "SMC primitives remain in runtime/patternEngine.ts — extraction deferred to next refactoring wave."
4. Проверить, что все четыре базовых индикатора (SMA, EMA, RSI, Bollinger) корректно экспортируются через `indicators/index.ts`.
5. Обновить doc-комментарий в начале `indicators/index.ts` — актуализировать список экспортируемых индикаторов.

**Тест-план:**
- Smoke-тест: `import { calcSMA, calcEMA, calcRSI, calcBollingerBands, calcATR, calcVWAP, calcADX, calcSuperTrend, calcMACD } from "./indicators/index.js"` — все функции резолвятся без ошибок.
- Если SMC вынесен: добавить аналогичный smoke-тест для SMC-функций.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие тесты зелёные.
- `indicators/index.ts` содержит полный список базовых индикаторов.
- Решение по SMC зафиксировано в PR-описании.
- `dslEvaluator.ts` стал короче минимум на 80 строк (удалены 4 приватные функции).

---

## Порядок выполнения задач

```
45-T1 → 45-T2 → 45-T3 → 45-T4
```

Каждая задача — отдельный PR. Последовательность обязательна: T2 и T3 зависят от установленного паттерна из T1.

## Ожидаемый результат

После завершения всех задач:
- `dslEvaluator.ts` не содержит приватных вычислительных функций индикаторов.
- Все базовые индикаторы (SMA, EMA, RSI, Bollinger, ATR, VWAP, ADX, SuperTrend, MACD) доступны через единый публичный `indicators/index.ts`.
- Решение по SMC зафиксировано явно.
- Тесты покрывают все новые файлы индикаторов.
