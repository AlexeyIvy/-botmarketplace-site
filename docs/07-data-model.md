# Данные и модель (DB Schema)

Документ описывает сущности, поля, связи, статусы и индексы.
Цель: MVP для 1 пользователя, но без миграционной боли при переходе к multi-user.

## 1) Общие требования к данным

MUST:
- Во всех таблицах есть `createdAt`, `updatedAt`.
- Все “публичные” идентификаторы ресурсов (botId/runId/connectionId) — UUID/ULID (не автоинкремент).
- Любой объект принадлежит `userId` (а в будущем `workspaceId`) — это основа object-level authorization.

SHOULD:
- Soft delete (deletedAt) для сущностей с историей (Bots, Connections).

## 2) Сущности и поля (MVP)

Ниже “логическая схема”. Реальная физическая схема зависит от выбранного стека (ORM/SQL).

### 2.1 User
- id (uuid/ulid, PK)
- email/username (unique)
- passwordHash / или внешний провайдер (в MVP можно упрощённо)
- createdAt, updatedAt

### 2.2 ExchangeConnection
Назначение: хранить подключение к бирже и секреты в зашифрованном виде.
- id (uuid/ulid, PK)
- userId (FK -> User.id, index)
- env: enum('demo','real')  (в MVP используем demo)
- label: string (optional)
- apiKeyId: string (можно хранить полностью или masked+hash)
- apiSecretEncrypted: blob/text (шифротекст)
- status: enum('new','ok','error','disabled')
- lastCheckedAt: timestamp
- createdAt, updatedAt, deletedAt?

Индексы:
- (userId, env)
- (userId, status)

### 2.3 InstrumentCache
Назначение: кеш справочника инструментов Bybit для валидации шагов цены/кол-ва.
Данные берём из instruments-info.
- id (uuid/ulid, PK) или составной ключ
- category: enum('linear','inverse','spot','option') (в MVP linear)
- symbol: string
- status: string (trading/halt и т.п. если доступно)
- priceFilterTickSize: string/decimal (из `priceFilter.tickSize`)
- lotSizeMinOrderQty: string/decimal (из `lotSizeFilter.minOrderQty`)
- lotSizeQtyStep: string/decimal (из `lotSizeFilter.qtyStep`)
- lotSizeMaxOrderQty: string/decimal (если нужно)
- rawJson: jsonb (сохранить оригинальный ответ для отладки)
- updatedAt

Индексы:
- (category, symbol) unique
- (updatedAt)

Факт: instruments-info содержит `priceFilter.tickSize` и `lotSizeFilter` (minOrderQty, qtyStep и др.). [web:341]

### 2.4 Bot
- id (uuid/ulid, PK)
- userId (FK, index)
- env: enum('demo','real') (в MVP demo; хранить явно, чтобы бот был привязан к окружению)
- category: enum('linear','inverse',...) (в MVP linear)
- symbol: string
- timeframe: string (например 1m/5m/15m)
- tpSlMode: enum('bybit_trading_stop','reduce_only_orders','attached_on_order') (в MVP default = bybit_trading_stop)
- status: enum('draft','ready','running','stopped','error','archived')
- activeSpecVersionId: FK -> BotSpecVersion.id
- createdAt, updatedAt, deletedAt?

Индексы:
- (userId, status)
- (userId, symbol)

### 2.5 BotSpecVersion
Назначение: версия стратегии и риск-параметров.
- id (uuid/ulid, PK)
- botId (FK, index)
- version: int (1..N) или ulid (по времени)
- strategySpecJson: jsonb
- riskConfigJson: jsonb
- createdAt

Индексы:
- (botId, version) unique
- (botId, createdAt)

### 2.6 BotRun
- id (uuid/ulid, PK)
- botId (FK, index)
- specVersionId (FK -> BotSpecVersion.id)
- status: enum('queued','running','paused','stopped','error','finished')
- startedAt, endedAt
- durationSec (целевое время)
- stopReason: enum('manual','timeout','error','risk','system')
- summaryJson: jsonb (минимум: counts, возможно pnl позже)
- createdAt, updatedAt

Индексы:
- (botId, createdAt desc)
- (status, createdAt desc)

### 2.7 BotEvent (Audit/Event log)
Назначение: журнал событий для отладки и аудита.
- id (uuid/ulid, PK)
- runId (FK -> BotRun.id, index)
- ts: timestamp (event time)
- type: enum/string (signal_generated, order_sent, order_update, position_update, risk_blocked, ws_reconnect, error)
- intentId: uuid/ulid (optional, index)
- reqId: string (optional)
- payloadJson: jsonb
- createdAt

Индексы:
- (runId, ts)
- (intentId)
- (type, ts)

## 3) Связи (ER)

User 1—N ExchangeConnection  
User 1—N Bot  
Bot 1—N BotSpecVersion  
Bot 1—N BotRun  
BotRun 1—N BotEvent

## 4) Миграции и совместимость

MUST:
- DSL/Strategy Spec имеет поле `specVersion`.
- При изменении структуры DSL:
  - либо миграция старых spec,
  - либо поддержка нескольких версий в валидаторе.

## 5) Multi-user задел (post-MVP)

План:
- Добавить `Workspace` и `workspaceId` во все сущности.
- RBAC роли на workspace.
- Квоты per workspace (боты, requests, AI generation).

Важно:
- Механика object-level authorization должна работать уже сейчас на `userId`, чтобы позже заменить/расширить на `workspaceId`.
