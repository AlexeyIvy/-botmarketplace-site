# Roadmap v2 — Production Hardening & Feature Completion

> Документ описывает план развития после завершения Stages 1-8.
> Каждая задача рассчитана на одну сессию Claude Code (~30 мин, ≤20 файлов).
> Формат: копируй блок "Промт для сессии" → вставляй в новую сессию Claude Code.
>
> **Деплой**: все задачи выполняются через терминальный Claude Code на VPS.
> После каждого PR → промт деплоя в конце документа.

## Текущее состояние

- **Stages 1-8**: завершены, 944 теста, последний PR #185
- **VPS**: botmarketplace.ru, systemd (botmarketplace-api, botmarketplace-web), PR #185 deployed
- **28 блоков** в визуальном конструкторе (19 supported, 9 compile-only)
- **Известный техдолг**: security, observability, compile-only блоки, funding pipeline

### Тест-baseline

| Метрика | Значение |
|---------|----------|
| Тесты | 944 pass |
| Единственный failure | positionManager.test.ts (Prisma client, pre-existing) |
| Блоки supported | 19 |
| Блоки compile-only | 9 (and_gate, or_gate, atr, bollinger, macd, volume, constant, proximity_filter, volume_profile) |

---

## Phase 9 — Security & Infrastructure Hardening

### 9.1 Non-root systemd + rate limiting

**Цель**: API и Web не должны работать от root. Rate limit на тяжёлые endpoints.

**Шаги:**
1. Создать системного пользователя `botmarket`
2. Перенастроить systemd units на `User=botmarket`
3. Добавить `express-rate-limit` middleware в API
4. Rate limit: `/lab/backtest` — 10 req/min, `/terminal/*` — 30 req/min
5. Перезапустить, проверить

**Файлы**: `apps/api/src/server.ts`, systemd units на VPS

**Промт для сессии**:
```
Работай в репо /opt/-botmarketplace-site.

1. Создай пользователя: sudo useradd -r -s /bin/false botmarket
2. Выдай права: sudo chown -R botmarket:botmarket /opt/-botmarketplace-site
3. Обнови /etc/systemd/system/botmarketplace-api.service — User=botmarket
4. Обнови /etc/systemd/system/botmarketplace-web.service — User=botmarket
5. В apps/api/src/server.ts добавь express-rate-limit:
   - /lab/backtest: 10 req/min (windowMs: 60000, max: 10)
   - /terminal/*: 30 req/min
   - всё остальное: 100 req/min
6. pnpm install express-rate-limit
7. Пересобери API: cd apps/api && npx tsc
8. sudo systemctl daemon-reload
9. sudo systemctl restart botmarketplace-api botmarketplace-web
10. Проверь: curl http://localhost:4000/health (или любой endpoint), curl http://localhost:3000
11. Проверь что процессы работают НЕ от root: ps aux | grep node
12. Закоммить изменения в server.ts, запушь
```

**Критерий готовности**: процессы работают от `botmarket`, rate limit отдаёт 429 при превышении.

---

### 9.2 Health check + structured logging

**Цель**: endpoint `/health` для nginx/мониторинга. Structured JSON logging через pino.

**Шаги:**
1. Добавить `GET /health` → `{ status: "ok", uptime, version, timestamp }`
2. Установить `pino` + `pino-http`
3. Создать `logger.ts` модуль
4. Заменить `console.log/warn/error` в ключевых модулях на logger
5. Добавить request logging middleware
6. Тест для `/health`

**Файлы**: `server.ts`, `logger.ts` (новый), `botWorker.ts`, `backtest.ts`

**Промт для сессии**:
```
Работай в репо botmarketplace-site. Не трогай файлы в patterns/ и funding/ — 
они уже готовы.

1. pnpm install pino pino-http
2. Создай apps/api/src/lib/logger.ts:
   - export const logger = pino({ level: process.env.LOG_LEVEL || "info" })
   - export default logger
3. Добавь GET /health endpoint в server.ts или routes/:
   - Ответ: { status: "ok", uptime: process.uptime(), timestamp: Date.now() }
4. Добавь pino-http middleware в server.ts для request logging
5. В botWorker.ts замени console.log/warn/error на logger.info/warn/error
   (только в этом файле, не трогай другие)
6. Напиши тест: GET /health → 200 + body.status === "ok"
7. Запусти тесты (npx vitest run), убедись что ≥944 pass
8. Закоммить, запушь, создай PR
```

**Критерий готовности**: `/health` отдаёт 200, логи в JSON-формате.

---

### 9.3 Prisma migration files + DB backup script

**Цель**: создать реальные migration files. Скрипт бэкапа PostgreSQL.

**Шаги:**
1. `npx prisma migrate dev --name add_funding_and_hedge_models`
2. Закоммитить `prisma/migrations/`
3. Создать `scripts/backup-db.sh`
4. На VPS: `prisma migrate deploy` + cron

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

1. Убедись что DATABASE_URL задан в .env (или экспортируй для сессии)
2. npx prisma migrate dev --name add_funding_and_hedge_models
   Это создаст migration files для: FundingSnapshot, SpreadSnapshot, 
   HedgePosition, LegExecution
3. Если migrate dev не работает (нет DB) — это ОК, тогда:
   - npx prisma migrate diff --from-empty --to-schema-datamodel prisma/schema.prisma --script > prisma/migrations/20260403000000_add_funding_and_hedge_models/migration.sql
   - Создай вручную нужную структуру папок
4. Создай scripts/backup-db.sh:
   #!/bin/bash
   BACKUP_DIR=/opt/backups
   mkdir -p $BACKUP_DIR
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   pg_dump $DATABASE_URL > $BACKUP_DIR/botmarket_$TIMESTAMP.sql
   find $BACKUP_DIR -name "*.sql" -mtime +14 -delete
   echo "$(date): Backup completed" >> /var/log/botmarket-backup.log
5. chmod +x scripts/backup-db.sh
6. Закоммить prisma/migrations/ и scripts/backup-db.sh, запушь, создай PR
```

**Деплой на VPS (после merge)**:
```
cd /opt/-botmarketplace-site && git pull origin main
npx prisma migrate deploy
crontab -e → добавь: 0 3 * * * /opt/-botmarketplace-site/scripts/backup-db.sh
sudo systemctl restart botmarketplace-api
```

**Критерий готовности**: таблицы FundingSnapshot/HedgePosition в БД, бэкап в cron.

---

## Phase 10 — Compile-Only Block Promotion

### 10.1 Audit supportMap + promote already-working blocks

**Цель**: несколько compile-only блоков (ATR, Bollinger, Constant) уже работают в evaluator — supportMap устарел.

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Задача: найти и устранить drift между getIndicatorValues и supportMap.

1. Прочитай apps/api/src/lib/dslEvaluator.ts функцию getIndicatorValues — 
   выпиши ВСЕ type branches (sma, ema, rsi, atr, adx, supertrend, vwap, 
   bollinger_*, constant, fair_value_gap, liquidity_sweep, order_block, 
   market_structure_shift, и т.д.)
2. Прочитай apps/api/src/lib/compiler/supportMap.ts — найди блоки 
   "compile-only" которые уже имеют ветки в getIndicatorValues
3. Промотируй найденные в "supported" с note "Evaluator runtime wired in dslEvaluator"
4. Обнови snapshot в tests/compiler/blockDrift.test.ts (массивы supported и compile-only)
5. Запусти npx vitest run — все тесты должны пройти
6. Закоммить, запушь, создай PR
```

**Ожидаемый результат**: ATR, Bollinger, Constant → supported. Остаются compile-only: macd, volume, and_gate, or_gate, proximity_filter, volume_profile.

---

### 10.2 Implement and_gate + or_gate in evaluator

**Цель**: composed conditions — "RSI > 70 AND SMA cross" в одном сигнале.

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Реализуй composed signal conditions (and_gate, or_gate) в evaluator.
Прочитай текущие типы в dslEvaluator.ts перед изменениями.

1. В dslEvaluator.ts расширь интерфейс DslSignal:
   - Добавь conditions?: DslSignal[] (для type "and" и "or")
2. В evaluateSignal добавь рекурсивные ветки:
   - type === "and" → conditions.every(sub => evaluateSignal(sub, ...))
   - type === "or" → conditions.some(sub => evaluateSignal(sub, ...))
   - Защита от бесконечной рекурсии: maxDepth=5
3. В compiler/blockHandlers.ts проверь что andGateHandler и orGateHandler
   корректно extract'ят sub-conditions из графа
4. Промотируй and_gate, or_gate в supportMap.ts → "supported"
5. Обнови blockDrift.test.ts snapshot
6. Напиши тесты в tests/lib/dslEvaluator.test.ts:
   - and(compare_true, compare_true) → true
   - and(compare_true, compare_false) → false  
   - or(compare_false, compare_true) → true
   - nested: and(or(...), compare)
   - maxDepth exceeded → false
7. Запусти полный тест suite, закоммить, запушь, создай PR
```

---

### 10.3 Implement MACD + Volume in evaluator

**Цель**: MACD histogram и Volume как indicator series в runtime.

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь MACD и Volume в evaluator runtime.

1. Проверь что apps/api/src/lib/indicators/ содержит calcMACD (или macd.ts).
   Если нет — реализуй MACD(fast, slow, signal) → { macd, signal, histogram }.
2. В dslEvaluator.ts добавь в getIndicatorValues:
   - "macd" → MACD histogram series (основной сигнал для compare)
   - "macd_signal" → MACD signal line
   - "volume" → candles.map(c => c.volume)
3. Добавь в IndicatorCache:
   - macd: Map<string, { macd: ..., signal: ..., histogram: ... }>
   - volume: (number|null)[] | null
4. Промотируй macd, volume в supportMap → "supported"
5. Обнови blockDrift.test.ts snapshot
6. Тесты: MACD на uptrend (histogram > 0), volume серия length === candles.length
7. Запусти тесты, закоммить, создай PR
```

---

## Phase 11 — Funding Pipeline (end-to-end)

> **Порядок**: scheduler (данные) → API routes (доступ) → UI (визуализация).
> Без scheduler'а API вернёт пустые результаты. Без API — UI нечего показывать.

### 11.1 Funding ingestion scheduler

**Цель**: cron job, который каждые 8 часов fetches funding rates с Bybit и сохраняет в БД.

**Зависимость**: Phase 9.3 (Prisma migrate — таблицы должны существовать в БД)

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Создай funding rate ingestion job. Используй существующие типы из 
apps/api/src/lib/funding/ (FundingSnapshot, parseFundingHistory, 
buildSpreadFromTickers и т.д.).

1. Создай apps/api/src/lib/funding/fetcher.ts:
   - fetchFundingHistory(symbol: string): Promise<BybitFundingHistoryItem[]>
     GET https://api.bybit.com/v5/market/funding/history?category=linear&symbol=...
   - fetchLinearTickers(): Promise<BybitLinearTicker[]>
     GET https://api.bybit.com/v5/market/tickers?category=linear
   - fetchSpotTickers(): Promise<BybitSpotTicker[]>
     GET https://api.bybit.com/v5/market/tickers?category=spot
   Используй fetch (Node 18+). Добавь try/catch + retry (1 retry).

2. Создай apps/api/src/lib/funding/ingestJob.ts:
   - ingestFundingRates(prisma, symbols: string[]): 
     fetch → parseFundingHistory → prisma.fundingSnapshot.createMany
   - ingestSpreads(prisma):
     fetchLinearTickers + fetchSpotTickers → match по symbol → 
     buildSpreadFromTickers → prisma.spreadSnapshot.createMany
   - runIngestion(prisma): вызывает оба + логирует результат

3. В server.ts зарегистрируй cron (import node-cron):
   cron.schedule("0 */8 * * *", () => runIngestion(prisma))
   pnpm install node-cron @types/node-cron

4. Тесты: мокнутый fetch → parse → правильные FundingSnapshot[]
   (НЕ тестируй реальный HTTP, только парсинг)
5. Закоммить, запушь, создай PR
```

---

### 11.2 Funding API routes

**Цель**: REST endpoints для scanner и funding history.

**Зависимость**: 11.1 (данные в БД)

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь API routes для funding scanner. Используй существующие функции из 
apps/api/src/lib/funding/ (scanFundingCandidates, buildCandidate и т.д.).

1. Создай apps/api/src/routes/funding.ts (или добавь в terminal.ts):

   GET /terminal/funding/scanner
   Query params: minYield (default 5), maxBasis (default 50), 
                 minStreak (default 3), limit (default 10)
   Логика:
   - Для каждого уникального symbol в FundingSnapshot за последние 7 дней:
     загрузи snapshots + последний SpreadSnapshot
   - Построй Map<symbol, {snapshots, spread}>
   - scanFundingCandidates(map, thresholds)
   - Верни JSON: { candidates: FundingCandidate[], updatedAt }

   GET /terminal/funding/:symbol/history
   Query params: from (ISO date), to (ISO date), limit (default 100)
   - prisma.fundingSnapshot.findMany({ where: { symbol, timestamp: { gte, lte } } })
   - Верни JSON: { snapshots: FundingSnapshot[] }

2. Зарегистрируй routes в server.ts
3. Тест: мокнутая Prisma → scanner возвращает ranked candidates
4. Закоммить, запушь, создай PR
```

---

### 11.3 Funding Scanner UI page

**Цель**: фронтенд-страница с таблицей funding arbitrage candidates.

**Зависимость**: 11.2 (API endpoints)

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Создай страницу Funding Scanner. Посмотри существующие страницы в 
apps/web/src/app/ для стиля и layout.

1. Создай apps/web/src/app/terminal/funding/page.tsx:
   - "use client"
   - Fetch GET /api/terminal/funding/scanner с query params
   - Таблица: Symbol | Yield % | Basis (bps) | Streak | Avg Rate | Current Rate
   - Цветовая индикация: зелёный yield > 20%, жёлтый 10-20%, серый < 10%
   - Сортировка по клику на заголовок колонки
   - Фильтры сверху: Min Yield (input), Max Basis (input), кнопка Refresh
   - Loading state + empty state ("No candidates match filters")

2. Добавь ссылку "Funding" в навигацию (найди layout.tsx или sidebar компонент)
3. Закоммить, запушь, создай PR
```

---

## Phase 12 — Evaluator Improvements

### 12.1 Direct sideCondition for discrete signals

**Цель**: SMC паттерны (+1/-1) используются как sideCondition без workaround.

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Добавь "indicator_sign" mode для sideCondition.

1. Прочитай текущую реализацию determineSide в dslEvaluator.ts
2. Расширь DslSideCondition:
   mode?: "price_vs_indicator" | "indicator_sign"
   (default: "price_vs_indicator" — текущее поведение, не ломай backward compat)

3. В determineSide():
   if (sc.mode === "indicator_sign") {
     if (val > 0) return "long";
     if (val < 0) return "short";
     return null;
   }
   // else: текущая логика price vs indicator

4. Обнови docs/schema/strategy.schema.json — добавь mode в sideCondition properties
5. Обнови docs/10-strategy-dsl.md — добавь описание нового mode
6. Тесты:
   - mode="indicator_sign", val=+1 → "long"
   - mode="indicator_sign", val=-1 → "short"
   - mode="indicator_sign", val=0 → null
   - mode=undefined → текущее поведение (backward compat)
7. Закоммить, создай PR
```

---

### 12.2 Unknown indicator type warning

**Цель**: предотвратить silent failures от тайпо в blockType.

**Промт для сессии**:
```
Работай в репо botmarketplace-site.

Маленькая задача (~10 минут).

В apps/api/src/lib/dslEvaluator.ts, в конце функции getIndicatorValues
(где возвращается new Array(candles.length).fill(null) для неизвестного типа):

1. Если apps/api/src/lib/logger.ts уже существует — импортируй logger
   Если нет — создай минимальный: 
   import pino from "pino"; export const logger = pino();
2. Перед return добавь:
   logger.warn({ blockType: type }, "Unknown indicator type — returning nulls")
3. Тест: вызови getIndicatorValues("nonexistent_typo", {}, candles, cache)
   → expect result.every(v => v === null)
4. Закоммить, запушь
```

---

## Порядок выполнения

```
Session 1:  9.1  — non-root + rate limiting
Session 2:  9.2  — health check + logging
Session 3:  9.3  — Prisma migrations + backup
Session 4:  10.1 — audit supportMap (быстрая, ~15 мин)
Session 5:  10.2 — and_gate / or_gate
Session 6:  10.3 — MACD + Volume
Session 7:  12.2 — unknown indicator warning (быстрая, ~10 мин)
Session 8:  12.1 — direct sideCondition
Session 9:  11.1 — funding scheduler
Session 10: 11.2 — funding API routes
Session 11: 11.3 — funding UI
```

**Оценка**: ~11 сессий по 30-60 мин. При 2 сессиях/день ≈ 1 неделя.

**Зависимости**:
- 9.3 → 11.1 (Prisma таблицы нужны для ingestion)
- 9.2 → 12.2 (logger нужен для warning)
- 11.1 → 11.2 → 11.3 (данные → API → UI)
- Остальные сессии независимы

---

## Промт для деплоя (после каждого merge)

> Копируй и вставляй в терминальный Claude Code на VPS после мерджа любого PR.

```
Задеплой последние изменения botmarketplace.ru.

cd /opt/-botmarketplace-site
git pull origin main

# Зависимости (если менялись)
pnpm install

# Prisma (если менялась schema)
npx prisma generate
npx prisma migrate deploy

# Билд API
cd apps/api && npx tsc && cd ../..

# Билд Web
cd apps/web && npx next build && cd ../..

# Рестарт
sudo systemctl restart botmarketplace-api
sleep 3
sudo systemctl restart botmarketplace-web
sleep 3

# Проверка
curl -s -o /dev/null -w "API: %{http_code}\n" http://localhost:4000
curl -s -o /dev/null -w "Web: %{http_code}\n" http://localhost:3000
systemctl is-active botmarketplace-api botmarketplace-web

echo "Deploy complete. Last commit:"
git log --oneline -1
```

---

## Принципы работы с контекстным окном

1. **Одна задача = одна сессия.** Не комбинируй задачи из разных фаз.
2. **Промт содержит всё нужное**: файлы, что делать, в каком порядке.
3. **Максимум 15-20 файлов** на сессию (чтение + запись).
4. **Указывай что НЕ трогать** — "не трогай patterns/, funding/" экономит контекст.
5. **Завершай коммитом** — следующая сессия начинает с чистого состояния.
6. **Self-review** — попроси Claude проревьюить перед мерджем.
7. **Деплой отдельно** — после merge используй промт деплоя выше.
