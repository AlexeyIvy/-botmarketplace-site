# Safe-Sleeve S002-D — Functional Layer Sizing v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** FUNCTIONAL_SIZING_PROPOSED — no live allocation authorized  
**Parent:** `docs/research/safe-sleeve-s002-pathway-failure-matrix-v0.1.md`  
**Study capital tier:** approximately USD 1,000 equivalent  
**Access profile:** Russia tax/KYC profile; T-Bank + Alfa-Bank; Bybit primary account-verified ingress candidate; OKX backup candidate not yet account-verified

## 1. Purpose

Convert S002-C from qualitative layers into functional dollar sizing for the approximately USD 1,000 research tier without guessing percentages and without modifying any active strategy.

Sizing is derived from:

- frozen R009 / R010 target-state mechanics;
- the requirement that H1 relies only on pre-positioned venue capital;
- the requirement that H24 can rebuild the directional execution state under ordinary conditions;
- the requirement that H72 can use an independent bank/venue route if the primary route is unavailable;
- R003 collateral remaining a separate risk sleeve rather than safe reserve.

No real-money deposit, trade or transfer is authorized.

## 2. Frozen directional mechanics relevant to sizing

R009 and R010 each have a frozen target range of 0-20% BTC exposure at portfolio level.

For a USD 1,000-equivalent strategy NAV:

- 2.5pp state increment = USD 25;
- 7.5% current inherited/recovery-state exposure example = USD 75;
- 10% trend component = USD 100;
- 17.5% current forward-state target example = USD 175;
- 20% maximum target = USD 200.

The sizing envelope must be based on the frozen maximum target, not on the current 17.5% state and not on prettier realized P&L.

## 3. Layer 2 — execution buffer sizing

### Mechanical requirement

The execution venue must be able to support the full frozen directional target state without requiring an external transfer at the instant of a signal.

Therefore:

`maximum directional position capacity = 0.20 * strategy NAV`

At USD 1,000:

`maximum directional position capacity = USD 200`

The venue also needs a small non-position reserve for:

- trading fees;
- venue-specific minimum order / quantity rules;
- rounding;
- minor NAV / price drift between signal calculation and execution.

Because Bybit BTC spot execution rules have not yet been frozen for this user-level implementation, the exact friction amount is not yet promoted to a hard number.

### Descriptive implementation candidate

For engineering purposes only:

> **Directional execution-buffer candidate: approximately USD 210 equivalent**

Interpretation:

- up to roughly USD 200 may be required as BTC position capacity;
- roughly USD 10 remains as provisional order/fee/rounding headroom;
- the USD 10 headroom is a descriptive placeholder to be replaced by exact venue rules before any demo that moves funds.

This is not a new R009/R010 parameter and does not alter target weights.

### Example at the current 17.5% target state

If a future demo were operating at a 17.5% target on USD 1,000 NAV, the approximately USD 210 venue envelope could conceptually contain:

- approximately USD 175 BTC exposure;
- approximately USD 35 liquid quote balance / execution headroom.

At the 20% maximum state:

- approximately USD 200 BTC exposure;
- approximately USD 10 execution headroom.

Any quote/stablecoin balance inside this execution buffer is still venue/stablecoin risk capital and is **not** counted as safe reserve.

## 4. Layer 3 — crisis bridge sizing

At this capital tier, S002 does **not** require a permanently separate USD 200+ self-custodied stablecoin balance.

Instead, the bridge is primarily a **mobilizable capacity requirement**.

### H1

H1 deployment is supplied only by the already-positioned execution buffer.

Target:

> **H1 executable capacity ≈ USD 210 on the active venue**

No bank -> P2P route is assumed to be deterministic inside H1.

### H24

If the venue balance must be rebuilt or the strategy must be re-established through a working route, the primary bank path should be capable of funding one full directional execution envelope.

Target:

> **H24 primary bridge capacity ≈ USD 210 equivalent**

This does not mean USD 210 must sit in a separate stablecoin wallet. It means at least this amount of the off-venue reserve must be operationally movable through the primary bank/P2P route when that route functions normally.

### H72

If the primary bank/rail is unavailable, the secondary bank should independently be capable of restoring the same directional execution envelope.

Target:

> **H72 independent backup-bank capacity ≈ USD 210 equivalent**

This creates a functional reason to keep real funds in the second bank rather than maintaining an empty backup account.

## 5. Layer 1 — off-venue survival reserve sizing

With a USD 1,000 total NAV and an approximately USD 210 venue execution envelope:

`off-venue residual = 1000 - 210 = USD 790`

To make the two-bank architecture genuinely independent, at least one full execution-envelope amount should already be available at the secondary bank.

Therefore a mechanically derived bank-capacity candidate is:

- **secondary-bank funded failover capacity: ≈ USD 210 equivalent**;
- **primary-bank residual survival cash: ≈ USD 580 equivalent**;
- total off-venue survival capital: ≈ USD 790 equivalent.

This is not a generic 58/21/21 portfolio rule. It is specific to the USD 1,000 study tier and the 20% maximum directional target plus provisional execution headroom.

The assignment of T-Bank versus Alfa-Bank as `primary` or `secondary` remains deliberately unfrozen until transfer/P2P reliability is tested. Do not choose the primary bank from anecdotal convenience alone.

## 6. Resulting directional-only architecture candidate

For an approximately USD 1,000 implementation of one frozen directional engine (R009 **or** R010), the current functional candidate is:

| Function | Mechanical candidate | Rationale |
|---|---:|---|
| Active venue execution envelope | ~USD 210 | supports frozen 20% max target + provisional friction headroom |
| Primary off-venue survival bank | ~USD 580 | residual survival reserve after maintaining independent failover capacity |
| Secondary off-venue bank / H72 failover | ~USD 210 | can independently rebuild one full execution envelope |
| Dedicated self-custody stablecoin bridge | USD 0 base case | unnecessary duplication at USD 1k until transfer drills show need |
| Total | ~USD 1,000 | arithmetic study envelope only |

Important:

- this table is a **design candidate for paper/demo engineering**, not a live allocation recommendation;
- exact RUB amounts depend on the exchange rate at the future implementation timestamp;
- the off-venue bank balances are survival capital, while the venue balance is risk/operations capital;
- if the second-bank balance is below one execution envelope, H72 independence is weakened.

## 7. Why the candidate is not based on arbitrary percentages

The amounts follow directly from frozen mechanics:

1. R009/R010 maximum target = 20% of NAV -> USD 200.
2. Add provisional friction headroom -> approximately USD 210 venue envelope.
3. Independent failover requires a second path capable of rebuilding that envelope -> approximately USD 210 at the secondary bank.
4. Remaining capital stays in the primary off-venue survival domain -> approximately USD 580.

If the capital tier changes, the dollar values must be recomputed rather than preserving 58/21/21 percentages.

## 8. Scaling formula

For directional strategy NAV `N`:

- maximum BTC position capacity = `0.20 * N`;
- execution envelope `E = 0.20 * N + F`, where `F` is venue-specific fee/min-order/rounding headroom;
- secondary-bank failover minimum ≈ `E` if true independent H72 rebuild capability is required;
- primary-bank survival residual = `N - 2E`, provided this remains positive;
- total off-venue reserve = `N - E`.

At very small N, fixed venue minimum-order rules can dominate and invalidate proportional scaling. This is why R009 G001/G002 remain authoritative for mechanical granularity.

## 9. Interaction with R003

R003 cannot be inserted into the USD 1,000 architecture as if its collateral were part of the safe sleeve.

For any future R003 allocation `C` under the frozen fully funded implementation:

- spot leg = `0.50 * C`;
- derivatives-collateral bookkeeping = `0.50 * C`;
- total R003 allocation `C` is risk/carry capital, not survival reserve.

Therefore:

> **every dollar allocated to R003 reduces the off-venue survival pool dollar-for-dollar unless additional capital is added.**

At the approximately USD 1,000 total-capital tier, a material live R003 allocation would materially weaken the simple directional safe-sleeve architecture.

S002-D therefore does **not** select a combined R009/R010/R003 live allocation. R003 continues in its separate prospective research records only.

This is an implementation-capital constraint, not a negative strategy conclusion and not a modification of R003.

## 10. R009 versus R010 separation

The approximately USD 210 execution envelope can describe the capacity requirement for either R009 or R010 because both have the same frozen 0-20% maximum target range.

It must **not** be interpreted as permission to run both at full NAV simultaneously or to merge their records.

R009 and R010 remain separate research candidates with separate prospective evidence.

## 11. Mixed RUB / USD-equivalent objective

At this stage, `USD 1,000 equivalent` is a sizing numeraire, not a requirement that the off-venue survival reserve be held as literal USD.

The base architecture currently prefers insured/off-venue RUB bank capital because that is the user-accessible survival domain already verified.

USD-equivalent preservation can later be evaluated through:

- FX exposure policy;
- accessible regulated foreign-currency bank instruments;
- bounded stablecoin bridge only if operationally justified;
- other legal instruments available to the user.

S002-D does not convert the survival reserve into stablecoins merely to label it `USD`.

## 12. Promotion blockers before exact layer sizing can be called final

The approximately USD 210 execution envelope is still descriptive until the following are checked for the intended demo venue/product:

- exact BTC spot minimum order / quantity step / minimum notional;
- actual maker/taker fee tier;
- quote asset used;
- BTCUSDT spot visibility at demo time;
- crypto withdrawal prerequisites;
- measured P2P spread and bank-transfer behavior;
- primary/secondary bank assignment;
- backup venue account eligibility if H72 venue redundancy is required.

No live transfer is required to freeze the formulas.

## 13. S002-D result

> **S002-D: FUNCTIONAL_SIZING_PROPOSED**

For the approximately USD 1,000 directional implementation study, the current architecture candidate is:

> **~USD 210 active-venue execution envelope + ~USD 790 off-venue reserve, with at least ~USD 210 of the off-venue reserve pre-positioned at the independent second bank.**

Equivalently for operational planning only:

> **~USD 580 primary survival bank + ~USD 210 secondary failover bank + ~USD 210 active venue.**

This is a mechanically derived demo-engineering candidate, not a production allocation and not authorization to fund accounts.

## 14. Research invariants

- R009-E002 inception remains `2026-09-10 00:00 UTC`;
- R003-E003 Binance boundary remains `2026-09-10 12:00 UTC`; future retry requires the causality-safe hotfix and no reset;
- R003-X003 Bybit boundary remains `2026-09-10 16:00 UTC` and separate from Binance;
- R010-E001 inception remains `2026-09-11 00:00 UTC`;
- R010 thresholds, weights and ATH reset remain frozen;
- inherited R010 armed tranches are not prospective validation;
- R009 is not retuned or replaced;
- no real-money deployment;
- broad platform development remains frozen.
