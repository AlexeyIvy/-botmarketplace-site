# 54. Flagship Rollout — DCA / MTF Scalper / SMC

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Связанные спеки:
- `docs/strategies/02-dca-momentum-bot.md`
- `docs/strategies/05-mtf-scalper.md`
- `docs/strategies/06-smc-liquidity-sweep.md`

## Контекст

Текущее состояние (проверено по коду):

- **DCA Momentum (`docs/strategies/02-dca-momentum-bot.md`).** Single-TF (например, M15). Использует `dca_config` блок (supported в `apps/api/src/lib/compiler/supportMap.ts`), `dcaEngine.ts` и `dcaBridge.ts` в `apps/api/src/lib/runtime/`. Семантика: фиксированные averaging steps под управлением momentum-фильтра (RSI / MACD / EMA-trend).
- **MTF Scalper (`docs/strategies/05-mtf-scalper.md`).** 3 TF: M1 (entry timing) + M5 (signal) + M15 (trend filter). Все индикаторы supported. `intervalAlignment.ts` уже умеет резолвить эти TF в bundle.
- **SMC Liquidity Sweep (`docs/strategies/06-smc-liquidity-sweep.md`).** 3 TF: M15 (entry) + H1 (structure) + H4 (HTF bias). Использует `liquidity_sweep`, `fair_value_gap`, `order_block`, `market_structure_shift` блоки — все реализованы в `apps/api/src/lib/runtime/patternEngine.ts` и supported в `supportMap.ts`.
- Шаблон активации стратегии — установлен в `docs/53` для Adaptive Regime: T1 (DSL) → T2 (walk-forward) → T3 (demo smoke) → T4 (publish). Этот документ переиспользует тот же шаблон, по 4 шага на каждую из трёх стратегий, с поправками для DCA (нет MTF bundle).
- Production go/no-go gate как процедура — отсутствует. До этого момента нет осознанного критерия «можно открывать live». T6 этот пробел закрывает.

## Цель

Довести 3 не-Funding флагмана до состояния `PUBLIC` в Lab Library, по тому же шаблону, что Adaptive Regime в `docs/53`:

1. **DCA Momentum** — single-TF, использует `dcaEngine`. Активация наиболее простая.
2. **MTF Scalper** — multi-TF (M1+M5+M15). Стресс-тест для bundle на быстрых интервалах.
3. **SMC Liquidity Sweep** — multi-TF (M15+H1+H4). Стресс-тест для pattern-based блоков.

Каждая — golden DSL + walk-forward acceptance + 30-минутный demo smoke + capability matrix update.

После 54-T1..T3 готовы все 4 не-Funding пресета в `PUBLIC`. T6 — формализация go/no-go gate: документ-aудит, по которому принимается решение «можно включать `BYBIT_ALLOW_LIVE` для отдельных пользователей». Реализация переключателя — за пределами этого документа; здесь только процедура и критерии.

## Не входит в задачу

- **Funding Arbitrage.** Отдельный трек — `docs/55`.
- **Live trading включение.** T6 — это документ-gate, не код. Изменение `BYBIT_ALLOW_LIVE` env / админ-toggle для отдельных пользователей — отдельная инженерная задача, которая стартует после прохождения T6 для каждой конкретной стратегии.
- **Multi-symbol раскат каждой стратегии.** Один пресет = baseline на одном symbol (BTCUSDT для всех). ETH/SOL/etc — после go/no-go gate для конкретной стратегии.
- **Кросс-стратегийные portfolio limits.** Out of scope.
- **Перепроектирование `dcaEngine`/`patternEngine`.** Используем существующие реализации.
- **AI-чат генерация preset'ов для этих стратегий.** DSL фиксируются вручную (как в `docs/53-T1`), не через AI.
- **Полный admin UI для preset versioning.** Если нужно тюнить параметры baseline пресетов после публикации — это делается через создание нового slug (`dca-momentum-v2`).

## Архитектурные решения

### Решение 1: Шаблон 54-Tn повторяет docs/53 для каждой стратегии

Каждая T-задача (T1, T2, T3) внутри себя повторяет структуру docs/53-T1..T6 — DSL → walk-forward → demo smoke → publish — но компактнее, потому что инфраструктура уже есть. Каждая T-задача = весь lifecycle одной стратегии до PUBLIC. Это экономнее, чем плодить 18 sub-tasks (3 стратегии × 6 шагов).

### Решение 2: Один companion-doc на каждую стратегию

`docs/54-baseline-results.md` — единый файл с тремя разделами: «DCA Momentum», «MTF Scalper», «SMC Liquidity Sweep». Каждый раздел: walk-forward summary + demo smoke summary + visibility flip timestamp. Легче навигировать, чем три отдельных файла.

### Решение 3: DCA Momentum — single-TF, без bundle

`Bot.datasetBundleJson === null` для DCA. Используется legacy single-TF путь из `docs/52-T3` (с уже исправленным interval-фильтром). Это проверяет, что multi-TF infra additive: single-TF стратегия не должна задействовать ни одну строку MTF кода.

### Решение 4: MTF Scalper — стресс-тест на M1

`Bot.timeframe = "M1"`. Polling cadence остаётся существующая (60s или короче, проверить config). M1 — самый быстрый TF в системе; load `loadCandleBundle({ M1, M5, M15 })` каждый tick должен укладываться в polling-cadence. Если профайлинг покажет регресс — fallback: уменьшить `lookbackBars` для M1 до 200 (вместо 500).

### Решение 5: SMC Liquidity Sweep — pattern blocks из patternEngine

Все блоки (`liquidity_sweep`, `fair_value_gap`, `order_block`, `market_structure_shift`) уже supported (`apps/api/src/lib/runtime/patternEngine.ts`). DSL компонуется в T3-T1 через эти блоки + standard compare/and_gate. Никакой новой логики паттернов не вводится.

### Решение 6: Production go/no-go gate — формальный документ, не код

T6 даёт audit-template, проверяющий 9 критериев готовности (security review, ops runbook, observability, demo smoke pass для всех 4, walk-forward pass для всех 4, и тд). Documentation-only, не вводит фичи. Реальное переключение `BYBIT_ALLOW_LIVE` — отдельная задача, которая ссылается на этот документ как на свой prerequisite.

---

## Задачи

### 54-T1: DCA Momentum — DSL + acceptance + publish (single-TF)

**Цель:** довести `dca-momentum` пресет от seed-заглушки (`docs/51-T6`) до `PUBLIC`. Single-TF, без bundle.

**Файлы для изменения:**
- `apps/api/prisma/seed/presets/dca-momentum.json` — финальный DSL.
- `apps/api/tests/fixtures/strategies/dca-momentum.golden.json`.
- `apps/api/scripts/runDcaMomentumBaseline.ts` — orchestration.
- `apps/api/scripts/demoSmoke.dcaMomentum.ts` — обёртка над generic `demoSmoke.ts` из `docs/53-T3`.
- `docs/54-baseline-results.md` — раздел «DCA Momentum».

**Шаги реализации:**
1. **DSL.** Полный preset через примитивы:
   - `enter_when`: `and_gate([ rsi(14, M15) < 30, ema(50, M15) trending up, momentum > 0 ])`. Конкретные блоки — `compare`, `cross`, optional `dca_config` для управления averaging.
   - `dca_config`: 3-5 averaging steps (зависит от concept doc), step distance 1.5%, размер шага возрастающий (martingale-light).
   - `exit_when`: `or_gate([ tp_hit, sl_hit, rsi(14) > 70 ])`.
   - `defaultBotConfigJson`: `{ symbol: "BTCUSDT", timeframe: "M15", quoteAmount: 100, maxOpenPositions: 1, ... }`.
   - **Без** `datasetBundleHintJson` — single-TF.
2. **Walk-forward acceptance.** Те же 6 folds, 4-1 train-test split (см. `docs/53-T2`). DCA-специфика: для acceptance проверять также `averageEntries` (среднее число DCA-step'ов на trade) и `maxDcaDepth` (максимальная глубина) — добавить эти агрегаты в companion-doc, без изменения Walk-Forward UI.
3. **Demo smoke.** 30+ мин на Bybit demo с `BTCUSDT`, M15. Acceptance — те же из `docs/53-T3`: 0 unhandled errors, ≥1 intent (вероятно — несколько за 30 мин при правильной настройке RSI<30 порога).
4. **Publish.** `publishPreset.ts --slug dca-momentum --visibility PUBLIC` после прохождения acceptance.
5. **Companion-doc.** Раздел «DCA Momentum» в `docs/54-baseline-results.md` со всем выше.

**Тест-план:**
- DSL компилируется (golden fixture тест).
- Walk-forward на CI sub-fixture: pipeline работает, `tradeCount > 0`, `dca_config` блок отрабатывает (по логам — DCA step вызвался хотя бы раз).
- Smoke replay (как в `docs/53-T6`) — отдельный fixture для DCA.

**Критерии готовности:**
- `dca-momentum` в PUBLIC, виден в `/lab/library`.
- Walk-forward acceptance pass.
- Demo smoke pass.
- Companion-doc раздел заполнен.

---

### 54-T2: MTF Scalper — DSL + acceptance + publish (3 TF)

**Цель:** довести `mtf-scalper` пресет до `PUBLIC`. Bundle `{M1, M5, M15}`.

**Файлы для изменения:**
- `apps/api/prisma/seed/presets/mtf-scalper.json`.
- `apps/api/tests/fixtures/strategies/mtf-scalper.golden.json`.
- `apps/api/scripts/runMtfScalperBaseline.ts`.
- `apps/api/scripts/demoSmoke.mtfScalper.ts`.
- `docs/54-baseline-results.md` — раздел «MTF Scalper».

**Шаги реализации:**
1. **DSL.**
   - `primaryTimeframe: "M1"`.
   - `datasetBundleHint: { M1: true, M5: true, M15: true }`.
   - `enter_when`: 3-уровневое выравнивание тренда — `and_gate([ ema_fast(9, M1) > ema_slow(21, M1), close(M5) > vwap(M5), ema(50, M15) trending up ])`. Все блоки supported.
   - `exit_when`: `or_gate([ ema_fast crosses below ema_slow on M1, atr-based trailing stop ])`.
   - `defaultBotConfigJson`: `{ symbol: "BTCUSDT", timeframe: "M1", quoteAmount: 50 (меньше из-за частоты), maxOpenPositions: 1, leverage: 5 }`.
2. **Walk-forward acceptance.** Особенности для high-frequency:
   - 6 folds, train 1 месяц / test 1 неделя (потому что M1 даёт ~43K свечей в месяц — больше плотность сигналов, можно укоротить fold).
   - `tradeCount` per fold ожидается высокий (десятки-сотни). Acceptance: `pnl > 0`, `sharpe > 0.5` (выше чем у Adaptive Regime, потому что HFT pattern должен иметь более стабильный edge при честных costs), `maxDD > -25%`.
   - Особое внимание `feeBps` — на M1 fee impact выше; baseline `feeBps: 6, slippageBps: 2`.
3. **Demo smoke.** 30+ мин. Особенности:
   - Polling cadence на M1 — проверить, что текущий polling-loop успевает (если нет — это блокер для MTF Scalper, эскалируется в `docs/50` как новая T-задача).
   - Ожидается заметно большее число intents за 30 мин (десятки), это нормально.
4. **Profile-check.** Перед T4 (publish) запустить профайлер `loadCandleBundle({M1,M5,M15})` per-tick — должно укладываться в <500ms на typical workspace. Если нет — fallback: уменьшить `lookbackBars` для M1 (см. §Решение 4 выше).
5. **Publish.** `--slug mtf-scalper --visibility PUBLIC`.

**Тест-план:**
- Golden DSL компилируется.
- Walk-forward sub-fixture (M1+M5+M15 на 1 неделе) — pipeline работает.
- Smoke replay fixture для MTF Scalper.
- Профайлер benchmark в companion-doc.

**Критерии готовности:**
- `mtf-scalper` в PUBLIC.
- Bundle `{M1, M5, M15}` корректно загружается per-tick без timeout'ов.
- Walk-forward acceptance pass.
- Demo smoke pass.
- Profile-check pass или явный fallback зафиксирован.

---

### 54-T3: SMC Liquidity Sweep — DSL + acceptance + publish (3 TF)

**Цель:** довести `smc-liquidity-sweep` пресет до `PUBLIC`. Bundle `{M15, H1, H4}`.

**Файлы для изменения:**
- `apps/api/prisma/seed/presets/smc-liquidity-sweep.json`.
- `apps/api/tests/fixtures/strategies/smc-liquidity-sweep.golden.json`.
- `apps/api/scripts/runSmcBaseline.ts`.
- `apps/api/scripts/demoSmoke.smc.ts`.
- `docs/54-baseline-results.md` — раздел «SMC Liquidity Sweep».

**Шаги реализации:**
1. **DSL.**
   - `primaryTimeframe: "M15"`.
   - `datasetBundleHint: { M15: true, H1: true, H4: true }`.
   - `enter_when`: типичный SMC сетап — `and_gate([ liquidity_sweep on H1, fair_value_gap on M15, market_structure_shift on M15, htf_bias from H4 (EMA200 trend) ])`. Все блоки supported в `patternEngine.ts`.
   - `exit_when`: `or_gate([ opposite order_block reached on M15, atr-trailing stop, structure invalidation on H1 ])`.
   - `defaultBotConfigJson`: `{ symbol: "BTCUSDT", timeframe: "M15", quoteAmount: 100, maxOpenPositions: 1, leverage: 3 }`.
2. **Walk-forward acceptance.**
   - 6 folds, train 4 месяца / test 1 месяц (как Adaptive Regime).
   - SMC даёт меньше сигналов (более избирательная стратегия). Acceptance: `pnl > 0`, `sharpe > 0.4`, `maxDD > -25%`. Если `tradeCount` на каком-то fold = 0 — это допустимо (фолд может быть в режиме без подходящих структур); но aggregate должен быть с положительным числом trades.
3. **Demo smoke.** 60+ мин (вместо 30) — потому что сигналы реже. Acceptance: 0 unhandled errors, ≥0 intents (signal может не появиться, не обязательно — это особенность SMC). Достаточно подтвердить, что polling-loop вызывает evaluator с bundle и pattern blocks возвращают валидные snapshots.
4. **Pattern engine sanity.** Один отдельный sub-test перед T4: на zashитой fixture (M15+H1+H4 за 2 недели с известным sweep событием) verify, что DSL правильно triggers entry. Это catches случаи, когда patternEngine выдаёт false negative из-за specific bundle alignment edge cases.
5. **Publish.** `--slug smc-liquidity-sweep --visibility PUBLIC`.

**Тест-план:**
- Golden DSL компилируется.
- Walk-forward sub-fixture работает.
- Pattern fixture sanity test (упомянутый выше) зелёный.
- Smoke replay fixture для SMC.

**Критерии готовности:**
- `smc-liquidity-sweep` в PUBLIC.
- Walk-forward acceptance pass.
- Demo smoke 60-мин pass.
- Pattern sanity test passed.

---

### 54-T4: Capability matrix + concept doc updates для всех трёх

**Цель:** обновить capability matrix и concept-доки для всех трёх стратегий — аналогично `docs/53-T5`, но скопом.

**Файлы для изменения:**
- `docs/strategies/08-strategy-capability-matrix.md` — три новые строки (или статусы) `dca-momentum: implemented`, `mtf-scalper: implemented`, `smc-liquidity-sweep: implemented`.
- `docs/strategies/02-dca-momentum-bot.md` — implementation status block.
- `docs/strategies/05-mtf-scalper.md` — то же.
- `docs/strategies/06-smc-liquidity-sweep.md` — то же.
- `docs/16-roadmap.md` — обновить статусы трёх стратегий в Post-MVP секции.
- `docs/strategies/01-flagship-overview.md` — отметить, что 4 не-Funding флагмана delivered (5-я — funding arb — статус из `docs/55`).

**Шаги реализации:**
1. В каждый concept-doc добавить implementation status (как в `docs/53-T5 §2`):
   > **Implementation status:** delivered as `<slug>` preset (`docs/54`). DSL: `apps/api/prisma/seed/presets/<slug>.json`. Golden fixture: `apps/api/tests/fixtures/strategies/<slug>.golden.json`.
2. В matrix — три обновления, формат точно совпадает с тем, что был добавлен в `docs/53-T5`.
3. В roadmap — пункт «5 флагманов» становится «4 delivered, 1 in funding-arb-track (`docs/55`)».
4. `docs/strategies/01-flagship-overview.md` — добавить timeline-block в верх документа: «Stage 3 delivered 2026-04-30 → 5 flagships implementation initiated. As of <date>: Adaptive Regime, DCA Momentum, MTF Scalper, SMC Liquidity Sweep — PUBLIC. Funding Arbitrage — see `docs/55`.»

**Тест-план:**
- Ручная вычитка матрицы.
- Markdown-link-check (если есть в репо).

**Критерии готовности:**
- Capability matrix обновлён для трёх стратегий.
- Implementation status block добавлен в каждый concept doc.
- Roadmap отражает статус.

---

### 54-T5: Тесты — golden DSL + walk-forward CI + smoke replay для каждой стратегии

**Цель:** для каждой из трёх стратегий — тот же набор тестов, что в `docs/53-T6`: golden DSL, walk-forward CI sub-fixture, smoke replay.

**Файлы для изменения:**
- `apps/api/tests/lib/compiler/dcaMomentum.test.ts`.
- `apps/api/tests/lib/compiler/mtfScalper.test.ts`.
- `apps/api/tests/lib/compiler/smcLiquiditySweep.test.ts`.
- `apps/api/tests/integration/dcaMomentumWalkForward.test.ts`.
- `apps/api/tests/integration/mtfScalperWalkForward.test.ts`.
- `apps/api/tests/integration/smcWalkForward.test.ts`.
- `apps/api/tests/integration/dcaMomentumSmokeReplay.test.ts`.
- `apps/api/tests/integration/mtfScalperSmokeReplay.test.ts`.
- `apps/api/tests/integration/smcSmokeReplay.test.ts`.

**Шаги реализации:**
1. Каждый test-файл — копия паттерна из `docs/53-T6`, под конкретный preset.
2. Sub-fixture для walk-forward — компактная (1-2 недели данных), достаточная только для проверки, что pipeline работает; не для полного acceptance (полный — в T1/T2/T3 этого документа).
3. Smoke replay — recorded JSON каждой стратегии, сериализованный после успешного demo smoke run в T1/T2/T3.
4. **Общий helper.** Чтобы не дублировать boilerplate, вынести helpers в `apps/api/tests/_helpers/strategyAcceptance.ts`:
   ```ts
   export function describeGoldenStrategy(slug: string, fixturePath: string) { ... }
   export function describeWalkForwardCi(slug: string, dataPath: string) { ... }
   export function describeSmokeReplay(slug: string, replayPath: string) { ... }
   ```
   Каждый concrete test-файл — 5-10 строк, вызов helper'а.
5. Ретроспективно обновить `docs/53-T6`-тесты на тот же helper (отдельный refactor PR, не блокирует T5).

**Тест-план:**
- `npm test` — все 9 новых тестов зелёные.
- Существующие тесты (`compiler`, `dslEvaluator`, `walkForward`, `botWorker`) — без регрессий.

**Критерии готовности:**
- 9 новых тестов добавлены и зелёные на CI.
- Общий helper в `_helpers/`.
- Smoke replay fixtures созданы.

---

### 54-T6: Production go/no-go gate (audit doc)

**Цель:** документ-аудит `docs/54-go-no-go-gate.md`, по которому принимается осознанное решение о включении live-торговли. Documentation-only, не вводит код.

**Файлы для изменения:**
- `docs/54-go-no-go-gate.md` (создать).

**Шаги реализации:**

Документ содержит 9 разделов-критериев. Решение «GO» возможно только когда все 9 имеют статус PASS (либо явно записанный в gate-документе rationale для каждого пункта, который PASS не получает).

1. **Strategy acceptance.** Все 4 не-Funding флагмана:
   - `walkForwardRunId` валиден и acceptance pass;
   - `demoSmokeRunId` (или ссылка на `.smoke-output/` запись) пройден;
   - golden fixture / DSL / smoke replay тесты зелёные на main.
2. **Security review.** `docs/05-security.md`, `docs/06-threat-model.md` — пересмотрены в течение 30 дней до gate. Аудит-checklist: secrets management, rate limiting, auth, idempotency, input validation на всех новых эндпоинтах из `docs/51`.
3. **Ops runbook.** `docs/15-operations.md` содержит процедуры: «как остановить все боты в emergency», «как откатить preset из PUBLIC в PRIVATE без удаления», «как продиагностировать застрявший bot run».
4. **Observability.** Минимум: дашборд / alerting на (a) число ERRORED ботов за 5/15 минут (alert при skyrocket), (b) p95 latency `/bots/:id/start`, (c) Bybit API error rate, (d) circuit breaker triggered count.
5. **Kill switch.** Глобальный admin-flag для отключения всей торговли (`TRADING_ENABLED=false`) — присутствует и протестирован.
6. **Liability.** Юридический disclaimer в Lab Library и на Bot create UI: «Trading involves risk. Past performance is not indicative of future results.» Текст согласован с product/legal.
7. **Capacity / cost.** Estimate БД-нагрузки и Bybit API rate-limit usage при ожидаемом числе одновременно работающих ботов (X = первый пилотный число пользователей).
8. **Rollback procedure.** Если после go-live обнаружен критический баг — есть план: остановить новых ботов через rate-limit/feature flag, оповестить активных пользователей, hotfix или rollback BYBIT_ALLOW_LIVE.
9. **Sign-off.** Подписи (по именам в companion-doc или git-blame на этом файле): tech lead, product lead, ops lead.

**Структура документа:**
- Заголовок, дата, версия.
- 9 секций как чек-лист с полями `Status: PASS|FAIL|PENDING`, `Evidence: <ссылка>`, `Notes:`.
- Финальное решение: GO / NO-GO / DEFERRED with rationale.

**Тест-план:**
- N/A — документ-аудит, не код.

**Критерии готовности:**
- Файл создан, шаблон заполнен placeholder'ами.
- Секции пронумерованы и каждая имеет Status-поле.
- Документ ссылается на companion-docs (`docs/53-baseline-results.md`, `docs/54-baseline-results.md`).
- В roadmap указано «go/no-go gate template ready, awaiting acceptance for individual flagships».

---

## Порядок выполнения задач

```
54-T1 (DCA) ──┐
              ├──→ 54-T4 (matrix) ──→ 54-T6 (gate doc)
54-T2 (MTF) ──┤                           │
              │       54-T5 (tests) ──────┘
54-T3 (SMC) ──┘
```

- 54-T1, T2, T3 — независимы между собой, могут идти параллельно или последовательно.
- DCA рекомендуется первой как самая простая (нет multi-TF, мало pattern complexity); это даёт быстрый второй success после Adaptive Regime, валидирующий single-TF путь.
- MTF Scalper может стартовать после T1 (нужен опыт `loadCandleBundle` performance).
- SMC может стартовать параллельно с MTF Scalper.
- T4 (capability matrix) выполняется кумулятивно: после каждого из T1/T2/T3 матрица обновляется на одну строку. Финальное закрытие T4 — после всех трёх.
- T5 (тесты) — параллельно с T1-T3, инкрементально.
- T6 (gate doc) — последний. Может писаться черновиком параллельно, но финализация — после прохождения acceptance всеми 4 не-Funding флагманами.

Каждая T-задача — отдельный PR.

## Зависимости от других документов

- `docs/50` — родительский overview.
- `docs/51` — обязателен. T1/T2/T3 публикуют preset'ы через preset system.
- `docs/52` — обязателен для T2 (MTF Scalper) и T3 (SMC). T1 (DCA) — single-TF, не использует.
- `docs/53` — обязателен. Этот документ переиспользует шаблон Adaptive Regime activation. Также `docs/53-T6` helpers (golden DSL test, walk-forward CI sub-fixture, smoke replay) переиспользуются в 54-T5.
- `docs/47` (sweep) — опциональный инструмент для tuning baseline params, если walk-forward acceptance не пройдёт с первого раза.
- `docs/48` (walk-forward) — обязателен для T1/T2/T3.
- `docs/49` (метрики) — обязателен. Acceptance gate проверяет sharpe.
- `docs/55` — независим. Не блокирует, но T6 (go/no-go gate) обновляется после закрытия `docs/55` ещё одной строкой.
- `docs/strategies/02, 05, 06, 08` — concept/matrix.
- `docs/05-security.md`, `docs/06-threat-model.md`, `docs/15-operations.md`, `docs/16-roadmap.md` — обновляются в T4/T6.

## Backward compatibility checklist

- `botWorker.ts`, `signalEngine.ts`, `exitEngine.ts`, `positionManager.ts`, `dcaEngine.ts`, `patternEngine.ts` — без правок. Все три стратегии реализуются конфигурацией DSL.
- `bybitOrder.ts` — без правок.
- Никаких новых composite signal types в evaluator.
- Никаких новых Prisma миграций (StrategyPreset, datasetBundleJson, templateSlug — уже введены `docs/51`/`docs/52`).
- Никаких изменений в `routes/demo.ts`.
- Public Lab Library поддерживает добавление новых PUBLIC карточек без правок UI.
- DCA single-TF путь использует legacy single-TF candle loading (с уже исправленным interval-фильтром из `docs/52-T3`).
- Existing single-TF backtest (`runBacktest(candles, dsl, opts)`) продолжает работать для DCA-сценариев без перехода на bundle-overload.
- T6 — documentation-only, никаких бинарных артефактов.

## Ожидаемый результат

После закрытия 54-T1..54-T6:

- В Lab Library живут 4 PUBLIC карточки: `adaptive-regime` (`docs/53`), `dca-momentum`, `mtf-scalper`, `smc-liquidity-sweep`.
- Каждая стратегия имеет: golden DSL fixture, walk-forward acceptance результат, demo smoke audit, capability matrix entry, smoke replay test в CI.
- `docs/54-baseline-results.md` — companion-doc с тремя разделами, фиксирующими реальные числа per стратегия.
- `docs/54-go-no-go-gate.md` — формальный template для production go-live решения; готов к заполнению по мере прохождения acceptance.
- Spec'и `docs/strategies/02, 05, 06` — содержат implementation status, ссылающийся на этот документ.
- Roadmap отражает: 4 не-Funding флагмана delivered. Funding Arb — в `docs/55` (параллельный трек).
- DSL evaluator, signal/exit/position engine, dcaEngine, patternEngine, botWorker — не модифицированы; все правки на уровне DSL configurations + acceptance pipeline.
- Это ставит платформу в состояние, в котором go-live решение зависит только от прохождения T6 gate-документа, а не от инженерных блокеров.
