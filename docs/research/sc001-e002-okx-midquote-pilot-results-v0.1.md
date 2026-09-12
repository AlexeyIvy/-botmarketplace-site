# SC001-E002 OKX Midquote Falsification Pilot — Results v0.1

Status: **MIDQUOTE_PILOT_PASS**  
Date: `2024-01-05`  
Parent mechanism: `SC001-E002 — 5s signed aggressive trade-flow continuation`

## Frozen result

The same frozen 5-second TFI mechanism remained predictive when the response variable was changed from next transaction price to L2 midquote, using only the last known book state at or before each target timestamp.

Primary 100 ms:
- valid decisions: 17,109;
- Spearman: `0.04767461418486088`;
- top-minus-bottom extreme-decile spread: `0.2494863426605216` bps;
- directional hit rate: `0.387719298245614`;
- top-decile mean response: `+0.15451294973881496` bps;
- bottom-decile mean response: `-0.09497339292170666` bps.

Stress / diagnostic:
- 250 ms Spearman: `0.04284156950029477`; spread `0.22937729201537227` bps;
- 500 ms Spearman: `0.03415604185428452`; spread `0.18237129288011134` bps.

The effect decays monotonically as latency increases.

## Comparison with same-day transaction-price replication

On the same OKX UTC day, the prior transaction-price screen produced approximately:
- 100 ms Spearman `0.04404785981292113`;
- 100 ms extreme-decile spread `0.2346359937236005` bps.

The midquote pilot is therefore not weaker on this day: Spearman is about 8.2% higher and the extreme spread about 6.3% higher. This materially weakens the hypothesis that the E002 effect is merely bid/ask bounce or persistence of trade-side prints.

This is still one already observed pilot day and is not sufficient to establish multi-day midquote robustness.

## L2 state freshness diagnostic

At 100 ms target times, age of the last known valid L2 state was:
- median: `5 ms`;
- p95: `16 ms`;
- p99: `32 ms`;
- maximum: `85,412 ms`.

The first three statistics show that almost all target states are very fresh. The rare long maximum corresponds to the full-day replay's already observed long inter-record gap and must remain visible as a diagnostic. No post-hoc age filter is applied to this pilot result.

## Critical interpretation

The most important positive finding is that the signal survives transition from transaction prices to an L2 midpoint reference. That is stronger evidence of a real short-horizon price-response relationship.

The main negative finding remains economic magnitude. A roughly `0.2495 bps` top-minus-bottom gross midquote spread still corresponds only to about `0.125 bps` per side under a simplistic symmetric long/short interpretation, before spread crossing, taker fees, depth consumption, slippage and sizing.

Directional hit rate remains well below 50%, reinforcing that TFI behaves as a conditional-return ranking / magnitude signal rather than a high-win-rate classifier.

## Firewall state

- execution profitability calculated: **NO**;
- strategy P&L calculated: **NO**;
- 2024-Q2 OKX accessed: **NO**;
- formal Validation accessed: **NO**;
- Final accessed: **NO**.

## Decision

Do not promote to an executable strategy yet. Freeze a four-day Q1 midquote confirmation protocol on the remaining preselected Q1 days, then acquire/replay those L2 archives in batches below the 2 GB phone cap. Do not inspect partial-batch alpha before all four confirmation days are qualified.
