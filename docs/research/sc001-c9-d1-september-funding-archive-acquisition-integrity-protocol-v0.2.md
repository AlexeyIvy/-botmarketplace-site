# SC001 — C9-D1 September Funding Archive Acquisition / Integrity Protocol v0.2

Date: 2026-09-18  
Status: **FROZEN SOURCE-BOUNDARY REPAIR AFTER v0.1 REVIEW / DATA-ONLY**  
Scope: `SCALPING RESEARCH / SC001`  
Supersedes: `sc001-c9-d1-september-funding-archive-acquisition-integrity-protocol-v0.1.md`

## 1. Trigger

C9-D1 v0.1 returned:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

because every inspected target stream contained a timestamp exactly equal to:

`1727712000000 = 2024-09-30T16:00:00Z = 2024-10-01T00:00:00+08:00`

and v0.1 used a strict half-open source-month check.

No strategy outcome, return, signal, threshold, event window or PnL was calculated.

## 2. Boundary semantics repair

The authorized source archive remains exactly:

`2024-09 UTC+8 FundingRate archive month`

Base source boundary:

- start = `2024-08-31T16:00:00Z`;
- archive end boundary = `2024-09-30T16:00:00Z`.

For funding-row integrity only, v0.2 admits:

`start <= funding_time <= archive_end_boundary`

The exact end-boundary timestamp is allowed because it is physically present in the official September archive.

Any target funding timestamp:

`funding_time > archive_end_boundary`

is a hard failure.

No later October UTC date/body is authorized.

## 3. Contamination interpretation

The allowed boundary event is on UTC date `2024-09-30`.

September 15-30 for the frozen eight assets was prospectively classified as:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

before D1 body access.

Therefore this repair introduces no new contaminated date.

## 4. All other v0.1 rules remain binding

Unchanged:

- exact eight-asset universe;
- exact D0 parent PASS;
- exact September metadata/file identity match;
- HEAD Content-Length match;
- SHA256;
- ZIP CRC;
- CSV schema;
- finite funding-rate validation;
- identical-only duplicate deduplication;
- >=80 unique funding timestamps;
- positive consecutive intervals;
- maximum consecutive interval <=8h;
- start/end coverage <=8h;
- no mark/index values opened in D1;
- no returns/basis transition/signal/sentinel/PnL;
- no direction/threshold/event-window selection;
- no July or October funding body;
- no protected/promotional body access.

## 5. Reuse rule

Already downloaded v0.1 September archive files may be reused only if:

- exact byte size matches the frozen D0 metadata;
- current official metadata filename set is identical;
- current HEAD Content-Length is identical;
- SHA256 and ZIP/CSV integrity are rechecked.

## 6. Exact terminal states

PASS:

`C9_D1_V02_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_V02_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW remains data/implementation state only.

## 7. Consequence of PASS

v0.2 PASS establishes only historical funding archive and timestamp/interval integrity.

It does not establish C9 predictive value, economic headroom or execution viability.

Only after PASS may a separate C9 state-transition sentinel be designed prospectively.
