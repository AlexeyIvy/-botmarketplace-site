# 50. Flagship Activation Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/strategies/07-flagship-implementation-roadmap.md`  
Дорожка: A (research → trading workflow)

## Контекст

Платформа прошла Track A (`docs/45-49`) и Stage 1–2 из `docs/strategies/07-flagship-implementation-roadmap.md` (foundation + DSL v2 + honest backtest). На момент 2026-04-30 в проде задеплоен `d939998` (см. снимок состояния от 2026-04-30 14:30 UTC). Что **уже есть** (проверено по коду):

- 33 DSL-блока статуса `supported` в `apps/api/src/lib/compiler/supportMap.ts` (см. `docs/strategies/08-strategy-capability-matrix.md`).
- Все P0/P1 индикаторы для флагманов: `vwap`, `adx`, `supertrend`, `volume_profile`, `proximity_filter`, `atr` (`apps/api/src/lib/indicators/`).
- Все SMC-блоки: `liquidity_sweep`, `fair_value_gap`, `order_block`, `market_structure_shift` (`apps/api/src/lib/runtime/patternEngine.ts`).
- DCA execution: `runtime/dcaEngine.ts`, `runtime/dcaBridge.ts`, блок `dca_config` supported.
- Runtime signal/exit/position layer: `apps/api/src/lib/signalEngine.ts`, `exitEngine.ts`, `positionManager.ts` — botWorker уже вызывает их в polling-loop (`botWorker.ts:1431-1432`).
- Production safety slice (Stage 8 early): зелёные тесты `safety/errorClassifier`, `safety/restartRecoveryAndKillSwitch`, `safety/circuitBreaker`, `safety/startupReconciliation`, `exchange/partialFill`.
- Funding data layer (частично): `apps/api/src/lib/funding/{fetcher,scanner,basis,hedgePlanner,ingestion}.ts`, модели Prisma `FundingSnapshot`, `SpreadSnapshot`, `HedgePosition`, `LegExecution`, роут `/hedges`.
- Walk-forward: `apps/api/src/lib/walkForward/{split,run,aggregate}.ts`, `WalkForwardRun` модель, POST/GET endpoints, UI panel (`docs/48`).

Что **отсутствует** относительно цели «5 флагманов готовы к demo-торговле»:

1. **Strategy Preset / Gallery system.** Нет модели `StrategyPreset` в Prisma. Нет API для каталога. Нет UI-galery. Нет one-click flow «карточка → бот на demo».  
   Единственное приближение — `routes/demo.ts` с двумя hardcoded breakout-presets для public landing page.
2. **Multi-interval dataset bundle.** `MarketDataset` хранит свечи **одного** интервала. Adaptive Regime требует `["5m", "1H"]`, MTF Scalper — `["1m", "5m", "15m"]`, SMC — `["15m", "1H", "4H"]`. Без этого ни один из трёх флагманов не backtestится честно и не запускается в runtime с консистентным MTF context.
3. **Composite signal types в DSL спецификациях стратегий не сверены с компилятором.** В `docs/strategies/03-adaptive-regime-bot.md` фигурируют `"supertrend_direction"`, `"bb_rsi_reversion"`, `"supertrend_flip_or_bb_midline"`. Это синтетические high-level имена — нужно либо реализовать в evaluator'е, либо переписать спецификацию через примитивы (`compare`, `cross`, `and_gate`, `enter_adaptive`).
4. **Bybit Spot execution adapter.** `find apps/api/src -name "*spot*"` — 0 файлов. Без него Funding Arb не может торговать spot-ногу.
5. **Demo connectivity smoke.** Ни один флагман не имеет автоматизированного теста «создать бота, запустить на Bybit demo на N минут, проверить что intents идут и нет unhandled errors». Только unit + integration.
6. **Production go/no-go gate** не оформлен как процедура. Нет осознанного критерия «готовы выпускать live», а значит нет и шкалы, по которой это решается.

## Цель

Довести 5 флагманских стратегий из `docs/strategies/01-flagship-overview.md` до состояния **production-ready demo**:
- one-click деплой из UI gallery → создаётся `StrategyVersion` + `Bot` (DRAFT);
- стратегия проходит golden backtest tests против известных fixtures;
- стратегия проходит walk-forward c положительным aggregate expectancy на N нерегрессионных датасетах;
- бот на Bybit demo генерирует intents, доезжающие до demo-endpoint'ов, без unhandled runtime errors в течение ≥30 минут (smoke);
- решение «открываем ли live-торговлю» принимается через явный gate-документ (не код).

## Не входит в задачу

- **Live Bybit trading** (real env). Все 5 стратегий доводятся только до demo. Promotion на live — отдельное продуктовое решение, оформляется в `docs/50-T10` gate-doc, но реализация / включение `BYBIT_ALLOW_LIVE` за пределами этой ветки документации.
- **Multi-symbol / multi-bot одновременно**. Каждый бот = одна symbol/strategy. Портфельные лимиты и кросс-стратегийные guards — out of scope.
- **AI-чат генерация Strategy Spec**. Существующая инфраструктура `apps/api/src/lib/ai/*`, `routes/ai.ts` остаётся как есть; UI-улучшения чата не входят.
- **Перепроектирование bot worker / lifecycle**. Изменения только additive — добавление новых полей/интентов/preset-flow. Текущая state machine `BotRunState` не пересматривается.
- **Реальные финансовые гарантии прибыльности.** «Положительный expectancy на walk-forward» — это статистическое условие приёмки, не обещание доходности.
- **Mutli-биржи** (Binance/OKX/etc).

## Архитектурные решения

### Решение 1: Preset как конкретная `StrategyVersion`-фабрика

Preset — это immutable JSON шаблон, который при `instantiate` производит:
1. Новый `Strategy` (если такого ещё нет в workspace) с `templateSlug` = preset.slug.
2. Новый `StrategyVersion` с `dslJson` из preset'а.
3. Новый `Bot` (status=DRAFT) с указанием на StrategyVersion.

Пользователь после instantiate видит обычного бота, который можно запускать через стандартный flow. Никакой отдельной runtime-семантики «preset-бот vs обычный» — preset только в момент создания.

### Решение 2: Multi-interval bundle = логический контейнер из N `MarketDataset`

Не вводим `DatasetBundle` как отдельную Prisma-сущность в первой версии. Вместо этого `BacktestSweep` / `WalkForwardRun` / `Bot` принимают `datasetBundleJson: { [interval]: datasetId }`. Это additive и совместимо с текущим single-interval API через нормализацию.

Подробности — в `docs/52-multi-interval-dataset-bundle.md`.

### Решение 3: Composite signal types — переписываем через примитивы

Не расширяем DSL evaluator под `"supertrend_direction"` etc. как отдельные типы. Вместо этого preset-DSL для Adaptive Regime составляется из существующих блоков: `supertrend` + `compare(direction, 1)` + `and_gate(EMA_200_1H_filter)`. Это сохраняет DSL-семантику минимальной и не вводит специальных «стратегических» типов сигналов в ядро.

Если конкретный флагман потребует семантики, не выражаемой через текущие 33 блока — этот gap фиксируется как **отдельный T-task на расширение блока**, а не как escape-hatch внутри preset'а.

### Решение 4: Funding Arbitrage — отдельный документ

Funding Arb структурно не похож на остальные 4 (multi-leg execution, spot+perp, hedge state). Включение его в общий план растянет роадмап и размоет фокус. Выделяется в `docs/55-funding-arbitrage-plan.md` как параллельный трек, который запускается **после** того, как первый non-Funding флагман прошёл go/no-go gate.

## Структура планирования

```
docs/50-flagship-activation-plan.md   ← этот документ (overview)
├── docs/51-strategy-preset-system.md           — preset model + API + UI gallery
├── docs/52-multi-interval-dataset-bundle.md    — MTF dataset pipeline
├── docs/53-adaptive-regime-bot-activation.md   — первая стратегия end-to-end
├── docs/54-flagship-rollout.md                  — DCA, MTF Scalper, SMC по шаблону
└── docs/55-funding-arbitrage-plan.md            — Funding Arb (параллельный трек)
```

Каждый дочерний документ — самодостаточный (Контекст / Цель / Не входит / Задачи T1..TN / Зависимости / Backward compat / DoD), как `docs/47`.

## Порядок выполнения

```
docs/51 ──┐
          ├──→ docs/53 ──→ docs/54 ──→ go/no-go gate (T10)
docs/52 ──┘                            │
                                       ↓
                                   docs/55 (start)
```

Конкретно:

1. **`docs/51` и `docs/52` — параллельно.** Оба — фундамент. 51 — preset system; 52 — multi-interval bundle. Они не конфликтуют (разные слои).
2. **`docs/53` — Adaptive Regime.** Использует обоих фундаментов. Это первый vertical slice.
3. **`docs/54` — DCA + MTF Scalper + SMC.** Используют те же фундаменты. DCA не требует MTF — может пойти первой; MTF Scalper и SMC требуют 52.
4. **Production go/no-go gate (T10 в docs/54).** Audit-doc, фиксирующий, что 4 не-Funding флагмана прошли все критерии готовности и можно осознанно переключать `BYBIT_ALLOW_LIVE` для отдельных пользователей.
5. **`docs/55` — Funding Arb.** Параллельный трек, не блокирует 51-54.

## Критерии готовности (на уровне всего плана)

Документ **50** считается «закрытым», когда:
- Все 5 дочерних документов созданы и каждое имеет статус `closed` (все T-задачи в нём смержены).
- 4 не-Funding стратегии задеплоены в Strategy Gallery и проходят свои DoD (см. соответствующие документы).
- `docs/55` либо закрыт, либо явно помечен deferred с описанием причин.
- В `docs/16-roadmap.md` обновлена секция Post-MVP — флагманы перестали быть «планируется».

## Зависимости

- `docs/45-49` — закрыты, поставка multi-param sweep, walk-forward, sharpe/PF/expectancy метрик. Используются как инструменты валидации (`docs/47` для оптимизации параметров preset'а; `docs/48` для walk-forward acceptance).
- `docs/strategies/01-08` — концептуальные доки 5 стратегий + capability matrix. Источник истинности по «что должна делать стратегия».
- `docs/10-strategy-dsl.md` — DSL v2. Возможно потребуется uplift'нуть один-два composite signal types (см. `docs/53`).
- `docs/14-deployment.md` / `docs/15-operations.md` — готовность инфраструктуры. Без правок в этом плане.
- `docs/05-security.md` / `docs/06-threat-model.md` — должны быть пересмотрены к моменту T10 (go/no-go gate) — расширение поверхности атаки за счёт автоматической торговли.

## Backward compatibility

- Все Prisma-миграции — additive (`StrategyPreset` — новая таблица; `BacktestSweep.datasetBundleJson` — новая nullable колонка; `Bot.templateSlug` — новая nullable колонка).
- Старые без-preset'овые потоки создания стратегии (Lab → Build → Compile → Backtest → Bot) остаются работающими.
- Старые single-interval бэктесты продолжают работать; multi-interval — новый additive путь.
- Никаких изменений в `BotIntent`, `BotRunState`, `IntentType` enum'ах в рамках этого плана (если потребуется — отдельный документ или явная правка `docs/52`).

## Ожидаемый результат

После закрытия всего плана:
- Пользователь открывает Strategy Gallery, видит 4 карточки (Adaptive Regime, DCA Momentum, MTF Scalper, SMC Liquidity Sweep), и опционально 5-ю (Funding Arb) если `docs/55` закрыт.
- Любая карточка → клик → бот на Bybit demo за <60 секунд.
- Каждая стратегия имеет golden tests + walk-forward acceptance, поэтому регрессии будущего рефакторинга индикаторов / runtime ловятся на CI.
- Существует осознанный, документированный gate для перехода на live.
- Funding Arb имеет отдельный статус (либо ready as 5th, либо deferred с явной причиной).
