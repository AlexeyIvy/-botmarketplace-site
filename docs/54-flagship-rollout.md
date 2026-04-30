# 54. Flagship Rollout — DCA, MTF Scalper, SMC

Статус: draft  
Владелец: core trading  
Последнее обновление: 2026-04-30  
Родительский документ: `docs/50-flagship-activation-plan.md`  
Зависит от: `docs/51`, `docs/52`, `docs/53`

## Контекст

`docs/53` обкатывает пайплайн (preset → walk-forward gate → demo smoke → publish) на одной стратегии (Adaptive Regime). `docs/54` повторяет ровно тот же пайплайн на оставшихся четырёх флагманах из `docs/strategies/01-flagship-overview.md`:

- **DCA Momentum** (`docs/strategies/06-dca-momentum-bot.md`).
- **MTF Confluence Scalper** (`docs/strategies/05-mtf-confluence-scalper.md`).
- **SMC Liquidity Sweep + FVG + Order Block** (`docs/strategies/02-smc-liquidity-sweep.md`).
- (Funding Arbitrage — отдельный трек, `docs/55`.)

Все нужные DSL-блоки уже supported (capability matrix `docs/strategies/08-strategy-capability-matrix.md`):
- `dca_config` (#132/#133) — для DCA.
- `vwap` (#125/#126), `volume_profile` (#135) — для MTF Scalper.
- `liquidity_sweep`, `fair_value_gap` (#137/#138), pattern engine — для SMC.

## Цель

Опубликовать ≥ 4 пресетов в галерею (вместе с Adaptive из `docs/53` — 5 флагманов в total). Каждый проходит acceptance gate из `docs/50 §A5`. Ноль расширений evaluator-а — только использование уже supported блоков.

## Не входит

- Funding Arbitrage — `docs/55`.
- Multi-symbol presets — каждый пресет фиксируется на одном символе (BTCUSDT по умолчанию; пользователь меняет после instantiate).
- Optimizer-driven параметры — стартуем с параметров spec'а; sweep — follow-up.
- Real-time push сигналов в Telegram/Discord — отдельная инфра.

## Архитектурные решения

### A1. Единый шаблон активации

Каждая из трёх стратегий проходит точно тот же набор шагов:
1. Golden DSL fixture.
2. Walk-forward acceptance.
3. Seed `StrategyPreset` (visibility=PRIVATE).
4. Demo smoke (30 мин).
5. Flip visibility=PUBLIC + matrix.

Эти шаги повторяют `docs/53-T1`..`docs/53-T5` буква в букву, отличаются только DSL-фикстурой и target-параметрами acceptance. Это значит: общий объём работ = 3 стратегии × 5 шагов = 15 атомарных задач, каждая мала.

### A2. Acceptance thresholds per spec

Из spec'ов (`docs/strategies/0X-...`):

| Стратегия | Walk-forward gate | Notes |
|---|---|---|
| DCA Momentum | `pnlPct > 5%`/year, `maxDrawdownPct > -15%`, `sharpe > 1.0` | DCA даёт стабильный, но скромный profile |
| MTF Scalper | `pnlPct > 0`, `sharpe > 1.5`, `winRate > 60%`, `maxDrawdownPct > -15%` | spec обещает sharpe 4.6+, ставим консервативный gate |
| SMC | `pnlPct > 0`, `sharpe > 0.5`, `winRate ≥ 35%` (R:R 1:3), `maxDrawdownPct > -30%` | low win-rate, R:R-driven |

Если стратегия не проходит — не публикуется (PRIVATE), фиксируется в release-checklist'е причиной.

### A3. Multi-TF dependencies

- **DCA Momentum** — single-TF (M15 или H1 по spec'у). `datasetBundleJson` не требуется.
- **MTF Scalper** — primary M1 + context M15/H1. Требует `docs/52` (полностью).
- **SMC** — primary M5 + context H1 (структура). Требует `docs/52`.

`MTF Scalper` использует M1 primary, что **не** входит в `Timeframe` enum проблема: `Timeframe` уже содержит M1 (`apps/api/prisma/schema.prisma:90`). Ok.

---

## Задачи

### 54-T1: DCA Momentum activation

**Стратегия:** Long-only / Short-only DCA с базовым ордером + 12 safety-orders, момент-фильтр RSI(14)<40 и close<EMA(21).

**Подзадачи (5 шагов из A1):**

#### 54-T1.1 Golden fixture
- `apps/api/tests/fixtures/strategies/dca-momentum-btc-15m.json` — DSL с `dca_config` блоком (params: `safetyOrderCount=12, stepPct=1.2, takeProfitPct=2.5, baseOrderUsdt=100`).
- Entry: `compare(rsi14, "<", 40)` AND `compare(close, "<", ema21)`.
- Exit: TP при цене `avgEntry * (1 + tpPct)` (вычисляется внутри `dca_config`).
- Synthetic candles: даунтренд → BO + 3 SO + price recovery → exit. Trade-log content: 1 закрытая сделка, avg-price пересчитан.

#### 54-T1.2 Walk-forward
- Dataset: BTCUSDT M15, 12 мес.
- `foldConfig: { isBars: 12000, oosBars: 3000, step: 3000 }`.
- Threshold из A2.
- Запись в `release-checklist.md`.

#### 54-T1.3 Seed preset (PRIVATE)
- `slug: "dca-momentum-btc-15m"`, `category: "dca"`, `timeframe: M15`.
- DSL из 54-T1.1.
- `defaultDatasetBundleJson: null` (single-TF).

#### 54-T1.4 Demo smoke
- 30+ мин в DEMO. DCA-специфика: убедиться, что safety-order ladder создаётся корректно (positionManager логирует ladder-orders).

#### 54-T1.5 Publish + matrix
- `PATCH visibility=PUBLIC`. Matrix row.

**DoD:** preset публичен, тест зелёный, release-checklist row pass.

---

### 54-T2: MTF Confluence Scalper activation

**Стратегия:** Long при `close > vwap_session` AND `near(close, poc, ±0.15%)` AND `rsi(3) < 30`. Short — симметрично с `> 70` и `vwap below`.

**Подзадачи:**

#### 54-T2.1 Golden fixture
- `apps/api/tests/fixtures/strategies/mtf-scalper-btc-1m.json`.
- Indicators: `vwap_session`, `volume_profile.poc/vah/val`, `rsi(3)`.
- DSL: `and_gate(compare(close, ">", vwap), near(close, vp.poc, 0.0015), compare(rsi3, "<", 30))`.
- `near(a, b, tol)` представляется как `compare(abs(a-b)/b, "<", tol)` через существующие compose-операции (если `near` нет в supported list — собираем из `subtract`+`abs`+`divide`+`compare`; проверить в matrix).
- Synthetic candles M1 + M15 + H1 (последние два через bundle): создать сегмент, где все три условия совпадают.
- Trade-log: 2 сделки long + 2 сделки short.

#### 54-T2.2 Walk-forward
- Datasets: BTCUSDT M1 (3 мес — высокая частота, маленькое окно достаточно), M15 (3 мес), H1 (3 мес).
- `datasetBundleJson: { M1, M15, H1 }`.
- Threshold из A2 — sharpe gate жёсткий, чтобы не пропустить переоценённую стратегию.

#### 54-T2.3 Seed preset
- `slug: "mtf-scalper-btc-1m"`, `category: "scalping"`, `timeframe: M1`.
- `defaultDatasetBundleJson: { "M1": true, "M15": true, "H1": true }`.

#### 54-T2.4 Demo smoke
- M1 — высокая частота. 30 минут DEMO; ожидать ≥ 1 сделки. Если 30 мин недостаточно — расширить до 60 (документировать в checklist'е).
- Particular check: latency `botWorker` цикла под MTF. После `docs/52-T3` profile показывает, что добавление двух context-TF добавляет ≤ 50ms на тик.

#### 54-T2.5 Publish + matrix.

**DoD:** preset публичен, latency MTF подтверждён, release-checklist row pass.

---

### 54-T3: SMC Liquidity Sweep activation

**Стратегия:** Long при `liquidity_sweep(direction="below", reference="PDL")` AND `fair_value_gap(direction="up")` AND `compare(close, ">", orderBlock.high)`. Short симметрично.

**Подзадачи:**

#### 54-T3.1 Golden fixture
- `apps/api/tests/fixtures/strategies/smc-btc-5m.json`.
- Indicators / pattern blocks: `liquidity_sweep`, `fair_value_gap`, `orderBlock` (см. matrix; если `orderBlock` существует только как `liquidity_sweep` extension — проверить и использовать). Использовать `previousDayLow` / `previousDayHigh` indicators.
- Synthetic candles M5 + H1: один сценарий с PDL sweep → reversal → entry. Один симметричный для short.
- Stop loss = below sweep low; take profit = 1:3 R:R через `compare(unrealizedPnlR, ">=", 3)`.
- Trade-log: 1 long + 1 short, обе закрыты по TP.

#### 54-T3.2 Walk-forward
- Datasets: BTCUSDT M5 (12 мес) + H1 (12 мес).
- Threshold из A2 (low win-rate, R:R-driven).
- В release-checklist отдельно фиксировать R:R на каждом fold'е (gate'у sharpe мало без R:R-context'а).

#### 54-T3.3 Seed preset
- `slug: "smc-liquidity-sweep-btc-5m"`, `category: "smart-money"`, `timeframe: M5`.
- `defaultDatasetBundleJson: { "M5": true, "H1": true }`.

#### 54-T3.4 Demo smoke
- 30 мин DEMO. SMC даёт мало сетапов на этом окне — может пройти без сделок. Это допустимо, лишь бы не было ошибок.
- Минимум: бот не падает, индикаторы (sweep/fvg detection) логируются как computed, hot-loop стабилен.

#### 54-T3.5 Publish + matrix.

**DoD:** preset публичен, release-checklist row pass.

---

### 54-T4: Library landing — featured presets section

**Цель:** на главной Lab Library странице вывести 5 флагманов как featured grid.

**Файлы:** `apps/web/src/app/lab/library/page.tsx` (расширить из `docs/51-T4`).

**Шаги:**
1. Добавить компонент `FeaturedPresetsRow` сверху галереи. Источник истины — фиксированный массив slug'ов: `['adaptive-regime-btc-5m', 'mtf-scalper-btc-1m', 'smc-liquidity-sweep-btc-5m', 'dca-momentum-btc-15m', 'bb-mean-reversion-public']`.
2. Если какого-то из slug'ов нет в API-ответе (PRIVATE / не seeded) — пропустить молча, без 404.
3. Featured cards визуально отличаются: метка "Flagship", иконка категории.
4. По клику — те же flow'ы, что обычные cards (`docs/51-T4`).

**Тест-план:** manual smoke в браузере; нет регрессий в обычной галерее.

**DoD:** featured row показывает 5 cards (после T1..T3 + Adaptive из `docs/53` + bb-mean-reversion из `docs/51`).

---

### 54-T5: Capability matrix — released-status sweep

**Цель:** обновить `docs/strategies/08-strategy-capability-matrix.md` финальной картинкой после rollout.

**Шаги:**
1. Каждая строка стратегии в matrix получает `released: yes`, `presetSlug: ...`, ссылку на release-checklist.
2. Если стратегия не прошла gate (T1.2 / T2.2 / T3.2 fail) — `released: no`, `blockedBy: walk-forward-acceptance`, причина в комментарии.
3. Update overview-документа `docs/strategies/01-flagship-overview.md` — пометки release-status напротив каждой стратегии.

**DoD:** documents committed, ссылки валидны.

---

## Порядок выполнения

```
54-T1 ─┐
54-T2 ─┼─→ 54-T4 → 54-T5
54-T3 ─┘
```

T1, T2, T3 параллелизуются (разные стратегии, разные fixture'ы и preset'ы — нет shared file conflicts). Каждая из T1/T2/T3 имеет внутреннюю последовательность .1→.5.

T4 после хотя бы одного из T1/T2/T3 (featured row может отображать частичный набор). T5 — финальный апдейт документации.

## Зависимости от других документов

- `docs/51` — preset CRUD, instantiate, UI library. Обязательная.
- `docs/52` — multi-TF bundle. Обязательная для T2/T3.
- `docs/53` — пилотный пайплайн обкатан, является шаблоном для всех трёх задач.
- `docs/47`, `docs/48`, `docs/49` — research-инфраструктура.

## Backward compatibility

- Никаких runtime-кода правок (всё уже на месте после 51/52).
- Все preset'ы стартуют PRIVATE, публикация — manual flip.
- `liquidity_sweep`/`fair_value_gap`/`dca_config`/`vwap`/`volume_profile` — уже supported, не расширяются.

## Ожидаемый результат

- В Lab Library Featured Row — 5 флагманских presets (≥ 4 из них — результат `docs/54`, плюс Adaptive из `docs/53`).
- Каждый прошёл walk-forward gate + demo smoke; release-checklist полон.
- Capability matrix обновлена до released-state.
- Никакой новой DSL-семантики не добавлено.
- `docs/55` (Funding Arbitrage) идёт независимо — этот документ закрывает основной флагманский трек.
