# SC001-E002 OKX Q1 Post-Replication Expert Review v0.1

Status: **REVIEW COMPLETE**  
Parent result: `SC001-E002-OKX-Q1-REPLICATION = OKX_REPLICATION_PASS`

## What is now established

The unchanged 5-second signed trade-flow continuation feature replicated on OKX across all five frozen 2024-Q1 UTC days. Primary 100 ms daily Spearman was positive 5/5 with median `0.062290487275085016`; extreme-decile spread was positive 5/5 with median `0.2346359937236005` bps. The 250 ms and 500 ms diagnostics also remained positive 5/5.

This materially reduces the probability that E002 is merely a Binance-specific data artifact.

## What is not established

The result is still not an executable strategy and not a profitability claim. The transaction-price response may contain:

- persistent taker-side/order-flow autocorrelation;
- bid/ask bounce and trade-sign persistence;
- delayed next-trade sampling relative to the nominal latency target;
- effects too small to survive fees/spread/depth impact.

## Key new concern: target-to-next-trade lag

At the 100 ms target, the median of the five daily median entry lags is about `390 ms`; daily p95 lags are around `2.1–3.6 s`, daily p99 around `3.6–6.2 s`, and the maximum observed lag is `19.339 s`.

Therefore a label called `100 ms` is actually a transaction-price reference at the first print at or after `t+100ms`, often materially later. This is valid for a predictive screen but cannot be interpreted as an executable fill price at 100 ms.

## Economic scale

Median 100 ms top-minus-bottom extreme-decile response on OKX is `0.2346359937236005` bps. A symmetric long-upper-tail / short-lower-tail interpretation has an approximate gross directional scale of only half that, about `0.1173` bps per trade side before any real execution cost.

This is small enough that a genuine predictive signal can still be economically unusable as a taker strategy.

## Directional hit-rate interpretation

At 100 ms the median daily extreme-tail directional hit rate is about `44.18%` and the mean about `43.33%`. The feature therefore appears to earn its mean-response separation through payoff asymmetry / magnitude ranking rather than a high win probability.

This is not a contradiction, but it raises tail-risk and cost-sensitivity concerns for any future trading rule.

## Optimization of the next stage

Do **not** jump directly from transaction-price replication to threshold tuning and P&L.

The next falsification should first ask:

> Does the same trade-flow signal predict **future OKX midquote movement** when the reference price comes from replayed L2 rather than the next trade print?

This directly attacks the strongest alternative explanation: bid/ask bounce and trade-sign persistence.

Only if the midquote effect survives should SC001 define a causal online threshold and test full taker execution economics.

## Firewall

- OKX Q2 remains unopened;
- formal Validation remains unopened;
- Final remains unopened;
- no post-hoc threshold selection is authorized;
- current full-day deciles remain diagnostics only and may not become a live rule.

## Next action

Run a metadata-only exact-date preflight for the five frozen Q1 OKX L2 archives. Do not download archive bodies until exact sizes are known and safe staged batches can be frozen under the 2 GB/run protection.
