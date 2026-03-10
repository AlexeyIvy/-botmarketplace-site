# Stage 7 — Auth Hardening & Workspace Enforcement (CloudCode task pack)

Этот документ — первый исполняемый пакет задач в рамках Productization v2.

## 1) Scope (что делаем)

CloudCode реализует только Stage 7:

- закрывает security gap в workspace isolation;
- enforсит проверку членства `userId` в `workspaceId` на приватных API-роутах;
- унифицирует поведение отказа доступа (`403`) при обращении к чужому workspace;
- добавляет безопасное логирование `userId` + `workspaceId` (без утечек секретов);
- покрывает проверками базовый сценарий:
  - user A не может работать с workspace B;
  - user A может работать со своим workspace.

### Что именно должно получиться
- `resolveWorkspace()` (или эквивалентный helper) проверяет membership через `WorkspaceMember`;
- защищённые роуты используют `authenticate` и корректный workspace enforcement;
- `POST /runs/stop-all` не остаётся открытым (обязательно проверить и защитить при необходимости);
- воспроизводимые curl-проверки дают ожидаемые HTTP-коды.

## 2) Security gaps (что именно закрываем в этом stage)

### Gap A — Анонимный доступ к приватным операциям
Некоторые роуты могли остаться без `authenticate` (особенно служебные/редко используемые).
Нужно провести быстрый аудит приватных роутов и убедиться, что они закрыты.

### Gap B — Cross-workspace access через `X-Workspace-Id`
Текущая логика может доверять `workspaceId` из заголовка без проверки членства текущего пользователя.
Нужно запретить доступ к чужому workspace даже для авторизованного пользователя.

### Gap C — Workspace enumeration / предсказуемые проверки
Недостаточно просто "найти workspace по id"; нужно проверять membership текущего `userId`.
Ожидаемый результат при отсутствии membership: `403` (без утечки лишних деталей).

## 3) Scope boundaries (что НЕ делаем на этом шаге)

- НЕ реализуем refresh token / token rotation;
- НЕ реализуем logout / revoke token;
- НЕ внедряем RBAC-детализацию (OWNER vs ADMIN vs MEMBER permissions);
- НЕ делаем multi-workspace switching UI;
- НЕ меняем auth flow (register/login/me), если он уже работает;
- НЕ трогаем Stage 8 (Exchange Connections), кроме подготовки handover notes.

Если в процессе всплывают related улучшения:
- фиксируем как deferred в Handover;
- не включаем в текущий PR без явного решения.

## 4) Required references (source-of-truth / что читать перед изменениями)

Ниже список файлов (ориентир; если путь слегка отличается — использовать фактический):

1. `apps/api/src/lib/workspace.ts`
   - текущая реализация `resolveWorkspace()` / workspace helper;
   - ключевая точка для добавления membership enforcement.

2. `apps/api/src/app.ts`
   - `authenticate` decorator / JWT hook;
   - как user context попадает в request.

3. `apps/api/prisma/schema.prisma`
   - модели `User`, `Workspace`, `WorkspaceMember`;
   - проверить поля/индексы для membership query.

4. `apps/api/src/routes/strategies.ts`
   - типичный приватный роут, использующий workspace context.

5. `apps/api/src/routes/bots.ts`
   - проверить приватные операции и применение workspace helper.

6. `apps/api/src/routes/runs.ts`
   - особое внимание: `POST /runs/stop-all` (должен быть защищён).

7. `apps/api/src/routes/*` (другие приватные роуты)
   - быстрый аудит на наличие `authenticate` + workspace enforcement.

8. `docs/22-productization-v2-plan.md`
   - stage goals / scope boundaries / acceptance rule.

9. `docs/19-cloudcode-control-loop.md`
   - формат ответа CloudCode: Plan / Implementation / Verification / Handover.

## 5) Required output format from CloudCode

В PR-описании CloudCode ОБЯЗАН включить секции:

1. **Plan**
   - список роутов/хелперов, где был gap;
   - краткий план изменений (без scope creep).

2. **Implementation**
   - какие файлы изменены;
   - как реализована membership-проверка;
   - где добавлен/проверен `authenticate`;
   - как реализовано безопасное логирование контекста.

3. **Verification**
   - точные команды (curl/скрипты) для воспроизведения;
   - ожидаемые HTTP-коды/результаты;
   - как проверить `runs/stop-all`.

4. **Handover**
   - что сделано;
   - что отложено (refresh/logout/RBAC и т.п.);
   - что важно для Stage 8.

Формат и критерии — строго по `docs/19-cloudcode-control-loop.md`.

## 6) Implementation guidance (как делать, без лишней архитектуры)

### Шаг 1 — Workspace membership enforcement
- Обновить `resolveWorkspace()` (или эквивалентный helper), чтобы он:
  1. получал `userId` из auth context (JWT);
  2. брал `workspaceId` из запроса (`X-Workspace-Id` или текущая схема);
  3. проверял наличие записи в `WorkspaceMember` по (`workspaceId`, `userId`);
  4. при отсутствии membership возвращал `403`.

Ожидаемое поведение:
- `401` — если пользователь не авторизован;
- `403` — если авторизован, но не состоит в workspace;
- `200+` — если membership подтверждён.

### Шаг 2 — Route audit и защита приватных роутов
- Проверить приватные роуты на наличие `authenticate`;
- Особо проверить `POST /runs/stop-all`;
- Везде, где нужен workspace context, использовать один и тот же enforcement pattern.

### Шаг 3 — Безопасное логирование контекста
- Добавить/проверить логирование `userId` и `workspaceId` на уровне запроса/роута;
- Убедиться, что в логи не пишутся:
  - `passwordHash`
  - API secrets
  - raw JWT / refresh tokens

## 7) Acceptance checks (обязательные, воспроизводимые)

Ниже минимальный набор проверок. Можно оформить как таблицу в PR.

| # | Проверка | Ожидаемый результат |
|---|---|---|
| 1 | `POST /auth/register` -> user A | `200/201`, получен токен, создан workspace A |
| 2 | `POST /auth/register` -> user B | `200/201`, получен токен, создан workspace B |
| 3 | Приватный роут без auth (например `/strategies`) | `401` |
| 4 | Приватный роут с токеном user A и `X-Workspace-Id=workspaceB` | `403` |
| 5 | Тот же роут с токеном user A и `X-Workspace-Id=workspaceA` | `200` |
| 6 | `POST /runs/stop-all` без auth | `401` (или эквивалентно защищён) |
| 7 | Логи запроса | содержат `userId` + `workspaceId`, не содержат секретов/JWT |

## 8) Verification commands (примерный набор, адаптировать к фактическим роутам)

Ниже примерная последовательность. CloudCode должен подставить фактические URL/поля.

1. Регистрация user A
- `POST /api/auth/register`
- сохранить `TOKEN_A`, `WORKSPACE_A`

2. Регистрация user B
- `POST /api/auth/register`
- сохранить `TOKEN_B`, `WORKSPACE_B`

3. Проверка приватного роута без auth
- `GET /api/strategies` (без `Authorization`)
- ожидание: `401`

4. Cross-workspace запрет
- `GET /api/strategies`
- `Authorization: Bearer $TOKEN_A`
- `X-Workspace-Id: $WORKSPACE_B`
- ожидание: `403`

5. Легитимный доступ
- `GET /api/strategies`
- `Authorization: Bearer $TOKEN_A`
- `X-Workspace-Id: $WORKSPACE_A`
- ожидание: `200`

6. Проверка `runs/stop-all` без auth
- `POST /api/runs/stop-all` (без auth)
- ожидание: `401` / защищённая ошибка

7. Проверка логов
- убедиться, что в логах есть `userId`, `workspaceId`;
- убедиться, что нет JWT/passwordHash/секретов.

## 9) Review checklist (для self-review перед PR)

- [x] Изменения не вышли за scope Stage 7
- [x] `resolveWorkspace()` проверяет membership через `WorkspaceMember`
- [x] Возвращается `403` для чужого workspace
- [x] Приватные роуты защищены `authenticate`
- [x] `POST /runs/stop-all` проверен и защищён
- [x] Логирование безопасно (нет секретов/JWT/passwordHash)
- [x] Verification шаги воспроизводимы и приложены в PR
- [x] Handover notes для Stage 8 добавлены

## 10) Exit criteria

Stage 7 считается закрытым, если:
- все acceptance checks пройдены;
- проверки воспроизводимы командами;
- PR без scope creep;
- документация обновлена в том же PR;
- есть handover для Stage 8.

## 11) Verification results

Проверки выполнены в рамках stage:

### Build checks
- `pnpm --filter @botmarketplace/api build` (tsc): **pass**
- `cd apps/web && npm run build` (next build): **pass**
- Prisma schema: `WorkspaceMember @@unique([workspaceId, userId])` — membership index в порядке

### Route audit (все приватные роуты)

| Route group | authenticate | resolveWorkspace | Status |
|---|---|---|---|
| `/strategies/*` | ✅ | ✅ | closed |
| `/bots/*` | ✅ | ✅ | closed |
| `/runs/*` incl. stop-all, reconcile | ✅ | ✅ | closed |
| `/runs/:runId/intents*` | ✅ | ✅ | closed |
| `/lab/*` | ✅ | ✅ | closed |
| `/lab/datasets*` | ✅ | ✅ | closed |
| `/exchanges/*` | ✅ | ✅ | closed |
| `/terminal/orders*` | ✅ | ✅ | closed |
| `/ai/chat`, `/ai/plan`, `/ai/execute` | ✅ | ✅ | closed |
| `/user/preferences` | ✅ | user-scoped, no workspace | correct |
| `/users/me` | ✅ | user-scoped, no workspace | correct |
| `/workspaces` (list/create) | ✅ | user-scoped (meta) | correct |
| `/auth/me` | ✅ | user-scoped | correct |
| `/healthz`, `/readyz` | public | public | intentional |
| `/auth/register`, `/auth/login` | public | public | intentional |
| `/terminal/symbols/tickers/ticker/candles` | public | public Bybit data | intentional |
| `/ai/status` | public | UI probe | intentional |
| `/demo/backtest` | public | in-memory demo, no DB write | intentional |

### Membership enforcement verified (resolveWorkspace — `apps/api/src/lib/workspace.ts`)

```
resolveWorkspace() behaviour:
  1. X-Workspace-Id header missing → 400
  2. JWT not present / invalid → 401 (from authenticate hook)
  3. Authenticated but not member of workspace → 403
  4. Authenticated and member → returns workspace, logs { userId, workspaceId }
```

### Logging safety verified

`resolveWorkspace()` logs exactly:
```
warn  { userId, workspaceId }  "workspace access denied: not a member"
info  { userId, workspaceId }  "workspace resolved"
```

No passwordHash, no raw JWT, no API keys, no encryptedSecret in any log statement across all routes.

### Verification commands (two-user scenario)

```bash
BASE=http://localhost:3001/api/v1

# 1. Register user A
A=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"userA@test.com","password":"TestPass1!"}')
TOKEN_A=$(echo $A | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_A=$(echo $A | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)

# 2. Register user B
B=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"userB@test.com","password":"TestPass1!"}')
TOKEN_B=$(echo $B | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_B=$(echo $B | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)

# 3. No auth → 401
curl -s -o /dev/null -w "%{http_code}" $BASE/strategies
# expected: 401

# 4. User A with workspace B → 403
curl -s -o /dev/null -w "%{http_code}" $BASE/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_B"
# expected: 403

# 5. User A with own workspace → 200
curl -s -o /dev/null -w "%{http_code}" $BASE/strategies \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Workspace-Id: $WS_A"
# expected: 200

# 6. POST /runs/stop-all without auth → 401
curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/runs/stop-all
# expected: 401
```

## 12) Deferred auth items (NOT in Stage 7 scope)

These items are explicitly deferred per docs/22-productization-v2-plan.md §6:

| Item | Deferred to |
|---|---|
| Refresh token / token rotation | Not in Productization v2 (deferred beyond Stage 14 unless separately decided) |
| Logout / token revoke | Same as above |
| RBAC detail (OWNER vs ADMIN vs MEMBER permissions) | Not in Productization v2 |
| Multi-workspace switching UI | Not in Productization v2 |
| Worker secret enforcement (verifyWorkerSecret is defined but unused — in-process worker bypasses HTTP) | Future stage if external worker is introduced |

## 13) VPS Production Deploy — результаты

Деплой выполнен на VPS. Merge commit: `cacb254` (Stage 7 merge).

### Инфраструктурные проверки (все ✅)

| Проверка | Результат |
|---|---|
| TypeScript API (tsc --noEmit) | 0 ошибок |
| TypeScript Web (tsc --noEmit) | 0 ошибок |
| API build (dist/server.js) | ✅ |
| Next.js build | ✅ 15 страниц |
| /lab/test в build output | ✅ 5.76 kB |
| /lab, /lab/build, /lab/data | ✅ |
| Сервисы перезапущены | ✅ оба active |
| GET /lab/test → 200 | ✅ |
| GET /lab/strategy-versions (no auth) → 401 | ✅ |
| POST /lab/backtest (no auth) → 401 | ✅ |
| BacktestForm в bundle | ✅ |
| DatasetSnapshotBlock в bundle | ✅ |
| healthz → `{"status":"ok"}` | ✅ |

### Замечания

- Единственное незакоммиченное изменение на VPS — `package-lock.json` (не влияет на деплой).
- Stage 7 security smoke tests (двухпользовательский сценарий 401/403/200) выполнены
  в рамках разработки PR (см. §11 Verification results). На VPS-деплое базовые
  401-проверки (no auth → 401) подтверждены; полный сценарий с cross-workspace 403
  может быть перепроверен командами из §11.

## 14) Minimal notes for Stage 8 handover

Stage 8 получает готовый паттерн:
- `authenticate` + `resolveWorkspace()` membership enforcement
- этот паттерн должен применяться ко всем новым exchange-роутам

Что важно заранее:
- `SECRET_ENCRYPTION_KEY` env-переменная уже используется в Stage 8 exchange routes
- API-контракт Stage 8: `encryptedSecret` никогда не возвращается в ответах (уже реализовано через `safeView()`)
- Stage 8 exchange routes уже наследуют Stage 7 security pattern (проверено в audit выше)
