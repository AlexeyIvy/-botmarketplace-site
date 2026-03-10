# Шаблон промта — Деплой Stage на VPS

> Используй этот шаблон при написании промта для Claude Code в VPS-сессии
> (pull, build, migrate, restart, smoke tests).
> Заполни все секции в `{{...}}`. Секции `[если есть]` — опциональны.

---

```
Ты — Claude Code, запущен на VPS с доступом к репозиторию botmarketplace-site.

## Контекст задачи

Задача: задеплоить {{STAGE_NUMBER}} — {{STAGE_NAME}}.
{{1–2 предложения: что затрагивает — backend/frontend/db/или только docs.}}

### Что такое {{STAGE_NUMBER}}

{{2–5 пунктов: ключевые изменения в коде. Конкретно: что за функция, какой файл, какое поведение.}}

**Изменённые файлы:**
| Файл | Описание |
|------|----------|
| `{{path/to/file.ts}}` | {{что изменено}} |
| `{{path/to/file.tsx}}` | {{что изменено}} |

[если есть Prisma]
**Prisma миграция:** `{{migration_name}}` — {{что делает, аддитивная/breaking}}.

[если только docs]
Производственный код уже в `main` (был смержен ранее). Этот PR содержит только docs.

{{STAGE_NUMBER}} НЕ содержит:
- {{Что явно вне scope}} ({{причина}}
- {{Пункт 2}}

### Ветка для деплоя

Branch: `{{main или feature-branch}}`
Merge commit SHA: `{{full SHA}}`
Базируется на: {{предыдущий Stage/Phase SHA коротко}}
Commit message: `{{git commit message}}`

---

## Задача: задеплоить {{STAGE_NUMBER}} на VPS

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

[если есть специфические pre-checks для этого Stage:]
# {{Stage-specific check}}
{{grep -n "..." apps/api/src/...}}
# Ожидается: {{что именно}}
```

Зафиксируй результаты — они войдут в финальный отчёт.

---

### ШАГ 1 — Получить {{STAGE_NUMBER}}

```bash
git fetch origin {{branch}}
git checkout {{branch}}
git pull origin {{branch}}
git log --oneline -3
```

Убедись что HEAD содержит нужный коммит:
```bash
git rev-parse HEAD
# Ожидается SHA: {{full SHA}}
```

Если SHA отличается:
```bash
git log --oneline --all | grep -i "{{stage name keywords}}"
```

[если нужна проверка diff]
Проверь diff относительно предыдущего Stage:
```bash
git diff --name-only {{prev SHA short}}..HEAD
```
Ожидаемый результат:
```
{{list of expected files}}
```

Проверь ключевые файлы на месте:
```bash
{{grep or test -f команды для проверки ключевых артефактов Stage}}
# Ожидается: {{что именно}}
```

[проверь что предыдущие Stage файлы не потеряны]
```bash
test -f {{critical file from prev stage}} && echo "OK" || echo "MISSING"
```

---

### ШАГ 2 — Установка зависимостей

[если Stage добавляет npm пакеты]
```bash
pnpm install
```

[если Stage НЕ добавляет npm пакеты]
{{STAGE_NUMBER}} не добавляет новых npm пакетов:
```bash
pnpm install --frozen-lockfile
```

Если завершился с ошибкой — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

[если есть Prisma миграция]
### ШАГ 3 — Prisma миграция

```bash
pnpm db:migrate
```
Ожидаемый результат: `{{migration_name}}` применена, exit code 0.

Проверь применение:
```bash
pnpm db:generate
{{проверочный grep по schema.prisma}}
```
Ожидается: {{что именно}}.

Если миграция упала — ОСТАНОВИСЬ. Не применяй SQL вручную.

---

[если нет Prisma миграции]
### ШАГ 3 — Prisma generate

{{STAGE_NUMBER}} не содержит Prisma миграций. Только пересборка клиента:
```bash
pnpm db:generate
```
Ожидаемый результат: `Prisma Client generated successfully` (exit code 0).

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

### ШАГ 5 — Production builds

**5.1 — API build:**
```bash
pnpm build:api 2>&1
```
Ожидаемый результат: exit code 0.
```bash
test -f apps/api/dist/server.js && echo "API dist OK" || echo "MISSING dist/server.js"
```

**5.2 — Web build (Next.js):**
```bash
pnpm build:web 2>&1
```
Ожидаемый результат: exit code 0, нет `Error:` / `Failed to compile`.

Ожидаемые страницы в выводе next build:
```
○ /
○ /login
○ /lab
[добавь страницы из этого Stage]
{{○ /{{new_page}}}}
```

Если любой build упал — зафиксируй полный вывод и ОСТАНОВИСЬ.

---

### ШАГ 6 — Проверка bundle

**6.1 — Артефакты {{STAGE_NUMBER}} в bundle:**
```bash
grep -r "{{key string from this Stage}}" \
  apps/api/dist/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

[если frontend]
```bash
grep -r "{{key component or string}}" \
  apps/web/.next/static/chunks/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

**6.2 — Регрессия предыдущего Stage:**
```bash
grep -r "{{key string from prev Stage}}" \
  apps/{{api/web}}/ --include="*.js" -l 2>/dev/null | head -3
# Ожидается: минимум 1 файл
```

---

### ШАГ 7 — Перезапуск сервисов

[укажи, что нужно перезапускать. Если только backend — можно не трогать web]

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

[добавь проверки страниц из предыдущих Stage]
```

---

### ШАГ 9 — Smoke Tests: {{STAGE_NUMBER}} (ОБЯЗАТЕЛЬНО)

[Это самая Stage-специфичная секция. Опиши конкретные API/UI тесты.]

**Подготовка:**
```bash
export BASE=http://localhost:4000/api/v1

# Зарегистрировать / залогиниться
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_{{stage}}@test.local","password":"SmokeTest1!"}')
echo "$REG"

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN length: ${#TOKEN}  WS_ID: $WS_ID"
```

Если TOKEN пустой — auth не работает, ОСТАНОВИСЬ.

**9.1 — {{Test name}}:**
```bash
S1=$(curl -s -o /dev/null -w "%{http_code}" \
  {{endpoint}} \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
echo "Test 9.1 ({{description}}) → $S1 (expected: {{code}})"
```

**9.2 — {{Test name}}:**
```bash
S2=$(curl -s {{endpoint}} \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" | {{grep or jq check}})
echo "Test 9.2: $S2"
```

[добавляй тесты по необходимости]

[если Stage включает security:]
**9.X — Нет токена → 401:**
```bash
curl -s -o /dev/null -w "%{http_code}" {{endpoint}}
# Ожидается: 401
```

**9.X — Cross-workspace → 403:**
```bash
# Зарегистрировать второго пользователя B (его WS_B)
REG_B=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest_{{stage}}_b@test.local","password":"SmokeTest1!"}')
TOKEN_B=$(echo "$REG_B" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_B=$(echo "$REG_B"   | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)

S=$(curl -s -o /dev/null -w "%{http_code}" {{endpoint}} \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_B")
echo "Cross-workspace → $S (expected: 403)"
```

---

### ШАГ 10 — Проверка логов

**10.1 — Есть userId + workspaceId в логах:**
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

### ШАГ 11 — Regression: предыдущие Stage

[добавь проверку ключевых endpoint'ов из предыдущих Stage]

```bash
echo "--- Regression: previous Stages ---"

# {{Prev Stage endpoint}} (нет auth)
curl -s -o /dev/null -w "%{http_code}" \
  $BASE/{{endpoint}} -H "Authorization: Bearer invalid"
# Ожидается: 401 (не 404)

# API health
curl -s $BASE/healthz | grep -o '"status":"ok"'
# Ожидается: "status":"ok"

# Public endpoint (если есть)
curl -s -o /dev/null -w "%{http_code}" \
  "$BASE/terminal/ticker?symbol=BTCUSDT"
# Ожидается: 200
```

---

### ШАГ 12 — Финальная git проверка

```bash
git log --oneline {{prev SHA short}}..HEAD
git show --stat HEAD
git rev-parse HEAD
```
Ожидается в log: `{{commit message keyword}}`.

---

## Ограничения — что НЕ делать

- НЕ менять содержимое файлов вне scope этого Stage
- НЕ применять SQL вручную
- НЕ делать задачи следующего Stage
- НЕ исправлять TypeScript ошибки самостоятельно — только репортировать
- НЕ делать merge или rebase
- {{Другие Stage-специфичные ограничения}}

---

## Формат отчёта

После выполнения всех шагов верни отчёт строго в этом формате:

### DEPLOY REPORT — {{STAGE_NUMBER}} ({{STAGE_NAME}})

**1. Environment**
- Node version:
- pnpm version:
- OS:
- api .env present: yes/no
- Pre-existing service manager: systemd / pm2 / manual / unknown
- PostgreSQL accessible: yes/no
{{- Stage-specific env checks:}}
{{- {{check name}}: yes/no}}

**2. Branch & Commit**
- Branch deployed: {{branch}}
- HEAD SHA:
- Expected SHA: {{full SHA}}
- SHA match: yes/no
{{- Diff files vs prev Stage: (list)}}
{{- {{key file}} present: yes/no}}

**3. Build Results**
- pnpm install: success / failed (with error)
- db:generate: success / failed
{{- db:migrate ({{migration_name}}): success / failed / N/A}}
- TypeScript API (tsc --noEmit): 0 errors / N errors
- TypeScript Web (tsc --noEmit): 0 errors / N errors
- API build (dist/server.js): success / failed
- next build: success / failed
{{- /{{new_page}} in build output: yes/no}}
{{- {{bundle check}}: yes/no}}

**4. Service Restart**
- Service manager used:
- API restart: success / failed
- Web restart: success / failed / skipped (not needed)
- API process running: yes/no
- Web process running: yes/no

**5. Smoke Tests — {{STAGE_NUMBER}}**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| {{test description}} | {{code}} | ? | |
| {{test description}} | {{code}} | ? | |
| [добавить строки по числу тестов] | | | |

**6. Regression Smoke Tests**
| Test | Expected | Actual | Pass/Fail |
|------|----------|--------|-----------|
| API health check | {"status":"ok"} | ? | |
| GET /login HTTP status | 200 | ? | |
| GET /lab HTTP status | 200 | ? | |
| {{prev Stage endpoint}} (no auth) | 401 | ? | |
| [добавить строки по числу регрессий] | | | |

**7. Final Judgment**
- {{STAGE_NUMBER}} successfully deployed: yes / no
- All smoke tests passed: yes / no
- Logs safe (no secrets): yes / no
- Regression from previous Stages: none / (describe)
- API health: ok / degraded
- Ready to proceed to {{next Stage}}: yes / no

---

Если на любом шаге возникает неожиданная ошибка — ОСТАНОВИСЬ и опиши проблему.
Не пытайся обойти её самостоятельно, если это выходит за рамки деплоя {{STAGE_NUMBER}}.
```

---

## Как пользоваться

1. Скопируй весь текст внутри `` ``` `` блока
2. Заполни все `{{...}}` плейсхолдеры
3. Удали опциональные секции `[если есть]` если они не применимы
4. Для ШАГ 9 — напиши конкретные curl-команды под этот Stage
5. Для таблицы в ШАГ 5 отчёта — добавь строки по числу своих тестов
6. Вставь в Claude Code (VPS-сессия)
