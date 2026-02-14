# Stage 1 — Platform bootstrap (CloudCode task pack)

Этот документ — первый исполняемый пакет задач для CloudCode.

## 1) Scope (что делаем)

CloudCode реализует только Stage 1:
- backend skeleton:
  - `GET /api/healthz`
  - `GET /api/readyz`
  - `POST /api/auth/login` (stub)
- frontend shell:
  - routes/pages: `Terminal`, `Lab`, `Factory`
- data layer bootstrap:
  - базовая миграция БД;
  - минимальные таблицы каркаса (без полной бизнес-логики).

## 2) Scope boundaries (что НЕ делаем на этом шаге)

- не реализуем торговую логику и интеграцию Bybit;
- не реализуем Runtime state machine;
- не делаем backtest/Research logic;
- не добавляем функционал beyond Stage 1.

## 3) Required references (source-of-truth)

- Stage framework: `docs/21-project-stages.md`
- Foundation stages: `docs/18-foundation-v1-plan.md`
- Control loop: `docs/19-cloudcode-control-loop.md`
- API contracts (human): `docs/12-api-contracts.md`
- API contracts (machine): `docs/openapi/openapi.yaml`

## 4) Required output format from CloudCode

В PR-описании CloudCode ОБЯЗАН включить секции:
1. Plan
2. Implementation
3. Verification
4. Handover

Формат и критерии — строго по `docs/19-cloudcode-control-loop.md`.

## 5) Acceptance checks (обязательные)

Минимальный набор проверок в PR:
- backend dev run: сервис стартует без ошибок;
- `GET /api/healthz` -> 200;
- `GET /api/readyz` -> 200;
- `POST /api/auth/login` -> deterministic stub response;
- frontend dev run: отображаются 3 роут-вкладки (`Terminal/Lab/Factory`);
- миграция БД применяется локально (команда + результат).

## 6) Review checklist (для PM/reviewer)

- шаг не вышел за scope Stage 1;
- команды проверки воспроизводимы;
- обновлены README/инструкции запуска;
- нет конфликтов с каноническими документами.

## 7) Exit criteria

Stage 1 закрыт, если:
- acceptance checks пройдены;
- PR принят и смержен;
- следующий task pack (Stage 2) подготовлен отдельно.
