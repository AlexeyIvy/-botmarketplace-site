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
