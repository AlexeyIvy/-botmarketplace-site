# Архитектура (MVP)

Документ описывает компоненты системы, потоки данных, границы доверия и ключевые архитектурные решения.
Цель: MVP должен быть простым, но безопасным и расширяемым до multi-user и real торговли.

## 1) Компоненты

### 1.1 Frontend (Web UI)
- Terminal: выбор инструмента, свечи, ручная торговля, таблицы ордеров/позиций.
- Bots: список/создание/запуск, просмотр логов BotRun.
- AI Chat: чат-интерфейс и редактор Strategy Spec.

Frontend НЕ имеет доступа к Bybit API secret и не может напрямую вызывать Bybit.

### 1.2 Backend API (App Server)
- Auth/session.
- CRUD: Bots, BotRuns, ExchangeConnection.
- Market data proxy/cache:
  - instruments list cache,
  - tickers proxy/cache,
  - свечи (источник фиксируется в интеграции).
- Risk/Execution service:
  - валидация Strategy Spec,
  - проверка лимитов,
  - формирование торговых запросов к Bybit,
  - идемпотентность intents/reqId.
- Audit logging + event store (BotEvent).

### 1.3 Bot Runtime Worker (Executor)
- Получает BotRun на исполнение.
- Загружает Bot+Strategy Spec+Risk config.
- Подписывается на market data (WS/REST).
- Генерирует intents (сигналы) и передаёт их в Execution/Risk слой.
- Получает обновления статусов ордеров/позиций и ведёт state machine.
- Пишет события BotEvent.

Worker НЕ принимает решения об авторизации пользователя и НЕ хранит секреты в логах.

### 1.4 Storage
- DB (PostgreSQL или аналог): Users, ExchangeConnection, Bots, BotRuns, BotEvents, InstrumentCache.
- (Опционально) Redis/Queue: очередь задач на BotRun, rate-limit counters, кэш market data.

## 2) Границы доверия (Trust boundaries)

- Internet ↔ Frontend: потенциально враждебная среда.
- Frontend ↔ Backend: только через авторизованный API, все входы валидируются.
- Backend ↔ Worker: внутренний канал (queue/RPC), но всё равно валидировать payload.
- Backend/Worker ↔ Bybit: внешний сервис; доверять нельзя, нужен retry/backoff, валидация ответов.

Секреты (Bybit API secret) живут только в backend/storage в зашифрованном виде и используются только в момент подписи запросов к Bybit.

## 3) Потоки данных (Data flows)

### 3.1 Market data (публичные данные)
1) Backend периодически обновляет instruments-info в InstrumentCache.
2) Frontend запрашивает список инструментов из backend (кэш).
3) Frontend получает tickers/цены (backend proxy или WS через backend — решение зависит от реализации).
4) Для свечей:
   - вариант A: backend отдаёт свечи по REST,
   - вариант B: frontend строит свечи из stream trade (потребует больше логики в UI),
   - MVP: предпочтительно A (проще в контроле и кэшировании).

### 3.2 Private data (баланс/позиции/ордера)
1) Пользователь сохраняет demo API key/secret в Settings.
2) Backend проверяет ключ и сохраняет секрет зашифрованно.
3) Backend/Worker периодически/по запросу запрашивает позиции/ордера и отдаёт frontend в безопасном виде.

### 3.3 Trading (ручная торговля)
1) Frontend отправляет request “создать ордер” (без секретов).
2) Backend валидирует параметры (symbol, qty, price, tick/step).
3) Backend подписывает запрос и отправляет в Bybit `Place Order`.
4) Backend возвращает ack (принято), но финальный статус подтверждается через WS/опрос и отражается в UI.
(Важный принцип: ack != filled.)

### 3.4 Bot run (автоторговля)
1) Frontend создаёт BotRun (Start на N минут).
2) Backend кладёт задачу в очередь/worker.
3) Worker начинает цикл:
   - читает market data,
   - вычисляет сигналы,
   - создаёт intents,
   - Execution/Risk проверяет лимиты,
   - отправляет запросы в Bybit,
   - обновляет state machine,
   - пишет BotEvent.
4) По Stop/Timeout — worker останавливается, финализирует отчёт BotRun.

## 4) WebSocket стратегия (reconnect + reconciliation)

Bybit рекомендует отправлять `ping` каждые 20 секунд для поддержания соединения.

MVP MUST:
- ping heartbeat каждые 20 секунд;
- reconnect с backoff;
- после reconnect выполнить reconciliation:
  - получить актуальные ордера/позиции через REST,
  - сравнить с локальным состоянием,
  - исправить расхождения (например, отметить ордер filled/canceled).

## 5) Идемпотентность и повторные запросы

MVP MUST:
- Любой “intent” имеет уникальный `intentId`.
- Execution слой хранит mapping `intentId -> reqId -> bybitOrderId`.
- При retry/повторе intent не создаёт новый ордер (если прошлый уже создан).

## 6) Масштабирование (post-MVP)

- Multi-user:
  - добавляем Workspace и лимиты,
  - изоляция ключей/данных.
- Multi-bot:
  - очередь BotRuns,
  - ограничение concurrency,
  - per-user quotas.
- Real trading:
  - feature flag,
  - дополнительные подтверждения,
  - расширенный аудит и risk-лимиты.

---

## 7) Research Lab v2 — архитектурная интеграция

> **Canonical spec:** `docs/23-lab-v2-ide-spec.md`. Данный раздел описывает место Lab в общей архитектуре системы — только то, что влияет на смежные компоненты.

### 7.1 Место Lab в общей архитектуре

Lab v2 (`/lab`) — это frontend IDE-шелл поверх существующих backend-сервисов.
Он не является отдельным сервисом. Он не создаёт параллельного data layer.

```
┌────────────────────────────────────────────────────────────────────┐
│  Browser — /lab (Lab Shell, Phase 1+)                              │
│                                                                     │
│  ┌─────────┐  ┌─────────────────┐  ┌────────────────────────────┐ │
│  │  Data   │  │  Build           │  │  Test / Classic             │ │
│  │  mode   │  │  mode            │  │  mode                       │ │
│  │(Stage19 │  │(React Flow       │  │(BacktestRunner /            │ │
│  │ dataset │  │ canvas,          │  │ DslEditor + AiChat)         │ │
│  │ UI)     │  │ Phase 3)         │  │                             │ │
│  └────┬────┘  └────────┬─────────┘  └───────────────────────────┘ │
│       │                 │                                           │
│    useLabGraphStore (Zustand) — session state, localStorage Phase 1 │
└───────┼─────────────────┼────────────────────────────────────────── ┘
        │                 │
        ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│  Backend API (/api/v1/)                                           │
│                                                                   │
│  Stage 19 dataset endpoints   │  Phase 3+ graph persistence      │
│  POST /lab/datasets           │  POST /lab/workspaces            │
│  GET  /lab/datasets           │  POST /lab/graphs                │
│  GET  /lab/datasets/:id       │  GET  /lab/graphs/:id            │
│  GET  /lab/datasets/:id/preview│ (quality in :id response body)  │
│                               │  Phase 4: graph compiler         │
│  Existing: BotRun, BotEvent,  │  POST /lab/graphs/:id/compile    │
│  StrategyVersion, BacktestResult│ → returns StrategyVersion       │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────┐
│  Bot Runtime (Worker)                                             │
│  Reads: StrategyVersion.body (compiled DSL JSON)                 │
│  Does NOT know: StrategyGraph, LabWorkspace, React Flow          │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Инварианты архитектуры Lab

**Frontend не ходит на биржу напрямую:**
Это правило не меняется для Lab. Frontend Lab shell запрашивает только собственный backend.
Все данные из Bybit приходят через Backend API (proxy / cached).

**Stage 19 dataset layer переиспользуется, не переписывается:**
Lab v2 Phase 2 строит UI поверх уже существующих Stage 19 API endpoints.
Не создаётся дублирующих таблиц `Dataset`, `DatasetDefinition` и т.п.
Единственное допустимое изменение схемы в Phase 2: `MarketDataset.name` (nullable).

**Phase 1 = нет backend-изменений:**
Phase 1 — только frontend shell, компонентная структура, context bar.
Никаких новых API эндпоинтов, никаких схем, никаких DB миграций.

**Graph = authoring layer, не runtime:**
StrategyGraph и LabWorkspace — объекты уровня редактора.
Bot Runtime получает только `StrategyVersion.body` (декларативный DSL).
Runtime не знает о React Flow, нодах, портах, LabWorkspace.

### 7.3 LabWorkspace vs Workspace

| | `LabWorkspace` | `Workspace` (post-MVP) |
|---|---|---|
| Что это | Рабочая область лаборатории для Lab v2 | Мультиарендный контейнер для всего приложения |
| Когда появляется | Phase 3 (DB table) / Phase 1 (client state) | Post-MVP |
| Ownership | `workspaceId` FK → Workspace; один LabWorkspace на Workspace в Phase 3 | Содержит пользователей и роли |
| Что хранит | activeExchangeConnectionId, activeDatasetId, uiState | userId набор, роли, квоты |
| Путается ли с Workspace | **НЕТ** — отдельная таблица, отдельный концепт | — |

> Правило: `LabWorkspace` принадлежит `Workspace` через `workspaceId` FK — но это разные сущности. `LabWorkspace` — инструментальная область редактора; `Workspace` — мультиарендный контейнер приложения. Не использовать взаимозаменяемо.

### 7.4 Цепочка компиляции (Phase 4)

```
StrategyGraph (Phase 3 DB entity)
     │
     │  POST /api/v1/lab/graphs/:id/compile
     ▼
Graph Compiler (Phase 4 backend service / function)
     │  Reads: StrategyGraph.nodesJson + edgesJson
     │  Reads: blockLibraryVersion → block-to-DSL mapping table
     ▼
StrategyVersion.body (declarative DSL JSON)
     │  + creates StrategyGraphVersion (immutable snapshot)
     ▼
BotRun → Bot Runtime Worker
     │  Reads StrategyVersion.body only
     ▼
Bybit API (via Backend)
```

- Компилятор живёт в backend (не в браузере).
- Mapping table (block type → DSL rule) документируется в `docs/10-strategy-dsl.md §8` до начала кодирования Phase 4.
- Фронтенд только вызывает эндпоинт компиляции и отображает результат.

### 7.5 Хронология новых компонентов по фазам

| Компонент | Тип | Фаза | Влияние на смежные системы |
|---|---|---|---|
| `LabShell`, `ContextBar`, mode tabs | Frontend only | Phase 1 | Нет (0 backend changes) |
| `react-resizable-panels` | Frontend dep | Phase 1 | Нет |
| Dataset UI (DatasetPanel) | Frontend only | Phase 2 | Читает Stage 19 API — не меняет его |
| `MarketDataset.name` column | DB migration | Phase 2 | Nullable add; non-breaking |
| `LabWorkspace` table | DB migration | Phase 3 | Новая таблица; нет FK на существующие critical entities |
| `StrategyGraph` table | DB migration | Phase 3 | Новая таблица; FK на LabWorkspace |
| React Flow canvas | Frontend dep | Phase 3 | Нет backend влияния |
| Graph compiler endpoint | Backend | Phase 4 | Создаёт StrategyVersion + StrategyGraphVersion |
| `StrategyGraphVersion` table | DB migration | Phase 4 | FK на StrategyGraph + StrategyVersion |
| BacktestRunner UI | Frontend | Phase 5 | Вызывает существующий Stage 19 backtest API |
