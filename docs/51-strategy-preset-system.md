# 51. Strategy Preset System

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`

## Контекст

- `Strategy` (`apps/api/prisma/schema.prisma:96`), `StrategyVersion` (`:114`), `Bot` (`:139`) — существуют, мутации идут через Lab + `POST /bots` (`apps/api/src/routes/bots.ts:58`).
- `StrategyPreset` модель **отсутствует**.
- В `apps/api/src/routes/demo.ts:29` лежат 2 hardcoded preset'а (`btc-breakout-demo`, `eth-mean-reversion-demo`) — это in-memory объекты для public-landing, не пользовательская сущность.
- Lab UI: `apps/web/src/app/lab/` (build/, test/, data/), нет library/. Боты создаются в `apps/web/src/app/factory/bots/page.tsx:160`.

## Цель

Ввести `StrategyPreset` как фабрику `StrategyVersion`. Один CRUD + один `instantiate`-эндпоинт + UI-галерея в Lab. После instantiate бот живёт по обычным правилам — runtime про presets не знает (`docs/50 §A1`).

## Не входит

- Никакой preset-семантики в `botWorker.ts`.
- Версионирование пресета (semver, миграции экземпляров) — пресет immutable снаружи; обновление через создание нового пресета.
- Marketplace, paywall, рейтинги.
- Параметризация при instantiate (override defaults) — v1 копирует preset как есть; параметры пользователь меняет в Lab после инстанцирования.
- Замена/удаление hardcoded presets из `routes/demo.ts` — это другая сущность (см. контекст).

## Архитектурные решения

### A1. Preset = (dslJson, executionPlanJson, metadata)

`StrategyPreset.dslJson` и `executionPlanJson` копируются один-в-один в новый `StrategyVersion(version=1)`. Никаких placeholders/templates: DSL уже валиден и компилируется.

### A2. Visibility

`PUBLIC` (видны всем) | `WORKSPACE` (видны только своему workspace) | `PRIVATE` (только автор). Публикация только через миграцию или admin-роут (не через user API в v1) — это даёт acceptance-gate из `docs/50 §A5`.

### A3. Instantiate atomicity

Один `prisma.$transaction`: создать `Strategy` + `StrategyVersion` + `Bot(status=DRAFT)`. Имя бота = `${preset.name} (preset)` с unique-suffix при коллизии.

---

## Задачи

### 51-T1: Prisma модель `StrategyPreset` + миграция

**Цель:** ввести таблицу.

**Файлы:** `apps/api/prisma/schema.prisma`, новая миграция `apps/api/prisma/migrations/<ts>_add_strategy_preset/migration.sql`.

**Шаги:**
1. Добавить enum `PresetVisibility { PUBLIC WORKSPACE PRIVATE }` рядом с `BotStatus` (`schema.prisma:135`).
2. Добавить модель:
   ```prisma
   model StrategyPreset {
     id                String           @id @default(uuid())
     slug              String           @unique
     name              String
     description       String
     category          String
     symbol            String
     timeframe         Timeframe
     dslJson           Json
     executionPlanJson Json
     defaultRiskPct    Float            @default(1.0)
     visibility        PresetVisibility @default(PRIVATE)
     ownerWorkspaceId  String?
     authorLabel       String?
     tagsJson          Json?
     createdAt         DateTime         @default(now())
     updatedAt         DateTime         @updatedAt

     ownerWorkspace Workspace? @relation(fields: [ownerWorkspaceId], references: [id], onDelete: SetNull)

     @@index([visibility])
     @@index([ownerWorkspaceId])
     @@index([category])
   }
   ```
3. Добавить inverse `presets StrategyPreset[]` в `Workspace` (рядом с другими relation-полями).
4. `npx prisma migrate dev --name add_strategy_preset` — миграция additive, без backfill.

**Тест-план:**
- `prisma migrate deploy` на pristine DB проходит.
- Существующие тесты Prisma (`apps/api/tests/`) зелёные.
- Создание preset через `prisma.strategyPreset.create` сериализует/десериализует DSL JSON без потерь.

**DoD:** миграция применилась локально и в CI; `tsc --noEmit` зелёный.

---

### 51-T2: API — CRUD + instantiate

**Цель:** новый роут `apps/api/src/routes/presets.ts` с пятью эндпоинтами.

**Файлы:** `apps/api/src/routes/presets.ts` (new), `apps/api/src/server.ts` (зарегистрировать), `apps/api/tests/routes/presets.test.ts` (new).

**Эндпоинты:**

| Method | Path | Auth | Описание |
|---|---|---|---|
| GET | `/lab/presets` | required | Список всех видимых пресетов: `PUBLIC` ∪ `WORKSPACE(myWorkspace)` ∪ `PRIVATE(authorMe)`. Query: `?category=&q=` |
| GET | `/lab/presets/:slug` | required | Один preset (с тем же visibility-фильтром) |
| POST | `/lab/presets` | required + admin-flag | Создать preset (для seed/admin) |
| PATCH | `/lab/presets/:slug` | required + admin-flag | Обновить (редкая операция) |
| POST | `/lab/presets/:slug/instantiate` | required | Создать `Strategy + StrategyVersion + Bot(DRAFT)` |

**Шаги:**
1. Подключить роуты в `server.ts` рядом с `botRoutes`/`labRoutes`.
2. Все list/get запросы фильтруют по visibility-правилу выше; `WORKSPACE`-пресеты невидимы для чужих workspace; `PRIVATE` — только для автора.
3. `POST /lab/presets` и `PATCH` — гейтить по env-флагу `ADMIN_API_KEY` (header `x-admin-key`) для v1, чтобы не плодить роли. Если флаг не выставлен — 403.
4. Body `instantiate` (все опциональны):
   ```ts
   { name?: string; symbol?: string; timeframe?: Timeframe; exchangeConnectionId?: string }
   ```
   Если `name` не передан — `${preset.name} (preset)` + unique-suffix `(2)`, `(3)` при коллизии в `(workspaceId, name)` (см. `Strategy.@@unique`, `schema.prisma:111`).
5. Транзакция `prisma.$transaction([...])`:
   - `Strategy.create({ workspaceId, name, symbol: body.symbol ?? preset.symbol, timeframe: body.timeframe ?? preset.timeframe, status: 'DRAFT' })`
   - `StrategyVersion.create({ strategyId, version: 1, dslJson: preset.dslJson, executionPlanJson: preset.executionPlanJson })`
   - `Bot.create({ workspaceId, name: <same>, strategyVersionId, symbol, timeframe, status: 'DRAFT', exchangeConnectionId })`
6. Ответ 201: `{ strategyId, strategyVersionId, botId }`.
7. Все ошибки — через `problem()` (как в `bots.ts`).

**Тест-план (e2e):**
- GET без auth → 401.
- GET с auth, нет PUBLIC и нет своих → пустой массив.
- GET после создания PUBLIC через admin → виден всем workspaces.
- GET с фильтром `?category=mean-reversion` → отфильтровано.
- POST `/instantiate` → создаются 3 записи (Strategy + StrategyVersion + Bot), botId возвращён, bot.status === 'DRAFT'.
- POST `/instantiate` дважды подряд → второй вызов получает name с suffix (2).
- POST `/instantiate` несуществующего slug → 404.
- POST `/instantiate` с `WORKSPACE`-пресетом из чужого workspace → 404 (не 403, чтобы не leak'ать существование).
- Транзакционность: симулировать падение на `Bot.create` (например, невалидный exchangeConnectionId) → ни Strategy, ни StrategyVersion не остались в БД.

**DoD:** все тесты зелёные; `tsc --noEmit` зелёный; `apps/api/src/server.ts` регистрирует роут.

---

### 51-T3: Seed — один публичный preset для smoke

**Цель:** проверить пайплайн end-to-end до полноценной активации пяти стратегий (`docs/53`/`docs/54`).

**Файлы:** `apps/api/prisma/seed/presets/bb-mean-reversion.json` (new), `apps/api/prisma/seed.ts` (расширить).

**Шаги:**
1. Создать минимальный валидный DSL Bollinger mean-reversion (entry: `compare(close, "<", bbands.lower)`, exit: `compare(close, ">", bbands.middle)`). DSL — JSON, формат как в существующих фикстурах backtest-тестов.
2. Compile через существующий compiler (`apps/api/src/lib/compiler/index.ts`) для генерации `executionPlanJson` — НЕ хардкодить.
3. В `seed.ts` upsert по `slug = 'bb-mean-reversion-public'` с `visibility: 'PUBLIC'`, `ownerWorkspaceId: null`.
4. Seed идемпотентен (upsert).

**Тест-план:**
- `prisma db seed` на чистой БД создаёт 1 preset.
- `prisma db seed` повторно — без дубликатов.
- `GET /lab/presets` любым auth-пользователем возвращает запись.
- `POST /lab/presets/bb-mean-reversion-public/instantiate` создаёт Bot.

**DoD:** seed запускается из коробки; smoke instantiate проходит.

---

### 51-T4: UI — Lab → Library → Presets

**Цель:** галерея + кнопка "Use this preset" в Lab.

**Файлы:** `apps/web/src/app/lab/library/page.tsx` (new), `apps/web/src/app/lab/library/PresetCard.tsx` (new), `apps/web/src/app/lab/LabShell.tsx` (добавить вкладку Library), `apps/web/src/app/lab/labApi.ts` (API-методы).

**Шаги:**
1. Добавить вкладку "Library" в `LabShell.tsx` рядом с Build/Test/Data.
2. `library/page.tsx`: `GET /lab/presets`, грид карточек. Каждая карточка: name, description, category, symbol, timeframe, кнопка "Use".
3. Click "Use" → `POST /lab/presets/:slug/instantiate` → редирект на `/factory/bots/${botId}` (как в `factory/page.tsx:188`).
4. Фильтр по category + поиск (контролируемый input, передаёт `q` в query).
5. Loading/error состояния как в существующих Lab-страницах.

**Тест-план (manual):**
- Library открывается, отображает seeded preset.
- Click "Use" → бот появляется в `/factory/bots`, Status=DRAFT, открыта детальная страница бота.
- Filter by category работает.
- Network error → toast/inline message.

**DoD:** `npm run typecheck` зелёный; manual smoke в браузере прошёл; нет регрессий в Build/Test/Data вкладках.

---

### 51-T5: Расширить capability matrix + release-checklist

**Файлы:** `docs/strategies/08-strategy-capability-matrix.md`, `docs/strategies/release-checklist.md` (new).

**Шаги:**
1. В `08-strategy-capability-matrix.md` добавить колонку `presetSlug`.
2. Создать `release-checklist.md` — таблица [strategy | golden-fixture | walk-forward gate | demo smoke | preset published]. Источник истины для `docs/50 §A5`.
3. Заполнить строку для `bb-mean-reversion-public` (golden-fixture в 51-T3, остальное TBD).

**DoD:** документы добавлены, ссылки из `docs/50` валидны.

---

## Порядок выполнения

```
51-T1 → 51-T2 → 51-T3 → 51-T4 → 51-T5
```

T1 и T2 строго последовательны (T2 нуждается в таблице). T3 нужен T2 (тестируется через `/instantiate`). T4 после T2/T3 (UI читает реальный API). T5 — последний, обновляет docs.

## Зависимости от других документов

- `docs/50` — формирующий документ.
- `docs/52` — независим в части schema, но instantiate должен корректно копировать `datasetBundleJson`, когда тот будет добавлен в preset (`docs/52-T1`). Это — follow-up к 51-T2 (одна доп. строка в transaction-block'е).
- `docs/53`, `docs/54` — потребители: они сидят presets и публикуют в галерею.

## Backward compatibility

- Все Prisma-изменения additive; существующие Strategy/StrategyVersion/Bot — без правок.
- `routes/demo.ts` hardcoded presets остаются (другая сущность).
- Старый `POST /bots` flow (Lab Build → Save → Factory create bot) работает без правок — instantiate это альтернативный путь.

## Ожидаемый результат

- Таблица `StrategyPreset` в продакшен-БД.
- `GET /lab/presets`, `POST /lab/presets/:slug/instantiate` работают; покрыты тестами.
- Один seeded публичный preset (`bb-mean-reversion-public`).
- Lab Library UI отображает галерею; click "Use" создаёт бот.
- Зафиксирован формат release-checklist для `docs/50 §A5`.
