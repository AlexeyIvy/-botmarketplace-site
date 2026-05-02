# Стратегия 2: Adaptive Regime Bot

> **Приоритет:** 🥈 Флагман #2 — умный бот с автопереключением режимов  
> **Аудитория:** Продвинутые трейдеры  
> **Edge:** Единственная стратегия, которая не «ломается» при смене режима рынка

> **Implementation status:** delivered as `adaptive-regime` preset — see `docs/53`.
> DSL: `apps/api/prisma/seed/presets/adaptive-regime.json`.
> Golden fixture: `apps/api/tests/fixtures/strategies/adaptive-regime.golden.json`.
> Visibility in Lab Library: PUBLIC.

## Концепция

Большинство ботов «ломаются» при смене рыночного режима: трендовые стратегии теряют деньги в боковике, и наоборот. Adaptive Regime Bot автоматически определяет текущий режим через ADX и активирует соответствующую подстратегию.

## Доказанные метрики

| Метрика | Тренд-режим | Боковой режим | Общие |
|---|---|---|---|
| Win Rate | 65% | 67% | ~66% |
| Profit Factor | 2.3 | 1.6–2.1 | ~2.0 |
| Sharpe Ratio | 1.8 | 2.1 | ~1.9–2.5 |
| Годовая доходность | 28–65% | — | 28–65% |
| Max Drawdown | 10–20% | — | 10–20% |

## Логика режимов

```
ADX(14) > 25  →  Режим "ТРЕНД"
   Активна: SuperTrend (ATR 55, Factor 2.0) + EMA 200 (MTF 1H)
   Логика:  Следуем тренду, входим на откатах

ADX(14) < 20  →  Режим "БОКОВИК"
   Активна: Bollinger Bands (20, 2σ) + RSI(3)
   Логика:  Покупаем на нижней полосе BB + RSI < 30
            Продаём на верхней полосе BB + RSI > 70

20 ≤ ADX ≤ 25  →  Режим "ПЕРЕХОД"
   Действие: НЕ открываем новые сделки, ждём чёткого режима
   Защита:   Управляем только уже открытыми позициями
```

## Параметры по режимам

### Тренд-режим: SuperTrend + EMA 200

| Параметр | Значение |
|---|---|
| SuperTrend ATR Period | **55** (5m BTC/ETH) |
| SuperTrend Factor | **2.0** |
| EMA (MTF фильтр) | **200** на 1H таймфрейме |
| Вход Long | Цена выше EMA 200 (1H) + SuperTrend зелёный |
| Вход Short | Цена ниже EMA 200 (1H) + SuperTrend красный |
| Stop Loss | За ближайший swing high/low |
| Take Profit | При смене цвета SuperTrend ИЛИ 3×ATR |
| Таймфрейм | 5m |

### Боковой режим: BB + RSI(3)

| Параметр | Значение |
|---|---|
| Bollinger Bands Period | **20** |
| BB Std Dev | **2.0** |
| RSI Period | **3** (сверхбыстрый) |
| RSI Oversold | **30** (вход Long) |
| RSI Overbought | **70** (вход Short) |
| Вход Long | Цена касается нижней BB + RSI < 30 + разворот |
| Вход Short | Цена касается верхней BB + RSI > 70 + разворот |
| Stop Loss | За пробой BB на 0.5% |
| Take Profit | Средняя линия BB (mean reversion) |
| Таймфрейм | 5m |

## Альткоины: адаптация параметров

Для активов с более высокой волатильностью (SOL, BNB, альты):

| Параметр | BTC/ETH | Альткоины |
|---|---|---|
| SuperTrend ATR | 55 | 10–14 |
| SuperTrend Factor | 2.0 | 3.5–4.5 |
| BB Std Dev | 2.0 | 2.5 |
| Risk per Trade | 0.5% | 0.3% |

## Необходимые DSL-блоки

| Блок | Описание | Приоритет |
|---|---|---|
| `SuperTrend` | ATR-based trend indicator (ATR period + factor) | 🔴 P0 |
| `ADX` | Average Directional Index — детектор режима рынка | 🔴 P0 |
| `BollingerBands` | Уже планируется в DSL MVP — уточнить реализацию | 🔴 P0 |
| `MultiTimeframe` | Получение EMA 200 с таймфрейма 1H | 🔵 P2 |
| `RegimeSwitcher` | Логический блок переключения подстратегий | 🔵 P2 |

## DSL JSON (концептуальный, после реализации блоков)

```json
{
  "dslVersion": 2,
  "name": "Adaptive Regime Bot — BTC 5m",
  "market": { "exchange": "bybit", "env": "demo", "category": "linear", "symbol": "BTCUSDT" },
  "timeframes": ["5m", "1H"],
  "entry": {
    "indicators": [
      { "type": "ADX", "length": 14 },
      { "type": "SuperTrend", "atrPeriod": 55, "factor": 2.0 },
      { "type": "EMA", "length": 200, "timeframe": "1H" },
      { "type": "BollingerBands", "period": 20, "stdDev": 2.0 },
      { "type": "RSI", "length": 3 }
    ],
    "signal": {
      "type": "regime_adaptive",
      "trendCondition": { "op": "gt", "left": "ADX_14", "right": 25 },
      "trendSignal": { "type": "supertrend_direction", "confirmWith": "EMA_200_1H" },
      "rangeCondition": { "op": "lt", "left": "ADX_14", "right": 20 },
      "rangeSignal": { "type": "bb_rsi_reversion", "rsiOversold": 30, "rsiOverbought": 70 }
    },
    "side": "Buy",
    "stopLoss": { "type": "swing", "lookback": 10 },
    "takeProfit": { "type": "supertrend_flip_or_bb_midline" }
  },
  "risk": {
    "maxPositionSizeUsd": 300,
    "riskPerTradePct": 0.5,
    "cooldownSeconds": 120
  },
  "guards": {
    "maxOpenPositions": 1,
    "maxOrdersPerMinute": 5,
    "pauseOnError": true
  }
}
```

## Связанные Issues

- `[DSL] Add SuperTrend indicator block (ATR + Factor)`
- `[DSL] Add ADX indicator block (regime detection)`
- `[DSL] Add MultiTimeframe (MTF) context support`
