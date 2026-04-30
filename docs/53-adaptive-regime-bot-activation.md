# 53. Adaptive Regime Bot — End-to-End Activation

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Связанный спек: `docs/strategies/03-adaptive-regime-bot.md`

## Контекст

Текущее состояние (проверено по коду):

- Concept-документ стратегии — `docs/strategies/03-adaptive-regime-bot.md`. Идея: на M5 entry под управлением SuperTrend, фильтр по тренду на H1 (EMA200 + ADX), Bollinger reversion как контр-сигнал в режиме flat.
- В нём упомянуты «composite signal types»: `"supertrend_direction"`, `"bb_rsi_reversion"`, `"supertrend_flip_or_bb_midline"`. В DSL evaluator таких отдельных типов **нет** — это синтетические high-level имена в исходной спецификации (см. `docs/50 §Решение 3`).
- В `apps/api/src/lib/compiler/supportMap.ts` все необходимые блоки supported: `supertrend`, `ema`, `adx`, `bollinger_bands`, `compare`, `cross`, `and_gate`, `or_gate`, `enter_when`, `exit_when`. Capability matrix — `docs/strategies/08-strategy-capability-matrix.md`.
- Pre-existing seed для `adaptive-regime` пресета — заглушка из `docs/51-T6` (минимальный валидный DSL); финальный DSL фиксируется в этом документе.
- Multi-TF runtime/backtest — обеспечивается `docs/52`. Bundle `{M5, H1}`.
- Walk-forward — `docs/48`, инструмент готов.
- Demo smoke harness — отсутствует. Никаких автоматизированных «запустить бот на Bybit demo на N минут» сценариев сейчас нет; есть только unit + integration.
- Bybit demo execution — работает через существующий `bybitOrder.ts` с `BYBIT_USE_DEMO=true` env; `category: "linear"`. Spot не требуется.

## Цель

Довести `adaptive-regime` пресет до состояния `PUBLIC` в Lab Library — первая end-to-end активация флагмана. Конкретно:

1. Финальный, валидный DSL для `adaptive-regime`, целиком составленный из 33 supported блоков. Никаких composite signal types; никакого расширения evaluator.
2. Golden walk-forward acceptance: на 6+ folds показывает `pnl > 0`, `sharpe > 0.3`, `maxDrawdown > -25%` (acceptance gate из `docs/50 §A5`).
3. Demo smoke: бот, созданный через `POST /presets/adaptive-regime/instantiate`, работает на Bybit demo 30+ минут без unhandled runtime errors; intents идут до demo endpoint'ов.
4. После прохождения 1-3 — admin переводит preset из `PRIVATE` в `PUBLIC` и он появляется в `/lab/library`.
5. Capability matrix и concept doc обновлены: композитные имена сигналов помечены как «реализовано через примитивы DSL»; в matrix добавлена строка `adaptive-regime: implemented`.

После закрытия 53 у нас есть **рабочий первый флагман в галерее** — это валидация всего стека (preset + bundle + acceptance + go/no-go gate).

## Не входит в задачу

- **Live trading.** Demo only. Перевод `BYBIT_ALLOW_LIVE` для пользователя — отдельный gate-doc (`docs/50 T10 в docs/54`), не часть этого документа.
- **Параметр-tuning через AI.** Параметры SuperTrend/EMA/ADX в DSL фиксируются как baseline; further optimization через Lab → Optimise (на основе `docs/47`) — отдельные эксперименты пользователя.
- **Multi-symbol Adaptive Regime.** Один бот = один symbol (по умолчанию `BTCUSDT`). Раскат на ETH/SOL — после go/no-go gate, отдельным шагом.
- **Перепроектирование SuperTrend / Bollinger индикаторов.** Используем существующие реализации `apps/api/src/lib/indicators/`.
- **Изменения runtime safety / error classifier'а.** Существующий `safety/*` slice достаточен.
- **Live order routing changes.** Никаких правок `bybitOrder.ts`.
- **Реальные финансовые гарантии.** Acceptance — статистическое условие. «Стратегия может работать в demo» ≠ «стратегия принесёт прибыль на live».

## Архитектурные решения

### Решение 1: DSL целиком через примитивы

Каждый высокоуровневый «сигнал» из concept doc развёртывается:

- `supertrend_direction(M5)` → `{ "indicator": "supertrend", "params": {...}, "sourceTimeframe": "M5", "field": "direction" }`. Comparison: `compare(direction, "==", 1)`.
- `bb_rsi_reversion` → `and_gate([ compare(close, "<", bb.lower), compare(rsi(14), "<", 30) ])`.
- `supertrend_flip_or_bb_midline` → `or_gate([ cross(supertrend.direction, "flip"), cross(close, "==", bb.middle) ])`.

Семантика flip: используем существующий `cross`-блок с режимом `direction_change` (если такой supported; иначе явный `compare(direction[t], "!=", direction[t-1])` через `prev` accessor — проверить в `supportMap.ts`).

Все эти конструкции — комбинации supported блоков. Никаких новых типов в evaluator.

### Решение 2: Bundle `{M5, H1}`, primary M5

`Bot.timeframe = "M5"` (entry/exit); `datasetBundleJson = { M5: ..., H1: ... }` (см. `docs/52`). Все DSL-блоки с `sourceTimeframe="H1"` работают на H1-стороне bundle; основная итерация — по M5.

### Решение 3: Acceptance gate — golden DSL + walk-forward + demo smoke

Тройка условий из `docs/50 §A5`. Каждое — отдельная T-задача (T1, T2, T3). Только когда все три зелёные, T4 переводит preset в `PUBLIC`. Это явный, проверяемый barrier; ни одно из условий не может быть проигнорировано.

### Решение 4: Demo smoke — отдельный harness, не unit-тест

Demo smoke — это не тест в классическом смысле (не блокирует CI). Это harness-скрипт `apps/api/scripts/demoSmoke.ts`, который запускает реальный `Bot` на Bybit demo через стандартный flow (POST `/presets/.../instantiate` → POST `/bots/:id/start`), мониторит intent-flow в БД и unhandled errors в логах. По истечении интервала (default 30 минут) выдаёт отчёт. Ручной запуск перед T4. Опционально — настраивается под cron/cloud для regression tracking; это out-of-scope текущего документа.

---

## Задачи

### 53-T1: Финальный DSL `adaptive-regime` через примитивы (golden fixture)

**Цель:** заменить заглушку из `docs/51-T6` на финальный DSL `adaptive-regime` через 33 supported блока. Зафиксировать как golden fixture для тестов.

**Файлы для изменения:**
- `apps/api/prisma/seed/presets/adaptive-regime.json` — финальный DSL.
- `apps/api/tests/fixtures/strategies/adaptive-regime.golden.json` (создать) — копия для тестов.
- `apps/api/tests/lib/compiler/adaptiveRegime.test.ts` (создать) — DSL компилируется, нет unsupported блоков.

**Шаги реализации:**
1. Раскрыть три композитных сигнала из concept doc через примитивы (см. §Решение 1). Итог — структура примерно:
   ```jsonc
   {
     "version": "v2",
     "primaryTimeframe": "M5",
     "datasetBundleHint": { "M5": true, "H1": true },
     "enter_when": {
       "or_gate": [
         {
           "and_gate": [
             { "compare": { "left": { "indicator": "supertrend", "params": {"period": 10, "multiplier": 3.0}, "sourceTimeframe": "M5", "field": "direction" }, "op": "==", "right": 1 } },
             { "compare": { "left": { "candle": "close" }, "op": ">", "right": { "indicator": "ema", "params": {"period": 200}, "sourceTimeframe": "H1" } } },
             { "compare": { "left": { "indicator": "adx", "params": {"period": 14}, "sourceTimeframe": "H1" }, "op": ">", "right": 20 } }
           ]
         },
         {
           "and_gate": [
             { "compare": { "left": { "candle": "close" }, "op": "<", "right": { "indicator": "bollinger_bands", "params": {"period": 20, "stdDev": 2}, "sourceTimeframe": "M5", "field": "lower" } } },
             { "compare": { "left": { "indicator": "rsi", "params": {"period": 14}, "sourceTimeframe": "M5" }, "op": "<", "right": 30 } },
             { "compare": { "left": { "indicator": "adx", "params": {"period": 14}, "sourceTimeframe": "H1" }, "op": "<", "right": 20 } }
           ]
         }
       ]
     },
     "exit_when": {
       "or_gate": [
         { "compare": { "left": { "indicator": "supertrend", "params": {"period": 10, "multiplier": 3.0}, "sourceTimeframe": "M5", "field": "direction" }, "op": "==", "right": -1 } },
         { "cross": { "left": { "candle": "close" }, "op": "above", "right": { "indicator": "bollinger_bands", "params": {"period": 20, "stdDev": 2}, "sourceTimeframe": "M5", "field": "middle" } } }
       ]
     },
     "stopLoss": { "type": "atr", "atrPeriod": 14, "multiplier": 2.0 },
     "takeProfit": { "type": "rr", "ratio": 2.0 }
   }
   ```
   Конкретные значения параметров — baseline из concept doc; могут варьироваться, golden fixture фиксирует именно эту версию.
2. Все блоки и поля проверяются `compileDsl` в тесте; если evaluator не поддерживает какое-то из обращений (например, `bollinger_bands.field=middle`) — это блокер, открывается follow-up T-задача на расширение конкретного блока (не на введение composite signal type).
3. `defaultBotConfigJson` в seed-файле:
   ```json
   {
     "symbol": "BTCUSDT",
     "timeframe": "M5",
     "quoteAmount": 100,
     "maxOpenPositions": 1,
     "leverage": 3
   }
   ```
4. Golden fixture (`tests/fixtures/.../golden.json`) — точная копия dslJson из seed-файла, импортируется тестами compiler / evaluator / backtest. При любом изменении DSL — golden обновляется явным diff'ом в PR.

**Тест-план:**
- `compileDsl(adaptiveRegime.golden.json)` → ok, нет ошибок.
- `evaluateDsl` на синтетической M5+H1 фикстуре с заведомо trend-up условиями → возвращает entry signal на ожидаемом баре.
- `evaluateDsl` на flat фикстуре с touch lower BB + rsi<30 → возвращает entry signal по второй ветке.
- `evaluateDsl` на flat без оверсолда → нет signal.

**Критерии готовности:**
- DSL компилируется.
- Никаких composite signal types — все блоки находятся в `supportMap.ts` со статусом `supported`.
- Golden fixture зафиксирована, тесты её используют.

---

### 53-T2: Backtest baseline + walk-forward acceptance run

**Цель:** прогнать DSL из 53-T1 через backtest на реальных данных + walk-forward. Зафиксировать baseline-метрики и acceptance result.

**Файлы для изменения:**
- `apps/api/scripts/runAdaptiveRegimeBaseline.ts` (создать) — orchestration script.
- `apps/api/tests/fixtures/datasets/adaptive-regime/M5.json`, `H1.json` (создать или ссылка на seeded MarketDataset).
- `apps/api/prisma/seed/datasets/adaptive-regime-fixture.ts` (создать) — seed M5+H1 свечей для воспроизводимого backtest.
- `docs/53-baseline-results.md` (создать как companion) — фиксация конкретных чисел.

**Шаги реализации:**
1. **Dataset fixture.** Не зависим от Bybit live history: используем зашитые JSON-файлы со свечами (минимум 6 месяцев M5 = ~52K свечей; H1 = ~4.3K). Источник — экспорт из существующего `MarketDataset` либо детерминированный generator (для unit-тестов; для baseline — реальные данные через одноразовый sync).
2. **Baseline backtest.**
   - `loadCandleBundle({ bundle: { M5: <id>, H1: <id> }, mode: "backtest" })`.
   - `runBacktest({ bundle, primaryInterval: "M5", dsl: golden, opts: { feeBps: 6, slippageBps: 1, fillAt: "NEXT_OPEN" } })`.
   - Зафиксировать: `tradeCount`, `winRate`, `pnlPct`, `sharpe`, `profitFactor`, `expectancy`, `maxDrawdownPct` в companion-doc.
3. **Walk-forward.**
   - Использовать существующий `walkForward/run.ts` (`docs/48`).
   - Split: 6 folds, train 4 месяца / test 1 месяц, expanding window.
   - Acceptance критерии (`docs/50 §A5`):
     - На каждом fold: `pnlPct > 0`.
     - Aggregated `sharpe > 0.3`.
     - Aggregated `maxDrawdownPct > -25%` (то есть DD не глубже 25%).
   - Если хотя бы один критерий не выполнен — T2 не закрыт. Варианты: tune baseline params (вручную через Lab → Optimise) и переделать walk-forward; или зафиксировать gap и эскалировать в `docs/50` (возможно, спека стратегии слишком оптимистична). Документ `docs/53-baseline-results.md` фиксирует и положительные, и отрицательные результаты.
4. Скрипт идемпотентен: можно перезапускать, результаты пишутся в companion-doc с timestamp.

**Тест-план:**
- Запуск скрипта → отчёт сгенерирован в companion-doc.
- Walk-forward все folds зелёные → acceptance pass.
- Любой fold красный → acceptance fail, документировано в companion-doc, T2 не закрыт.

**Критерии готовности:**
- Baseline metrics зафиксированы в `docs/53-baseline-results.md`.
- Walk-forward acceptance pass подтверждён (или иначе явно эскалирован).
- Walk-forward результат сохранён в `WalkForwardRun` записи; `walkForwardRunId` упомянут в companion-doc.
- Никаких изменений в производственной БД — все данные на тестовом workspace.

---

### 53-T3: Demo smoke harness — 30-минутный прогон на Bybit demo

**Цель:** скрипт `demoSmoke.ts`, запускающий Adaptive Regime бот на Bybit demo, мониторящий поток intent'ов и unhandled errors в течение 30+ минут.

**Файлы для изменения:**
- `apps/api/scripts/demoSmoke.ts` (создать) — generic harness, параметризуется `presetSlug`.
- `apps/api/scripts/demoSmoke.adaptiveRegime.ts` (создать) — тонкая обёртка с `presetSlug="adaptive-regime"`.
- `docs/53-baseline-results.md` — добавить раздел «Demo smoke run».

**Шаги реализации:**
1. Параметры (env / args):
   - `BYBIT_USE_DEMO=true` — обязательно.
   - `BYBIT_API_KEY_DEMO`, `BYBIT_API_SECRET_DEMO` — берутся из существующего `ExchangeConnection` записи workspace'а (script использует тот же loader, что runtime).
   - `--duration-min` (default 30).
   - `--symbol` (default `BTCUSDT`).
2. Алгоритм:
   1. POST `/presets/adaptive-regime/instantiate` с `{ workspaceId, overrides: { symbol, quoteAmount: 50 /* минимум для demo */ } }`.
   2. POST `/bots/:id/start`.
   3. Запуск polling-loop в скрипте: каждые 60s читать `BotIntent` count, `BotRunState`, последние ошибки из существующего error-log таблицы (`BotError` или эквивалент в текущем коде — проверить).
   4. По истечении `duration-min`: POST `/bots/:id/stop`. Финальный отчёт.
3. Acceptance условия для T3:
   - `BotRunState` за весь период != `ERRORED`.
   - Хотя бы 1 `BotIntent` сгенерирован (это не требование к торговому результату — это проверка, что polling реально вызывает evaluator). Если 0 интентов за 30 минут — это red flag по DSL (либо рынок строго flat без сигналов, либо баг). Помечается warning, не failure; принимается решение запустить ещё раз / увеличить duration.
   - 0 unhandled errors в logs.
   - Bybit demo endpoints отвечают 200 OK (нет 401/403/429 sustained).
4. Отчёт пишется в companion-doc + полная копия логов (за минусом секретов) сохраняется в `apps/api/scripts/.smoke-output/<timestamp>.log`. `.smoke-output/` добавляется в `.gitignore`.
5. Запуск — ручной, перед T4. Не часть CI.

**Тест-план:**
- Скрипт запускается локально / на staging-сервере с настроенными demo credentials.
- Через 30+ минут отчёт сохранён, acceptance условия проверены.
- Если acceptance не выполнено — T3 не закрыт, разбираем root cause; не «закрываем глаза».

**Критерии готовности:**
- Скрипт работает, отчёт за один полный run сохранён.
- В companion-doc раздел «Demo smoke run» содержит дату, длительность, intent count, ссылка на лог-файл (или его статус-summary).
- В логах нет unhandled errors / Bybit auth issues.
- Решение «proceed to T4» зафиксировано подписью владельца документа в companion-doc.

---

### 53-T4: Visibility flip: PRIVATE → PUBLIC + публикация в Lab Library

**Цель:** перевод preset из `PRIVATE` в `PUBLIC` после прохождения T1+T2+T3. Появление карточки в `/lab/library`.

**Файлы для изменения:**
- `apps/api/scripts/publishPreset.ts` (создать) — admin-only утилита, обновляющая `visibility`.
- `docs/53-baseline-results.md` — раздел «Visibility flip».

**Шаги реализации:**
1. Скрипт принимает аргументы `--slug adaptive-regime --visibility PUBLIC`. Проверки внутри:
   - Существует preset с таким slug.
   - В companion-doc `docs/53-baseline-results.md` указано "Acceptance: PASS" (через простой grep по конкретной строке-маркеру). Это охранник от случайной публикации без acceptance. Если маркера нет — скрипт просит явный `--force` и логирует warning.
   - Запись в audit-log (существующая `AuditLog` таблица или просто `console.log` + persistent file `apps/api/.publish-audit.log`).
2. После update: открыть `/lab/library` (вручную), убедиться, что карточка появилась.
3. Никакой автоматизации публикации в CI — это сознательно ручной шаг с проверкой.
4. Откат: `--visibility PRIVATE` через тот же скрипт. Это восстанавливает PRIVATE без удаления preset'а / связанных ботов.

**Тест-план:**
- Запуск без acceptance-маркера → warning, требуется `--force`.
- Запуск с маркером → preset переведён в `PUBLIC`.
- `GET /presets` без auth → возвращает `adaptive-regime`.
- `GET /lab/library` в браузере → карточка видна.
- Откат `--visibility PRIVATE` → карточка исчезает.

**Критерии готовности:**
- `adaptive-regime` в `PUBLIC`, виден в Lab Library.
- В audit-log запись с timestamp и admin-ID.
- В companion-doc раздел «Visibility flip» с timestamp.

---

### 53-T5: Capability matrix update + concept doc cross-link

**Цель:** обновить capability matrix (`docs/strategies/08-strategy-capability-matrix.md`) и concept doc (`docs/strategies/03-adaptive-regime-bot.md`).

**Файлы для изменения:**
- `docs/strategies/08-strategy-capability-matrix.md` — добавить строку `adaptive-regime: implemented` (или эквивалент для текущего формата матрицы).
- `docs/strategies/03-adaptive-regime-bot.md` — добавить раздел «Реализация», ссылающийся на этот документ + golden fixture; явно отметить, что composite signal types из исходного спека развёрнуты через примитивы.
- `docs/16-roadmap.md` — отметить Adaptive Regime как `delivered` в Post-MVP секции.

**Шаги реализации:**
1. Открыть текущую матрицу, понять формат (строки = стратегии, колонки = блоки / индикаторы / статус). Найти строку для Adaptive Regime, проставить статус `implemented` или эквивалент. Если строки нет — добавить.
2. В `03-adaptive-regime-bot.md` в начале документа после headline добавить блок:
   > **Implementation status:** delivered as `adaptive-regime` preset (`docs/53`). DSL: `apps/api/prisma/seed/presets/adaptive-regime.json`. Golden fixture: `apps/api/tests/fixtures/strategies/adaptive-regime.golden.json`. Composite signal types из исходной спеки развёрнуты через примитивы DSL — см. `docs/53 §Решение 1`.
3. В `docs/16-roadmap.md` — обновить статус первого флагмана. Без подробных правок остальных пунктов.
4. **Никаких** изменений в `docs/strategies/01-flagship-overview.md` сверх ссылок на эти доки.

**Тест-план:**
- Ручная вычитка: matrix корректна, ссылки кликабельны.
- Никаких сломанных линков (запустить markdown-link-check, если он есть в репо).

**Критерии готовности:**
- Capability matrix обновлена.
- Concept doc содержит implementation status.
- Roadmap отражает delivered-статус.

---

### 53-T6: Тесты — golden DSL fixture + walk-forward acceptance + smoke replay

**Цель:** покрыть тестами: golden DSL (компиляция + sanity evaluator), walk-forward acceptance в CI на маленькой sub-fixture, smoke replay на recorded data.

**Файлы для изменения:**
- `apps/api/tests/lib/compiler/adaptiveRegime.test.ts` — компиляция DSL (создан в T1).
- `apps/api/tests/integration/adaptiveRegimeWalkForward.test.ts` (создать).
- `apps/api/tests/integration/adaptiveRegimeSmokeReplay.test.ts` (создать).

**Шаги реализации:**
1. **Golden DSL.** Загрузить `tests/fixtures/strategies/adaptive-regime.golden.json` через `compileDsl`. Любая регрессия в supportMap или DSL-форме → красный тест.
2. **Walk-forward CI test.**
   - Используется компактная sub-fixture (~2 месяца M5 + H1 свечей, hardcoded), не полные 6 месяцев из 53-T2.
   - Запустить walk-forward через те же helpers, что в production code.
   - Acceptance критерии **смягчены** для CI: `tradeCount > 0 на каждом fold`, `aggregated pnlPct != null`. То есть проверяем только что pipeline работает, не что результат соответствует «production-grade» acceptance. Полный acceptance — на full data, в T2 (вне CI).
3. **Smoke replay.**
   - Recorded data: один полный demo-smoke run сериализован в JSON (intent log, candle snapshots, evaluator outputs). Помещается в `tests/fixtures/.../smokeReplay.json`.
   - Тест проигрывает intent flow через mocked `bybitOrder` (никаких real HTTP) и проверяет, что evaluator производит те же intents, что были в реальном run.
   - Это regression test: если позже DSL или evaluator изменится — replay упадёт, надо явно обновить fixture.
4. Все тесты — детерминированы, без рандома, без current time зависимостей.

**Тест-план:**
- `npm test` (apps/api) — все три новых теста зелёные.
- Существующие тесты (`compiler`, `dslEvaluator`, `walkForward`, `botWorker`) — без регрессий.
- Покрытие новых файлов ≥ 80%.

**Критерии готовности:**
- Все три теста добавлены и зелёные на CI.
- Golden fixture явно используется как single source of truth.
- Smoke replay fixture помечена с timestamp оригинального run'а в комментарии.

---

## Порядок выполнения задач

```
53-T1 ──→ 53-T2 ──→ 53-T3 ──→ 53-T4 ──→ 53-T5
   │
   └────────────────────────────────────→ 53-T6
```

- 53-T1 (DSL) — первая, всё опирается на golden fixture.
- 53-T2 (walk-forward acceptance) — после T1.
- 53-T3 (demo smoke) — после T2 (нет смысла гонять demo, если walk-forward провалился).
- 53-T4 (publish) — только после T1+T2+T3 успеха. Это явный gate.
- 53-T5 (matrix/concept doc) — после T4.
- 53-T6 (тесты) — может вестись параллельно с T1-T5 инкрементально; финализируется после T1.

Каждая T-задача — отдельный PR. T2 и T3 могут произвести negative result — тогда документ ставится на паузу до решения «tune params» / «эскалировать в `docs/50`».

## Зависимости от других документов

- `docs/50` — родительский overview.
- `docs/51` — обязателен. Без preset-системы T4 («publish to Library») невозможен. T1 заменяет seed-заглушку из `docs/51-T6`.
- `docs/52` — обязателен. Bundle `{M5, H1}` — фундамент multi-TF DSL.
- `docs/47` (sweep) — может использоваться для tuning baseline params, если первый walk-forward run не пройдёт acceptance.
- `docs/48` (walk-forward) — обязателен для T2.
- `docs/49` (sharpe/PF/expectancy метрики) — обязателен для acceptance gate (T2 проверяет sharpe).
- `docs/strategies/03-adaptive-regime-bot.md` — concept-doc, обновляется в T5.
- `docs/strategies/08-strategy-capability-matrix.md` — capability matrix, обновляется в T5.

## Backward compatibility checklist

- Никаких изменений в `botWorker.ts`, `signalEngine.ts`, `exitEngine.ts`, `positionManager.ts` сверх того, что уже введено в `docs/52` и `docs/51`. Activation Adaptive Regime — чисто конфигурация (DSL + bundle), не правка ядра.
- `bybitOrder.ts` — без правок. Demo smoke использует тот же путь, что обычный bot run.
- Composite signal types из исходного спека НЕ вводятся в evaluator. Любая попытка добавить `"supertrend_direction"` как отдельный type — нарушение `docs/50 §Решение 3` и должна быть отклонена в код-ревью.
- Никаких изменений в Prisma schema (`StrategyPreset`, `Bot`, `BacktestSweep`, `WalkForwardRun` уже расширены в `docs/51`/`docs/52`).
- Existing public Lab Library страница (`docs/51-T5`) поддерживает добавление новой PUBLIC карточки без правок UI.
- `routes/demo.ts` (hardcoded breakout-presets для лендинга) — не затронут.

## Ожидаемый результат

После закрытия 53-T1..53-T6:

- В Lab Library живёт PUBLIC карточка `adaptive-regime`. Один клик → бот на Bybit demo.
- Существует golden DSL fixture, gating CI: любая регрессия в DSL evaluator или supportMap, ломающая стратегию, ловится на CI.
- Walk-forward acceptance (полный, на 6 folds) пройден на baseline parameters; результат зафиксирован в `docs/53-baseline-results.md`.
- Demo smoke 30+ минут отработан без unhandled errors; intent flow подтверждён.
- Capability matrix отражает delivered-статус. Concept doc указывает реализационные ссылки.
- Архитектурно — это первая end-to-end активация, валидирующая работоспособность всего стека `docs/51 + docs/52 + docs/47/48/49` под реальную стратегию. Эта же шаблонная последовательность T1..T6 переиспользуется в `docs/54` для DCA / MTF Scalper / SMC.
