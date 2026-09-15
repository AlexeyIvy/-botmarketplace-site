# SC001-E006 — Same-Venue Spot/Perpetual Basis Dislocation -> Convergence Research Plan v0.1

Date: 2026-09-15  
Status: **PLANNING DOCUMENT — NO E006 ALPHA AUTHORIZED**

## 1. Why E006 exists

E006 is a genuinely new SC001 mechanism family after terminal E001, E002 standalone, E003 and E004 failures.

It is not a rescue of E004 and does not reuse E004 parameters.

E005 remains closed because it was reserved exclusively for an incremental E002-TFI test on top of an independently viable E004 base strategy; that prerequisite was not met.

## 2. Core hypothesis

A rare transient divergence between same-venue BTC spot and BTC perpetual prices may reflect short-lived derivatives-specific inventory pressure, forced flow, leverage demand or liquidity imbalance.

If the divergence subsequently converges, a paired relative-value trade may capture movement measured in many basis points while substantially reducing exposure to the common directional BTC move.

Initial instrument pair under study:

- OKX `BTC-USDT` spot;
- OKX `BTC-USDT-SWAP` perpetual.

The intended edge is convergence of relative price, not prediction of BTC direction.

## 3. Why this family is preferred over immediate large-price-jump continuation/reversal

The full E001-E004 record now gives a stronger prior that entering a one-leg BTC trade after an already-visible price/flow transition often leaves only a tiny residual move.

A simple large-jump continuation/reversal experiment remains a legitimate fallback family, but it would again enter after a large directional move and therefore risks repeating the same residual-edge problem.

E006 changes the mechanism class instead:

- two closely related instruments rather than one directional leg;
- relative-price dislocation rather than post-event BTC direction;
- common BTC beta largely offset in the paired gross response;
- potentially lower event frequency;
- economically meaningful absolute divergence can be required before a trade is even considered.

## 4. Economics-first warning

A paired taker trade is not cheaper than E004.

Opening and closing two instruments creates four taker fills. On a one-reference-leg-notional normalization, a regular-user fee burden can therefore be roughly twice the single-instrument round-trip burden before spread, depth, legging risk and any borrow/funding effects.

Consequently E006 must target **large** transient basis moves. A few bps of convergence is economically irrelevant.

The eventual executable protocol must freeze a materially conservative gross hurdle, likely in the several-tens-of-bps range, before any L2 work. The exact normalization and numerical gate are not frozen by this planning document.

## 5. Data boundary and chronology firewall

Before any E006 alpha calculation, first perform a **data-only feasibility stage**.

Already-qualified source:

- March-2024 OKX `BTC-USDT-SWAP` trade archives already used in SC001.

New source to qualify:

- matching March-2024 OKX `BTC-USDT` SPOT public historical trade data.

Initial data-only scope:

- metadata / identity / archive feasibility first;
- if feasible, acquire only source labels required to reconstruct DEV-DISCOVERY UTC days `2024-03-01..20` under qualified causal UTC semantics;
- do not acquire/open E006 Confirmation spot bodies before a frozen E006 Discovery protocol earns that step;
- Q2, formal Validation and Final remain closed;
- no E006 signal, basis, response, return or P&L may be calculated during the data-feasibility stage.

The existing swap archives do not authorize opening new protected periods for the new spot leg.

## 6. Data-feasibility requirements

The data-only stage must determine, without alpha:

1. whether official/public historical `BTC-USDT` SPOT trades for March 2024 can be identified and retrieved reproducibly;
2. exact filenames/identities and SHA256;
3. schema and timestamp semantics;
4. whether a Q006R-like UTC reconstruction is required;
5. complete UTC minute/second coverage sufficient for a causal paired screen;
6. deterministic within-stream ordering;
7. whether spot and swap exchange timestamps can be causally aligned without using future information;
8. storage/runtime feasibility on the qualified VPS.

Any data ambiguity or irreproducible source identity yields a data-stage FAIL/REVIEW and E006 alpha remains closed.

## 7. Mandatory executable-protocol freeze items

Only after the data-feasibility stage PASSes may an executable E006 protocol be frozen.

Before first E006 alpha, it must define exactly:

- synchronized spot and swap price statistic (for example a short causal VWAP or other robust tape statistic; not selected after outcomes);
- evaluation grid and timestamp ordering;
- basis formula and units;
- causal baseline / normalization for ordinary basis;
- absolute economic dislocation threshold and/or causal tail rule;
- strict trigger semantics and tie handling;
- which dislocation sign(s) are genuinely tradable under the intended account/access model;
- if negative-basis trades require spot borrowing, exact borrow-feasibility/economic treatment before promotion;
- paired decision timestamp;
- primary latency and latency stress;
- two-leg entry proxy and allowed legging window;
- fixed exit/convergence rule and maximum hold;
- no-overlap/conflict logic;
- maximum positions and turnover cap;
- paired gross-edge normalization;
- completion definition for both legs;
- Discovery and Confirmation gross-economics gates;
- robust distribution, day-breadth, concentration and side/sign gates;
- a small diagnostic neighborhood that cannot rescue a failed primary.

No parameter may be selected after observing E006 returns.

## 8. Base-strategy firewall

Base E006 must not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression flags;
- post-hoc event/day/hour filters;
- winner-only basis sign selection after output.

Any later auxiliary-feature test requires an independently viable E006 base and a separate experiment identifier.

## 9. Proposed stage order

`E006 data feasibility -> final mathematical/economic audit -> executable protocol freeze -> implementation preflight -> DEV-DISCOVERY gross paired economics -> unchanged one-time DEV-CONFIRMATION -> only if PASS, paired L2/execution economics -> later protected temporal validation`

No stage may be skipped.

## 10. Gross-economics philosophy

The first alpha stage should remain trade-tape-only and deliberately conservative.

Promotion should require evidence that the relative-price convergence itself is naturally large enough to survive a paired taker implementation. At minimum the frozen gates should again include:

- completed paired trades;
- completion rate;
- pooled mean;
- symmetric trimmed mean;
- pooled median;
- median active-day mean;
- positive-day breadth;
- day concentration;
- sign/direction concentration if both signs are enabled;
- primary latency stress;
- explicit turnover ceiling.

A small statistically significant basis effect is not enough.

## 11. Stop rules

If the data stage fails: stop/pause E006 without alpha.

If frozen Discovery gross economics fail: terminal E006 Discovery FAIL; do not open Confirmation or acquire paired L2 for rescue.

Do not rescue via:

- lower/VIP fees;
- maker assumptions;
- alternate basis sign selected after output;
- looser shock threshold;
- different synchronization grid;
- different baseline/lookback;
- different hold/exit;
- TFI/FLOW_IMPULSE/compression filters;
- Q2/Validation/Final exploration.

## 12. Immediate next action

Do **not** calculate E006 basis or returns yet.

Create and run a data-only SPOT historical-data feasibility preflight for `BTC-USDT` covering only the March-2024 source labels needed for DEV-DISCOVERY UTC reconstruction. Record metadata, hashes, schema, timestamp/order coverage and storage requirements only.
