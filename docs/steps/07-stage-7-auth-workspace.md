# Stage 7 — Auth Hardening & Workspace Enforcement

## Цель

Закрыть два security gap, выявленных после Foundation baseline:

1. **Gap A** — роуты с бизнес-данными (`/strategies`, `/bots`, `/runs`, `/intents`, `/lab`)
   не имеют `onRequest: [app.authenticate]`: любой анонимный запрос с известным `workspaceId`
   получает данные без JWT-проверки.

2. **Gap B** — `resolveWorkspace()` не проверяет членство пользователя в workspace:
   аутентифицированный пользователь может передать чужой `X-Workspace-Id` и получить
   чужие данные.

3. **Gap C** — `GET /workspaces` и `POST /workspaces` открыты без auth, позволяя
   перечислить все workspace-идентификаторы.

## Scope

- Добавить `onRequest: [app.authenticate]` на все роуты, использующие `resolveWorkspace()`
- Обновить `resolveWorkspace()`: добавить проверку `WorkspaceMember` для `userId` из JWT
- Добавить auth на `/workspaces` (GET — фильтровать по userId; POST — привязывать к userId)
- Логировать `userId` + `workspaceId` на каждом защищённом запросе (через `request.log`)
- Обновить этот документ по факту (если что-то отклонилось от плана)

## Scope boundaries (НЕ делаем в этом stage)

- Refresh token / token rotation → deferred
- Logout / token revoke → deferred
- RBAC (различение OWNER / ADMIN / MEMBER прав) → deferred
- Multi-workspace switching UI → deferred
- Изменение frontend (кроме минимальных фиксов, если auth сломается) → deferred
- Любые изменения схемы Prisma → deferred

## Required references

Прочитать перед началом работы:

```
apps/api/src/lib/workspace.ts          ← resolveWorkspace() — текущая реализация
apps/api/src/app.ts                    ← authenticate decorator, JWT setup
apps/api/src/routes/auth.ts           ← JWT payload shape: { sub: userId, email }
apps/api/src/routes/strategies.ts     ← использует resolveWorkspace() без authenticate
apps/api/src/routes/bots.ts           ← использует resolveWorkspace() без authenticate
apps/api/src/routes/runs.ts           ← использует resolveWorkspace() без authenticate
apps/api/src/routes/intents.ts        ← использует resolveWorkspace() без authenticate
apps/api/src/routes/lab.ts            ← использует resolveWorkspace() без authenticate
apps/api/src/routes/workspaces.ts     ← GET/POST без auth, данные всех workspace доступны
apps/api/prisma/schema.prisma         ← WorkspaceMember модель с userId + workspaceId
```

## Required output format

### Phase 1 — Plan

Перед изменениями вывести список:
- Все роуты (метод + путь), которые добавляют `authenticate`
- Сигнатура обновлённой `resolveWorkspace()` (принимает userId)
- Что меняется в `/workspaces` GET и POST

### Phase 2 — Implementation

Порядок изменений:

**Шаг 1** — `apps/api/src/lib/workspace.ts`

Обновить `resolveWorkspace()`:
```typescript
// Новая сигнатура:
export async function resolveWorkspace(
  request: FastifyRequest,
  reply: FastifyReply
): Promise<Workspace | null>
// Логика:
// 1. Читать X-Workspace-Id header → 400 если отсутствует
// 2. Читать userId из request.user.sub (JWT уже верифицирован authenticate)
// 3. Проверить WorkspaceMember { workspaceId, userId } → 403 если нет записи
// 4. request.log.info({ userId, workspaceId }, "workspace resolved")
// 5. Вернуть workspace
```

**Шаг 2** — `apps/api/src/routes/strategies.ts`, `bots.ts`, `runs.ts`, `intents.ts`, `lab.ts`

На каждом роуте, использующем `resolveWorkspace()`, добавить `onRequest: [app.authenticate]`.
Пример:
```typescript
// было:
app.get("/strategies", async (request, reply) => {

// стало:
app.get("/strategies", { onRequest: [app.authenticate] }, async (request, reply) => {
```

**Шаг 3** — `apps/api/src/routes/workspaces.ts`

- `GET /workspaces` → добавить `authenticate`, фильтровать по userId (только workspace, где
  есть `WorkspaceMember` с этим userId)
- `POST /workspaces` → добавить `authenticate`, добавить userId в `WorkspaceMember` при создании

### Phase 3 — Verification

Воспроизводимые команды для проверки (выполнять после `pnpm dev` или против прода):

```bash
API=http://localhost:4000/api/v1

# 1. Зарегистрировать двух пользователей
RESP_A=$(curl -s -X POST $API/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"userA@test.local","password":"passwordA1"}')
TOKEN_A=$(echo $RESP_A | jq -r '.accessToken')
WS_A=$(echo $RESP_A | jq -r '.workspaceId')

RESP_B=$(curl -s -X POST $API/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"userB@test.local","password":"passwordB1"}')
TOKEN_B=$(echo $RESP_B | jq -r '.accessToken')
WS_B=$(echo $RESP_B | jq -r '.workspaceId')

# 2. Анонимный запрос к /strategies → 401
curl -s -o /dev/null -w "%{http_code}" $API/strategies \
  -H "X-Workspace-Id: $WS_A"
# Ожидается: 401

# 3. User A с чужим workspaceId → 403
curl -s -o /dev/null -w "%{http_code}" $API/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_B"
# Ожидается: 403

# 4. User A со своим workspaceId → 200
curl -s -o /dev/null -w "%{http_code}" $API/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_A"
# Ожидается: 200

# 5. GET /workspaces без auth → 401
curl -s -o /dev/null -w "%{http_code}" $API/workspaces
# Ожидается: 401

# 6. GET /workspaces с auth User A → только workspace A, не B
curl -s $API/workspaces \
  -H "Authorization: Bearer $TOKEN_A" | jq '.[].id'
# Ожидается: только WS_A, WS_B не присутствует

# 7. Проверить логи — нет утечки секретов
# В stdout API: grep "workspace resolved" — должен содержать userId и workspaceId
# Не должно быть: passwordHash, accessToken, JWT payload fields кроме sub/email
```

### Phase 4 — Handover

После завершения зафиксировать в PR-описании:

- Список всех изменённых файлов
- Подтверждение, что все 7 проверок выше прошли
- Deferred items (refresh token, RBAC, logout) — ссылка на секцию ниже

## Acceptance checks

| # | Команда / шаг | Ожидаемый результат |
|---|---------------|---------------------|
| 1 | Анонимный GET /strategies с любым X-Workspace-Id | HTTP 401 |
| 2 | GET /strategies с TOKEN_A и WS_B (чужой) | HTTP 403 |
| 3 | GET /strategies с TOKEN_A и WS_A (свой) | HTTP 200 |
| 4 | GET /workspaces без auth | HTTP 401 |
| 5 | GET /workspaces с TOKEN_A | Список не включает WS_B |
| 6 | Логи API | Содержат `userId` + `workspaceId`, нет `passwordHash`/`accessToken` |
| 7 | Все 5 доменных route-файлов | Все роуты с resolveWorkspace() имеют authenticate |

## Review checklist

- [ ] `resolveWorkspace()` проверяет `WorkspaceMember` — не только существование workspace
- [ ] Все роуты с `resolveWorkspace()` имеют `onRequest: [app.authenticate]`
- [ ] `GET /workspaces` фильтрует по userId
- [ ] `POST /workspaces` привязывает userId в WorkspaceMember
- [ ] `request.log.info(...)` не включает чувствительные поля
- [ ] Нет изменений схемы Prisma (scope boundary)
- [ ] Нет изменений frontend (scope boundary, если не сломалось)
- [ ] Deferred items зафиксированы, не реализованы

## Deferred items (фиксируем, не делаем)

| Item | Причина отложить |
|------|-----------------|
| Refresh token / rotation | Усложняет flow, не критично для demo-first |
| Logout / token revoke | Требует blacklist-store или short-lived tokens |
| RBAC (OWNER vs MEMBER) | Нет реальных multi-user сценариев в demo-first |
| Multi-workspace switching UI | UI scope, зависит от Stage 9+ |

## Exit criteria

Stage 7 считается закрытым если:

1. Все 7 acceptance checks воспроизводимы командами выше без ручных правок
2. PR содержит только изменения в scope (workspace.ts, 5 route-файлов, workspaces.ts)
3. Нет изменений Prisma-схемы
4. Документация обновлена в том же PR (этот файл, если были отклонения от плана)
5. Подготовлен handover для Stage 8

---

## Handover для Stage 8 (Exchange Connections)

После закрытия Stage 7 Stage 8 получает:

- Все приватные роуты защищены JWT + workspace membership
- `request.user.sub` содержит `userId` и доступен в любом защищённом хендлере
- `resolveWorkspace()` возвращает `{ id, name }` workspace после проверки членства

Stage 8 добавляет:
- Новую Prisma-модель `ExchangeConnection` (поля: `id`, `workspaceId`, `name`, `exchange`,
  `apiKey`, `encryptedSecret`, `status`, `createdAt`)
- Шифрование: `encryptedSecret` через Node `crypto` (AES-256-CBC или AES-256-GCM),
  ключ из `SECRET_ENCRYPTION_KEY` env-переменной
- CRUD эндпоинты с `authenticate` + `resolveWorkspace()` (паттерн Stage 7)
- Эндпоинт `POST /exchange-connections/:id/test` — проверка подключения к бирже
- API никогда не возвращает `encryptedSecret` в ответах
- Минимальный UI-статус подключения

Договорённости:
- `SECRET_ENCRYPTION_KEY` должен быть добавлен в `.env` и `deploy/setup.sh`
- `apiKey` хранится plaintext (не секрет — публичный идентификатор)
- `encryptedSecret` — приватный ключ API, только зашифрованный вариант в БД
