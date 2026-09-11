# SC001 staged acquisition review v0.1

Date: 2026-09-11
Status: FROZEN BEFORE MICROSTRUCTURE P&L

## Decision after cross-disciplinary review

The Q004R result is strong enough to establish deterministic OKX price-level replay on the sampled prefixes, but it is not a reason to download all 70 frozen L2 days immediately.

A full OKX L2 day is computationally expensive on Android: Q004R prefixes imply millions of JSONL book records per day, and the daily compressed archives can be hundreds of MB while the decompressed member is several GB. Therefore bulk L2-first acquisition would create unnecessary phone-runtime, battery, network and storage risk before a strategy hypothesis exists.

The acquisition order is revised to a cheap-to-expensive funnel:

1. Binance BTCUSDT USD-M 1m DEV backbone first.
2. Binance/Bybit trade-level data only for frozen DEV acquisition days, staged one day at a time.
3. One full-day OKX L2 engineering pilot on the earliest frozen DEV acquisition day before any multi-day L2 campaign.
4. Additional OKX L2 DEV days only when required by a preregistered L2 hypothesis or execution audit.
5. VALIDATION remains unopened at minute/tick/L2 resolution until a DEV hypothesis and implementation are frozen.
6. FINAL remains unopened at minute/tick/L2 resolution until the candidate has passed VALIDATION and is frozen for one-shot final evaluation.

## Statistical corrections

The 70-day frozen calendar intentionally oversamples CPI/NFP/FOMC days relative to their natural calendar frequency. Therefore a naive pooled average across the 70 days is forbidden as an estimator of real-world unconditional P&L. Event and non-primary-event strata must be reported separately unless an explicit natural-calendar weighting rule is preregistered.

`ORDINARY_WEEKDAY` / `ORDINARY_WEEKEND` means only that the day is not one of the three selected primary event classes. It does not mean "news-free". Other macro, regulatory or crypto-specific events may occur and must not be silently relabeled away.

For event-versus-control comparisons, time-of-day seasonality must be controlled. Primary event windows are anchored to the official event time. Matched non-event controls must use comparable local-US time anchors rather than arbitrary full-day averages.

Inference must be clustered/block-based at the day or event level. Individual book updates or trades are not independent observations.

## Execution boundary

Primary execution research remains taker-first. OKX L2 supports spread, depth, imbalance, deterministic price-level replay and conservative taker sweep modeling. It does not establish exact maker queue priority or MBO position.

Latency must not be modeled as zero in the primary case. The frozen primary/stress concept remains 100 ms / 250 ms / 500 ms unless a later, separately frozen infrastructure measurement justifies a new experiment.

## Unit-normalization boundary

OKX derivative book size is contract-based. Historical research must retain native contract units. Conversion to BTC/notional is secondary and requires validated contract metadata. Current instrument metadata must not be silently projected backward if a historical rule change cannot be ruled out.

## Immediate next stage

`SC001-DATA-A001`: acquire and validate only the DEV portion of the Binance BTCUSDT USD-M 1m backbone, using official monthly archives and official checksums. No strategy/P&L is permitted.
