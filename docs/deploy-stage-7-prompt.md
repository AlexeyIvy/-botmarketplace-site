# VPS Deploy Prompt — Stage 7 (Auth Hardening & Workspace Enforcement)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Stage 7 — Auth Hardening & Workspace Enforcement.
Stage 7 — первый этап Productization v2 (docs/22-productization-v2-plan.md).
Затрагивает только backend API и docs (нет Prisma миграций, нет новых npm-пакетов,
нет изменений фронтенда).

### Что такое Stage 7

Stage 7 закрывает security gap в workspace isolation:
- `resolveWorkspace()` (apps/api/src/lib/workspace.ts) проверяет membership через
  таблицу `WorkspaceMember` по составному ключу (workspaceId, userId);
- доступ к чужому workspace → `403 Forbidden`;
- все приватные роуты защищены `authenticate` + `resolveWorkspace()`;
- `POST /runs/stop-all` явно защищён;
- логирование: только `{ userId, workspaceId }`, без passwordHash/JWT/secrets;
- docs/steps/07-stage-7-auth-workspace.md — обновлён (checklist, verification table,
  deferred items, Stage 8 handover).

**Изменённые файлы в PR (1 файл):**
- `docs/steps/07-stage-7-auth-workspace.md`
  — закрыт review checklist, добавлены verification results, route audit table,
    curl-команды двух-пользовательского сценария, deferred items.

Ядро реализации (уже в main до Stage 7 PR):
- `apps/api/src/lib/workspace.ts` — resolveWorkspace() с membership enforcement
- все роуты в `apps/api/src/routes/` — authenticate + resolveWorkspace()

Stage 7 НЕ содержит:
- Prisma миграций
- новых npm пакетов
- изменений фронтенда
- refresh token / logout / RBAC

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `10a8c13c9bb33edefe69b59bceaaf9665c20e6af`
Базируется на Phase 5 SHA: `3c13614` (fix Phase 5 VPS sync)
Commit message: `feat(security): Stage 7 — Auth Hardening & Workspace Enforcement (#64)`

---

## Задача: задеплоить Stage 7 на VPS

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
   git status
   git branch
   git log --oneline -5
   ```

3. Состояние запущенных сервисов:
   ```
   systemctl status botmarket-api 2>/dev/null || echo "no botmarket-api unit"
   systemctl status botmarket-web 2>/dev/null || echo "no botmarket-web unit"
   pm2 list 2>/dev/null || echo "no pm2"
   pgrep -a node || echo "no node processes"
   ```

4. Проверь env файлы:
   ```
   test -f apps/api/.env && echo "api .env exists" || echo "no api .env"
   test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"
   ```

5. Проверь доступность PostgreSQL:
   ```
   pg_isready 2>/dev/null && echo "pg ready" || echo "pg_isready N/A"
   ```

6. Проверь текущий workspace.ts — убедись, что membership enforcement уже в коде:
   ```
   grep -n "workspaceMember\|403\|not a member" apps/api/src/lib/workspace.ts | head -10
   ```
   Ожидается: строки с `workspaceMember.findUnique`, `403`, `"not a member"`.

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Stage 7

```
git fetch origin main
git checkout main
git pull origin main
git log --oneline -3
```

Убедись, что HEAD содержит merge commit Stage 7:
```
git rev-parse HEAD
```
Ожидается SHA: `10a8c13c9bb33edefe69b59bceaaf9665c20e6af`

Если SHA отличается — проверь git log, убедись что Stage 7 присутствует:
```
git log --oneline --all | grep -i "stage-7\|Stage 7\|Auth Hardening"
```

Проверь diff относительно Phase 5 (ожидается 1 файл):
```
git diff --name-only 3c13614..HEAD
```
Ожидаемый результат:
```
docs/steps/07-stage-7-auth-workspace.md
```

Если в diff есть production-код помимо docs — зафиксируй и сообщи.

Проверь ключевые файлы Stage 7 на месте:
```
grep -c "workspaceMember" apps/api/src/lib/workspace.ts
```
Ожидается: >= 1 (membership query присутствует).

```
grep -c "resolveWorkspace" apps/api/src/routes/strategies.ts
grep -c "resolveWorkspace" apps/api/src/routes/bots.ts
grep -c "resolveWorkspace" apps/api/src/routes/runs.ts
grep -c "resolveWorkspace" apps/api/src/routes/lab.ts
grep -c "resolveWorkspace" apps/api/src/routes/exchanges.ts
```
Ожидается: каждый >= 1.

Проверь, что `/runs/stop-all` защищён:
```
grep -A2 "stop-all" apps/api/src/routes/runs.ts | head -6
```
Ожидается: `onRequest: [app.authenticate]` в той же строке или рядом.

Проверь, что Phase 5 файлы не потеряны:
```
test -f apps/api/src/routes/lab.ts && echo "lab.ts OK" || echo "MISSING lab.ts"
test -f apps/web/src/app/lab/test/page.tsx && echo "test/page.tsx OK" || echo "MISSING test page"
test -f apps/web/src/app/lab/build/page.tsx && echo "build/page.tsx OK" || echo "MISSING build page"
test -f apps/web/src/app/lab/data/page.tsx && echo "data/page.tsx OK" || echo "MISSING data page"
```

---

### ШАГ 2 — Установка зависимостей

Stage 7 не добавляет новых npm пакетов:

```
pnpm install --frozen-lockfile
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma generate

Stage 7 не содержит Prisma миграций. Только пересборка клиента на случай clean env:

```
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

Проверь, что WorkspaceMember модель в схеме корректна:
```
grep -A8 "model WorkspaceMember" apps/api/prisma/schema.prisma
```
Ожидается: поля `workspaceId`, `userId`, `@@unique([workspaceId, userId])`.

---

### ШАГ 4 — TypeScript проверка (tsc)

**4.1 — API:**
```
pnpm --filter @botmarketplace/api exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

**4.2 — Web:**
```
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй TypeScript ошибки самостоятельно — только репортируй.

---

### ШАГ 5 — Production builds

**5.1 — API build:**
```
pnpm build:api 2>&1
```
Ожидаемый результат: exit code 0.

Проверь:
```
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**5.2 — Web build (Next.js):**
```
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, нет `Error:` / `Failed to compile`.

Stage 7 не меняет фронтенд, поэтому все Phase 5 маршруты должны быть на месте:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если любой build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 6 — Проверка bundle: Stage 7 code + Phase 5 регрессия

**6.1 — resolveWorkspace в bundle (Stage 7):**
```
grep -r "workspace access denied\|not a member\|resolveWorkspace\|workspaceMember" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.2 — Membership enforcement в bundle (Stage 7):**
```
grep -r "workspaceId_userId\|workspaceMember" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.3 — Phase 5 не сломана (BacktestForm в frontend bundle):**
```
grep -r "BacktestForm\|strategyVersionId\|POLL_INTERVAL_MS" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.4 — Phase 4 не сломана (graph-compiler в bundle):**
```
grep -r "graphToDSL\|compiledDsl\|StrategyGraphVersion" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.5 — Phase 3C не сломана (validateGraph в bundle):**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

---

### ШАГ 7 — Перезапуск сервисов

Stage 7 меняет только API (workspace enforcement уже в коде). Необходимо перезапустить API.
Web перезапускать не обязательно, но рекомендуется для чистоты.

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
Ожидается: `{"status":"ok","uptime":...}`.

**8.2 Web: /login возвращает 200:**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
```
Ожидается: `200`.

**8.3 Web: /lab возвращает 200 (Phase 5 не сломана):**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`.

**8.4 Web: /lab/test возвращает 200 (Phase 5 не сломана):**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`.

---

### ШАГ 9 — Smoke Tests: Stage 7 Security (ОБЯЗАТЕЛЬНО)

Это ключевые проверки Stage 7. Выполни все 7 тестов.

**Подготовка — зарегистрировать двух пользователей:**

```bash
# Пользователь A
REG_A=$(curl -s -X POST http://localhost:4000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"stagetest_a@test.local","password":"StageTest1!"}')
echo "REG_A: $REG_A"

TOKEN_A=$(echo "$REG_A" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_A=$(echo "$REG_A"   | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN_A length: ${#TOKEN_A}"
echo "WS_A: $WS_A"

# Пользователь B
REG_B=$(curl -s -X POST http://localhost:4000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"stagetest_b@test.local","password":"StageTest1!"}')
echo "REG_B: $REG_B"

TOKEN_B=$(echo "$REG_B" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_B=$(echo "$REG_B"   | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN_B length: ${#TOKEN_B}"
echo "WS_B: $WS_B"
```

Если TOKEN_A или TOKEN_B пустые — auth не работает, ОСТАНОВИСЬ.

---

**9.1 — Нет токена → 401:**
```bash
S1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/strategies)
echo "Test 9.1 (no auth) → $S1 (expected: 401)"
```
Ожидается: `401`.

**9.2 — Токен A, X-Workspace-Id = WS_B → 403:**
```bash
S2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_B")
echo "Test 9.2 (user A → workspace B) → $S2 (expected: 403)"
```
Ожидается: `403`.

**9.3 — Токен A, X-Workspace-Id = WS_A → 200:**
```bash
S3=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_A")
echo "Test 9.3 (user A → workspace A) → $S3 (expected: 200)"
```
Ожидается: `200`.

**9.4 — Токен B, X-Workspace-Id = WS_A → 403:**
```bash
S4=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/strategies \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "X-Workspace-Id: $WS_A")
echo "Test 9.4 (user B → workspace A) → $S4 (expected: 403)"
```
Ожидается: `403`.

**9.5 — Токен B, X-Workspace-Id = WS_B → 200:**
```bash
S5=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/strategies \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "X-Workspace-Id: $WS_B")
echo "Test 9.5 (user B → workspace B) → $S5 (expected: 200)"
```
Ожидается: `200`.

**9.6 — POST /runs/stop-all без токена → 401:**
```bash
S6=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/runs/stop-all)
echo "Test 9.6 (stop-all, no auth) → $S6 (expected: 401)"
```
Ожидается: `401`.

**9.7 — POST /runs/stop-all с токеном A, WS_B → 403:**
```bash
S7=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/runs/stop-all \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_B")
echo "Test 9.7 (stop-all, user A → workspace B) → $S7 (expected: 403)"
```
Ожидается: `403`.

---

**Повтори тесты 9.1–9.7 на /bots (второй route group):**
```bash
echo "--- /bots route group ---"

B1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/bots)
echo "Test bots-1 (no auth) → $B1 (expected: 401)"

B2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/bots \
  -H "Authorization: Bearer $TOKEN_A" -H "X-Workspace-Id: $WS_B")
echo "Test bots-2 (user A → workspace B) → $B2 (expected: 403)"

B3=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/bots \
  -H "Authorization: Bearer $TOKEN_A" -H "X-Workspace-Id: $WS_A")
echo "Test bots-3 (user A → workspace A) → $B3 (expected: 200)"
```

**Повтори на /lab/graphs (lab route group):**
```bash
echo "--- /lab/graphs route group ---"

L1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/graphs)
echo "Test lab-1 (no auth) → $L1 (expected: 401)"

L2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/graphs \
  -H "Authorization: Bearer $TOKEN_A" -H "X-Workspace-Id: $WS_B")
echo "Test lab-2 (user A → workspace B) → $L2 (expected: 403)"

L3=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/graphs \
  -H "Authorization: Bearer $TOKEN_A" -H "X-Workspace-Id: $WS_A")
echo "Test lab-3 (user A → workspace A) → $L3 (expected: 200)"
```

---

### ШАГ 10 — Smoke Tests: безопасность логов

**10.1 — Проверь, что в свежих логах API есть userId + workspaceId:**
```bash
# Взять последние 50 строк API-лога (подставь фактический путь к логу)
LOG_FILE=/var/log/botmarket-api.log
if [ -f "$LOG_FILE" ]; then
  tail -50 "$LOG_FILE" | grep -E "userId|workspaceId|workspace resolved|access denied" | tail -5
else
  echo "log file not found at $LOG_FILE — check journalctl or pm2 logs"
  journalctl -u botmarket-api --no-pager -n 30 2>/dev/null | grep -E "userId|workspaceId" | tail -5 || true
  pm2 logs api --lines 30 --nostream 2>/dev/null | grep -E "userId|workspaceId" | tail -5 || true
fi
```
Ожидается: строки вида `"userId":"...","workspaceId":"..."`.

**10.2 — Проверь отсутствие секретов в логах (КРИТИЧНО):**
```bash
LOG_FILE=/var/log/botmarket-api.log
if [ -f "$LOG_FILE" ]; then
  tail -200 "$LOG_FILE" | grep -iE "passwordHash|jwt|bearer |secret|encryptedSecret|apiKey" | head -5
else
  journalctl -u botmarket-api --no-pager -n 100 2>/dev/null | \
    grep -iE "passwordHash|jwt|bearer |encryptedSecret" | head -5 || true
  pm2 logs api --lines 100 --nostream 2>/dev/null | \
    grep -iE "passwordHash|jwt|bearer |encryptedSecret" | head -5 || true
fi
```
Ожидается: ПУСТОЙ вывод (никаких совпадений).
Если найдены совпадения — это критическая проблема, зафиксируй и сообщи.

---

### ШАГ 11 — Regression: Phase 5 API endpoints

**11.1 — GET /lab/strategy-versions (Phase 5, нет auth):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/strategy-versions \
  -H "Authorization: Bearer invalid"
```
Ожидается: `401` (не 404 — endpoint должен существовать).

**11.2 — POST /lab/backtest (Phase 5, нет auth):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:4000/api/v1/lab/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid" \
  -d '{"strategyVersionId":"x","datasetId":"y"}'
```
Ожидается: `401`.

**11.3 — GET /lab/datasets (Phase 2A, нет auth):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid"
```
Ожидается: `401`.

**11.4 — GET /exchanges (Stage 8, нет auth):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/exchanges \
  -H "Authorization: Bearer invalid"
```
Ожидается: `401`.

**11.5 — GET /terminal/ticker (public, нет auth):**
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:4000/api/v1/terminal/ticker?symbol=BTCUSDT"
```
Ожидается: `200` (публичный endpoint, auth не нужен).

---

### ШАГ 12 — Финальная git проверка

```bash
git log --oneline 3c13614..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `docs(stage-7): verify Stage 7 Auth Hardening & Workspace Enforcement complete`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов кода (workspace.ts, routes/*)
- НЕ применять SQL вручную
- НЕ реализовывать refresh token / logout / RBAC
- НЕ делать Stage 8 задачи
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- НЕ создавать новые API endpoints

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Stage 7 (Auth Hardening & Workspace Enforcement)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: 10a8c13c9bb33edefe69b59bceaaf9665c20e6af
- SHA match: yes/no
- Diff files vs Phase 5: (1 file — docs/steps/07-stage-7-auth-workspace.md)
- workspace.ts has workspaceMember check: yes/no
- resolveWorkspace in strategies.ts: yes/no
- resolveWorkspace in runs.ts: yes/no
- resolveWorkspace in lab.ts: yes/no
- stop-all has authenticate: yes/no
- Phase 5 files present (lab/test/page.tsx, lab/build/page.tsx): yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed (with error)
- WorkspaceMember @@unique in schema: yes/no
- TypeScript API (tsc --noEmit): 0 errors / N errors (list if any)
- TypeScript Web (tsc --noEmit): 0 errors / N errors (list if any)
- API build (dist/server.js): success / failed (with error)
- next build: success / failed (with error)
- /lab/test in build output: yes/no
- resolveWorkspace in API dist bundle: yes/no
- BacktestForm in frontend bundle (Phase 5): yes/no
- graph-compiler in bundle (Phase 4): yes/no
- validateGraph in bundle (Phase 3C): yes/no

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed
- API process running after restart: yes / no
- Web process running after restart: yes / no

**5. Security Smoke Tests (Stage 7)**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /strategies (no auth) | 401 | ? | |
| GET /strategies TOKEN_A → WS_B (cross-workspace) | 403 | ? | |
| GET /strategies TOKEN_A → WS_A (own workspace) | 200 | ? | |
| GET /strategies TOKEN_B → WS_A (cross-workspace) | 403 | ? | |
| GET /strategies TOKEN_B → WS_B (own workspace) | 200 | ? | |
| POST /runs/stop-all (no auth) | 401 | ? | |
| POST /runs/stop-all TOKEN_A → WS_B | 403 | ? | |
| GET /bots (no auth) | 401 | ? | |
| GET /bots TOKEN_A → WS_B | 403 | ? | |
| GET /bots TOKEN_A → WS_A | 200 | ? | |
| GET /lab/graphs (no auth) | 401 | ? | |
| GET /lab/graphs TOKEN_A → WS_B | 403 | ? | |
| GET /lab/graphs TOKEN_A → WS_A | 200 | ? | |
| Logs contain userId + workspaceId | present | ? | |
| Logs contain passwordHash/JWT/secrets | absent | ? | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab/test HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| API health check | {"status":"ok"} | ? | |
| GET /lab/strategy-versions (no auth) | 401 | ? | |
| POST /lab/backtest (no auth) | 401 | ? | |
| GET /lab/datasets (no auth) | 401 | ? | |
| GET /exchanges (no auth) | 401 | ? | |
| GET /terminal/ticker?symbol=BTCUSDT | 200 | ? | |

**7. Final Judgment**
- Stage 7 successfully deployed: yes / no
- All security smoke tests passed: yes / no
- Any 403 failures on legitimate own-workspace access: yes / no (should be NO)
- Any 200/success on cross-workspace access: yes / no (should be NO)
- Logs safe (no secrets): yes / no
- Phase 5 regression: none / (describe if any)
- API health: ok / degraded
- Ready to proceed to Stage 8: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Stage 7.
```
