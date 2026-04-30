# 50. Flagship Activation Plan

Статус: draft  
Владелец: core trading  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Связанные документы: `docs/strategies/01-flagship-overview.md`, `docs/strategies/07-flagship-implementation-roadmap.md`  
Дорожка: B (production rollout)

## Контекст

Дорожка A (research workflow) закрыта: реализованы и развёрнуты в проде backtest realism (`docs/46`), strategy optimizer (`docs/47`), walk-forward validation (`docs/48`) и расширенные метрики отчёта (`docs/49`). Прод обновлён 2026-04-30 14:30 UTC до коммита `d939998` (30 коммитов, 3 additive миграции; rollback-tag `deploy-43eae33-pre-research-track`, бэкап БД `/var/backups/botmarket-pre-deploy-20260430T142212Z.dump`).

Что фактически есть в коде на момент 2026-04-30 (проверено):

- 33 DSL-блока supported в evaluator + compiler (`apps/api/src/lib/compiler/supportMap.ts`; матрица — `docs/strategies/08-strategy-capability-matrix.md`).
- `signalEngine.ts`, `exitEngine.ts`, `positionManager.ts` лежат в `apps/api/src/lib/`. `botWorker.ts` импортирует их (`apps/api/src/lib/botWorker.ts:47`–`54`) и вызывает в основном цикле (`apps/api/src/lib/botWorker.ts:1431`–`1432`).
- `apps/api/src/lib/runtime/` содержит только: `dcaBridge.ts`, `dcaEngine.ts`, `patternEngine.ts`, `positionSizer.ts`.
- Funding lib уже частично реализована: `apps/api/src/lib/funding/` = `basis.ts`, `fetcher.ts`, `hedgePlanner.ts`, `hedgeTypes.ts`, `index.ts`, `ingestJob.ts`, `ingestion.ts`, `scanner.ts`, `types.ts`. Prisma-модели `FundingSnapshot` (`apps/api/prisma/schema.prisma:764`), `SpreadSnapshot` (`:774`), `HedgePosition` (`:794`), `LegExecution` (`:810`) присутствуют; роут `/hedges` (`apps/api/src/routes/hedges.ts`) живой.
- Spot-адаптер Bybit **отсутствует**: `apps/api/src/lib/exchange/` содержит только `instrumentCache.ts` и `normalizer.ts`. Нет ни ордеров, ни рыночных данных по spot — без него funding-arb (delta-hedge со spot-ногой) не запускается.
- `Bot.timeframe: Timeframe` — единичный таймфрейм (`apps/api/prisma/schema.prisma:147`); valid values в API — `"M1" | "M5" | "M15" | "H1"` (`apps/api/src/routes/bots.ts:13`). `BacktestSweep.datasetId String` (`apps/api/prisma/schema.prisma:691`) и `WalkForwardRun.datasetId String` (`:741`) — единичный датасет на запуск. Multi-interval бэктеста и multi-interval ботов **нет**.
- `StrategyPreset` Prisma-модель **отсутствует**.
- `apps/api/src/routes/demo.ts` содержит только два hardcoded публичных preset'а — `btc-breakout-demo` (60m, 90 дней) и `eth-mean-reversion-demo` (15m, 45 дней) — без auth, без записи в БД, для landing-page демонстрации (`apps/api/src/routes/demo.ts:29`–`44`). Это не та сущность, которую можно реюзать как «фабрика стратегий».
- Spec'и пяти флагманских стратегий уже написаны: `docs/strategies/02-smc-liquidity-sweep.md`, `03-adaptive-regime-bot.md`, `04-funding-arbitrage-delta-hedge.md`, `05-mtf-confluence-scalper.md`, `06-dca-momentum-bot.md`.
- Adaptive Regime spec (`docs/strategies/03-adaptive-regime-bot.md`) требует `["5m", "1H"]` MTF + SuperTrend(ATR=55, factor=2.0) на 5m + EMA 200 на 1H + BB+RSI mean-reversion в range-режиме.

## Цель

Запустить пять флагманских стратегий из `docs/strategies/01-flagship-overview.md` в production: пользователь может выбрать пресет в Lab → инстанцировать → запустить бот в DEMO/PROD без правки DSL вручную. Активация делается **без расширения evaluator-а** — все composite-сигналы пишутся через существующие 33 примитивных DSL-блока. Параллельно даётся независимый трек funding-arb, требующий новой архитектуры (spot adapter + multi-leg execution).

## Не входит в задачу

- Расширение evaluator-а под высокоуровневые имена сигналов (например, `supertrend_direction`, `bb_rsi_reversion`). Composite-логика выражается через цепочки `compare`, `cross`, `and_gate`, `enter_adaptive` — этого достаточно (см. `docs/strategies/08-strategy-capability-matrix.md`).
- Новые типы биржевых ордеров и новые exchange-провайдеры (кроме Bybit Spot adapter в треке funding-arb).
- Distributed worker-pool, ML-блоки, autoML, оптимизатор пресетов.
- Marketplace монетизация / paywall — сами presets лежат в свободном доступе.
- Любые правки `runBacktest`, `dslEvaluator`, `botWorker.ts` core-loop, кроме точечных адаптаций, прописанных в дочерних документах.

## Архитектурные решения

Эти решения зафиксированы и в дочерних документах не переоткрываются.

### A1. Preset = фабрика StrategyVersion

`StrategyPreset` хранит шаблон DSL и параметры по умолчанию. Operation `instantiate` создаёт обычные `Strategy` + `StrategyVersion` + `Bot(status=DRAFT)`. После instantiate preset-связи у бота нет — он становится самостоятельной стратегией пользователя. Никакой отдельной runtime-семантики «preset-бот» — `botWorker` про presets ничего не знает. Это резко сокращает поверхность изменений: ровно одна новая таблица + один CRUD + один instantiate-эндпоинт + UI-галерея. Подробности — `docs/51`.

### A2. Multi-interval bundle = JSON-map на существующих сущностях

Adaptive Regime и MTF Scalper требуют доступа к 2..3 таймфреймам одновременно. Решение: в `BacktestSweep`, `WalkForwardRun`, `Bot` добавляется новая nullable колонка `datasetBundleJson Json?` со схемой `Record<Interval, DatasetId>` (например, `{"M5": "ds_abc", "H1": "ds_def"}`). Существующее поле `datasetId` (для sweep/walk-forward) и `timeframe` (для Bot) сохраняются: trading-таймфрейм/датасет = primary; bundle — дополнительные таймфреймы. Отдельной таблицы `DatasetBundle` в v1 нет — это лишнее indirection. Подробности — `docs/52`.

### A3. Composite-сигналы через примитивные DSL-блоки

Любой высокоуровневый сигнал из spec'ов флагманских стратегий разбирается на цепочку из 33 базовых блоков. Например, `supertrend_direction == "up"` → `cross(close, supertrend(ATR=55, factor=2.0), direction="above")` + `and_gate(...)`. `bb_rsi_reversion` → `compare(rsi(14), op="<", value=30) AND compare(close, op="<", path="bbands.lower")`. Каждое такое разложение появляется как golden-fixture в `apps/api/tests/fixtures/strategies/<name>.json` и проверяется test'ом, что DSL компилируется и эвалюэтор даёт ожидаемый сигнал на синтетических свечах. Подробности — `docs/53`.

### A4. Funding Arb — отдельный трек

Multi-leg execution (perp short + spot long), spot rate limits, spot/perp balance reconciliation, два набора API-ключей — другая архитектура. Этот трек идёт **параллельно** активации флагманских пяти и не блокирует их. Подробности — `docs/55`.

### A5. Acceptance-gate для каждой стратегии

Pre-production gate (см. `docs/47-T6` стиль): прежде чем стратегия попадает в галерею публичных пресетов, она должна пройти три ворот:

1. **Golden DSL-fixture** — DSL компилируется без ошибок, evaluator на синтетических свечах даёт сигналы в ожидаемом порядке (unit-тест).
2. **Walk-forward acceptance** — `pnlPct > 0`, `sharpe > 0.3` (или соразмерный профильный порог из spec'а), `maxDrawdownPct > -25%` на 6+ folds (не cherry-picked окно). Используется уже существующий `WalkForwardRun` (`docs/48`).
3. **30-минутный demo smoke** — запуск в DEMO-аккаунте (Bybit testnet или sandbox) минимум 30 минут без падений, без unhandled rejection в Sentry, не более одного circuit-breaker трипа. Прогон фиксируется в release-checklist'е стратегии.

Стратегия, не прошедшая хотя бы одни ворота, остаётся в `presetVisibility = "PRIVATE"` и не появляется в публичной галерее.

## Раскладка работ по документам

```
docs/50 (overview, этот файл)
├── docs/51 (preset system)        — независимо, можно стартовать сразу
├── docs/52 (multi-interval bundle) — независимо, можно стартовать сразу
├── docs/53 (adaptive regime bot)   — depends on 51 + 52
├── docs/54 (flagship rollout: DCA, MTF Scalper, SMC) — depends on 51 + 52
└── docs/55 (funding arb plan)      — независимо
```

Параллелизация:

- 51 и 52 идут параллельно — это самостоятельные slice'ы.
- 53 — первая end-to-end активация (Adaptive Regime). Его задача — обкатать пайплайн (preset → instantiate → walk-forward → demo smoke) на одной стратегии.
- 54 повторяет проверенный пайплайн на оставшихся четырёх флагманах. SMC/MTF Scalper тоже требуют 52 (multi-TF). DCA и Momentum обходятся одним TF, но используют те же presets (51).
- 55 — отдельный трек, не зависит от 51..54.

## Зависимости

- `docs/51-strategy-preset-system.md` — нужен для всех остальных активационных документов.
- `docs/52-multi-interval-dataset-bundle.md` — нужен для 53 и для SMC/MTF в 54.
- `docs/53-adaptive-regime-bot-activation.md` — pilot end-to-end (минимум одна полностью работающая стратегия).
- `docs/54-flagship-rollout.md` — масштабирование пилота на остальные четыре стратегии.
- `docs/55-funding-arbitrage-plan.md` — независимый параллельный трек.
- Существующие документы: `docs/44`..`docs/49` (research dorожка) — фундамент, на котором стоит всё.

## Backward compatibility

- Все Prisma-миграции — additive (новая таблица `StrategyPreset` и новые nullable колонки `datasetBundleJson`).
- Существующие боты, sweep'ы, walk-forward run'ы продолжают работать без правок (datasetBundleJson = `null` → старый single-interval путь).
- `botWorker.ts` core-loop не трогается за пределами заранее объявленных точек (загрузка multi-TF свечей в `docs/52`).
- Public-landing demo (`/demo/backtest`) и его hardcoded presets остаются как есть — это не та же сущность, что `StrategyPreset`.
- Никаких изменений в `runBacktest`, `dslEvaluator`, exchange-логике (вне трека `docs/55`).

## Acceptance criteria для всего блока 50

После закрытия 51..54:

- В Lab → Library → Presets отображается публичная галерея ≥ 5 стратегий (Adaptive Regime, SMC Liquidity Sweep, MTF Confluence Scalper, DCA Momentum, Bollinger Mean-Reversion или эквивалент).
- Любой пользователь может в один клик инстанцировать пресет → получить `Bot(status=DRAFT)`, готовый к запуску в DEMO.
- Каждая публичная стратегия прошла все три gate'а из A5 и имеет:
  - golden DSL-fixture в `apps/api/tests/fixtures/strategies/<name>.json`,
  - walk-forward acceptance row в release-checklist'е,
  - demo smoke лог.
- 33 DSL-блока остаются единственным supported set'ом — ни одного нового блока не добавлено. Capability-матрица (`docs/strategies/08-strategy-capability-matrix.md`) обновлена с пометкой «released» против каждой стратегии.

После закрытия 55:

- Bybit Spot adapter активен: `apps/api/src/lib/exchange/bybitSpot.ts` + интеграционные тесты на testnet.
- Hedge multi-leg engine принимает spot-ногу; `LegExecution` корректно записывает spot-fills.
- Funding-arb preset в галерее с пометкой `BETA`, доступен только в DEMO до прохождения acceptance-gate'а на проде.

## Риски и контрмеры

- **Composite-сигналы окажутся выразительно недостаточными для какого-то spec'а.** Контрмера: golden-fixture пишется до DSL-кодирования; если для spec'а нет валидной разбивки на 33 блока — стратегия откладывается, вместо расширения evaluator-а. Это сознательный конструктивный выбор `A3`, а не дефект.
- **Multi-TF загрузка свечей деградирует latency `botWorker`.** Контрмера: ленивая подгрузка более крупного TF (например, 1H обновляется только когда закрывается 1H-бар, а не на каждом 5m-тике). Подробности — `docs/52`.
- **Walk-forward acceptance не достигается на исторических данных.** Контрмера: спецификация считается research-failure, а не engineering-failure — стратегия не активируется, в release-checklist'е фиксируется причина. Это здоровый исход: пайплайн отработал.
- **Spot adapter обнаруживает отличия Bybit Spot API от Perp.** Контрмера: `docs/55` отдельным треком, без блокирования основной активации.

## Ожидаемый результат

Полностью функциональная воронка от пользователя до прод-бота: открыл галерею → выбрал пресет → инстанцировал → запустил в DEMO → walk-forward report зелёный → перевёл в PROD. Активированы пять флагманских стратегий + funding arb (последний — отдельным треком, в BETA). 33 DSL-блока остались неприкосновенными. Архитектура «preset = фабрика StrategyVersion» гарантирует, что после инстанцирования бот живёт по обычным правилам — никакого кодирования preset-семантики в runtime нет.
