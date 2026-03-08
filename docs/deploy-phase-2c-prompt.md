# VPS Deploy Prompt — Phase 2C (Quality Summary UI)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 2C — Quality Summary UI.
Это frontend-only изменение. Бекенд, база данных и API не затронуты.

### Что такое Phase 2C

Phase 2C — четвёртая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md).
Базируется на Phase 2B (preview table/chart). Добавляет Quality Summary UI:

- `apps/web/src/app/lab/data/page.tsx` — единственный изменённый файл:
  - `QualitySummary` компонент: collapsible блок (compact + expanded состояния)
  - compact state: однострочник с status label, описанием, числом candles и issues
  - expanded state: полная таблица (candles, gaps, maxGap, dupeAttempts,
    sanityIssues, hash, fetchedAt, engineVersion) + "Raw details" expander
  - явная обработка READY / PARTIAL / FAILED:
    - READY: зелёный badge "All clear"
    - PARTIAL: persistent warning banner + quality details
    - FAILED: error banner + preview заблокирован (сообщение "Preview unavailable")
  - `DatasetResult` (после submit): использует QualitySummary, FAILED блокирует preview
  - `ActiveDatasetInfo` (выбор существующего):
    - fetch GET /lab/datasets/:id для qualityJson + engineVersion
    - FAILED error banner (отсутствовал в Phase 2B)
    - QualitySummary с live quality detail
  - `DatasetDetail` type добавлен
  - стили: `qualitySectionStyle`, `toggleBtnStyle`

Phase 2C НЕ содержит:
- изменений бекенда (apps/api/)
- изменений БД (Prisma schema, миграции)
- новых API endpoints (использован только существующий GET /lab/datasets/:id)
- React Flow / graph editor
- Phase 3 функционала

### Ветка для деплоя

Branch: `claude/lab-phase-2c-5Vnfy`
Commit SHA: `306b99cc6d065494b8765a89c9547a0d43de0ad0`
Базируется на: `claude/lab-phase-2b-5Vnfy`

---

## Задача: задеплоить Phase 2C на VPS

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
   systemctl status botmarket-web 2>/dev/null || echo "no systemd unit"
   pm2 list 2>/dev/null || echo "no pm2"
   pgrep -a node || echo "no node processes"
   ```

4. Проверь env файлы:
   ```
   test -f .env && echo ".env exists" || echo "no .env"
   test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"
   ```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Phase 2C ветку

```
git fetch origin claude/lab-phase-2c-5Vnfy
git checkout claude/lab-phase-2c-5Vnfy
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
`feat(lab): Phase 2C — Quality summary UI`

Проверь SHA:
```
git rev-parse HEAD
```
Ожидается: `306b99cc6d065494b8765a89c9547a0d43de0ad0`

Проверь diff относительно Phase 2B ветки (должен быть ровно 1 файл):
```
git diff --name-only origin/claude/lab-phase-2b-5Vnfy..HEAD
```

Ожидаемый результат:
```
apps/web/src/app/lab/data/page.tsx
```

Если в diff есть что-то кроме этого 1 файла — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 2A/2B файлы на месте:
```
test -f apps/web/src/app/lab/DatasetPreview.tsx && echo "DatasetPreview OK" || echo "MISSING DatasetPreview"
test -f apps/web/src/app/lab/useLabGraphStore.ts  && echo "store OK"          || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx            && echo "layout OK"         || echo "MISSING layout"
```

Проверь, что API файлы не затронуты:
```
git diff origin/claude/lab-phase-2b-5Vnfy..HEAD -- apps/api/ | head -5
```
Ожидается: пустой вывод.

---

### ШАГ 2 — Установка зависимостей

Phase 2C не добавляет новых npm пакетов, поэтому `--frozen-lockfile` обязателен:

```
pnpm install --frozen-lockfile
```

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — TypeScript проверка (tsc)

```
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```

Ожидаемый результат: 0 ошибок, команда завершается с кодом 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй TypeScript ошибки самостоятельно — это выходит за рамки деплоя.

---

### ШАГ 4 — Production build (Next.js)

```
pnpm build:web 2>&1
```

Ожидаемый результат:
- Build завершился успешно (exit code 0)
- В выводе нет `Error:` или `Failed to compile`
- /lab/data присутствует в списке собранных страниц и его размер стал больше, чем в Phase 2B

Проверь lab маршруты в выводе билда. Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Проверь размер /lab/data chunk — Phase 2C добавила QualitySummary, размер должен
увеличиться относительно Phase 2B (~12-15 kB, было ~10 kB):
```
# Строку с /lab/data из вывода next build скопируй в отчёт
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 5 — Проверка bundle содержимого

Убедись, что QualitySummary попал в bundle:

```
grep -r "qualitySectionStyle\|QualitySummary\|toggleBtnStyle\|All clear\|Unusable" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

Убедись, что DatasetPreview по-прежнему в bundle (Phase 2B не сломана):
```
grep -r "DatasetPreview\|tanstack\|virtual\|lightweight-charts" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

Убедись, что Dataset Builder (Phase 2A) по-прежнему в bundle:
```
grep -r "Fetch Dataset\|estimatedCandles\|BTCUSDT" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

---

### ШАГ 6 — Перезапуск веб-сервиса

Определи, как запущен Next.js на этом VPS, и перезапусти его.

**Вариант A — systemd:**
```
systemctl restart botmarket-web
sleep 5
systemctl status botmarket-web
```

**Вариант B — pm2:**
```
pm2 restart web
sleep 5
pm2 status
pm2 logs web --lines 30 --nostream
```

**Вариант C — ручной запуск (если нет systemd/pm2):**
```
pkill -f "next start" || true
sleep 2
cd apps/web && nohup pnpm start >> /var/log/botmarket-web.log 2>&1 &
echo "PID: $!"
sleep 5
pgrep -a node | grep next
```

Зафиксируй, какой вариант был использован и его результат.

---

### ШАГ 7 — Smoke Tests

Это обязательные проверки после деплоя. Выполни все.

**7.1 HTTP: /lab/data возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/data
```
Ожидается: `200`

**7.2 HTTP: /lab возвращает 200 (ClassicMode не сломан)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**7.3 HTTP: /lab/build и /lab/test возвращают 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200` для каждого.

**7.4 API: GET /api/v1/lab/datasets доступен (Phase 2A endpoint)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401` (endpoint существует, токен невалидный — это корректно).
Если `404` — API endpoint исчез, это регрессия.

**7.5 API: GET /api/v1/lab/datasets/:id доступен (используется Phase 2C)**
```
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/datasets/non-existent-id-test \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401` (endpoint существует).
Если `404` — endpoint исчез, Phase 2C не сможет подгружать quality details.

**7.6 API: preview endpoint по-прежнему работает (Phase 2B не сломана)**
```
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:4000/api/v1/lab/datasets/non-existent/preview \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.

**7.7 QualitySummary в bundle**
```
grep -r "qualitySectionStyle\|toggleBtnStyle" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.8 PARTIAL/FAILED/READY тексты в bundle**
```
grep -r "All clear\|Unusable\|Preview unavailable" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.9 Отсутствие API изменений**
```
git diff origin/claude/lab-phase-2b-5Vnfy..HEAD -- apps/api/ | wc -l
```
Ожидается: `0`

**7.10 Отсутствие Prisma schema изменений**
```
git diff origin/claude/lab-phase-2b-5Vnfy..HEAD -- \
  packages/shared/prisma/ apps/api/prisma/ 2>/dev/null | wc -l
```
Ожидается: `0`

**7.11 API health check**
```
curl -s http://localhost:4000/health 2>/dev/null || echo "API not on 4000 or not running"
```
Цель: убедиться, что деплой frontend не сломал API.

---

### ШАГ 8 — Финальная git проверка

```
git log --oneline origin/claude/lab-phase-2b-5Vnfy..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 2C файлов
- НЕ делать Phase 3 (graph editor, React Flow, compiler)
- НЕ делать merge в main
- НЕ трогать apps/api/, Prisma schema, БД миграции
- НЕ "исправлять" TypeScript ошибки, если они появятся — только репортировать
- НЕ запускать db:migrate
- НЕ создавать новые API endpoints
- НЕ деплоить API (только frontend)

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 2C

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown

**2. Branch & Commit**
- Branch deployed: claude/lab-phase-2c-5Vnfy
- HEAD SHA:
- Expected SHA: 306b99cc6d065494b8765a89c9547a0d43de0ad0
- SHA match: yes/no
- Diff files count vs Phase 2B: (must be 1)
- Files in diff: (list them)
- DatasetPreview.tsx present: yes/no
- useLabGraphStore.ts present: yes/no
- API diff empty: yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- TypeScript (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/data in build output: yes/no + size (kB)
- /lab/build in build output: yes/no
- /lab/test in build output: yes/no
- QualitySummary in bundle: yes/no
- DatasetPreview in bundle: yes/no
- Dataset Builder in bundle: yes/no

**4. Service Restart**
- Service manager used:
- Restart status: success / failed
- Process running after restart: yes / no

**5. Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab/data HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /lab/build HTTP status | 200 | ? | |
| GET /lab/test HTTP status | 200 | ? | |
| GET /api/v1/lab/datasets (no auth) | 401 | ? | |
| GET /api/v1/lab/datasets/:id (no auth) | 401 | ? | |
| GET /api/v1/lab/datasets/:id/preview (no auth) | 401 | ? | |
| QualitySummary styles in bundle | file found | ? | |
| READY/PARTIAL/FAILED texts in bundle | file found | ? | |
| API diff empty | 0 lines | ? | |
| Prisma diff empty | 0 lines | ? | |
| API health check | 200 or N/A | ? | |

**6. Final Judgment**
- Phase 2C successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- Dataset Builder (Phase 2A) operational: yes / no
- Preview (Phase 2B) operational: yes / no
- Quality summary UI deployed: yes / no
- GET /lab/datasets/:id endpoint accessible: yes / no
- No new API endpoints added: yes / no
- No DB migrations run: yes / no
- Ready for Phase 3 development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 2C.
```
