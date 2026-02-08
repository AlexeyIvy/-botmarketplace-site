# Roadmap (MVP -> Post-MVP)

## 1) MVP scope

MVP MUST:
- Bybit demo-first: private account/order/position только через demo.
- Strategy DSL (валидируемый) + bot runtime state machine.
- Backend API: auth, стратегии, боты, webhooks signals.
- Базовые guards: 1 позиция на symbol, rate limiting, pause on error.
- Логи и базовая операционка.

MVP SHOULD:
- Read-only UI: список ботов/стратегий/лог событий.
- Минимальный мониторинг (healthz/readyz).

## 2) Definition of Done (MVP)

- Документация в `docs/` актуальна.
- Все конфиги валидируются (schema).
- Бот переживает рестарт/обрыв WS (reconciliation).
- SL/TP обязателен и проверен на demo.

## 3) Post-MVP

- Multi-symbol / multi-bot per user.
- Spot/inverse рынки.
- Портфельные лимиты, дневные лимиты.
- Расширенный Strategy DSL (индикаторы/условия) без исполнения кода.
- Роли/команды, аудит-лог.

## 4) Release checklist (минимум)

- Секреты не в репо.
- Прогон smoke-тестов на demo.
- Бэкап БД/план восстановления.
- Проверка лимитов и пауз.

