# VPS Deploy Prompt — Issue #123 (Strategy Capability Matrix & Drift Contract Tests)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Issue #123 — Strategy Capability Matrix & UI/Compiler Drift Contract Tests.
Это часть Sprint 1 roadmap (#120). Затрагивает только backend API (compiler module) и docs.
Нет Prisma миграций, нет новых npm-пакетов, нет изменений фронтенда.

### Что такое Issue #123

Issue #123 добавляет drift-detection инфраструктуру между UI block library и backend compiler:
- `BLOCK_SUPPORT_MAP` (apps/api/src/lib/compiler/supportMap.ts) — авторитативный реестр support-статусов для всех 17 UI-блоков (supported / compile-only / unsupported)
- 11 contract tests (apps/api/tests/compiler/blockDrift.test.ts) — автоматически детектируют расхождения между blockDefs.ts (UI) и compiler registry (backend)
- Capability matrix документ (docs/strategies/08-strategy-capability-matrix.md) — human-readable companion к supportMap
- Re-export supportMap через compiler index.ts

**Изменённые файлы:**
| Файл | Описание |
|------|----------|
| `apps/api/src/lib/compiler/supportMap.ts` | Новый: BLOCK_SUPPORT_MAP с support-статусами всех 17 блоков |
| `apps/api/src/lib/compiler/index.ts` | Добавлен re-export supportMap и типов |
| `apps/api/tests/compiler/blockDrift.test.ts` | Новый: 11 contract tests для drift detection |
| `docs/strategies/08-strategy-capability-matrix.md` | Новый: capability matrix документ |

Issue #123 НЕ содержит:
- Prisma миграций
- Новых npm пакетов
- Изменений фронтенда
- Новых block handlers (DSL v2 — это #124)
- UI индикаторов unsupported статуса (это #125)
- Изменений runtime/backtest поведения

### Ветка для деплоя

Branch: `main`
Merge commit SHA: `979c2c6151a5978ec0ae45fd6e277e234460ab38`
Базируется на: `b203241` (Issue #122 — block registry architecture)
Commit message: `feat(api): strategy capability matrix & drift contract tests (#123)`

---

## Задача: задеплоить Issue #123 на VPS

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

# Stage-specific: проверить что #122 (block registry) на месте
test -f apps/api/src/lib/compiler/blockRegistry.ts && echo "#122 blockRegistry.ts present" || echo "MISSING blockRegistry.ts"
test -f apps/api/src/lib/compiler/blockHandlers.ts && echo "#122 blockHandlers.ts present" || echo "MISSING blockHandlers.ts"
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Issue #123

```bash
git fetch origin main
git checkout main
git pull origin main
git log --oneline -3
```

Убедись что HEAD содержит нужный коммит:
```bash
git rev-parse HEAD
# Ожидается SHA: 979c2c6151a5978ec0ae45fd6e277e234460ab38
```

Если SHA отличается:
```bash
git log --oneline --all | grep -i "capability\|drift\|123"
```

Проверь diff относительно предыдущего Issue #122:
```bash
git diff --name-only b203241..HEAD
```
Ожидаемый результат:
```
apps/api/src/lib/compiler/index.ts
apps/api/src/lib/compiler/supportMap.ts
apps/api/tests/compiler/blockDrift.test.ts
docs/strategies/08-strategy-capability-matrix.md
```

Проверь ключевые файлы на месте:
```bash
test -f apps/api/src/lib/compiler/supportMap.ts && echo "supportMap.ts OK" || echo "MISSING supportMap.ts"
test -f apps/api/tests/compiler/blockDrift.test.ts && echo "blockDrift.test.ts OK" || echo "MISSING blockDrift.test.ts"
test -f docs/strategies/08-strategy-capability-matrix.md && echo "capability-matrix.md OK" || echo "MISSING capability-matrix.md"
grep -q "BLOCK_SUPPORT_MAP" apps/api/src/lib/compiler/index.ts && echo "supportMap re-export OK" || echo "MISSING re-export"
```

Проверь что предыдущие Issue файлы не потеряны:
```bash
test -f apps/api/src/lib/compiler/blockRegistry.ts && echo "#122 OK" || echo "#122 MISSING"
test -f apps/api/src/lib/compiler/blockHandlers.ts && echo "#122 OK" || echo "#122 MISSING"
test -f apps/api/tests/lib/blockRegistry.test.ts && echo "#121/#122 tests OK" || echo "MISSING"
```

---

### ШАГ 2 — Установка зависимостей

Issue #123 не добавляет новых npm пакетов:
```bash
pnpm install --frozen-lockfile
```

Если завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma generate

Issue #123 не содержит Prisma миграций. Только пересборка клиента:
```bash
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

---

### ШАГ 4 — Тесты (КЛЮЧЕВОЙ ШАГ для #123)

Поскольку Issue #123 — это contract tests, запуск тестов является основной валидацией.

**4.1 — Все API тесты:**
```bash
pnpm --filter @botmarketplace/api test 2>&1
```
Ожидаемый результат: **65 tests passed** (54 existing + 11 new drift tests), 0 failed.

**4.2 — Contract tests отдельно (verbose):**
```bash
cd apps/api && pnpm exec vitest run tests/compiler/blockDrift.test.ts --reporter=verbose 2>&1
cd ../..
```
Ожидаемый результат: 11 tests passed:
- UI → Compiler contract (2 tests)
- Compiler → UI contract (1 test)
- Support map completeness (4 tests)
- Category consistency (1 test)
- Support status snapshot (3 tests)

Если тесты падают — зафиксируй полный вывод и ОСТАНОВИСЬ. Это критично.

---

### ШАГ 5 — Production builds

**5.1 — API build:**
```bash
pnpm build:api 2>&1
```
Примечание: `tsc` выдаст TS6059 ошибки для test файлов (rootDir vs include — pre-existing issue).
Это НЕ блокирует деплой, т.к. production runtime использует `dist/server.js`.

Проверь артефакт:
```bash
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

Если `dist/server.js` уже существует от предыдущего деплоя и не изменился — это нормально.
supportMap.ts — test/compile-time only, не влияет на runtime bundle.

**5.2 — Web build (Next.js):**
```bash
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, нет `Error:` / `Failed to compile`.

---

### ШАГ 6 — Проверка bundle

**6.1 — Артефакты #123 в source (test-time only, не в dist):**
```bash
grep -r "BLOCK_SUPPORT_MAP" apps/api/src/lib/compiler/ --include="*.ts" -l 2>/dev/null | head -3
# Ожидается: supportMap.ts и index.ts
```

**6.2 — Регрессия #122 (block registry в bundle):**
```bash
grep -r "BlockRegistry" apps/api/src/lib/compiler/ --include="*.ts" -l 2>/dev/null | head -3
# Ожидается: blockRegistry.ts и index.ts
```

---

### ШАГ 7 — Перезапуск сервисов

Issue #123 добавляет только compile-time/test-time код (supportMap + tests + docs).
Runtime behavior API не меняется. Перезапуск нужен только если делался build.

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

### ШАГ 9 — Smoke Tests: Issue #123 (ОБЯЗАТЕЛЬНО)

Issue #123 не добавляет новых API endpoints или UI страниц.
Основная валидация — это ШАГ 4 (тесты). Но проверим что ничего не сломалось:

**9.1 — Compiler module загружается без ошибок:**
```bash
cd apps/api && node -e "
const m = require('./dist/lib/compiler/index.js');
console.log('compileGraph:', typeof m.compileGraph);
console.log('BLOCK_SUPPORT_MAP:', typeof m.BLOCK_SUPPORT_MAP);
console.log('Support map keys:', m.BLOCK_SUPPORT_MAP ? Object.keys(m.BLOCK_SUPPORT_MAP).length : 'N/A');
" 2>&1 || echo "Module load check skipped (ESM or dist not updated)"
cd ..
```
Примечание: если проект использует ESM и dist не пересобран, этот тест может быть пропущен — это нормально, т.к. supportMap — test-time dependency.

**9.2 — Capability matrix документ на месте и непустой:**
```bash
wc -l docs/strategies/08-strategy-capability-matrix.md
# Ожидается: ~109 строк
head -5 docs/strategies/08-strategy-capability-matrix.md
# Ожидается: "# Strategy Capability Matrix"
```

**9.3 — Support map source содержит все 17 блоков:**
```bash
grep -c "status:" apps/api/src/lib/compiler/supportMap.ts
# Ожидается: 17
```

**9.4 — Повторный запуск contract tests (финальная проверка):**
```bash
cd apps/api && pnpm exec vitest run tests/compiler/blockDrift.test.ts 2>&1
cd ../..
# Ожидается: 11 tests passed, 0 failed
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
```

---

### ШАГ 12 — Финальная git проверка

```bash
git log --oneline b203241..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `capability matrix` или `drift contract tests` или `#123`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов вне scope Issue #123
- НЕ реализовывать DSL v2 (#124) или UI индикаторы (#125)
- НЕ добавлять новые block handlers только ради закрытия drift
- НЕ исправлять pre-existing TS6059 ошибки (rootDir issue) — только репортировать
- НЕ делать merge или rebase
- НЕ менять runtime/backtest behavior

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Issue #123 (Strategy Capability Matrix & Drift Contract Tests)

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no
- #122 blockRegistry.ts present: yes/no
- #122 blockHandlers.ts present: yes/no

**2. Branch & Commit**
- Branch deployed: main
- HEAD SHA:
- Expected SHA: 979c2c6151a5978ec0ae45fd6e277e234460ab38
- SHA match: yes/no
- Diff files vs #122: (list)
- supportMap.ts present: yes/no
- blockDrift.test.ts present: yes/no
- capability-matrix.md present: yes/no
- supportMap re-export in index.ts: yes/no

**3. Build & Test Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed
- API tests (all): 65 passed / N passed / failed
- Contract tests (blockDrift): 11 passed / N passed / failed
- API build (dist/server.js): success / failed / skipped (pre-existing)
- next build: success / failed
- TS6059 pre-existing errors: yes/no (expected: yes — not a blocker)

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed / skipped
- API process running: yes/no
- Web process running: yes/no

**5. Smoke Tests — Issue #123**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| Contract tests (11 total) | 11 passed | ? | |
| Capability matrix doc exists | ~109 lines | ? | |
| Support map has 17 entries | 17 | ? | |
| Compiler module loads | OK | ? | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| Auth /me (no auth) | 401 | ? | |
| Terminal ticker | 200 | ? | |
| No crash logs | empty | ? | |
| No secrets in logs | empty | ? | |

**7. Final Judgment**
- Issue #123 successfully deployed: yes / no
- All contract tests passed: yes / no
- All smoke tests passed: yes / no
- Logs safe (no secrets): yes / no
- Regression from previous Issues: none / (describe)
- API health: ok / degraded
- Ready to proceed to Issue #124: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя Issue #123.
```
