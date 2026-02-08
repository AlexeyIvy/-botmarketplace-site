# API Contracts (MVP)

Документ фиксирует контракты HTTP API для backend MVP.

Source of truth:
- OpenAPI: `docs/openapi/openapi.yaml`

## 1) Общие правила

- Base URL: `/api`
- Формат данных: JSON
- Время: ISO-8601 в UTC
- Auth: `Authorization: Bearer <token>` (для защищённых endpoints)

## 2) Public endpoints

- `GET /api/healthz` (liveness)
- `GET /api/readyz` (readiness)
- `POST /api/auth/login` (login)
- `POST /api/signals/webhook/{strategyId}` (приём сигнала)

## 3) Protected endpoints

### Strategies
- `GET /api/strategies`
- `POST /api/strategies`
- `POST /api/strategies/{strategyId}:validate`

### Bots
- `GET /api/bots`
- `POST /api/bots`
- `GET /api/bots/{botId}/events`

## 4) Errors: Problem Details (RFC 9457)

Ошибки возвращаем в формате Problem Details:
- `Content-Type: application/problem+json`
- Поля: `type`, `title`, `status`, опционально `detail`, `instance`
- Допускаются расширения (extra fields) при необходимости

Это описано в RFC 9457 и медиа-тип `application/problem+json` зарегистрирован в IANA для этой спецификации. [web:733][web:858]

## 5) Ошибки валидации (договорённость MVP)

Для ошибок валидации допускаем extension-поле:
- `errors[]`: массив объектов `{ pointer, detail }`
- `pointer` — JSON Pointer на поле запроса (например `/risk/riskPerTradePct`)
Формат JSON Pointer определён в RFC 6901. [web:842]

