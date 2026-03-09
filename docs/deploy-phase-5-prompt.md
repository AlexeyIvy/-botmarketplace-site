# VPS Deploy Prompt — Phase 5 (Backtest Integration)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 5 — Backtest Integration with explicit dataset + strategy version binding.
Phase 5 затрагивает бекенд (API + Prisma миграция) и фронтенд (/lab/test).

### Что такое Phase 5

Phase 5 — финальная фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md §16, Phase 5A + 5B).
Базируется на Phase 4 (Graph-to-DSL compiler). Реализует полноценный backtest-раннер
с явным биндингом датасета и конкретной версии стратегии.

**Изменённые файлы (ровно 4):**
- `apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql`
  — новая nullable FK колонка `strategyVersionId` на таблице `BacktestResult`,
    FK constraint + ON DELETE SET NULL, индекс
- `apps/api/prisma/schema.prisma`
  — добавлено поле `strategyVersionId String?` в модель `BacktestResult`;
    обратная relation `backtestResults BacktestResult[]` в `StrategyVersion`
- `apps/api/src/routes/lab.ts`
  — НОВЫЙ endpoint: `GET /lab/strategy-versions` — список скомпилированных версий стратегий воркспейса
  — ИЗМЕНЁН контракт `POST /lab/backtest`: вместо `strategyId` теперь `strategyVersionId` (обязательный)
  — `runBacktestAsync` принимает явный `strategyVersionId`, использует его для поиска DSL
  — `BACKTEST_SELECT` добавлено поле `strategyVersionId`
- `apps/web/src/app/lab/test/page.tsx`
  — полная реализация Test tab (Phase 5A + 5B):
    - `BacktestForm` — форма запуска: выбор StrategyVersion + Dataset + feeBps + slippageBps + fillAt
    - `StatusBadge` — визуальный статус PENDING/RUNNING/DONE/FAILED
    - `DatasetSnapshotBlock` — блок с инфо о датасете (symbol, interval, диапазон, candles, hash) §6.5
    - `MetricsTab` — сводные метрики (trades, winrate, PnL, drawdown)
    - `TradesTab` — таблица всех сделок с outcome и pnlPct
    - `EquityTab` — кривая equity (lightweight-charts, LineData)
    - `LogsTab` — raw JSON лог
    - `ResultDetail` — полный drawer с 4 вкладками
    - polling каждые 2 сек (`POLL_INTERVAL_MS = 2000`) для активных бектестов

Phase 5 НЕ содержит:
- изменений graph-редактора (build, data вкладок)
- изменений Phase 3C/4 файлов (validationTypes, StrategyNode, etc.)
- нового npm пакета — lightweight-charts уже добавлен в Phase 2B
- Phase 6 и следующего функционала

### Ветка и коммит для деплоя

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
   systemctl status botmarket-api 2>/dev/null  || echo "no botmarket-api systemd unit"
   systemctl status botmarket-web 2>/dev/null  || echo "no botmarket-web systemd unit"
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
   pg_isready 2>/dev/null || echo "pg_isready not available"
   ```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Phase 5 ветку

```
git fetch origin main
git checkout main
git pull origin main
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
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

Ожидаемый результат (ровно 4 файла):
```
apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql
apps/api/prisma/schema.prisma
apps/api/src/routes/lab.ts
apps/web/src/app/lab/test/page.tsx
```

Если в diff есть что-то кроме этих 4 файлов — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 4 файлы на месте:
```
test -f apps/api/src/graph-compiler/index.ts     && echo "graph-compiler OK"  || echo "MISSING graph-compiler"
test -f apps/web/src/app/lab/build/page.tsx       && echo "build page OK"      || echo "MISSING build page"
test -f apps/web/src/app/lab/validationTypes.ts   && echo "validationTypes OK" || echo "MISSING validationTypes"
test -f apps/web/src/app/lab/build/nodes/StrategyNode.tsx && echo "StrategyNode OK" || echo "MISSING StrategyNode"
```

Проверь, что Phase 2A/2B/2C файлы не потеряны:
```
test -f apps/web/src/app/lab/DatasetPreview.tsx   && echo "DatasetPreview OK"  || echo "MISSING DatasetPreview"
test -f apps/web/src/app/lab/useLabGraphStore.ts  && echo "store OK"           || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx           && echo "layout OK"          || echo "MISSING layout"
test -f apps/web/src/app/lab/data/page.tsx        && echo "data page OK"       || echo "MISSING data page"
```

Проверь новый migration файл:
```
test -f apps/api/prisma/migrations/20260309b_phase5_backtest_version_binding/migration.sql \
  && echo "migration.sql OK" || echo "MISSING migration.sql"
```

---

### ШАГ 2 — Установка зависимостей

Phase 5 не добавляет новых npm пакетов. Стандартный install:

```
pnpm install
```

Проверь наличие lightweight-charts (из Phase 2B):
```
test -d apps/web/node_modules/lightweight-charts && echo "lightweight-charts OK" || echo "MISSING lightweight-charts"
```

Проверь наличие @xyflow/react (из Phase 3A):
```
test -d apps/web/node_modules/@xyflow/react && echo "@xyflow/react OK" || echo "MISSING @xyflow/react"
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — Prisma client regeneration

После изменений в schema.prisma необходимо пересгенерировать Prisma client:

```
pnpm --filter @botmarketplace/api db:generate
```

Ожидаемый результат: Prisma Client generated successfully (exit code 0).

Если генерация завершилась с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 4 — DB миграция

Phase 5 содержит аддитивную миграцию (nullable FK, без breaking changes):
- Новая nullable колонка `strategyVersionId` в таблице `BacktestResult`
- FK constraint с `ON DELETE SET NULL` на `StrategyVersion`
- Индекс `BacktestResult_strategyVersionId_idx`

```
pnpm --filter @botmarketplace/api db:migrate
```

Ожидаемый результат:
- Команда завершилась с exit code 0
- В выводе: `1 migration applied` или `All migrations have been applied`
- Указание на `20260309b_phase5_backtest_version_binding`

Если миграция завершилась с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.
Не пытайся применять SQL вручную — только через Prisma.

Проверь применение миграции:
```
pnpm --filter @botmarketplace/api exec prisma migrate status 2>&1 | tail -10
```
Ожидается: все миграции applied, pending count = 0.

---

### ШАГ 5 — TypeScript проверка (tsc)

**5.1 — API:**
```
pnpm --filter @botmarketplace/api exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

**5.2 — Web:**
```
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```
Ожидаемый результат: 0 ошибок, exit code 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй TypeScript ошибки самостоятельно — только репортируй.

---

### ШАГ 6 — Production build (Next.js)

```
pnpm build:web 2>&1
```

Ожидаемый результат:
- Build завершился успешно (exit code 0)
- В выводе нет `Error:` или `Failed to compile`
- `/lab/test` присутствует в списке собранных страниц
- Остальные lab маршруты тоже присутствуют

Проверь lab маршруты в выводе билда. Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 7 — Проверка bundle содержимого

**7.1 — BacktestForm в bundle**
```
grep -r "BacktestForm\|strategyVersionId\|POLL_INTERVAL_MS" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.2 — DatasetSnapshotBlock в bundle**
```
grep -r "DatasetSnapshotBlock\|Dataset Snapshot\|datasetHash" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.3 — MetricsTab / TradesTab / EquityTab в bundle**
```
grep -r "MetricsTab\|TradesTab\|EquityTab\|LogsTab\|ResultDetail" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.4 — StatusBadge + polling в bundle**
```
grep -r "StatusBadge\|POLL_INTERVAL_MS\|PENDING\|RUNNING\|DONE\|FAILED" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.5 — lightweight-charts EquityTab в bundle**
```
grep -r "lightweight-charts\|IChartApi\|LineData\|addLineSeries" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.6 — Phase 4 не сломана (graph-compiler в bundle)**
```
grep -r "graphToDSL\|compiledDsl\|StrategyGraphVersion\|graph-compiler" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.7 — Phase 3C не сломана (validationTypes в bundle)**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph\|ValidationDrawer" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.8 — Phase 2B не сломана (DatasetPreview в bundle)**
```
grep -r "DatasetPreview\|lightweight-charts" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

---

### ШАГ 8 — Сборка и перезапуск API

Phase 5 изменяет `apps/api/src/routes/lab.ts` — необходима пересборка API.

```
pnpm build:api 2>&1
```

Если команда `build:api` не существует, попробуй:
```
pnpm --filter @botmarketplace/api build 2>&1
```

Ожидаемый результат: exit code 0.

---

### ШАГ 9 — Перезапуск сервисов

Определи, как запущены сервисы на этом VPS, и перезапусти оба (API и Web).

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
pm2 status

pm2 restart web
sleep 5
pm2 status
pm2 logs web --lines 30 --nostream
pm2 logs api --lines 30 --nostream
```

**Вариант C — ручной запуск (если нет systemd/pm2):**
```
pkill -f "next start" || true
pkill -f "node.*api" || true
sleep 2

# Запуск API
cd apps/api && nohup node dist/index.js >> /var/log/botmarket-api.log 2>&1 &
echo "API PID: $!"

# Запуск Web
cd apps/web && nohup pnpm start >> /var/log/botmarket-web.log 2>&1 &
echo "Web PID: $!"

sleep 5
pgrep -a node | grep -E "api|next"
```

Зафиксируй, какой вариант был использован и его результат.

---

### ШАГ 10 — Smoke Tests

Это обязательные проверки после деплоя. Выполни все.

**10.1 HTTP: /lab/test возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`

**10.2 HTTP: /lab/build возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
```
Ожидается: `200`

**10.3 HTTP: /lab/data возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/data
```
Ожидается: `200`

**10.4 HTTP: /lab возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**10.5 API: новый endpoint GET /api/v1/lab/strategy-versions доступен (401, не 404)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/strategy-versions \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.
Если `404` — новый endpoint не зарегистрирован, это критическая регрессия.

**10.6 API: POST /api/v1/lab/backtest требует strategyVersionId (400, не 422 / не 500)**
```
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:4000/api/v1/lab/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token" \
  -d '{"datasetId":"test"}'
```
Ожидается: `401` (auth fail before validation — это нормально).
Если вернулся `404` — endpoint исчез, это критическая регрессия.

**10.7 API: старый endpoint GET /api/v1/lab/datasets на месте**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.

**10.8 API: GET /api/v1/lab/backtest на месте**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/backtest \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.

**10.9 API health check**
```
curl -s http://localhost:4000/api/v1/healthz
```
Ожидается: `{"status":"ok"}`.

**10.10 BacktestForm в bundle**
```
grep -r "BacktestForm\|strategyVersionId\|POLL_INTERVAL_MS" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.11 DatasetSnapshotBlock в bundle**
```
grep -r "DatasetSnapshotBlock\|Dataset Snapshot" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.12 MetricsTab / TradesTab / EquityTab в bundle**
```
grep -r "MetricsTab\|TradesTab\|EquityTab\|ResultDetail" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.13 Phase 4 регрессия: graph-compiler на месте**
```
grep -r "graphToDSL\|compiledDsl" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.14 Phase 3C регрессия: validationTypes на месте**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.15 Phase 2C регрессия: QualitySummary на месте**
```
grep -r "qualitySectionStyle\|All clear\|Unusable" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**10.16 Проверка migration в Prisma status**
```
pnpm --filter @botmarketplace/api exec prisma migrate status 2>&1 | grep -E "applied|pending|phase5"
```
Ожидается: `20260309b_phase5_backtest_version_binding` — applied.

**10.17 Проверка strategyVersionId колонки в БД**
```
pnpm --filter @botmarketplace/api exec prisma db execute \
  --stdin <<'SQL'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'BacktestResult' AND column_name = 'strategyVersionId';
SQL
```
Ожидается: строка с `strategyVersionId`, `text`, `YES`.
Если колонка не найдена — миграция не применилась.

---

### ШАГ 11 — Финальная git проверка

```
git log --oneline a3660fb6535a7a1cd02707169c654f510be484f3..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 5 файлов
- НЕ реализовывать Phase 6 и следующий функционал
- НЕ делать merge или rebase
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ применять SQL миграции вручную — только через `pnpm db:migrate`
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
- graph-compiler present (Phase 4): yes/no
- validationTypes.ts present (Phase 3C): yes/no
- DatasetPreview.tsx present (Phase 2B): yes/no
- lightweight-charts in node_modules: yes/no
- @xyflow/react in node_modules: yes/no

**3. Build & Migration Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed (with error)
- db:migrate: success / failed (with error)
- Migration applied: 20260309b_phase5_backtest_version_binding — yes/no
- strategyVersionId column in DB: yes/no
- TypeScript API (tsc --noEmit): 0 errors / N errors (list if any)
- TypeScript Web (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/build in build output: yes/no + size (kB)
- /lab/data in build output: yes/no
- /lab/test in build output: yes/no + size (kB)
- BacktestForm in bundle: yes/no
- DatasetSnapshotBlock in bundle: yes/no
- MetricsTab/TradesTab/EquityTab in bundle: yes/no
- lightweight-charts equity in bundle: yes/no
- graph-compiler in bundle (Phase 4): yes/no
- validationTypes in bundle (Phase 3C): yes/no
- QualitySummary in bundle (Phase 2C): yes/no
- DatasetPreview in bundle (Phase 2B): yes/no

**4. Service Restart**
- Service manager used:
- API restart status: success / failed
- Web restart status: success / failed
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
| GET /api/v1/healthz | {"status":"ok"} | ? | |
| BacktestForm in bundle | file found | ? | |
| DatasetSnapshotBlock in bundle | file found | ? | |
| MetricsTab/TradesTab/EquityTab in bundle | file found | ? | |
| graph-compiler in bundle (Phase 4) | file found | ? | |
| validateGraph in bundle (Phase 3C) | file found | ? | |
| QualitySummary in bundle (Phase 2C) | file found | ? | |
| Migration applied | applied | ? | |
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
- DatasetSnapshotBlock functional: yes / no
- GET /lab/strategy-versions endpoint active: yes / no
- POST /lab/backtest accepts strategyVersionId: yes / no
- strategyVersionId column added to BacktestResult: yes / no
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
