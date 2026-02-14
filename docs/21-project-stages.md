# Project stages — master execution plan

Документ фиксирует этапы по всему проекту (end-to-end), чтобы у команды был единый скелет исполнения.

Принцип планирования:
- этапы фиксируем целиком сразу;
- детализируем подшаги олько для ближайшего этапа;
- следующий этап раскрывается после приёмки текущего.

## Stage 0 — Governance & baseline docs (done)

Цель:
- убрать дубли документации;
- зафиксировать source-of-truth;
- подготовить Foundation execution и control loop.

Каноника:
- `docs/20-canonical-map.md`
- `docs/18-foundation-v1-plan.md`
- `docs/19-cloudcode-control-loop.md`

## Stage 1 — Platform bootstrap (in progress)

Цель:
- поднять минимальный технический каркас проекта:
  - backend skeleton,
  - frontend shell,
  - базовая БД/миграции,
  - базовый CI-style smoke checks.

Выход stage:
- API `healthz/readyz` + auth stub;
- UI routes: `Terminal / Lab / Factory`;
- миграции применяются локально;
- есть документированный runbook запуска dev окружения.

Детализация stage:
- `docs/steps/01-stage-1-bootstrap.md`

## Stage 2 — Terminal Core (contract-first)

Цель:
- реализовать торговый минимум Terminal по OpenAPI:
  - instruments/ticker/candles,
  - exchange connections,
  - manual orders,
  - positions.

Контракт-гейт:
- `docs/openapi/openapi.yaml`
- `docs/12-api-contracts.md`

## Stage 3 — Strategy Core

Цель:
- CRUD стратегий;
- schema validation;
- versioning strategy spec;
- стабильные ошибки валидации.

## Stage 4 — Bot Runtime Core

Цель:
- state machine;
- reconciliation после restart/reconnect;
- idempotency (`intentId`/`orderLinkId`);
- event log.

## Stage 5 — Research Lab Minimum

Цель:
- исторический replay/backtest;
- базовые метрики;
- demo-forward прогон стратегии.

## Stage 6 — Hardening & Release Readiness

Цель:
- rate limiting;
- pause-on-error;
- ops/runbooks/backup-restore;
- smoke test checklist для MVP release.

## Stage acceptance rule (для всех)

Этап считается закрытым только если:
1. все обязательные результаты этапа выполнены;
2. проверки воспроизводимы командами;
3. есть PR и commit history без scope creep;
4. документация обновлена в том же PR.
