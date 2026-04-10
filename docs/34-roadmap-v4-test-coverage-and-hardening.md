# Roadmap V4 — Test Coverage & Hardening

> **Статус**: активный план, создан 2026-04-10
> **Контекст**: экспертное ревью после завершения всех 12 задач Roadmap V3 Follow-up (#211-#222).
> Покрытие тестами выросло до 1295, но 50% route-файлов и весь actions-слой остаются без тестов.
> **Общая оценка**: 7.3/10. Архитектура зрелая, trading core хорошо покрыт, но бизнес-CRUD и безопасность — главные пробелы.
>
> **Цель документа**: зафиксировать следующий batch доработок с приоритизацией по impact.
> **GitHub Issues**: #223-#235 (13 задач)

---

## Текущее состояние покрытия

| Область | Файлов | С тестами | Покрытие | Критичность gap |
|---------|--------|-----------|----------|-----------------|
| Routes (API endpoints) | 20 | 10 | 50% | HIGH — бизнес-ядро не покрыто |
| Lib (core logic) | 81 | ~40 | ~50% | MEDIUM — trading core покрыт хорошо |
| Actions (CRUD bridge) | 4 | 0 | 0% | HIGH — bridge между routes и DB |
| AI module | 6 | 0 | 0% | MEDIUM — prompt injection risk |
| Frontend (Next.js) | 18 pages | 0 | 0% | LOW — пока приемлемо |

### Непокрытые route-файлы (10 из 20)

| Route | Endpoints | Риск без тестов |
|-------|-----------|-----------------|
| `bots.ts` | 7 (CRUD + start/stop + positions) | **HIGH** — ядро продукта |
| `runs.ts` | 10+ (lifecycle + reconcile + heartbeat) | **HIGH** — state machine transitions |
| `strategies.ts` | 5 (CRUD + validate + versions) | **HIGH** — DSL pipeline |
| `intents.ts` | 3 (create + list + state change) | **HIGH** — idempotency гарантии |
| `lab.ts` | 15+ (graphs + compile + backtest + sweep) | MEDIUM — research IDE |
| `datasets.ts` | 4 (CRUD + preview + quality) | MEDIUM — data layer |
| `ai.ts` | 4 (chat + plan + execute + status) | MEDIUM — LLM integration |
| `workspaces.ts` | 2 (list + create) | LOW — simple CRUD |
| `users.ts` | 1 (PATCH /me) | LOW — trivial |
| `preferences.ts` | 2 (GET + PATCH) | LOW — settings |

---

## Tier A — Критические (бизнес-ядро без тестов)

### A1. Route tests: bots.ts (#223)

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 1 сессия |
| **Файлы** | новый `apps/api/tests/routes/bots.test.ts`, `apps/api/src/routes/bots.ts` |

**Проблема:**
`bots.ts` — 7 endpoints (GET /bots, POST /bots, GET /bots/:id, PATCH /bots/:id, GET /bots/:id/runs, GET /bots/:id/positions, POST /bots/:id/start-stop). Все за `app.authenticate`. Workspace isolation через `resolveWorkspace()`. **Ноль тестов.** Любой рефакторинг CRUD или isolation — слепая зона.

**Что покрыть:**
- CRUD: create bot, get by id, list, update name/exchangeConnectionId
- Auth: 401 without token, 403 wrong workspace
- Workspace isolation: user A не видит ботов user B
- Validation: missing required fields → 400
- Edge cases: get nonexistent bot → 404, duplicate create logic

**Паттерн:** по аналогии с `auth.test.ts` — `buildApp()`, mock prisma, `app.inject()`.

---

### A2. Route tests: runs.ts (#224)

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 1-2 сессии |
| **Файлы** | новый `apps/api/tests/routes/runs.test.ts`, `apps/api/src/routes/runs.ts` |

**Проблема:**
`runs.ts` — 10+ endpoints: POST /runs (start), POST /runs/:id/stop, GET /runs/:id/state, POST /runs/stop-all, POST /runs/reconcile, GET /runs/:id/events, GET /runs/:id/intents. State transitions, optimistic locking (version field), worker-secret guard на machine-to-machine endpoints. **Ноль тестов.**

**Что покрыть:**
- Start run: success, bot not found, already running → conflict
- Stop run: success, not found, already stopped → no-op
- Stop-all: cancels all RUNNING runs for workspace
- State endpoint: returns current state + version
- Auth: 401/403 for all endpoints
- Worker secret: /runs/:id/state с неверным секретом → 403
- Events/intents listing: pagination, empty results

---

### A3. Route tests: strategies.ts (#225)

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 1 сессия |
| **Файлы** | новый `apps/api/tests/routes/strategies.test.ts`, `apps/api/src/routes/strategies.ts` |

**Проблема:**
`strategies.ts` — 5 endpoints: GET/POST /strategies, GET /strategies/:id, POST /strategies/:id/versions, POST /strategies/validate. DSL validation endpoint — ключевой для Lab. **Ноль тестов.**

**Что покрыть:**
- CRUD: create, list, get by id
- Version creation: valid DSL → 201, invalid DSL → 400
- Validate endpoint: valid → { valid: true }, invalid → { valid: false, errors }
- Auth + workspace isolation
- Edge cases: create version for nonexistent strategy → 404

---

### A4. Crypto roundtrip тесты (#226)

| | |
|---|---|
| **Приоритет** | CRITICAL |
| **Effort** | 0.5 сессии |
| **Файлы** | новый `apps/api/tests/lib/crypto.test.ts`, `apps/api/src/lib/crypto.ts` |

**Проблема:**
`crypto.ts` реализует AES-256-GCM шифрование API-ключей бирж. Есть `encryptionKeyFix.test.ts` (16 тестов), но нет roundtrip тестов самого encrypt/decrypt. Если шифрование/дешифрование сломается — все exchange connections перестанут работать.

**Что покрыть:**
- encrypt → decrypt → assert same plaintext (roundtrip)
- Different plaintexts produce different ciphertexts (random IV)
- Wrong key → decrypt throws
- Tampered ciphertext → decrypt throws (auth tag validation)
- Empty string encryption
- Unicode/special characters

> Документировано в Roadmap V3 Tier 2 как незакрытая задача.

---

## Tier B — Важные (надёжность и изоляция)

### B1. Route tests: intents.ts + datasets.ts (#227)

| | |
|---|---|
| **Приоритет** | HIGH |
| **Effort** | 1 сессия |
| **Файлы** | новые `apps/api/tests/routes/intents.test.ts`, `apps/api/tests/routes/datasets.test.ts` |

**Проблема:**
`intents.ts` — idempotent order intent creation (clientOrderId generation, state transitions). Критично для гарантий идемпотентности. `datasets.ts` — dataset CRUD с hash verification и candle pagination. **Оба без тестов.**

**Что покрыть (intents):**
- POST /runs/:runId/intents: success, duplicate clientOrderId → idempotent
- GET /runs/:runId/intents: list with pagination
- PATCH state: valid transition, invalid transition → 400
- Auth + workspace isolation

**Что покрыть (datasets):**
- CRUD: create dataset, list, get by id
- Preview endpoint: returns paginated candles
- Data quality metrics endpoint
- Auth + workspace isolation

---

### B2. Actions layer tests (#228)

| | |
|---|---|
| **Приоритет** | HIGH |
| **Effort** | 1 сессия |
| **Файлы** | новые `apps/api/tests/lib/actions/*.test.ts`, `apps/api/src/lib/actions/` |

**Проблема:**
Слой `actions/` (bots.ts, lab.ts, runs.ts, strategies.ts) — bridge между routes и Prisma. Содержит бизнес-логику: `createBot()`, `startRun()`, `runBacktestAction()`, `createStrategy()`. **Весь слой — 0 тестов.** Если route tests мокают actions, то сами actions остаются непокрытыми.

**Что покрыть:**
- `actions/bots.ts`: createBot, updateBot, workspace scoping
- `actions/runs.ts`: startRun validation (bot exists, not already running), stopRun
- `actions/strategies.ts`: createStrategy, createVersion (DSL validation)
- `actions/lab.ts`: runBacktestAction, graph CRUD

**Паттерн:** unit tests с vi.mock для prisma. Тестировать бизнес-правила, не DB queries.

---

### B3. Workspace isolation тесты (#229)

| | |
|---|---|
| **Приоритет** | HIGH |
| **Effort** | 1 сессия |
| **Файлы** | новый `apps/api/tests/security/workspaceIsolation.test.ts`, `apps/api/src/lib/workspace.ts` |

**Проблема:**
Multi-tenant isolation через `resolveWorkspace()` middleware — критический security boundary. User из workspace A не должен видеть/менять данные workspace B. `workspace.ts` без тестов. Cross-workspace атаки не тестируются ни в одном test file.

**Что покрыть:**
- resolveWorkspace(): valid membership → OK, no membership → 403
- Cross-workspace bot access: user A → bot from workspace B → 403
- Cross-workspace strategy access: same pattern
- Missing X-Workspace-Id header → 400 or default workspace
- Edge case: user removed from workspace after token issued

---

### B4. Worker extraction refactor (botWorker.ts split) (#230)

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 2 сессии |
| **Файлы** | `apps/api/src/lib/botWorker.ts` → split into multiple |

**Проблема:**
`botWorker.ts` — **1835+ строк**, God Object. Содержит: poll loop, lease renewal, intent execution, reconciliation, DCA routing, fill handling, error classification dispatch, safety guards, position lifecycle. Документировано в V3 Tier 3 как задача worker extraction.

**Решение:**
Вынести в отдельные модули:
1. `intentExecutor.ts` — `executeIntent()` + demo/live paths
2. `intentProcessor.ts` — `processIntents()` + strategy disabled logic
3. `reconciler.ts` — `reconcilePlacedIntents()` + `reconcileEntryFill()` + `reconcileExitFill()`
4. `botWorker.ts` — тонкий orchestrator (poll loop, lease, dispatch)

> Тесты (B3 из V3 Follow-up) уже написаны для exported functions — после split нужно только поправить import paths.

> Зависимость: после A1-A3 (route tests), чтобы не сломать тесты при рефакторинге.

---

## Tier C — Средний приоритет (безопасность и quality)

### C1. Telegram token encryption (#231)

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 0.5 сессии |
| **Файлы** | `apps/api/src/routes/notifications.ts`, `apps/api/src/lib/notify.ts` |

**Проблема:**
Telegram `botToken` хранится в `UserPreference.notifyJson` в plain text. Exchange API ключи шифруются AES-256-GCM, но Telegram токены — нет. Если DB скомпрометирована, атакер получает доступ ко всем Telegram ботам пользователей.

**Решение:**
1. При сохранении: `encrypt(botToken, encKey)` → store encrypted
2. При отправке: `decrypt(encryptedToken, encKey)` → use
3. При чтении в API: возвращать masked (`****last4`)
4. Миграция: one-time script для шифрования существующих токенов

---

### C2. AI input sanitization (#232)

| | |
|---|---|
| **Приоритет** | MEDIUM |
| **Effort** | 0.5 сессии |
| **Файлы** | `apps/api/src/lib/ai/context.ts`, `apps/api/src/lib/ai/planContext.ts` |

**Проблема:**
`buildContext()` и `buildPlanContext()` передают пользовательские данные (strategy descriptions, symbol names, DSL snippets) в LLM без санитизации. Потенциальный prompt injection vector.

**Решение:**
- Валидировать и sanitize user inputs перед включением в prompt
- Ограничить длину context fields
- Escape специальных символов в user-provided content

---

### C3. CSP enforcement transition (#233)

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 0.5 сессии |
| **Файлы** | `deploy/nginx.conf` |

**Проблема:**
Content-Security-Policy в report-only mode (V3 Tier 1 рекомендация). Нужно проанализировать violation reports и переключить на enforcement.

**Решение:**
1. Проверить логи на CSP violations за последние дни
2. Если violations = 0 → переключить на enforcement
3. Если есть violations → исправить, затем переключить

---

### C4. PATCH /exchanges apiKey validation (#234)

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 15 мин |
| **Файлы** | `apps/api/src/routes/exchanges.ts` |

**Проблема:**
Документировано в V3 review notes: PATCH /exchanges/:id не валидирует новый apiKey (может быть пустой строкой). Нужна минимальная валидация.

**Решение:**
```typescript
if (body.apiKey !== undefined && (!body.apiKey || body.apiKey.length < 10)) {
  return problem(reply, 400, "apiKey must be at least 10 characters");
}
```

---

### C5. Route tests: lab.ts + ai.ts (#235)

| | |
|---|---|
| **Приоритет** | LOW |
| **Effort** | 2 сессии |
| **Файлы** | новые `apps/api/tests/routes/lab.test.ts`, `apps/api/tests/routes/ai.test.ts` |

**Проблема:**
`lab.ts` — самый большой route file (15+ endpoints: graphs, compile, backtest, sweep). `ai.ts` — LLM integration (chat, plan, execute). Оба без тестов, но менее критичны чем bots/runs/strategies.

**Что покрыть (lab):**
- Graph CRUD: create, get, list
- Compile endpoint: valid graph → compiled, invalid → errors
- Backtest launch: success, invalid params
- Sweep management

**Что покрыть (ai):**
- Chat: success, empty message
- Plan: success, invalid strategy
- Execute: valid planId, expired plan → 400
- Status: returns model availability

---

## Зависимости

```
A4 (crypto) ─── standalone, можно параллельно
A1 (bots) ──┐
A2 (runs)   ├── основа для B3 (workspace isolation)
A3 (strats) ┘
              └── B4 (worker split) зависит от route tests
B1 (intents+datasets) ── standalone
B2 (actions) ── standalone
B3 (workspace isolation) ── после A1-A3
B4 (worker extraction) ── после A1-A3 route tests
C1 (telegram encryption) ── standalone
C2 (AI sanitization) ── standalone
C3 (CSP) ── standalone
C4 (exchanges validation) ── standalone
C5 (lab+ai tests) ── standalone
```

**Рекомендуемый порядок:**
1. Batch 1 (параллельно): A1 + A2 + A3 + A4
2. Batch 2 (параллельно): B1 + B2 + B3 + C1 + C4
3. Batch 3 (параллельно): B4 + C2 + C3
4. Batch 4: C5

---

## Сводка effort

| Tier | Задач | Effort | Результат |
|------|-------|--------|-----------|
| Tier A | 4 | ~3.5-4.5 сессии | Бизнес-ядро покрыто тестами, crypto verified |
| Tier B | 4 | ~5 сессий | Actions tested, isolation verified, worker cleaned up |
| Tier C | 5 | ~4 сессии | Security hardened, remaining routes covered |
| **Итого** | **13** | **~12-14 сессий** | **Route coverage 90%+, security gaps closed** |

**После Tier A:** route coverage вырастет с 50% до 75%, crypto roundtrip гарантирован.
**После Tier B:** multi-tenant isolation протестирован, botWorker.ts разбит на модули.
**После Tier C:** security gaps закрыты, готовность к V3 Tier 3 (live trading reliability).
