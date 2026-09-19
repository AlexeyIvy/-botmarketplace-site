# SC001 — Current Four-Role Critical Review v0.1

Date: 2026-09-19
Status: **DEEP CROSS-REVIEW COMPLETE / GOVERNANCE CORRECTIONS REQUIRED BEFORE B13-C**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.93.md`;
- `docs/research/sc001-c11-final-three-role-disposition-review-v0.1.md`;
- `docs/research/sc001-b13a-funding-differential-structural-result-v0.3.md`;
- `docs/research/sc001-b13b-cross-venue-underlying-identity-audit-v0.1.md`;
- `docs/research/sc001-b13b-prospective-launch-event-admission-protocol-v0.1.md`.

## 1. Executive conclusion

The main research conclusions survive critical review, but two scopes must be tightened and two process controls must be added.

Binding outcomes that remain unchanged:

- C11 frozen 1-second direction extractor: terminal reject;
- C12 standalone parity-reversion candidate: terminal reject;
- B13-A single-settlement four-fill funding-differential architecture: structural reject;
- B13-B historical 7-event S0: DEFER after semantic identity failure.

Required improvements:

1. narrow B13-A interpretation to the tested architecture, not every conceivable funding-carry architecture;
2. strengthen B13-B prospective admission from ticker/launchTime checks to full economic-unit and standard-perpetual maturity checks;
3. add a mandatory pre-outcome semantic-identity gate for every cross-venue study;
4. add implementation handshake/fixture self-tests before remote outcome runs.

No new market outcome is opened by this review.

---

## 2. Programmer / systems-engineer review

### 2.1 What worked

The research kernel now has strong fail-closed behavior:

- Git-blob implementation freezes;
- explicit contamination registry;
- exact terminal tokens;
- DATA_INVALID / NO_TRADE separation;
- source body firewalls;
- append-only versioning;
- schema-drift handling;
- one-shot guards.

These controls prevented engineering defects from being misclassified as strategy outcomes.

### 2.2 What failed operationally

Several remote iterations failed for avoidable implementation reasons:

- BLS day zero-padding parser;
- raw-HTML versus visible-text parser;
- OKX trade CSV schema drift;
- OKX metadata response-wrapper assumption;
- stale freeze-status literal.

These failures did not contaminate strategy outcomes, but they consumed operator time and reveal insufficient local preflight coverage.

### 2.3 Required improvement: implementation self-test

Before any future outcome-bearing VPS run, require a local/static self-test that verifies:

- runner compiles;
- freeze file exists;
- runner expected freeze-status equals actual freeze-status;
- every frozen SHA path resolves;
- exact event/universe counts match;
- parser fixture accepts all explicitly allowed schemas;
- parser fixture rejects an unknown schema;
- metadata-response walker is tested on a representative stored/fixture shape;
- output path/version cannot collide with a prior terminal result.

A runner that cannot pass this self-test cannot be launched remotely.

### 2.4 Required improvement: semantic sign-off before price

The B13-B false raw SURVIVE demonstrates that syntactic symbol identity is not enough.

For cross-venue work, source-semantic identity must be frozen before price access.

Required fields:

- asset class;
- full underlying identity;
- economic unit / price denominator;
- contract status (pre-market vs standard);
- listing/trading-open timestamp;
- quote/settlement;
- exact reference maturity start.

No cross-venue price ratio is authorized before this sign-off.

---

## 3. Trader review

### 3.1 C11

The C11 conclusion survives critique.

Strength:

- raw and residual movement is clearly real;
- the tested 1-second sign extractor is weak.

Observed:

- median residual abs move ~24.11 bps;
- median signed continuation ~3.63 bps;
- only 6/24 events reached >=20 bps in the selected direction.

Even if exact execution burden were somewhat below the frozen 20 bps reference, the directional extractor remains too weak and unstable to justify Confirmation.

Trader interpretation:

`MACRO_EVENT_MOVEMENT_IS_REAL / TESTED_DIRECTION_RULE_NOT_TRADABLE`

No C11 rescue.

### 3.2 C12

The C12 rejection also survives critique.

Three episodes concentrated in one month cannot support a systematic standalone strategy regardless of the descriptive 2/3 reversion rate.

The parity-stress state remains useful as risk context, not alpha.

### 3.3 B13-A

The tested B13-A architecture is decisively unattractive:

- median funding differential ~0.41 bps;
- p99 ~2.22 bps;
- maximum ~27.34 bps;
- frozen four-fill burden = 40 bps.

The maximum itself failed to reach break-even.

However the correct scope is:

`SINGLE_SETTLEMENT_FOUR_FILL_FUNDING_DIFFERENTIAL_ARCHITECTURE_REJECTED`

not:

`ALL_POSSIBLE_CROSS_VENUE_FUNDING_CARRY_REJECTED`.

A persistent multi-settlement carry would be a materially different mechanism with:

- longer capital lock;
- changing funding sign;
- cross-venue basis risk;
- liquidation/margin risk;
- venue/counterparty risk;
- collateral fragmentation;
- different fill amortization.

It may only re-enter through a new base-mechanism card and fresh evidence.

It is not a priority rescue.

### 3.4 B13-B

The economic intuition remains interesting because non-collision raw launch bases were large.

But the historical runner cannot support a tradable claim because:

- two ticker collisions were invalid;
- KITE requires exact price-denominator normalization;
- MEGA Bybit reference had pre-market history and converted to standard perpetual on the same day as the OKX launch;
- launch timestamp semantics require stronger corroboration;
- initial launch price may face special listing/pre-open risk controls.

Therefore prospective-only continuation is correct.

---

## 4. Financial review

### 4.1 Cost assumptions

The project has generally erred conservatively on cost, which is desirable at the structural-screen stage.

For C11, higher real event slippage would only strengthen rejection.

For B13-A, the 40 bps four-fill burden excludes several real risks:

- collateral fragmentation;
- funding sign changes during legging;
- cross-venue transfer/counterparty risk;
- basis drift while holding;
- liquidation buffer.

Therefore B13-A single-settlement rejection is economically robust.

### 4.2 B13-A persistent carry caveat

Longer-horizon carry could amortize entry/exit fills across multiple funding events, but that does not automatically improve economics.

The relevant future quantity would be:

`cumulative realized cross-venue funding transfer - basis/margin/capital risk`

not one-event differential.

This is a new architecture and cannot use H1-2025 as fresh evidence after the current screen.

### 4.3 B13-B launch headroom

Large raw launch basis is not equivalent to realizable arbitrage.

Before any future execution design require:

- same economic unit;
- simultaneously tradable standard contracts;
- realistic shortability / order availability;
- launch price limits;
- depth/spread/legging reserve;
- whether the reference contract is truly mature standard trading, not pre-market.

The first price-bearing prospective test should remain a headroom/mechanism test, not PnL.

---

## 5. Mathematics / statistics review

### 5.1 Gate semantics

Current frozen gates are useful as engineering/research sentinels.

They are not formal statistical significance tests.

This distinction should remain explicit.

### 5.2 C11 uncertainty

Examples of descriptive binomial uncertainty if events were IID:

- 14/24 positive signed continuation -> 95% Wilson interval approximately 39%-76%;
- 6/24 signed continuation >=20 bps -> approximately 12%-45%.

Events are not truly IID, so these intervals should not be used as formal inference.

The important C11 conclusion is magnitude-based, not p-value based:

median signed continuation ~3.63 bps versus a 20 bps structural reference.

That gap makes the rejection robust.

### 5.3 C12 uncertainty

2/3 reversion success has an extremely wide interval and one-month clustering.

The project correctly refuses to treat 66.7% as a stable probability estimate.

### 5.4 B13-A pseudo-sample-size risk

6,634 matched settlements are not 6,634 independent observations:

- symbols share market regimes;
- funding schedules cluster in time;
- cross-venue rates co-move.

Do not attach IID p-values to that count.

The robust result is simpler:

within the frozen six-month 12-symbol sample, the observed maximum differential (~27.34 bps) was below the frozen 40 bps burden.

Generalization beyond that regime remains a separate question.

### 5.5 B13-B small-N and survivor censoring

Even five apparently valid historical events all above 50 bps would not establish a stable probability.

A nominal 5/5 success rate has very wide small-sample uncertainty even before survivor-censoring and semantic issues.

Therefore prospective accumulation is mandatory.

### 5.6 Multiple-testing discipline

SC001 has now evaluated many mechanisms.

Any future positive sentinel is subject to researcher-selection pressure even when each individual protocol is frozen.

Required rule:

`SELECTION-SURVIVE != CONFIRMATION`

Every future positive candidate must earn prospective evidence after candidate design is frozen.

---

## 6. Newly identified B13-B source-semantic issues

### 6.1 KITE price denominator

Official OKX launch documentation states:

- face value = 10;
- price quotation = value of 10 KITE in USDT.

Therefore direct comparison to another venue requires explicit normalization to the same economic unit before taking a log price ratio.

No normalization may be inferred from observed prices.

### 6.2 MEGA reference maturity

Bybit MEGAUSDT existed as a pre-market perpetual before April 30, 2026 and was converted to a standard perpetual on April 30, 2026.

Therefore old Bybit `launchTime` can materially overstate maturity of the standard reference contract.

Future B13-B maturity must be measured from:

`STANDARD_PERPETUAL_AVAILABLE_TIME`

not generic first/pre-market launch time.

### 6.3 Launch-time source reconciliation

For future events record both:

- API listTime;
- official announcement trading-open timestamp.

If they disagree, event status must be:

`IDENTITY/TIME_REVIEW`

until resolved.

No price bucket may be anchored to an unresolved timestamp.

---

## 7. Corrected project-level conclusions

### C11

Keep:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

Scope:

tested first-causal-1s sign extractor only.

Retain macro-event movement risk state.

### C12

Keep:

`C12_S0_REJECT_PARITY_REVERSION`

Retain rare parity-stress state only.

### B13-A

Keep exact protocol verdict:

`B13A_REJECT_STRUCTURAL`

Interpretation narrowed to:

`SINGLE_SETTLEMENT_FOUR_FILL_ARCHITECTURE_REJECTED`

Do not generalize to every possible persistent funding-carry design.

### B13-B

Keep binding historical state:

`B13B_S0_DEFER_SAMPLE`

Historical branch remains closed.

Prospective admission protocol must be strengthened before future event use.

---

## 8. Required optimization before B13-C

Before moving to B13-C:

1. freeze a generic pre-outcome semantic/implementation gate;
2. supersede B13-B prospective admission protocol with standard-maturity, denominator and launch-time reconciliation;
3. update roadmap to reflect narrowed B13-A interpretation;
4. do not launch any new outcome run during these governance corrections.

After these changes, B13-C source/data-feasibility audit may begin.
