# VPS Deploy Prompt — Phase 1B (Lab Store + Route-Aware Tabs)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 1B — Lab Store Wiring + Route-Aware Tabs.
Это frontend-only изменение. Бекенд, база данных и API не затронуты.

### Что такое Phase 1B

Phase 1B — вторая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md).
Базируется на Phase 1A (LabShell + ClassicMode). Добавляет:

- `apps/web/src/app/lab/useLabGraphStore.ts` — Zustand 5 store с zundo temporal
  middleware (activeConnectionId, activeDatasetId, activeGraphId,
  validationState, runState, nodes[], edges[])
- `apps/web/src/app/lab/layout.tsx` — LabShell как Next.js layout для /lab/*
  (shell теперь один раз на уровне layout, не в page.tsx)
- `apps/web/src/app/lab/LabShell.tsx` — обновлён: children prop вместо
  classicContent, usePathname для active tab, Link-навигация, Context Bar
  читает из useLabGraphStore (null → "— not selected")
- `apps/web/src/app/lab/page.tsx` — упрощён: только ClassicMode контент,
  без shell (shell теперь в layout)
- `apps/web/src/app/lab/data/page.tsx` — маршрут /lab/data (placeholder)
- `apps/web/src/app/lab/build/page.tsx` — маршрут /lab/build (placeholder)
- `apps/web/src/app/lab/test/page.tsx` — маршрут /lab/test (placeholder)
- `apps/web/package.json` — добавлены zustand@^5.0.11, zundo@^2.3.0

Phase 1B не содержит:
- изменений бекенда (apps/api/)
- изменений БД (Prisma schema)
- новых API endpoints
- React Flow
- dataset builder
- реального функционала Data/Build/Test (только placeholder)
- localStorage persistence

### Ветка для деплоя

Branch: `claude/lab-phase-1b-LLRAu`
Commit SHA: `55537498f104863ba6dd060f8010a90cc8a2006f`
Базируется на: `claude/lab-phase-1a-XjD9d`

---

## Задача: задеплоить Phase 1B на VPS

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

### ШАГ 1 — Получить Phase 1B ветку

```
git fetch origin claude/lab-phase-1b-LLRAu
git checkout claude/lab-phase-1b-LLRAu
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
`feat(lab): Phase 1B — useLabGraphStore + route-aware tabs`

Проверь SHA:
```
git rev-parse HEAD
```
Ожидается: `55537498f104863ba6dd060f8010a90cc8a2006f`

Проверь diff относительно Phase 1A ветки (должны быть ровно 9 файлов):
```
git diff --name-only origin/claude/lab-phase-1a-XjD9d..HEAD
```

Ожидаемый результат (порядок может отличаться):
```
apps/web/package.json
apps/web/src/app/lab/LabShell.tsx
apps/web/src/app/lab/build/page.tsx
apps/web/src/app/lab/data/page.tsx
apps/web/src/app/lab/layout.tsx
apps/web/src/app/lab/page.tsx
apps/web/src/app/lab/test/page.tsx
apps/web/src/app/lab/useLabGraphStore.ts
pnpm-lock.yaml
```

Если в diff есть что-то кроме этих 9 файлов — ОСТАНОВИСЬ и сообщи об этом.

Проверь, что Phase 1A файлы не были удалены:
```
test -f apps/web/src/app/lab/ClassicMode.tsx && echo "ClassicMode OK" || echo "MISSING ClassicMode"
test -f apps/web/src/app/lab/useLabGraphStore.ts && echo "store OK" || echo "MISSING store"
test -f apps/web/src/app/lab/layout.tsx && echo "layout OK" || echo "MISSING layout"
```

---

### ШАГ 2 — Установка зависимостей

```
pnpm install --frozen-lockfile
```

Флаг `--frozen-lockfile` обязателен: Phase 1B добавила zustand и zundo,
lockfile уже зафиксирован в коммите.

Проверь, что пакеты установились:
```
ls node_modules/.pnpm | grep zustand | head -3
ls node_modules/.pnpm | grep zundo | head -3
```
Ожидается: вывод не пустой для обоих.

Если pnpm install завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 3 — TypeScript проверка (tsc)

```
pnpm --filter @botmarketplace/web exec tsc --noEmit 2>&1
```

Ожидаемый результат: 0 ошибок, команда завершается с кодом 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй TypeScript ошибки самостоятельно — это выходит за рамки деплоя Phase 1B.

---

### ШАГ 4 — Production build (Next.js)

```
pnpm build:web 2>&1
```

Это выполнит `next build` для apps/web.

Ожидаемый результат:
- Build завершился успешно (exit code 0)
- В выводе нет `Error:` или `Failed to compile`
- Все 4 lab маршрута присутствуют в списке собранных страниц

Проверь lab маршруты в выводе билда. Ищи строки вида:
```
○ /lab
○ /lab/build
○ /lab/data
○ /lab/test
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 5 — Перезапуск веб-сервиса

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

### ШАГ 6 — Smoke Tests

Это обязательные проверки после деплоя. Выполни все.

**6.1 HTTP: /lab возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**6.2 HTTP: /lab/data возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/data
```
Ожидается: `200`

**6.3 HTTP: /lab/build возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/build
```
Ожидается: `200`

**6.4 HTTP: /lab/test возвращает 200**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab/test
```
Ожидается: `200`

**6.5 Проверка, что useLabGraphStore попал в bundle:**
```
grep -r "useLabGraphStore\|activeConnectionId\|zundo\|temporal" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл.

**6.6 Проверка, что layout.tsx обернул /lab маршруты:**
```
ls apps/web/.next/server/app/lab/ 2>/dev/null
```
Ожидается: `layout.js` (или аналог) присутствует в директории.

**6.7 Проверка ClassicMode по-прежнему в bundle:**
```
grep -r "ClassicMode\|GuestLabClassicMode\|AuthLabClassicMode" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
```
Ожидается: минимум 1 файл (ClassicMode не был удалён).

**6.8 Проверка отсутствия изменений в API:**
```
git diff origin/claude/lab-phase-1a-XjD9d..HEAD -- apps/api/ | head -5
```
Ожидается: пустой вывод.

**6.9 Проверка отсутствия изменений в Prisma schema:**
```
git diff origin/claude/lab-phase-1a-XjD9d..HEAD -- packages/shared/prisma/ apps/api/prisma/ 2>/dev/null | head -5
```
Ожидается: пустой вывод.

**6.10 Проверка health API (если API запущен):**
```
curl -s http://localhost:4000/health 2>/dev/null || echo "API not on 4000 or not running"
```
Цель: убедиться, что деплой frontend не сломал API.

---

### ШАГ 7 — Финальная git проверка

```
git log --oneline origin/claude/lab-phase-1a-XjD9d..HEAD
git show --stat HEAD
git rev-parse HEAD
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 1B файлов
- НЕ делать Phase 2 (dataset builder — отдельная задача)
- НЕ делать merge в main
- НЕ трогать apps/api/, Prisma schema, БД миграции
- НЕ "исправлять" TypeScript ошибки, если они появятся — только репортировать
- НЕ запускать db:migrate
- НЕ деплоить API (только frontend)

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 1B

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown

**2. Branch & Commit**
- Branch deployed: claude/lab-phase-1b-LLRAu
- HEAD SHA:
- Expected SHA: 55537498f104863ba6dd060f8010a90cc8a2006f
- SHA match: yes/no
- Diff files count vs Phase 1A: (must be 9)
- Files in diff: (list them)
- ClassicMode.tsx present: yes/no
- useLabGraphStore.ts present: yes/no
- layout.tsx present: yes/no

**3. Build Results**
- pnpm install: success / failed (with error)
- zustand installed: yes/no
- zundo installed: yes/no
- TypeScript (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab in build output: yes/no
- /lab/data in build output: yes/no
- /lab/build in build output: yes/no
- /lab/test in build output: yes/no

**4. Service Restart**
- Service manager used:
- Restart status: success / failed
- Process running after restart: yes / no

**5. Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab HTTP status | 200 | ? | |
| GET /lab/data HTTP status | 200 | ? | |
| GET /lab/build HTTP status | 200 | ? | |
| GET /lab/test HTTP status | 200 | ? | |
| useLabGraphStore in bundle | file found | ? | |
| layout.js in .next/server/app/lab | present | ? | |
| ClassicMode in bundle | file found | ? | |
| API diff empty | empty | ? | |
| Prisma diff empty | empty | ? | |
| API health check | 200 or N/A | ? | |

**6. Final Judgment**
- Phase 1B successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- Classic mode operational: yes / no
- Guest mode not broken: yes / no
- Ready for Phase 2A development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 1B.
```
