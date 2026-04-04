# Strategy DSL

Цель: определить формат стратегии, который можно:
1) хранить в БД/репозитории,
2) валидировать,
3) безопасно исполнять ботом (без произвольного кода).

В MVP используем JSON (или YAML, который конвертируется в JSON) + JSON Schema 2020-12.

> **DSL v2** (Stage 2) расширяет MVP-спецификацию: первоклассные динамические выходы,
> условный выбор стороны (long/short) внутри одной стратегии и политика миграции v1 → v2.
> Секции, помеченные `[v2]`, требуют `dslVersion >= 2`.

## 1) Принципы

MVP MUST:
- Стратегия — это декларативная конфигурация, без произвольных скриптов.
- Любая стратегия валидируется схемой до запуска.
- Стратегия исполняется одинаково в симуляции и в реальной торговле (demo), различается только источник исполнения.

## 2) Версионирование

MVP MUST:
- В стратегии есть `dslVersion` (семантическая/целочисленная версия).
- Бэкенд хранит и стратегию, и нормализованный конфиг (после дефолтов/миграций).

### 2.1 Версии DSL [v2]

| dslVersion | Описание | Статус |
|------------|----------|--------|
| 1 | MVP — фиксированный SL/TP, одна сторона, одна позиция | Stable |
| 2 | Динамические выходы, условная сторона (long/short), расширенный risk | Active |

**Правило определения версии:** если в JSON-объекте присутствует поле `exit` верхнего уровня **или**
`entry.sideCondition`, стратегия считается v2 (`dslVersion >= 2`). Валидатор отклоняет
`dslVersion: 1` при наличии v2-полей.

## 3) Модель стратегии (объект)

### 3.1 Общие поля

- `id` (string): внутренний идентификатор стратегии.
- `name` (string): отображаемое имя.
- `dslVersion` (int): версия DSL.
- `enabled` (bool): включена ли стратегия.
- `market` (object): рынок и символ.
- `timeframes` (array): таймфреймы, которые нужны стратегии.
- `entry` (object): правила входа.
- `risk` (object): риск-менеджмент.
- `execution` (object): правила исполнения (типы ордеров, проскальзывание, ретраи).
- `guards` (object): предохранители (лимиты, паузы, kill-switch).

### 3.2 Market

MVP:
- `exchange`: `"bybit"`
- `env`: `"demo"`
- `category`: `"linear"`
- `symbol`: например `"BTCUSDT"`

### 3.3 Entry / Exit

MVP поддерживаем 1 позицию на символ (одновременно):
- `side`: `"Buy"` или `"Sell"`
- `signal`: откуда берём сигнал (в MVP: webhook/ручной триггер/внутренний генератор).
- `order`: параметры входа (market/limit, qty/quoteQty, maxSlippageBps).

Выход (v1):
- SL/TP обязателен (фиксированный или по ATR, но формально — декларативно).
- В MVP базовый вариант: фиксированный SL/TP в процентах или цене.

### 3.4 Conditional side selection [v2]

В v2 поле `entry.side` может быть как фиксированным (`"Buy"` / `"Sell"`), так и **условным**.
Условный выбор стороны определяется объектом `entry.sideCondition`:

```json
{
  "entry": {
    "sideCondition": {
      "indicator": { "type": "EMA", "length": 200 },
      "source": "close",
      "long": { "op": "gt" },
      "short": { "op": "lt" }
    }
  }
}
```

**Семантика (mode = `"price_vs_indicator"`, default):**
- Если `close > EMA(200)` — бот открывает **long** (`"Buy"`).
- Если `close < EMA(200)` — бот открывает **short** (`"Sell"`).

**Семантика (mode = `"indicator_sign"`):**
- Если значение индикатора `> 0` — **long**.
- Если значение индикатора `< 0` — **short**.
- Если значение `= 0` — позиция не открывается.
- Полезно для дискретных сигналов (SMC patterns: +1/-1, MACD histogram и т.д.).

**Общие правила:**
- Если `entry.sideCondition` присутствует, `entry.side` НЕ указывается (это ошибка валидации).
- `sideCondition.indicator` — любой зарегистрированный в block registry индикатор.
- `sideCondition.source` — ценовой канал для сравнения (по умолчанию `"close"`, только для `price_vs_indicator` mode).
- `sideCondition.mode` — режим определения стороны (`"price_vs_indicator"` | `"indicator_sign"`, по умолчанию `"price_vs_indicator"`).
- `sideCondition.long.op` / `sideCondition.short.op` — оператор сравнения (`"gt"`, `"lt"`, `"gte"`, `"lte"`, только для `price_vs_indicator` mode).

**Правила:**
1. `entry.side` и `entry.sideCondition` — **взаимоисключающие**. Наличие обоих = ошибка валидации.
2. Одно из двух **обязательно** в стратегии.
3. `sideCondition` требует `dslVersion >= 2`.

### 3.5 Exit architecture [v2]

v2 вводит **top-level секцию `exit`**, которая заменяет встраивание SL/TP в `entry`.

```json
{
  "exit": {
    "stopLoss": {
      "type": "fixed_pct",
      "value": 2.0
    },
    "takeProfit": {
      "type": "fixed_pct",
      "value": 4.0
    },
    "trailingStop": {
      "type": "trailing_pct",
      "activationPct": 1.5,
      "callbackPct": 0.5
    },
    "indicatorExit": {
      "indicator": { "type": "RSI", "length": 14 },
      "condition": { "op": "gt", "value": 70 },
      "appliesTo": "long"
    },
    "timeExit": {
      "maxBarsInPosition": 50
    }
  }
}
```

#### Exit types

| Type | Field | Описание |
|------|-------|----------|
| Fixed SL | `exit.stopLoss` | Обязательный. `type`: `"fixed_pct"`, `"fixed_price"`, `"atr_multiple"` |
| Fixed TP | `exit.takeProfit` | Обязательный. Те же типы, что и SL |
| Trailing stop | `exit.trailingStop` | Опциональный. `type`: `"trailing_pct"`, `"trailing_atr"` |
| Indicator exit | `exit.indicatorExit` | Опциональный. Закрытие по индикатору |
| Time exit | `exit.timeExit` | Опциональный. Закрытие по количеству баров |

#### Stop-loss / Take-profit type variants

```
"fixed_pct"     — процент от цены входа
"fixed_price"   — абсолютная цена
"atr_multiple"  — множитель ATR(period) от цены входа
```

Для `atr_multiple`:
```json
{
  "type": "atr_multiple",
  "value": 2.0,
  "atrPeriod": 14
}
```

#### Trailing stop

```json
{
  "type": "trailing_pct",
  "activationPct": 1.5,
  "callbackPct": 0.5
}
```

- `activationPct` — профит (%) для активации трейлинг-стопа.
- `callbackPct` — откат (%) от максимума для срабатывания.
- Для `trailing_atr`: `activationAtr` и `callbackAtr` вместо процентов.

#### Indicator exit

```json
{
  "indicator": { "type": "RSI", "length": 14 },
  "condition": { "op": "gt", "value": 70 },
  "appliesTo": "long"
}
```

- `appliesTo`: `"long"`, `"short"`, `"both"` — к какой стороне применяется.
- Если `sideCondition` = обе стороны, `indicatorExit` может иметь разные правила для long/short.

#### Time exit

```json
{
  "maxBarsInPosition": 50
}
```

Закрывает позицию, если она открыта дольше N баров (на основном таймфрейме).

#### Приоритет выходов

Если несколько условий выхода срабатывают на одном баре:
1. **stopLoss** (высший приоритет — защита капитала)
2. **trailingStop**
3. **indicatorExit**
4. **takeProfit**
5. **timeExit** (низший приоритет)

#### Совместимость с v1

В v1-стратегиях `exit` верхнего уровня отсутствует; SL/TP находятся в `entry.stopLoss` / `entry.takeProfit`.
При миграции v1 → v2 эти поля переносятся в `exit` (см. секцию миграции).

## 4) Risk management

MVP MUST:
- `maxPositionSizeUsd` (number): верхний лимит позиции.
- `riskPerTradePct` (number): риск на сделку в % от депозита (или фикс в USD — один из вариантов).
- `cooldownSeconds` (int): пауза после стопа/тейка.

MVP SHOULD:
- `dailyLossLimitUsd` (number): дневной лимит убытка (kill-switch).

## 5) Execution

MVP MUST:
- `orderType`: `"Market"` или `"Limit"`
- `reduceOnly` для закрывающих ордеров (если применимо в реализации).
- `clientOrderIdPrefix` (string) для формирования `orderLinkId` и трассировки.

## 6) Guards

MVP MUST:
- `maxOpenPositions` = 1 (на символ).
- `maxOrdersPerMinute` (int): защита от спама.
- `pauseOnError` (bool): при повторяющихся ошибках — ставим стратегию на паузу.

## 6.1) v1 → v2 Migration policy [v2]

### Принципы миграции

1. **v1-стратегии остаются валидными.** Валидатор и рантайм продолжают принимать `dslVersion: 1`.
2. **Автоматическая миграция при редактировании.** Если пользователь открывает v1-стратегию в Lab v2 editor, система предлагает миграцию. Миграция создаёт **новую версию** (`StrategyVersion`), не мутирует существующую.
3. **Миграция необратима на уровне версии.** `dslVersion: 2` нельзя понизить до 1. Предыдущая v1-версия остаётся в истории.

### Алгоритм миграции v1 → v2

```
function migrateV1toV2(v1: DslV1): DslV2 {
  return {
    ...v1,
    dslVersion: 2,
    exit: {
      stopLoss: v1.entry.stopLoss,       // перенос из entry
      takeProfit: v1.entry.takeProfit,    // перенос из entry
    },
    entry: {
      ...v1.entry,
      // удаляем stopLoss/takeProfit из entry
      stopLoss: undefined,
      takeProfit: undefined,
    },
  };
}
```

### Что происходит с полями

| v1 поле | v2 поле | Действие |
|---------|---------|----------|
| `entry.stopLoss` | `exit.stopLoss` | Перенос |
| `entry.takeProfit` | `exit.takeProfit` | Перенос |
| `entry.side` | `entry.side` или `entry.sideCondition` | Сохранение (side condition — опционально, добавляется пользователем) |
| `dslVersion: 1` | `dslVersion: 2` | Обновление |
| Все остальные поля | Без изменений | — |

### Ограничения

- Миграция НЕ создаёт `trailingStop`, `indicatorExit`, `timeExit` — это opt-in от пользователя.
- Миграция НЕ переключает `entry.side` на `sideCondition` — это явное действие.
- API-эндпоинт: `POST /api/strategies/:id/migrate` — возвращает preview diff, применяется после подтверждения.

---

## 7) JSON Schema (черновик, MVP)

Файл схемы будем держать рядом в `docs/schema/strategy.schema.json`.
Диалект: JSON Schema 2020-12 (через `$schema`). [web:653][web:657]

---

## 8) Визуальный граф как authoring-слой (Lab v2)

> **Это декларация архитектурного принципа**, а не описание текущей реализации.
> Детали компиляции и block-to-DSL mapping будут специфицированы в Phase 4.

### Принцип

Визуальный редактор (`StrategyGraph`) является **authoring-интерфейсом** поверх этого DSL.
Он **не является** отдельным рантаймом стратегий.

Цепочка:
```
StrategyGraph (visual) → Compiler (Phase 4) → StrategyVersion.body (DSL JSON) → Bot runtime
```

Рантайм ботов работает исключительно с `StrategyVersion.body` в формате этого DSL.
Он не знает о `StrategyGraph`, `LabGraphNode`, или React Flow.

### Что это означает на практике

- Граф должен всегда быть компилируемым в валидный DSL-объект.
- Если граф не может быть скомпилирован — его нельзя запустить как бота.
- Любое добавление нового блока в граф требует соответствующего правила в компиляторе.
- Граф не добавляет новых runtime-возможностей, не описанных в DSL.

### Статус компилятора

- Phase 1–2: компилятор отсутствует; граф существует только как UI-черновик.
- Phase 3: граф сохраняется и валидируется клиентски; компилятор ещё не готов.
- Phase 4: компилятор реализуется; блок-to-DSL mapping table фиксируется в этом документе перед кодированием.
- Phase 6: (опционально) DSL-редактор и граф становятся взаимозаменяемыми представлениями.

> **Правило:** Compiler mapping table (block type → DSL field/rule) **должна быть задокументирована
> в этом файле** до начала кодирования компилятора в Phase 4. Не допускать скрытых маппингов только в коде.

---

## 9) Block-to-DSL mapping table (Phase 4 compiler)

> **Статус: ЗАФИКСИРОВАН** — заполнен перед началом кодирования компилятора в Phase 4.

### 9.1 Принципы маппинга

- Compiler traverses the graph in topological order.
- Each block type has exactly one rule below that determines how it maps to a DSL field or section.
- Blocks without a mapping rule produce a compile-time validation error.
- Hidden graph structure (e.g. intermediate Series nodes) is not emitted into the DSL — only terminal decisions are emitted.

### 9.2 Mapping table

| Block type    | Category  | DSL target                                      | Notes                                                                                  |
|---------------|-----------|-------------------------------------------------|----------------------------------------------------------------------------------------|
| `candles`     | input     | `market` (implicit source)                      | Confirms market data source is present. Symbol/timeframe come from compile request.   |
| `SMA`         | indicator | `entry.indicators[]` → `{ type:"SMA", length }` | `params.length` → `length`. Connected to candles via input port.                      |
| `EMA`         | indicator | `entry.indicators[]` → `{ type:"EMA", length }` | `params.length` → `length`. Connected to candles via input port.                      |
| `RSI`         | indicator | `entry.indicators[]` → `{ type:"RSI", length }` | `params.length` → `length`. Connected to candles via input port.                      |
| `compare`     | logic     | `entry.signal.conditions[]` → `{ op, left, right }` | `params.op` → `op`. Inputs `a`, `b` identify connected indicator refs.           |
| `cross`       | logic     | `entry.signal` → `{ type: params.mode, fast, slow }` | `params.mode` → signal type: `"crossover"`, `"crossunder"`, or `"both"`. Inputs `a`, `b` identify fast/slow indicator refs. |
| `enter_long`  | execution | `entry.side: "Buy"`                             | Exactly one entry node required. Conflict with `enter_short` = compile error.         |
| `enter_short` | execution | `entry.side: "Sell"`                            | Exactly one entry node required. Conflict with `enter_long` = compile error.          |
| `stop_loss`   | risk      | v1: `entry.stopLoss`; **v2: `exit.stopLoss`** + `risk.riskPerTradePct` | `params.type` → SL type; `params.value` → SL value. v2: supports `atr_multiple`. |
| `take_profit` | risk      | v1: `entry.takeProfit`; **v2: `exit.takeProfit`** | `params.type` → TP type; `params.value` → TP value. v2: supports `atr_multiple`. |
| `trailing_stop` [v2] | risk | `exit.trailingStop` | `params.activationPct` → activation; `params.callbackPct` → callback. Requires `dslVersion >= 2`. |
| `indicator_exit` [v2] | risk | `exit.indicatorExit` | `params.indicator` → indicator config; `params.condition` → exit condition; `params.appliesTo` → side filter. |
| `time_exit` [v2] | risk | `exit.timeExit` | `params.maxBarsInPosition` → bar limit. |
| `side_condition` [v2] | logic | `entry.sideCondition` | `params.indicator` → regime indicator; `params.longOp`/`params.shortOp` → comparison operators. Replaces `enter_long`/`enter_short`. |

### 9.3 Fixed DSL defaults (compiler-injected, not from graph blocks)

These fields are required by `strategy.schema.json` but have no corresponding graph block.
They are injected by the compiler with safe defaults:

| DSL field                       | Injected value | Reason                                              |
|---------------------------------|----------------|-----------------------------------------------------|
| `dslVersion`                    | `1` or `2`     | Determined by presence of v2 blocks in graph        |
| `enabled`                       | `true`         | Compiled strategies are enabled by default          |
| `market.exchange`               | `"bybit"`      | MVP only supports Bybit                             |
| `market.env`                    | `"demo"`       | Compiled strategies run in demo env until explicitly promoted |
| `market.category`               | `"linear"`     | MVP only supports linear (USDT-perp) contracts      |
| `risk.maxPositionSizeUsd`       | `100`          | Conservative default; user adjusts via bot config  |
| `risk.cooldownSeconds`          | `60`           | 1-minute cooldown after stop/take                  |
| `execution.orderType`           | `"Market"`     | Market orders for MVP                              |
| `execution.clientOrderIdPrefix` | `"lab_"`       | All lab-compiled strategies use this prefix        |
| `execution.maxSlippageBps`      | `50`           | 0.5% max slippage                                  |
| `guards.maxOpenPositions`       | `1`            | MVP: single position per symbol (DSL const)        |
| `guards.maxOrdersPerMinute`     | `10`           | Safety guard                                       |
| `guards.pauseOnError`           | `true`         | Pause strategy on repeated errors                  |

### 9.4 Compile-time validation rules (server-side, Phase 4)

In addition to client-side validation (Phase 3C), the compiler enforces:

1. **Candles block required**: at least one `candles` block must be present and connected to the indicator chain.
2. **Entry block required**: exactly one `enter_long` or `enter_short` must be present (v1), **or** one `side_condition` block (v2).
3. **Risk block required**: at least one `stop_loss` and at least one `take_profit` block required.
4. **Entry connected**: the `enter_long`/`enter_short` (or `side_condition`) signal input must be reachable from a `cross` or `compare` node.
5. **Risk connected**: `enter_long`/`enter_short` risk input must be reachable from a `stop_loss` or `take_profit` node.
6. **No cycles**: graph must be a DAG (redundant with Phase 3C but re-enforced server-side).
7. **Conflicting entries**: cannot have both `enter_long` and `enter_short` in the same graph (v1 constraint). In v2, `side_condition` replaces both.
8. **[v2] Exit section required**: if `dslVersion >= 2`, `exit.stopLoss` and `exit.takeProfit` must be present as top-level exit section.
9. **[v2] Side exclusivity**: `entry.side` and `entry.sideCondition` are mutually exclusive. Presence of both = compile error.
10. **[v2] Version consistency**: v2-only blocks (`trailing_stop`, `indicator_exit`, `time_exit`, `side_condition`) require `dslVersion >= 2`.

### 9.5 Compile output structure

```json
{
  "strategyVersionId": "<uuid>",
  "compiledDsl": { /* full StrategyVersion.body DSL */ },
  "validationIssues": [
    { "severity": "error", "message": "...", "nodeId": "<optional node id>" }
  ]
}
```

`validationIssues` is empty on success. On schema or graph errors, `strategyVersionId` is omitted and `compiledDsl` is omitted.

