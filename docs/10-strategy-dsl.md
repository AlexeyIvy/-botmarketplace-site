# Strategy DSL (MVP)

Цель: определить формат стратегии, который можно:
1) хранить в БД/репозитории,
2) валидировать,
3) безопасно исполнять ботом (без произвольного кода).

В MVP используем JSON (или YAML, который конвертируется в JSON) + JSON Schema 2020-12.

## 1) Принципы

MVP MUST:
- Стратегия — это декларативная конфигурация, без произвольных скриптов.
- Любая стратегия валидируется схемой до запуска.
- Стратегия исполняется одинаково в симуляции и в реальной торговле (demo), различается только источник исполнения.

## 2) Версионирование

MVP MUST:
- В стратегии есть `dslVersion` (семантическая/целочисленная версия).
- Бэкенд хранит и стратегию, и нормализованный конфиг (после дефолтов/миграций).

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

Выход:
- SL/TP обязателен (фиксированный или по ATR, но формально — декларативно).
- В MVP базовый вариант: фиксированный SL/TP в процентах или цене.

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
| `stop_loss`   | risk      | `entry.stopLoss` + `risk.riskPerTradePct`       | `params.type` → `entry.stopLoss.type`; `params.value` → `entry.stopLoss.value` and `risk.riskPerTradePct`. |
| `take_profit` | risk      | `entry.takeProfit`                              | `params.type` → `entry.takeProfit.type`; `params.value` → `entry.takeProfit.value`.  |

### 9.3 Fixed DSL defaults (compiler-injected, not from graph blocks)

These fields are required by `strategy.schema.json` but have no corresponding graph block.
They are injected by the compiler with safe defaults:

| DSL field                       | Injected value | Reason                                              |
|---------------------------------|----------------|-----------------------------------------------------|
| `dslVersion`                    | `1`            | MVP DSL version                                     |
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
2. **Entry block required**: exactly one `enter_long` or `enter_short` must be present.
3. **Risk block required**: at least one `stop_loss` and at least one `take_profit` block required.
4. **Entry connected**: the `enter_long`/`enter_short` signal input must be reachable from a `cross` or `compare` node.
5. **Risk connected**: `enter_long`/`enter_short` risk input must be reachable from a `stop_loss` or `take_profit` node.
6. **No cycles**: graph must be a DAG (redundant with Phase 3C but re-enforced server-side).
7. **Conflicting entries**: cannot have both `enter_long` and `enter_short` in the same graph (Phase 4 MVP constraint).

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

