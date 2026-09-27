# SC001 Current Roadmap and Stop Rules v5.129

Date: 2026-09-27  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 sample gate PASS / exact 76-file price-source metadata preflight prepared**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.128.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Unchanged:
`B14A_P0_DEFER_DATA`

## B13-C S0 real source-only census

Runner job:
`job_20260927T065951Z_3326eb04`

PASS:
- `B13C_S0_SOURCE_ONLY_CLUSTER_CENSUS_PASS`
- `B13C_S0_REAL_EVENT_ONLY_CLUSTER_CENSUS_BOOTSTRAP_PASS`

Observed source-only results:
- raw event rows read = 32,474;
- unique events in frozen interval = 32,381;
- duplicate fingerprints collapsed = 0;
- total raw clusters before filters = 10,734;
- clusters under minimum 3 events = 8,743;
- mixed-side clusters excluded = 83;
- gap-censored clusters = 3;
- eligible clusters = 1,905;
- minimum sample gate = 100;
- sample gate ready = true;
- exact required Bybit price archives = 76.

Merged source gaps:
- count = 15;
- duration = 324,430 ms.

No price body or return was opened.

## Current archive availability

The exact manifest requires 76 symbol-date archives.

Required Sep26 archives are for:
BTCUSDT, DOGEUSDT, ETHUSDT, FILUSDT, ORDIUSDT, SOLUSDT, SUIUSDT and XRPUSDT.

On 2026-09-27 all eight Sep26 files are visible in the official Bybit public trade directories.

Together with the previously verified Sep19-Sep25 source listings, the exact 76 required archive identities are now publicly available.

## Metadata preflight before any download

Prepared:

`research/sc001/sc001_b13c_s0_price_archive_metadata_preflight_v0_1.py`

SHA256:

`4ba2c03f060c3b009a1090d52fd394dbab5829f103a4a01328a75cdaf9bd5039`

Binding freeze:

`docs/research/sc001-b13c-s0-price-archive-metadata-preflight-freeze-v0.1.json`

Network scope:
- host = `public.bybit.com` only;
- HTTP = HEAD only;
- no body download;
- no redirects to foreign hosts.

Purpose:
- require all 76 HTTP 200;
- record Content-Length and metadata;
- compute exact total bytes before downloading;
- keep prices/returns/PnL closed.

Research Runner cannot perform this step because its jobs are intentionally offline.

## Next state

`RUN_B13C_S0_76_FILE_HEAD_METADATA_PREFLIGHT_ON_VPS`
