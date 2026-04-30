# 51. Strategy Preset System

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Дорожка: A (research → trading workflow)

## Контекст

Текущее состояние (проверено по коду):

- Создание стратегии и бота сегодня делается через Lab → Build → Compile → Backtest → POST `/bots`. Эндпоинт `POST /bots` (`apps/api/src/routes/bots.ts:58`, тип `CreateBotBody:22`) принимает уже подготовленные `strategyId` + `strategyVersionId` и создаёт `Bot` со статусом `DRAFT`.
- Каталога «готовых стратегий» в продукте нет. Единственное приближение — `apps/api/src/routes/demo.ts` с двумя hardcoded breakout-presets для public landing page; это не reusable factory, а хак под лендинг.
- Prisma-модели `StrategyPreset`, `PresetVisibility` enum, `Bot.templateSlug` — отсутствуют (`apps/api/prisma/schema.prisma`).
- В Lab UI (`apps/web/src/app/lab/`) нет страницы Library / Gallery; есть только Build, Test, Optimise.
- 4 не-Funding флагмана описаны в `docs/strategies/02-…` … `docs/strategies/06-…`, capability matrix — `docs/strategies/08-strategy-capability-matrix.md`. Все блоки, нужные для их DSL, уже `supported` в `apps/api/src/lib/compiler/supportMap.ts` (33 блока — см. `docs/50 §Контекст`).
- Существующий `Strategy` имеет `templateSlug String?` — НЕТ, проверено: поле не объявлено. Связь preset→strategy будет добавляться в этом плане.

## Цель

- Ввести immutable JSON-шаблон `StrategyPreset` как «фабрику» `StrategyVersion`.
- Один эндпоинт `POST /presets/:slug/instantiate` за одну Prisma-транзакцию создаёт `Strategy` + `StrategyVersion` + `Bot` (status=`DRAFT`) и возвращает `botId`. Дальнейший lifecycle бота — стандартный, никакой preset-специфичной runtime-семантики.
- Каталог пресетов в Lab UI: страница `/lab/library`, карточки → один клик → бот.
- Видимость управляется enum'ом `PresetVisibility { PRIVATE, PUBLIC }`. До прохождения acceptance gate (`docs/50 §A5`) пресет хранится с `PRIVATE`. Переход в `PUBLIC` — отдельная админская операция, не часть DoD данного документа.
- Никаких изменений в существующем flow Lab → Build → Compile → Backtest → `POST /bots`. Это параллельный, additive путь.

## Не входит в задачу

- **AI-чат генерация preset'ов.** Существующий `apps/api/src/lib/ai/*` остаётся как есть; Lab Library — это куратор-курируемый каталог.
- **Версионирование preset'ов с историей.** Preset считается immutable: при необходимости менять — создаём новый slug (`adaptive-regime-v2`). Никаких миграций instantiate-версий вслед за изменениями исходного preset'а — Bot уже привязан к собственной `StrategyVersion`.
- **UI-редактор preset'ов.** Создание / правка пресетов на этом этапе делается миграцией / seed-скриптом (51-T6). Полноценный admin UI — отдельный документ.
- **Marketplace, рейтинги, комментарии.** Только каталог + instantiate. Социальный слой — out of scope.
- **Промо-флаги вроде `featured`, `recommended`.** Сортировка в gallery — детерминированная по slug или `updatedAt DESC`, без weighted ranking.
- **Cross-workspace sharing.** Пресет либо `PRIVATE` для конкретного workspace, либо `PUBLIC` (виден всем). Гранулярные ACL — out of scope.
- **Импорт / экспорт DSL JSON через UI.** Endpoint`POST /presets` принимает JSON, но UI-страницы для загрузки нет — admin использует API напрямую или seed.

## Архитектурные решения

### Решение 1: Preset — immutable factory, не runtime-сущность

`StrategyPreset` хранит:

- `slug String @id` — стабильный идентификатор (`adaptive-regime`, `dca-momentum`, `mtf-scalper`, `smc-liquidity-sweep`).
- `name String`, `description String`, `category String` (`trend` | `dca` | `scalping` | `smc` | `arb`).
- `dslJson Json` — DSL стратегии, тот же формат, что в `StrategyVersion.dslJson`.
- `defaultBotConfigJson Json` — дефолтные параметры для `Bot` (`symbol`, `timeframe`, `quoteAmount`, `maxOpenPositions`, …).
- `datasetBundleHintJson Json?` — рекомендованный multi-interval bundle (см. `docs/52`); опционально, single-TF пресеты не задают.
- `visibility PresetVisibility @default(PRIVATE)` (enum `PRIVATE | PUBLIC`).
- `createdAt`, `updatedAt`.

Никакой backref `Bot.presetId` — связь только через `Bot.templateSlug` (`String?`, без FK), чтобы preset мог быть удалён / переименован без каскада на ботов. См. 51-T4.

### Решение 2: Instantiate — одна транзакция, без частичных состояний

`POST /presets/:slug/instantiate` принимает `{ workspaceId, overrides?: Partial<BotConfig> }`. В рамках одной `prisma.$transaction([…])`:

1. `Strategy.create({ name: preset.name, workspaceId, templateSlug: preset.slug })` — каждый instantiate создаёт **новую** `Strategy`. Намеренно не переиспользуем существующую — чтобы один пользователь мог иметь несколько ботов от одного пресета с разной конфигурацией / параметрами без shared StrategyVersion.
2. `StrategyVersion.create({ strategyId, dslJson: preset.dslJson, version: 1, status: "compiled" })` — компиляция DSL уже в момент create; если падает — вся транзакция откатывается.
3. `Bot.create({ strategyId, strategyVersionId, status: "DRAFT", templateSlug: preset.slug, ...mergedConfig })`.

Возвращается `{ botId, strategyId, strategyVersionId }`. Дальнейшие действия — стандартные: `PATCH /bots/:id`, `POST /bots/:id/start`.

### Решение 3: Visibility-gate — preset публикуется только после acceptance

Acceptance из `docs/50 §A5` (golden DSL fixture + walk-forward + 30-мин demo smoke) — обязательное условие для перевода `visibility` в `PUBLIC`. До тех пор пресет существует в БД с `PRIVATE` и виден только в админ-панели (51-T5). Это даёт возможность раскатывать пресеты по одному (`docs/53` → `docs/54`) без изменения каталога для конечных пользователей.

### Решение 4: Composite signal types — переписываются через примитивы

См. `docs/50 §Решение 3`. Никаких новых типов сигналов в evaluator не вводится: каждый `dslJson` пресета составляется из 33 уже supported блоков (`apps/api/src/lib/compiler/supportMap.ts`). Если конкретный флагман потребует семантики, не выражаемой через существующие блоки — это блокер, фиксируется как отдельная T-задача в `docs/53`/`docs/54`, не как escape-hatch внутри preset'а.

---

## Задачи

### 51-T1: Prisma модель `StrategyPreset` + миграция

**Цель:** ввести Prisma-модель `StrategyPreset` и enum `PresetVisibility`. Чисто схема + миграция, без endpoint'ов.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — добавить модель и enum.
- `apps/api/prisma/migrations/<timestamp>_strategy_preset/migration.sql` — additive миграция.
- `apps/api/tests/prisma/strategyPreset.test.ts` (создать) — sanity-чек create/findUnique.

**Шаги реализации:**
1. В `schema.prisma` рядом с `Strategy` (примерно строка 230, источник истинности — текущий файл) добавить:
   ```prisma
   enum PresetVisibility {
     PRIVATE
     PUBLIC
   }

   model StrategyPreset {
     slug                  String           @id
     name                  String
     description           String
     category              String
     dslJson               Json
     defaultBotConfigJson  Json
     datasetBundleHintJson Json?
     visibility            PresetVisibility @default(PRIVATE)
     createdAt             DateTime         @default(now())
     updatedAt             DateTime         @updatedAt

     @@index([visibility])
     @@index([category])
   }
   ```
2. `npx prisma migrate dev --name strategy_preset` — генерация миграции локально, ручная проверка SQL (additive `CREATE TABLE` + `CREATE TYPE`, не должно быть `ALTER` существующих таблиц).
3. Никаких backfill'ов — таблица создаётся пустой.
4. `npx prisma generate` обновляет client; убедиться, что новый тип доступен в `apps/api/src/lib/prisma.ts` потребителях.

**Тест-план:**
- `prisma.strategyPreset.create({ data: { slug: "test", name: "T", description: "x", category: "trend", dslJson: {}, defaultBotConfigJson: {}, visibility: "PRIVATE" } })` → успех.
- `findUnique({ where: { slug: "test" } })` → возвращает запись.
- Дублирующий create по тому же slug → ошибка уникальности.
- `visibility` без value → дефолт `PRIVATE`.

**Критерии готовности:**
- `npx prisma migrate dev` проходит без ошибок.
- `npx prisma generate` — client типизирован.
- `tsc --noEmit` зелёный.
- Существующие тесты Prisma (если есть) зелёные.
- В schema.prisma нет изменений других моделей.

---

### 51-T2: CRUD-эндпоинты пресетов

**Цель:** ввести `POST /presets`, `GET /presets`, `GET /presets/:slug`. UPDATE / DELETE на этом этапе не реализуются — пресеты иммутабельны, новый slug = новая запись.

**Файлы для изменения:**
- `apps/api/src/routes/presets.ts` (создать) — Fastify router, регистрация в `apps/api/src/server.ts`.
- `apps/api/tests/routes/presets.test.ts` (создать).

**Шаги реализации:**
1. `POST /presets` (admin-only — гард по существующему `requireAdmin` middleware, тот же что у `/admin/*`). Body:
   ```ts
   type CreatePresetBody = {
     slug: string;            // /^[a-z0-9-]{3,64}$/
     name: string;            // 1..120
     description: string;     // 1..500
     category: "trend" | "dca" | "scalping" | "smc" | "arb";
     dslJson: unknown;        // валидируется compileDsl ниже
     defaultBotConfigJson: {
       symbol: string;
       timeframe: "M1" | "M5" | "M15" | "H1";
       quoteAmount: number;
       maxOpenPositions: number;
       [k: string]: unknown;
     };
     datasetBundleHintJson?: Record<string, string | true> | null;
     visibility?: "PRIVATE" | "PUBLIC"; // default PRIVATE
   };
   ```
   До записи — прогнать `dslJson` через существующий `compileDsl` (`apps/api/src/lib/compiler/compile.ts`). Если компиляция падает — 400 с массивом ошибок. Это гарант, что preset технически валиден на момент создания.
2. `GET /presets` — query: `?category=...&visibility=...`. Без авторизации возвращает только `visibility=PUBLIC`. С админ-токеном возвращает всё. Ответ — массив без `dslJson` (для каталога достаточно метаданных + `defaultBotConfigJson`); `dslJson` отдаётся только в `GET /presets/:slug`.
3. `GET /presets/:slug` — полный объект с `dslJson`. Без авторизации недоступен для `PRIVATE` (404, не 403, чтобы не раскрывать существование).
4. Регистрация роута в `server.ts` рядом с другими `/lab`/`/bots` роутерами; rate limit — стандартный (тот же, что у `/bots`).
5. **Никаких** `PATCH` / `DELETE` пока: если потребуется поправить пресет — создаётся новый slug, старый помечается `visibility=PRIVATE` через прямой SQL / отдельный admin-tool. Это сознательное ограничение для иммутабельности; снимается в follow-up документе.

**Тест-план:**
- POST невалидного `slug` (uppercase / spaces) → 400.
- POST с DSL, который не компилируется → 400, тело содержит компиляторные ошибки.
- POST успешный → 201, `findUnique` возвращает запись.
- POST дубль slug → 409.
- GET list без auth: только `PUBLIC`.
- GET list с admin: все.
- GET `:slug` для `PRIVATE` без auth → 404.
- GET `:slug` для `PUBLIC` без auth → 200 с `dslJson`.

**Критерии готовности:**
- Роут зарегистрирован, ручной curl проходит.
- Все тесты зелёные.
- В OpenAPI (если генерируется) появляются три новых эндпоинта.
- `compileDsl` вызывается на POST — невалидные DSL не записываются.

---

### 51-T3: Instantiate-эндпоинт (транзакция Strategy + StrategyVersion + Bot)

**Цель:** `POST /presets/:slug/instantiate` создаёт три сущности в одной транзакции и возвращает `{ botId, strategyId, strategyVersionId }`.

**Файлы для изменения:**
- `apps/api/src/routes/presets.ts` — добавить хендлер.
- `apps/api/tests/routes/presets.test.ts` — расширить.

**Шаги реализации:**
1. Body:
   ```ts
   type InstantiateBody = {
     workspaceId: string;
     overrides?: Partial<{
       symbol: string;
       timeframe: "M1" | "M5" | "M15" | "H1";
       quoteAmount: number;
       maxOpenPositions: number;
       name: string; // user-facing имя бота
     }>;
   };
   ```
2. Хендлер:
   - Загрузить пресет (`findUnique({ where: { slug } })`); если `visibility=PRIVATE` и нет admin-токена — 404 (та же политика, что в T2).
   - Слить `defaultBotConfigJson` с `overrides` (overrides приоритетнее). Валидировать `timeframe` против `VALID_TIMEFRAMES = ["M1","M5","M15","H1"]` из `apps/api/src/routes/bots.ts:22` (импорт не делать, чтобы избежать circular; продублировать литерал и добавить TODO-comment про централизацию в follow-up).
   - В `prisma.$transaction`:
     - `Strategy.create({ name: overrides?.name ?? preset.name, workspaceId, templateSlug: preset.slug })`.
     - `StrategyVersion.create({ strategyId, dslJson: preset.dslJson, version: 1, status: "compiled" })`. Если в текущем коде `StrategyVersion.status` имеет другие значения — использовать существующий `compiled`/`ready`-эквивалент, проверить `schema.prisma`.
     - `Bot.create({ strategyId, strategyVersionId, status: "DRAFT", templateSlug: preset.slug, ...mergedConfig })`.
   - Транзакция целиком откатывается, если любой шаг падает (включая ошибку Prisma на FK / unique).
3. Ответ: `{ botId, strategyId, strategyVersionId }`, status 201.
4. Никаких side effects вне транзакции (никаких email / webhook / queue.publish). Создание бота — чистая операция БД.
5. Авторизация: эндпоинт требует обычного user-токена (не admin). `workspaceId` валидируется на принадлежность пользователю — переиспользовать существующий guard из `routes/bots.ts` (см. `assertWorkspaceMembership` или эквивалент в текущем коде).
6. Идемпотентности **нет**: повторный POST создаст вторую `Strategy`/`Bot`. Это явное решение — каждый instantiate = новый экземпляр. Дедуп ответственность клиента (например, double-click на карточке gallery → debounce на UI).

**Тест-план:**
- POST с невалидным `slug` → 404.
- POST на `PRIVATE` без admin → 404.
- POST успех: проверить, что в БД появились ровно одна `Strategy`, одна `StrategyVersion`, один `Bot`, все с `templateSlug = preset.slug`.
- POST с `overrides.symbol` — `Bot.symbol` равен override'у, не дефолту.
- POST с `overrides.timeframe="M30"` → 400 (не в `VALID_TIMEFRAMES`).
- Симуляция падения `Bot.create` (например, через мок) → ни `Strategy`, ни `StrategyVersion` в БД не остаются (rollback).
- 2 последовательных POST → создаются 2 независимых бота.

**Критерии готовности:**
- Транзакционная атомарность подтверждена тестом.
- `Bot.status === "DRAFT"` в результате — старт отдельным вызовом `POST /bots/:id/start`.
- Существующие тесты `/bots` зелёные без правок.
- Ручной smoke: instantiate seed-пресета (после 51-T6) → `POST /bots/:id/start` → бот появляется в polling-loop.

---

### 51-T4: `Bot.templateSlug` для трекинга происхождения

**Цель:** ввести nullable `templateSlug String?` в `Bot` и `Strategy` для трекинга, из какого пресета произведён экземпляр. Без FK на `StrategyPreset` — связь по строке.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — `Bot`, `Strategy`.
- `apps/api/prisma/migrations/<timestamp>_template_slug/migration.sql` — additive.
- `apps/api/src/routes/bots.ts` — расширить `CreateBotBody:22` опциональным `templateSlug`.
- `apps/api/src/routes/presets.ts` — instantiate (51-T3) уже пишет `templateSlug`.
- `apps/api/tests/routes/bots.test.ts` — добавить кейс с `templateSlug`.

**Шаги реализации:**
1. В `Bot` модель добавить:
   ```prisma
   templateSlug String?
   @@index([templateSlug])
   ```
   Аналогично — в `Strategy`. Без relation block, чтобы preset мог быть удалён без каскада.
2. Миграция: `ALTER TABLE "Bot" ADD COLUMN "templateSlug" TEXT; CREATE INDEX "Bot_templateSlug_idx" ON "Bot"("templateSlug");` — идентично для `Strategy`. Existing rows получают `NULL`.
3. `CreateBotBody` (`bots.ts:22`): добавить optional `templateSlug?: string` (regex `/^[a-z0-9-]{3,64}$/`). Если присутствует — кладётся в `Bot.create({ ... templateSlug })`. Не валидировать существование preset'а с таким slug — это просто метка, не FK.
4. В UI Bot page (отдельно — в 51-T5) добавить badge "From preset: `<slug>`" если `templateSlug != null`. На этом этапе — только бэкенд.
5. **Обратное чтение**: `GET /presets/:slug/usage` — НЕ реализуется в этом этапе (нет требований). Потенциальный count `prisma.bot.count({ where: { templateSlug } })` — оставить на follow-up.

**Тест-план:**
- `POST /bots` с `templateSlug` → создан бот, поле сохранено.
- `POST /bots` без `templateSlug` → создан бот с `templateSlug = null` (backward-compat).
- `POST /presets/:slug/instantiate` → `Bot.templateSlug === preset.slug` и `Strategy.templateSlug === preset.slug` (повторная проверка из 51-T3 на уровне БД).
- Удаление preset'а (через прямой SQL) → существующий бот живёт, его `templateSlug` остаётся валидной строкой, но при попытке загрузить preset через `GET /presets/:slug` будет 404. Это ожидаемое поведение; UI должен корректно скрывать badge.

**Критерии готовности:**
- Миграция additive, существующие row'ы целы.
- `tsc --noEmit` зелёный.
- `POST /bots` без `templateSlug` работает идентично текущему поведению (нет регрессий в `bots.test.ts`).

---

### 51-T5: UI Lab Library (gallery)

**Цель:** страница `/lab/library` со списком карточек `PUBLIC` пресетов; клик «Use preset» → diaglog с конфигурацией → POST `/presets/:slug/instantiate` → редирект на страницу созданного бота.

**Файлы для изменения:**
- `apps/web/src/app/lab/library/page.tsx` (создать).
- `apps/web/src/app/lab/library/PresetCard.tsx` (создать).
- `apps/web/src/app/lab/library/InstantiateDialog.tsx` (создать).
- `apps/web/src/app/lab/layout.tsx` — добавить пункт "Library" в навигацию рядом с Build/Test/Optimise.
- `apps/web/src/lib/api/presets.ts` (создать) — типизированные клиенты `listPresets`, `getPreset`, `instantiatePreset`.

**Шаги реализации:**
1. `/lab/library` — серверный component, грузит `GET /presets?visibility=PUBLIC` и рендерит сетку карточек. Каждая карточка: name, описание (truncate 200 chars), category badge, кнопка "Use preset".
2. Если list пустой (например, до 51-T6 / до публикации первого пресета) — показывается empty-state с подсказкой "No public presets yet. Build your own via Lab → Build."
3. `InstantiateDialog`: форма с полями из `defaultBotConfigJson` (symbol / timeframe / quoteAmount / maxOpenPositions). Дефолты предзаполнены, пользователь может изменить → отправляет в `overrides`. Кнопка "Create bot" → `POST /presets/:slug/instantiate` → router.push(`/bots/${botId}`).
4. Если preset имеет `datasetBundleHintJson != null` — показать info-бокс "This preset uses multi-interval data. Configure dataset bundle on the bot page after creation." Линк на гайд (плейсхолдер `docs/52`).
5. Admin-режим: если у пользователя admin-токен, гruzить `GET /presets` без фильтра — карточки `PRIVATE` отображаются с серым бейджем "Private", "Use preset" работает идентично.
6. Никаких новых глобальных стейт-сторов; локальный `useState` в страницах достаточно. Используем существующий `apiClient` обвязку из `apps/web/src/lib/api/`.
7. На странице бота (`/bots/[id]`, существующая) добавить условный badge "From preset: `<slug>`" если `bot.templateSlug != null` — отдельный мини-PR в рамках T5.

**Тест-план:**
- Ручной smoke в браузере:
  - Открыть `/lab/library` без пресетов в БД → empty-state.
  - Создать через API один `PUBLIC` preset → перезагрузить страницу → карточка появилась.
  - Кнопка "Use preset" → диалог открывается с дефолтами.
  - Submit с overrides → `POST /presets/:slug/instantiate` → редирект на `/bots/<id>`, на странице видна badge "From preset".
  - Submit от админа на `PRIVATE` preset → бот создаётся.
- Регрессия: `/lab/build`, `/lab/test`, `/lab/optimise` продолжают работать без изменений.

**Критерии готовности:**
- TypeScript-проверка фронта зелёная.
- E2E тест (если есть playwright-suite) проходит для goldenpath; иначе — ручной smoke задокументирован в PR.
- Нет регрессий навигации Lab.

---

### 51-T6: Seed-пресеты для 4 флагманов в статусе PRIVATE

**Цель:** добавить seed-скрипт, создающий 4 не-Funding пресета в `PRIVATE`. Это даёт реальные DSL-fixtures, на которых будут работать `docs/53` (Adaptive Regime) и `docs/54` (DCA / MTF Scalper / SMC). Funding Arb идёт отдельно в `docs/55-T6`.

**Файлы для изменения:**
- `apps/api/prisma/seed/presets/adaptive-regime.json` (создать) — DSL.
- `apps/api/prisma/seed/presets/dca-momentum.json` (создать).
- `apps/api/prisma/seed/presets/mtf-scalper.json` (создать).
- `apps/api/prisma/seed/presets/smc-liquidity-sweep.json` (создать).
- `apps/api/prisma/seed/seedPresets.ts` (создать) — upsert по slug.
- `apps/api/prisma/seed/index.ts` — вызвать `seedPresets()` если ещё не вызван.
- `apps/api/tests/prisma/seedPresets.test.ts` (создать).

**Шаги реализации:**
1. JSON-файлы с DSL — заглушки с минимальной валидной DSL-структурой (один блок `enter_when` через `compare`/`crosses`, один `exit_when`, корректный `defaultBotConfigJson`). Полные DSL для каждой стратегии оформляются в соответствующих документах (`docs/53` для Adaptive Regime — golden fixture; `docs/54` для остальных). На этапе T6 достаточно того, чтобы каждый JSON прогонялся через `compileDsl` без ошибок.
2. `seedPresets.ts`:
   ```ts
   const presets = [
     { slug: "adaptive-regime", file: "./presets/adaptive-regime.json", category: "trend" },
     { slug: "dca-momentum",    file: "./presets/dca-momentum.json",    category: "dca" },
     { slug: "mtf-scalper",     file: "./presets/mtf-scalper.json",     category: "scalping" },
     { slug: "smc-liquidity-sweep", file: "./presets/smc-liquidity-sweep.json", category: "smc" },
   ];

   for (const p of presets) {
     const data = JSON.parse(await fs.readFile(...));
     await prisma.strategyPreset.upsert({
       where: { slug: p.slug },
       create: { slug: p.slug, ...data, category: p.category, visibility: "PRIVATE" },
       update: { ...data, category: p.category }, // visibility НЕ обновляется через seed
     });
   }
   ```
3. `update`-ветка намеренно не трогает `visibility` — как только preset переведён в `PUBLIC` админом, повторный seed не откатит это.
4. `seedPresets()` вызывается из `prisma/seed/index.ts` (стандартный hook `prisma db seed`).
5. Каждый JSON-файл прогоняется через `compileDsl` в `seedPresets.test.ts`. Если хоть один не валиден — тест красный, seed не публикуется.

**Тест-план:**
- Запуск `npx prisma db seed` дважды подряд → идемпотентность (no-op на втором запуске за исключением `updatedAt`).
- В тесте: `compileDsl(preset.dslJson)` для каждого slug — без ошибок.
- В тесте: каждый preset имеет `visibility="PRIVATE"`.
- В тесте: после ручного перевода preset'а в `PUBLIC` через прямой SQL и повторного seed — `visibility` остаётся `PUBLIC`.

**Критерии готовности:**
- Все 4 seed-пресета компилируются.
- Идемпотентность подтверждена тестом.
- В CI seed запускается на тестовой БД и не падает.
- DSL-fixtures помечены как «черновики, финальный вид — в `docs/53/54`».

---

### 51-T7: Тесты — CRUD + instantiate + UI smoke

**Цель:** довести покрытие preset-системы до уровня, при котором регрессии ловятся на CI. Объединяет тесты, описанные в T1..T6, и добавляет интеграционный e2e.

**Файлы для изменения:**
- `apps/api/tests/routes/presets.test.ts` — расширить.
- `apps/api/tests/integration/presetInstantiateFlow.test.ts` (создать) — e2e.
- `apps/web/tests/lab/library.spec.ts` (если есть playwright) — UI smoke.

**Шаги реализации:**
1. Объединить unit-тесты из T1 (Prisma model), T2 (CRUD), T3 (instantiate transaction), T4 (templateSlug), T6 (seed compileDsl) — убедиться, что они существуют как отдельные spec-файлы, без дублей.
2. **Интеграционный e2e** в `presetInstantiateFlow.test.ts`:
   - `prisma db seed` → 4 preset'а в БД (`PRIVATE`).
   - Через прямой SQL установить `visibility="PUBLIC"` для `adaptive-regime`.
   - `GET /presets` без auth → возвращает только `adaptive-regime`.
   - `POST /presets/adaptive-regime/instantiate` с фейковым workspace → 201, `botId` в ответе.
   - `GET /bots/:id` → `Bot.status === "DRAFT"`, `templateSlug === "adaptive-regime"`, есть `strategyVersionId`, в `StrategyVersion.dslJson` лежит DSL пресета (deep equal).
   - `POST /bots/:id/start` → стандартный flow срабатывает (это тест на отсутствие preset-специфичной runtime-семантики; `botWorker.ts` не должен видеть никакой разницы между preset'овым и обычным ботом).
3. UI-smoke (если playwright настроен): открыть `/lab/library`, кликнуть "Use preset" на `adaptive-regime`, заполнить форму, submit → ожидать редирект на `/bots/<id>` и наличие badge "From preset".
4. Все новые тесты — детерминированы (фикстуры зашиты, рандом / `Date.now()` не используется в DSL-валидации). Полей с current time в моделях `StrategyPreset` нет проблематичных, но в ассертах сверяем `slug`/`name`/`dslJson`, а не `createdAt`.

**Тест-план:**
- `npm test` (`apps/api`) проходит локально и в CI.
- Существующие тесты `/bots`, `/lab/*` остаются зелёными.
- Покрытие новых файлов (`routes/presets.ts`, `seed/seedPresets.ts`) ≥ 80% по строкам (ориентир, не блокер).

**Критерии готовности:**
- Все новые тесты зелёные.
- E2E `presetInstantiateFlow.test.ts` проходит на чистой тестовой БД.
- В PR-описании отмечено, что preset-flow не трогает `botWorker.ts` / runtime — это инвариант проекта (`docs/50 §Решение 1`).

---

## Порядок выполнения задач

```
51-T1 ──→ 51-T2 ──→ 51-T3 ──→ 51-T6 ──→ 51-T5
              ↘                  ↗
               51-T4 ────────────
                                 ↘
                                  51-T7
```

- 51-T1 (Prisma модель) — первая, без неё ничего не работает.
- 51-T2 (CRUD) и 51-T4 (`Bot.templateSlug`) можно делать параллельно после T1.
- 51-T3 (instantiate) требует T1, T2 и T4 (использует `Bot.templateSlug`).
- 51-T6 (seed) требует T1 + T2 (DSL валидируется через `compileDsl` тем же путём, что в `POST /presets`). Может идти параллельно с T3 после того, как T2 закрыта.
- 51-T5 (UI) — самая последняя из «функциональных», требует T2 (list/get) и T3 (instantiate).
- 51-T7 (тесты) — встраивается инкрементально в каждую из T1..T6, плюс отдельный финальный e2e-spec.

Каждая задача — отдельный PR. T7 e2e-spec может ехать вместе с T6 или отдельным PR'ом.

## Зависимости от других документов

- `docs/50` — родительский overview. Никакая T-задача из 51 не противоречит решениям, зафиксированным там.
- `docs/52-multi-interval-dataset-bundle.md` — независим. `datasetBundleHintJson` в `StrategyPreset` — необязательное поле; пресеты, которые не используют multi-interval, не зависят от 52.
- `docs/53-adaptive-regime-bot-activation.md` — потребитель 51. Использует `POST /presets/:slug/instantiate` для one-click активации; финальный DSL для `adaptive-regime` пресета фиксируется в 53-T1 (golden fixture).
- `docs/54-flagship-rollout.md` — потребитель 51. Аналогично 53, но для DCA / MTF Scalper / SMC.
- `docs/47` / `docs/48` / `docs/49` — закрыты. Используются как инструменты валидации внутри acceptance gate (`docs/50 §A5`), не блокируют документ 51.
- `docs/strategies/01-08` — концептуальные. Источник истинности по DSL-составу каждого флагмана.

## Backward compatibility checklist

- Никаких изменений в существующем `POST /bots` flow: `templateSlug` опционален, default `null`, поведение для клиентов без знаний о preset'ах идентично текущему.
- `botWorker.ts`, `signalEngine.ts`, `exitEngine.ts`, `positionManager.ts` — не модифицируются. Preset-flow «выходит» из себя сразу после instantiate; runtime видит обычного `Bot` с обычной `StrategyVersion`.
- Prisma миграции — только additive: новая таблица `StrategyPreset`, новый enum `PresetVisibility`, две новые nullable колонки `Bot.templateSlug`, `Strategy.templateSlug`.
- Существующие `Strategy`, `StrategyVersion`, `Bot`-записи продолжают работать; `templateSlug=NULL` для всех.
- `routes/demo.ts` (hardcoded breakout-presets для лендинга) остаётся как есть и не мигрирует на `StrategyPreset` в рамках этого документа — у него другая семантика (public lead-gen, без БД).
- AI-чат / Lab Build / Lab Test / Lab Optimise — не затрагиваются.
- Никаких изменений в `BotIntent`, `BotRunState`, `IntentType` enum'ах.
- Removal preset'а через прямой SQL — не каскадирует на ботов: связь `Bot.templateSlug` без FK (см. 51-T4), badge "From preset" просто перестаёт показываться.

## Ожидаемый результат

После закрытия всех задач 51-T1..51-T7:

- В Lab UI существует страница `/lab/library` со списком публичных пресетов; одна кнопка превращает карточку в живого бота (DRAFT) за <60 секунд.
- БД хранит 4 не-Funding пресета как `PRIVATE` (заполнены seed'ом из 51-T6), готовых к публикации после прохождения acceptance gate в `docs/53` / `docs/54`.
- API эндпоинты `GET /presets`, `GET /presets/:slug`, `POST /presets/:slug/instantiate` стабильны и покрыты тестами.
- Существующий flow Lab → Build → Compile → Backtest → `POST /bots` работает без регрессий — preset является **дополнительным** входом в систему, а не заменой.
- Каждый созданный из пресета бот несёт `templateSlug` для аналитики и будущего displayed-attribution.
- DSL-evaluator, signal/exit/position engine, botWorker — не модифицированы; preset-флоу полностью локализован в `routes/presets.ts` + Prisma миграциях.
