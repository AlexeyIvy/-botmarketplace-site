# SC001 Current Roadmap and Stop Rules v4.38

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D1 v0.1 BOUNDARY REVIEW CLASSIFIED / v0.2 REPAIR FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.37.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 still has no strategy verdict.

## 2. C9-D1 v0.1 result

C9-D1 v0.1 returned:

`C9_D1_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

Root cause:

the official September UTC+8 funding archive contains a target funding timestamp exactly at the archive end boundary:

`2024-09-30T16:00:00Z = 2024-10-01T00:00:00+08:00`

v0.1 incorrectly rejected this exact boundary because it enforced `ts < SOURCE_END_MS`.

Binding review record:

`docs/research/sc001-c9-d1-v0.1-funding-archive-integrity-review-result-v0.1.md`

Classification:

`SOURCE_MONTH_ENDPOINT_BOUNDARY_SEMANTICS / NOT_RESEARCH_FAIL`

## 3. No contamination event

The exact boundary timestamp is still on UTC date `2024-09-30`.

September 15-30 for the frozen eight assets had already been prospectively classified as:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

before D1 body access.

No October UTC Confirmation date/body was accessed.

## 4. Contamination registry updated

Current registry:

`docs/research/sc001-contamination-registry-v0.7.json`

Frozen C9 funding timestamp rule:

`start <= funding_time <= exact archive_end_boundary`

Any target funding timestamp later than:

`2024-09-30T16:00:00Z`

is forbidden.

## 5. C9-D1 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c9-d1-september-funding-archive-acquisition-integrity-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c9_d1_v02_september_funding_archive_integrity.py`

Freeze:

`docs/research/sc001-c9-d1-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `0c9aefa53c8a78ace316b77f89f9ba90bc3fb4de`;
- runner: `36202b2a88db66eb819059e4a5e73f113a2e3033`;
- contamination registry: `4138d2003246adc9aeb12f842a7d32981792df06`.

## 6. v0.2 repair scope

Only one semantic change:

- exact archive end-boundary funding timestamp is admitted.

Everything else remains unchanged:

- exact September archive identity;
- D0 parent PASS;
- exact byte/HEAD identity;
- SHA256;
- ZIP CRC;
- CSV schema;
- funding timestamp uniqueness;
- maximum interval <=8h;
- no mark/index values opened in D1;
- no return/basis-transition/signal/sentinel/PnL;
- no direction/threshold/event-window selection;
- no July/October funding bodies;
- no protected/promotional body access.

## 7. Reuse of already downloaded v0.1 files

D1 v0.2 may reuse local September funding archives from v0.1 only after re-verifying:

- filename set;
- current official metadata;
- HEAD Content-Length;
- local byte size;
- SHA256;
- ZIP/CSV integrity.

No stale file is trusted solely because it exists locally.

## 8. Exact D1 v0.2 terminal states

PASS:

`C9_D1_V02_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_V02_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW remains data/implementation state only.

## 9. Immediate next action

Run the frozen D1 v0.2 boundary-repair integrity stage on VPS.

Only after exact PASS may a C9 state-transition sentinel be designed.
