# BotMarketplace — Техническое задание (v0.1)

Статус: MVP planning (Demo-first)  
Дата: 2026-02-06  
Владелец продукта: Alexey  
Репозиторий: -botmarketplace-site  
Назначение: веб-терминал + AI-конструктор стратегий + запуск ботов на Bybit Demo

---

## Оглавление

### 0) Введение
- [Глоссарий и определения](docs/00-glossary.md)

### 1) Цели и границы
- [Цели, не-цели, допущения, ограничения](docs/01-goals-scope.md)

### 2) Функциональные требования
- [Функционал MVP и будущие расширения](docs/02-requirements-functional.md)

### 3) Нефункциональные требования (NFR)
- [Надёжность, производительность, лимиты, совместимость](docs/03-requirements-nonfunctional.md)

### 4) Архитектура
- [Компоненты, потоки данных, окружения](docs/04-architecture.md)

### 5) Безопасность
- [Политики секретов, сессии, авторизация, anti-abuse](docs/05-security.md)

### 6) Модель угроз
- [Активы, угрозы, меры, остаточные риски](docs/06-threat-model.md)

### 7) Данные и сущности
- [Схема БД, сущности, статусы, миграции](docs/07-data-model.md)

### 8) Контракты backend API
- [Эндпоинты, payloads, ошибки, идемпотентность](docs/08-api-contracts.md)

### 9) Интеграция Bybit
- [Demo/Real, REST/WS, rate limits, trading-stop](docs/09-bybit-integration.md)

### 10) Strategy DSL (конструктор стратегий)
- [JSON-формат, валидация, примеры стратегий](docs/10-strategy-dsl.md)

### 11) Bot Runtime
- [Исполнение, state machines, reconciliation, timeout](docs/11-bot-runtime.md)

### 12) UI/UX
- [Страницы, user flows, RU/EN i18n](docs/12-ui-ux.md)

### 13) Observability и Ops
- [Логи, метрики, алерты, runbooks, бэкапы](docs/13-observability-ops.md)

### 14) Roadmap / Спринты
- [План работ спринтами + чеклисты](docs/14-roadmap-sprints.md)

### 15) Acceptance criteria
- [Критерии приёмки MVP и по спринтам](docs/15-acceptance-criteria.md)

---

## Ключевые решения (зафиксировано)

- MVP по умолчанию: рынок `linear` (USDT perpetual).
- Инструмент: пользователь выбирает любой `linear` инструмент (список из instruments-info).
- Запуск бота: по кнопке, с ограничением времени (timeout).
- Ордера: market + limit в MVP.
- SL/TP: обязательно; режим по умолчанию — Bybit `Set Trading Stop`.
- UI: RU + EN (документация — RU).
- Пользователи: сначала 1 пользователь, но сущности и API проектируем с `userId/workspaceId` под будущий multi-user.

---

## Как читать документацию (для агента/разработчика)

1) Начни с: [Цели и границы](docs/01-goals-scope.md) и [Функциональные требования](docs/02-requirements-functional.md).  
2) Если работаешь с Bybit — см. [Интеграция Bybit](docs/09-bybit-integration.md).  
3) Если работаешь с ботами — см. [Strategy DSL](docs/10-strategy-dsl.md) и [Bot Runtime](docs/11-bot-runtime.md).  
4) По безопасности — см. [Безопасность](docs/05-security.md) и [Модель угроз](docs/06-threat-model.md).  
