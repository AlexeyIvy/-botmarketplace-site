# SC001 — Independent Base Concepts B1/B2/B3 Non-Alpha Comparative Review v0.1

Date: 2026-09-18
Status: **COMPARATIVE REVIEW COMPLETE / TWO BASES SELECTED / NO OUTCOME OPENED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-independent-base-opportunity-design-brief-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-base-b1-macro-release-impulse-feasibility-card-v0.1.md`;
- `docs/research/sc001-base-b2-triangular-spot-parity-feasibility-card-v0.1.md`;
- `docs/research/sc001-base-b3-stablecoin-parity-feasibility-card-v0.1.md`.

## 1. Review objective

Select at most one or two genuinely independent base opportunities for C11+ assignment without opening historical strategy outcomes.

## 2. B1 — Scheduled Tier-1 US Macro Release Impulse

Independence:

PASS.

The event clock is external and official. It does not depend on C1-C10 features.

Economic payer:

Forced repricing after scheduled macro information arrival.

Execution structure:

- two fills;
- short hold;
- no paired-leg burden.

Edge-to-Fill:

- preliminary burden ~20 bps including event slippage reserve;
- mechanism has a credible reason for tens-of-bps movement on some scheduled releases;
- exact frequency/headroom remains unknown until frozen sentinel.

Data:

- official release calendars are public;
- BTC trade data are public/available in SC001 infrastructure.

Risks:

- event slippage;
- sparse independent event count;
- strong clustering by macro regime.

Disposition:

`SELECTED_FOR_FROZEN_EXPERIMENT`

Reason:

Independent, low-fill, bounded, public-data feasible, and economically capable of producing edge scale materially above the ordinary 1-4 bps design prior.

## 3. B2 — Same-Venue Triangular Spot Parity

Independence:

PASS.

Economic payer:

Temporary no-arbitrage cross-rate mismatch.

Execution structure:

- three near-simultaneous taker fills;
- extreme legging/latency sensitivity.

Edge-to-Fill:

FAIL.

- fee floor already ~15 bps before spread/depth/legging reserve;
- public/non-colocated SC001 infrastructure cannot identify atomic executable three-book opportunities reliably;
- no separate structural reason exists for ordinary liquid parity violations to persist at tens of bps.

Data/latency:

Mismatch with the mechanism.

Disposition:

`REJECT_STRUCTURAL`

No sentinel/backtest.

## 4. B3 — Stablecoin Parity Dislocation Reversion

Independence:

PASS.

The anchor is external parity/redemption pressure, not a rolling local reference.

Economic payer:

Stablecoin arbitrage/redemption capital and liquidity provision around temporary cross-rate dislocation.

Execution structure:

- two spot fills;
- no multi-leg simultaneous execution requirement.

Edge-to-Fill:

- preliminary burden ~15 bps;
- genuine stress dislocations can plausibly exceed this scale;
- ordinary deviations may not.

Data:

- direct USDC-USDT spot market exists;
- public historical spot data are feasible.

Risks:

- true credit/depeg events;
- opportunity rarity;
- trader may not have direct institutional redemption access;
- convergence may exceed max hold.

Disposition:

`SELECTED_FOR_FROZEN_EXPERIMENT`

Reason:

Independent fixed-parity mechanism, low fill count, public-data feasibility and a credible path to tens-of-bps headroom during stress.

## 5. Comparative decision

Selected:

1. B1 -> assign `C11`;
2. B3 -> assign `C12`.

Rejected:

- B2 triangular parity -> `REJECT_STRUCTURAL`.

N1/N2/N3 remain auxiliary families only and are not attached yet.

## 6. Batch diversity

C11 and C12 are structurally distinct:

### C11
- external scheduled event;
- directional;
- event-slippage risk;
- seconds/minutes.

### C12
- external parity anchor;
- reversion/convergence;
- stablecoin credit/liquidity risk;
- minutes.

They do not share the same economic payer or risk signature.

## 7. Current authorization

Assign candidate IDs only.

Allowed next:

- candidate-ID freeze;
- metadata/source semantics preflight;
- chronology/contamination planning;
- cheapest-sentinel design freeze.

Not allowed yet:

- historical price-headroom outcome;
- threshold tuning;
- protected/promotional evidence.
