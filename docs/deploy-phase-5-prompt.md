# VPS Deploy Prompt — Phase 5 (Backtest Integration)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 5 — Backtest integration with explicit dataset + strategy version binding.
Phase 5 затрагивает бекенд (API + Prisma миграция) и фронтенд (/lab/test).

### Что такое Phase 5

Phase 5 — десятая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md §Phase 5, PR 12–13).
Базируется на Phase 4 (Graph-to-DSL compiler). Реализует полноценный backtest-раннер
с явным биндингом датасета и конкретной версии стратегии (воспроизводимые бектесты).

**Изменённые файлы (ровно 4):**
- `apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql`
  — аддитивная миграция: nullable FK-колонка `strategyVersionId` на `BacktestResult`,
    FK constraint ON DELETE SET NULL + индекс. Без breaking changes.
- `apps/api/prisma/schema.prisma`
  — поле `strategyVersionId String?` в модели `BacktestResult`;
    обратная relation `backtestResults BacktestResult[]` в `StrategyVersion`.
- `apps/api/src/routes/lab.ts`
  — НОВЫЙ endpoint `GET /lab/strategy-versions` — список версий стратегий воркспейса;
  — ИЗМЕНЁН контракт `POST /lab/backtest`: `strategyId` → `strategyVersionId` (обязательный);
  — `runBacktestAsync` использует явный `strategyVersionId` для поиска DSL;
  — `BACKTEST_SELECT` включает поле `strategyVersionId`.
- `apps/web/src/app/lab/test/page.tsx`
  — полная реализация Test tab (Phase 5A + 5B): `BacktestForm` (выбор StrategyVersion +
    Dataset + feeBps + slippageBps + fillAt), polling каждые 2 сек, `StatusBadge`
    (PENDING/RUNNING/DONE/FAILED), `DatasetSnapshotBlock` (§6.5), `MetricsTab`,
    `TradesTab`, `EquityTab` (lightweight-charts), `LogsTab`, `ResultDetail`.

Phase 5 НЕ содержит:
- изменений graph-редактора (build/data вкладки, Phase 3/4 файлы)
- новых npm пакетов (lightweight-charts уже добавлен в Phase 2B)
- Phase 6 функционала

### Ветка для деплоя

Branch: `main`
Commit SHA: `9258f917fb3316671becc65fe1d62288d08b908f`
Базируется на Phase 4 SHA: `a3660fb6535a7a1cd02707169c654f510be484f3`
Commit message: `feat(lab): Phase 5 — Backtest integration with explicit dataset + strategy version binding`

---

## Задача: задеплоить Phase 5 на VPS

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

### ШАГ 1 — Получить Phase 5

```
git fetch origin main
git checkout main
git pull origin main
git log --oneline -3
```

Убедись, что HEAD содержит коммит:
`feat(lab): Phase 5 — Backtest integration with explicit dataset + strategy version binding`

Проверь SHA:
```
git rev-parse HEAD
```
Ожидается: `9258f917fb3316671becc65fe1d62288d08b908f`

Проверь diff относительно Phase 4 (должно быть ровно 4 файла):
```
git diff --name-only a3660fb6535a7a1cd02707169c654f510be484f3..HEAD
```

Ожидаемый результат:
```
apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql
apps/api/prisma/schema.prisma
apps/api/src/routes/lab.ts
apps/web/src/app/lab/test/page.tsx
```

Если в diff есть что-то кроме этих 4 файлов — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 4 файлы не потеряны:
```
test -f apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql \
  && echo "migration OK"    || echo "MISSING migration.sql"
test -f apps/web/src/app/lab/build/page.tsx          && echo "build page OK"    || echo "MISSING build page"
test -f apps/web/src/app/lab/validationTypes.ts      && echo "validTypes OK"    || echo "MISSING validationTypes"
test -f apps/web/src/app/lab/build/nodes/StrategyNode.tsx && echo "StrategyNode OK" || echo "MISSING StrategyNode"
```

Проверь, что Phase 2A/2B/2C файлы не потеряны:
```
test -f apps/web/src/app/lab/DatasetPreview.tsx  && echo "DatasetPreview OK" || echo "MISSING DatasetPreview"
test -f apps/web/src/app/lab/useLabGraphStore.ts && echo "store OK"          || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx          && echo "layout OK"         || echo "MISSING layout"
test -f apps/web/src/app/lab/data/page.tsx       && echo "data page OK"      || echo "MISSING data page"
```

---

### ШАГ 2 — Установка зависимостей

Phase 5 не добавляет новых npm пакетов:

```
pnpm install --frozen-lockfile
```

Проверь ключевые зависимости:
```
test -d apps/web/node_modules/lightweight-charts && echo "lightweight-charts OK" || echo "MISSING lightweight-charts"
test -d apps/web/node_modules/@xyflow/react      && echo "@xyflow/react OK"      || echo "MISSING @xyflow/react"
test -d node_modules/.pnpm | grep -q zundo       && echo "zundo OK"              || echo "check zundo manually"
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma: generate + migrate

**3.1 — Пересборка Prisma Client (schema изменился):**
```
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

**3.2 — Применить миграцию:**
```
pnpm db:migrate
```
Ожидаемый результат:
- exit code 0
- В выводе упоминается `20260309b_phase5_backtest_version_binding`
- `1 migration applied` или `All migrations have been applied`

Если миграция завершилась с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.
Не применяй SQL вручную — только через `pnpm db:migrate`.

**3.3 — Проверка статуса миграций:**
```
pnpm --filter @botmarketplace/api exec prisma migrate status 2>&1 | tail -10
```
Ожидается: pending count = 0.

**3.4 — Проверка новой колонки в БД:**
```
pnpm --filter @botmarketplace/api exec prisma db execute --stdin <<'SQL'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'BacktestResult' AND column_name = 'strategyVersionId';
SQL
```
Ожидается: строка с `strategyVersionId`, тип `text`, nullable `YES`.
Если колонка не найдена — миграция не применилась, ОСТАНОВИСЬ.

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
Ожидаемый результат: exit code 0, в `apps/api/dist/` появился `server.js`.

Проверь:
```
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**5.2 — Web build (Next.js):**
```
pnpm build:web 2>&1
```
Ожидаемый результат:
- exit code 0, нет `Error:` / `Failed to compile`
- Все 4 lab маршрута присутствуют в выводе

Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если любой build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 6 — Проверка bundle содержимого

**6.1 — BacktestForm + strategyVersionId в bundle:**
```
grep -r "BacktestForm\|strategyVersionId\|POLL_INTERVAL_MS" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.2 — DatasetSnapshotBlock в bundle (§6.5):**
```
grep -r "DatasetSnapshotBlock\|Dataset Snapshot\|datasetHash" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.3 — Вкладки результатов в bundle:**
```
grep -r "MetricsTab\|TradesTab\|EquityTab\|LogsTab\|ResultDetail" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.4 — StatusBadge + polling в bundle:**
```
grep -r "StatusBadge\|PENDING\|RUNNING\|DONE\|FAILED" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.5 — Phase 4 не сломана (graph-compiler в bundle):**
```
grep -r "graphToDSL\|compiledDsl\|StrategyGraphVersion" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.6 — Phase 3C не сломана (validateGraph в bundle):**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph\|ValidationDrawer" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.7 — Phase 2C не сломана (QualitySummary в bundle):**
```
grep -r "qualitySectionStyle\|All clear\|Unusable" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.8 — Phase 2B не сломана (DatasetPreview + lightweight-charts в bundle):**
```
grep -r "DatasetPreview\|lightweight-charts" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

---

### ШАГ 7 — Перезапуск сервисов

Phase 5 меняет API — необходимо перезапустить оба сервиса (API и Web).

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

### ШАГ 8 — Smoke Tests

Это обязательные проверки после деплоя. Выполни все.

**8.1 HTTP: /lab/test возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`

**8.2 HTTP: /lab/build возвращает 200 (Phase 4 не сломана)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
```
Ожидается: `200`

**8.3 HTTP: /lab/data возвращает 200 (Phase 2A/2C не сломана)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/data
```
Ожидается: `200`

**8.4 HTTP: /lab возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**8.5 API: новый endpoint GET /api/v1/lab/strategy-versions доступен (401, не 404)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/strategy-versions \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`. Если `404` — endpoint не зарегистрирован, это критическая ошибка.

**8.6 API: POST /api/v1/lab/backtest доступен (401, не 404)**
```
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:4000/api/v1/lab/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token" \
  -d '{"strategyVersionId":"x","datasetId":"y"}'
```
Ожидается: `401`. Если `404` — endpoint исчез, это критическая ошибка.

**8.7 API: GET /api/v1/lab/datasets по-прежнему работает (Phase 2A не сломана)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.

**8.8 API: GET /api/v1/lab/backtest по-прежнему работает**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/backtest \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.

**8.9 API health check**
```
curl -s http://localhost:4000/api/v1/healthz 2>/dev/null || \
curl -s http://localhost:4000/health 2>/dev/null         || \
echo "API health endpoint N/A"
```
Ожидается: `{"status":"ok"}`.

**8.10 BacktestForm в bundle**
```
grep -r "BacktestForm\|strategyVersionId\|POLL_INTERVAL_MS" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.11 DatasetSnapshotBlock в bundle**
```
grep -r "DatasetSnapshotBlock\|Dataset Snapshot" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.12 Вкладки результатов в bundle**
```
grep -r "MetricsTab\|TradesTab\|EquityTab\|ResultDetail" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.13 Phase 4 регрессия: graph-compiler на месте**
```
grep -r "graphToDSL\|compiledDsl" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.14 Phase 3C регрессия: validateGraph на месте**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.15 Phase 2C регрессия: QualitySummary на месте**
```
grep -r "qualitySectionStyle\|toggleBtnStyle" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**8.16 Статус миграции**
```
pnpm --filter @botmarketplace/api exec prisma migrate status 2>&1 | grep -E "applied|pending|phase5"
```
Ожидается: `20260309b_phase5_backtest_version_binding` со статусом applied, pending = 0.

**8.17 strategyVersionId колонка в БД**
```
pnpm --filter @botmarketplace/api exec prisma db execute --stdin <<'SQL'
SELECT column_name FROM information_schema.columns
WHERE table_name = 'BacktestResult' AND column_name = 'strategyVersionId';
SQL
```
Ожидается: одна строка `strategyVersionId`. Если пусто — миграция не применилась.

---

### ШАГ 9 — Финальная git проверка

```
git log --oneline a3660fb6535a7a1cd02707169c654f510be484f3..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 5 файлов
- НЕ реализовывать Phase 6 (private data, compare runs, stale-state)
- НЕ делать merge или rebase
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ применять SQL вручную — только через `pnpm db:migrate`
- НЕ изменять Prisma schema
- НЕ создавать новые API endpoints

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 5

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
- Expected SHA: 9258f917fb3316671becc65fe1d62288d08b908f
- SHA match: yes/no
- Diff files count vs Phase 4: (must be 4)
- Files in diff: (list them)
- migration.sql present: yes/no
- test/page.tsx present: yes/no
- build/page.tsx present (Phase 4): yes/no
- validationTypes.ts present (Phase 3C): yes/no
- DatasetPreview.tsx present (Phase 2B): yes/no
- lightweight-charts in node_modules: yes/no
- @xyflow/react in node_modules: yes/no

**3. Build & Migration Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed (with error)
- db:migrate: success / failed (with error)
- Migration applied (20260309b): yes/no
- strategyVersionId column in DB: yes/no
- TypeScript API (tsc --noEmit): 0 errors / N errors (list if any)
- TypeScript Web (tsc --noEmit): 0 errors / N errors (list if any)
- API build (dist/server.js): success / failed (with error)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/build in build output: yes/no + size (kB)
- /lab/data in build output: yes/no
- /lab/test in build output: yes/no + size (kB)
- BacktestForm in bundle: yes/no
- DatasetSnapshotBlock in bundle: yes/no
- MetricsTab/TradesTab/EquityTab in bundle: yes/no
- graph-compiler in bundle (Phase 4): yes/no
- validateGraph in bundle (Phase 3C): yes/no
- QualitySummary in bundle (Phase 2C): yes/no
- DatasetPreview in bundle (Phase 2B): yes/no

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed
- API process running after restart: yes / no
- Web process running after restart: yes / no

**5. Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab/test HTTP status | 200 | ? | |
| GET /lab/build HTTP status | 200 | ? | |
| GET /lab/data HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /api/v1/lab/strategy-versions (no auth) | 401 | ? | |
| POST /api/v1/lab/backtest (no auth) | 401 | ? | |
| GET /api/v1/lab/datasets (no auth) | 401 | ? | |
| GET /api/v1/lab/backtest (no auth) | 401 | ? | |
| API health check | {"status":"ok"} | ? | |
| BacktestForm in bundle | file found | ? | |
| DatasetSnapshotBlock in bundle | file found | ? | |
| MetricsTab/TradesTab/EquityTab in bundle | file found | ? | |
| graph-compiler in bundle (Phase 4) | file found | ? | |
| validateGraph in bundle (Phase 3C) | file found | ? | |
| QualitySummary in bundle (Phase 2C) | file found | ? | |
| Migration 20260309b applied | applied | ? | |
| strategyVersionId column in DB | present | ? | |

**6. Final Judgment**
- Phase 5 successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- Backtest form on /lab/test: yes / no
- Strategy version selector functional: yes / no
- Dataset selector functional: yes / no
- Polling (2s) for active backtests: yes / no
- MetricsTab functional: yes / no
- TradesTab functional: yes / no
- EquityTab (lightweight-charts): yes / no
- DatasetSnapshotBlock functional (§6.5): yes / no
- GET /lab/strategy-versions endpoint active: yes / no
- POST /lab/backtest accepts strategyVersionId: yes / no
- strategyVersionId column in BacktestResult: yes / no
- Graph editor (Phase 4) operational: yes / no
- Validation UI (Phase 3C) operational: yes / no
- Dataset Builder (Phase 2A) operational: yes / no
- Preview (Phase 2B) operational: yes / no
- Quality summary (Phase 2C) operational: yes / no
- Ready for Phase 6 development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 5.
```
