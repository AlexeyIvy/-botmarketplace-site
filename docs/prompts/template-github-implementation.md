# Шаблон промта — Реализация Stage на GitHub

> Используй этот шаблон при написании промта для Claude Code в GitHub-сессии
> (написание кода, коммит, открытие PR).
> Заполни все секции в `{{...}}`. Секции с `[если есть]` — опциональны.

---

```
Ты — Claude Code, работаешь в GitHub-репозитории botmarketplace-site.

## Задача

Реализуй {{STAGE_NUMBER}} — {{STAGE_NAME}}.
Ветка для разработки: `{{BRANCH_NAME}}`.

Документ требований: `docs/steps/{{NN}}-stage-{{N}}-{{slug}}.md`
Roadmap: `docs/21-project-stages.md`

---

## Контекст

{{STAGE_NAME}} — {{1–2 предложения: что это, зачем, в какую картину вписывается}}.

Базируется на: {{предыдущий Stage/Phase}}.
Следующий этап: {{следующий Stage/Phase}}.

---

## Scope — что реализовать

{{Пронумерованный список функциональности, например:}}
1. `POST /exchanges` — создать ExchangeConnection, зашифровать secret (AES-256-GCM)
2. `GET /exchanges` — список подключений без секретов
3. `GET /exchanges/:id` — одно подключение без секретов
4. `PATCH /exchanges/:id` — обновить, перешифровать secret при изменении
5. `DELETE /exchanges/:id` — удалить
6. `POST /exchanges/:id/test` — проверить подключение (demo-first: всегда CONNECTED)
7. Все endpoints: `authenticate` + `resolveWorkspace()`
8. Обновить OpenAPI контракт

---

## Out of scope — что НЕ реализовывать

- {{Пункт 1}} ({{причина или Stage, где это будет}}
- {{Пункт 2}}
- {{Пункт 3}}

---

## Файлы для создания / изменения

| Файл | Действие | Описание |
|------|----------|----------|
| `apps/api/prisma/schema.prisma` | изменить | добавить модель `{{ModelName}}` |
| `apps/api/prisma/migrations/{{date}}_{{slug}}/migration.sql` | создать | аддитивная миграция |
| `apps/api/src/lib/{{helper}}.ts` | создать | {{что делает}} |
| `apps/api/src/routes/{{route}}.ts` | создать | {{endpoints}} |
| `apps/api/src/app.ts` | изменить | зарегистрировать `{{routeName}}Routes` |
| `apps/web/src/app/{{page}}/page.tsx` | создать/изменить | {{UI}} |
| `docs/openapi/openapi.yaml` | изменить | добавить schemas + paths |
| `docs/steps/{{NN}}-stage-{{N}}-{{slug}}.md` | создать | документация Stage |

[если только backend] Фронтенд не меняется.
[если только frontend] Бекенд и БД не меняются.

---

## Ключевые паттерны проекта (обязательно соблюдать)

**Auth & Workspace:**
- Все приватные endpoints: `onRequest: [app.authenticate, app.resolveWorkspace]`
- Workspace ID берётся из `request.workspaceId` (установлен middleware)
- Cross-workspace доступ → 403 (обрабатывается в `resolveWorkspace`)

**Error format (RFC 9457 Problem Details):**
```ts
reply.status(404).send({
  type: 'about:blank',
  title: 'Not Found',
  status: 404,
  detail: 'Resource not found',
})
```

**Prisma queries:**
- Всегда фильтровать по `workspaceId` в `where`
- `findUnique` вместо `findFirst` где есть уникальный ключ

**TypeScript:**
- `strict: true` — нет `any`, нет `!` non-null assertions без обоснования
- Типы выносить в отдельные interface/type, не inline

**Логирование:**
- Только `{ userId, workspaceId }` — никаких токенов, паролей, секретов

[если есть шифрование]
**Шифрование:**
- Использовать `apps/api/src/lib/crypto.ts` (AES-256-GCM, уже реализован)
- Никогда не возвращать `encryptedSecret`, `apiKey`, `secret` в API-ответах

[если есть Prisma миграция]
**Prisma миграции:**
- Только аддитивные изменения (новые поля nullable или с DEFAULT)
- Без `DROP COLUMN`, без изменения типов существующих полей
- Имя миграции: `{{YYYYMMDD}}{{letter}}_{{slug}}`

---

## Acceptance criteria

- [ ] TypeScript: 0 ошибок (`pnpm --filter @botmarketplace/api exec tsc --noEmit`)
- [ ] TypeScript web: 0 ошибок (`pnpm --filter @botmarketplace/web exec tsc --noEmit`)
- [ ] API build: exit code 0 (`pnpm build:api`)
- [ ] Web build: exit code 0 (`pnpm build:web`)
- [ ] Prisma migrate: exit code 0 [если есть миграция]
- [ ] Все новые endpoints возвращают правильные HTTP коды
- [ ] 401 без токена, 403 при cross-workspace, 200/201 на валидный запрос
- [ ] Нет секретов / паролей в API-ответах и логах
- [ ] OpenAPI обновлён [если есть новые endpoints]
- [ ] `docs/steps/{{NN}}-stage-{{N}}-{{slug}}.md` создан и заполнен

---

## Команды проверки (выполни перед коммитом)

```bash
# TypeScript
pnpm --filter @botmarketplace/api exec tsc --noEmit
pnpm --filter @botmarketplace/web exec tsc --noEmit

# Builds
pnpm build:api
pnpm build:web

# [если есть миграция] Prisma
pnpm db:generate
```

---

## Git

Ветка: `{{BRANCH_NAME}}`
Формат коммита: `feat({{scope}}): Stage {{N}} — {{STAGE_NAME}}`

После реализации:
1. Убедись что все acceptance criteria выполнены
2. Создай коммит с сообщением выше
3. Открой PR в `main` с описанием: что реализовано, какие файлы изменены, acceptance criteria

---

## Формат отчёта (после завершения)

### IMPLEMENTATION REPORT — Stage {{N}} ({{STAGE_NAME}})

**1. Реализовано**
- [ ] {{feature 1}}
- [ ] {{feature 2}}
- [ ] ...

**2. Файлы изменений**
| Файл | Действие | Краткое описание |
|------|----------|-----------------|
| `...` | создан/изменён | ... |

**3. TypeScript**
- API: 0 errors / N errors (список если есть)
- Web: 0 errors / N errors (список если есть)

**4. Builds**
- API build: success / failed
- Web build: success / failed
- Prisma migrate: success / N/A

**5. PR**
- PR URL:
- Branch: `{{BRANCH_NAME}}` → `main`

**6. Что отложено (deferred)**
- {{item}} → Stage {{N+1}}
```

---

## Как пользоваться

1. Скопируй весь текст внутри `` ``` `` блока
2. Заполни все `{{...}}` плейсхолдеры
3. Удали опциональные секции `[если есть]` если они не применимы
4. Вставь в Claude Code (GitHub-сессия)
