# SC001 Current Roadmap and Stop Rules v4.37

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D0 v0.2 PASS / C9-D1 SEPTEMBER FUNDING INTEGRITY FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.36.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 still has no strategy verdict.

## 2. C9-D0 v0.2 result

Exact:

`C9_D0_V02_DATA_SEMANTICS_PASS`

Observed:

- assets passed `8/8`;
- funding archive metadata found;
- mark/index 4H coverage/alignment complete;
- historical funding body downloaded/opened false;
- returns/basis-transition/signal/sentinel/PnL false;
- direction/threshold/event-window selected false;
- protected/promotional market body accessed false;
- exit code 0.

Binding result record:

`docs/research/sc001-c9-d0-v0.2-data-semantics-pass-result-v0.1.md`

## 3. C9-D1 calibration source prospectively declared

Before funding-body access, contamination registry advanced to:

`docs/research/sc001-contamination-registry-v0.6.json`

C9-D1 authorized source month:

`2024-09 UTC+8 FundingRate archive month`

UTC source interval:

`[2024-08-31T16:00:00Z, 2024-09-30T16:00:00Z)`

For BTC/ETH/DOGE/ORDI/UNI/XRP/OP/BCH this source interval is now permanently:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

Newly nonpromotional dates are September 15-30 for these eight assets; Aug 31 and Sep 1-14 were already contaminated/source-support.

## 4. Protected funding bodies remain closed

C9-D1 must not open:

- July 2024 funding monthly body;
- October 2024 funding monthly body;
- any protected holdout/Confirmation body.

This preserves July gap and October Confirmation.

## 5. C9-D1 frozen implementation

Protocol:

`docs/research/sc001-c9-d1-september-funding-archive-acquisition-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c9_d1_september_funding_archive_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c9-d1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `fdf072d7ffee97fa62fc877e9ee7c7c54c087438`;
- runner: `3a92e3e7d78ea65d16ddc4b7a43f12e4f07ccd37`;
- contamination registry: `848c21bcf78affe245baf37608b355c9aac5edb9`.

## 6. D1 permitted work

D1 may:

- re-query exact September funding archive metadata;
- cross-check filenames and Content-Length against D0;
- download only September funding bodies;
- verify size/SHA256/ZIP CRC/CSV schema;
- parse exact target-instrument funding timestamps;
- validate funding rates as finite but not store/use them;
- reconstruct observed consecutive funding interval hours.

D1 may not open mark/index values or calculate any state-transition outcome.

## 7. Exact D1 terminal states

PASS:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW is data/implementation state only.

## 8. D1 PASS requirements

For each of eight instruments:

- exact D0 file identity match;
- exact body byte size;
- ZIP integrity;
- >=80 unique target funding timestamps;
- all target timestamps inside authorized source month;
- first/end coverage gaps <=8h;
- maximum consecutive funding interval <=8h;
- no conflicting duplicate timestamps.

## 9. Hard firewalls

All remain false:

- mark/index values opened for D1;
- funding values used for strategy;
- returns;
- basis transition;
- signal;
- sentinel;
- PnL;
- direction selection;
- threshold selection;
- event-window selection;
- July funding body;
- October funding body;
- protected/promotional body access.

## 10. Immediate next action

Run frozen C9-D1 funding archive acquisition/integrity on VPS.

Only after exact D1 PASS may a C9 state-transition sentinel be designed and frozen.
