# SC001-E002 OKX Q1 Replication Results v0.1

Verdict: **OKX_REPLICATION_PASS**  
Parent mechanism: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`  
Protocol commit: `dccf2fd4e95996a77b980e1ca0c3ad0c5662416f`  
Scope: five frozen 2024-Q1 OKX UTC days reconstructed by Q006R

## Primary result

The unchanged 5-second signed trade-flow continuation mechanism replicated on OKX BTC-USDT-SWAP across all five pre-frozen Q1 UTC days.

Primary 100 ms target latency:

- positive daily Spearman: 5 / 5;
- median daily Spearman: `0.062290487275085016`;
- mean daily Spearman: `0.06369241570221684`;
- one-sided sign-test p-value under 50/50 sign null: `0.03125`;
- positive extreme-decile spread days: 5 / 5;
- median extreme-decile spread: `0.2346359937236005` bps;
- event-day median Spearman: `0.062290487275085016`;
- ordinary-day median Spearman: `0.07408369786622518`.

Stress/diagnostic latency:

- 250 ms: 5/5 positive days; median daily Spearman `0.05626737248947782`; median extreme spread `0.217230469236402` bps;
- 500 ms: 5/5 positive days; median daily Spearman `0.05048505656336044`; median extreme spread `0.1797692434073717` bps.

All frozen OKX Q1 replication gates passed.

## Cross-venue interpretation

The Binance reference median daily Spearman on the same five Q1 dates was `0.086705639006201`. The OKX/Binance median-Spearman ratio is about `0.7184`.

This materially reduces the plausibility that the original E002 effect was only a Binance-specific data artifact. It does not prove an executable cross-venue alpha and does not authorize using Binance signals for OKX execution.

## Trade-arrival lag diagnostic

The 100 ms response label uses the first actual trade at or after the target time. On OKX, target-to-next-trade lag is material:

- median of daily median entry lags: about `390 ms`;
- median of daily p95 entry lags: about `2.56 s`;
- median of daily p99 entry lags: about `4.71 s`;
- maximum observed daily entry lag across the five days: `19.339 s`.

Therefore the label is not a literal 100 ms executable-price measurement. The effective observed trade reference often occurs materially later because of trade-arrival sparsity. This strengthens the need for L2 quotes before any execution claim.

## Economic caution

The median 100 ms extreme-decile spread is only about `0.235 bps`. A symmetric tail-trade interpretation implies a gross directional scale of only about half that spread, roughly `0.117 bps` per side before spread, fees, depth impact, slippage, and order-size constraints.

Directional hit rate is weak: the median across the five 100 ms days is about `44.18%`, and the mean is about `43.33%`. The signal therefore continues to look like a return-ranking / payoff-asymmetry feature rather than a high-win-rate classifier.

This is compatible with a real predictive effect but leaves a substantial risk that taker execution economics are negative even if the signal itself is genuine.

## Boundary

- strategy P&L calculated: **NO**;
- execution profitability calculated: **NO**;
- OKX Q2 accessed: **NO**;
- formal Validation accessed: **NO**;
- Final accessed: **NO**.

## Decision

Classification remains a predictive signal with successful cross-venue Q1 replication. Do not promote to `ROBUST_HISTORICAL_CANDIDATE` yet.

Before downloading broad L2 history or opening OKX Q2, freeze the first causal executable-rule/economics design. The rule must not use full-day ex-post deciles. It must define a threshold available at decision time, non-overlapping position logic, exact taker entry/exit semantics, historical fee treatment, depth consumption, latency, and capital-size assumptions. Then test only on already-open Q1 development days with Q2 preserved as same-venue confirmation holdout.
