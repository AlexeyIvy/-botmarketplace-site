# SC001 — B15 Independent-Base Multi-Role Critical Review v0.1

Date: 2026-09-19
Status: **NON-ALPHA DESIGN REVIEW / NO B15 CANDIDATE ID / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v5.26.md`;
- `docs/research/sc001-strategy-landscape-v0.9.md`;
- `docs/research/sc001-feature-evidence-registry-v0.8.md`;
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.7.md`;
- `docs/research/sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.2.md`;
- `docs/research/sc001-parallel-independent-base-mechanism-pool-v0.1.md`.

## 1. Review objective

Identify a genuinely independent B15 base mechanism while B13-C and B14-A run prospectively in the background.

No market outcome is opened.

No B15 candidate/experiment ID is assigned.

The review uses three required lenses:

1. financial/economic;
2. programmer + trader/execution;
3. mathematics/statistics.

## 2. Binding lessons before B15

B15 must not be a disguised rescue of:

- C1 ordinary spot/perp basis convergence;
- C2 local-reference mean reversion;
- C3 continuation/volatility expansion;
- C4 cross-asset lead/lag;
- C5 aggressive-flow exhaustion;
- C6 cross-sectional dispersion/reversion;
- C7 ordinary maker spread capture;
- C8 ordinary continuous cross-venue dislocation;
- C9 scheduled funding/mark-index normalization;
- C10 broad L2 liquidity vacuum;
- C11 macro-event first-second direction capture;
- C12 standalone stablecoin parity reversion;
- B13-A one-settlement cross-venue funding differential.

Project design prior remains:

ordinary liquid-market information generally appears in low-single-digit bps unless a separate structural/exogenous mechanism explains larger magnitude.

Therefore B15 should prefer an explicit market-friction payer or contractual/operational discontinuity.

---

# 3. Shortlist

## B15-P1 — Transferability Shock / Capital-Segmentation Dislocation

### Mechanism

A crypto asset remains actively traded on multiple venues, but deposit/withdrawal transferability for the relevant asset/network becomes unavailable or materially impaired on at least one venue.

External price discovery continues, but inventory cannot freely move through the normal arbitrage loop.

Economic mechanism:

`TRANSFERABILITY LOSS -> CAPITAL/INVENTORY SEGMENTATION -> PERSISTENT CROSS-VENUE PRICE DISLOCATION`

This differs from C8 because C8 studied continuously connected venues where ordinary arbitrage should rapidly remove same-asset deviations.

### Preferred architecture

Best architecture uses prospectively pre-positioned inventory/cash on both venues.

When Venue A is rich and Venue B is cheap:

- sell pre-positioned asset inventory on rich venue;
- buy same economic asset on cheap venue.

Initial market fills:

`2`

Later inventory rebalance may use restored transferability rather than two additional market exits.

If pre-positioned inventory is unavailable and a derivative hedge is required, the architecture becomes more expensive and must receive a separate card.

### Economic payer

Participants who demand immediacy while arbitrage capital is segmented:

- forced sellers/buyers on the impaired venue;
- inventory-constrained market makers;
- traders unable to transfer the asset/network;
- local demand/supply imbalance during the outage.

### Expected scale

Mechanistically capable of tens or hundreds of bps because the normal capital-transfer arbitrage channel can be disabled.

No magnitude is assumed before a prospective source/headroom screen.

### Key risks

- transfer status can be network-specific, not asset-wide;
- deposit may be open while withdrawal is closed or vice versa;
- the same ticker can represent different economic units;
- venue/chain counterparty risk increases during outages;
- inventory may remain trapped for an unknown duration;
- withdrawal reopen may be delayed;
- transfer fees and chain fees;
- quote/stablecoin transferability may also be impaired;
- pre-positioned inventory has capital opportunity cost.

### Independence

This is not C8 rescue.

The state variable is not a price deviation threshold.

The independent causal state is loss of convertibility/transferability.

Price dislocation is an outcome of that state, not the trigger definition.

---

## B15-P2 — Scheduled Delisting / Forced-Close Dislocation

### Mechanism

An exchange prospectively announces that a standard spot/perpetual/futures product will cease trading and positions/orders will be closed, settled or otherwise terminated at a known time.

Potential mechanism:

`FORCED INVENTORY UNWIND + MARKET-MAKER WITHDRAWAL + TERMINAL VENUE RULE -> LOCAL/REFERENCE DISLOCATION`

### Strength

A real forced-flow event exists and can plausibly create larger-than-ordinary movement.

### Main problem

This mechanism is adjacent to B14-A because both ultimately rely on a terminal contractual/exchange event.

It is not identical:

- B14-A = normal dated-futures expiry;
- P2 = abnormal venue/product termination and forced unwind.

But the independence margin is smaller than P1.

### Architecture

Likely requires a local affected leg plus an external reference/hedge.

Typical structural burden:

3-4 market fills unless the affected leg receives a deterministic settlement/forced-close treatment.

### Risks

- low liquidity before delisting;
- special price limits;
- short-sale/borrow restrictions;
- external-reference identity mistakes;
- announcement timestamp versus actual close semantics;
- adverse selection and gap risk;
- concentrated low-quality/small-cap universe.

### Disposition

Hold as second-line mechanism.

---

## B15-P3 — Fixed Conversion / Redemption Anchor Arbitrage

### Mechanism

A venue, issuer or protocol offers an operationally accessible conversion/redemption facility at a known deterministic ratio while the secondary market trades away from that conversion value.

Economic mechanism:

`SECONDARY-MARKET DISLOCATION -> FIXED CONVERSION/REDEMPTION ANCHOR`

This differs from C12.

C12 assumed secondary-market parity reversion.

P3 would require an actual executable conversion/redemption mechanism, not an expectation of reversion.

### Structural appeal

Potentially very low fill count:

- one market entry;
- one conversion/redemption action;
- possibly one inventory rebalance.

If the fixed conversion is truly accessible, the edge-to-fill structure can be excellent.

### Main problems

- access may be account/KYC/jurisdiction specific;
- conversion limits/caps;
- facility may suspend exactly during stress;
- API automation may not exist;
- withdrawal/redemption delays;
- issuer/venue counterparty risk;
- opportunity rate may be extremely low.

### Disposition

High theoretical quality, but source/access feasibility is uncertain.

Hold until accessibility can be proved without price outcomes.

---

# 4. Financial / economic expert review

## 4.1 P1

Strongest economic logic of the three.

The mechanism has a clear payer:

temporary inability to move arbitrage inventory.

The important improvement over prior SC001 relative-value work is architectural:

with pre-positioned asset and cash, the opening arbitrage can require only two market fills rather than four.

That materially improves:

`edge scale / structural fill burden`

Capital cost is the main hidden expense:

- idle inventory on multiple venues;
- venue credit risk;
- trapped inventory duration;
- rebalancing cost.

Financial conclusion:

`PROMISING_IF_TRANSFER_STATE_CAN_BE_PROVED_PROSPECTIVELY`

## 4.2 P2

Economically real forced-flow mechanism.

But terminal-event logic partially overlaps B14-A and execution conditions may become worst exactly when nominal dislocation is largest.

Financial conclusion:

`REAL_MECHANISM / SECOND_PRIORITY / HIGH_EXIT_RISK`

## 4.3 P3

Potentially the cleanest theoretical arbitrage because a fixed conversion anchor can replace uncertain mean reversion.

But accessibility is the mechanism.

If the user/account cannot actually invoke the conversion under the relevant stress conditions, there is no strategy.

Financial conclusion:

`EXCELLENT_IN_THEORY / ACCESSIBILITY_UNPROVEN`

---

# 5. Programmer + trader / execution expert review

## 5.1 P1

### Programmer

The hardest problem is not price collection.

It is source semantics.

Required event state should distinguish at minimum:

- venue;
- exact asset identity;
- exact network/chain;
- deposit enabled/disabled;
- withdrawal enabled/disabled;
- maintenance reason/status;
- observed state-change timestamp;
- source timestamp versus local receive timestamp.

A generic `coin disabled` boolean is insufficient.

Need a fail-closed identity layer because many assets have multiple networks.

Historical status APIs may be unavailable or authenticated.

Therefore first work must be source/access audit, not backtest.

### Trader

P1 is attractive because latency may be less extreme than C8.

When transfers are genuinely blocked, the gap can persist because the arb loop is physically impaired.

Best trading architecture requires capital pre-positioning before the event.

Trader conclusion:

`BEST B15 LEAD IF SOURCE + INVENTORY ARCHITECTURE PASS`

## 5.2 P2

### Programmer

Official announcements and instrument status changes can usually provide event clocks, but parsing event semantics is brittle.

Need reconciliation of:

- announcement effective time;
- API instrument state;
- actual final trade timestamp;
- settlement/forced-close rule.

### Trader

Markets approaching delisting often become toxic:

- spreads widen;
- depth disappears;
- borrow/short availability degrades.

Large displayed price gaps may not be executable.

Conclusion:

`FEASIBLE_TO_RESEARCH / EXECUTION HOSTILE`

## 5.3 P3

### Programmer

Account-specific conversion facilities are difficult to represent with public data alone.

A safe implementation would need read-only capability discovery first and strict rate/limit verification.

### Trader

If facility is real and callable, this is compelling.

If not, public secondary-market price gaps are irrelevant.

Conclusion:

`DO NOT PRICE-TEST BEFORE ACCESS PROOF`

---

# 6. Mathematics / statistics expert review

## 6.1 General warning

B15 must not use second-by-second observations as independent sample size.

The relevant inference units are structural events.

## 6.2 P1 inference unit

Primary unit:

`transferability-shock event × asset × venue-pair × network state`

Within one outage, thousands of price ticks are one clustered regime.

Future evidence should report:

- number of independent outage episodes;
- number of assets;
- number of venue pairs;
- duration distribution;
- event clustering;
- concentration by one exchange/network.

A spectacular single outage cannot validate a general strategy.

## 6.3 P2 inference unit

`delisting/forced-close event`

Severe selection bias risk:

delisted assets are systematically distressed.

Do not generalize from event count as if assets were random.

Need prospective event census.

## 6.4 P3 inference unit

`independent conversion-stress episode`

Likely very low-N.

Even if each observed episode is profitable, the strategy may remain economically unimportant if opportunities occur only a few times per year.

Opportunity-rate and capital utilization must therefore be first-class gates.

## 6.5 Multiplicity

Do not test all three price mechanisms and promote whichever looks best.

Required sequence:

1. choose one lead from non-price reasoning;
2. freeze its source/semantic architecture;
3. perform cheapest source/headroom sentinel;
4. only then consider the next mechanism.

---

# 7. Cross-role synthesis

## Lead

`B15-P1 TRANSFERABILITY SHOCK / CAPITAL SEGMENTATION`

Why it survives best:

- independent economic payer;
- plausible tens/hundreds-bps scale;
- potentially only two initial market fills with pre-positioned capital;
- lower latency dependence than ordinary C8 cross-venue dislocation;
- clearly distinct from C1-C12/B13-A/B14-A;
- naturally fail-closed and prospectively observable.

## Reserve 1

`B15-P3 FIXED CONVERSION / REDEMPTION ANCHOR`

Reason:

best theoretical edge-to-fill structure, but access feasibility is uncertain.

## Reserve 2

`B15-P2 SCHEDULED DELISTING / FORCED CLOSE`

Reason:

real structural event, but more adjacent to B14-A and execution can be hostile.

---

# 8. Required B15 next step

Do not open cross-venue prices yet.

Perform only a:

`B15-P1 TRANSFERABILITY-SHOCK SOURCE / ACCESS / SEMANTIC FEASIBILITY AUDIT`

Questions:

1. Which exchanges expose authoritative deposit/withdraw/network status prospectively?
2. Is access public, authenticated-read-only, or unavailable?
3. Can state changes be timestamped causally?
4. Can exact network identity be frozen?
5. Can the same economic asset be verified across venues?
6. Can a pre-positioned two-fill inventory architecture be implemented without relying on transfers during the outage?
7. What transfer/rebalance costs exist after reopening?
8. Can at least one future clean event path be collected without inspecting price outcomes?

No P1 threshold, spread, asset subset or venue winner may be selected from price data during this audit.

---

# 9. Current disposition

B15 status:

`INDEPENDENT_BASE_MECHANISM_REVIEW_COMPLETE`

Provisional lead:

`B15-P1_TRANSFERABILITY_SHOCK_CAPITAL_SEGMENTATION`

No candidate ID.

No price outcome.

Next allowed work:

source/access/semantic feasibility only.
