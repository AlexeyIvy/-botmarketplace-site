# Stage 8 — Exchange Connections (demo-first)

## Status: DONE

## 1) Scope

- CRUD `ExchangeConnection` (create / list / get / patch / delete)
- `POST /exchanges/:id/test` — demo-first connectivity check
- AES-256-GCM secret encryption via `SECRET_ENCRYPTION_KEY` env
- All endpoints: `authenticate` + `resolveWorkspace()` enforcement
- API never returns `apiKey`, `secret`, or `encryptedSecret`
- OpenAPI contract updated

## 2) Scope boundaries (что НЕ сделано)

- Нет Vault / KMS / pgcrypto
- Нет production-grade secret manager
- Нет real-money execution или биржевых вызовов (Stage 9b)
- Нет RBAC
- Нет UI (backend + OpenAPI контракт)

## 3) Environment requirements

`SECRET_ENCRYPTION_KEY` — обязательная переменная окружения для Stage 8.
Формат: 64 hex-символа (32 bytes).

Генерация:
```sh
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

При отсутствии или неверном формате все endpoints, требующие шифрования (`POST /exchanges`, `PATCH /exchanges/:id` с `secret`, `POST /exchanges/:id/test`), вернут:

```json
{
  "type": "about:blank",
  "title": "Server Configuration Error",
  "status": 500,
  "detail": "Secret encryption key is not configured. Set SECRET_ENCRYPTION_KEY env variable."
}
```

## 4) Файлы изменений

| Файл | Тип |
|------|-----|
| `apps/api/prisma/schema.prisma` | добавлена модель `ExchangeConnection` + enum `ExchangeConnectionStatus` |
| `apps/api/prisma/migrations/20260221a_add_exchange_connections/migration.sql` | новая миграция |
| `apps/api/src/lib/crypto.ts` | новый: AES-256-GCM encrypt/decrypt + `getEncryptionKey()` |
| `apps/api/src/routes/exchanges.ts` | новый: CRUD + test connection |
| `apps/api/src/app.ts` | регистрация `exchangeRoutes` |
| `docs/openapi/openapi.yaml` | добавлены Exchange Connection endpoints + schemas |
| `docs/steps/08-stage-8-exchange-connections.md` | этот файл |

## 5) Verification commands

### Предварительно

```sh
export BASE=http://localhost:3000/api/v1
export SECRET_ENCRYPTION_KEY=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")

# Зарегистрировать / залогиниться
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}' | jq -r '.accessToken')

WORKSPACE_ID=<your-workspace-id>
```

### CREATE
```sh
curl -s -X POST $BASE/exchanges \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"exchange":"BYBIT","name":"Main","apiKey":"key123","secret":"sec456"}' | jq .
# → 201, содержит id/exchange/name/status=UNKNOWN, НЕТ secret/encryptedSecret/apiKey
```

### LIST
```sh
curl -s $BASE/exchanges \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" | jq .
# → 200, массив без секретов
```

### GET
```sh
CONN_ID=<id из CREATE>
curl -s $BASE/exchanges/$CONN_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" | jq .
# → 200, без секретов
```

### PATCH (перешифрование)
```sh
curl -s -X PATCH $BASE/exchanges/$CONN_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"secret":"newsecret789"}' | jq .
# → 200, status сброшен в UNKNOWN, secretов нет в ответе
```

### TEST CONNECTION
```sh
curl -s -X POST $BASE/exchanges/$CONN_ID/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" | jq .
# → 200, {"id":"...","status":"CONNECTED","detail":"Credentials verified (demo-first...)"}
```

### DELETE
```sh
curl -s -X DELETE $BASE/exchanges/$CONN_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID"
# → 204
```

### Cross-workspace → 403
```sh
curl -s $BASE/exchanges \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: <OTHER_WORKSPACE_ID>" | jq .
# → 403
```

### Without auth → 401
```sh
curl -s $BASE/exchanges | jq .
# → 401
```

### Missing SECRET_ENCRYPTION_KEY → 500
```sh
SECRET_ENCRYPTION_KEY="" node ... # запустить сервер без ключа
curl -s -X POST $BASE/exchanges \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WORKSPACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"exchange":"BYBIT","name":"Test","apiKey":"k","secret":"s"}' | jq .
# → 500, "Server Configuration Error"
```

## 6) Acceptance checklist

- [x] CRUD exchange connections работает
- [x] Все endpoints защищены `authenticate`
- [x] Везде используется `resolveWorkspace()`
- [x] Секрет хранится в `encryptedSecret` (AES-256-GCM)
- [x] Используется `SECRET_ENCRYPTION_KEY`
- [x] Секреты не возвращаются в API (redaction через `safeView()`)
- [x] `test connection` реализован (demo-first)
- [x] OpenAPI обновлён
- [x] Handover notes для Stage 9b добавлены
- [x] Нет scope creep

## 7) Handover для Stage 9b (Terminal Manual Order Flow)

### Как использовать `ExchangeConnection`

Stage 9b получает готовую сущность подключения к бирже.

**Получить подключение для выполнения ордера:**
```typescript
import { prisma } from "../lib/prisma.js";
import { decrypt } from "../lib/crypto.js";

const conn = await prisma.exchangeConnection.findUnique({ where: { id: connectionId } });
// conn.workspaceId === workspace.id (уже проверено resolveWorkspace)

const key = Buffer.from(process.env.SECRET_ENCRYPTION_KEY!, "hex");
const secret = decrypt(conn.encryptedSecret, key);
// → используй conn.apiKey + secret для инициализации Bybit SDK
```

**Доступные поля:**
- `id`, `workspaceId`, `exchange` (например `"BYBIT"`), `name`, `apiKey`
- `encryptedSecret` — расшифровать через `decrypt()`
- `status` — `UNKNOWN | CONNECTED | FAILED` (обновлять после реального вызова)

**Паттерн обновления статуса после реального вызова:**
```typescript
await prisma.exchangeConnection.update({
  where: { id: conn.id },
  data: { status: "CONNECTED" }, // или "FAILED"
});
```

### Ограничения demo-first (остаются к Stage 9b)

- `POST /exchanges/:id/test` не делает реальный биржевой вызов — Stage 9b должен заменить stub на `GET /v5/account/info` (Bybit) или аналог
- `apiKey` хранится в plain text — для production потребует отдельного решения (deferred)
- Нет ротации ключей и key versioning

## 8) Deviations

Нет отклонений от заявленного scope Stage 8.
`apiKey` хранится plain (по условию задачи: "apiKey можно хранить как обычное поле (demo-first)").
