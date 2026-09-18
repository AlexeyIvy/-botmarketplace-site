# SC001 — C11 v2 Selection/Calibration Metadata Preflight Protocol v0.2

Date: 2026-09-19
Status: **ENGINEERING-ONLY AMENDMENT AFTER V0.1 REVIEW / NO CHRONOLOGY CHANGE / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`
Supersedes runner-validation semantics only from:
`docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.1.md`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.74.md`;
- `docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.19.json`;
- v0.1 metadata preflight REVIEW observed at event 17/24.

## 1. Observed v0.1 REVIEW

The v0.1 run stopped at:

`EMPLOYMENT 2026-06-05`

with:

`BLS metadata mismatch ... {'date': False, 'title': True, 'time': True}`

Official BLS evidence confirms the frozen event is correct:

- release date: 2026-06-05;
- release time: 08:30 AM ET;
- release: Employment Situation for May 2026.

The defect is formatting-only:

- runner expected text equivalent to `June 5, 2026`;
- the official BLS list page renders `June 05, 2026`.

Therefore the v0.1 result is:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

with reason:

`ENGINEERING_BLS_DAY_ZERO_PADDING_PARSER_DEFECT`

It is not a data failure and not a strategy verdict.

## 2. Frozen chronology unchanged

All 24 event identities, dates and UTC timestamps remain exactly as frozen in:

`docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`

No event may be added, removed, substituted or shifted.

## 3. v0.2 BLS verification improvement

Replace literal human date-text substring matching with a row-bound semantic check.

For each event, require one normalized BLS schedule-row pattern containing together:

1. full English month name;
2. calendar day accepting either unpadded or zero-padded form;
3. exact year;
4. exact `08:30 AM`;
5. exact release-family title:
   - `Employment Situation`, or
   - `Consumer Price Index`.

Example accepted equivalents for 2026-06-05:

- `June 5, 2026`;
- `June 05, 2026`.

The parser must not relax the year, month, day, time or release-family identity.

## 4. All other protocol rules unchanged

Still require:

- 24/24 BLS checks;
- 24/24 exact OKX archive identities;
- trusted `static.okx.com` final archive URL;
- HEAD 200;
- positive numeric Content-Length;
- 12 CPI / 12 Employment.

Still forbidden:

- archive body GET/open;
- macro values/surprise;
- first impulse;
- residual move;
- direction;
- continuation;
- execution;
- PnL;
- Confirmation outcome.

## 5. Exact terminal states

PASS:

`C11_V2_SC_METADATA_PREFLIGHT_PASS`

REVIEW:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

A repeated REVIEW remains engineering/source-only.

## 6. Rerun policy

Because v0.1 stopped before any market body or outcome access and v0.2 changes only metadata parser semantics, a complete 24-event v0.2 rerun is authorized.

Do not resume from event 17 as if prior partial checks were final evidence. Re-run all 24 metadata checks under one implementation identity for a single internally consistent report.
