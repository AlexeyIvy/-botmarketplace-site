# Стратегия 4: MTF Confluence Scalper

> **Приоритет:** 4️⃣ Флагман #4 — институциональный скальпинг  
> **Аудитория:** Профессиональные трейдеры  
> **Edge:** Вход только при совпадении 3 независимых инструментов — highest win rate среди скальп-стратегий

> **Implementation status:** delivered as `mtf-scalper` preset — see `docs/54-T2`.
> DSL: `apps/api/prisma/seed/presets/mtf-scalper.json`.
> Golden fixture: `apps/api/tests/fixtures/strategies/mtf-scalper.golden.json`.
> Visibility in Lab Library: PUBLIC.

## Концепция

**Конфлюэнс** — это совпадение нескольких независимых инструментов в одной точке. VWAP показывает «справедливую цену» сессии, Volume Profile (POC/VAH/VAL) — зоны максимальной рыночной активности, RSI(3) — мгновенный тайминг перегрева/перепроданности. Вход только когда все три одновременно указывают в одну сторону.

## Доказанные метрики

| Метрика | Значение |
|---|---|
| Win Rate | **~78%** |
| Sharpe Ratio (live) | **4.64–5.5** |
| Годовая доходность | 30–80% |
| Max Drawdown | 8–15% |
| Avg trades/day | 5–15 |
| Таймфрейм входа | 1m |

## Логика конфлюэнса

```
CONFLUENCE LONG (все 3 условия обязательны):
✅ Условие 1 — VWAP Bias:
   Цена ВЫШЕ Session VWAP → бычий контекст сессии

✅ Условие 2 — Volume Profile Support:
   Цена находится У зоны POC или VAL (±0.1–0.15%)
   → Зона максимального объёма = реальная поддержка

✅ Условие 3 — RSI(3) Timing:
   RSI(3) < 30 и начинает разворачиваться вверх
   → Локальная перепроданность в контексте восходящего тренда

→ Все 3 условия = ВЫСОКОКАЧЕСТВЕННЫЙ СИГНАЛ → Вход Long

CONFLUENCE SHORT — зеркально:
✅ Цена НИЖЕ Session VWAP
✅ Цена у VAH или POC (сверху)
✅ RSI(3) > 70 и разворачивается вниз
```

## Параметры стратегии

| Параметр | Значение |
|---|---|
| VWAP | Session (ежедневный сброс в 00:00 UTC) |
| Volume Profile | Session VP: POC, VAH (Value Area High), VAL (Value Area Low) |
| Value Area | 70% объёма сессии |
| RSI Period | **3** (сверхбыстрый) |
| RSI Oversold / OB | 30 / 70 |
| Proximity к POC/VAL | ±0.1–0.15% от уровня |
| Вход | Закрытие 1m свечи с подтверждением |
| Stop Loss | За POC / за VAL / за структурный уровень |
| Take Profit 1 | Ближайшая VWAP линия |
| Take Profit 2 | До противоположной границы Value Area |
| Альтернативный TP | 2 × ATR(14) |
| Таймфрейм входа | **1m** |
| Таймфрейм контекста | **5m** (режим рынка), **15m** (структура) |
| Лучшие символы | BTCUSDT, ETHUSDT |
| Лучшее время | London Open и NY Open |

## Мультитаймфреймовый фреймворк

```
15m  →  Определить режим рынка (тренд/боковик через EMA 50/200)
 5m  →  Подтвердить направление VWAP и Volume Profile зоны
 1m  →  Точка входа: RSI(3) сигнал у объёмного уровня
```

**Правило:** 5m говорит «куда», 1m говорит «когда».

## Необходимые DSL-блоки

| Блок | Описание | Приоритет |
|---|---|---|
| `VWAP` | Session VWAP с ежедневным сбросом | 🔴 P0 |
| `VolumeProfile` | Сессионный Volume Profile: POC, VAH, VAL | 🟡 P1 |
| `RSI` | Уже есть в DSL v1 — использовать Period=3 | ✅ Готово |
| `ProximityFilter` | Фильтр близости к уровню (±N%) | 🟡 P1 |
| `MultiTimeframe` | Контекст 5m/15m внутри 1m стратегии | 🔵 P2 |
| `ATR` | Динамический TP/SL по волатильности | 🟡 P1 |

## DSL JSON (концептуальный, после реализации блоков)

```json
{
  "dslVersion": 2,
  "name": "MTF Confluence Scalper — BTC 1m",
  "market": { "exchange": "bybit", "env": "demo", "category": "linear", "symbol": "BTCUSDT" },
  "timeframes": ["1m", "5m", "15m"],
  "entry": {
    "indicators": [
      { "type": "VWAP", "period": "session" },
      { "type": "VolumeProfile", "period": "session", "valueAreaPct": 70 },
      { "type": "RSI", "length": 3 },
      { "type": "ATR", "length": 14 }
    ],
    "signal": {
      "type": "confluence",
      "conditions": [
        { "op": "gt", "left": "close", "right": "VWAP" },
        { "op": "near", "left": "close", "right": "VP_POC", "tolerance": 0.0015 },
        { "op": "lt", "left": "RSI_3", "right": 30 }
      ],
      "requireAll": true
    },
    "side": "Buy",
    "stopLoss": { "type": "structural", "reference": "VP_VAL" },
    "takeProfit": { "type": "atr_multiple", "atrMultiple": 2.0 }
  },
  "risk": {
    "maxPositionSizeUsd": 200,
    "riskPerTradePct": 0.3,
    "cooldownSeconds": 60
  },
  "guards": {
    "maxOpenPositions": 1,
    "maxOrdersPerMinute": 10,
    "pauseOnError": true
  }
}
```

## Связанные Issues

- `[DSL] Add VWAP indicator block (session-based)`
- `[DSL] Add VolumeProfile block (POC/VAH/VAL)`
- `[DSL] Add MultiTimeframe (MTF) context support`
- `[DSL] Add ATR indicator block`
