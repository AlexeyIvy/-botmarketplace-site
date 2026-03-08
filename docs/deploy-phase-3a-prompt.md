# VPS Deploy Prompt — Phase 3A (Graph Canvas Base)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 3A — Graph Canvas Base.
Это frontend-only изменение. Бекенд, база данных и API не затронуты.

### Что такое Phase 3A

Phase 3A — пятая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md).
Базируется на Phase 2C (Quality Summary UI). Добавляет React Flow canvas в Build tab:

- `apps/web/package.json` — добавлена зависимость `@xyflow/react: ^12.10.1`
- `apps/web/package-lock.json` — создан lockfile для новой зависимости
- `apps/web/src/app/lab/useLabGraphStore.ts` — обновлён:
  - `nodes: unknown[]` → `nodes: Node[]` из @xyflow/react (строгая типизация)
  - `edges: unknown[]` → `edges: Edge[]` из @xyflow/react
  - добавлен `onNodesChange(changes: NodeChange[])` — использует `applyNodeChanges`
  - добавлен `onEdgesChange(changes: EdgeChange[])` — использует `applyEdgeChanges`
  - добавлены `setNodes(nodes: Node[])` и `setEdges(edges: Edge[])`
  - undo/redo по-прежнему через zundo `temporal` middleware (без изменений в стратегии)
- `apps/web/src/app/lab/build/page.tsx` — заменён placeholder реальным canvas:
  - `ReactFlowProvider` + `ReactFlow` из `@xyflow/react`
  - `<Background>` — dot grid, `<Controls>` — fit-to-view, `<MiniMap>`
  - `colorMode="dark"` — совместимость с dark UI
  - `deleteKeyCode: ["Delete", "Backspace"]` — удаление выделенных узлов/рёбер
  - Keyboard shortcuts via `window.addEventListener("keydown")`:
    - Cmd/Ctrl+Z → undo (zundo)
    - Cmd/Ctrl+Y / Cmd/Ctrl+Shift+Z → redo (zundo)
    - Cmd/Ctrl+A → select all nodes
    - Escape → deselect all
  - canvas читает nodes/edges из useLabGraphStore как source of truth
  - initial state — empty graph (nodes: [], edges: [])

Phase 3A НЕ содержит:
- изменений бекенда (apps/api/)
- изменений БД (Prisma schema, миграции)
- новых API endpoints
- block palette, custom node renderers, typed ports
- Inspector feature logic, Validation drawer logic
- graph persistence (PATCH /lab/graphs)
- Phase 3B/3C функционала

### Ветка для деплоя

Branch: `claude/deploy-phase-3a-5Vnfy`
Commit SHA: `e2233fc4b649b289e512c933598251c4740efcac`
Базируется на: `claude/lab-phase-2c-5Vnfy`

---

## Задача: задеплоить Phase 3A на VPS

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

### ШАГ 1 — Получить Phase 3A ветку

```
git fetch origin claude/deploy-phase-3a-5Vnfy
git checkout claude/deploy-phase-3a-5Vnfy
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
`feat(lab): Phase 3A — Graph canvas base`

Проверь SHA:
```
git rev-parse HEAD
```
Ожидается: `e2233fc4b649b289e512c933598251c4740efcac`

Проверь diff относительно Phase 2C ветки (должно быть ровно 4 файла):
```
git diff --name-only origin/claude/lab-phase-2c-5Vnfy..HEAD
```

Ожидаемый результат:
```
apps/web/package-lock.json
apps/web/package.json
apps/web/src/app/lab/build/page.tsx
apps/web/src/app/lab/useLabGraphStore.ts
```

Если в diff есть что-то кроме этих 4 файлов — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 2A/2B/2C файлы на месте:
```
test -f apps/web/src/app/lab/DatasetPreview.tsx && echo "DatasetPreview OK" || echo "MISSING DatasetPreview"
test -f apps/web/src/app/lab/useLabGraphStore.ts  && echo "store OK"          || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx            && echo "layout OK"         || echo "MISSING layout"
test -f apps/web/src/app/lab/data/page.tsx         && echo "data page OK"      || echo "MISSING data page"
```

Проверь, что API файлы не затронуты:
```
git diff origin/claude/lab-phase-2c-5Vnfy..HEAD -- apps/api/ | head -5
```
Ожидается: пустой вывод.

---

### ШАГ 2 — Установка зависимостей

Phase 3A добавляет новый npm пакет `@xyflow/react`. Обычный install:

```
pnpm install
```

Проверь, что @xyflow/react установлен:
```
test -d apps/web/node_modules/@xyflow/react && echo "@xyflow/react OK" || echo "MISSING @xyflow/react"
```

Проверь версию:
```
cat apps/web/node_modules/@xyflow/react/package.json | grep '"version"'
```
Ожидается: версия 12.x.x

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
- /lab/build присутствует в списке собранных страниц, его размер заметно больше, чем в Phase 2C
  (добавлен React Flow bundle: ~57 kB / ~159 kB First Load JS total)

Проверь lab маршруты в выводе билда. Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Проверь размер /lab/build chunk — Phase 3A добавила @xyflow/react (~57 kB),
размер должен значительно увеличиться относительно Phase 2C:
```
# Строку с /lab/build из вывода next build скопируй в отчёт
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 5 — Проверка bundle содержимого

Убедись, что @xyflow/react попал в bundle:
```
grep -r "xyflow\|reactflow\|ReactFlow\|MiniMap" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

Убедись, что keyboard shortcuts попали в bundle:
```
grep -r "deleteKeyCode\|onNodesChange\|onEdgesChange" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

Убедись, что DatasetPreview по-прежнему в bundle (Phase 2B/2C не сломана):
```
grep -r "DatasetPreview\|lightweight-charts" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

Убедись, что QualitySummary по-прежнему в bundle (Phase 2C не сломана):
```
grep -r "qualitySectionStyle\|All clear\|Unusable" \
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

**7.1 HTTP: /lab/build возвращает 200 (canvas загружается)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
```
Ожидается: `200`

**7.2 HTTP: /lab возвращает 200 (ClassicMode не сломан)**
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

**7.5 @xyflow/react в bundle**
```
grep -r "xyflow\|MiniMap" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.6 Canvas styles в bundle (ReactFlow CSS)**
```
grep -r "react-flow\|react_flow\|reactflow" \
  apps/web/.next/static/css/ --include="*.css" -l 2>/dev/null | head -3
# Если CSS inline — ищем в chunks:
grep -r "react-flow__" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл (CSS либо в .css, либо inline в JS chunk).

**7.7 Keyboard shortcuts в bundle**
```
grep -r "deleteKeyCode\|Backspace\|onNodesChange" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.8 useLabGraphStore изменения в bundle**
```
grep -r "applyNodeChanges\|applyEdgeChanges\|setNodes\|setEdges" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.9 Phase 2C регрессия: QualitySummary на месте**
```
grep -r "qualitySectionStyle\|toggleBtnStyle" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**7.10 API: GET /api/v1/lab/datasets доступен (Phase 2A endpoint)**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/api/v1/lab/datasets \
  -H "Authorization: Bearer invalid_token"
```
Ожидается: `401`.
Если `404` — API endpoint исчез, это регрессия.

**7.11 Отсутствие API изменений**
```
git diff origin/claude/lab-phase-2c-5Vnfy..HEAD -- apps/api/ | wc -l
```
Ожидается: `0`

**7.12 Отсутствие Prisma schema изменений**
```
git diff origin/claude/lab-phase-2c-5Vnfy..HEAD -- \
  packages/shared/prisma/ apps/api/prisma/ 2>/dev/null | wc -l
```
Ожидается: `0`

**7.13 API health check**
```
curl -s http://localhost:4000/health 2>/dev/null || echo "API not on 4000 or not running"
```
Цель: убедиться, что деплой frontend не сломал API.

---

### ШАГ 8 — Финальная git проверка

```
git log --oneline origin/claude/lab-phase-2c-5Vnfy..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 3A файлов
- НЕ делать Phase 3B/3C (block palette, Inspector logic, validation, persistence)
- НЕ делать merge в main
- НЕ трогать apps/api/, Prisma schema, БД миграции
- НЕ "исправлять" TypeScript ошибки, если они появятся — только репортировать
- НЕ запускать db:migrate
- НЕ создавать новые API endpoints
- НЕ деплоить API (только frontend)
- НЕ удалять Inspector placeholder и Diagnostics placeholder из LabShell

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 3A

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown

**2. Branch & Commit**
- Branch deployed: claude/deploy-phase-3a-5Vnfy
- HEAD SHA:
- Expected SHA: e2233fc4b649b289e512c933598251c4740efcac
- SHA match: yes/no
- Diff files count vs Phase 2C: (must be 4)
- Files in diff: (list them)
- DatasetPreview.tsx present: yes/no
- useLabGraphStore.ts present: yes/no
- @xyflow/react in node_modules: yes/no + version
- API diff empty: yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- TypeScript (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/build in build output: yes/no + size (kB)
- /lab/data in build output: yes/no
- /lab/test in build output: yes/no
- @xyflow/react in bundle: yes/no
- Keyboard shortcuts in bundle: yes/no
- QualitySummary in bundle (2C regression check): yes/no
- DatasetPreview in bundle (2B regression check): yes/no

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
| @xyflow/react in bundle | file found | ? | |
| ReactFlow CSS in bundle | file found | ? | |
| Keyboard shortcuts in bundle | file found | ? | |
| applyNodeChanges in bundle | file found | ? | |
| QualitySummary styles in bundle | file found | ? | |
| GET /api/v1/lab/datasets (no auth) | 401 | ? | |
| API diff empty | 0 lines | ? | |
| Prisma diff empty | 0 lines | ? | |
| API health check | 200 or N/A | ? | |

**6. Final Judgment**
- Phase 3A successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- @xyflow/react canvas on /lab/build: yes / no
- Classic mode (/lab) operational: yes / no
- Dataset Builder (Phase 2A) operational: yes / no
- Preview (Phase 2B) operational: yes / no
- Quality summary (Phase 2C) operational: yes / no
- No new API endpoints added: yes / no
- No DB migrations run: yes / no
- Ready for Phase 3B development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 3A.
```
