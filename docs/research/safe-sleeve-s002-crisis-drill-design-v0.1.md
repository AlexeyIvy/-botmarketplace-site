# Safe-Sleeve S002-E — Crisis Drill Design v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-11  
**Status:** CRISIS_DRILL_DESIGNED — no live-money test authorized  
**Parent sizing:** `docs/research/safe-sleeve-s002-functional-layer-sizing-v0.1.md`  
**Study capital tier:** approximately USD 1,000 equivalent

## 1. Purpose

Precommit the operational test plan for the S002 multi-domain layered reserve before any funds are moved.

The drill is designed to answer one narrow question:

> Can the proposed reserve architecture preserve capital and restore the required directional execution capacity through independent paths inside the intended H1/H24/H72 windows?

The drill does not test strategy profitability, antifragility, alpha or market timing.

No active strategy parameter or forward record is changed.

## 2. Architecture under test

Current descriptive candidate from S002-D:

- active-venue execution envelope: approximately USD 210 equivalent;
- primary off-venue survival bank: approximately USD 580 equivalent;
- secondary off-venue failover bank: approximately USD 210 equivalent;
- dedicated self-custody stablecoin bridge: USD 0 in the base case;
- Bybit: primary account-verified crypto ingress candidate;
- OKX: backup crypto candidate pending account-level verification.

These are engineering candidates, not live allocations.

## 3. Frozen success horizons

### H1 — immediate execution

Goal:

- the strategy can execute from capital already positioned at the active venue;
- no bank/P2P transfer is required to satisfy H1.

Precommitted success condition:

> A functioning venue account has sufficient immediately usable balance to support the full frozen directional execution envelope for one R009 **or** R010 engine.

For the USD 1,000 study tier, this means approximately USD 210 of executable venue capacity once exact venue rules are frozen.

### H24 — primary rebuild path

Goal:

- if the active-venue capital must be rebuilt or replenished, the primary off-venue bank path can restore one full directional execution envelope under ordinary non-failure conditions before the next daily operational cycle.

Precommitted success condition:

> The primary bank -> crypto ingress -> trading-account path can make approximately one execution envelope available within 24 hours, including all mandatory platform/account transfers.

### H72 — independent failover

Goal:

- if the primary bank/rail or primary venue path is unavailable, an independent path can restore the same execution capacity within 72 hours under an ordinary contingency.

Precommitted success condition:

> A path that does not depend on the failed primary domain can restore approximately one execution envelope within 72 hours.

A path is not independent if it relies on the same failed bank, same frozen venue account, same single stablecoin issuer without an alternative, or the same inaccessible credentials.

## 4. Drill stages

### Stage 0 — documentation-only dry run

No money moves.

Collect and timestamp:

- bank transfer-limit screens for T-Bank and Alfa-Bank;
- Bybit current KYC and product visibility;
- Bybit RUB/USDT P2P ad availability;
- payment-method labels visible on actual P2P ads;
- Bybit deposit/withdrawal/security prerequisite screens where visible without funding;
- OKX account/KYC/product availability if a backup account is opened;
- exact BTC spot instrument rules for intended demo venue;
- maker/taker fee schedule applicable to the account;
- relevant support/status pages.

Stage-0 output is an evidence table only.

### Stage 1 — tabletop route simulation

No money moves.

For each route, manually write the exact click/decision sequence:

1. bank balance available;
2. open P2P marketplace;
3. filter RUB -> quote asset;
4. choose counterparty under precommitted quality criteria;
5. complete bank payment step;
6. P2P asset arrives in Funding account;
7. internal transfer to Unified Trading Account if required;
8. verify BTC spot order entry is available;
9. stop before placing an order.

Record every step that can block or delay the route.

### Stage 2 — future de-minimis operational drill

**Not authorized by this document.**

Only if a later project decision explicitly authorizes a live operational test, use the smallest legally/operationally sensible amount needed to validate settlement behavior rather than the full USD 210 envelope.

The de-minimis drill would measure:

- actual bank transfer time;
- P2P counterparty completion time;
- actual spread;
- platform internal-transfer time;
- withdrawal/security restrictions;
- reconciliation evidence;
- whether the route works on the user's actual account.

No strategy position is required for this drill.

### Stage 3 — future full-envelope paper/demo rehearsal

No real trading capital is required.

Use recorded mechanics and a shadow ledger to simulate a USD 210 rebuild from timestamped route observations.

Only after Stage 2 and explicit authorization could a real-money implementation test ever be considered.

## 5. Precommitted route-quality criteria

A P2P route must not be selected after seeing which counterparty happened to be fastest in one test.

Before any future operational drill, counterparties must satisfy a precommitted filter such as:

- meaningful completed-order history;
- high completion rate;
- payment method matching the user's bank account in the same verified name;
- order limits compatible with the test amount;
- no instruction to route payment through third-party accounts;
- no request to communicate/pay outside the platform workflow.

Exact numerical thresholds should be frozen immediately before the first live operational drill using current marketplace distributions, not optimized afterward from outcomes.

## 6. Failure scenarios to rehearse

### F1 — Primary crypto venue outage

Assumption:

- Bybit unavailable or account access impaired.

Expected response:

- do not send new money to Bybit;
- off-venue reserve remains untouched;
- use backup venue only if independently verified;
- if backup venue is not verified, accept missed execution rather than bypass controls.

PASS criterion:

- survival reserve remains accessible outside the failed venue;
- no architecture rule requires recovery of trapped Bybit funds before the reserve can survive.

### F2 — Primary bank transfer restriction

Assumption:

- primary bank cannot make the required P2P/payment transfer.

Expected response:

- secondary bank already contains at least one execution-envelope equivalent;
- switch to secondary bank route;
- do not first transfer money from the failed primary bank into the secondary bank, because that would defeat independence.

PASS criterion:

- secondary bank can independently originate the required bridge route.

### F3 — RUB P2P liquidity degradation

Assumption:

- spreads widen materially or suitable counterparties disappear.

Expected response:

- do not chase increasingly poor quotes merely to satisfy an arbitrary speed target;
- preserve off-venue reserve;
- evaluate alternate verified venue/rail;
- allow missed execution if no compliant route exists.

PASS criterion:

- architecture can fail safely without forcing conversion at any price.

### F4 — USDT-specific stress

Assumption:

- USDT depeg/redemption/issuer concern or venue suspension.

Expected response:

- no assumption that USDT remains safe because it is a stablecoin;
- pause new USDT bridge use;
- use only a separately pre-verified alternative quote/bridge path if available;
- otherwise preserve bank reserve.

PASS criterion:

- majority of safe capital is not trapped in USDT/common crypto infrastructure.

### F5 — Weekend / holiday crisis

Assumption:

- crypto market is open while some traditional rails are slower or unavailable.

Expected response:

- H1 relies only on the venue execution buffer;
- no promise that the full survival reserve becomes immediately deployable;
- H24/H72 are evaluated using observed actual rail availability.

PASS criterion:

- architecture does not require impossible instant bank settlement to maintain the frozen strategy design.

### F6 — Account-security lock

Assumption:

- primary crypto account is temporarily locked by security/risk controls.

Expected response:

- do not create a new account to bypass controls;
- preserve off-venue reserve;
- use independently verified backup venue only if compliant and already established.

PASS criterion:

- safe capital remains outside the locked account.

### F7 — Secondary-bank unavailable during primary-venue failure

Assumption:

- one bank and one crypto venue fail simultaneously.

Expected response:

- check whether the remaining bank + backup venue pair forms a genuinely independent route;
- if not, accept delayed deployment.

PASS criterion:

- capital survival takes priority over forced execution.

## 7. Evidence log required for any future live drill

For every route attempt record:

- UTC start timestamp;
- local timestamp;
- bank used;
- crypto venue used;
- payment method;
- amount in RUB;
- implied USD-equivalent at contemporaneous reference FX;
- quote asset amount;
- advertised P2P rate;
- market/reference rate used for spread comparison;
- counterparty completion statistics visible before selection;
- order accepted timestamp;
- bank payment sent timestamp;
- crypto released timestamp;
- asset visible in Funding account timestamp;
- internal transfer complete timestamp;
- asset tradable timestamp;
- fees;
- failed/retried steps;
- screenshots/export references;
- any AML/security/risk-control messages.

Do not keep the only evidence inside the exchange app.

## 8. PASS / WARN / FAIL logic

### H1

`PASS` if the pre-positioned execution envelope is actually usable on the intended venue/product.

`WARN` if only part of the envelope is usable because of product/min-order/security restrictions.

`FAIL` if the architecture requires external funding to meet ordinary immediate execution needs.

### H24

`PASS` if the primary route restores one execution-envelope equivalent within 24 hours under normal conditions with acceptable documented spread/fees.

`WARN` if it completes inside 24h but requires manual escalation, unusual counterparty selection, or materially adverse cost.

`FAIL` if it cannot complete inside 24h or violates account/compliance constraints.

### H72

`PASS` if a genuinely independent backup path restores one execution-envelope equivalent within 72 hours.

`WARN` if the path works but shares a material failure domain not previously recognized.

`FAIL` if the backup still depends on the failed primary bank/venue/account or cannot restore capacity inside 72h.

## 9. Stop conditions

Immediately stop a future operational drill if:

- payment instructions require a third-party account inconsistent with platform rules;
- the counterparty asks to move communication/payment outside the platform;
- the bank raises a fraud/AML warning that requires review;
- the exchange account enters a security/risk lock;
- the quote/spread is materially outside the precommitted acceptance range;
- the user cannot preserve transaction evidence;
- the route requires changing strategy rules or forward clocks.

A stopped drill is not a research failure by itself; it is evidence about the route.

## 10. Interaction with R009 / R010 / R003

- R009 and R010 signals are not used to time the operational drill.
- Do not wait for a market crash to conduct the first transfer test.
- Do not use early forward P&L to decide which bank/venue route to test.
- R003 collateral is not part of this directional safe-sleeve drill.
- A later R003 collateral drill must be separate because its 50/50 fully funded construction has different failure mechanics.

## 11. S002-E result

> **S002-E: CRISIS_DRILL_DESIGNED**

The architecture now has precommitted H1/H24/H72 definitions, failure scenarios, evidence requirements and stop conditions.

No real-money drill has been authorized or executed.

The next valid S002 step is to decide whether the existing evidence is sufficient for a provisional `IMPLEMENTATION_CANDIDATE` status or whether backup-venue/account and exact Bybit BTC spot mechanics should be checked first.

## 12. Research invariants

- R009-E002 inception remains `2026-09-10 00:00 UTC`;
- R003-E003 Binance boundary remains `2026-09-10 12:00 UTC`; future retry requires the causality-safe hotfix and no reset;
- R003-X003 Bybit boundary remains `2026-09-10 16:00 UTC` and separate from Binance;
- R010-E001 inception remains `2026-09-11 00:00 UTC`;
- R010 thresholds, weights and ATH reset remain frozen;
- inherited R010 armed tranches are not prospective validation;
- R009 remains unchanged and is not replaced by R010;
- no real-money deployment;
- broad platform development remains frozen.
