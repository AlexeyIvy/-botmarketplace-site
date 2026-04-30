# 55. Funding Arbitrage — Plan

Статус: draft  
Владелец: core trading  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Связанный спек: `docs/strategies/04-funding-arbitrage-delta-hedge.md`

## Контекст

Текущее состояние (проверено по коду):

- Concept-документ: `docs/strategies/04-funding-arbitrage-delta-hedge.md`. Идея: при положительном funding rate на perpetual — short perp + long spot того же символа, удержать через funding payment, выйти. Дельта-нейтральная позиция, прибыль = funding − fees − spread cost.
- Funding lib **уже есть**: `apps/api/src/lib/funding/` содержит `basis.ts`, `fetcher.ts`, `hedgePlanner.ts`, `hedgeTypes.ts`, `index.ts`, `ingestJob.ts`, `ingestion.ts`, `scanner.ts`, `types.ts`.
- Prisma модели готовы: `FundingSnapshot` (`schema.prisma:764`), `SpreadSnapshot` (`schema.prisma:774`), `HedgePosition` (`schema.prisma:794`), `LegExecution` (`schema.prisma:810`).
- Роут `/hedges` живой: `apps/api/src/routes/hedges.ts`. Эндпоинты:
  - `POST /hedges/entry` — создать `HedgePosition` со spot- и perp-leg как `BotIntent` записями.
  - `POST /hedges/:id/execute` — пометить как executed.
  - `POST /hedges/:id/exit` — exit процедура.
  - `GET /hedges`, `GET /hedges/:id` — read.
- Spot-нога создаётся как `BotIntent` с `metaJson.category = "spot"` (`hedges.ts:152`, `hedges.ts:227`). **Реального spot-исполнения через Bybit API нет** — intent создаётся, но никакой POST к `/v5/order/create` с `category=spot` сегодня не происходит.
- `bybitOrder.ts` параметризован: `category: "linear" | "spot"` (`apps/api/src/lib/bybitOrder.ts:89`, `:174`). Уровень API готов.
- `apps/api/src/lib/exchange/` содержит **только** `instrumentCache.ts` и `normalizer.ts`. Spot-specific market-data adapter (`bybitSpot.ts`: ticker, candles, instrument cache) — **отсутствует**.
- `ExchangeConnection` Prisma model — single API key (linear). Spot обычно требует отдельные права; в текущей схеме нет места для spot-credentials, либо отсутствует phys-проверка scope'ов.
- Funding events на Bybit perpetual — раз в 8 часов (00:00, 08:00, 16:00 UTC). Демо-smoke на 30 минут не зацепит ни одного — поэтому acceptance gate расширяется до 60+ минут с явной привязкой к funding window.

## Цель

Довести funding-arb до состояния production-ready BETA-пресета в Lab Library:

1. Spot-нога реально исполняется в Bybit (не остаётся «бумажным» BotIntent).
2. Funding scanner доступен через UI; пользователь видит таблицу кандидатов (symbol × current funding rate × spread).
3. Dedicated runtime — `hedgeBotWorker` — обрабатывает funding-arb mode, не ломая основной `botWorker.ts`.
4. Acceptance gate проходит: 60+ минут на Bybit demo с реально зацепленным funding event, обе ноги исполнились, hedge закрылся, P&L соответствует expected funding − costs.
5. Preset `funding-arb` опубликован в Lab Library со специальной visibility=`BETA` (или эквивалентом, см. §Решение 4) — отличающейся от обычной `PUBLIC`, чтобы UI явно сигнализировал «это experimental, multi-leg, может стоить денег при ошибке».

После закрытия 55 в Lab Library — 5 карточек, последняя помечена как BETA. Live-включение funding-arb — отдельное решение, с дополнительным sub-gate'ом в `docs/54 §54-T6` (поскольку multi-leg execution имеет свой класс рисков, отличный от single-leg флагманов).

## Не входит в задачу

- **Live trading.** Только demo. Live-включение funding-arb — после go/no-go gate с дополнительными критериями (spot/perp inventory accounting, manual approval для каждого entry в первое время, position size cap).
- **Negative funding (long perp + short spot).** Spot-shorting на Bybit или сложный, или недоступен на demo. Покрываем только positive-funding direction (short perp + long spot).
- **Множественные одновременные hedge positions.** Один бот = один активный hedge за раз. Концепт «portfolio of hedges» — out of scope.
- **Cross-exchange funding arb.** Только Bybit (perp + spot одной биржи). Multi-exchange — отдельный документ.
- **Auto-recovery после частичного fill.** Если spot fill 0.5 BTC из 1.0 запрошенных — hedge ставится на pause и эскалируется как ERRORED. Авто-добивание / re-quote — out of scope первой версии.
- **Базис-arb (spot ↔ perp price diff trading).** Только funding rate, не basis spread.
- **Перепроектирование `bybitOrder.ts`.** Уже параметризован — используем как есть.
- **Отдельный AI-чат для funding-arb.** DSL для funding-arb minimal (mode flag + symbol + size); не требует AI-генерации.

## Архитектурные решения

### Решение A1: Bybit Spot adapter — отдельный модуль

`apps/api/src/lib/exchange/bybitSpot.ts` (создаётся в 55-T1). Содержит:
- `fetchSpotCandles(symbol, interval, limit)` — для UI / диагностики, не критично для funding-arb runtime.
- `fetchSpotTicker(symbol)` — последняя цена + bid/ask, для расчёта spread cost.
- `getSpotInstrumentInfo(symbol)` — tick size, lot size, min order size — параметры, нужные для round'ера sizing.
- Trading сам по себе — через существующий `bybitOrder.ts` с `category: "spot"`. Этот модуль market-data only.
- Использует существующий нормализатор `apps/api/src/lib/exchange/normalizer.ts` для преобразования сырого Bybit response → внутренний формат.

### Решение A2: Multi-leg execution = HedgePosition с двумя BotIntent'ами

Существующая модель `HedgePosition` + два `BotIntent`'а (один с `metaJson.category="linear"`, второй с `category="spot"`) — оставляется как есть. 55-T2 завершает execution: spot-leg `BotIntent` действительно отправляется в Bybit через `bybitOrder` с `category: "spot"`. После исполнения обоих legs `HedgePosition.status` переходит в `EXECUTED`; если только один — `PARTIAL_ERROR` и алёрт.

### Решение A3: Acceptance gate — 60+ минут, привязка к funding event

В отличие от 30-минутного demo smoke для остальных флагманов (`docs/53-T3`), funding-arb acceptance включает:
- Запуск runs strictly в окне (T_funding − 30 min, T_funding + 30 min) — то есть прямо вокруг funding event timestamp.
- Проверка: entry-сигнал сработал до funding (perp short + spot long executed), funding payment получен (видно по Bybit API `/v5/account/transaction-log`), exit отработал после funding (close perp short + sell spot), P&L close to `funding_payment − fees − slippage`.
- Если acceptance не проходит за один run — повтор на следующем funding window. Документировано в companion-doc.

### Решение A4: Visibility = BETA

`StrategyPreset` enum `PresetVisibility` сейчас имеет `PRIVATE | PUBLIC` (`docs/51-T1`). Для funding-arb нужна третья степень — `BETA`. Два варианта:
1. Расширить enum до `PRIVATE | BETA | PUBLIC`. Минус: каждое место, где код фильтрует `visibility=PUBLIC`, нужно решить — включает ли он `BETA`.
2. Добавить отдельную nullable колонку `isBeta Boolean @default(false)` рядом с `visibility`. Plus: orthogonal axis. Minus: ещё одна миграция, ещё одна ось.

**Выбираем (1) — extend enum.** Конкретно — `PRIVATE | BETA | PUBLIC`. UI Lab Library показывает `PUBLIC` без бейджа; `BETA` — с явным жёлтым бейджем "BETA — multi-leg execution, monitor closely"; `PRIVATE` — только в admin view. Все эндпоинты `GET /presets` и `getPreset` явно опрашивают `visibility IN ('PUBLIC', 'BETA')` для аутентифицированных user'ов; неаутентифицированный landing — только `PUBLIC`. Миграция enum — additive (PostgreSQL: `ALTER TYPE ... ADD VALUE 'BETA' BEFORE 'PUBLIC'`).

### Решение A5: Funding-arb runtime ≠ обычный botWorker

Funding-arb — не «evaluator + intent» полный обычный bot. Его cycle:
1. Сканирование funding rates (по cron / на старте бота).
2. Если есть кандидат с rate > threshold — POST `/hedges/entry` с конкретным symbol+size.
3. POST `/hedges/:id/execute`.
4. Wait until next funding tick (sleep до T_funding + buffer).
5. Verify funding payment received → POST `/hedges/:id/exit`.
6. Repeat.

Этот цикл не помещается в существующий polling-loop `botWorker.ts` (который заточен на DSL-evaluator). Поэтому вводим **dedicated runtime** — `apps/api/src/runtime/hedgeBotWorker.ts` (отдельная entrypoint). `Bot.mode` enum (новое поле) различает: `DSL` (default) → обычный botWorker; `FUNDING_ARB` → hedgeBotWorker. Это **аддитивно**: existing боты получают `mode=DSL` и работают через старый путь.

Альтернатива — встраивать всё в `botWorker.ts` через if/else — отвергается: смешение state machines усложняет maintenance и ломает изоляцию.

---

## Задачи

### 55-T1: Bybit Spot adapter — market data + ticker

**Цель:** ввести `apps/api/src/lib/exchange/bybitSpot.ts` с тремя market-data функциями. Trading через `bybitOrder` (уже параметризован).

**Файлы для изменения:**
- `apps/api/src/lib/exchange/bybitSpot.ts` (создать).
- `apps/api/src/lib/exchange/normalizer.ts` — переиспользовать или мягко расширить (если spot формат отличается чем-то от linear — добавить overload, не менять existing).
- `apps/api/tests/lib/exchange/bybitSpot.test.ts` (создать).

**Шаги реализации:**
1. Сигнатуры:
   ```ts
   export async function fetchSpotCandles(args: {
     symbol: string;
     interval: CandleInterval;
     limit?: number; // default 200, max 1000
   }): Promise<MarketCandle[]>;

   export async function fetchSpotTicker(symbol: string): Promise<{
     symbol: string;
     lastPrice: number;
     bidPrice: number;
     askPrice: number;
     bidSize: number;
     askSize: number;
     timestamp: Date;
   }>;

   export async function getSpotInstrumentInfo(symbol: string): Promise<{
     symbol: string;
     baseAsset: string;
     quoteAsset: string;
     tickSize: number;
     lotSize: number;
     minOrderSize: number;
     minOrderValue: number;
   }>;
   ```
2. Endpoints (Bybit v5):
   - Candles: `GET /v5/market/kline?category=spot&symbol=...`.
   - Ticker: `GET /v5/market/tickers?category=spot&symbol=...`.
   - Instrument: `GET /v5/market/instruments-info?category=spot&symbol=...`.
3. Auth не требуется для market-data — public endpoints. Используется тот же HTTP-клиент, что в существующем коде (axios / undici, проверить).
4. **Cache.** Instrument info — TTL 24h в memory (instruments редко меняются). Ticker — TTL 5s. Candles — без кэша на этом уровне.
5. Normalizer: spot kline формат идентичен linear (Bybit v5 унифицирует). Если есть разница в timestamp / orderbook fields — добавить spot-overload в normalizer, не менять linear-логику.
6. Логирование на каждом запросе (`logger.debug`) с маркером "[bybit-spot]".

**Тест-план:**
- Unit с mocked HTTP: `fetchSpotCandles("BTCUSDT", "M5", 100)` → возвращает 100 candles.
- Unit: `fetchSpotTicker("BTCUSDT")` → возвращает объект с числовыми полями.
- Unit: `getSpotInstrumentInfo` → возвращает корректную структуру.
- Cache: два последовательных `fetchSpotTicker` в пределах 5s → один HTTP-запрос (assert mock call count).
- Error: 4xx от Bybit → typed exception, понятный message.

**Критерии готовности:**
- 3 функции exported.
- Unit-тесты зелёные.
- Используется существующий HTTP-клиент / нормализатор; никакого нового HTTP-стека.
- Lint / type-check pass.

---

### 55-T2: Завершить spot-leg execution в `/hedges/:id/execute` и `/hedges/:id/exit`

**Цель:** в `/hedges/:id/execute` и `/hedges/:id/exit` дойти до реального вызова Bybit API для spot-ноги. Перевести `BotIntent` со `category="spot"` в `LegExecution` запись после успешного fill.

**Файлы для изменения:**
- `apps/api/src/routes/hedges.ts` — `POST /hedges/:id/execute`, `POST /hedges/:id/exit`.
- `apps/api/src/lib/bybitOrder.ts` — без правок (уже параметризован), но добавить unit-tests конкретно для `category: "spot"` ветки если их нет.
- `apps/api/tests/routes/hedges.test.ts` — расширить.

**Шаги реализации:**
1. В `/hedges/:id/execute`:
   - Загрузить `HedgePosition` + два `BotIntent`'а (один linear, один spot).
   - Для linear-ноги — текущий путь через `bybitOrder({ category: "linear", ... })` (если он сегодня уже работает; если нет — это блокер, эскалируется как pre-T2 fix).
   - Для spot-ноги — новый путь: `bybitOrder({ category: "spot", side: "Buy", symbol, qty: spotQty, orderType: "Market" })`. Sizing: spot quantity вычисляется через `getSpotInstrumentInfo` из 55-T1 (минимум `minOrderSize`, кратно `lotSize`). При невозможности удовлетворить min — отказ операции с понятной ошибкой.
   - **Атомарность.** Bybit API не предлагает atomic «execute both legs». Реализуем sequential: spot first (он медленнее по latency), затем perp. Если spot fail → перп не открывается, hedge помечается `FAILED`. Если spot ok, perp fail → spot уже открыт; делаем compensating market sell на spot (best-effort), помечаем `PARTIAL_ERROR`. Compensating sell — простая логика, не retry-loop.
   - После успеха: создать `LegExecution` записи (одна на каждую ногу) с реальными fill prices/qtys из Bybit response. `HedgePosition.status = EXECUTED`.
2. В `/hedges/:id/exit`:
   - Reverse direction: spot Sell + perp Buy-to-close.
   - Аналогичная sequential logic. Если perp close fail после spot sell → `PARTIAL_EXIT_ERROR` алёрт.
   - `HedgePosition.status = EXITED`. Запись финальных fill prices в новую (или existing) `LegExecution` с типом `EXIT`.
3. Idempotency: повторный POST `/hedges/:id/execute` после успешного execute → 409 `already executed`. Не выполнять второй раз.
4. Logging: каждый вызов Bybit API + response status + ms — в structured log с hedgeId.

**Тест-план:**
- Mock Bybit: успешный execute обоих legs → `HedgePosition.status === "EXECUTED"`, две `LegExecution` записи.
- Mock: spot fail → linear leg не вызывается, `status = "FAILED"`, нет orphan позиций.
- Mock: spot ok, perp fail → compensating spot sell вызывается, `status = "PARTIAL_ERROR"`, алёрт залогирован.
- Mock: повторный execute → 409.
- Тоже для `/exit` — mock сценарии successful, partial, error.

**Критерии готовности:**
- Реальная spot-нога исполняется (пройдено на demo, не только моках).
- `LegExecution` записи содержат корректные fill data.
- Compensating logic покрыта тестом.
- Existing `/hedges/entry` endpoint без правок (он только создаёт записи).

---

### 55-T3: Funding scanner — UI таблица кандидатов

**Цель:** вывести существующий `lib/funding/scanner.ts` через эндпоинт + UI таблицу кандидатов. Пользователь видит, на каких symbol сейчас положительный funding и насколько он перекрывает предполагаемые costs.

**Файлы для изменения:**
- `apps/api/src/routes/funding.ts` (создать).
- `apps/web/src/app/lab/funding/page.tsx` (создать).
- `apps/web/src/app/lab/funding/CandidatesTable.tsx` (создать).
- `apps/api/tests/routes/funding.test.ts` (создать).

**Шаги реализации:**
1. **API.** `POST /funding/scan` → запускает `scanner.scan()` (или эквивалентную функцию из `lib/funding/scanner.ts`), возвращает массив:
   ```ts
   type FundingCandidate = {
     symbol: string;
     currentFundingRate: number;       // например, 0.0001 = 0.01% per 8h
     annualizedRate: number;           // *3*365
     nextFundingTime: string;          // ISO
     spotBidAsk: { bid: number; ask: number };
     perpBidAsk: { bid: number; ask: number };
     spread: number;                   // (perp.mid - spot.mid) / spot.mid
     estimatedNetReturn: number;       // funding - feesEstimate - spreadCost
   };
   ```
   Если scanner синхронен и быстр — возвращаем сразу. Если требует async fetch — POST возвращает `{ scanId }`, GET `/funding/scan/:id` возвращает результат (как у sweep). Уточнить по существующему `scanner.ts` — какая реализация.
2. **GET `/funding/snapshots`** — read-only access к существующей `FundingSnapshot` таблице, для history view.
3. **UI page `/lab/funding`.** Кнопка "Scan now" → POST → таблица результатов. Колонки: Symbol, Funding Rate (8h), Annualized, Next Funding, Spread, Net Return Estimate, Action (кнопка "Open hedge bot" → инстанцирует funding-arb preset с этим symbol).
4. **Sort / filter.** Default sort by `estimatedNetReturn DESC`. Filter inputs: `min funding rate`, `max spread`, `symbol search`.
5. Авторизация: только аутентифицированные пользователи.
6. **Rate limit на `/funding/scan`.** 1 запрос в 30 сек на пользователя — Bybit market-data rate-limit предотвращает спам.

**Тест-план:**
- POST `/funding/scan` — возвращает массив (mock scanner output).
- GET `/funding/snapshots` — возвращает persisted history.
- Action "Open hedge bot" → корректно вызывает `POST /presets/funding-arb/instantiate` с overrides.
- UI smoke: таблица рендерится, sort/filter работают.
- Rate limit срабатывает на втором быстром запросе.

**Критерии готовности:**
- Эндпоинты работают.
- UI page доступна, smoke прошёл.
- Existing `lib/funding/scanner.ts` не модифицируется в части business-логики; правки только в части invoke / streaming output.

---

### 55-T4: Funding-arb «strategy mode» + dedicated hedgeBotWorker

**Цель:** ввести `Bot.mode` (enum `DSL | FUNDING_ARB`); создать dedicated runtime `hedgeBotWorker.ts`; routing — по `bot.mode`.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — `BotMode` enum, `Bot.mode BotMode @default(DSL)`.
- `apps/api/prisma/migrations/<timestamp>_bot_mode/migration.sql`.
- `apps/api/src/runtime/hedgeBotWorker.ts` (создать).
- `apps/api/src/botWorker.ts` — на старте каждого tick / scheduler — если `bot.mode === FUNDING_ARB`, делегировать `hedgeBotWorker.tick(bot)` и пропустить DSL evaluator. Это minimal-touch — добавление одной ветки.
- `apps/api/prisma/seed/presets/funding-arb.json` (создать) — preset с `defaultBotConfigJson.mode = "FUNDING_ARB"`.
- `apps/api/src/routes/presets.ts` — instantiate-обработчик из `docs/51-T3` копирует `mode` из `defaultBotConfigJson` в `Bot.create({ mode })`.

**Шаги реализации:**
1. **Schema.**
   ```prisma
   enum BotMode {
     DSL
     FUNDING_ARB
   }
   model Bot {
     // ... existing
     mode BotMode @default(DSL)
   }
   ```
   Миграция additive: existing rows получают `DSL` (default). `bots.test.ts` зелёный без правок.
2. **`hedgeBotWorker.tick(bot)`:**
   - Stage 1 (no active hedge): запустить `scanner.scan()`, выбрать кандидата по `bot.config.thresholds`, если есть — POST `/hedges/entry` + POST `/hedges/:id/execute`. После успеха `Bot.lastHedgeId` (новое nullable поле; добавить в той же миграции) указывает на активный hedge.
   - Stage 2 (active hedge, до funding): sleep до `nextFundingTime + delta_buffer` (нет polling — это event-driven через scheduled task).
   - Stage 3 (post-funding): verify funding payment via Bybit account API; POST `/hedges/:id/exit`. `Bot.lastHedgeId = null`. Loop to Stage 1.
   - Каждый stage переход — log + intent в существующий `BotIntent` для аудита (хоть это и не trading intent в DSL смысле, переиспользуем таблицу).
3. **State machine.** `BotRunState` enum уже существует. Новые «псевдо-состояния» хранятся в `Bot.metaJson.hedgeStage` (`"SCANNING" | "WAITING_FUNDING" | "EXITING"`), не расширяем enum чтобы не ломать существующий код.
4. **Routing.** В `botWorker.ts` (или scheduler — wherever ticks dispatched) — одна if-ветка:
   ```ts
   if (bot.mode === "FUNDING_ARB") {
     await hedgeBotWorker.tick(bot);
     return;
   }
   // ... existing DSL path
   ```
5. **Seed preset.** `funding-arb.json`:
   ```json
   {
     "name": "Funding Arbitrage (Bybit Perp + Spot)",
     "description": "Delta-neutral hedge: short perp + long spot when funding rate is positive. BETA — multi-leg execution.",
     "category": "arb",
     "dslJson": null,
     "defaultBotConfigJson": {
       "symbol": "BTCUSDT",
       "mode": "FUNDING_ARB",
       "minFundingRate": 0.0002,
       "maxSpreadBps": 5,
       "quoteAmount": 1000
     }
   }
   ```
   Видимость — `BETA` после T6.

**Тест-план:**
- Миграция applied: existing bots `mode === "DSL"`, новый bot c `mode="FUNDING_ARB"` создаётся.
- Routing: bot с `mode=DSL` идёт через `botWorker`, evaluator вызывается; bot с `mode=FUNDING_ARB` — через `hedgeBotWorker`, evaluator НЕ вызывается (mock evaluator проверяет 0 вызовов).
- `hedgeBotWorker.tick`: на mocked scanner выдает кандидата → entry+execute вызываются.
- `tick` после executed: ожидает funding window → exit вызывается.
- Recovery: если процесс перезапущен в Stage 2 — на следующем tick stage восстанавливается из `Bot.metaJson.hedgeStage` + `lastHedgeId`.

**Критерии готовности:**
- Existing DSL-боты работают без регрессий (tests `botWorker/*.test.ts` зелёные).
- `hedgeBotWorker` тесты зелёные.
- `botWorker.ts` изменения локализованы в одной if-ветке.
- Seed preset создан, instantiate работает (проверено вручную).

---

### 55-T5: Spot/perp balance reconciliation + dual API key

**Цель:** dual API key (perp + spot) на уровне `ExchangeConnection`; reconciliation при старте hedge — проверка достаточности balance на обеих сторонах.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — `ExchangeConnection` расширяется опциональными `spotApiKey String?`, `spotApiSecret String?` (encrypted, reuse existing crypto helpers). Миграция additive.
- `apps/api/src/lib/exchange/balanceCheck.ts` (создать) — `checkBalanceForHedge(connection, symbol, quoteAmount): Promise<{ ok: boolean; reason?: string }>`.
- `apps/api/src/runtime/hedgeBotWorker.ts` — вызов `checkBalanceForHedge` перед entry.
- `apps/api/tests/lib/exchange/balanceCheck.test.ts`.
- UI: `apps/web/src/app/account/exchange-connection/...` (пути уточнить по существующему фронту) — добавить optional поля spot key/secret.

**Шаги реализации:**
1. **Schema.** Поля `spotApiKey`, `spotApiSecret` опциональны. Если хотя бы одно null — `ExchangeConnection.canTradeSpot()` возвращает false. Funding-arb боты, которым нужен spot, при `canTradeSpot=false` отказывают в entry с понятной ошибкой.
2. **balanceCheck.**
   - Запросить `GET /v5/account/wallet-balance?accountType=UNIFIED` (linear) и `?accountType=SPOT` (или единый — Bybit unified трекинг работает по-разному; уточнить по docs Bybit). Вернуть available USDT-equivalents.
   - Проверить, что perp side имеет достаточно для short с leverage; spot side имеет достаточно USDT для buy `quoteAmount`.
   - Безопасный buffer 10% сверх минимума, чтобы fee/slippage не убили execute.
3. **UI.** В странице ExchangeConnection — два набора полей: "Perp API key/secret" (existing), "Spot API key/secret" (new, optional, с подсказкой "required for funding arbitrage strategy").
4. **Single-key fallback.** Если у Bybit-аккаунта unified-маржа и один API key с обеими permissions — пользователь оставляет spot fields пустыми; `balanceCheck` использует existing key для обоих запросов. Логика выбора:
   ```ts
   const spotCreds = connection.spotApiKey ?? connection.apiKey;
   ```
5. **Permissions check на старте.** При создании `ExchangeConnection` или функции "Test connection" — пробуем `GET /v5/account/info` с обоими ключами и проверяем scope'ы (Bybit отдаёт permissions). Если spot scope отсутствует — warning в UI.

**Тест-план:**
- Миграция applied — existing connections без spot полей живы.
- `balanceCheck` mock'ed: достаточный баланс → ok; недостаточный → not ok с reason.
- Single-key fallback: connection без spot key → balanceCheck использует apiKey, не падает.
- UI smoke: spot fields добавляются, сохраняются, отображаются маскированными.

**Критерии готовности:**
- `ExchangeConnection` расширен.
- `balanceCheck` работает для обоих режимов (single-key и dual-key).
- `hedgeBotWorker` отказывает в entry при недостаточном балансе с понятной ошибкой.
- UI обновлён, smoke прошёл.

---

### 55-T6: Acceptance gate (60-мин demo с funding event) + BETA publish + matrix update

**Цель:** acceptance gate (60-мин demo run with funding event); расширение PresetVisibility до `BETA`; публикация `funding-arb` как `BETA`; capability matrix update.

**Файлы для изменения:**
- `apps/api/prisma/schema.prisma` — расширить `PresetVisibility` enum (см. §Решение A4).
- `apps/api/prisma/migrations/<timestamp>_preset_beta/migration.sql`.
- `apps/api/src/routes/presets.ts` — корректировка фильтрации `visibility IN ('PUBLIC', 'BETA')` для аутентифицированных user'ов.
- `apps/web/src/app/lab/library/PresetCard.tsx` — BETA badge (yellow, текст "BETA — multi-leg execution, monitor closely").
- `apps/api/scripts/demoSmoke.fundingArb.ts` (создать) — обёртка demoSmoke, заточенная под funding event window.
- `docs/55-baseline-results.md` (создать) — companion-doc с раунд-ап.
- `docs/strategies/04-funding-arbitrage-delta-hedge.md` — добавить implementation status block.
- `docs/strategies/08-strategy-capability-matrix.md` — строка `funding-arb: implemented (BETA)`.

**Шаги реализации:**
1. **Schema.** `ALTER TYPE "PresetVisibility" ADD VALUE 'BETA' BEFORE 'PUBLIC'`. Existing rows с `PRIVATE` или `PUBLIC` остаются. Default не меняется.
2. **Filtering.** В `GET /presets` без auth → `visibility = "PUBLIC"`. С auth → `visibility IN ("PUBLIC", "BETA")`. С admin → всё. Update `getPreset` аналогично.
3. **UI badge.** На `PresetCard` если `preset.visibility === "BETA"` — yellow badge + tooltip с warning text. Тот же подход для странице `/bots/:id` если `bot.templateSlug` соответствует BETA preset'у.
4. **Acceptance run.**
   - Скрипт `demoSmoke.fundingArb.ts`: принимает `--funding-time T` (next funding timestamp). Запускает бот за 30 мин до T, мониторит до T+30 мин.
   - Acceptance criteria:
     - Entry: hedge entered with both legs filled (LegExecution × 2 records exist) до funding_time.
     - Funding payment: запрос Bybit account API после funding_time подтверждает payment.
     - Exit: hedge exited with both legs closed после funding payment.
     - P&L: `realized_pnl ≈ funding_payment − total_fees − slippage_estimate`. Tolerance ±20% (потому что demo Bybit может flash-tick spreads).
     - 0 unhandled errors в течение всего run.
   - Если acceptance fail на первой попытке — не паника. Funding events каждые 8h; повторить на следующем. Документировать каждый attempt в companion-doc.
5. **Publish.**
   - `publishPreset.ts --slug funding-arb --visibility BETA` (расширить скрипт из `docs/53-T4` поддержкой `BETA` value).
   - Audit log entry.
6. **Matrix + concept doc updates** — те же что в `docs/53-T5`/`docs/54-T4`, но для funding-arb.

**Тест-план:**
- Миграция enum applied, existing API endpoints не сломаны.
- Filtering корректен на трёх уровнях (none / authed / admin).
- BETA badge виден в UI.
- `demoSmoke.fundingArb.ts` запускается, отчёт сохранён.
- Acceptance criteria evaluated в companion-doc для конкретного run.

**Критерии готовности:**
- `funding-arb` в `BETA`, виден в `/lab/library` для аутентифицированных user'ов с явным badge.
- Companion-doc заполнен реальным runs.
- Capability matrix обновлён.
- Concept doc содержит implementation status.
- Acceptance pass подтверждён хотя бы для одного funding event window.

---

## Порядок выполнения задач

```
55-T1 (spot adapter) ──┐
55-T3 (scanner UI)  ──┴──→ 55-T2 (spot exec) ──→ 55-T4 (mode + worker) ──→ 55-T5 (balance) ──→ 55-T6 (acceptance + BETA)
```

- 55-T1 и 55-T3 — независимы и могут идти параллельно. T1 — фундамент; T3 — пользовательский discovery surface.
- 55-T2 (spot execution) требует T1 (spot adapter) и существующего `bybitOrder` с `category=spot`.
- 55-T4 (mode + worker) — после T2 (worker вызывает execute).
- 55-T5 (balance) — после T4 (worker integration point для balanceCheck перед entry).
- 55-T6 (acceptance + BETA publish) — последняя; требует всё предыдущее.

Каждая T-задача — отдельный PR. T1 + T3 могут идти в одном спринте параллельно.

## Зависимости от других документов

- `docs/50` — родительский overview, `§Решение 4` явно указывает funding-arb как параллельный трек.
- `docs/51` — обязателен. T6 публикует preset через preset system; T6 расширяет `PresetVisibility` enum, заведённый в `docs/51-T1`.
- `docs/52` — **независим.** Funding-arb single-TF (smoke интервал — типично M5 для мониторинга, но не требует bundle). Никаких блок-зависимостей.
- `docs/53/54` — независимы. Funding-arb идёт параллельно. T6 (go/no-go gate) в `docs/54` обновляется доп строкой про funding-arb sub-gate.
- `docs/strategies/04-funding-arbitrage-delta-hedge.md` — concept-doc, обновляется в T6.
- `docs/strategies/08-strategy-capability-matrix.md` — matrix, обновляется в T6.
- `docs/15-operations.md` — runbook должен включать «как остановить активный hedge при инциденте» (добавить параграф в T6 либо отдельным follow-up).

## Backward compatibility checklist

- Все Prisma миграции — additive: новый `Bot.mode` с default `DSL` (existing rows получают этот default), новые nullable spot credentials в `ExchangeConnection`, новое значение `BETA` в `PresetVisibility` enum.
- Existing DSL-боты работают без правок. Routing в `botWorker.ts` — одна if-ветка на старте tick.
- `bybitOrder.ts` — без правок (уже параметризован).
- `routes/hedges.ts` `/entry` endpoint — без правок (только creation `BotIntent` записей). Изменения в `/execute` и `/exit`.
- `lib/funding/scanner.ts` — без правок business-логики.
- `signalEngine.ts`, `exitEngine.ts`, `positionManager.ts`, `dslEvaluator.ts` — не модифицируются. Funding-arb их не использует.
- `routes/presets.ts` (`docs/51-T2/T3`) — фильтры `visibility` в two мест расширяются на `BETA`; instantiate-обработчик копирует `mode` из defaultBotConfigJson — это лёгкое расширение, не breaking.
- Existing Lab Library carddesign — добавляется один conditional badge для `BETA`; PUBLIC карточки выглядят без изменений.
- AI-чат, Lab Build/Test/Optimise/Walk-Forward — не затронуты.

## Ожидаемый результат

После закрытия 55-T1..55-T6:

- В Lab Library 5 карточек: 4 PUBLIC (Adaptive Regime, DCA Momentum, MTF Scalper, SMC Liquidity Sweep) + 1 BETA (Funding Arb) с явным warning-badge.
- Bybit Spot adapter `bybitSpot.ts` существует, market-data доступна по public endpoints.
- Spot-нога реально исполняется через `bybitOrder({ category: "spot" })`. `LegExecution` записи реальные, не «бумажные».
- Dedicated `hedgeBotWorker` обрабатывает funding-arb cycle (scan → entry → wait → exit) без вмешательства в DSL `botWorker`.
- Funding scanner UI доступен в `/lab/funding`; пользователь видит candidates с net-return оценкой.
- ExchangeConnection поддерживает dual API key (perp + spot), balanceCheck блокирует entry при недостаточных средствах.
- Acceptance gate пройден: 60-минутный demo run с реальным funding event подтвердил end-to-end funding-arb cycle.
- BETA visibility означает: видно аутентифицированным user'ам, но not promoted to anonymous landing. Промоция в PUBLIC — после 30+ days BETA с положительной operational telemetry, отдельным решением вне этого документа.
- Docs/16 roadmap отражает: 5 флагманов delivered (4 PUBLIC, 1 BETA). Stage 3 закрыт.
