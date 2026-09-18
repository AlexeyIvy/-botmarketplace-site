# SC001 — C11 v2 Fresh-Chronology Contamination / Source Audit v0.1

Date: 2026-09-19
Status: **C11_V2_FRESH_CHRONOLOGY_AUDIT_PASS — CLEAN CANDIDATE CHRONOLOGY IDENTIFIED / EXACT ARCHIVE METADATA STILL CLOSED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/dialog-handoff-2026-09-18-v6.0.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.71.md`;
- `docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.17.json`;
- `docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md`.

## 1. Purpose

Audit candidate later C11 chronology before any new BTC price outcome is opened.

This audit is contamination/source governance only. It does **not** authorize:

- historical trade-body GET/open for the fresh candidate events;
- first-impulse calculation;
- residual +1s -> +60s movement calculation;
- direction/continuation calculation;
- Confirmation access;
- execution/fill/PnL work.

## 2. Binding prior contamination

H1-2025 remains nonpromotional for C11 v2.

Exact prior C11 directional Selection/Calibration window:

`2025-01-01 through 2025-06-30`

with 12 CPI / Employment events.

H1-2025 was used for:

- C11-S0 raw event-move headroom;
- C11-S1 first-impulse continuation;
- the 2025-05-02 zero-first-impulse diagnostic.

Therefore H1-2025 is **CONTAMINATED_FOR_C11_V2_DIRECTION_DESIGN** and cannot be reused as fresh v2 evidence.

## 3. What does not by itself contaminate a later period

The old `SC001-MICRO-CALENDAR-v0.1` covered a FINAL range of 2025-07-01 through 2026-08-31, but its build explicitly read no price, return, spread, volatility, strategy output or P&L.

Therefore:

`CALENDAR_RESERVED != PRICE_OUTCOME_CONTAMINATED`

The old calendar can be evidence that dates were prospectively enumerated, but it is not itself evidence that later BTC outcomes were opened.

Likewise, engineering/schema-only qualification is not automatically strategy-outcome contamination. The known 2026-07-15 qualification-only OKX L2 date is not a C11 CPI/Employment event date.

## 4. Repository exact-date audit

Repository search was performed for every candidate CPI / Employment event date listed below.

No candidate Selection/Calibration event date was found in a C11-relevant or other SC001 price-bearing outcome artifact.

For the candidate Confirmation dates, the few exact-date hits were non-C11-contextual:

- 2026-04-10 — platform/test-roadmap material, not SC001 event outcome;
- 2026-05-08 — deployment incident comment, not SC001 event outcome;
- 2026-05-12 — platform baseline timestamp, not SC001 event outcome;
- 2026-06-05 — R010 independent-branch historical state, not SC001 event outcome;
- 2026-09-11 — primarily document/project dates and SC001 setup/data-engineering records, not C11 price outcome.

Under the SC001 independence boundary, these do not constitute C11 v2 Selection/Confirmation outcome access.

If later evidence shows that any candidate event body/outcome was actually inspected for C11-relevant feature, threshold, horizon, direction or strategy selection, that date must fail closed and this audit must be versioned rather than silently amended.

## 5. Source audit

C11-D0 already established:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

with:

- official BLS event-clock semantics qualified;
- OKX `BTC-USDT-SWAP-trades-YYYY-MM-DD.zip` resolver/metadata path qualified on representative CPI and Employment events;
- historical price bodies unopened at D0.

The H1 C11-D1 protocol established the exact metadata-only pattern that must be reused for a fresh chronology:

1. official BLS date + 08:30 AM ET check;
2. exact OKX archive identity/HEAD check;
3. no body GET/open;
4. no macro value/surprise;
5. no BTC outcome.

Important boundary:

**D0 source semantics do not prove that every new candidate archive exists.**

Exact archive identity/HEAD for the fresh events remains a required metadata-only preflight before any fresh price body is authorized.

## 6. Q4-2025 source/calendar anomaly

Q4-2025 is not classified as price-contaminated by this audit.

However, official BLS records show a lapse-in-appropriations release disruption:

- some releases were delayed;
- CPI for October 2025 was canceled;
- other CPI/Employment releases moved materially from their ordinary cadence.

Therefore Q4-2025 is classified:

`SOURCE_CALENDAR_IRREGULAR_NOT_PRIMARY_FRESH_CHRONOLOGY`

This exclusion is based only on official release-calendar structure before opening C11 BTC outcomes. It is **not** based on BTC movement or strategy performance.

Official source references:

- https://www.bls.gov/schedule/2025/
- https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm

## 7. Clean candidate Selection/Calibration chronology

Preferred clean candidate chronology after audit:

`2025-Q3 + 2026-Q1`

Exactly 12 scheduled C11 events, six CPI and six Employment:

### 2025-Q3

- 2025-07-03 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-07-15 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2025-08-01 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-08-12 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2025-09-05 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2025-09-11 — Consumer Price Index — 08:30 ET / 12:30 UTC.

### 2026-Q1

- 2026-01-09 — Employment Situation — 08:30 ET / 13:30 UTC;
- 2026-01-13 — Consumer Price Index — 08:30 ET / 13:30 UTC;
- 2026-02-11 — Employment Situation — 08:30 ET / 13:30 UTC;
- 2026-02-13 — Consumer Price Index — 08:30 ET / 13:30 UTC;
- 2026-03-06 — Employment Situation — 08:30 ET / 13:30 UTC;
- 2026-03-11 — Consumer Price Index — 08:30 ET / 12:30 UTC.

Rationale:

- chosen by calendar/source structure, not BTC outcome;
- exact-date repo audit found no C11-relevant price-bearing use;
- retains 12-event scale comparable to the original H1 calibration while avoiding reuse of contaminated H1;
- preserves both event families with six instances each;
- Q4-2025 is skipped for an objective official-calendar disruption reason, not performance.

This is an **audit recommendation**, not yet the formal chronology freeze.

## 8. Untouched candidate Confirmation chronology

Preferred later untouched Confirmation reserve:

`2026-Q2 + 2026-Q3`

Exactly 12 events, six CPI and six Employment:

- 2026-04-03 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-04-10 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2026-05-08 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-05-12 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2026-06-05 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-06-10 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2026-07-02 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-07-14 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2026-08-07 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-08-12 — Consumer Price Index — 08:30 ET / 12:30 UTC;
- 2026-09-04 — Employment Situation — 08:30 ET / 12:30 UTC;
- 2026-09-11 — Consumer Price Index — 08:30 ET / 12:30 UTC.

The previous 2026-07-15 qualification-only OKX date is adjacent to, but does not overlap, the 2026-07-14 CPI event.

Confirmation remains **CLOSED**.

No rule, gate, threshold or implementation may be changed using Confirmation outcomes because none are authorized to be opened at this stage.

## 9. Audit disposition

Exact audit state:

`C11_V2_FRESH_CHRONOLOGY_AUDIT_PASS`

Meaning:

- a defensible fresh candidate Selection/Calibration chronology exists;
- a later untouched candidate Confirmation reserve exists;
- H1-2025 remains contaminated;
- Q4-2025 is source/calendar-irregular and not preferred for the primary v2 chronology;
- no fresh BTC price outcome has been opened by this audit;
- exact OKX archive metadata for the candidate fresh dates is still unverified and must be checked metadata-only.

This is not:

- a direction-rule PASS;
- a headroom PASS;
- a strategy PASS;
- permission to open Confirmation;
- permission to model execution/PnL.

## 10. Immediate next action

Before any BTC trade body is opened:

1. create a formal fresh chronology freeze using the 12 + 12 candidate event lists, subject only to objective source correction;
2. run/prepare a metadata-only D1-style official-calendar + exact OKX archive HEAD preflight for all frozen dates;
3. keep Selection/Calibration and Confirmation identities separate in the contamination registry;
4. only after metadata PASS, freeze C11 Direction Rule v2 plus Stage A/Stage B gates;
5. only then authorize fresh Selection/Calibration price outcome.

No VPS price-bearing run is authorized by this audit.
