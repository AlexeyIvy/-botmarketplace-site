# VPS Deploy Prompt — Phase 1A (Lab Shell Refactor)

Скопируй этот промт целиком в терминальный Claude Code на VPS.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить Phase 1A — Lab Shell Refactor.
Это frontend-only изменение. Бекенд, база данных и API не затронуты.

### Что такое Phase 1A

Phase 1A — первая фаза Lab v2 IDE (doc: docs/23-lab-v2-ide-spec.md).

Содержимое коммита:
- `apps/web/src/app/lab/LabShell.tsx` — новый multi-panel IDE shell
  (react-resizable-panels: Context Bar + табы Classic/Data/Build/Test + Inspector + Diagnostics)
- `apps/web/src/app/lab/ClassicMode.tsx` — весь существующий /lab функционал
  (StrategyList, DslEditor, AiChat, BacktestReport) вынесен в отдельный компонент
- `apps/web/src/app/lab/page.tsx` — обновлён: guest mode без shell, auth mode через LabShell
- `apps/web/package.json` — добавлена зависимость react-resizable-panels
- `pnpm-lock.yaml` — обновлён lockfile

Phase 1A не содержит:
- изменений бекенда (apps/api/)
- изменений БД (Prisma schema)
- новых API endpoints
- Zustand store wiring (это Phase 1B)
- реального функционала вкладок Data/Build/Test (только placeholder)

### Ветка для деплоя

Branch: `claude/lab-phase-1a-XjD9d`
Базовый коммит Phase 1A SHA: `731ca7b2fe4423cd43990c55b36b71a6f93d58c6`
(на VPS SHA будет отличаться из-за cherry-pick, но содержимое идентично)

---

## Задача: задеплоить Phase 1A на VPS

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

4. Проверь, есть ли .env или нужные переменные окружения:
   ```
   test -f .env && echo ".env exists" || echo "no .env"
   test -f apps/web/.env.local && echo "web .env.local exists" || echo "no web .env.local"
   ```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить Phase 1A ветку

```
git fetch origin claude/lab-phase-1a-XjD9d
git checkout claude/lab-phase-1a-XjD9d
git log --oneline -3
```

Убедись, что HEAD содержит коммит с сообщением:
`feat(lab): Phase 1A — Lab shell refactor (UI only, no backend)`

Проверь diff против main (должны быть только 5 файлов):
```
git diff --name-only main..HEAD
```

Ожидаемый результат:
```
apps/web/package.json
apps/web/src/app/lab/ClassicMode.tsx
apps/web/src/app/lab/LabShell.tsx
apps/web/src/app/lab/page.tsx
pnpm-lock.yaml
```

Если в diff есть что-то кроме этих 5 файлов — ОСТАНОВИСЬ и сообщи об этом.
Если файлов меньше 5 — ОСТАНОВИСЬ.

---

### ШАГ 2 — Установка зависимостей

```
pnpm install --frozen-lockfile
```

Флаг `--frozen-lockfile` обязателен: Phase 1A добавила `react-resizable-panels`,
и lockfile уже зафиксирован в коммите.

Если pnpm install завершился с ошибкой — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 3 — TypeScript проверка (tsc)

```
cd apps/web
npx tsc --noEmit 2>&1
```

Ожидаемый результат: 0 ошибок, команда завершается с кодом 0.

Если есть TypeScript ошибки — зафиксируй полный список и ОСТАНОВИСЬ.
Не исправляй TypeScript ошибки самостоятельно — это выходит за рамки деплоя Phase 1A.

---

### ШАГ 4 — Production build (Next.js)

```
cd /path/to/repo  # вернись в корень репозитория
pnpm build:web 2>&1
```

Это выполнит `next build` для apps/web.

Ожидаемый результат:
- Build завершился успешно (exit code 0)
- В выводе нет `Error:` или `Failed to compile`
- Маршрут `/lab` присутствует в списке собранных страниц

Проверь, что маршрут `/lab` попал в сборку:
```
grep -r "lab" apps/web/.next/server/app --include="*.json" -l 2>/dev/null | head -5
```

Если build упал — зафиксируй полный вывод ошибки и ОСТАНОВИСЬ.

---

### ШАГ 5 — Перезапуск веб-сервиса

Определи, как запущен Next.js на этом VPS, и перезапусти его.

Варианты (проверь и выбери подходящий):

**Вариант A — systemd:**
```
systemctl restart botmarket-web
systemctl status botmarket-web
```

**Вариант B — pm2:**
```
pm2 restart web
pm2 status
pm2 logs web --lines 20
```

**Вариант C — ручной запуск (если нет systemd/pm2):**
```
# Останови существующий процесс
pkill -f "next start" || true
# Запусти в фоне
cd apps/web && nohup pnpm start >> /var/log/botmarket-web.log 2>&1 &
echo "PID: $!"
```

Зафиксируй, какой вариант был использован.

После перезапуска подожди 5 секунд, затем проверь, что процесс запустился:
```
pgrep -a node | grep next
```

---

### ШАГ 6 — Smoke Tests

Это обязательные проверки после деплоя. Выполни все.

**6.1 HTTP проверка /lab маршрута:**
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/lab
```
Ожидается: `200`

**6.2 Проверка, что LabShell.tsx попал в bundle:**
```
grep -r "LabShell\|react-resizable-panels\|ResizablePanels\|lab-shell" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -5
```
Ожидается: минимум 1 файл в результате.

**6.3 Проверка, что ClassicMode.tsx попал в bundle:**
```
grep -r "ClassicMode\|DslEditor\|AiChat\|StrategyList" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -5
```
Ожидается: минимум 1 файл в результате.

**6.4 Проверка отсутствия изменений в API:**
```
git diff main..HEAD -- apps/api/ | head -5
```
Ожидается: пустой вывод (API не затронут).

**6.5 Проверка отсутствия изменений в Prisma schema:**
```
git diff main..HEAD -- packages/shared/prisma/ apps/api/prisma/ 2>/dev/null | head -5
```
Ожидается: пустой вывод (БД не затронута).

**6.6 Проверка health API (если API запущен):**
```
curl -s http://localhost:4000/health 2>/dev/null || echo "API not running or not on 4000"
```
Цель: убедиться, что деплой frontend не сломал API.

---

### ШАГ 7 — Финальная git проверка

```
git log --oneline main..HEAD
git show --stat HEAD
git rev-parse HEAD
git rev-parse origin/main
```

---

## Ограничения — что НЕ делать

- НЕ менять содержимое Phase 1A файлов
- НЕ делать Phase 1B (Zustand store wiring — отдельная задача)
- НЕ делать merge в main
- НЕ трогать apps/api/, Prisma schema, БД миграции
- НЕ "исправлять" TypeScript ошибки, если они появятся — только репортировать
- НЕ запускать db:migrate
- НЕ деплоить API (только frontend)

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — Phase 1A

**1. Environment**
- Node version:
- pnpm version:
- OS:
- .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown

**2. Branch & Commit**
- Branch deployed: claude/lab-phase-1a-XjD9d
- HEAD SHA:
- main SHA:
- diff files count vs main: (must be 5)
- Files in diff: (list them)

**3. Build Results**
- pnpm install: success / failed (with error)
- TypeScript (tsc --noEmit): 0 errors / N errors (list if any)
- next build: success / failed (with error)
- /lab route in build output: yes / no

**4. Service Restart**
- Service manager used:
- Restart status: success / failed
- Process running after restart: yes / no

**5. Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| GET /lab HTTP status | 200 | ? | |
| LabShell in bundle | file found | ? | |
| ClassicMode in bundle | file found | ? | |
| API diff empty | empty | ? | |
| Prisma diff empty | empty | ? | |
| API health check | 200 or N/A | ? | |

**6. Final Judgment**
- Phase 1A successfully deployed: yes / no
- All smoke tests passed: yes / no
- Any blockers found: (describe or "none")
- Ready for Phase 1B development: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему,
не пытайся её обойти самостоятельно, если это выходит за рамки деплоя Phase 1A.
```
