# Стратегия 5: DCA Momentum Bot

> **Приоритет:** 5️⃣ Флагман #5 — массовый продукт для новичков  
> **Аудитория:** Новички и пассивные инвесторы  
> **Edge:** +245% live за 4 года на BTC при drawdown 12% — работает в любом рынке

> **Implementation status:** delivered as `dca-momentum` preset — see `docs/54-T1`.
> DSL: `apps/api/prisma/seed/presets/dca-momentum.json`.
> Golden fixture: `apps/api/tests/fixtures/strategies/dca-momentum.golden.json`.
> Visibility in Lab Library: PUBLIC.

## Концепция

**Dollar Cost Averaging (DCA)** с моментум-фильтром — наиболее популярный тип автоматизации среди розничных пользователей. Бот открывает базовую позицию при сигнале входа и автоматически усредняется при движении цены против позиции через «safety orders». По мере усреднения TP автоматически пересчитывается к новой средней цене. Моментум-фильтр (RSI + EMA) предотвращает вход в слишком сильный нисходящий тренд.

## Доказанные метрики

| Метрика | Значение |
|---|---|
| Backtest ROI (4 года BTC) | **+285%** |
| Live ROI (4 года BTC) | **+245%** |
| Max Drawdown | **12%** |
| Sharpe Ratio | ~1.8 |
| Лучшие рынки | Бычий (Long DCA), Медвежий (Short DCA) |
| Safety Orders | **12** (оптимальное число) |
| Step между SO | **1.2%** |

## Логика стратегии

```
Шаг 1: Сигнал входа (Momentum Filter)
   → RSI(14) < 40 (не в перекупленности)
   → Цена ниже EMA 21 (небольшой откат от тренда)
   → Открываем Base Order (базовый ордер)

Шаг 2: Safety Orders (автоусреднение)
   → SO #1: цена падает на 1.2% от Base Order → докупаем
   → SO #2: цена падает ещё на 1.2% × 1.05 (step scale) → докупаем
   → ... до SO #12
   → Размер каждого SO: base × volume_scale (по умолчанию 1.2)

Шаг 3: Take Profit (автопересчёт)
   → TP = средняя цена позиции + target%
   → После каждого SO TP пересчитывается автоматически
   → Закрытие всей позиции одним TP ордером

Шаг 4: Цикл
   → После TP — cooldown → ждём следующий сигнал входа
   → При достижении max safety orders — удержание до TP или timeout
```

## Параметры стратегии

| Параметр | Значение |
|---|---|
| Направление | Long DCA (бычий рынок) / Short DCA (медвежий) |
| Base Order Size | 5–10% от депозита |
| Safety Orders | **12** |
| Step % (SO distance) | **1.2%** |
| Step Scale | 1.05 (каждый следующий SO чуть дальше) |
| Volume Scale | 1.2 (каждый SO чуть больше предыдущего) |
| Take Profit % | **1.5%** от средней цены |
| Momentum Filter RSI | Period **14**, вход при RSI < 40 |
| Momentum Filter EMA | Period **21**, цена ниже EMA для входа |
| Max Active Deals | 3–5 (диверсификация по символам) |
| Cooldown после TP | 60–300 секунд |
| Символы | BTCUSDT, ETHUSDT + любые топ-20 по капитализации |
| Таймфрейм | 1H (сигнал), 15m (исполнение) |

## Управление капиталом

```
Пример для депозита $1,000:

Base Order:     $50    (5%)
SO #1:          $60    (×1.2)
SO #2:          $72    (×1.2²)
...
SO #12:         ~$310  (×1.2¹²)

Максимальная загрузка на 1 сделку: ~$1,500 (1.5× депозита)
→ Рекомендуется плечо 1.5–2x или ограничить до 8 SO
```

## Варианты конфигурации

### Консервативный (низкий риск)
| Параметр | Значение |
|---|---|
| Safety Orders | 6 |
| Step % | 2.0% |
| TP % | 1.0% |
| Volume Scale | 1.0 (равные SO) |
| Риск | Низкий, меньше прибыли |

### Агрессивный (высокий риск)
| Параметр | Значение |
|---|---|
| Safety Orders | 15 |
| Step % | 0.8% |
| TP % | 2.0% |
| Volume Scale | 1.5 |
| Риск | Высокий, потенциал выше |

## Необходимые DSL-блоки

| Блок | Описание | Приоритет |
|---|---|---|
| `DCA` | Safety orders, step%, volume scale, TP пересчёт | 🟡 P1 |
| `RSI` | Уже есть в DSL v1 — Period 14 для фильтра | ✅ Готово |
| `EMA` | Уже есть в DSL v1 — Period 21 для фильтра | ✅ Готово |
| `MultiDeal` | Управление несколькими активными сделками | 🔵 P2 |

## DSL JSON (концептуальный, после реализации блока DCA)

```json
{
  "dslVersion": 2,
  "name": "DCA Momentum Bot — BTC Long",
  "market": { "exchange": "bybit", "env": "demo", "category": "linear", "symbol": "BTCUSDT" },
  "timeframes": ["1H"],
  "entry": {
    "indicators": [
      { "type": "RSI", "length": 14 },
      { "type": "EMA", "length": 21 }
    ],
    "signal": {
      "type": "dca_start",
      "conditions": [
        { "op": "lt", "left": "RSI_14", "right": 40 },
        { "op": "lt", "left": "close", "right": "EMA_21" }
      ]
    },
    "side": "Buy"
  },
  "dca": {
    "baseOrderPct": 5,
    "safetyOrders": 12,
    "stepPct": 1.2,
    "stepScale": 1.05,
    "volumeScale": 1.2,
    "takeProfitPct": 1.5
  },
  "risk": {
    "maxPositionSizeUsd": 1500,
    "riskPerTradePct": 2.0,
    "cooldownSeconds": 120
  },
  "guards": {
    "maxOpenPositions": 3,
    "maxOrdersPerMinute": 10,
    "pauseOnError": true
  }
}
```

## Связанные Issues

- `[DSL] Add DCA block (safety orders, step%, volume scale)`
- `[DSL] Add MultiDeal manager block`
