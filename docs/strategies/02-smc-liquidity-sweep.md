# Стратегия 1: SMC Liquidity Sweep + FVG + Order Block

> **Приоритет:** 🥇 Флагман #1 — институциональный уровень  
> **Аудитория:** Профессиональные трейдеры  
> **Edge:** Единственный подход, объясняющий *почему* движется цена — охота за ликвидностью

> **Implementation status:** delivered as `smc-liquidity-sweep` preset — see `docs/54-T3`.
> DSL: `apps/api/prisma/seed/presets/smc-liquidity-sweep.json`.
> Golden fixture: `apps/api/tests/fixtures/strategies/smc-liquidity-sweep.golden.json`.
> Visibility in Lab Library: PUBLIC.

## Концепция

**Smart Money Concepts (SMC)** основана на том, что институциональные игроки намеренно «охотятся» за стоп-лоссами розничных трейдеров, чтобы получить ликвидность для своих позиций. Liquidity Sweep — это момент, когда цена пробивает значимый уровень (собирает стопы) и резко разворачивается. Именно в этой точке открывается сделка.

## Доказанные метрики

| Метрика | Значение |
|---|---|
| Win Rate | 36–59% |
| Risk:Reward | 1:3 — 1:5 |
| Мат. ожидание | +0.5–1.5% за сделку |
| Sharpe (est.) | 2.0–3.0 |
| Годовая доходность | 50–120% |
| Max Drawdown | 20–30% |
| Таймфрейм входа | 1m / 5m |
| Таймфрейм структуры | 15m / 1H |

## Логика стратегии (шаги)

```
Шаг 1: Определить ликвидность
   → PDH / PDL (Previous Day High / Low)
   → PWH / PWL (Previous Week High / Low)
   → Session High / Low (London, NY)
   → Equal Highs / Equal Lows (ретейл стопы)

Шаг 2: Дождаться Liquidity Sweep
   → Цена пробивает уровень ликвидности
   → Свеча закрывается ОБРАТНО за пробитый уровень (ложный пробой)
   → Подтверждение: объём на свече свипа выше среднего

Шаг 3: Подтвердить через Market Structure Shift (MSS)
   → После свипа — смена структуры рынка (Break of Structure)
   → Displacement: мощная направленная свеча после свипа

Шаг 4: Войти в зоне FVG или Order Block
   → FVG: разрыв между свечами (imbalance zone)
   → OB: последняя противоположная свеча перед импульсом
   → Вход на ретесте FVG/OB

Шаг 5: Risk Management
   → Stop Loss: за вик свечи-свипа (ниже всего свипа)
   → Take Profit: до противоположной ликвидности
   → R:R минимум 1:3, целевой 1:5
```

## Параметры стратегии

| Параметр | Значение |
|---|---|
| Entry Type | FVG (Fair Value Gap) или Order Block (OB) |
| Stop Loss | За вик Liquidity Sweep свечи |
| Take Profit | Противоположный уровень ликвидности |
| Min Risk:Reward | 1:3 |
| Target Risk:Reward | 1:5 |
| Risk per Trade | 0.5–1% депозита |
| Kill Zones | London Open: 08:00–10:00 UTC, NY Open: 13:30–15:30 UTC |
| Лучшие символы | BTCUSDT, ETHUSDT, SOLUSDT |
| Таймфрейм входа | 1m / 5m |
| Таймфрейм структуры | 15m / 1H / 4H |
| Лучшие условия | Высокая ликвидность, начало сессий |

## Kill Zones (лучшее время для торговли)

```
Азиатская сессия:  00:00–03:00 UTC  (накопление, тихий рынок)
London Open:       07:00–10:00 UTC  ⭐ ЛУЧШЕЕ ВРЕМЯ
NY Open:           12:00–15:00 UTC  ⭐ ЛУЧШЕЕ ВРЕМЯ
London Close:      15:00–17:00 UTC  (часто реверсы)
```

## Необходимые DSL-блоки

| Блок | Описание | Приоритет |
|---|---|---|
| `LiquiditySweep` | Детектор свипа: PDH/PDL, session H/L, equal highs/lows | 🔵 P2 |
| `FairValueGap` | Определение FVG (imbalance) между 3 свечами | 🔵 P2 |
| `OrderBlock` | Последняя противоположная свеча перед импульсом | 🔵 P2 |
| `MarketStructureShift` | Детектор смены структуры (BOS / CHoCH) | 🔵 P2 |
| `MultiTimeframe` | Получение данных с другого таймфрейма | 🔵 P2 |
| `SessionFilter` | Kill Zones — фильтр торговых сессий | 🟡 P1 |
| `VWAP` | Session VWAP как дополнительный bias | 🔴 P0 |

## DSL JSON (концептуальный, после реализации блоков)

```json
{
  "dslVersion": 2,
  "name": "SMC Liquidity Sweep + FVG",
  "market": { "exchange": "bybit", "env": "demo", "category": "linear", "symbol": "BTCUSDT" },
  "timeframes": ["1m", "5m", "15m", "1H"],
  "entry": {
    "indicators": [
      { "type": "LiquiditySweep", "lookback": 20 },
      { "type": "FairValueGap", "minSize": 0.1 },
      { "type": "VWAP", "period": "session" },
      { "type": "SessionFilter", "killZones": ["london_open", "ny_open"] }
    ],
    "signal": { "type": "liquidity_sweep_fvg_entry" },
    "side": "Buy",
    "stopLoss": { "type": "sweep_wick" },
    "takeProfit": { "type": "opposite_liquidity", "minRR": 3.0 }
  },
  "risk": {
    "maxPositionSizeUsd": 500,
    "riskPerTradePct": 0.5,
    "cooldownSeconds": 300
  },
  "guards": {
    "maxOpenPositions": 1,
    "maxOrdersPerMinute": 3,
    "pauseOnError": true
  }
}
```

## Связанные Issues

- `[DSL] Add LiquiditySweep detector`
- `[DSL] Add FairValueGap (FVG) block`
- `[DSL] Add OrderBlock (OB) block`
- `[DSL] Add MultiTimeframe (MTF) context support`
- `[DSL] Add SessionFilter (Kill Zones) block`
