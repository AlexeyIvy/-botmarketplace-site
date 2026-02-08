# API Contracts (MVP)

Документ фиксирует минимальные контракты HTTP API для backend MVP.

## 1) Общие правила

MVP:
- Base URL: `/api`
- Формат данных: JSON
- Время: ISO-8601 в UTC
- Идентификаторы: UUID/ULID (на уровне реализации)

## 2) Auth

MVP (упрощённо):
- Аутентификация через bearer token (например JWT) в `Authorization: Bearer <token>`.
- Роли: `user`, `admin` (в MVP может быть только `user`).

Эндпоинты:
- `POST /api/auth/login` -> `{ accessToken, refreshToken }`
- `POST /api/auth/refresh` -> `{ accessToken }`
- `POST /api/auth/logout` -> `204`

## 3) Strategies

- `GET /api/strategies` -> список стратегий пользователя
- `POST /api/strategies` -> создать стратегию (payload = Strategy DSL)
- `GET /api/strategies/{strategyId}`
- `PUT /api/strategies/{strategyId}` -> обновить
- `POST /api/strategies/{strategyId}:validate` -> валидировать без сохранения
- `POST /api/strategies/{strategyId}:enable` / `:disable`

MVP MUST:
- При создании/обновлении стратегия валидируется JSON Schema (см. `docs/schema/strategy.schema.json`).

## 4) Bots

- `GET /api/bots`
- `POST /api/bots` -> создать бота (strategyId + symbol/env)
- `GET /api/bots/{botId}`
- `POST /api/bots/{botId}:start`
- `POST /api/bots/{botId}:stop`
- `POST /api/bots/{botId}:pause`
- `POST /api/bots/{botId}:resume`

MVP:
- Статусы: `IDLE`, `ARMED`, `ENTRY_PENDING`, `IN_POSITION`, `EXIT_PENDING`, `PAUSED`, `DISABLED`.

## 5) Signals / Webhooks

- `POST /api/signals/webhook/{strategyId}`

Payload (MVP пример):
{
  "side": "Buy",
  "symbol": "BTCUSDT",
  "reason": "manual-test",
  "ts": "2026-02-08T12:00:00Z"
}

MVP MUST:
- Webhook подписан shared secret (например `X-Signature` HMAC) — конкретика в реализации.

## 6) Read-only Views

- `GET /api/bots/{botId}/orders`
- `GET /api/bots/{botId}/positions`
- `GET /api/bots/{botId}/events` (transition log)

## 7) Errors (RFC 9457)

Ошибки возвращаем в формате Problem Details:
- `Content-Type: application/problem+json`
- Поля: `type`, `title`, `status`, `detail`, `instance`
- Для ошибок валидации допускаем расширение `errors[]` с `detail` и `pointer` (JSON Pointer)

Основа: RFC 9457 Problem Details for HTTP APIs. [web:733]

