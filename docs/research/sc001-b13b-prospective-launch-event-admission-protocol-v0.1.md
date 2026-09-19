# SC001 — B13-B Prospective Launch Event Admission Protocol v0.1

Date: 2026-09-19
Status: **FROZEN PROSPECTIVE EVENT GOVERNANCE / NO PRICE OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.92.md`;
- `docs/research/sc001-b13b-cross-venue-underlying-identity-audit-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.25.json`.

## 1. Purpose

Define the only allowed future evidence path for B13-B after the historical S0 was deferred by cross-venue underlying-identity failures.

No historical launch may be substituted into this prospective stream.

## 2. Prospective boundary

Only OKX launch events first identified and admitted **after 2026-09-19 governance freeze** may enter this stream.

An event must be admitted before any launch-day price/body outcome is opened.

## 3. Required OKX identity fields

Before admission record from official OKX sources:

- instrument ID;
- asset class: crypto / equity / commodity / ETF / other;
- full underlying/project/company name;
- ticker;
- base/quote;
- exact listTime;
- official announcement URL;
- contract type;
- settlement currency;
- face value / contract value;
- price quotation unit;
- index/underlying description.

Ticker equality alone is never sufficient.

## 4. Required Bybit reference fields

For the exact proposed mature reference record:

- symbol;
- asset class;
- full underlying/project/company name;
- base/quote;
- launchTime;
- official announcement/product reference where available;
- contract type;
- settlement currency;
- price quotation unit / denomination semantics.

## 5. Same-underlying admission gate

PASS only if all:

1. same asset class;
2. same identifiable underlying/project/company;
3. same economic unit after explicit quotation normalization;
4. same quote currency family compatible with direct USDT comparison;
5. Bybit launchTime at least 90 calendar days before OKX listTime.

If any identity field is ambiguous:

`B13B_PROSPECTIVE_IDENTITY_REVIEW`

No price access.

If clearly different:

`B13B_PROSPECTIVE_EVENT_NOT_ELIGIBLE`

No replacement is chosen based on expected price behavior.

## 6. Price-denomination gate

Before price access, freeze an explicit normalization statement.

Examples:

- both prices quote 1 base token -> multiplier 1;
- one venue quotes N base tokens -> normalize prospectively by exact documented N;
- equity/ETF versus crypto -> not compatible;
- any unresolved denomination -> REVIEW.

No multiplier may be inferred from observed cross-venue price ratios.

## 7. Source-availability gate

Before price access verify metadata/HEAD only for:

- exact OKX launch-day historical/public trade source;
- exact Bybit same-underlying launch-day public trade source.

No trade body opened during admission.

## 8. Prospective event record

Every admitted event receives an append-only record containing:

- admission timestamp;
- all identity fields;
- source URLs/identities;
- quotation normalization;
- mature-reference age;
- source availability;
- exact status.

Allowed status:

- `B13B_PROSPECTIVE_EVENT_ADMITTED`;
- `B13B_PROSPECTIVE_IDENTITY_REVIEW`;
- `B13B_PROSPECTIVE_EVENT_NOT_ELIGIBLE`;
- `B13B_PROSPECTIVE_SOURCE_REVIEW`.

## 9. Outcome firewall

Admission itself does not authorize:

- launch price/body access;
- basis calculation;
- convergence;
- signal;
- execution;
- PnL.

A separate future event-outcome freeze is required.

## 10. Formal sample rule

No formal B13-B candidate promotion or Confirmation verdict is allowed until a future protocol freezes:

- minimum prospective admitted event count;
- launch headroom metric;
- convergence metric;
- structural burden;
- stop rules.

Those counts must be frozen before consuming future prospective outcomes for a formal verdict.

## 11. Historical boundary

The historical seven-event calibration set remains closed.

Do not:

- replace BB/QNT;
- mine additional 2026 historical launches;
- merge historical events into the prospective denominator;
- reuse raw historical SURVIVE as promotional evidence.
