# UI/UX (MVP v1 → Lab v2 evolution)

Документ описывает структуру интерфейса, основные страницы, user flows и компонентную модель.
Разделён на две части: MVP v1 (текущая реализация) и Lab v2 (спланированная поэтапная эволюция).

> **Canonical Lab v2 spec:** `docs/23-lab-v2-ide-spec.md`. Данный раздел — краткое отражение для согласованности, не дублирует детали.

## 1) Общие принципы

- Mobile-last: MVP оптимизирован под десктоп (1280px+), адаптив — post-MVP.
- Язык: RU + EN (i18n через next-intl).
- Тема: тёмная по умолчанию (trading convention), light — post-MVP.
- Design tokens отделены от бизнес-логики (для будущего редизайна).

## 2) Структура страниц (роуты)

| Route | Название | Назначение |
|---|---|---|
| `/terminal` | Terminal | Ручная торговля: график, ордера, позиции |
| `/lab` | Research Lab | Strategy DSL редактор, backtest, AI-чат |
| `/factory` | Bot Factory | Список ботов, создание, запуск, логи |
| `/settings` | Settings | Exchange connections, профиль |
| `/login` | Login | Аутентификация |

## 3) Terminal (ручная торговля)

### Layout
- **Левая панель**: список инструментов (search + filter по `linear`).
- **Центр**: свечной график (lightweight-charts), переключение таймфреймов (1m/5m/15m/1h).
- **Правая панель**: форма ордера (Market/Limit), поля SL/TP (обязательны).
- **Нижняя панель**: таблицы открытых ордеров, позиций, истории.

### User flow: ручная сделка
1. Выбрать инструмент из списка.
2. Увидеть график + текущую цену.
3. Заполнить форму ордера (side, type, qty, price, SL, TP).
4. Нажать «Place Order».
5. Увидеть ордер в таблице открытых ордеров.
6. Увидеть обновление статуса (accepted → filled / rejected).

### Компоненты
- `InstrumentList` — список инструментов с поиском
- `CandleChart` — свечной график
- `OrderForm` — форма создания ордера
- `OrdersTable` — открытые ордера
- `PositionsTable` — текущие позиции
- `TradeHistory` — история сделок

## 4) Research Lab

> **Status:** This section covers two overlapping generations of the Lab UI.
> Lab v2 is implemented incrementally via phases (see `docs/23-lab-v2-ide-spec.md`).
> Classic mode (MVP v1) remains mandatory until Phase 4 of Lab v2 is accepted.

---

### 4A) Classic mode (MVP v1 — current implementation, must be preserved)

**Layout:**
- **Left panel**: strategy list (CRUD).
- **Center**: Strategy DSL editor (JSON) + real-time schema validation.
- **Right panel**: AI chat (strategy generation and editing).
- **Bottom panel**: backtest results (when triggered).

**User flow: creating a strategy via AI:**
1. Open Lab, click "New Strategy".
2. Describe the idea in AI chat (plain text).
3. AI generates a Strategy Spec (JSON) + explanation.
4. User sees JSON in editor, can hand-edit.
5. Click "Validate" — schema check runs.
6. Click "Save" — strategy is persisted.

**User flow: backtest (MVP minimum):**
1. Select a saved strategy.
2. Click "Run Backtest" (historical replay over candles).
3. See report: trades, winrate, PnL, max drawdown.

**Classic mode components:**
- `StrategyList` — strategy list with CRUD actions
- `DslEditor` — JSON editor with syntax highlighting and live validation
- `AiChat` — chat panel (input + history + strategy output)
- `BacktestReport` — backtest results (table + metrics)

> **Non-negotiable:** `DslEditor`, `AiChat`, and `BacktestReport` MUST NOT be removed
> until Lab v2 Phase 4 is formally accepted. Both modes coexist as tabs.

---

### 4B) Lab v2 shell (phased evolution — details in `docs/23-lab-v2-ide-spec.md`)

Lab v2 transforms `/lab` into a multi-mode IDE shell. The layout evolves across phases.

**Target shell layout (Phase 1):**

```
┌─────────────────────────────────────────────────────────────────┐
│  Context bar: [ExchangeConnection ▾] [Dataset ▾]  [Build ▾]    │
├────────────┬────────────────────────────────────┬───────────────┤
│  Left      │  Center (mode-dependent view)       │  Right        │
│  panel     │                                      │  Inspector    │
│  (Data /   │  [Data] dataset list + preview       │  panel        │
│   palette  │  [Build] React Flow strategy canvas  │               │
│   or       │  [Test]  backtest run + results      │               │
│   dataset  │  [Classic] DSL editor + AI chat      │               │
│   list)    │                                      │               │
├────────────┴────────────────────────────────────┴───────────────┤
│  Bottom drawer: node output preview / validation issues / logs   │
└─────────────────────────────────────────────────────────────────┘
```

**Top context bar (Phase 1):**
- Exchange connection selector (read from user's saved connections).
- Dataset selector (binds active `MarketDataset` to the workspace).
- Mode tabs: `[Data]` / `[Build]` / `[Test]` / `[Classic]`.
- `Classic` tab is always visible until Phase 4 acceptance.

**Data mode (Phase 2):**
- Left: list of `MarketDataset` definitions for the workspace.
- Center: dataset definition form (symbol, timeframe, date range) + data quality indicator.
- Right: Inspector with dataset metadata (row count, last fetched, hash).
- Bottom: row count / data preview (virtualized table or OHLCV chart).

**Build mode (Phase 3):**
- Left: searchable/categorized block palette.
- Center: React Flow strategy canvas (see §6.3.1 of Lab v2 spec for connection UX).
- Right: Inspector for selected node (parameters, port info, validation errors).
- Bottom: diagnostics drawer (validation issues, stale nodes, execution log).

**Test mode (Phase 5):**
- Center: backtest run trigger + reproducible result viewer.
- Right: run metadata (dataset hash, strategy version, engine version).
- Bottom: equity curve, trade list, performance metrics.

**Inspector panel (mandatory from Phase 3):**
- Shows context for the selected graph object (node or edge).
- For nodes: type, parameters, port status (connected / unconnected / error), validation errors.
- For edges: source port, target port, data type, stale/invalid state.
- For no selection: workspace summary (node count, validation status).

**Diagnostics drawer (Phase 3):**
- Persistent bottom panel listing graph-level issues.
- Issue types: required-port-missing, type-mismatch (if edge was saved), stale-node, risk-block-absent.
- Each issue is actionable (click → focus affected node/edge on canvas).

**Lab v2 components (new, phased):**
- `LabShell` — top-level route layout with context bar + mode tabs
- `ContextBar` — connection + dataset selector + mode switcher
- `DatasetPanel` — dataset list and definition form (Phase 2)
- `StrategyCanvas` — React Flow canvas wrapper (Phase 3)
- `BlockPalette` — categorized, searchable block list (Phase 3)
- `LabInspector` — context-sensitive right panel (Phase 3)
- `DiagnosticsDrawer` — validation issues + logs (Phase 3)
- `BacktestRunner` — reproducible run trigger + result viewer (Phase 5)

## 5) Bot Factory

### Layout
- **Список ботов**: карточки/таблица со статусом (draft/ready/running/stopped/error).
- **Детали бота**: конфиг, стратегия, risk params, event log.
- **Управление**: Start (duration) / Stop / Delete.

### User flow: запуск бота
1. Создать бота: выбрать стратегию, задать risk-параметры.
2. Увидеть превью: symbol, strategy, SL/TP, risk limits.
3. Нажать «Start» с указанием duration (минуты).
4. Бот переходит в `running`, UI показывает live-лог событий.
5. По timeout или по кнопке «Stop» — бот останавливается.
6. Просмотр журнала событий (BotEvents).

### Компоненты
- `BotList` — список ботов с фильтром по статусу
- `BotCard` — карточка бота (summary)
- `BotDetail` — полная информация + управление
- `EventLog` — реалтайм лог событий бота
- `RiskBadge` — индикатор текущей риск-политики (strict/pause-only)

## 6) Settings

- `ExchangeConnectionForm` — добавить/проверить demo API ключ
- `ConnectionStatus` — статус подключения (OK/Error + last check)
- Секрет не отображается после сохранения (только masked)

## 7) Общие компоненты

- `AppLayout` — shell с навигацией (Terminal / Lab / Factory / Settings)
- `Navbar` — top bar с текущим разделом и user info
- `ErrorBoundary` — обработка ошибок рендера
- `ProblemToast` — отображение Problem Details ошибок от API
- `ConfirmDialog` — подтверждение опасных действий (Stop All, Delete)
