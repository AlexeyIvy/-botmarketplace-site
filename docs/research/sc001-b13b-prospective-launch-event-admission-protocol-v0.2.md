# SC001 — B13-B Prospective Launch Event Admission Protocol v0.2

Date: 2026-09-19
Status: **FROZEN PROSPECTIVE EVENT GOVERNANCE / STRENGTHENED AFTER FOUR-ROLE REVIEW**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-b13b-prospective-launch-event-admission-protocol-v0.1.md`

Parents:

- `docs/research/sc001-current-four-role-critical-review-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`;
- `docs/research/sc001-b13b-cross-venue-underlying-identity-audit-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.25.json`.

## 1. Prospective boundary

Only OKX launch events first identified and admitted after the 2026-09-19 governance freeze may enter.

No historical replacement.

No launch price/body outcome before admission.

## 2. OKX identity package

Require official OKX evidence for:

- instrument ID;
- asset class;
- full underlying/project/company name;
- ticker;
- base/quote;
- API listTime;
- official announcement trading-open timestamp;
- official announcement URL;
- contract type;
- settlement currency;
- face value / contract value;
- price quotation unit;
- index/underlying description.

## 3. OKX time reconciliation

API `listTime` and official announcement trading-open timestamp must agree within a frozen source-tolerance of:

`<=60 seconds`

If they do not:

`B13B_PROSPECTIVE_EVENT_TIME_REVIEW`

No price access.

No source is silently preferred because it produces cleaner price behavior.

## 4. Bybit reference package

Require:

- symbol;
- asset class;
- full underlying/project/company name;
- base/quote;
- API launchTime;
- whether launchTime refers to pre-market or standard perpetual;
- official standard-perpetual listing/conversion timestamp when pre-market existed;
- contract type;
- settlement currency;
- price quotation unit;
- denomination/contract-size semantics;
- official announcement/product references where available.

## 5. Standard-maturity clock

The 90-day maturity rule applies to:

`STANDARD_PERPETUAL_AVAILABLE_TIME`

not generic/pre-market launchTime.

If the Bybit contract began in pre-market and converted later:

`reference_age = OKX trading-open time - Bybit standard-perpetual conversion time`

Require:

`reference_age >=90 calendar days`

MEGA-style same-day conversion therefore would not qualify as a mature reference.

## 6. Same-underlying gate

PASS only if:

1. same asset class;
2. same identifiable underlying/project/company;
3. same economic unit after documented normalization;
4. quote/settlement compatible with direct USDT relative-price comparison;
5. standard Bybit reference age >=90 days.

Ticker equality alone is insufficient.

## 7. Price-denomination gate

Before any future price access freeze:

- OKX quote unit;
- Bybit quote unit;
- exact multiplicative normalization to one common base-unit price.

If either venue quotes N tokens per price unit, normalize using official documentation only.

No multiplier may be inferred from observed price ratio.

Unresolved:

`B13B_PROSPECTIVE_DENOMINATION_REVIEW`

No price access.

## 8. Source-availability gate

Verify metadata/HEAD only for exact launch-day sources on both venues.

No trade body opened during admission.

## 9. Allowed admission states

- `B13B_PROSPECTIVE_EVENT_ADMITTED`;
- `B13B_PROSPECTIVE_IDENTITY_REVIEW`;
- `B13B_PROSPECTIVE_EVENT_TIME_REVIEW`;
- `B13B_PROSPECTIVE_DENOMINATION_REVIEW`;
- `B13B_PROSPECTIVE_EVENT_NOT_ELIGIBLE`;
- `B13B_PROSPECTIVE_SOURCE_REVIEW`.

## 10. Outcome firewall

Admission itself never authorizes:

- trade-body price outcome;
- launch basis;
- convergence;
- strategy signal;
- execution;
- PnL.

A future event-outcome implementation freeze is required.

## 11. Formal sample rule

Before consuming future prospective outcomes for a formal B13-B verdict, separately freeze:

- minimum prospective admitted event count;
- headroom metric;
- convergence metric;
- structural burden;
- stop rules;
- confirmation role.

## 12. Historical boundary

Historical seven-event calibration remains closed.

Do not merge it into prospective denominator.

Do not rescue BB/QNT.

Do not use raw historical SURVIVE as promotional evidence.
