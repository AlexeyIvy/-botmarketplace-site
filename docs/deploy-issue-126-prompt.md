# VPS Deploy Prompt — Issue #126 (DSL-Driven Backtest Evaluator)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Issue #126 — DSL-Driven Backtest Evaluator.
Это P0 архитектурный PR, заменяющий старый hardcoded price-breakout алгоритм на generic DSL-driven evaluator. Затрагивает backend API (backtest engine, sweep, routes). Нет Prisma миграций, нет новых npm-пакетов, нет изменений фронтенда.

### Что такое Issue #126

Issue #126 полностью переписывает backtest engine:
- Новый `dslEvaluator.ts` — pure-function evaluator, читающий entry/exit/risk из compiled Strategy DSL
- 6 типов exit: SL, TP, indicator_exit, time_exit, trailing_stop, end_of_data
- Dual-side entry через `sideCondition` (DSL v2) — long и short в одной стратегии
- Indicator cache — pre-compute once, O(1) lookup per bar
- `backtest.ts` стал thin wrapper, делегирующий всё в dslEvaluator
- BacktestSweep теперь мутирует DSL через `applyDslSweepParam()` на каждой итерации
- end_of_data outcome определяется по фактическому PnL (не hardcoded NEUTRAL)
- Deterministic: same input → same output (протестировано)

**Изменённые файлы:**
| Файл | Описание |
|------|----------|
| `apps/api/src/lib/dslEvaluator.ts` | Новый: DSL-driven backtest evaluator (780 строк) |
| `apps/api/src/lib/backtest.ts` | Переписан: thin wrapper вокруг dslEvaluator |
| `apps/api/src/lib/dslSweepParam.ts` | Новый: утилита для DSL param injection в sweep |
| `apps/api/src/routes/lab.ts` | Обновлён: sweep использует mutated DSL |
| `apps/api/src/lib/compiler/supportMap.ts` | Обновлён: VWAP/ADX/SuperTrend promoted to "supported" |
| `apps/api/tests/lib/dslEvaluator.test.ts` | Новый: 38 тестов evaluator |
| `apps/api/tests/lib/backtest.test.ts` | Обновлён: тесты под DSL-driven API |
| `apps/api/tests/lib/applyDslSweepParam.test.ts` | Новый: 5 тестов sweep param injection |
| `apps/api/tests/fixtures/candles.ts` | Новый: генераторы candle datasets для тестов |
| `apps/api/tests/compiler/blockDrift.test.ts` | Обновлён: support status snapshot обновлён |

Issue #126 НЕ содержит:
- Prisma миграций
- Новых npm пакетов
- Изменений фронтенда
- Runtime/live execution (#128 — отдельный issue)
- DCA backtest support
- Multi-timeframe backtest

### Зависимости

Issue #126 базируется на:
- #124 (DSL v2 spec) — evaluator понимает v2 конструкции
- #125 (indicator engine) — VWAP, ADX, SuperTrend используются в evaluator

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `a77f6f1ea3e650145a92d1c8eb7371ca57a2c71f`
Базируется на: `4398401` (Issue #125 — indicator engine)
Commit message: `feat(api): DSL-driven backtest evaluator (#150)`

---

## Задача: задеплоить Issue #126 на VPS

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

# Stage-specific: проверить что #125 (indicator engine) на месте
test -f apps/api/src/lib/indicators/atr.ts && echo "#125 atr.ts present" || echo "MISSING atr.ts"
test -f apps/api/src/lib/indicators/adx.ts && echo "#125 adx.ts present" || echo "MISSING adx.ts"
test -f apps/api/src/lib/indicators/supertrend.ts && echo "#125 supertrend.ts present" || echo "MISSING supertrend.ts"
test -f apps/api/src/lib/indicators/vwap.ts && echo "#125 vwap.ts present" || echo "MISSING vwap.ts"
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Issue #126

```bash
git fetch origin main
git checkout main
git pull origin main
git log --oneline -3
```

Убедись что HEAD содержит нужный коммит:
```bash
git rev-parse HEAD
# Ожидается SHA: a77f6f1ea3e650145a92d1c8eb7371ca57a2c71f
```

Если SHA отличается:
```bash
git log --oneline --all | grep -i "backtest\|evaluator\|126\|150"
```

Проверь diff относительно предыдущего Issue #125:
```bash
git diff --name-only 4398401..HEAD
```
Ожидаемый результат:
```
apps/api/src/lib/backtest.ts
apps/api/src/lib/compiler/supportMap.ts
apps/api/src/lib/dslEvaluator.ts
apps/api/src/lib/dslSweepParam.ts
apps/api/src/routes/lab.ts
apps/api/tests/compiler/blockDrift.test.ts
apps/api/tests/fixtures/candles.ts
apps/api/tests/lib/applyDslSweepParam.test.ts
apps/api/tests/lib/backtest.test.ts
apps/api/tests/lib/dslEvaluator.test.ts
```

Проверь ключевые файлы на месте:
```bash
test -f apps/api/src/lib/dslEvaluator.ts && echo "dslEvaluator.ts OK" || echo "MISSING dslEvaluator.ts"
test -f apps/api/src/lib/dslSweepParam.ts && echo "dslSweepParam.ts OK" || echo "MISSING dslSweepParam.ts"
test -f apps/api/tests/lib/dslEvaluator.test.ts && echo "dslEvaluator.test.ts OK" || echo "MISSING"
test -f apps/api/tests/lib/applyDslSweepParam.test.ts && echo "applyDslSweepParam.test.ts OK" || echo "MISSING"
test -f apps/api/tests/fixtures/candles.ts && echo "candles.ts OK" || echo "MISSING candles.ts"
grep -q "runDslBacktest" apps/api/src/lib/dslEvaluator.ts && echo "runDslBacktest export OK" || echo "MISSING export"
grep -q "applyDslSweepParam" apps/api/src/routes/lab.ts && echo "sweep param import OK" || echo "MISSING import"
```

Проверь что предыдущие Issue файлы не потеряны:
```bash
test -f apps/api/src/lib/indicators/atr.ts && echo "#125 OK" || echo "#125 MISSING"
test -f apps/api/src/lib/compiler/blockRegistry.ts && echo "#122 OK" || echo "#122 MISSING"
test -f apps/api/src/lib/compiler/supportMap.ts && echo "#123 OK" || echo "#123 MISSING"
```

---

### ШАГ 2 — Установка зависимостей

Issue #126 не добавляет новых npm пакетов:
```bash
pnpm install --frozen-lockfile
```

Если завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma generate

Issue #126 не содержит Prisma миграций. Только пересборка клиента:
```bash
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

---

### ШАГ 4 — Тесты (КЛЮЧЕВОЙ ШАГ для #126)

Поскольку Issue #126 — это замена backtest engine, запуск тестов является основной валидацией.

**4.1 — Все API тесты:**
```bash
pnpm --filter @botmarketplace/api test 2>&1
```
Ожидаемый результат: **141 tests passed** (9 test files), 0 failed.

**4.2 — DSL evaluator тесты отдельно (verbose):**
```bash
cd apps/api && pnpm exec vitest run tests/lib/dslEvaluator.test.ts --reporter=verbose 2>&1
cd ../..
```
Ожидаемый результат: 38 tests passed:
- parseDsl (3 tests)
- Edge cases — empty/single/insufficient candles (3 tests)
- SMA crossover long (3 tests)
- SMA crossunder short (2 tests)
- Dual-side sideCondition (1 test)
- Indicator exit (1 test)
- Time exit (1 test)
- Trailing stop (1 test)
- ATR-based exits (1 test)
- Determinism (2 tests)
- Fees/slippage impact (1 test)
- Report rounding (1 test)
- Max drawdown (1 test)
- Unsupported signal type (1 test)
- end_of_data outcome — WIN on profit (1 test)
- end_of_data outcome — LOSS on loss (1 test)
- Golden backtest regression (1 test)

**4.3 — Sweep param тесты:**
```bash
cd apps/api && pnpm exec vitest run tests/lib/applyDslSweepParam.test.ts --reporter=verbose 2>&1
cd ../..
```
Ожидаемый результат: 5 tests passed:
- Patches matching nodeId block
- Does not mutate original DSL
- No-match returns unmodified clone
- Patches nested exit blocks
- Works with different param names

**4.4 — Backtest wrapper тесты:**
```bash
cd apps/api && pnpm exec vitest run tests/lib/backtest.test.ts --reporter=verbose 2>&1
cd ../..
```
Ожидаемый результат: 10 tests passed.

**4.5 — Contract drift тесты (регрессия #123):**
```bash
cd apps/api && pnpm exec vitest run tests/compiler/blockDrift.test.ts --reporter=verbose 2>&1
cd ../..
```
Ожидаемый результат: 11 tests passed (support status snapshot обновлён для #126).

Если тесты падают — зафиксируй полный вывод и ОСТАНОВИСЬ. Это критично.

---

### ШАГ 5 — Production builds

**5.1 — API build:**
```bash
pnpm build:api 2>&1
```
Примечание: `tsc` может выдать TS6059 ошибки для test файлов (rootDir vs include — pre-existing issue).
Это НЕ блокирует деплой, т.к. production runtime использует `dist/server.js`.

Проверь артефакт:
```bash
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**5.2 — Web build (Next.js):**
```bash
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, нет `Error:` / `Failed to compile`.

Если любой build упал — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 6 — Проверка bundle

**6.1 — Артефакты #126 в bundle:**
```bash
grep -r "runDslBacktest" apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл (dslEvaluator.js)

grep -r "applyDslSweepParam" apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл (dslSweepParam.js или lab.js)

grep -r "end_of_data" apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

**6.2 — Регрессия #125 (indicator engine в bundle):**
```bash
grep -r "calcATR\|calcADX\|calcSuperTrend\|calcVWAP" apps/api/dist/ --include="*.js" -l 2>/dev/null | head -5
# Ожидается: минимум 1 файл для каждого индикатора
```

**6.3 — Регрессия #122 (block registry):**
```bash
grep -r "BlockRegistry" apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

---

### ШАГ 7 — Перезапуск сервисов

Issue #126 меняет runtime backend код (backtest engine + routes).
Перезапуск API обязателен.

**Вариант A — systemd:**
```bash
systemctl restart botmarket-api
sleep 3
systemctl status botmarket-api

systemctl restart botmarket-web
sleep 5
systemctl status botmarket-web
```

**Вариант B — pm2:**
```bash
pm2 restart api
sleep 3
pm2 logs api --lines 20 --nostream

pm2 restart web
sleep 5
pm2 status
pm2 logs web --lines 30 --nostream
```

**Вариант C — ручной (если нет systemd/pm2):**
```bash
pkill -f "node.*dist/server" || true
pkill -f "next start"        || true
sleep 2

cd apps/api && nohup node dist/server.js >> /var/log/botmarket-api.log 2>&1 &
echo "API PID: $!"

cd ../web && nohup pnpm start >> /var/log/botmarket-web.log 2>&1 &
echo "Web PID: $!"

sleep 5
pgrep -a node | grep -E "server|next"
```

Зафиксируй, какой вариант использован и его результат.

---

### ШАГ 8 — Smoke Tests: базовая инфраструктура

**8.1 API health check:**
```bash
curl -s http://localhost:4000/api/v1/healthz
# Ожидается: {"status":"ok","uptime":...}
```

**8.2 Web: /login возвращает 200:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
# Ожидается: 200
```

**8.3 Web: предыдущие страницы не сломаны:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
# Ожидается: 200
```

---

### ШАГ 9 — Smoke Tests: Issue #126 (ОБЯЗАТЕЛЬНО)

**Подготовка:**
```bash
export BASE=http://localhost:4000/api/v1

# Зарегистрировать / залогиниться
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_126@test.local","password":"SmokeTest1!"}')
echo "$REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN пустой — auth не работает, ОСТАНОВИСЬ.

**9.1 — POST /lab/backtest endpoint доступен (DSL-driven):**
```bash
S1=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"nonexistent","strategyVersionId":"nonexistent"}')
echo "Test 9.1 (backtest endpoint exists) → $S1 (expected: 400 or 404, NOT 500)"
```

**9.2 — POST /lab/backtest/sweep endpoint доступен:**
```bash
S2=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest/sweep \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"x","strategyVersionId":"y","sweepParam":{"blockId":"n1","paramName":"length","from":5,"to":10,"step":1}}')
echo "Test 9.2 (sweep endpoint exists) → $S2 (expected: 400 or 404, NOT 500)"
```

**9.3 — Sweep validation — missing params → 400:**
```bash
S3=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest/sweep \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Test 9.3 (sweep validation) → $S3 (expected: 400)"
```

**9.4 — Sweep validation — bad range → 400:**
```bash
S4=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest/sweep \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"x","strategyVersionId":"y","sweepParam":{"blockId":"n1","paramName":"length","from":10,"to":5,"step":1}}')
echo "Test 9.4 (sweep bad range) → $S4 (expected: 400)"
```

**9.5 — Backtest/sweep без auth → 401:**
```bash
S5=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Test 9.5 (backtest no auth) → $S5 (expected: 401)"

S6=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest/sweep \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Test 9.6 (sweep no auth) → $S6 (expected: 401)"
```

**9.6 — GET /lab/backtests list works:**
```bash
S7=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/backtests \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 9.7 (backtest list) → $S7 (expected: 200)"
```

---

### ШАГ 10 — Проверка логов

**10.1 — Нет crash-логов после рестарта:**
```bash
LOG=/var/log/botmarket-api.log
if [ -f "$LOG" ]; then
  tail -30 "$LOG" | grep -iE "error|crash|fatal|uncaught" | head -5
else
  journalctl -u botmarket-api --no-pager -n 30 2>/dev/null | grep -iE "error|crash|fatal" | head -5 || true
  pm2 logs api --lines 30 --nostream 2>/dev/null | grep -iE "error|crash|fatal" | head -5 || true
fi
# Ожидается: ПУСТОЙ вывод (нет ошибок)
```

**10.2 — Нет секретов в логах (КРИТИЧНО):**
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

---

### ШАГ 11 — Regression: предыдущие Issues

```bash
echo "--- Regression: previous Issues ---"

# API health
curl -s http://localhost:4000/api/v1/healthz | grep -o '"status":"ok"'
# Ожидается: "status":"ok"

# Auth endpoint exists (401, не 404)
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/auth/me -H "Authorization: Bearer invalid"
# Ожидается: 401

# Public endpoint
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:4000/api/v1/terminal/ticker?symbol=BTCUSDT"
# Ожидается: 200

# Lab page
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
# Ожидается: 200

# Graph endpoints (from previous issues)
curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/graphs \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID"
# Ожидается: 200
```

---

### ШАГ 12 — Финальная git проверка

```bash
git log --oneline 4398401..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `DSL-driven backtest evaluator` или `#150`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов вне scope Issue #126
- НЕ реализовывать runtime evaluator (#128) — это следующий issue
- НЕ исправлять pre-existing TS6059 ошибки (rootDir issue) — только репортировать
- НЕ делать merge или rebase
- НЕ менять DCA/MTF behavior
- НЕ применять SQL вручную

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Issue #126 (DSL-Driven Backtest Evaluator)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no
- #125 indicator files present (atr/adx/supertrend/vwap): yes/no

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: a77f6f1ea3e650145a92d1c8eb7371ca57a2c71f
- SHA match: yes/no
- Diff files vs #125: (list)
- dslEvaluator.ts present: yes/no
- dslSweepParam.ts present: yes/no
- runDslBacktest export: yes/no
- applyDslSweepParam import in lab.ts: yes/no

**3. Build & Test Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed
- API tests (all): 141 passed / N passed / failed
- DSL evaluator tests: 38 passed / N passed / failed
- Sweep param tests: 5 passed / N passed / failed
- Backtest wrapper tests: 10 passed / N passed / failed
- Contract drift tests: 11 passed / N passed / failed
- API build (dist/server.js): success / failed
- next build: success / failed
- runDslBacktest in dist: yes/no
- applyDslSweepParam in dist: yes/no
- TS6059 pre-existing errors: yes/no (expected: yes — not a blocker)

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed / skipped
- API process running: yes/no
- Web process running: yes/no

**5. Smoke Tests — Issue #126**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| POST /lab/backtest (exists) | 400/404 | ? | |
| POST /lab/backtest/sweep (exists) | 400/404 | ? | |
| Sweep missing params | 400 | ? | |
| Sweep bad range | 400 | ? | |
| Backtest no auth | 401 | ? | |
| Sweep no auth | 401 | ? | |
| GET /lab/backtests | 200 | ? | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| Auth /me (no auth) | 401 | ? | |
| Terminal ticker | 200 | ? | |
| GET /lab/graphs | 200 | ? | |
| No crash logs | empty | ? | |
| No secrets in logs | empty | ? | |

**7. Final Judgment**
- Issue #126 successfully deployed: yes / no
- All 141 tests passed: yes / no
- All smoke tests passed: yes / no
- Logs safe (no secrets): yes / no
- Regression from previous Issues: none / (describe)
- API health: ok / degraded
- Ready to proceed to Issue #128: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя Issue #126.
```
