# Safe-Sleeve S002 — User-Access Due-Diligence Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** ACCESS_PROFILE_REQUIRED; protocol frozen before product-level selection  
**Parent architecture:** `MULTI-DOMAIN LAYERED RESERVE` from S001  
**Canonical roadmap:** `docs/research/r009-r003-strategy-first-roadmap-v3.0.md`

## 1. Purpose

Convert the S001 architecture class into a concrete, user-access-aware implementation without changing any active strategy and without selecting products, venues, capital tiers or instruments from observed P&L.

S002 must answer four separate implementation questions:

1. where off-venue survival capital can realistically be held;
2. how much capital must remain immediately executable for routine operations;
3. what bridge can move capital into a functioning crypto venue during stress;
4. what collateral is required for derivatives strategies and therefore must be treated as risk capital rather than safe reserve.

Yield is subordinate to survival, access, mobility and failure-domain separation.

## 2. Frozen research invariants

S002 must not alter or reset the active prospective records.

- **R009-E002:** inception remains `2026-09-10 00:00 UTC`.
- **R003-E003 Binance:** decision boundary remains `2026-09-10 12:00 UTC`; future refreshes must use the frozen causality-safe launcher/hotfix; no reset or venue substitution.
- **R003-X003 Bybit:** boundary remains `2026-09-10 16:00 UTC`; separate parallel forward; never merge with Binance.
- **R010-E001:** inception remains `2026-09-11 00:00 UTC`; thresholds, weights, ATH reset and inception remain frozen; inherited armed tranches are warmup only and not prospective validation.

Additional constraints:

- R009 G001/G002 are complete.
- `$250` is only a coarse mechanical floor.
- `$1,000` is only the current descriptive small-account demo-engineering candidate, not an optimized universal minimum.
- G003 remains deferred.
- Do not retune R009.
- Do not replace R009 with R010.
- Do not select asset, venue or capital tier because of prettier historical/early-forward P&L.
- No real-money deployment.
- Broad platform development remains frozen.

## 3. S002 access gate

Product-level due diligence is not allowed until the user access profile is explicit enough to test eligibility.

Required access facts:

### A. Legal / tax access

- legal residence / jurisdiction relevant to account eligibility;
- tax residence if different and materially relevant to instrument access or after-tax treatment;
- base-currency liabilities and preferred reserve currency/currencies;
- any known restrictions on U.S. securities, money-market funds, crypto derivatives or stablecoin use.

### B. Banking rails

For each usable bank/payment relationship:

- country / banking jurisdiction;
- currencies actually supported;
- outbound and inbound rail availability;
- domestic wire / international wire / ACH / SEPA / equivalent availability where applicable;
- daily or monthly transfer limits;
- transfer cut-off times and weekend behavior;
- known crypto-exchange transfer restrictions;
- deposit-insurance regime and applicable coverage limits.

### C. Broker / custodian access

For each account that is already open or realistically openable:

- legal entity and jurisdiction serving the user;
- access to short sovereign bills or equivalent government paper;
- access to government money-market funds or equivalent cash-management funds;
- settlement cycle;
- withdrawal / bank-link behavior;
- cash sweep behavior;
- custody / investor-protection regime;
- minimums, fees and FX costs.

### D. Crypto venue access

For Binance, Bybit and any other venue actually available to the user:

- exact legal entity / regional product accessed;
- spot availability;
- derivatives availability;
- fiat deposit / withdrawal rails;
- stablecoin deposit / withdrawal networks;
- withdrawal limits;
- API availability;
- whether transfers can operate during weekends/holidays;
- any regional product restrictions.

S002 must not infer access from historical data availability or from the existence of a public API.

### E. Self-custody / bridge capability

- whether self-custodied stablecoin is operationally acceptable;
- wallet type and recovery discipline;
- chains actually usable by the target venues;
- maximum acceptable stablecoin issuer concentration;
- willingness to keep a small bridge balance exposed to stablecoin / chain risk.

### F. Deployment requirement

The user must define the practical crisis-deployment objective, at least descriptively:

- capital needed within **H1**;
- capital needed within **H24**;
- capital needed within **H72**;
- whether weekend / holiday deployment is required;
- expected total portfolio/account-size range for implementation research.

The implementation must be sized from these operational requirements, not from a generic percentage template.

## 4. Evidence hierarchy

For eligibility and operational rules, use the following evidence order:

1. official bank / broker / custodian / exchange / government documentation;
2. official account-specific terms or authenticated product pages where available;
3. regulator / deposit insurer / securities-protection documentation;
4. third-party documentation only as corroboration, never as the sole basis for an eligibility decision.

For each important rule record:

- source;
- effective/retrieval date;
- jurisdiction / account type;
- exact operational implication;
- confidence level;
- whether the rule is generic or user-account-specific.

## 5. Four-layer implementation model

### Layer 1 — Off-venue survival reserve

Primary objective: survive crypto-venue, stablecoin and trading-infrastructure failure with principal availability preserved as far as practicable.

Candidate classes may include, only where actually accessible:

- insured bank deposits;
- broker-held short sovereign bills;
- government money-market or equivalent short-duration government-cash vehicles;
- other regulated cash-like instruments that satisfy the same failure-domain requirements.

This layer should not depend on the primary crypto venue remaining functional.

### Layer 2 — Execution buffer

A deliberately small balance already positioned where routine strategy operations occur.

It exists to avoid unnecessary transfer churn and missed ordinary rebalances, but it is **not** counted as fully safe capital.

Sizing rule:

> execution buffer = minimum operational amount required for expected ordinary rebalancing + fees + rounding/minimum-order effects + explicitly chosen operational headroom.

It must not be enlarged merely to increase convenience or yield.

### Layer 3 — Crisis-deployment bridge

Capital or an instrument path whose purpose is speed rather than maximum safety or yield.

Possible mechanisms may include, only if access is confirmed:

- fast bank/broker-to-exchange fiat rails;
- a bounded self-custodied stablecoin bridge;
- a second independent fiat/crypto ingress route.

Sizing rule:

> bridge size = amount required to satisfy the frozen H1/H24/H72 deployment objective under the tested transfer path.

A bridge can be operationally valuable while still carrying issuer, chain, banking or access risk; those risks must be explicit.

### Layer 4 — Derivatives collateral

Capital required for R003 or any other derivatives position.

This capital is exposed to venue, margin, collateral and operational risk and therefore must never be counted as off-venue safe reserve.

For R003, the frozen fully funded 50/50 equal-BTC construction remains unchanged. S002 may analyze where the collateral sits and how it is replenished, but may not alter R003 economics.

## 6. No-percentage rule before access testing

S002 does not begin with allocations such as 60/20/10/10.

The ordering is:

1. determine accessible instruments and rails;
2. measure/verify transfer and settlement behavior;
3. define the minimum execution buffer;
4. define H1/H24/H72 crisis bridge requirements;
5. define derivatives collateral requirements from frozen strategies;
6. assign the remaining capital to the survival layer subject to custody/insurance concentration limits;
7. only then compare yield, fees and taxes among implementations that already pass the resilience gate.

## 7. Failure-domain matrix required for each candidate pathway

Each candidate implementation must be tested against at least:

- primary exchange outage;
- primary exchange withdrawal freeze;
- stablecoin depeg or redemption impairment;
- chosen chain congestion / halt;
- bank transfer delay;
- broker settlement delay;
- weekend / holiday market closure;
- bank or custodian access interruption;
- regional account restriction or product withdrawal;
- simultaneous crypto crash plus infrastructure stress;
- one-custodian concentration;
- inability to replenish derivatives collateral.

For every scenario record separately:

- capital surviving nominally;
- capital accessible at H1;
- capital accessible at H24;
- capital accessible at H72;
- capital trapped in the same failure domain;
- operational workaround, if any.

## 8. Candidate evaluation metrics

Do not collapse S002 into a single APY ranking.

Primary metrics:

- `survival_independence`;
- `H1_accessible_fraction`;
- `H24_accessible_fraction`;
- `H72_accessible_fraction`;
- `crypto_venue_common_mode_exposure`;
- `stablecoin_common_mode_exposure`;
- `single_custodian_concentration`;
- `weekend_deployability`;
- `transfer_failure_recovery_path`;
- `operational_complexity`.

Secondary metrics, considered only after the above:

- gross yield;
- after-fee yield;
- after-tax yield where material;
- FX cost;
- account minimums;
- maintenance burden.

## 9. Required operational drill before promotion

A pathway is not considered implementation-ready solely because documentation says transfers are supported.

Before any real-capital promotion, the future implementation process must include controlled non-production or de minimis operational tests where legally and operationally appropriate:

- off-venue account -> bridge;
- bridge -> trading venue;
- trading venue -> off-venue withdrawal;
- broker/security liquidation -> bank cash -> venue path where applicable;
- weekend/holiday path if the architecture relies on it;
- failed-transfer / delayed-transfer reconciliation.

S002 research can design these drills now, but no real-money test is authorized by this protocol.

## 10. Interaction with R009 / R010 / R003

- R009 and R010 continue unchanged; S002 only determines how future cash/dry-powder components could be held and mobilized.
- R003 collateral remains separate derivatives risk capital.
- Realized R003 carry may later fund a bounded ring-fenced convexity or reserve budget, but expected future carry cannot be treated as guaranteed safe-sleeve yield.
- Safe-sleeve product selection must not use early forward P&L as a selection variable.

## 11. S002 stage gates

### S002-A — ACCESS_PROFILE_FROZEN

Pass when the required jurisdiction, account, rail, self-custody and H1/H24/H72 information is explicit enough to test concrete products.

### S002-B — ELIGIBILITY_VERIFIED

Pass when each candidate bank/broker/custodian/venue pathway has official evidence that the user can actually use it.

### S002-C — PATHWAY_MATRIX_COMPLETE

Pass when settlement/transfer behavior, failure domains, fees and custody limits are documented for viable pathways.

### S002-D — LAYER_SIZING_PROPOSED

Pass when execution buffer, bridge and derivatives collateral are sized from operational requirements rather than arbitrary percentages, leaving the residual survival reserve subject to concentration limits.

### S002-E — CRISIS_DRILL_DESIGNED

Pass when a reproducible operational drill and reconciliation checklist exists for H1/H24/H72 access.

### S002-F — IMPLEMENTATION_CANDIDATE

Pass only if one architecture satisfies survival/access requirements without relying on a single venue, stablecoin issuer, bank or custodian as a catastrophic common mode.

This status is still not authorization for real-money deployment.

## 12. Current result

> **S002 STATUS: ACCESS_PROFILE_REQUIRED**

The architecture class is sufficiently defined to proceed, but concrete product-level recommendations would currently require unsupported assumptions about legal/account eligibility.

Therefore the next valid action is to freeze the user access profile, then research only the pathways that are actually available.

No active strategy, parameter, venue-forward record, inception clock or capital-tier conclusion is changed by S002 v0.1.
