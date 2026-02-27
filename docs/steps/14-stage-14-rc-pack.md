# Stage 14 — Release Candidate Pack

## Status: DONE

## 1) Scope

- **RC Checklist** — единый документ с критериями "GO/NO-GO" перед релизом
- **Release Notes** — что в RC, что ограничено, что deferred
- **Handover/Runbook** — как деплоить, диагностировать, обслуживать
- **Smoke suite: Section 14** — Exchange Connections checks + global secret leak guard
- **Smoke suite: улучшенный summary** — hints для диагностики при падениях
- **deploy.sh: tag/ref-based deploy** — поддержка `--ref v0.1.0-rc1` для фиксированного деплоя
- **OpenAPI: missing endpoints** — добавлены `/auth/register`, `/auth/me`, `/lab/backtest*`, `/runs/{runId}/intents*`
- **OpenAPI: missing schemas** — `BotIntentView`, `BotIntentCreateRequest`, `BacktestCreateRequest`, `BacktestView`

Нет новых фич, нет изменений в логике API, нет новых зависимостей.

## 2) Scope Boundaries (что НЕ входит в Stage 14)

- Нет новых API endpoints (только документирование существующих)
- Нет UI изменений
- Нет DSL изменений
- Нет новых npm-зависимостей
- Нет DB-миграций
- Нет изменений в business logic

## 3) Files Changed

| Файл | Изменение |
|------|-----------|
| `docs/release/RC_CHECKLIST.md` | NEW — RC checklist (90+ пунктов, 12 секций) |
| `docs/release/RELEASE_NOTES_RC.md` | NEW — Release notes v0.1.0-rc1 |
| `docs/runbooks/RUNBOOK.md` | NEW — Operations runbook / handover |
| `docs/steps/14-stage-14-rc-pack.md` | NEW — этот файл |
| `deploy/smoke-test.sh` | Добавлена Section 14 (Exchange Connections + secret leak guard + улучшенный summary) |
| `deploy/deploy.sh` | Добавлен `--ref` флаг для tag/SHA-based деплоя + `DEPLOYED_REF` вывод |
| `docs/openapi/openapi.yaml` | Добавлены `/auth/register`, `/auth/me`, lab/intents endpoints + schemas |

## 4) Детали реализации

### Section 14 в smoke-test.sh (7 новых проверок)

```
14.1  POST /exchanges (demo connection) → 201
14.2  POST /exchanges → no secret fields in response
14.3  GET /exchanges → 200
14.4  GET /exchanges/:id → 200 + no secrets
14.5  GET /exchanges without auth → 401
14.6  DELETE /exchanges/:id → 204
14.7  Global secret leak guard (ticker/strategies/bots/lab/backtests list endpoints)
```

Итого smoke проверок после Stage 14: **90** (было 83).

### Улучшенный summary в smoke-test.sh

При падении тестов выводятся:
- Подсказки по частым причинам (rate limit, worker state, JWT, secrets)
- Команда для повторного запуска с нужным `BASE_URL`
- Команда для просмотра API логов

### deploy.sh: tag/ref-based деплой

**До:**
```bash
bash deploy/deploy.sh --branch main
```

**После — поддержка тега:**
```bash
bash deploy/deploy.sh --ref v0.1.0-rc1
# Делает: git fetch --tags && git checkout v0.1.0-rc1 (detached HEAD)
# Вывод деплоя содержит: "Deployed ref: v0.1.0-rc1"
```

**Тегирование RC:**
```bash
git tag -a v0.1.0-rc1 -m "Release Candidate 1 — Stage 14 complete"
git push origin v0.1.0-rc1
```

### OpenAPI gaps

Были пропущены:
- `POST /auth/register` + `GET /auth/me` — базовые auth endpoints
- `POST /lab/backtest` + `GET /lab/backtests` + `GET /lab/backtest/:id` — Research Lab
- `POST /runs/{runId}/intents` + `GET /runs/{runId}/intents` — Bot Intents (Stage 12)
- Schemas: `BotIntentView`, `BotIntentCreateRequest`, `BacktestCreateRequest`, `BacktestView`
- 401 response на `/auth/login` (было только 400)
- 429 response на `/auth/register` (rate limit)

Все добавлены без изменения существующих контрактов.

## 5) Security

Нет изменений в auth/workspace isolation. Section 14 дополнительно верифицирует:
- Exchange Connections не утекают секреты в list/get ответах
- Глобальная проверка на `encryptedSecret`/`passwordHash` в list endpoints

## 6) Verification Commands

```bash
# Запуск smoke suite (полный, 90 тестов)
bash deploy/smoke-test.sh

# Против production
BASE_URL=https://botmarketplace.store bash deploy/smoke-test.sh

# С worker secret (production mode)
BOT_WORKER_SECRET="$(grep BOT_WORKER_SECRET .env | cut -d= -f2 | tr -d '"')" \
  bash deploy/smoke-test.sh

# Деплой по тегу
bash deploy/deploy.sh --ref v0.1.0-rc1

# Проверить deployed ref
git describe --tags --always

# Верификация OpenAPI — нет ошибок валидации (если есть swagger-cli)
# npx swagger-cli validate docs/openapi/openapi.yaml
```

## 7) Acceptance Checklist (Stage 14)

- [x] RC checklist готов (`docs/release/RC_CHECKLIST.md`)
- [x] Release notes готовы (`docs/release/RELEASE_NOTES_RC.md`)
- [x] Handover/runbook готов (`docs/runbooks/RUNBOOK.md`)
- [x] Smoke-suite стабилен и покрывает E2E happy paths (90 тестов, sections 1–14)
- [x] Новые smoke проверки: Exchange Connections + global secret leak guard
- [x] deploy.sh поддерживает `--ref` для деплоя по тегу/SHA
- [x] OpenAPI дополнен недостающими endpoints и schemas
- [x] Нет scope creep (нет новых фич, нет изменений в логике)
- [x] Нет новых зависимостей
- [x] Нет DB-миграций
- [x] Verification воспроизводим командами
- [x] Проект demo-ready / RC-ready

## 8) E2E Happy Paths Coverage

| Сценарий | Секция smoke | Статус |
|---------|--------------|--------|
| Auth: Register → Login → Me | §3, §4 | ✅ |
| Exchange: Create → List → Get → Delete | §14 | ✅ |
| Terminal: Ticker → Candles (valid + errors) | §9 | ✅ |
| Strategy: Create → Validate → Version | §10 | ✅ |
| Bot Factory: Create Bot → Start Run → Events → Stop | §10, §11 | ✅ |
| Cross-workspace isolation | §11.5 | ✅ |
| Research Lab: Backtest create → list → get | §12 | ✅ |
| Observability: healthz + X-Request-Id | §13 | ✅ |
| Secret leak guard (all list endpoints) | §9, §11, §14.7 | ✅ |
| Rate limiting (429, not 500) | §5, §13 | ✅ |
| Worker auth (production BOT_WORKER_SECRET) | §7 | ✅ |

## 9) Known Limitations (demo-first)

| Limitation | Deferred to |
|-----------|-------------|
| Bot worker in-process (not separate process) | Stage 15+ |
| Real-money execution (only Bybit demo mode) | Separate decision |
| No refresh token / logout endpoint | Stage 15+ |
| No RBAC (single role: owner) | Stage 15+ |
| No centralized log aggregator | Stage 15+ |
| `execution.maxSlippageBps` enforcement | Stage 15+ |
| `entry.signal = "webhook"` routing | Stage 15+ |
| No Prometheus /metrics | Stage 15+ |
| DSL v1 only | By demand |

## 10) Deviations

Ни одного. Весь scope Stage 14 реализован как запланировано.

Единственное уточнение: OpenAPI gaps оказались шире, чем ожидалось (также отсутствовали Lab и Intents endpoints). Добавлены все, без изменения существующих контрактов — в рамках scope "OpenAPI sanity".
