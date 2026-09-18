# SC001 Current Roadmap and Stop Rules v4.36

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D0 v0.1 REVIEW CLASSIFIED / v0.2 METADATA-ONLY REPAIR FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.35.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 has no strategy verdict yet.

## 2. C9-D0 v0.1 result

The first C9-D0 data-semantics probe returned:

`C9_D0_DATA_SEMANTICS_REVIEW`

with zero historical funding rows from the current REST funding endpoint but complete mark/index timestamp coverage/alignment.

Binding result record:

`docs/research/sc001-c9-d0-v0.1-data-semantics-review-result-v0.1.md`

Classification:

`SOURCE_TRANSPORT_LIMITATION / NOT_RESEARCH_FAIL`

## 3. Root cause

OKX's current `/api/v5/public/funding-rate-history` endpoint only exposes recent history and does not serve the frozen 2024 dates in 2026.

Deep historical perpetual funding is available through the official historical market-data service.

This source behavior was already observed and repaired previously in SC001 E002.

## 4. Protected-data guardrail

The official historical funding files are monthly.

Do not download/open July 2024 funding archive under C9-D0 because it contains the protected July 16-30 gap.

Therefore the v0.2 repair is metadata/HEAD-only for funding archives.

## 5. C9-D0 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c9-d0-okx-funding-archive-metadata-mark-index-semantics-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c9_d0_v02_okx_funding_archive_metadata_mark_index_semantics.py`

Freeze:

`docs/research/sc001-c9-d0-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `af907cbee3b38ff8bebd77bb3bcde9a5a49c89bd`;
- runner: `0cb774dca5f06700664267420613dd3f0288b3c4`;
- freeze: `947f7cff388c8d5878236dfaacb6784e9c45c52c`.

## 6. v0.2 funding checks

For each frozen asset family and July/September month:

- query official `market-data-history`;
- `module=3`;
- `instType=SWAP`;
- `instFamilyList=<uly>`;
- `dateAggrType=monthly`;
- locate trusted archive file metadata;
- verify `static.okx.com` identity;
- verify positive Content-Length with HEAD;
- download/open no funding archive body.

## 7. v0.2 mark/index checks

Retain historical 4H semantics/coverage checks on already contaminated:

- 2024-07-01..14;
- 2024-09-01..14.

No price values are retained for strategy use.

## 8. Exact v0.2 terminal states

PASS:

`C9_D0_V02_DATA_SEMANTICS_PASS`

REVIEW:

`C9_D0_V02_DATA_SEMANTICS_REVIEW`

Neither state is a C9 strategy outcome.

## 9. After v0.2 PASS

Do not open July/September funding bodies.

Instead:

1. select one or more complete, nonprotected calendar months prospectively;
2. update contamination registry before body access;
3. label whole month(s) `NONPROMOTIONAL_SELECTION_CALIBRATION`;
4. freeze funding archive acquisition/integrity;
5. inspect realized funding timestamps/intervals only after that;
6. then design a C9 state-transition sentinel.

## 10. Immediate next action

Run frozen C9-D0 v0.2 metadata/HEAD-only probe on VPS.

No C9 alpha, return, threshold, event window or PnL computation is authorized.
