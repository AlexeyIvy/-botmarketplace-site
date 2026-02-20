# Stage 5 — Research Lab Minimum

## Цель

Реализовать минимальный backtesting модуль:
- исторический replay по свечам Bybit
- детерминированный отчёт (trades, winrate, PnL, max drawdown)
- demo-forward прогон (через существующий bot runtime)

## Acceptance criteria (из docs/15-acceptance-criteria.md)

- [ ] Исторический replay по свечам генерирует отчёт
- [ ] Отчёт содержит: количество сделок, winrate, PnL, max drawdown
- [ ] Отчёт детерминированный (одинаковые данные → одинаковый результат)
- [ ] Demo-forward прогон стратегии записывает события в журнал

## Архитектура

### Backend

1. **DB: `BacktestResult`** — хранит параметры и результаты бэктеста
2. **`lib/bybitCandles.ts`** — загрузка исторических свечей из Bybit public API
3. **`lib/backtest.ts`** — движок симуляции (детерминированный, без IO)
4. **`routes/lab.ts`** — эндпоинты:
   - `POST /api/v1/lab/backtest` — запуск бэктеста
   - `GET  /api/v1/lab/backtest/:id` — статус / результат
   - `GET  /api/v1/lab/backtests` — список для workspace

### Алгоритм симуляции (MVP, детерминированный)

1. Загружаем OHLCV свечи для symbol/interval за указанный период
2. Для каждой свечи вычисляем rolling high (lookback N candles)
3. Сигнал BUY: close[i] > max(close[i-N..i-1])  (price breakout)
4. Если нет открытой позиции → открываем LONG по close[i]
   - SL = entry * (1 − riskPct/100)
   - TP = entry * (1 + 2 × riskPct/100)  (2:1 R/R)
5. На каждой следующей свече:
   - low[j] ≤ SL → закрыть (LOSS)
   - high[j] ≥ TP → закрыть (WIN)
6. Конец периода → закрыть позицию по close (NEUTRAL)
7. Метрики: trades, wins, winrate, totalPnlPct, maxDrawdownPct

Параметры берутся из Strategy DSL (`risk.riskPerTradePct`, дефолт 1.0%).
Lookback N = 20 (фиксировано, MVP).

### Frontend

Lab page (`apps/web/src/app/lab/page.tsx`):
- Форма: workspace, strategy ID, symbol, interval, from/to дата
- Кнопка "Run Backtest"
- Опрос статуса каждые 2с
- Отображение результатов в таблице

## Файлы, затронутые изменениями

```
apps/api/prisma/schema.prisma
apps/api/prisma/migrations/20260220a_add_backtest_result/migration.sql
apps/api/src/lib/bybitCandles.ts          (новый)
apps/api/src/lib/backtest.ts              (новый)
apps/api/src/routes/lab.ts               (новый)
apps/api/src/app.ts
apps/web/src/app/lab/page.tsx
docs/steps/05-stage-5-research-lab.md    (этот файл)
```

## Demo-forward

Demo-forward реализован через существующий BotRun + BotEvent pipeline:
- Пользователь создаёт Bot из стратегии и запускает Run
- BotEvent лог пишет события (signal, order_sent, order_update, ...)
- Lab страница ссылается на Factory для demo-forward запуска
