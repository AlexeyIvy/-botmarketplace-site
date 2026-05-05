# VPS Deploy Prompt — Phase C1 (Parametric Optimisation / Grid Search)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase C1 — Parametric Optimisation (Grid Search).
Phase C1 — финальная фаза Lab improvements (docs/25-lab-improvements-plan.md).
Затрагивает backend API (новые endpoints + Prisma миграция) и frontend (новый компонент + изменённая страница).

### Что такое Phase C1

Phase C1 добавляет параметрическую оптимизацию (Grid Search) в Research Lab:
- Новая Prisma модель `BacktestSweep` + enum `SweepStatus` + связь с `Workspace`
- Миграция `20260319a_phase_c1_backtest_sweep` (новая таблица + enum)
- `POST /api/v1/lab/backtest/sweep` — запуск sweep (guard: runCount > 50 → HTTP 422, max 2 concurrent → HTTP 429, rate limit 5/min)
- `GET /api/v1/lab/backtest/sweep/:id` — polling статуса/результатов
- `GET /api/v1/lab/backtest/sweeps` — список sweep'ов workspace
- `OptimisePanel.tsx` — новый frontend компонент (block/param selector, range inputs, progress bar, сортируемая таблица результатов)
- Top-level tab bar "Run Backtest | Optimise" в Test page
- `POST /api/v1/lab/backtest` (оригинальный endpoint) НЕ модифицирован
- Существующий flow "Run Backtest" полностью сохранён

**Изменённые/созданные файлы (6 файлов):**
- `apps/api/prisma/schema.prisma` — добавлены `SweepStatus` enum, `BacktestSweep` model
- `apps/api/prisma/migrations/20260319a_phase_c1_backtest_sweep/migration.sql` — новый
- `apps/api/src/routes/lab.ts` — добавлены sweep endpoints + async runner
- `apps/web/src/app/lab/test/page.tsx` — добавлен top-level tab bar
- `apps/web/src/app/lab/test/OptimisePanel.tsx` — новый
- `docs/steps/25c1-lab-phase-c1-grid-search.md` — новый

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `6901694`
Предыдущий HEAD (Phase B2): `0542b88`
Commit message: `feat(lab): Phase C1 — parametric optimisation (Grid Search) (#118)`

---

## Задача: задеплоить Phase C1 на VPS

Выполни следующие шаги строго по порядку.

---

### ШАГ 0 — Диагностика среды

Проверь состояние VPS перед началом:

1. Версии инструментов:
   ```
   node --version        # должен быть >=20
   pnpm --version        # должен быть >=10
   git --version
   ```

2. Текущее состояние репозитория:
   ```
   cd /opt/-botmarketplace-site
   git status
   git branch
   git log --oneline -5
   ```

3. Состояние запущенных сервисов:
   ```
   systemctl status botmarket-api 2>/dev/null || echo "no botmarket-api unit"
   systemctl status botmarket-web 2>/dev/null || echo "no botmarket-web unit"
   pm2 list 2>/dev/null || echo "no pm2"
   ```

4. Проверь env файлы:
   ```
   test -f .env && echo ".env exists" || echo "no .env"
   test -f apps/api/.env && echo "api .env exists" || echo "no api .env"
   test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"
   ```

5. Проверь доступность PostgreSQL:
   ```
   pg_isready 2>/dev/null && echo "pg ready" || echo "pg_isready N/A"
   ```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Phase C1

```
git fetch origin main
git checkout main
git pull origin main
git log --oneline -5
```

Убедись, что HEAD содержит merge commit Phase C1:
```
git rev-parse --short HEAD
```
Ожидается SHA: `6901694`

Проверь diff относительно Phase B2:
```
git diff --name-only 0542b88..HEAD
```
Ожидаемый результат (6 файлов):
```
apps/api/prisma/migrations/20260319a_phase_c1_backtest_sweep/migration.sql
apps/api/prisma/schema.prisma
apps/api/src/routes/lab.ts
apps/web/src/app/lab/test/OptimisePanel.tsx
apps/web/src/app/lab/test/page.tsx
docs/steps/25c1-lab-phase-c1-grid-search.md
```

Проверь ключевые файлы на месте:
```
grep -c "BacktestSweep" apps/api/prisma/schema.prisma
# Ожидается: >= 2

grep -c "backtest/sweep" apps/api/src/routes/lab.ts
# Ожидается: >= 3

test -f apps/web/src/app/lab/test/OptimisePanel.tsx && echo "OptimisePanel OK" || echo "MISSING"
```

Проверь что оригинальный POST /lab/backtest НЕ изменён:
```
grep -n "POST.*\/lab\/backtest\"" apps/api/src/routes/lab.ts
```
Ожидается: строка с `"/lab/backtest"` (без /sweep) — оригинальный endpoint на месте.

Проверь guard runCount > 50:
```
grep -A2 "runCount > 50" apps/api/src/routes/lab.ts
```
Ожидается: строка с `return problem(reply, 422, "Sweep Too Large"...`.

---

### ШАГ 2 — Установка зависимостей

Phase C1 не добавляет новых npm пакетов:

```
pnpm install --frozen-lockfile
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma: миграция + generate

**3.1 — Проверь, что миграция присутствует:**
```
ls -la apps/api/prisma/migrations/20260319a_phase_c1_backtest_sweep/
cat apps/api/prisma/migrations/20260319a_phase_c1_backtest_sweep/migration.sql
```
Ожидается: SQL с CREATE TYPE "SweepStatus" и CREATE TABLE "BacktestSweep".

**3.2 — Применить миграцию:**
```
pnpm db:migrate
```
Ожидаемый результат: migration applied successfully (exit code 0).

Если миграция завершилась ошибкой — зафиксируй и ОСТАНОВИСЬ. НЕ применяй SQL вручную.

**3.3 — Regenerate Prisma client:**
```
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully`.

**3.4 — Проверь модель в схеме:**
```
grep -A20 "model BacktestSweep" apps/api/prisma/schema.prisma
```
Ожидается: поля id, workspaceId, strategyVersionId, datasetId, sweepParamJson, status, runCount, resultsJson.

---

### ШАГ 4 — TypeScript проверка

**4.1 — API:**
```
pnpm --filter @botmarketplace/api exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок.

**4.2 — Web:**
```
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.

---

### ШАГ 5 — Production builds

**5.1 — API build:**
```
pnpm build:api 2>&1
```
Ожидаемый результат: exit code 0.
```
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**5.2 — Web build (Next.js):**
```
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, все маршруты на месте:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если любой build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 6 — Проверка bundle: Phase C1 code + regression

**6.1 — Sweep endpoints в API bundle (Phase C1):**
```
grep -r "backtest/sweep\|BacktestSweep\|Sweep Too Large" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -5
```
Ожидается: минимум 1 файл.

**6.2 — computeSharpe в API bundle (Phase C1):**
```
grep -r "computeSharpe\|runSweepAsync" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.3 — OptimisePanel в frontend bundle (Phase C1):**
```
grep -r "OptimisePanel\|Optimise.*Grid Search\|Run Sweep" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.4 — Существующий BacktestForm (Phase 5 regression check):**
```
grep -r "BacktestForm\|Run Backtest" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.5 — validateGraph в bundle (Phase 3C regression check):**
```
grep -r "validateGraph\|MISSING_RISK_BLOCK" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

---

### ШАГ 7 — Перезапуск сервисов

Phase C1 меняет API (новые endpoints + миграция) и Web (новый компонент). Перезапустить оба.

**Вариант A — systemd:**
```
systemctl restart botmarket-api
sleep 3
systemctl status botmarket-api

systemctl restart botmarket-web
sleep 5
systemctl status botmarket-web
```

**Вариант B — pm2:**
```
pm2 restart api
sleep 3
pm2 logs api --lines 20 --nostream

pm2 restart web
sleep 5
pm2 status
pm2 logs web --lines 30 --nostream
```

**Вариант C — ручной запуск (если нет systemd/pm2):**
```
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

Зафиксируй, какой вариант был использован и его результат.

---

### ШАГ 8 — Smoke Tests: базовая инфраструктура

**8.1 API health check:**
```
curl -s http://localhost:4000/api/v1/healthz
```
Ожидается: `{"status":"ok",...}`.

**8.2 Web: /login возвращает 200:**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
```
Ожидается: `200`.

**8.3 Web: /lab возвращает 200:**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`.

**8.4 Web: /lab/test возвращает 200:**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`.

---

### ШАГ 9 — Smoke Tests: Phase C1 API endpoints

**Подготовка — получить токен и workspace:**

```bash
REG=$(curl -s -X POST http://localhost:4000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"c1test_$(date +%s)@test.local\",\"password\":\"C1Test1234!\"}")
echo "REG: $REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}"
echo "WS: $WS"
```

Если TOKEN пустой — попробуй login с существующим пользователем. Если не работает — ОСТАНОВИСЬ.

**9.1 — POST /lab/backtest/sweep без auth → 401:**
```bash
S1=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/lab/backtest/sweep \
  -H "Content-Type: application/json" \
  -d '{}')
echo "Test 9.1 (no auth) → $S1 (expected: 401)"
```

**9.2 — POST /lab/backtest/sweep с auth но без body → 400:**
```bash
S2=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/lab/backtest/sweep \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS" \
  -d '{}')
echo "Test 9.2 (empty body) → $S2 (expected: 400)"
```

**9.3 — POST /lab/backtest/sweep с runCount > 50 → 422:**
```bash
S3_BODY=$(curl -s \
  -X POST http://localhost:4000/api/v1/lab/backtest/sweep \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS" \
  -d '{"datasetId":"fake","strategyVersionId":"fake","sweepParam":{"blockId":"b1","paramName":"p1","from":1,"to":1000,"step":1},"feeBps":10,"slippageBps":5}')
S3_STATUS=$(echo "$S3_BODY" | grep -o '"status":[0-9]*' | head -1 | cut -d: -f2)
echo "Test 9.3 (runCount>50) → status $S3_STATUS (expected: 422)"
echo "Body: $S3_BODY"
```
Ожидается: HTTP 422, body содержит "Sweep exceeds maximum of 50 runs".

**9.4 — GET /lab/backtest/sweep/:id без auth → 401:**
```bash
S4=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/backtest/sweep/nonexistent)
echo "Test 9.4 (get sweep, no auth) → $S4 (expected: 401)"
```

**9.5 — GET /lab/backtest/sweep/:id с auth, несуществующий → 404:**
```bash
S5=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/backtest/sweep/nonexistent \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 9.5 (get sweep, not found) → $S5 (expected: 404)"
```

**9.6 — GET /lab/backtest/sweeps с auth → 200:**
```bash
S6=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/backtest/sweeps \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 9.6 (list sweeps) → $S6 (expected: 200)"
```

**9.7 — Оригинальный POST /lab/backtest всё ещё работает (regression):**
```bash
S7=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/lab/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS" \
  -d '{"strategyVersionId":"fake","datasetId":"fake"}')
echo "Test 9.7 (original backtest endpoint) → $S7 (expected: 404, dataset not found)"
```
Ожидается: `404` (Not Found — dataset/strategyVersion не найдены, но endpoint существует и обрабатывает запрос, а не 401/405).

---

### ШАГ 10 — Regression: предыдущие фазы

**10.1 — GET /lab/graphs (Phase 4):**
```bash
R1=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/graphs \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.1 (lab/graphs) → $R1 (expected: 200)"
```

**10.2 — GET /lab/strategy-versions (Phase 5):**
```bash
R2=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/strategy-versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.2 (strategy-versions) → $R2 (expected: 200)"
```

**10.3 — GET /lab/backtests (Phase 5):**
```bash
R3=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/backtests \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.3 (backtests list) → $R3 (expected: 200)"
```

**10.4 — GET /lab/datasets (Stage 19):**
```bash
R4=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS")
echo "Test 10.4 (datasets) → $R4 (expected: 200)"
```

**10.5 — GET /terminal/ticker (public):**
```bash
R5=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:4000/api/v1/terminal/ticker?symbol=BTCUSDT")
echo "Test 10.5 (terminal ticker, public) → $R5 (expected: 200)"
```

---

### ШАГ 11 — Запуск полного smoke-test скрипта

```bash
bash deploy/smoke-test.sh --base-url https://botmarketplace.ru 2>&1 | tail -30
```

Зафиксируй итоговый PASS/FAIL count.

---

### ШАГ 12 — Финальная git проверка

```bash
git log --oneline -5
git rev-parse --short HEAD
git diff --stat 0542b88..HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов кода (schema.prisma, routes/lab.ts, page.tsx, OptimisePanel.tsx)
- НЕ применять SQL миграции вручную — только через `pnpm db:migrate`
- НЕ откатывать миграцию
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- НЕ создавать новые API endpoints
- НЕ делать Phase C2 задачи

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase C1 (Parametric Optimisation / Grid Search)

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
- Expected SHA: 6901694
- SHA match: yes/no
- Diff files vs Phase B2: (6 files listed above)
- BacktestSweep in schema: yes/no
- Sweep endpoints in lab.ts: yes/no
- OptimisePanel.tsx present: yes/no
- Original POST /lab/backtest preserved: yes/no
- runCount > 50 guard present: yes/no

**3. Migration**
- Migration name: 20260319a_phase_c1_backtest_sweep
- Migration applied: success / failed (with error)
- Prisma generate: success / failed

**4. Build Results**
- pnpm install: success / failed
- TypeScript API (tsc --noEmit): 0 errors / N errors
- TypeScript Web (tsc --noEmit): 0 errors / N errors
- API build (dist/server.js): success / failed
- next build: success / failed
- /lab/test in build output: yes/no
- Sweep code in API dist bundle: yes/no
- OptimisePanel in frontend bundle: yes/no
- BacktestForm in frontend bundle (Phase 5): yes/no
- validateGraph in bundle (Phase 3C): yes/no

**5. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed
- API process running: yes / no
- Web process running: yes / no

**6. Phase C1 Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| POST /lab/backtest/sweep (no auth) | 401 | ? | |
| POST /lab/backtest/sweep (empty body) | 400 | ? | |
| POST /lab/backtest/sweep (runCount>50) | 422 | ? | |
| GET /lab/backtest/sweep/:id (no auth) | 401 | ? | |
| GET /lab/backtest/sweep/:id (not found) | 404 | ? | |
| GET /lab/backtest/sweeps (auth) | 200 | ? | |
| POST /lab/backtest original (regression) | 404 | ? | |

**7. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /lab/test HTTP status | 200 | ? | |
| GET /lab/graphs (auth) | 200 | ? | |
| GET /lab/strategy-versions (auth) | 200 | ? | |
| GET /lab/backtests (auth) | 200 | ? | |
| GET /lab/datasets (auth) | 200 | ? | |
| GET /terminal/ticker (public) | 200 | ? | |

**8. Full Smoke Test Script**
- Total PASS:
- Total FAIL:

**9. Final Judgment**
- Phase C1 successfully deployed: yes / no
- Migration applied cleanly: yes / no
- All C1 smoke tests passed: yes / no
- Regression tests passed: yes / no
- Original backtest flow preserved: yes / no
- API health: ok / degraded
- Ready for production use: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase C1.
```
