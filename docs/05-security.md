# Безопасность (Security)

Документ фиксирует минимальные обязательные политики безопасности для MVP и требования, которые нельзя нарушать при расширении проекта.

Основа: OWASP API Security Top 10 (2023) и OWASP рекомендации по управлению сессиями. [web:400][web:391]

---

## 1) Принципы безопасности

MUST:
- Минимальные привилегии: каждый компонент получает только то, что нужно.
- Zero trust к входным данным: любой ввод от UI/AI/внешних API валидируется.
- “Intent-only” стратегия: стратегия не имеет прямого доступа к торговым операциям.
- Fail-safe: при сомнениях (desync, rate limit, ошибки) бот уходит в `paused`/`stopped`.

---

## 2) Аутентификация и сессии

### 2.1 MVP (1 пользователь)
MUST:
- Даже в MVP все запросы к backend требуют аутентификацию.
- Админские операции (Stop All, просмотр сырых логов/конфигов) доступны только админ-сессии.

### 2.2 Cookies / сессии (если cookie-based)
MUST:
- Cookies сессии: `HttpOnly`, `Secure`, `SameSite=Lax` (или `Strict` если возможно). [web:391]
- Защита от CSRF: CSRF token или эквивалентный механизм. [web:391]
- Сессии имеют TTL и обновление токена по правилам (rotation).

---

## 3) Авторизация (самая частая уязвимость API)

### 3.1 Object-level authorization (BOLA / IDOR)
MUST:
- Любой эндпоинт, который принимает ID ресурса (botId, runId, connectionId), обязан проверять,
  что ресурс принадлежит текущему `userId/workspaceId`.
- Публичные идентификаторы ресурсов — UUID/ULID (не последовательные), чтобы исключить перебор. [web:403]
Причина: OWASP API1:2023 — Broken Object Level Authorization. [web:400]

### 3.2 Function-level authorization
MUST:
- Админские функции и “опасные” операции (Stop All, enable real env) вынесены в отдельные маршруты
  и защищены ролью/флагом.

---

## 4) Секреты и ключи (Bybit API secrets)

MUST:
- Bybit API secret хранится только зашифрованным (at-rest).
- Secret никогда не:
  - возвращается в UI,
  - попадает в логи,
  - отправляется в AI/LLM,
  - попадает в трейс/ошибку.
- UI после сохранения показывает только masked keyId (например, последние 4 символа).

MUST:
- При удалении подключения secret должен быть “затираем” (secure delete на уровне приложения/БД насколько возможно).

SHOULD:
- Разнести доступ к secret: только Execution/Risk слой имеет право расшифровывать secret.

---

## 5) Anti-abuse и лимиты (OWASP API4:2023)

### 5.1 Лимиты на backend
MUST:
- Rate limiting per user/per IP на ключевые эндпоинты:
  - create order,
  - start bot,
  - AI generate spec,
  - market data heavy endpoints.
- Ограничение размера payload (JSON), ограничение глубины JSON.

Причина: OWASP API4:2023 Unrestricted Resource Consumption. [web:400]

### 5.2 Лимиты на ботов
MUST:
- Max concurrent BotRuns (в MVP: 1).
- Max duration run.
- Cooldown между start.
- Max orders/min и max intents/min внутри runtime.

---

## 6) Безопасность AI-контура

MUST:
- AI генерирует только Strategy Spec и пояснения.
- AI НЕ имеет инструмента/права:
  - выполнять торговые операции,
  - читать/писать секреты,
  - выполнять произвольный код на сервере.
- Все тексты из AI рассматриваются как потенциально вредоносные:
  - если UI рендерит markdown/HTML — обязательная санитизация (защита от XSS).

MUST:
- В prompts/logs запрещены секреты и PII (redaction фильтр).

---

## 7) Безопасность торгового исполнения

MUST:
- Все торговые действия проходят через Risk guard:
  - max position USDT,
  - max loss per run,
  - SL/TP обязательны,
  - max orders/min,
  - cooldown.
- Идемпотентность:
  - каждый intent имеет `intentId`,
  - повтор intent не создаёт дубль ордера (mapping хранится в БД),
  - cancel/update операции тоже идемпотентны.

MUST:
- Подтверждение статуса:
  - успешный ответ `Place Order` не означает `filled`,
  - фактическое состояние подтверждается по приватным потокам/REST reconciliation.

---

## 8) Логи, аудит и приватность

MUST:
- Логи структурированные (JSON), с `runId`, `botId`, `intentId`, `reqId`, `env`.
- В логах нет:
  - API secrets,
  - персональных данных (если появятся в будущем),
  - “сырых” входов без redaction.

SHOULD:
- Append-only хранение важных событий (audit trail).
- Retention policy (например 30–90 дней на MVP).

---

## 9) Инциденты и аварийные процедуры (MVP)

MUST:
- Кнопка “Stop All”.
- Runbook: что делать при:
  - частых 429/rate limit,
  - desync WS,
  - ошибках подписи,
  - подозрительной активности.
- Минимальный “panic mode”: отключить ботов и запретить торговые эндпоинты до ручного включения.

---

## 10) Checklist безопасности перед релизом MVP

- [ ] Все ID ресурса проверяются на принадлежность user/workspace (BOLA).
- [ ] Реализованы rate limits на backend.
- [ ] Секреты шифруются и не попадают в логи/AI.
- [ ] Cookies имеют HttpOnly/Secure/SameSite и есть CSRF защита (если cookie-based).
- [ ] Есть Stop All и лимиты ботов.
- [ ] AI не вызывает торговые операции, markdown/HTML санитизируется.
