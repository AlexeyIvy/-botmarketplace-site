# VPS Deploy Prompt — Phase 3C (Graph Validation UI)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 3C — Graph Validation UI.
Это frontend-only изменение. Бекенд, база данных и API не затронуты.

### Что такое Phase 3C

Phase 3C — восьмая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md §13.3, §28).
Базируется на Phase 3B (Node Palette + Inspector + Connection UX). Добавляет
полноценную клиентскую валидацию графа и визуальную обратную связь:

**Новые файлы:**
- `apps/web/src/app/lab/validationTypes.ts` — типы ValidationIssue, ValidationSeverity
  + чистая функция `validateGraph(nodes, edges): ValidationIssue[]` с 4 правилами:
  - Rule 1: MISSING_RISK_BLOCK — нет ни одного risk-блока (error)
  - Rule 2: MISSING_ENTRY_BLOCK — нет enter_long/enter_short (error)
  - Rule 3: MISSING_INPUT_BLOCK — нет input/candles блока (warning, только если граф не пустой)
  - Rule 4: REQUIRED_PORT_UNCONNECTED — обязательный input порт без соединения (error, per node/port)

**Изменённые файлы:**
- `apps/web/src/app/lab/useLabGraphStore.ts` — добавлены:
  - поле `validationIssues: ValidationIssue[]` в LabGraphState (не персистируется)
  - action `runValidation()` — запускает validateGraph + обновляет validationState и validationIssues
  - auto-trigger: `onNodesChange` и `onEdgesChange` и `setEdges` вызывают `runValidation()` с debounce 500ms
  - тип `ValidationState` расширен: `"idle" | "ok" | "warning" | "error" | "stale"`

- `apps/web/src/app/lab/build/nodes/StrategyNode.tsx` — Phase 3C добавляет:
  - Error badge (⚠) на header ноды при наличии validation issues (§28 Level 3)
    - красный (#D44C4C) для errors, жёлтый (#FBBF24) для warnings only
  - Красный port ring с анимацией (`portErrorPulse`) для required портов с validation error (§28 Level 3)
  - `hasValidationError` prop в PortHandle + соответствующие стили
  - Чтение `validationIssues` из useLabGraphStore

- `apps/web/src/app/lab/build/page.tsx` — Phase 3C добавляет:
  - `ValidationDrawer` компонент — docked bottom drawer (§28 Level 5):
    - Collapsible header с текущим validation status (✓ Valid / N errors / N warnings)
    - Список issues: ⊗ для error, ⚠ для warning, кликабельные → focusNode + setCenter
    - Клавиатурная доступность (Enter/Space → focusNode)
    - Пустое состояние: "Add blocks..." (idle) или "✓ Graph is valid." (ok)
  - Интеграция в layout: canvas (flex:1) + ValidationDrawer (flexShrink:0) в column flex

Phase 3C НЕ содержит:
- изменений бекенда (apps/api/)
- изменений БД (Prisma schema, миграции)
- новых API endpoints
- graph persistence (PATCH /lab/graphs)
- Phase 3D и следующего функционала

### Ветка для деплоя

Branch: `claude/deploy-phase-3c-5Vnfy`
Commit SHA: `dba5d626d43e3131fa77868d866e2b29b989008a`
Базируется на: `claude/deploy-phase-3b-5Vnfy` (SHA: `6c1b9588fc93382657512a18c45c44ddb0faea46`)

---

## Задача: задеплоить Phase 3C на VPS

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

### ШАГ 1 — Получить Phase 3C ветку

```
git fetch origin claude/deploy-phase-3c-5Vnfy
git checkout claude/deploy-phase-3c-5Vnfy
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
`feat(lab): Phase 3C — graph validation UI (StrategyNode indicators + validation panel)`

Проверь SHA:
```
git rev-parse HEAD
```
Ожидается: `dba5d626d43e3131fa77868d866e2b29b989008a`

Проверь diff относительно Phase 3B ветки (должно быть ровно 4 файла):
```
git diff --name-only origin/claude/deploy-phase-3b-5Vnfy..HEAD 2>/dev/null || \
git diff --name-only 6c1b9588fc93382657512a18c45c44ddb0faea46..HEAD
```

Ожидаемый результат (ровно 4 файла):
```
apps/web/src/app/lab/build/nodes/StrategyNode.tsx
apps/web/src/app/lab/build/page.tsx
apps/web/src/app/lab/useLabGraphStore.ts
apps/web/src/app/lab/validationTypes.ts
```

Если в diff есть что-то кроме этих 4 файлов — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 3B файлы на месте:
```
test -f apps/web/src/app/lab/build/nodes/StrategyNode.tsx && echo "StrategyNode OK" || echo "MISSING StrategyNode"
test -f apps/web/src/app/lab/build/BlockPalette.tsx       && echo "BlockPalette OK"  || echo "MISSING BlockPalette"
test -f apps/web/src/app/lab/build/InspectorPanel.tsx     && echo "Inspector OK"     || echo "MISSING Inspector"
test -f apps/web/src/app/lab/build/ConnectionContext.tsx  && echo "ConnCtx OK"       || echo "MISSING ConnCtx"
test -f apps/web/src/app/lab/validationTypes.ts           && echo "validationTypes OK" || echo "MISSING validationTypes"
```

Проверь, что Phase 2A/2B/2C файлы не потеряны:
```
test -f apps/web/src/app/lab/DatasetPreview.tsx && echo "DatasetPreview OK" || echo "MISSING DatasetPreview"
test -f apps/web/src/app/lab/useLabGraphStore.ts && echo "store OK"          || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx          && echo "layout OK"         || echo "MISSING layout"
test -f apps/web/src/app/lab/data/page.tsx       && echo "data page OK"      || echo "MISSING data page"
```

Проверь, что API файлы не затронуты:
```
git diff 6c1b9588fc93382657512a18c45c44ddb0faea46..HEAD -- apps/api/ | head -5
```
Ожидается: пустой вывод.

---

### ШАГ 2 — Установка зависимостей

Phase 3C не добавляет новых npm пакетов. Стандартный install для синхронизации:

```
pnpm install
```

Проверь, что @xyflow/react по-прежнему установлен (из Phase 3A):
```
test -d apps/web/node_modules/@xyflow/react && echo "@xyflow/react OK" || echo "MISSING @xyflow/react"
```

Проверь наличие zundo (из Phase 1B):
```
test -d apps/web/node_modules/zundo && echo "zundo OK" || echo "MISSING zundo"
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
- `/lab/build` присутствует в списке собранных страниц
- Размер `/lab/build` не сильно изменился относительно Phase 3B
  (Phase 3C добавляет только JS-логику без новых npm пакетов)

Проверь lab маршруты в выводе билда. Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 5 — Проверка bundle содержимого

**5.1 — validationTypes в bundle**
```
grep -r "MISSING_RISK_BLOCK\|MISSING_ENTRY_BLOCK\|validateGraph\|ValidationIssue" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.2 — ValidationDrawer в bundle**
```
grep -r "ValidationDrawer\|validationState\|validationIssues\|Add blocks to the canvas" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.3 — Error badge на нодах в bundle**
```
grep -r "portErrorPulse\|hasValidationError\|errorBadgeColor\|showErrorBadge" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.4 — Правила валидации в bundle**
```
grep -r "MISSING_INPUT_BLOCK\|REQUIRED_PORT_UNCONNECTED\|runValidation" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.5 — Phase 3B не сломана (@xyflow/react в bundle)**
```
grep -r "xyflow\|MiniMap\|ReactFlow\|BlockPalette\|InspectorPanel" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.6 — Phase 2C не сломана (QualitySummary в bundle)**
```
grep -r "qualitySectionStyle\|All clear\|Unusable" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**5.7 — Phase 2B не сломана (DatasetPreview в bundle)**
```
grep -r "DatasetPreview\|lightweight-charts" \
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

**7.1 HTTP: /lab/build возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
```
Ожидается: `200`

**7.2 HTTP: /lab возвращает 200 (Classic mode)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**7.3 HTTP: /lab/data возвращает 200 (Phase 2C не сломана)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/data
```
Ожидается: `200`

**7.4 HTTP: /lab/test возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`

**7.5 validateGraph в bundle**
```
grep -r "MISSING_RISK_BLOCK\|validateGraph" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.6 ValidationDrawer в bundle**
```
grep -r "validationIssues\|ValidationDrawer\|validationState" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.7 Error badge + port ring в bundle**
```
grep -r "portErrorPulse\|hasValidationError\|errorBadgeColor" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.8 runValidation debounce в bundle**
```
grep -r "runValidation\|debounce\|validationDebounce" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.9 Phase 3B регрессия: @xyflow/react на месте**
```
grep -r "xyflow\|onNodesChange\|onEdgesChange" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.10 Phase 3B регрессия: BlockPalette на месте**
```
grep -r "BlockPalette\|block-palette-search\|onAddBlock" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.11 Phase 2C регрессия: QualitySummary на месте**
```
grep -r "qualitySectionStyle\|toggleBtnStyle" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.12 API: GET /api/v1/lab/datasets доступен (Phase 2A endpoint)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.
Если `404` — API endpoint исчез, это регрессия.

**7.13 Отсутствие API изменений**
```
git diff 6c1b9588fc93382657512a18c45c44ddb0faea46..HEAD -- apps/api/ | wc -l
```
Ожидается: `0`

**7.14 Отсутствие Prisma schema изменений**
```
git diff 6c1b9588fc93382657512a18c45c44ddb0faea46..HEAD -- \
  packages/shared/prisma/ apps/api/prisma/ 2>/dev/null | wc -l
```
Ожидается: `0`

**7.15 API health check**
```
curl -s http://localhost:4000/health 2>/dev/null || echo "API not on 4000 or not running"
```
Цель: убедиться, что деплой frontend не сломал API.

---

### ШАГ 8 — Финальная git проверка

```
git log --oneline 6c1b9588fc93382657512a18c45c44ddb0faea46..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 3C файлов
- НЕ реализовывать Phase 3D и следующий функционал (persistence, graph export, AI-chat)
- НЕ делать merge в main
- НЕ трогать apps/api/, Prisma schema, БД миграции
- НЕ "исправлять" TypeScript ошибки, если они появятся — только репортировать
- НЕ запускать db:migrate
- НЕ создавать новые API endpoints
- НЕ деплоить API (только frontend)

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 3C

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown

**2. Branch & Commit**
- Branch deployed: claude/deploy-phase-3c-5Vnfy
- HEAD SHA:
- Expected SHA: dba5d626d43e3131fa77868d866e2b29b989008a
- SHA match: yes/no
- Diff files count vs Phase 3B: (must be 4)
- Files in diff: (list them)
- validationTypes.ts present: yes/no
- StrategyNode.tsx present: yes/no
- BlockPalette.tsx present (3B): yes/no
- InspectorPanel.tsx present (3B): yes/no
- @xyflow/react in node_modules: yes/no
- zundo in node_modules: yes/no
- API diff empty: yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- TypeScript (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/build in build output: yes/no + size (kB)
- /lab/data in build output: yes/no
- /lab/test in build output: yes/no
- validateGraph in bundle: yes/no
- ValidationDrawer in bundle: yes/no
- Error badge / port ring in bundle: yes/no
- runValidation in bundle: yes/no
- @xyflow/react in bundle (3B regression): yes/no
- QualitySummary in bundle (2C regression): yes/no
- DatasetPreview in bundle (2B regression): yes/no

**4. Service Restart**
- Service manager used:
- Restart status: success / failed
- Process running after restart: yes / no

**5. Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab/build HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| GET /lab/data HTTP status | 200 | ? | |
| GET /lab/test HTTP status | 200 | ? | |
| validateGraph in bundle | file found | ? | |
| ValidationDrawer in bundle | file found | ? | |
| Error badge/port ring in bundle | file found | ? | |
| runValidation debounce in bundle | file found | ? | |
| @xyflow/react in bundle (3B) | file found | ? | |
| BlockPalette in bundle (3B) | file found | ? | |
| QualitySummary in bundle (2C) | file found | ? | |
| GET /api/v1/lab/datasets (no auth) | 401 | ? | |
| API diff empty | 0 lines | ? | |
| Prisma diff empty | 0 lines | ? | |
| API health check | 200 or N/A | ? | |

**6. Final Judgment**
- Phase 3C successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- ValidationDrawer on /lab/build: yes / no
- Error badge on nodes: yes / no
- Port error ring animation: yes / no
- validateGraph debounce (500ms): yes / no
- Block Palette operational (Phase 3B): yes / no
- Inspector Panel operational (Phase 3B): yes / no
- Canvas operational (Phase 3A): yes / no
- Dataset Builder (Phase 2A) operational: yes / no
- Preview (Phase 2B) operational: yes / no
- Quality summary (Phase 2C) operational: yes / no
- No new API endpoints added: yes / no
- No DB migrations run: yes / no
- Ready for Phase 3D development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 3C.
```
