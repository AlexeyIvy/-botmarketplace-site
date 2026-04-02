# Roadmap v2 — Production Hardening & Feature Completion

> Документ описывает план развития после завершения Stages 1-8.
> Каждая задача рассчитана на одну сессию Claude Code (~30 мин, ≤20 файлов).
> Формат: копируй блок "Промт для сессии" → вставляй в новую сессию.

## Текущее состояние

- **Stages 1-8**: завершены, 944 теста, PR #184
- **VPS**: botmarketplace.store, systemd, PR #184 deployed
- **28 блоков** в визуальном конструкторе (19 supported, 9 compile-only)
- **Известный техдолг**: security, observability, compile-only блоки, funding pipeline

---

## Phase 9 — Security & Infrastructure Hardening

### 9.1 Non-root systemd + rate limiting

**Цель**: API и Web не должны работать от root. Rate limit на тяжёлые endpoints.

**Шаги (одна сессия на VPS):**
1. Создать системного пользователя `botmarket`
2. Перенастроить systemd units на `User=botmarket`
3. Добавить `express-rate-limit` middleware в API
4. Rate limit: `/lab/backtest` — 10 req/min, `/terminal/*` — 30 req/min
5. Перезапустить, проверить

**Файлы**: `apps/api/src/server.ts` (middleware), systemd units на VPS

**Промт для сессии**:
```
Работай в репо /opt/-botmarketplace-site на VPS.

1. Создай пользователя: sudo useradd -r -s /bin/false botmarket
2. Выдай права: sudo chown -R botmarket:botmarket /opt/-botmarketplace-site
3. Обнови systemd units (User=botmarket вместо root)
4. В apps/api/src/server.ts добавь express-rate-limit:
   - /lab/backtest: 10 req/min
   - /terminal/*: 30 req/min  
   - всё остальное: 100 req/min
5. pnpm install express-rate-limit @types/express-rate-limit
6. Пересобери, рестартни, проверь что всё работает
```

---

### 9.2 Health check + structured logging

**Цель**: endpoint `/health` для nginx/мониторинга. Замена console.log на pino.

**Шаги (одна сессия, ~15 файлов):**
1. Добавить `GET /health` → `{ status: "ok", uptime, version, timestamp }`
2. Установить `pino` + `pino-http`
3. Заменить `console.log/warn/error` в ключевых модулях на `logger.info/warn/error`
4. Добавить request logging middleware (pino-http)
5. Тест для `/health`

**Файлы**: `server.ts`, `logger.ts` (новый), `botWorker.ts`, `backtest.ts`

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

1. Создай apps/api/src/lib/logger.ts — экспортирует pino logger
2. Добавь GET /health endpoint в server.ts: {status:"ok", uptime, version}
3. Добавь pino-http middleware для request logging
4. Замени console.log/warn/error на logger в: botWorker.ts, backtest.ts, server.ts
5. Напиши тест для /health
6. pnpm install pino pino-http
7. Запусти тесты, закоммить, запушь
```

---

### 9.3 Prisma migration files + DB backup script

**Цель**: создать реальные migration files (не db push). Скрипт бэкапа PostgreSQL.

**Шаги (одна сессия):**
1. `npx prisma migrate dev --name add_funding_and_hedge_models`
2. Закоммитить `prisma/migrations/` 
3. Создать `scripts/backup-db.sh` (pg_dump → /opt/backups/)
4. Добавить cron: ежедневно в 3:00

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

1. npx prisma migrate dev --name add_funding_and_hedge_models
   (создаст migration files для FundingSnapshot, SpreadSnapshot, HedgePosition, LegExecution)
2. Закоммить prisma/migrations/ 
3. Создай scripts/backup-db.sh:
   - pg_dump с timestamp в /opt/backups/
   - Удаляет бэкапы старше 14 дней
   - Логирует в /var/log/botmarket-backup.log
4. Закоммить, запушь
5. На VPS: prisma migrate deploy + crontab -e → 0 3 * * * /opt/-botmarketplace-site/scripts/backup-db.sh
```

---

## Phase 10 — Compile-Only Block Promotion

### 10.1 Audit supportMap + promote already-working blocks

**Цель**: ATR, Bollinger, Constant уже работают в evaluator — обновить supportMap.

**Шаги (одна сессия, ~10 файлов):**
1. Прочитать `getIndicatorValues` — найти все type branches
2. Сравнить с `supportMap.ts` — найти расхождения
3. Промотировать всё что реально работает
4. Обновить snapshot в `blockDrift.test.ts`
5. Запустить тесты

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

1. Прочитай apps/api/src/lib/dslEvaluator.ts функцию getIndicatorValues — 
   выпиши все поддерживаемые type branches
2. Прочитай apps/api/src/lib/compiler/supportMap.ts — найди блоки со 
   статусом "compile-only" которые уже работают в evaluator
3. Промотируй их в "supported" с соответствующим note
4. Обнови snapshot в tests/compiler/blockDrift.test.ts
5. Запусти тесты, закоммить, запушь, создай PR
```

---

### 10.2 Implement and_gate + or_gate in evaluator

**Цель**: composed conditions — "RSI > 70 AND SMA cross" в одном сигнале.

**Шаги (одна сессия, ~10 файлов):**
1. Расширить `DslSignal` типом `"and"` / `"or"` с массивом sub-conditions
2. Добавить ветки в `evaluateSignal`
3. Промотировать `and_gate`, `or_gate` в supportMap
4. Тесты: compound conditions, nested gates, edge cases
5. Обновить blockDrift snapshot

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Реализуй composed signal conditions (and_gate, or_gate) в evaluator.

1. В dslEvaluator.ts расширь DslSignal:
   - type: "and" → conditions: DslSignal[], все должны быть true
   - type: "or" → conditions: DslSignal[], хотя бы одна true
2. В evaluateSignal добавь рекурсивные ветки для "and"/"or"
3. Промотируй and_gate, or_gate в supportMap.ts
4. Обнови blockDrift.test.ts snapshot
5. Напиши тесты в tests/lib/dslEvaluator.test.ts:
   - and(compare_true, compare_true) → true
   - and(compare_true, compare_false) → false  
   - or(compare_false, compare_true) → true
   - nested: and(or(...), compare) 
6. Запусти полный тест suite, закоммить, запушь, создай PR
```

---

### 10.3 Implement MACD + Volume in evaluator

**Цель**: MACD histogram и Volume как indicator series.

**Шаги (одна сессия, ~8 файлов):**
1. Проверить что `calcMACD` есть в indicators/
2. Добавить ветки в `getIndicatorValues` + IndicatorCache
3. Добавить volume series (просто `candles[i].volume`)
4. Промотировать в supportMap
5. Тесты

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь MACD и Volume в evaluator runtime.

1. Проверь что apps/api/src/lib/indicators/ содержит calcMACD. Если нет — реализуй.
2. В dslEvaluator.ts добавь в getIndicatorValues:
   - "macd" → MACD histogram series
   - "volume" → candles.map(c => c.volume)
3. Добавь в IndicatorCache: macd Map, volume (number|null)[]|null
4. Промотируй macd, volume в supportMap
5. Обнови blockDrift.test.ts
6. Тесты: MACD на тренде, volume серия длиной = candles
7. Запусти тесты, закоммить, создай PR
```

---

## Phase 11 — Funding Pipeline (end-to-end)

### 11.1 Funding ingestion scheduler

**Цель**: cron job, который каждые 8 часов fetches funding rates с Bybit.

**Шаги (одна сессия, ~6 файлов):**
1. Создать `apps/api/src/lib/funding/fetcher.ts` — HTTP-вызовы к Bybit API
2. Создать `apps/api/src/lib/funding/ingestJob.ts` — fetch → parse → save to DB
3. Cron через `node-cron` или отдельный скрипт
4. Тесты с мокнутыми HTTP-ответами

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Создай funding rate ingestion job.

1. apps/api/src/lib/funding/fetcher.ts:
   - fetchFundingRates(symbol): GET /v5/market/funding/history
   - fetchLinearTickers(): GET /v5/market/tickers?category=linear
   - fetchSpotTickers(): GET /v5/market/tickers?category=spot
   Используй существующий HTTP-клиент или fetch.

2. apps/api/src/lib/funding/ingestJob.ts:
   - ingestFundingRates(): fetch → parseFundingHistory → upsert в FundingSnapshot
   - ingestSpreads(): fetchLinearTickers + fetchSpotTickers → buildSpreadFromTickers → save
   
3. Зарегистрируй cron в server.ts: каждые 8 часов запускать ingestJob
4. Тесты: мокнутые ответы → parse → правильные FundingSnapshot[]
5. Закоммить, запушь, создай PR
```

---

### 11.2 Funding API routes

**Цель**: REST endpoints для scanner и history.

**Шаги (одна сессия, ~5 файлов):**
1. `GET /terminal/funding/scanner` — query DB → scanFundingCandidates → JSON
2. `GET /terminal/funding/:symbol/history` — FundingSnapshot[] за период
3. Query params: minYield, maxBasis, limit, from/to
4. Тесты

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь API routes для funding scanner.

1. В apps/api/src/routes/terminal.ts (или новый funding.ts):
   - GET /terminal/funding/scanner
     Query: minYield, maxBasis, minStreak, limit
     → загрузи последние FundingSnapshot + SpreadSnapshot из Prisma
     → scanFundingCandidates(symbolData, thresholds)
     → верни JSON

   - GET /terminal/funding/:symbol/history
     Query: from, to, limit
     → FundingSnapshot[] из Prisma за период

2. Тесты с мокнутой Prisma
3. Закоммить, запушь, создай PR
```

---

### 11.3 Funding Scanner UI page

**Цель**: фронтенд-страница с таблицей funding candidates.

**Шаги (одна сессия, ~5 файлов):**
1. Новая страница `apps/web/src/app/terminal/funding/page.tsx`
2. Таблица: symbol, yield%, basis bps, streak, avg rate
3. Фильтры: min yield, max basis
4. Fetch из `/terminal/funding/scanner`

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Создай страницу Funding Scanner.

1. apps/web/src/app/terminal/funding/page.tsx:
   - Fetch GET /api/terminal/funding/scanner
   - Таблица с колонками: Symbol, Yield %, Basis (bps), Streak, Avg Rate
   - Сортировка по клику на заголовок
   - Фильтры: минимальный yield, максимальный basis
   - Стиль — как существующие страницы терминала

2. Добавь ссылку в навигацию (если есть sidebar/nav)
3. Закоммить, запушь, создай PR
```

---

## Phase 12 — Evaluator Improvements

### 12.1 Direct sideCondition for discrete signals

**Цель**: SMC паттерны (+1/-1) используются как sideCondition напрямую.

**Шаги (одна сессия, ~5 файлов):**
1. Добавить `mode?: "price_vs_indicator" | "indicator_sign"` в `DslSideCondition`
2. В `determineSide`: если mode=indicator_sign, val>0→long, val<0→short
3. Обновить schema.json
4. Тесты
5. Обновить DSL docs

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь "direct" mode для sideCondition (discrete SMC signals).

1. В dslEvaluator.ts тип DslSideCondition:
   - Добавь mode?: "price_vs_indicator" | "indicator_sign"
   - Default: "price_vs_indicator" (текущее поведение)

2. В determineSide():
   - Если mode === "indicator_sign":
     val > 0 → "long", val < 0 → "short", val === 0 → null
   - Иначе: текущая логика (price vs indicator)

3. Обнови docs/schema/strategy.schema.json — добавь mode в sideCondition
4. Тесты: SMC sweep +1 → long, -1 → short, 0 → null
5. Обнови docs/10-strategy-dsl.md — задокументируй новый mode
6. Закоммить, создай PR
```

---

### 12.2 Unknown indicator type warning

**Цель**: предотвратить silent failures от тайпо в blockType.

**Шаги (одна мини-сессия, ~3 файла):**
1. В `getIndicatorValues` — `logger.warn` для unknown type
2. Тест: unknown type → all nulls + warning logged

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

В apps/api/src/lib/dslEvaluator.ts в функции getIndicatorValues,
в конце (где возвращается all-nulls для неизвестного типа):
1. Добавь логирование: logger.warn({ blockType: type }, "Unknown indicator type in getIndicatorValues — returning nulls")
2. Импортируй logger (если logger.ts ещё не создан — создай минимальный на pino)
3. Тест: вызови getIndicatorValues("typo_indicator", ...) → expect all nulls
4. Закоммить, запушь
```

---

## Порядок выполнения (рекомендуемый)

```
Session 1:  9.1  — non-root + rate limiting (VPS)
Session 2:  9.2  — health check + logging
Session 3:  9.3  — Prisma migrations + backup
Session 4:  10.1 — audit supportMap (быстрая)
Session 5:  10.2 — and_gate / or_gate
Session 6:  10.3 — MACD + Volume
Session 7:  12.2 — unknown indicator warning (быстрая)
Session 8:  12.1 — direct sideCondition
Session 9:  11.1 — funding scheduler
Session 10: 11.2 — funding API routes
Session 11: 11.3 — funding UI
```

**Оценка**: ~11 сессий, каждая ~30-60 минут. При 2 сессиях в день — ~1 неделя.

---

## Принципы работы с контекстным окном

1. **Одна задача = одна сессия.** Не комбинируй задачи из разных фаз.
2. **Промт содержит всё нужное**: файлы, что делать, в каком порядке.
3. **Максимум 15-20 файлов** на сессию (чтение + запись).
4. **Завершай коммитом** — следующая сессия начинает с чистого состояния.
5. **Self-review** — попроси Claude проревьюить перед мерджем.
