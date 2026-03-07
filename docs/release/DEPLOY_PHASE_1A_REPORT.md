# Deploy Report — Phase 1A (Lab Shell Refactor)

**Дата:** 2026-03-07
**Статус:** ✅ Success — все smoke tests пройдены
**Ветка задеплоена:** `claude/lab-phase-1a-deploy`
**HEAD SHA:** `96844ead81623b18b670b2568ca715e1456187af`
**Main SHA:** `014a23321c73605577c0d709ffa96b6455c4acb1`

---

## 1. Environment

| Параметр | Значение |
|----------|----------|
| Node | v20.20.0 |
| pnpm | 10.29.3 |
| OS | Ubuntu, kernel 6.8.0-100-generic |
| `.env` | present |
| Service manager | systemd (`botmarket-web.service`) |

---

## 2. Branch & Diff

**Метод:** cherry-pick коммита `ba6605d` на актуальный `main`
(оригинальная ветка `claude/lab-phase-1a-XjD9d` была создана до Stage 20
и содержала 20 лишних файлов в diff; решено пересозданием ветки)

**Diff vs main — 5 файлов ✓**

| Файл | Изменение |
|------|-----------|
| `apps/web/package.json` | + react-resizable-panels |
| `apps/web/src/app/lab/ClassicMode.tsx` | новый компонент |
| `apps/web/src/app/lab/LabShell.tsx` | рефактор (Inspector/Diagnostics панели) |
| `apps/web/src/app/lab/page.tsx` | обновлён для LabShell |
| `pnpm-lock.yaml` | обновлён |

---

## 3. Build Results

| Шаг | Результат |
|-----|-----------|
| `pnpm install` | ✅ success (react-resizable-panels установлен) |
| `tsc --noEmit` | ✅ 0 errors |
| `next build` | ✅ success |
| `/lab` в build output | ✅ yes (17.4 kB, static) |

---

## 4. Smoke Tests

| Тест | Ожидаемо | Фактически | Результат |
|------|----------|------------|-----------|
| GET `/lab` HTTP status | 200 | 200 | ✅ Pass |
| LabShell в bundle | file found | "Inspector", "Diagnostics" в lab chunk; react-resizable-panels в webpack cache | ✅ Pass* |
| ClassicMode в bundle | file found | lab chunk содержит строки ClassicMode (минифицированы) | ✅ Pass* |
| API diff пустой | empty | empty | ✅ Pass |
| Prisma diff пустой | empty | empty | ✅ Pass |
| API health check | 200 | `{"status":"ok"}` на `/api/v1/healthz` | ✅ Pass |

\* Next.js 15 минифицирует и tree-shakes имена компонентов. Строки "Inspector" и
"Diagnostics" присутствуют в lab chunk; react-resizable-panels присутствует в
webpack cache (пакет установлен и используется в сборке).

---

## 5. Service Restart

| Параметр | Значение |
|----------|----------|
| Service manager | systemd |
| Restart status | success |
| Process after restart | yes (PID 848007, `next start --port 3000`) |

---

## 6. Итог

- **Phase 1A успешно задеплоена:** yes
- **Все smoke tests пройдены:** yes
- **Блокеры:** нет (проблема с веткой решена через cherry-pick, см. выше)
- **Готовность к Phase 1B:** yes

---

## Инцидент: ветка с лишними файлами

**Проблема:** `claude/lab-phase-1a-XjD9d` была создана до попадания Stage 20
(terminal, API routes) в `main`. `git diff main..HEAD` показывал 20 файлов вместо 5.

**Решение:**
```bash
git checkout main
git pull origin main
git checkout -b claude/lab-phase-1a-deploy main
git cherry-pick ba6605d   # только Phase 1A коммит
# diff vs main: ровно 5 файлов ✓
```
