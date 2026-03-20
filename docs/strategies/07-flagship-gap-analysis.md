# Gap Analysis: Flagship Strategies vs. Current Implementation

> Дата: 2026-03-20
> Автор: Code Review (Expert Programmer)
> Цель: определить все необходимые изменения для реализации настроек, тестов и торговли по 5 флагманским стратегиям

---

## Краткое резюме

Платформа имеет солидную MVP-основу: граф-компилятор, DSL-валидатор, бот-рантайм, бэктест-движок. Однако **текущая реализация покрывает ~20% требований** для полноценной торговли по флагманским стратегиям. Ниже — систематический gap-анализ по 8 ключевым направлениям.

---

## 1. DSL-блоки: текущее vs. требуемое

### Реализовано (blockDefs.ts + graphCompiler.ts)

| Блок | Категория | Статус |
|------|-----------|--------|
| Candles | input | OK |
| Constant | input | OK |
| SMA | indicator | OK |
| EMA | indicator | OK |
| RSI | indicator | OK |
| MACD | indicator | OK (frontend only, compiler не обрабатывает) |
| Bollinger Bands | indicator | OK (frontend only, compiler не обрабатывает) |
| ATR | indicator | OK (frontend only, compiler не обрабатывает) |
| Volume | indicator | OK (frontend only, compiler не обрабатывает) |
| Compare | logic | OK |
| Cross | logic | OK |
| AND / OR | logic | OK (frontend only, compiler не обрабатывает) |
| Enter Long / Short | execution | OK |
| Stop Loss / Take Profit | risk | OK |

### Критический gap: compiler обрабатывает только SMA, EMA, RSI

`graphCompiler.ts:193` — `const indicatorTypes = ["SMA", "EMA", "RSI"]` — это жёсткий whitelist. MACD, Bollinger, ATR, Volume блоки определены во фронтенде, но **компилятор их игнорирует** — они не попадают в DSL.

### Нужно добавить (по приоритету)

| Приоритет | Блок | Нужен для стратегий | Тип работы |
|-----------|------|---------------------|------------|
| **P0** | `VWAP` | MTF Scalper, SMC | Новый индикатор + расчёт |
| **P0** | `SuperTrend` | Adaptive Regime | Новый индикатор (ATR + Factor) |
| **P0** | `ADX` | Adaptive Regime | Новый индикатор |
| **P1** | `VolumeProfile` | MTF Scalper | Сложный индикатор (POC, VAH, VAL) |
| **P1** | `FundingRate` | Funding Arb | Новый datasource (Bybit API) |
| **P1** | `DCA` | DCA Bot | Новый execution model (safety orders) |
| **P1** | `SessionFilter` | SMC | Логический фильтр по времени |
| **P1** | `ProximityFilter` | MTF Scalper | Логический фильтр близости к уровню |
| **P1** | `ATR` (compiler) | Все кроме DCA | Уже есть во frontend, нужен в compiler |
| **P2** | `LiquiditySweep` | SMC | Сложный детектор паттернов |
| **P2** | `FairValueGap` | SMC | Детектор FVG между 3 свечами |
| **P2** | `OrderBlock` | SMC | Детектор OB |
| **P2** | `MarketStructureShift` | SMC | Детектор BOS/CHoCH |
| **P2** | `MultiTimeframe` | SMC, Adaptive, MTF Scalper | Архитектурное расширение |
| **P2** | `RegimeSwitcher` | Adaptive Regime | Условное переключение подстратегий |
| **P2** | `MultiDeal` | DCA Bot | Управление несколькими сделками |
| **P2** | `DeltaNeutral` | Funding Arb | Spot+Perp execution |
| **P2** | `BasisMonitor` | Funding Arb | Мониторинг спреда |
| **P2** | `FundingRateScanner` | Funding Arb | Сканер по всем символам |

---

## 2. Graph Compiler: критические доработки

### 2.1 Расширение indicatorTypes whitelist
**Файл:** `apps/api/src/lib/graphCompiler.ts:193`

Текущий код:
```ts
const indicatorTypes = ["SMA", "EMA", "RSI"];
```

Нужно: поддержка всех индикаторов из blockDefs + новых. Необходим рефакторинг в registry-паттерн, чтобы добавление нового индикатора не требовало правки compiler core.

### 2.2 DSL Version 2
Все концептуальные JSON в стратегиях используют `dslVersion: 2`. Текущий compiler жёстко ставит `DSL_VERSION = 1`. Нужна миграция DSL-схемы на v2 с обратной совместимостью.

### 2.3 Multi-timeframe support
Текущий compiler принимает один `timeframe`, стратегии требуют `timeframes: ["1m", "5m", "15m"]`. Нужно:
- Изменить сигнатуру `compileGraph()` для массива таймфреймов
- Добавить MultiTimeframe блок, который запрашивает данные с другого TF
- Расширить entry.indicators для указания timeframe per indicator

### 2.4 Новые типы сигнальной логики
Текущий compiler понимает только `cross` и `compare`. Стратегии требуют:
- `regime_adaptive` (Adaptive Regime Bot) — условный переключатель
- `confluence` (MTF Scalper) — requireAll: true, AND-логика нескольких условий
- `liquidity_sweep_fvg_entry` (SMC) — составной паттерн
- `dca_start` (DCA Bot) — стартовый сигнал с DCA-логикой

### 2.5 Расширенные типы Stop Loss / Take Profit
Текущий SL/TP: `fixed` и `atr-multiple` / `r-multiple`. Стратегии требуют:
- `sweep_wick` — SL за вик свечи-свипа (SMC)
- `opposite_liquidity` — TP до противоположной ликвидности (SMC)
- `supertrend_flip_or_bb_midline` — динамический TP (Adaptive)
- `structural` — SL/TP по структурному уровню (MTF Scalper)
- `atr_multiple` — TP по N×ATR (MTF Scalper)

---

## 3. DSL Schema: обновления

**Файл:** `apps/api/src/lib/dslValidator.ts`

### 3.1 Entry section — слишком свободная
```ts
entry: { type: "object", additionalProperties: true }
```
Нет валидации структуры `entry`. Для production нужна строгая валидация indicators, signal, stopLoss, takeProfit внутри entry.

### 3.2 Отсутствующие секции DSL
- `dca` — секция DCA-параметров (baseOrderPct, safetyOrders, stepPct, etc.)
- `timeframes` — массив таймфреймов (есть в schema, но не валидируется строго)
- `market.category` — захардкожено `const: "linear"`, Funding Arb требует `spot`

### 3.3 Guards — maxOpenPositions
`maxOpenPositions: { type: "integer", const: 1 }` — жёстко 1. DCA Bot требует 3-5, MultiDeal нужен >1.

---

## 4. Backtest Engine: фундаментальные ограничения

**Файл:** `apps/api/src/lib/backtest.ts`

### Текущее состояние
Движок реализует **одну единственную стратегию**: price-breakout с lookback 20 и фиксированным 2:1 R/R. Это **не DSL-driven** бэктест — он полностью игнорирует DSL стратегии.

### Требуется
1. **DSL-driven backtest engine** — исполнение DSL-логики на исторических данных
2. **Расчёт индикаторов** — библиотека: SMA, EMA, RSI, MACD, BB, ATR, VWAP, SuperTrend, ADX, VolumeProfile
3. **Signal evaluation** — вычисление сигналов по DSL entry.signal
4. **DCA execution model** — safety orders, TP пересчёт по средней цене
5. **Multi-timeframe data** — загрузка и alignment данных с разных TF
6. **Short positions** — текущий движок только Long (breakout)
7. **Sharpe Ratio, Profit Factor** — отсутствуют в BacktestReport, нужны для оценки стратегий
8. **Equity curve** — для визуализации drawdown и роста капитала

### Приоритет: КРИТИЧЕСКИЙ
Без DSL-driven бэктеста **невозможно тестировать ни одну флагманскую стратегию**. Это блокер №1.

---

## 5. Bot Runtime: доработки для торговли

**Файл:** `apps/api/src/lib/botWorker.ts`

### 5.1 Отсутствует signal engine в runtime
Bot worker управляет lifecycle (QUEUED → RUNNING → STOPPED), но **не генерирует торговые сигналы**. Intent-ы создаются извне — нет автоматической генерации из DSL.

Нужно:
- Встроить DSL interpreter в botWorker polling loop
- На каждом тике: получить свежие свечи → рассчитать индикаторы → проверить сигнал → создать BotIntent

### 5.2 DCA execution model
Текущий BotIntent поддерживает ENTRY, EXIT, SL, TP, CANCEL. Для DCA нужно:
- Тип `SAFETY_ORDER` в IntentType
- Логика размещения серии safety orders при отклонении цены
- Автопересчёт TP при каждом новом safety order
- Трекинг средней цены позиции

### 5.3 Funding Rate datasource
Для Funding Arb нужен отдельный data pipeline:
- Periodic fetch: `GET /v5/market/tickers` → funding rate
- Historical funding: `GET /v5/market/funding/history`
- Scanner: фильтрация символов по порогу ставки

### 5.4 Spot API интеграция
Текущая интеграция — только `linear` (USDT perpetual). Funding Arb требует:
- Bybit Spot API для покупки актива
- Одновременное управление spot + perp позициями
- Delta-neutral балансировка

### 5.5 Session Filtering
SMC и MTF Scalper работают в Kill Zones. Нужен:
- Фильтр по UTC-часам в bot runtime
- Блокировка ENTRY intent-ов вне Kill Zone

---

## 6. Data Model: необходимые изменения

**Файл:** `apps/api/prisma/schema.prisma`

### 6.1 Timeframe enum
```prisma
enum Timeframe { M1, M5, M15, H1 }
```
Отсутствуют: `M30`, `H4`, `D1` — нужны для multi-timeframe стратегий (HTF context 4H для SMC, D1 для DCA).

### 6.2 IntentType — расширение
Добавить: `SAFETY_ORDER`, `HEDGE_OPEN`, `HEDGE_CLOSE` — для DCA и Funding Arb.

### 6.3 Position tracking
Отсутствует модель Position — трекинг открытых позиций, средней цены, нереализованного PnL. Сейчас position state неявно в intent-ах.

Необходимо:
```prisma
model Position {
  id          String @id @default(uuid())
  botRunId    String
  symbol      String
  side        OrderSide
  avgEntryPrice Decimal
  qty         Decimal
  unrealizedPnl Decimal?
  status      PositionStatus // OPEN, CLOSED
  openedAt    DateTime
  closedAt    DateTime?
}
```

### 6.4 FundingRate data model
```prisma
model FundingRateSnapshot {
  id         String   @id @default(uuid())
  exchange   String
  symbol     String
  rate       Decimal
  nextFundingTime DateTime
  fetchedAt  DateTime @default(now())
  @@unique([exchange, symbol, fetchedAt])
}
```

### 6.5 Strategy template / preset system
Для 5 флагманских стратегий нужна система «пресетов» — готовых конфигураций, которые пользователь может запустить одной кнопкой:
```prisma
model StrategyPreset {
  id          String @id @default(uuid())
  slug        String @unique  // "smc-liquidity-sweep"
  name        String
  description String
  dslJson     Json
  category    String  // "flagship"
  difficulty  String  // "beginner", "advanced", "professional"
  createdAt   DateTime @default(now())
}
```

---

## 7. Testing Infrastructure: полностью отсутствует

В проекте **нет ни одного теста**. Для production-ready торговых стратегий это неприемлемо.

### 7.1 Unit тесты (критический приоритет)

| Что тестировать | Файл | Описание |
|-----------------|------|----------|
| Индикаторы | `lib/indicators/*.test.ts` | SMA, EMA, RSI, MACD, BB, ATR, VWAP, SuperTrend, ADX на known-good data |
| DSL Validator | `lib/dslValidator.test.ts` | Валидные/невалидные DSL JSON, edge cases |
| Graph Compiler | `lib/graphCompiler.test.ts` | Минимальные графы → DSL, ошибки, warnings |
| Backtest Engine | `lib/backtest.test.ts` | Детерминированные тесты: known candles → known trades |
| State Machine | `lib/stateMachine.test.ts` | Все допустимые и запрещённые transitions |
| Signal Evaluator | `lib/signalEvaluator.test.ts` | Cross, compare, confluence, regime |

### 7.2 Integration тесты

| Что тестировать | Описание |
|-----------------|----------|
| Strategy CRUD | Create → Version → Validate → List → Archive |
| Bot lifecycle | Create → Queue → Start → Running → Stop |
| Compile-to-Backtest | Graph → Compile → Create backtest → Run → Report |
| DCA flow | Base Order → Safety Orders → TP recalculate → Close |
| Bybit mock | Mocked exchange responses для intent execution |

### 7.3 Strategy-specific тесты

Для каждой из 5 стратегий нужен golden-test:
1. Известный набор свечей (fixture)
2. DSL JSON стратегии
3. Ожидаемый результат бэктеста (trades, winrate, PnL)

Это гарантирует, что изменения в коде не ломают торговую логику.

### 7.4 Инфраструктура
- Vitest (совместим с TypeScript, ESM, Fastify)
- Тестовая БД (Docker, Prisma migrate)
- CI pipeline (GitHub Actions)

---

## 8. Frontend: настройки стратегий

### 8.1 Strategy Settings Panel
Для каждой стратегии нужна UI-страница настроек с:
- Параметры по умолчанию из документации
- Валидация в реальном времени
- Пресеты (Conservative / Default / Aggressive для DCA)
- Подсказки из документации

### 8.2 Block Palette — новые блоки
`blockDefs.ts` нужно расширить на все новые блоки с правильными портами и параметрами.

### 8.3 Strategy Presets Gallery
Галерея 5 флагманских стратегий с:
- Карточками: метрики, описание, аудитория
- One-click deploy → создаёт Strategy + Bot с пресетными параметрами
- Индикатор готовности: какие блоки реализованы, какие нет

---

## Roadmap реализации (рекомендуемый порядок)

### Phase 1: Foundation (блокер для всего остального)
1. **Testing infrastructure** — Vitest setup, первые unit tests для существующего кода
2. **Indicator library** — отдельный модуль `lib/indicators/` с расчётами SMA, EMA, RSI, MACD, BB, ATR + unit tests
3. **Compiler refactor** — registry-паттерн вместо hardcoded indicatorTypes, поддержка BB, MACD, ATR, Volume
4. **DSL v2 schema** — расширение schema для новых секций

### Phase 2: P0 индикаторы + DSL-driven backtest
5. **VWAP** — индикатор + блок + compiler + test
6. **SuperTrend** — индикатор + блок + compiler + test
7. **ADX** — индикатор + блок + compiler + test
8. **DSL-driven backtest engine** — исполнение DSL на исторических данных вместо hardcoded breakout

### Phase 3: Первая торгуемая стратегия (Adaptive Regime Bot)
9. **RegimeSwitcher** logic block
10. **Signal evaluator** в bot runtime
11. **Position tracking** (data model + logic)
12. **Adaptive Regime Bot preset** — полный end-to-end: DSL → Compile → Backtest → Bot → Trade (demo)

### Phase 4: P1 блоки + DCA Bot
13. **DCA execution model** — safety orders, TP recalculate
14. **DCA block** + compiler support
15. **MultiDeal** — maxOpenPositions > 1
16. **DCA Momentum Bot preset**

### Phase 5: MTF Scalper
17. **VolumeProfile** индикатор
18. **ProximityFilter** logic block
19. **MultiTimeframe** architecture
20. **SessionFilter** (Kill Zones)
21. **MTF Confluence Scalper preset**

### Phase 6: Funding Arb + SMC
22. **FundingRate datasource** + Bybit API
23. **Spot API integration**
24. **DeltaNeutral** execution
25. **SMC P2 blocks** (LiquiditySweep, FVG, OrderBlock, MSS)

---

## Оценка трудоёмкости

| Phase | Описание | Оценка |
|-------|----------|--------|
| 1 | Foundation (tests, indicators, compiler) | Большой объём, высокий приоритет |
| 2 | P0 индикаторы + DSL backtest | Большой объём, критический путь |
| 3 | Adaptive Regime Bot (первый торгуемый) | Средний объём |
| 4 | DCA Bot | Средний объём (DCA — новый execution model) |
| 5 | MTF Scalper | Большой объём (MTF архитектура) |
| 6 | Funding Arb + SMC | Очень большой объём (Spot API, delta-neutral, P2 блоки) |

---

## Критические блокеры (что мешает начать торговать)

1. **Backtest engine не использует DSL** — невозможно тестировать стратегии
2. **Compiler не знает половину блоков** — BB, MACD, ATR, Volume существуют только в UI
3. **Bot runtime не генерирует сигналы** — нет signal engine, бот не может торговать автономно
4. **Нет тестов** — невозможно безопасно рефакторить и добавлять новые блоки
5. **Нет Position tracking** — нет трекинга средней цены, нереализованного PnL

Эти 5 пунктов — абсолютный минимум, без которого ни одна флагманская стратегия не может быть запущена.
