# VPS Deploy Prompt — Issue #129 + #156 (Exchange Normalization, Partial-Fill Reconciliation)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Issue #129 + follow-up #156 — Exchange Normalization, Position Sizing, Partial-Fill Reconciliation, Demo Routing.
Это два связанных PR, которые закрывают gap между runtime engine (#128) и реальным exchange execution. Затрагивают backend API: Prisma миграция (IntentState + BotIntent columns), exchange modules, botWorker reconciliation, Bybit order handling. Нет изменений фронтенда, нет новых npm-пакетов.

### Что такое Issue #129

Issue #129 добавляет exchange-safety layer между runtime и Bybit:
- Новый `exchange/normalizer.ts` — нормализация qty/price по instrument rules (lotSizeFilter, priceFilter, minNotional)
- Новый `exchange/instrumentCache.ts` — кэш instrument info с TTL 5 min
- Новый `runtime/positionSizer.ts` — notional→qty конвертация с instrument-aware rounding
- Обновлён `bybitOrder.ts` — environment routing (demo/live), order status API, `mapBybitStatus()`, `avgPrice` extraction
- Обновлён `bybitCandles.ts` — переключение на demo/live endpoint
- Обновлён `terminal.ts` — live order status sync с Bybit
- Обновлён `positionManager.ts` — `applyPartialFill()` function для partial fill accounting
- Обновлён `botWorker.ts` — instrument-aware sizing в evaluateStrategies()

### Что такое #156 (follow-up)

PR #156 подключает `applyPartialFill()` к реальному runtime:
- Новая функция `reconcilePlacedIntents()` в botWorker — reconciliation loop каждые 4s
- Новые функции `reconcileEntryFill()` / `reconcileExitFill()` — routing fills через position lifecycle
- Добавлен `PARTIALLY_FILLED` в IntentState enum
- Добавлены колонки `cumExecQty`, `avgFillPrice` в BotIntent для delta tracking
- Fill price берётся из Bybit `avgPrice` (actual fill price, не order price)
- Position side определяется из `intent.side` (BUY→LONG, SELL→SHORT)

**Изменённые файлы (совокупно #129 + #156):**
| Файл | Описание |
|------|----------|
| `apps/api/prisma/schema.prisma` | +PARTIALLY_FILLED enum, +cumExecQty, +avgFillPrice columns |
| `apps/api/prisma/migrations/20260322b_partial_fill_intent_state/migration.sql` | ALTER TYPE IntentState, ALTER TABLE BotIntent |
| `apps/api/src/lib/exchange/normalizer.ts` | Новый: order normalization по instrument rules |
| `apps/api/src/lib/exchange/instrumentCache.ts` | Новый: instrument info cache |
| `apps/api/src/lib/runtime/positionSizer.ts` | Новый: notional→qty sizing |
| `apps/api/src/lib/bybitOrder.ts` | +avgPrice, +environment routing, +order status API |
| `apps/api/src/lib/bybitCandles.ts` | demo/live endpoint routing |
| `apps/api/src/lib/positionManager.ts` | +applyPartialFill() |
| `apps/api/src/lib/botWorker.ts` | +reconcilePlacedIntents(), instrument-aware sizing |
| `apps/api/src/routes/terminal.ts` | live order status sync |
| `apps/api/tests/exchange/normalization.test.ts` | 19 тестов normalizer |
| `apps/api/tests/exchange/partialFill.test.ts` | 14 тестов partial fill + env routing |
| `apps/api/tests/runtime/positionSizer.test.ts` | 11 тестов position sizer |
| `apps/api/tests/runtime/reconciliation.test.ts` | 31 тест reconciliation logic |

**Prisma миграция:** `20260322b_partial_fill_intent_state` — аддитивная. Добавляет enum value `PARTIALLY_FILLED` в IntentState, добавляет nullable columns `cumExecQty` и `avgFillPrice` в BotIntent.

Issue #129 + #156 НЕ содержат:
- Изменений фронтенда
- Новых npm пакетов
- Полный production OMS/reconciliation framework
- WebSocket execution streams
- DCA/multi-position support

### Зависимости

#129 + #156 базируются на:
- #128 (runtime signal/exit engine) — botWorker loop, evaluateStrategies()
- #127 (position domain) — Position/PositionEvent models, positionManager
- Prisma миграция #127 (`20260322a_stage3_position_domain`) должна быть уже применена

### Ветка для деплоя

Branch: `main`
HEAD SHA: `058c403359519bab4a0397d6a4d2f6b3d50ce823`
Базируется на: `1e89c0c` (Issue #128 — runtime signal/exit engine)
Коммиты:
- `1a9da20` feat(api): exchange normalization, sizing, partial-fill handling, demo routing (#129)
- `058c403` feat: wire partial-fill reconciliation into runtime (#156)

---

## Задача: задеплоить Issue #129 + #156 на VPS

Выполни следующие шаги строго по порядку.

---

### ШАГ 0 — Диагностика среды

```bash
# Версии инструментов
node --version        # ожидается >=20
pnpm --version        # ожидается >=10
git --version

# Состояние репозитория
git status
git branch
git log --oneline -5

# Сервисы
systemctl status botmarket-api 2>/dev/null || echo "no botmarket-api unit"
systemctl status botmarket-web 2>/dev/null || echo "no botmarket-web unit"
pm2 list 2>/dev/null || echo "no pm2"
pgrep -a node || echo "no node processes"

# Env файлы
test -f apps/api/.env && echo "api .env exists" || echo "no api .env"
test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"

# PostgreSQL
pg_isready 2>/dev/null && echo "pg ready" || echo "pg_isready N/A"

# Проверка предыдущей миграции (#127 Position domain)
grep -c "PositionSide" apps/api/prisma/schema.prisma
# Ожидается: > 0 (миграция #127 уже в schema)

# Проверка environment routing config
grep "BYBIT_ENV" apps/api/.env 2>/dev/null || echo "BYBIT_ENV not set (defaults to demo)"
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Issue #129 + #156

```bash
git fetch origin main
git checkout main
git pull origin main
git log --oneline -5
```

Убедись что HEAD содержит нужный коммит:
```bash
git rev-parse HEAD
# Ожидается SHA: 058c403359519bab4a0397d6a4d2f6b3d50ce823
```

Если SHA отличается:
```bash
git log --oneline --all | grep -iE "reconcil|normali|partial"
```

Проверь diff относительно предыдущего Issue #128:
```bash
git diff --name-only 1e89c0c..HEAD
```
Ожидаемый результат — 15 файлов:
```
apps/api/prisma/migrations/20260322b_partial_fill_intent_state/migration.sql
apps/api/prisma/schema.prisma
apps/api/src/lib/botWorker.ts
apps/api/src/lib/bybitCandles.ts
apps/api/src/lib/bybitOrder.ts
apps/api/src/lib/exchange/instrumentCache.ts
apps/api/src/lib/exchange/normalizer.ts
apps/api/src/lib/positionManager.ts
apps/api/src/lib/runtime/positionSizer.ts
apps/api/src/routes/terminal.ts
apps/api/tests/exchange/normalization.test.ts
apps/api/tests/exchange/partialFill.test.ts
apps/api/tests/runtime/positionSizer.test.ts
apps/api/tests/runtime/reconciliation.test.ts
docs/deploy-issue-128-prompt.md
```

Проверь ключевые артефакты на месте:
```bash
test -f apps/api/src/lib/exchange/normalizer.ts && echo "normalizer OK" || echo "MISSING"
test -f apps/api/src/lib/exchange/instrumentCache.ts && echo "instrumentCache OK" || echo "MISSING"
test -f apps/api/src/lib/runtime/positionSizer.ts && echo "positionSizer OK" || echo "MISSING"
grep -c "reconcilePlacedIntents" apps/api/src/lib/botWorker.ts
# Ожидается: >= 2 (definition + call in poll)
grep -c "avgPrice" apps/api/src/lib/bybitOrder.ts
# Ожидается: >= 3 (interface + type + extraction)
grep -c "PARTIALLY_FILLED" apps/api/prisma/schema.prisma
# Ожидается: >= 1
```

Проверь что предыдущие файлы из #128 не потеряны:
```bash
test -f apps/api/src/lib/signalEngine.ts && echo "signalEngine OK" || echo "MISSING"
test -f apps/api/src/lib/exitEngine.ts && echo "exitEngine OK" || echo "MISSING"
test -f apps/api/src/lib/positionManager.ts && echo "positionManager OK" || echo "MISSING"
```

---

### ШАГ 2 — Установка зависимостей

Issue #129 + #156 не добавляют новых npm пакетов:
```bash
pnpm install --frozen-lockfile
```

Если завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma миграция

```bash
pnpm db:migrate
```
Ожидаемый результат: `20260322b_partial_fill_intent_state` применена, exit code 0.

Проверь применение:
```bash
pnpm db:generate
grep "PARTIALLY_FILLED" apps/api/prisma/schema.prisma
grep "cumExecQty" apps/api/prisma/schema.prisma
grep "avgFillPrice" apps/api/prisma/schema.prisma
```
Ожидается: все три grep дают совпадения.

Если миграция упала — ОСТАНОВИСЬ. Не применяй SQL вручную.

---

### ШАГ 4 — TypeScript проверка (tsc)

**4.1 — API:**
```bash
pnpm --filter @botmarketplace/api exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок (кроме TS6059 для test файлов — pre-existing), exit code 0.

**4.2 — Web:**
```bash
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

Если есть TypeScript ошибки (кроме TS6059) — зафиксируй полный список и ОСТАНОВИСЬ.

---

### ШАГ 5 — Тесты (ОБЯЗАТЕЛЬНО)

```bash
cd apps/api && pnpm test 2>&1
```

Ожидаемый результат: **296 тестов, 18 файлов, все pass**.

Ключевые test suites для #129 + #156:
| Test File | Tests | Описание |
|-----------|-------|----------|
| `tests/exchange/normalization.test.ts` | 19 | order normalization rules |
| `tests/exchange/partialFill.test.ts` | 14 | partial fill math + env routing |
| `tests/runtime/positionSizer.test.ts` | 11 | notional→qty sizing |
| `tests/runtime/reconciliation.test.ts` | 31 | reconciliation: deltas, state transitions, routing, VWAP, PnL |

Если любые тесты падают — зафиксируй вывод и ОСТАНОВИСЬ.

---

### ШАГ 6 — Production builds

**6.1 — API build:**
```bash
cd /root/botmarketplace-site  # или где лежит repo на VPS
pnpm build:api 2>&1
```
Ожидаемый результат: exit code 0.
```bash
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**6.2 — Web build (Next.js):**
```bash
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, нет `Error:` / `Failed to compile`.

Если любой build упал — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 7 — Проверка bundle

**7.1 — Артефакты #129 + #156 в bundle:**
```bash
grep -r "reconcilePlacedIntents\|normalizeOrder\|instrumentCache\|applyPartialFill" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -5
# Ожидается: минимум 1 файл
```

**7.2 — Регрессия предыдущих Issues:**
```bash
grep -r "evaluateEntry\|evaluateExit\|signalEngine\|exitEngine" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл (из #128)
```

---

### ШАГ 8 — Перезапуск сервисов

**Вариант A — systemd:**
```bash
systemctl restart botmarket-api
sleep 3
systemctl status botmarket-api
```

**Вариант B — pm2:**
```bash
pm2 restart api
sleep 3
pm2 logs api --lines 20 --nostream
```

**Вариант C — ручной:**
```bash
pkill -f "node.*dist/server" || true
sleep 2
cd apps/api && nohup node dist/server.js >> /var/log/botmarket-api.log 2>&1 &
echo "API PID: $!"
sleep 3
pgrep -a node | grep server
```

Web перезапуск тоже (если нужен — #129 не меняет frontend, но build:web обновил bundle):
```bash
# systemd: systemctl restart botmarket-web
# pm2: pm2 restart web
# manual: аналогично
```

Зафиксируй, какой вариант использован и его результат.

---

### ШАГ 9 — Smoke Tests: базовая инфраструктура

**9.1 API health check:**
```bash
curl -s http://localhost:4000/api/v1/healthz
# Ожидается: {"status":"ok","uptime":...}
```

**9.2 Web: /login возвращает 200:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
# Ожидается: 200
```

**9.3 Web: предыдущие страницы:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
# Ожидается: 200
```

---

### ШАГ 10 — Smoke Tests: Issue #129 + #156 (ОБЯЗАТЕЛЬНО)

**Подготовка:**
```bash
export BASE=http://localhost:4000/api/v1

# Зарегистрировать / залогиниться
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_129@test.local","password":"SmokeTest1!"}')
echo "$REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN пустой — попробуй login:
```bash
REG=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_129@test.local","password":"SmokeTest1!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN всё ещё пустой — auth не работает, ОСТАНОВИСЬ.

**10.1 — Ticker endpoint (exchange routing):**
```bash
S1=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/terminal/ticker?symbol=BTCUSDT")
echo "Test 10.1 (ticker) → $S1 (expected: 200)"
```

**10.2 — Candles endpoint:**
```bash
S2=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/terminal/candles?symbol=BTCUSDT&interval=15&limit=10")
echo "Test 10.2 (candles) → $S2 (expected: 200)"
```

**10.3 — Bot positions endpoint (requires auth):**
```bash
# Создать бота для теста
BOT=$(curl -s -X POST $BASE/bots \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke_129","symbol":"BTCUSDT","description":"smoke test"}')
BOT_ID=$(echo "$BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "Bot ID: $BOT_ID"

# GET positions (should be empty array)
S3=$(curl -s "$BASE/bots/$BOT_ID/positions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 10.3 (positions) → $S3 (expected: [] or empty array)"
```

**10.4 — Worker reconciliation loop running (check logs):**
```bash
# Проверь что worker не крашнулся при старте
journalctl -u botmarket-api --no-pager -n 50 2>/dev/null | grep -iE "botWorker|reconcil" | tail -5 || \
  pm2 logs api --lines 50 --nostream 2>/dev/null | grep -iE "botWorker|reconcil" | tail -5 || \
  tail -100 /var/log/botmarket-api.log 2>/dev/null | grep -iE "botWorker|reconcil" | tail -5 || \
  echo "could not check worker logs"
# Ожидается: "botWorker started" в логах, без errors
```

**10.5 — Нет токена → 401:**
```bash
S5=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/bots")
echo "Test 10.5 (no auth) → $S5 (expected: 401)"
```

---

### ШАГ 11 — Проверка логов

**11.1 — Нет секретов в логах (КРИТИЧНО):**
```bash
LOG=/var/log/botmarket-api.log
if [ -f "$LOG" ]; then
  tail -200 "$LOG" | grep -iE "passwordHash|jwt|bearer |secret|encryptedSecret|apiKey" | head -5
else
  journalctl -u botmarket-api --no-pager -n 100 2>/dev/null | \
    grep -iE "passwordHash|jwt|bearer |encryptedSecret" | head -5 || true
fi
# Ожидается: ПУСТОЙ вывод. Совпадения — критическая проблема.
```

**11.2 — Worker логи корректны:**
```bash
journalctl -u botmarket-api --no-pager -n 100 2>/dev/null | grep -i "error" | tail -5 || \
  pm2 logs api --lines 100 --nostream 2>/dev/null | grep -i "error" | tail -5 || \
  tail -200 /var/log/botmarket-api.log 2>/dev/null | grep -i "error" | tail -5 || true
# Если есть ошибки — зафиксируй, но не считай blocker если worker работает
```

---

### ШАГ 12 — Regression: предыдущие Issues

```bash
echo "--- Regression: previous Issues ---"

# Health
curl -s $BASE/healthz | grep -o '"status":"ok"'
# Ожидается: "status":"ok"

# Auth endpoint exists
curl -s -o /dev/null -w "%{http_code}" \
  $BASE/auth/login -X POST -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"invalid"}'
# Ожидается: 400 или 401 (не 404)

# Ticker (public)
curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/terminal/ticker?symbol=BTCUSDT"
# Ожидается: 200

# Lab backtest endpoint (auth required)
curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/lab/backtest" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{}'
# Ожидается: 400 (bad request, not 404 or 500)
```

---

### ШАГ 13 — Финальная git проверка

```bash
git log --oneline 1e89c0c..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `normalization`, `reconciliation`, `partial-fill`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов вне scope этого деплоя
- НЕ применять SQL вручную
- НЕ делать задачи Issue #130
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- НЕ менять BYBIT_ENV на "live" (оставить demo или не задавать)

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Issue #129 + #156 (Exchange Normalization, Partial-Fill Reconciliation)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no
- Previous migration (20260322a) applied: yes/no
- BYBIT_ENV: demo / live / not set (defaults to demo)

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: 058c403359519bab4a0397d6a4d2f6b3d50ce823
- SHA match: yes/no
- Diff files count: (expected: 15)
- normalizer.ts present: yes/no
- instrumentCache.ts present: yes/no
- positionSizer.ts present: yes/no
- reconcilePlacedIntents in botWorker: yes/no
- avgPrice in bybitOrder: yes/no
- PARTIALLY_FILLED in schema: yes/no

**3. Build Results**
- pnpm install: success / failed
- db:migrate (20260322b_partial_fill_intent_state): success / failed / already applied
- db:generate: success / failed
- TypeScript API (tsc --noEmit): 0 errors / N errors (excluding TS6059)
- TypeScript Web (tsc --noEmit): 0 errors / N errors
- Tests: N/296 passed, N files
- API build (dist/server.js): success / failed
- next build: success / failed

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed / skipped
- API process running: yes/no
- Web process running: yes/no

**5. Smoke Tests — #129 + #156**
| # | Test | Expected | Actual | Pass/Fail |
|---|------|----------|--------|-----------|
| 10.1 | Ticker endpoint | 200 | ? | |
| 10.2 | Candles endpoint | 200 | ? | |
| 10.3 | Bot positions | [] | ? | |
| 10.4 | Worker logs (no crash) | "botWorker started" | ? | |
| 10.5 | No auth → 401 | 401 | ? | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP | 200 | ? | |
| GET /lab HTTP | 200 | ? | |
| Auth endpoint exists | 400/401 | ? | |
| Ticker public | 200 | ? | |
| Lab backtest endpoint | 400 | ? | |

**7. Log Safety**
- Secrets in logs: none / found (describe)
- Worker errors: none / (describe)

**8. Final Judgment**
- Issue #129 + #156 successfully deployed: yes / no
- All smoke tests passed: yes / no
- All 296 tests passed: yes / no
- Logs safe (no secrets): yes / no
- Regression from previous Issues: none / (describe)
- API health: ok / degraded
- Worker running: yes / no
- Ready to proceed to Issue #130: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя #129 + #156.
```
