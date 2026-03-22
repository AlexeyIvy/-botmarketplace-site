# VPS Deploy Prompt — Issue #128 (Runtime Signal/Exit Engine from Compiled DSL)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Issue #128 — Runtime Signal/Exit Engine from Compiled DSL.
Это комплексный PR, включающий два issue: #127 (Position domain + Prisma миграция) и #128 (signalEngine, exitEngine, riskManager, botWorker). Затрагивает backend API: новая Prisma миграция, новые runtime-движки, новые REST endpoints для позиций. Нет изменений фронтенда, нет новых npm-пакетов.

### Что такое Issue #128

Issue #128 добавляет runtime-движок для исполнения стратегий из DSL в реальном времени:
- Новый `signalEngine.ts` — pure-function evaluator: читает compiled DSL, оценивает entry conditions по текущим свечам, генерирует OpenSignal или null
- Новый `exitEngine.ts` — runtime exit evaluator: SL, TP, trailing_stop, indicator_exit, time_exit. Приоритет: SL → trailing → indicator → TP → time (совпадает с backtest)
- Новый `riskManager.ts` — минимальный sizing и eligibility layer: position sizing, cooldown, max open positions
- Обновлённый `botWorker.ts` — runtime loop интеграция с signal/exit engines
- Issue #127 (Position domain): новые Prisma модели Position + PositionEvent, positionManager.ts, новые REST endpoints в bots.ts

**Изменённые файлы:**
| Файл | Описание |
|------|----------|
| `apps/api/prisma/schema.prisma` | Новые модели: Position, PositionEvent + enums |
| `apps/api/prisma/migrations/20260322a_stage3_position_domain/migration.sql` | Prisma миграция: Position + PositionEvent таблицы |
| `apps/api/src/lib/signalEngine.ts` | Новый: runtime entry signal evaluator |
| `apps/api/src/lib/exitEngine.ts` | Новый: runtime exit condition evaluator |
| `apps/api/src/lib/riskManager.ts` | Новый: sizing + eligibility layer |
| `apps/api/src/lib/botWorker.ts` | Обновлён: интеграция runtime engines |
| `apps/api/src/lib/dslEvaluator.ts` | Обновлён: рефакторинг shared primitives |
| `apps/api/src/lib/positionManager.ts` | Новый: Position domain CRUD + snapshot |
| `apps/api/src/routes/bots.ts` | Обновлён: GET /bots/:id/positions, GET /bots/:id/positions/:positionId/events, activePosition в GET /bots/:id |
| `apps/api/tests/lib/signalEngine.test.ts` | Новый: тесты signal engine |
| `apps/api/tests/lib/exitEngine.test.ts` | Новый: тесты exit engine |
| `apps/api/tests/lib/riskManager.test.ts` | Новый: тесты risk manager |
| `apps/api/tests/lib/runtimeReplay.test.ts` | Новый: integration replay тест |
| `apps/api/tests/lib/positionManager.test.ts` | Новый: тесты position manager |

**Prisma миграция:** `20260322a_stage3_position_domain` — аддитивная. Создаёт таблицы Position, PositionEvent и enums PositionSide, PositionStatus, PositionEventType.

Issue #128 НЕ содержит:
- Изменений фронтенда
- Новых npm пакетов
- Exchange API интеграции (#129 — отдельный issue)
- DCA/multi-position support
- Worker cron/scheduler setup

### Зависимости

Issue #128 базируется на:
- #126 (DSL-driven backtest evaluator) — shared evaluation primitives
- #125 (indicator engine) — VWAP, ADX, SuperTrend в signal/exit evaluation
- #124 (DSL v2 spec) — exit rules, dual-side entry

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `1e89c0c582e4fa221c7e40c60b86576e87a0cf09`
Базируется на: `d25ad64` (Issue #126 deploy prompt)
Commit message: `Merge PR #153: runtime signal/exit engine from compiled DSL (#128)`

---

## Задача: задеплоить Issue #128 на VPS

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
test -f .env && echo "root .env exists" || echo "no root .env"
test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"

# PostgreSQL
pg_isready 2>/dev/null && echo "pg ready" || echo "pg_isready N/A"

# Stage-specific: проверка что предыдущий deploy (#126) на месте
grep -n "parseDsl" apps/api/src/lib/dslEvaluator.ts | head -3
# Ожидается: функция parseDsl существует

test -f apps/api/src/lib/dslEvaluator.ts && echo "dslEvaluator OK" || echo "MISSING dslEvaluator"
test -f apps/api/src/lib/backtest.ts && echo "backtest OK" || echo "MISSING backtest"
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Issue #128

```bash
git fetch origin main
git checkout main
git pull origin main
git log --oneline -5
```

Убедись что HEAD содержит нужный коммит:
```bash
git rev-parse HEAD
# Ожидается SHA: 1e89c0c582e4fa221c7e40c60b86576e87a0cf09
```

Если SHA отличается:
```bash
git log --oneline --all | grep -i "signal\|exit.*engine\|#128"
```

Проверь diff относительно предыдущего деплоя:
```bash
git diff --name-only d25ad64..HEAD
```
Ожидаемый результат:
```
apps/api/prisma/migrations/20260322a_stage3_position_domain/migration.sql
apps/api/prisma/schema.prisma
apps/api/src/lib/botWorker.ts
apps/api/src/lib/dslEvaluator.ts
apps/api/src/lib/exitEngine.ts
apps/api/src/lib/positionManager.ts
apps/api/src/lib/riskManager.ts
apps/api/src/lib/signalEngine.ts
apps/api/src/routes/bots.ts
apps/api/tests/lib/exitEngine.test.ts
apps/api/tests/lib/positionManager.test.ts
apps/api/tests/lib/riskManager.test.ts
apps/api/tests/lib/runtimeReplay.test.ts
apps/api/tests/lib/signalEngine.test.ts
```

Проверь ключевые файлы на месте:
```bash
test -f apps/api/src/lib/signalEngine.ts && echo "signalEngine OK" || echo "MISSING"
test -f apps/api/src/lib/exitEngine.ts && echo "exitEngine OK" || echo "MISSING"
test -f apps/api/src/lib/riskManager.ts && echo "riskManager OK" || echo "MISSING"
test -f apps/api/src/lib/positionManager.ts && echo "positionManager OK" || echo "MISSING"
test -f apps/api/prisma/migrations/20260322a_stage3_position_domain/migration.sql && echo "migration OK" || echo "MISSING"
```

Проверь что предыдущие Stage файлы не потеряны:
```bash
test -f apps/api/src/lib/dslEvaluator.ts && echo "dslEvaluator OK" || echo "MISSING"
test -f apps/api/src/lib/backtest.ts && echo "backtest OK" || echo "MISSING"
test -f apps/api/src/lib/compiler/supportMap.ts && echo "supportMap OK" || echo "MISSING"
```

---

### ШАГ 2 — Установка зависимостей

Issue #128 не добавляет новых npm пакетов:
```bash
pnpm install --frozen-lockfile
```

Если завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma миграция

```bash
pnpm db:migrate
```
Ожидаемый результат: `20260322a_stage3_position_domain` применена, exit code 0.

Проверь применение:
```bash
pnpm db:generate
grep -n "model Position" apps/api/prisma/schema.prisma
grep -n "model PositionEvent" apps/api/prisma/schema.prisma
grep -n "PositionSide" apps/api/prisma/schema.prisma
```
Ожидается: модели Position, PositionEvent и enum PositionSide найдены в schema.

Если миграция упала — ОСТАНОВИСЬ. Не применяй SQL вручную.

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

### ШАГ 5 — Юнит-тесты (ОБЯЗАТЕЛЬНО)

```bash
pnpm test:api 2>&1
```
Ожидаемый результат: все тесты проходят, exit code 0.

Ключевые тест-файлы Issue #128:
- `tests/lib/signalEngine.test.ts`
- `tests/lib/exitEngine.test.ts`
- `tests/lib/riskManager.test.ts`
- `tests/lib/runtimeReplay.test.ts`
- `tests/lib/positionManager.test.ts`

Если тесты падают — зафиксируй полный вывод и ОСТАНОВИСЬ.

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
○ /factory
```

Если любой build упал — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 7 — Проверка bundle

**7.1 — Артефакты Issue #128 в bundle:**
```bash
grep -r "signalEngine\|SignalEngine\|evaluateSignal" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл

grep -r "exitEngine\|ExitEngine\|evaluateExits" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл

grep -r "riskManager\|RiskManager\|checkEligibility\|computeQty" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл

grep -r "positionManager\|listBotPositions\|getActiveBotPosition" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

**7.2 — Регрессия предыдущего Stage (#126):**
```bash
grep -r "dslEvaluator\|parseDsl\|evaluateDsl" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

---

### ШАГ 8 — Перезапуск сервисов

Нужно перезапустить оба сервиса (есть Prisma миграция + изменения backend).

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

**9.3 Web: предыдущие страницы не сломаны:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
# Ожидается: 200

curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/factory
# Ожидается: 200
```

---

### ШАГ 10 — Smoke Tests: Issue #128 (ОБЯЗАТЕЛЬНО)

**Подготовка:**
```bash
export BASE=http://localhost:4000/api/v1

# Зарегистрировать тестового пользователя
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_128@test.local","password":"SmokeTest1!"}')
echo "$REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN пустой — попробуй login:
```bash
REG=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_128@test.local","password":"SmokeTest1!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN всё ещё пустой — auth не работает, ОСТАНОВИСЬ.

**10.1 — Создать бота для тестирования позиций:**
```bash
BOT=$(curl -s -X POST $BASE/bots \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke128","symbol":"BTCUSDT","timeframe":"M5","dslJson":"{}"}')
echo "$BOT"
BOT_ID=$(echo "$BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "BOT_ID: $BOT_ID"
```

**10.2 — GET /bots/:id возвращает activePosition (null допустим):**
```bash
S2=$(curl -s $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 10.2 (GET bot detail with activePosition): $S2"
echo "$S2" | grep -o '"activePosition"' && echo "activePosition field PRESENT" || echo "activePosition field MISSING"
# Ожидается: поле activePosition присутствует (значение null — ок)
```

**10.3 — GET /bots/:id/positions возвращает массив:**
```bash
S3=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/bots/$BOT_ID/positions \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 10.3 (GET positions list) → $S3 (expected: 200)"
```

**10.4 — GET /bots/:id/positions без токена → 401:**
```bash
S4=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/bots/$BOT_ID/positions)
echo "Test 10.4 (no auth → 401) → $S4 (expected: 401)"
```

**10.5 — Cross-workspace → 403:**
```bash
REG_B=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_128_b@test.local","password":"SmokeTest1!"}')
TOKEN_B=$(echo "$REG_B" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_B=$(echo "$REG_B"   | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)

S5=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_B")
echo "Test 10.5 (cross-workspace → 403) → $S5 (expected: 403)"
```

**10.6 — GET /bots/:id/positions/:fakeId/events → 404:**
```bash
S6=$(curl -s -o /dev/null -w "%{http_code}" \
  $BASE/bots/$BOT_ID/positions/nonexistent-id/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 10.6 (position not found → 404) → $S6 (expected: 404)"
```

---

### ШАГ 11 — Проверка логов

**11.1 — Есть userId + workspaceId в логах:**
```bash
LOG=/var/log/botmarket-api.log
if [ -f "$LOG" ]; then
  tail -50 "$LOG" | grep -E "userId|workspaceId" | tail -5
else
  journalctl -u botmarket-api --no-pager -n 30 2>/dev/null | grep -E "userId|workspaceId" | tail -5 || true
  pm2 logs api --lines 30 --nostream 2>/dev/null | grep -E "userId|workspaceId" | tail -5 || true
fi
# Ожидается: строки с userId и workspaceId
```

**11.2 — Нет секретов в логах (КРИТИЧНО):**
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

### ШАГ 12 — Regression: предыдущие Stage

```bash
echo "--- Regression: previous Stages ---"

# Auth endpoint (нет auth)
curl -s -o /dev/null -w "%{http_code}" \
  $BASE/bots -H "Authorization: Bearer invalid"
# Ожидается: 401 (не 404)

# API health
curl -s $BASE/healthz | grep -o '"status":"ok"'
# Ожидается: "status":"ok"

# API readyz
curl -s -o /dev/null -w "%{http_code}" $BASE/readyz
# Ожидается: 200

# Public endpoint (если есть)
curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/terminal/ticker?symbol=BTCUSDT"
# Ожидается: 200

# Backtest endpoint (#126) — проверка что не сломан
curl -s -o /dev/null -w "%{http_code}" \
  $BASE/lab/backtest -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" \
  -H "Content-Type: application/json" \
  -d '{"botId":"'$BOT_ID'"}'
# Ожидается: НЕ 404 (может быть 400/422 — ок, endpoint существует)
```

---

### ШАГ 13 — Финальная git проверка

```bash
git log --oneline d25ad64..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `runtime signal/exit engine` или `#128`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов вне scope этого деплоя
- НЕ применять SQL вручную
- НЕ делать задачи следующего Stage (#129 — exchange integration)
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- НЕ настраивать cron/scheduler для botWorker — это вне scope

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Issue #128 (Runtime Signal/Exit Engine)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no
- dslEvaluator.ts present (prev Stage): yes/no
- backtest.ts present (prev Stage): yes/no

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: 1e89c0c582e4fa221c7e40c60b86576e87a0cf09
- SHA match: yes/no
- Diff files vs prev Stage: (list)
- signalEngine.ts present: yes/no
- exitEngine.ts present: yes/no
- riskManager.ts present: yes/no
- positionManager.ts present: yes/no
- Migration file present: yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- db:migrate (20260322a_stage3_position_domain): success / failed
- db:generate: success / failed
- TypeScript API (tsc --noEmit): 0 errors / N errors
- TypeScript Web (tsc --noEmit): 0 errors / N errors
- Unit tests (pnpm test:api): X passed / Y failed
- API build (dist/server.js): success / failed
- next build: success / failed
- signalEngine in bundle: yes/no
- exitEngine in bundle: yes/no
- riskManager in bundle: yes/no
- positionManager in bundle: yes/no
- dslEvaluator in bundle (regression): yes/no

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed
- API process running: yes/no
- Web process running: yes/no

**5. Smoke Tests — Issue #128**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /factory HTTP status | 200 | ? | |
| GET /bots/:id activePosition field | present | ? | |
| GET /bots/:id/positions | 200 | ? | |
| GET /bots/:id/positions (no auth) | 401 | ? | |
| Cross-workspace access | 403 | ? | |
| Position not found | 404 | ? | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| API readyz | 200 | ? | |
| GET /bots invalid auth | 401 | ? | |
| GET /terminal/ticker | 200 | ? | |
| POST /lab/backtest (exists) | not 404 | ? | |

**7. Final Judgment**
- Issue #128 successfully deployed: yes / no
- Prisma migration applied: yes / no
- All unit tests passed: yes / no
- All smoke tests passed: yes / no
- Logs safe (no secrets): yes / no
- Regression from previous Stages: none / (describe)
- API health: ok / degraded
- Ready to proceed to Issue #129 (Exchange Integration): yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя Issue #128.
```
