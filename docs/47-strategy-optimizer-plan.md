# 47. Strategy Optimizer Plan

Статус: draft  
Владелец: core trading / lab  
Последнее обновление: 2026-04-26  
Родительский документ: `docs/44-strategy-engine-overview.md`  
Дорожка: A (research workflow)

## Контекст

Текущее состояние (проверено по коду):

- Phase C1 sweep уже реализован: `POST /lab/backtest/sweep` (`apps/api/src/routes/lab.ts:838`), `GET /lab/backtest/sweep/:id` (`apps/api/src/routes/lab.ts:935`), `GET /lab/backtest/sweeps` (`apps/api/src/routes/lab.ts:962`).
- Sweep — это **1-D linear sweep** одного параметра: `SweepRequestBody.sweepParam: { blockId, paramName, from, to, step }` (`apps/api/src/routes/lab.ts:1230`), runCount = `floor((to - from) / step) + 1`, max 20 (`apps/api/src/routes/lab.ts:873`).
- `runSweepAsync(sweepId)` — fire-and-forget loop (`apps/api/src/routes/lab.ts:1258`), candle load один раз на sweep (`apps/api/src/routes/lab.ts:1281`), линейный цикл `for (let paramValue = from; paramValue <= to; paramValue += step)` (`apps/api/src/routes/lab.ts:1312`).
- На каждой итерации: `runBacktest(candles, mutatedDsl, { feeBps, slippageBps, fillAt: "CLOSE" })` (`apps/api/src/routes/lab.ts:1346`).
- Sharpe считается локально: `computeSharpe(report.tradeLog.map(t => t.pnlPct))` (`apps/api/src/routes/lab.ts:1357`) — будет удалён после `docs/49-T3` (`report.sharpe` придёт из ядра).
- Best row выбирается жёстко по `pnlPct`: `results.reduce((best, r) => r.pnlPct > best.pnlPct ? r : best)` (`apps/api/src/routes/lab.ts:1398`) — нет настраиваемого `rankBy`.
- Мутация DSL: `applyDslSweepParam(dsl, blockId, paramName, paramValue)` (`apps/api/src/lib/dslSweepParam.ts:12`) — один параметр.
- Prisma модель: `BacktestSweep` со `sweepParamJson Json` (один объект) и `bestParamValue Float?` (`apps/api/prisma/schema.prisma:686`); `SweepStatus: PENDING|RUNNING|DONE|FAILED` (`apps/api/prisma/schema.prisma:677`).
- Хранение строк: `SweepRow { paramValue: number, backtestResultId, pnlPct, winRate, maxDrawdownPct, tradeCount, sharpe }` (`apps/api/src/routes/lab.ts:1244`) — plain `paramValue`, не словарь.
- Frontend: `OptimisePanel.tsx` — `SweepParam` тип (`apps/web/src/app/lab/test/OptimisePanel.tsx:18`), UI sort (`SortKey`, строка 67), `OptimiseMetric = "pnl" | "winRate" | "sharpe" | "maxDrawdown"` объявлен (`apps/web/src/app/lab/test/OptimisePanel.tsx:70`, использован в `setMetric` строка 122 и `<select>` строка 504), но **не передаётся в API** — это чисто клиентская сортировка.
- POLL/MAX: `POLL_INTERVAL_MS=2000`, `MAX_RUNS=20` (`apps/web/src/app/lab/test/OptimisePanel.tsx:75`).
- Sweepable parameters берутся из `BLOCK_DEF_MAP` через `getNumericParams` (`apps/web/src/app/lab/test/OptimisePanel.tsx:87`) и определены для SMA/EMA/RSI/MACD/Bollinger/ATR/ADX/SuperTrend (`apps/web/src/app/lab/build/blockDefs.ts:137`–`286`).
- Тесты: `apps/api/tests/routes/lab.test.ts:442`–`515`.
- Phase C1 spec: `docs/steps/25c1-lab-phase-c1-grid-search.md`.

## Цель

- Расширить sweep до **multi-parameter grid** (1..N параметров, N ≤ 3 чтобы декартово произведение помещалось в текущий лимит 20 runs).
- Ввести серверный `rankBy` для выбора best row по выбранной метрике.
- Сохранить полную backward compatibility: старый `sweepParam` (singular) и старый ответ с `paramValue: number` продолжают работать.
- Минимальные правки UI: добавление/удаление строк параметров, селектор rank-by.

## Решение по форме параметров

В `SweepRequestBody` вводится новое поле `sweepParams: SweepParam[]` (массив, 1..3 элемента). Старое поле `sweepParam` (одиночное) сохраняется как backward-compat alias: если пришло `sweepParam` без `sweepParams`, бэкенд оборачивает его в массив длиной 1. Если пришли оба — `sweepParams` приоритетнее, `sweepParam` игнорируется. Это additive расширение в духе `docs/44 §Backward compatibility`.

В `SweepRow` добавляется `paramValues: Record<string, number>` где ключ — `${blockId}.${paramName}`. Для 1-параметрического запуска поле `paramValue: number` остаётся заполненным (равно единственному значению в `paramValues`), чтобы старые клиенты (текущий `OptimisePanel.tsx`) продолжили работать без правок.

## Не входит в задачу

- Random search, Bayesian optimization, любая non-grid стратегия выбора точек.
- Distributed optimization, worker pool, BullMQ — изменения сугубо in-process в `runSweepAsync`.
- Изменение лимита 20 runs или rate limit (5/min, 2 concurrent per workspace).
- Изменения `runBacktest`, `dslEvaluator` или ядра execution.
- Введение `reportVersion` (правило отложено в `docs/49`).
- Сохранение полной матрицы для визуализации heatmap — в данном этапе достаточно линейной таблицы строк.
- Замена `applyDslSweepParam` без обёртки — старая сигнатура остаётся.

---

## Задачи

### 47-T1: Расширить `SweepRequestBody` до массива параметров

**Цель:** принимать `sweepParams: SweepParam[]` (1..3) с backward-compat alias на `sweepParam`.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — тип `SweepRequestBody` (строка 1230), валидация в `POST /lab/backtest/sweep` (строка 838).
- `apps/api/tests/routes/lab.test.ts` — расширить тесты валидации.

**Шаги реализации:**
1. В `SweepRequestBody` добавить `sweepParams?: SweepParam[]` рядом с существующим `sweepParam?: SweepParam`. Оба поля делать optional на уровне типа; валидация обеспечит, что хотя бы одно присутствует.
2. В обработчике `POST /lab/backtest/sweep` после парсинга body нормализовать вход: если `sweepParams` отсутствует, но есть `sweepParam` → `sweepParams = [sweepParam]`; если есть оба — использовать `sweepParams`, `sweepParam` игнорируется (логировать warning).
3. Валидация: `1 ≤ sweepParams.length ≤ 3`; для каждого элемента — `from < to`, `step > 0`, `(to - from) / step + 1 ≥ 2`. Декартов размер `Π (runs_i)` — проверять отдельно в 47-T3.
4. Сохранять весь массив в `BacktestSweep.sweepParamJson` как массив объектов (поле уже `Json`, миграция не требуется). Для 1-параметрического случая — массив длины 1, формат сохраняется как объект-в-массиве.
5. **Backward-compat при чтении** `sweepParamJson`: существующие записи в БД до 47-T1 содержат единичный объект `{ blockId, paramName, from, to, step }`, новые — массив `[{...}]`. Везде, где читается это поле (`runSweepAsync`, `GET /lab/backtest/sweep/:id`, `GET /lab/backtest/sweeps`), нормализовать через единый helper:
   ```ts
   const normalizeSweepParams = (json: unknown): SweepParam[] =>
     Array.isArray(json) ? json as SweepParam[] : [json as SweepParam];
   ```
   Helper применять перед любой работой со значением. Никаких backfill-миграций — старые записи остаются в исходном формате.
6. Обновить response типов `GET /lab/backtest/sweep/:id` — добавить `sweepParams: SweepParam[]` (через `normalizeSweepParams`), при этом для backward compat сохранить `sweepParam: SweepParam` как первый элемент массива.

**Тест-план:**
- Отправка только `sweepParam` → принимается, нормализуется в `sweepParams: [...]`.
- Отправка только `sweepParams` (1 элемент) → принимается.
- Отправка `sweepParams` (2 и 3 элемента) → принимается.
- Отправка `sweepParams` (4 элемента) → 400.
- Отправка обоих — `sweepParams` побеждает, в логах warning.
- Отсутствие обоих → 400.
- GET-эндпоинт возвращает оба поля для 1-парам случая.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Существующие тесты sweep зелёные без правок.
- Новые тесты валидации зелёные.
- Миграция Prisma не требуется (поле уже `Json`).

---

### 47-T2: Multi-param мутация DSL — `applyDslSweepParams`

**Цель:** ввести функцию для мутации сразу нескольких параметров DSL за один проход, сохранив `applyDslSweepParam` как тонкую обёртку.

**Файлы для изменения:**
- `apps/api/src/lib/dslSweepParam.ts` — добавить `applyDslSweepParams`, оставить `applyDslSweepParam`.
- `apps/api/tests/lib/dslSweepParam.test.ts` (создать или дополнить, если уже есть) — unit-тесты.

**Шаги реализации:**
1. Добавить функцию `applyDslSweepParams(dsl: DslJson, params: Array<{ blockId: string; paramName: string; value: number }>): DslJson`.
2. Реализация: глубокий клон DSL один раз (`structuredClone`), затем in-place мутация по каждому элементу `params` — ровно та же логика поиска блока по `blockId` и присвоения `paramName`, что в существующем `applyDslSweepParam` (строки 12–35). Если блок не найден или `paramName` не существует — выбросить ту же ошибку, что и в одиночной версии (сохранить текст ошибки).
3. Переписать `applyDslSweepParam(dsl, blockId, paramName, value)` как `return applyDslSweepParams(dsl, [{ blockId, paramName, value }])`. Старая сигнатура остаётся, импортёры не меняются.
4. Обеспечить детерминизм: порядок применения мутаций = порядок элементов массива. Документировать это в JSDoc.
5. Если два элемента массива указывают на один и тот же `(blockId, paramName)` — последний выигрывает (но валидация в 47-T1 должна это предотвращать — добавить проверку уникальности на уровне роутера).

**Тест-план:**
- Unit: 1 параметр через `applyDslSweepParams` — результат идентичен `applyDslSweepParam`.
- Unit: 2 параметра в разных блоках — оба применены.
- Unit: 2 параметра в одном блоке — оба применены.
- Unit: несуществующий `blockId` — та же ошибка, что в одиночной версии.
- Unit: исходный DSL не мутируется (immutability проверка через deep equality до/после).
- Существующие тесты `applyDslSweepParam` зелёные без правок.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Все существующие импортёры `applyDslSweepParam` работают без изменений.
- `applyDslSweepParams` экспортируется из `dslSweepParam.ts`.
- Покрытие тестами включает single-param, multi-param и ошибочные сценарии.

---

### 47-T3: N-D grid generation в `runSweepAsync` + расширение `SweepRow`

**Цель:** в существующем fire-and-forget sweep-loop заменить линейный 1-D цикл на декартов перебор по `sweepParams`; сохранить лимит 20 runs; расширить `SweepRow` дополнительным полем `paramValues`.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — `runSweepAsync` (`строка 1258`), типизация `SweepRow` (`строка 1244`), валидация общего числа runs (`строка 873`).
- `apps/api/tests/routes/lab.test.ts` — расширить существующие e2e тесты sweep.

**Шаги реализации:**
1. Перенести вычисление `runCount` per-param: для каждого `p ∈ sweepParams` `runs_p = floor((p.to - p.from) / p.step) + 1`. Полное число итераций = `Π runs_p`. Если `Π runs_p > 20` → 400 на эндпоинте (валидация до запуска `runSweepAsync`).
2. В `runSweepAsync` сгенерировать массив комбинаций. Реализация: чистый детерминированный декартов перебор (например, n-вложенный `for` через рекурсию или iterative с массивом индексов). Порядок комбинаций — лексикографический по индексам параметров `[0..0..0], [0..0..1], ...` — фиксируется в комментарии для воспроизводимости.
3. Для каждой комбинации: построить `params: Array<{ blockId, paramName, value }>`, вызвать `applyDslSweepParams(dsl, params)` (из 47-T2), затем `runBacktest(candles, mutatedDsl, { feeBps, slippageBps, fillAt: "CLOSE" })`. Параметр `fillAt` остаётся `"CLOSE"` пока `docs/46` не закрыт; после `docs/46-T1` сюда передаётся пользовательский `fillAt`.
4. В `SweepRow` добавить новое поле `paramValues: Record<string, number>` где ключ = `${blockId}.${paramName}`. Поле `paramValue: number` сохраняется и для случая `sweepParams.length === 1` равно единственному значению из `paramValues` (для backward compat). Для `sweepParams.length > 1` — `paramValue` равно значению **первого** параметра из массива (документировать в комментарии; клиенты, которые поддерживают multi-param, должны читать `paramValues`).
5. Хранение в БД: **отдельной таблицы `BacktestSweepRow` НЕТ**. `SweepRow[]` сериализуется внутри `BacktestSweep.resultsJson Json?` (`apps/api/prisma/schema.prisma:699`). Соответственно — **никакой Prisma-миграции не требуется**: новое поле `paramValues` добавляется внутрь существующего JSON-массива. Шаги: (а) обновить TS-тип `SweepRow`, (б) при записи в `resultsJson` сериализовать новое поле, (в) при чтении из `resultsJson` принимать оба формата (старые записи без `paramValues` корректно обрабатываются как `paramValues = { [`${blockId}.${paramName}`]: paramValue }` через fallback-helper).
6. Прогресс: текущий `progress: number` в `BacktestSweep` сохраняется как `iterationsDone / totalIterations` — формула не меняется, корректно работает для N-D.

**Тест-план:**
- e2e: 1-параметрический sweep — старый формат запроса работает, ответ содержит и `paramValue`, и `paramValues`.
- e2e: 2-параметрический sweep с малыми диапазонами (например, 2×3 = 6 runs) — все 6 комбинаций пробежали, `paramValues` корректен на каждой строке.
- e2e: 3×3×3 = 27 runs → 400 (превышен лимит 20).
- e2e: 3×3 = 9 runs — успех.
- Юнит: декартов генератор детерминирован (одинаковый input → одинаковый порядок комбинаций).
- Существующие тесты sweep продолжают проходить.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Лимит 20 runs соблюдается.
- Старый клиент получает ровно тот же набор полей, что и раньше (`paramValue`, `pnlPct`, `winRate`, ...).
- Новый клиент получает дополнительно `paramValues`.
- Миграция Prisma additive, безопасна для существующих записей.

---

### 47-T4: Серверный `rankBy` для выбора best row

**Цель:** ввести параметр `rankBy: "pnlPct" | "winRate" | "sharpe" | "profitFactor" | "expectancy"` в `SweepRequestBody`; жёсткий выбор по `pnlPct` заменить на выбор по указанной метрике; сохранить полную backward compatibility.

**Файлы для изменения:**
- `apps/api/src/routes/lab.ts` — `SweepRequestBody` (`строка 1230`), best-row selection (`строка 1398`).
- `apps/api/tests/routes/lab.test.ts` — добавить тест-кейсы.

**Шаги реализации:**
1. В `SweepRequestBody` добавить optional `rankBy?: "pnlPct" | "winRate" | "sharpe" | "profitFactor" | "expectancy"`. Default: `"pnlPct"` (сохраняет текущее поведение). `winRate` включён несмотря на свою методологическую слабость (легко обманывается мелкими wins при крупных losses): пользователь имеет на это право, и оставить его UI-only при наличии серверных `sharpe/PF/expectancy` было бы непоследовательно.
2. Поля `sharpe`, `profitFactor`, `expectancy` приходят из `DslBacktestReport` после `docs/49-T2`. До тех пор реализуются только ветки `pnlPct` и `winRate` (оба доступны из текущего `report` без зависимостей); для `sharpe`/`profitFactor`/`expectancy` до завершения `docs/49-T2` бросать 400 с пояснением "rankBy=<x> requires docs/49-T2 metrics; available now: 'pnlPct', 'winRate'". Это явная gating-зависимость, документировать в PR-описании.
3. В `runSweepAsync` после сбора всех `results` заменить жёсткий `r.pnlPct > best.pnlPct` на `compareByMetric(r, best, rankBy) > 0`. Реализация `compareByMetric`:
   - `pnlPct`: больше = лучше.
   - `winRate`: больше = лучше.
   - `sharpe`: больше = лучше; `null` трактуется как `-Infinity`.
   - `profitFactor`: больше = лучше; `Infinity` (нет убытков) сортируется выше любого конечного.
   - `expectancy`: больше = лучше.
4. Tie-breaking (per `docs/44 §Детерминизм`): при равенстве метрики использовать индекс комбинации (меньший индекс = победитель). Это даёт детерминированный результат для одинаковых сценариев.
5. Сохранить `bestParamValue Float?` в `BacktestSweep` для 1-параметрического случая (значение первого параметра комбинации-победителя). Добавить `bestParamValuesJson Json?` для multi-param.
   - **Prisma migration**: `ALTER TABLE "BacktestSweep" ADD COLUMN "bestParamValuesJson" JSONB` (additive, nullable). В `schema.prisma` рядом с `bestParamValue Float?` (line 700): `bestParamValuesJson Json?`.
   - Также additive колонка `rankBy String @default("pnlPct")` в той же миграции — для эхо-ответа и аудита (без неё `GET /lab/backtest/sweep/:id` не сможет восстановить, по какой метрике выбран best).
6. В response `GET /lab/backtest/sweep/:id` вернуть оба поля, плюс `rankBy` (эхо запроса).

**Тест-план:**
- `rankBy` не указан → default `pnlPct`, поведение совпадает с текущим.
- `rankBy: "pnlPct"` явно → поведение совпадает с default.
- `rankBy: "sharpe"` без `docs/49-T2` → 400.
- (после `docs/49-T2`) `rankBy: "sharpe"` — best row выбран по sharpe; tie-break проверен фикстурой с равными значениями.
- `rankBy` не из allowed enum → 400.

**Критерии готовности:**
- `tsc --noEmit` проходит.
- Default-поведение идентично текущему — старые клиенты не сломаны.
- `bestParamValue` для 1-param случая совпадает со старым полем при `rankBy="pnlPct"`.
- 400 для метрик, требующих `docs/49-T2`, с понятным сообщением.

---

### 47-T5: UI — multi-param строки и rank-by селектор в `OptimisePanel.tsx`

**Цель:** позволить пользователю добавить до 3 параметров для grid-search и выбрать серверную метрику ранжирования; минимальные правки таблицы для отображения нескольких param-колонок.

**Файлы для изменения:**
- `apps/web/src/app/lab/test/OptimisePanel.tsx`.

**Шаги реализации:**
1. Заменить state одиночного `sweepParam` на массив `sweepParams: SweepParam[]` (1..3). UI: список строк, в каждой — селектор блока + селектор параметра + поля `from/to/step`. Кнопка `+ Add parameter` (disabled при достижении 3); кнопка удаления на каждой строке (disabled когда строк ровно 1).
2. Перед отправкой POST: считать суммарный размер grid-а `Π runs_p` локально и блокировать кнопку запуска (с подсказкой "макс 20 итераций"), если превышено. Та же валидация остаётся на сервере (47-T3).
3. Существующий локальный `OptimiseMetric` (`строка 70`) — перевести в передаваемый на сервер `rankBy` параметр запроса. Маппинг: `"pnl"→"pnlPct"`, `"winRate"→` (НЕ передавать, т.к. в server-side enum его нет — оставить как UI-only sort), `"sharpe"→"sharpe"`, `"maxDrawdown"→` (UI-only sort). То есть `rankBy` присылается только для `pnl`/`sharpe`/(после `docs/49-T2`) `profitFactor`/`expectancy`. Для `winRate`/`maxDrawdown` — `rankBy` не присылается, делается клиентский sort (как сейчас).
4. Таблица результатов: вместо одной колонки `paramValue` — серия колонок по `sweepParams`, читать из `paramValues`. Для backward-compat: если ответ содержит только `paramValue` (старый сервер), отрисовать одну колонку.
4.1. **Расширение `SortKey`** (`apps/web/src/app/lab/test/OptimisePanel.tsx:67`). Текущий enum жёстко содержит литерал `"paramValue"`. После multi-param param-колонки динамические — каждая идентифицируется ключом `${blockId}.${paramName}`. Решение: расширить `SortKey` через type-union:
   ```ts
   type FixedSortKey = "pnlPct" | "winRate" | "maxDrawdownPct" | "tradeCount" | "sharpe";
   type ParamSortKey = `param:${string}`;       // например, "param:block_42.length"
   type SortKey = FixedSortKey | ParamSortKey | "paramValue"; // "paramValue" — legacy 1-param fallback
   ```
   В `handleSort` для `ParamSortKey` распаковывать ключ → получать `(blockId, paramName)` → сортировать `rows` по `row.paramValues[`${blockId}.${paramName}`]`. Для `"paramValue"` — старая ветка (если сервер прислал только legacy-поле).
5. `MAX_RUNS = 20` остаётся; обновить подсказку рядом с кнопкой запуска: "Макс 20 итераций (произведение run-counts всех параметров)".
6. Не вводить новые публичные компоненты: всё inline в `OptimisePanel.tsx`.

**Тест-план:**
- Ручной smoke в Lab → Test → Optimise:
  - 1 параметр — старый сценарий, всё работает.
  - 2 параметра 2×3 = 6 runs — таблица содержит 2 param-колонки и 6 строк.
  - 3 параметра 2×2×3 = 12 — успех.
  - 3 параметра 3×3×3 = 27 — кнопка disabled, подсказка показана.
- `rankBy=pnl` → серверный best совпадает с лучшим pnl в таблице.
- `rankBy=sharpe` (после `docs/49-T2`) — серверный best совпадает с лучшим sharpe.
- `rankBy=winRate` или `maxDrawdown` — `rankBy` не отправляется, серверный best остаётся по `pnlPct`, клиентский sort работает.

**Критерии готовности:**
- TypeScript-проверка фронтенда проходит.
- Lab UI запускается, golden-path 1-param + multi-param работает в браузере.
- Нет регрессий в существующем sort/filter поведении.

---

### 47-T6: Тесты — unit и e2e расширения

**Цель:** довести покрытие до уровня, при котором регрессии sweep-функционала ловятся на CI.

**Файлы для изменения:**
- `apps/api/tests/lib/dslSweepParam.test.ts` (создать или дополнить).
- `apps/api/tests/routes/lab.test.ts` — расширить блок тестов `/lab/backtest/sweep` (`строки 442–515`).
- (опционально) `apps/api/tests/lib/sweepGrid.test.ts` — unit для декартова генератора, если он вынесен в отдельную функцию в 47-T3.

**Шаги реализации:**
1. Добавить unit-тесты для `applyDslSweepParams` (см. 47-T2 тест-план), если не были добавлены в самой задаче 47-T2.
2. Добавить unit-тест для генератора комбинаций: вход `[{from:1,to:2,step:1},{from:10,to:20,step:5}]` → выход `[[1,10],[1,15],[1,20],[2,10],[2,15],[2,20]]` — проверить порядок и полноту.
3. Расширить `lab.test.ts`:
   - happy-path 2-param sweep: проверить `paramValues` на каждой строке, проверить `bestParamValuesJson` после завершения.
   - rejection при `Π runs > 20`.
   - rejection при `sweepParams.length === 0` или `> 3`.
   - rejection при дубликате `(blockId, paramName)` в `sweepParams`.
   - backward-compat: старый запрос с `sweepParam` (singular) проходит.
4. Все новые тесты должны быть детерминированы: фикстуры свечей зашиты в файл, рандом не используется (если бы использовался — явный seed).

**Тест-план:**
- `npm test` (или соответствующий тестовый раннер apps/api) проходит.
- Time-skewed/flaky тесты отсутствуют (новые тесты не зависят от текущего времени).

**Критерии готовности:**
- Все новые тесты зелёные на CI.
- Существующие тесты sweep остаются зелёными.
- Покрытие `dslSweepParam.ts` и grid-генератора ≥ 90% по строкам (метрика опциональна, ориентир).

---

## Порядок выполнения задач

```
47-T1 → 47-T2 → 47-T3 → 47-T4 → 47-T5 → 47-T6
```

Каждая задача — отдельный PR.

- 47-T1 и 47-T2 можно параллелить, но T3 требует обоих.
- 47-T4 зависит от `docs/49-T2` для `rankBy ∈ {sharpe, profitFactor, expectancy}`. Если `docs/49-T2` ещё не закрыт на момент T4 — реализовать только `pnlPct`-ветку, оставив 400 для остальных, и закрыть остальные ветки follow-up PR-ом после `docs/49-T2`.
- 47-T5 идёт после T3 и T4 (UI читает новый формат ответа и отправляет `rankBy`).
- 47-T6 — последний шаг или встроен в каждую предыдущую задачу инкрементально.

## Зависимости от других документов

- `docs/49-T2` — расширение `DslBacktestReport` полями `sharpe`, `profitFactor`, `expectancy`. Обязательно для полноценного 47-T4. Без него реализуется только `rankBy="pnlPct"`.
- `docs/46-T1` — параметр `fillAt` в `DslExecOpts`. Косвенная: после закрытия `docs/46-T1` `runSweepAsync` должен передавать пользовательский `fillAt` в `runBacktest`, а не жёстко `"CLOSE"` (`apps/api/src/routes/lab.ts:1346`).
- `docs/45` — независимо. Никаких блокирующих связей.

## Backward compatibility checklist

- `SweepRequestBody.sweepParam` (singular) продолжает работать.
- `SweepRow.paramValue: number` сохраняется в ответе для всех случаев.
- `BacktestSweep.bestParamValue` сохраняется для 1-param случая.
- `rankBy` отсутствует → default `"pnlPct"` → поведение идентично текущему.
- Миграции Prisma — только additive колонки (`paramValuesJson`, `bestParamValuesJson`).
- Старый клиент (`OptimisePanel.tsx` до 47-T5) с новым сервером — работает: читает `paramValue`, игнорирует `paramValues`.
- Старый сервер с новым клиентом (47-T5) — работает: клиент видит `paramValue` без `paramValues` и отрисовывает одну колонку.
- `reportVersion` не вводится (правило отложено в `docs/49`).

## Ожидаемый результат

После завершения всех задач:
- Lab Optimise позволяет запускать grid-search по 1..3 параметрам в пределах лимита 20 runs.
- Best row выбирается на сервере по настраиваемой метрике с детерминированным tie-break.
- `runBacktest` и ядро DSL-evaluator не модифицированы (правки только на уровне sweep-loop и DSL-мутации).
- Вся существующая Phase C1 функциональность работает без правок клиентского кода вне `OptimisePanel.tsx`.
