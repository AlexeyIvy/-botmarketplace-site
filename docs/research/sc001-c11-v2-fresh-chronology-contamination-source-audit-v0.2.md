# SC001 — C11 v2 Fresh-Chronology Contamination / Source Audit v0.2

Date: 2026-09-19
Status: **CORRECTED AUDIT — E001 COARSE-PRICE EXPOSURE INCORPORATED / PROSPECTIVE CONFIRMATION REQUIRED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `docs/research/sc001-c11-v2-fresh-chronology-contamination-source-audit-v0.1.md`

Parents:

- `docs/research/sc001-e001-results-v0.1.md`;
- `docs/research/sc001-e001-pretest-freeze-v0.1.md`;
- `docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.18.json`;
- `docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md`.

## 1. Why v0.2 is required

The v0.1 audit correctly found no C11-specific price-bearing use of the proposed later event dates, but it did not fully account for an older broad SC001 result:

`SC001-E001`

E001 opened Binance BTCUSDT 1-hour market outcomes across:

`2020-01-01 00:00 UTC through 2026-09-09 19:00 UTC`

and explicitly reported a Final slice covering 2025 through the 2026-09-09 cutoff.

Therefore dates before the E001 cutoff cannot honestly be called globally `PRICE_UNSEEN` within SC001.

This correction does **not** mean C11-specific 1-second/60-second OKX event outcomes were opened. They were not.

The correct distinction is:

- broad/coarse BTC price exposure exists through E001;
- C11-specific OKX event microstructure outcomes remain unopened outside H1-2025.

## 2. Binding H1-2025 state

H1-2025 remains:

`CONTAMINATED_FOR_C11_V2_DIRECTION_DESIGN`

because it was directly used for:

- C11-S0 event-move headroom;
- C11-S1 first-impulse continuation;
- the 2025-05-02 zero-first-impulse diagnostic.

H1-2025 may not be reused as fresh v2 evidence.

## 3. Historical later-period contamination classification

For C11 event dates after H1-2025 and at/before the E001 cutoff, use:

`C11_MICROSTRUCTURE_OUTCOME_UNOPENED_BUT_SC001_COARSE_PRICE_EXPOSED`

Meaning:

- no C11 first-impulse outcome opened;
- no C11 +1s -> +60s continuation outcome opened;
- no C11 event execution/PnL opened;
- but Binance 1-hour BTC outcomes from the same broad chronology were already consumed by E001.

These dates are therefore suitable only for **nonpromotional Selection/Calibration**, not for untouched Confirmation.

The 2026-09-11 CPI event is after the E001 historical cutoff and was not opened by E001, but it is retained with the historical Selection/Calibration pool for a simple calendar rule rather than being selectively promoted.

## 4. Q4-2025 calendar anomaly remains valid

Q4-2025 is not excluded because of BTC behavior.

Official BLS lapse-in-appropriations records show major release disruption, including:

- Employment Situation for October 2025 canceled;
- CPI for October 2025 canceled;
- multiple other releases delayed.

Official source:

https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm

Classification:

`SOURCE_CALENDAR_IRREGULAR_INCOMPLETE_CORE_FAMILY_CADENCE`

For the primary C11 v2 historical Selection/Calibration chronology, Q4-2025 is excluded as a whole to avoid mixing a quarter with missing core CPI/Employment release identities into an otherwise complete two-family monthly event design.

This exclusion is source/calendar based and was fixed before C11 v2 outcomes.

## 5. Improved historical Selection/Calibration design

Instead of using only 12 later events, v0.2 uses every complete CPI + Employment release in the audited non-Q4 blocks before the current freeze:

- 2025-Q3;
- 2026-Q1;
- 2026-Q2;
- 2026-Q3.

Total:

- CPI = 12;
- Employment Situation = 12;
- total event releases = 24.

Why this is stronger:

1. the direction rule and gates will be frozen **before** these C11-specific outcomes are opened;
2. all events are chosen by calendar, not BTC movement;
3. using 24 rather than 12 reduces small-N fragility;
4. no historical Confirmation reserve is needed because Confirmation is moved to a truly prospective future block;
5. Q4-2025 is excluded only for documented missing/canceled core releases.

This 24-event batch is:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

It must never later be relabeled as untouched Confirmation.

## 6. Exact historical Selection/Calibration release chronology

All releases are official BLS 08:30 ET releases.

### 2025-Q3

- 2025-07-03 — Employment Situation — 12:30 UTC;
- 2025-07-15 — Consumer Price Index — 12:30 UTC;
- 2025-08-01 — Employment Situation — 12:30 UTC;
- 2025-08-12 — Consumer Price Index — 12:30 UTC;
- 2025-09-05 — Employment Situation — 12:30 UTC;
- 2025-09-11 — Consumer Price Index — 12:30 UTC.

### 2026-Q1

- 2026-01-09 — Employment Situation — 13:30 UTC;
- 2026-01-13 — Consumer Price Index — 13:30 UTC;
- 2026-02-11 — Employment Situation — 13:30 UTC;
- 2026-02-13 — Consumer Price Index — 13:30 UTC;
- 2026-03-06 — Employment Situation — 13:30 UTC;
- 2026-03-11 — Consumer Price Index — 12:30 UTC.

The February 2026 dates are the official revised release dates following the 2026 lapse in appropriations. No event is removed merely because its date was revised.

### 2026-Q2

- 2026-04-03 — Employment Situation — 12:30 UTC;
- 2026-04-10 — Consumer Price Index — 12:30 UTC;
- 2026-05-08 — Employment Situation — 12:30 UTC;
- 2026-05-12 — Consumer Price Index — 12:30 UTC;
- 2026-06-05 — Employment Situation — 12:30 UTC;
- 2026-06-10 — Consumer Price Index — 12:30 UTC.

### 2026-Q3

- 2026-07-02 — Employment Situation — 12:30 UTC;
- 2026-07-14 — Consumer Price Index — 12:30 UTC;
- 2026-08-07 — Employment Situation — 12:30 UTC;
- 2026-08-12 — Consumer Price Index — 12:30 UTC;
- 2026-09-04 — Employment Situation — 12:30 UTC;
- 2026-09-11 — Consumer Price Index — 12:30 UTC.

The old qualification-only date 2026-07-15 does not overlap any of these event releases.

## 7. Stronger untouched Confirmation design

The prior v0.1 proposal to use 2026-Q2 + 2026-Q3 as Confirmation is withdrawn because those dates are inside the E001 broad 1-hour historical exposure window.

The new Confirmation is fully prospective relative to this audit/freeze.

Freeze exact **event identities by reference month**, not by market outcome:

Reference months:

`September 2026 through February 2027`

For each reference month include exactly:

1. Employment Situation;
2. Consumer Price Index.

Total frozen slots:

`12`

This makes the identity rule exact even where 2027 publication dates are not yet published.

Known official future release dates at the time of this freeze include:

- Employment Situation, reference September 2026 -> 2026-10-02 08:30 ET;
- CPI, reference September 2026 -> 2026-10-14 08:30 ET;
- Employment Situation, reference October 2026 -> 2026-11-06 08:30 ET;
- CPI, reference October 2026 -> 2026-11-10 08:30 ET;
- Employment Situation, reference November 2026 -> 2026-12-04 08:30 ET;
- CPI, reference November 2026 -> 2026-12-10 08:30 ET.

The remaining six 2027 release dates are not selected later. Their identities are already frozen by family + reference month.

## 8. Future calendar revision / cancellation rule

For the prospective Confirmation slots:

- event identity is `family + reference_month`;
- official release timestamp comes only from BLS;
- if BLS revises a date/time before publication, use the final official scheduled timestamp without changing the event identity;
- no replacement is selected because market conditions look preferable;
- if a frozen release identity is canceled, record `CALENDAR_CANCELED`;
- a canceled slot is not replaced by another event;
- price outcome is not fabricated for a canceled slot.

For reporting, preserve:

`frozen_slots -> released_events -> data_valid -> actionable -> executed`

Signal state on a released data-valid event remains one of:

- NO_TRADE;
- LONG;
- SHORT.

DATA_INVALID remains separate.

## 9. Source status

Existing C11 source semantics remain qualified:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

But exact OKX archive identity/HEAD has not yet been verified for the new 24-event Selection/Calibration set.

Therefore the next allowed step remains metadata-only:

- official BLS date/time check;
- exact OKX archive identity;
- HEAD Content-Length;
- no historical trade-body GET/open;
- no first impulse;
- no residual move;
- no direction;
- no PnL.

## 10. Corrected audit verdict

Exact state:

`C11_V2_FRESH_CHRONOLOGY_AUDIT_V02_PASS`

Interpretation:

- v0.1 was too strong in calling the historical 2025-2026 blocks clean without qualifying E001 coarse-price exposure;
- historical later events remain usable for nonpromotional C11-specific Selection/Calibration;
- untouched Confirmation is moved to a truly prospective future 12-slot block;
- no new C11 price outcome was opened by this correction.

## 11. Immediate next action

1. freeze the exact 24-event historical Selection/Calibration set;
2. freeze the 12 prospective Confirmation identities;
3. prepare and freeze a metadata-only 24-event Selection/Calibration source/archive preflight;
4. syntax-check the runner;
5. only after metadata PASS freeze Direction Rule v2 and Stage A/B gates;
6. only then authorize Selection/Calibration price outcomes.

No VPS price-bearing run is authorized.
