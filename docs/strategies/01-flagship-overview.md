# Flagship Strategies — Обзор

> Данный документ описывает 5 флагманских стратегий для Bot Marketplace.  
> Платформа строится **под стратегии**, а не стратегии под платформу.

## Критерии отбора

Все стратегии отобраны по трём критериям:
1. **Доказанная edge** — задокументированные результаты live/backtest с Sharpe > 1.5
2. **Масштабируемость** — работают в автоматическом режиме без ручного вмешательства
3. **Маркетинговая ценность** — каждая стратегия покрывает отдельный сегмент аудитории

## Сводная таблица

| # | Стратегия | Доходность (год) | Max DD | Sharpe | Аудитория | Документ |
|---|---|---|---|---|---|---|
| 🥇 | SMC Liquidity Sweep + FVG + OB | 50–120% | 20–30% | 2.0–3.0 | Профессионалы | [02-smc-liquidity-sweep.md](./02-smc-liquidity-sweep.md) |
| 🥈 | Adaptive Regime Bot | 28–65% | 10–20% | 1.8–2.5 | Продвинутые | [03-adaptive-regime-bot.md](./03-adaptive-regime-bot.md) |
| 🥉 | Funding Rate Arbitrage | ~19% | 0.85% | 5.0+ | Консерваторы | [04-funding-arbitrage-delta-hedge.md](./04-funding-arbitrage-delta-hedge.md) |
| 4 | MTF Confluence Scalper | 30–80% | 8–15% | 4.6–5.5 | Профессионалы | [05-mtf-confluence-scalper.md](./05-mtf-confluence-scalper.md) |
| 5 | DCA Momentum Bot | ~245% / 4 года | 12% | 1.8 | Новички | [06-dca-momentum-bot.md](./06-dca-momentum-bot.md) |

## Покрытие аудитории

```
Новички       →  DCA Momentum Bot          (простой вход, авто-усреднение)
Консерваторы  →  Funding Rate Arbitrage    (нейтральный рынок, 0.85% DD)
Продвинутые   →  Adaptive Regime Bot       (умный бот, сам выбирает режим)
Профессионалы →  MTF Confluence Scalper    (институциональный скальпинг)
Профессионалы →  SMC Liquidity Sweep       (институциональный flow, топ edge)
```

## DSL-блоки, необходимые для реализации

См. полный список в разделе [Roadmap DSL-блоков](#roadmap-dsl-блоков).

### Roadmap DSL-блоков

| Приоритет | Блок | Нужен для |
|---|---|---|
| 🔴 P0 | `VWAP` (session reset) | MTF Scalper, SMC |
| 🔴 P0 | `SuperTrend` (ATR + Factor) | Adaptive Regime |
| 🔴 P0 | `ADX` (режим-детектор) | Adaptive Regime |
| 🟡 P1 | `VolumeProfile` (POC, VAH, VAL) | MTF Scalper |
| 🟡 P1 | `FundingRate` (datasource) | Funding Arb |
| 🟡 P1 | `DCA` (safety orders, step%) | DCA Bot |
| 🔵 P2 | `LiquiditySweep` (PDH/PDL) | SMC |
| 🔵 P2 | `FairValueGap` (FVG) | SMC |
| 🔵 P2 | `OrderBlock` (OB) | SMC |
| 🔵 P2 | `MultiTimeframe` (MTF context) | SMC, MTF Scalper |

## Связанные документы

- [Strategy DSL (текущий MVP)](../10-strategy-dsl.md)
- [Bot Runtime](../11-bot-runtime.md)
- [Functional Requirements](../02-requirements-functional.md)
