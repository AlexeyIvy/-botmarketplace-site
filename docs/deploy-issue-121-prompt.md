# VPS Deploy Prompt — Issue #121 (Test Harness & Backend Strategy Test Layout)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Issue #121 — Test Harness & Backend Strategy Test Layout.
Затрагивает только backend API (новые dev-зависимости + test infrastructure). Frontend не изменён.

### Что такое Issue #121

Issue #121 добавляет тестовую инфраструктуру для backend API:
- Vitest test runner (vitest.config.ts + devDependency в apps/api/package.json)
- 3 набора unit-тестов: graphCompiler (13 тестов), backtest (11), dslValidator (19) — итого 43 теста
- Test fixtures: candles.ts (генераторы uptrend/downtrend/flat), graphs.ts (JSON для compiler)
- TESTING.md — документация по запуску тестов
- pnpm test:api / pnpm --filter @botmarketplace/api test скрипты
- Hotfix: убран "tests" из apps/api/tsconfig.json include (конфликт с rootDir: "./src")

**Изменённые/созданные файлы (12 файлов):**
| Файл | Описание |
|------|----------|
| `apps/api/TESTING.md` | Документация по тестам |
| `apps/api/package.json` | Добавлен vitest в devDependencies, скрипты test/test:watch |
| `apps/api/tests/fixtures/candles.ts` | Фикстуры свечей |
| `apps/api/tests/fixtures/graphs.ts` | Фикстуры графов |
| `apps/api/tests/lib/backtest.test.ts` | Тесты backtest |
| `apps/api/tests/lib/dslValidator.test.ts` | Тесты DSL валидатора |
| `apps/api/tests/lib/graphCompiler.test.ts` | Тесты компилятора графов |
| `apps/api/tsconfig.json` | Убран "tests" из include (hotfix TS6059) |
| `apps/api/vitest.config.ts` | Конфигурация Vitest |
| `docs/strategies/07-flagship-gap-analysis.md` | Анализ flagship стратегий |
| `package.json` | Скрипт test:api в корне |
| `pnpm-lock.yaml` | Обновлённый lockfile |

Issue #121 НЕ содержит:
- Prisma миграций (нет изменений схемы)
- Новых API endpoints (только тесты существующего кода)
- Frontend изменений (web не затронут)

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `7084bc4e924765b398f821b2ea295b24d9ad3184`
Базируется на: Phase C1 (`f1ddfb0`)
Commit message: `feat(api): test harness & backend strategy test layout + tsconfig hotfix (#121)`

---

## Задача: задеплоить Issue #121 на VPS

Выполни следующие шаги строго по порядку.

---

### ШАГ 0 — Диагностика среды

```bash
# Версии инструментов
node --version        # ожидается >=20
pnpm --version        # ожидается >=10
git --version

# Состояние репозитория
cd /opt/-botmarketplace-site
git status
git branch
git log --oneline -5

# Сервисы
systemctl status botmarket-api 2>/dev/null || echo "no botmarket-api unit"
systemctl status botmarket-web 2>/dev/null || echo "no botmarket-web unit"
pm2 list 2>/dev/null || echo "no pm2"
pgrep -a node || echo "no node processes"

# Env файлы
test -f .env && echo ".env exists" || echo "no .env"
test -f apps/api/.env && echo "api .env exists" || echo "no api .env"
test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"

# PostgreSQL
pg_isready 2>/dev/null && echo "pg ready" || echo "pg_isready N/A"

# Pre-check: убедись что tsconfig hotfix с VPS (если был) не конфликтует
grep '"tests"' apps/api/tsconfig.json && echo "WARNING: tests still in tsconfig include" || echo "tsconfig OK (no tests in include)"
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Issue #121

```bash
git fetch origin main
git checkout main
git pull origin main
git log --oneline -5
```

Убедись что HEAD содержит merge commit #121:
```bash
git rev-parse HEAD
# Ожидается SHA: 7084bc4e924765b398f821b2ea295b24d9ad3184
```

Если SHA отличается:
```bash
git log --oneline --all | grep -i "121\|test.harness"
```

Проверь diff относительно предыдущего HEAD (Phase C1 deploy prompt):
```bash
git diff --name-only f1ddfb0..HEAD
```
Ожидаемый результат (12 файлов):
```
apps/api/TESTING.md
apps/api/package.json
apps/api/tests/fixtures/candles.ts
apps/api/tests/fixtures/graphs.ts
apps/api/tests/lib/backtest.test.ts
apps/api/tests/lib/dslValidator.test.ts
apps/api/tests/lib/graphCompiler.test.ts
apps/api/tsconfig.json
apps/api/vitest.config.ts
docs/strategies/07-flagship-gap-analysis.md
package.json
pnpm-lock.yaml
```

Проверь ключевые файлы на месте:
```bash
test -f apps/api/vitest.config.ts && echo "vitest.config.ts OK" || echo "MISSING"
test -f apps/api/TESTING.md && echo "TESTING.md OK" || echo "MISSING"
test -d apps/api/tests/lib && echo "tests/lib/ OK" || echo "MISSING"
test -d apps/api/tests/fixtures && echo "tests/fixtures/ OK" || echo "MISSING"

# vitest в package.json
grep -c "vitest" apps/api/package.json
# Ожидается: >= 3

# test:api скрипт в корне
grep "test:api" package.json
# Ожидается: строка со скриптом

# tsconfig НЕ содержит "tests" в include
grep '"tests"' apps/api/tsconfig.json && echo "FAIL: tests still in tsconfig" || echo "tsconfig include OK"
```

---

### ШАГ 2 — Установка зависимостей

Issue #121 добавляет vitest как devDependency — нужен полный install:
```bash
pnpm install
```

Проверь что vitest установлен:
```bash
pnpm --filter @botmarketplace/api exec vitest --version
# Ожидается: версия vitest (например 4.x)
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma generate

Issue #121 не содержит Prisma миграций. Только пересборка клиента:
```bash
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

---

### ШАГ 4 — TypeScript проверка (tsc)

**4.1 — API:**
```bash
pnpm --filter @botmarketplace/api exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

**4.2 — Web:**
```bash
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй ошибки самостоятельно — только репортируй.

---

### ШАГ 5 — Запуск тестов (КЛЮЧЕВОЙ ШАГ для Issue #121)

Это основной deliverable Issue #121 — тестовый harness должен работать.

**5.1 — Запуск всех тестов:**
```bash
pnpm test:api 2>&1
```
Ожидаемый результат: 43 теста, все PASS, exit code 0.

**5.2 — Проверка отдельных test suites:**
```bash
echo "--- graphCompiler tests ---"
pnpm --filter @botmarketplace/api exec vitest run tests/lib/graphCompiler.test.ts 2>&1 | tail -5

echo "--- backtest tests ---"
pnpm --filter @botmarketplace/api exec vitest run tests/lib/backtest.test.ts 2>&1 | tail -5

echo "--- dslValidator tests ---"
pnpm --filter @botmarketplace/api exec vitest run tests/lib/dslValidator.test.ts 2>&1 | tail -5
```
Ожидается:
- graphCompiler: 13 passed
- backtest: 11 passed
- dslValidator: 19 passed
- Итого: 43 passed, 0 failed

Если тесты падают — зафиксируй полный вывод ошибок и ОСТАНОВИСЬ.

---

### ШАГ 6 — Production builds

**6.1 — API build:**
```bash
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

Ожидаемые страницы в выводе next build:
```
○ /
○ /login
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если любой build упал — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 7 — Проверка bundle

**7.1 — Предыдущие Phase артефакты не потеряны (regression):**
```bash
# Phase C1: sweep endpoints
grep -r "backtest/sweep\|BacktestSweep" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл

# Phase 3C: validateGraph
grep -r "validateGraph\|MISSING_RISK_BLOCK" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл

# Phase 5: BacktestForm
grep -r "BacktestForm\|Run Backtest" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

---

### ШАГ 8 — Перезапуск сервисов

Issue #121 добавляет только тесты и tsconfig hotfix — production runtime не изменён.
Однако tsconfig fix может повлиять на build output, поэтому перезапуск нужен.

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

cd /opt/-botmarketplace-site
cd apps/api && nohup node dist/server.js >> /var/log/botmarket-api.log 2>&1 &
echo "API PID: $!"

cd ../web && nohup pnpm start >> /var/log/botmarket-web.log 2>&1 &
echo "Web PID: $!"

sleep 5
pgrep -a node | grep -E "server|next"
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

**9.3 Web: /lab возвращает 200:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
# Ожидается: 200
```

---

### ШАГ 10 — Regression Smoke Tests: предыдущие фазы

**Подготовка — получить токен:**
```bash
export BASE=http://localhost:4000/api/v1

REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"deploy121_$(date +%s)@test.local\",\"password\":\"Deploy121Test!\"}")
echo "$REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS: $WS"
```

Если TOKEN пустой — попробуй login с существующим пользователем. Если не работает — ОСТАНОВИСЬ.

**10.1 — GET /lab/graphs (Phase 4):**
```bash
R1=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/graphs \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.1 (lab/graphs) → $R1 (expected: 200)"
```

**10.2 — GET /lab/strategy-versions (Phase 5):**
```bash
R2=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/strategy-versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.2 (strategy-versions) → $R2 (expected: 200)"
```

**10.3 — GET /lab/backtests (Phase 5):**
```bash
R3=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/backtests \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.3 (backtests list) → $R3 (expected: 200)"
```

**10.4 — GET /lab/datasets (Stage 19):**
```bash
R4=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.4 (datasets) → $R4 (expected: 200)"
```

**10.5 — POST /lab/backtest/sweep без auth → 401 (Phase C1):**
```bash
R5=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST $BASE/lab/backtest/sweep \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Test 10.5 (sweep no auth) → $R5 (expected: 401)"
```

---

### ШАГ 11 — Запуск полного smoke-test скрипта

```bash
bash deploy/smoke-test.sh --base-url https://botmarketplace.store 2>&1 | tail -30
```

Зафиксируй итоговый PASS/FAIL count.

---

### ШАГ 12 — Проверка логов

**12.1 — Нет секретов в логах (КРИТИЧНО):**
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

### ШАГ 13 — Финальная git проверка

```bash
git log --oneline f1ddfb0..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: коммиты связанные с #121 и tsconfig hotfix.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое тестовых файлов или vitest.config.ts
- НЕ применять SQL вручную
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- НЕ менять production code (src/)
- НЕ создавать новые тесты — только деплой существующих

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Issue #121 (Test Harness & Backend Strategy Test Layout)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: 7084bc4e924765b398f821b2ea295b24d9ad3184
- SHA match: yes/no
- Diff files vs previous HEAD: (list)
- vitest.config.ts present: yes/no
- TESTING.md present: yes/no
- tests/lib/ directory present: yes/no
- tests/fixtures/ directory present: yes/no
- vitest in package.json: yes/no
- test:api script in root: yes/no

**3. Dependencies**
- pnpm install: success / failed
- vitest version installed:

**4. TypeScript**
- TypeScript API (tsc --noEmit): 0 errors / N errors
- TypeScript Web (tsc --noEmit): 0 errors / N errors

**5. Test Results (KEY)**
| Test Suite | Tests | Passed | Failed |
|------------|-------|--------|--------|
| graphCompiler.test.ts | ? | ? | ? |
| backtest.test.ts | ? | ? | ? |
| dslValidator.test.ts | ? | ? | ? |
| TOTAL | ? | ? | ? |

**6. Build Results**
- API build (dist/server.js): success / failed
- Web build (next build): success / failed

**7. Service Restart**
- Service manager used:
- API restart: success / failed
- API process running: yes/no
- Web restart: success / failed
- Web process running: yes/no

**8. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /lab/graphs (auth) | 200 | ? | |
| GET /lab/strategy-versions (auth) | 200 | ? | |
| GET /lab/backtests (auth) | 200 | ? | |
| GET /lab/datasets (auth) | 200 | ? | |
| POST /lab/backtest/sweep (no auth) | 401 | ? | |

**9. Full Smoke Test Script**
- Total PASS:
- Total FAIL:

**10. Final Judgment**
- Issue #121 successfully deployed: yes / no
- All 43 tests passed: yes / no
- Builds succeed: yes / no
- Regression tests passed: yes / no
- API health: ok / degraded
- Test harness ready for next stages: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя Issue #121.
```
