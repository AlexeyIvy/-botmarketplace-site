# SC001 Current Roadmap and Stop Rules v5.130

Date: 2026-09-27  
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 76-file metadata PASS / exact cluster freeze prepared**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.129.md`

## B15-P1

Unchanged:
`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

## B14-A

Unchanged:
`B14A_P0_DEFER_DATA`

## B13-C S0 source-only census

Binding source-only result:
- unique liquidation events = 32,381;
- eligible clusters = 1,905;
- required price archives = 76;
- sample gate >=100 = PASS.

No price or return outcome has been opened.

## 76-file HEAD metadata preflight

Operator-run VPS result:

`B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_PASS`

Observed:
- required archives = 76/76;
- total compressed bytes = 2,633,144,445;
- total compressed GiB = 2.452.

Report path on VPS:

`/home/botmarket/sc001_data/SC001_B13C_S0_PRICE_ARCHIVE_PREFLIGHT/b13c_s0_price_archive_metadata_preflight_v0_1.json`

This was HEAD-only. Price bodies remain unopened.

## Storage/extraction policy

Do not permanently retain all 2.452 GiB merely to run S0.

Preferred acquisition architecture:
1. freeze exact 1,905 eligible cluster identities;
2. download one required archive at a time;
3. verify metadata/size/SHA/gzip/CSV schema;
4. extract only the exact frozen entry and exit 1-second buckets;
5. persist normalized price-anchor rows and archive integrity metadata;
6. delete the compressed body after successful normalized extraction unless retained for a separately justified audit cache.

This minimizes peak disk use while preserving reproducibility through source file SHA256 and exact extracted rows.

## Exact cluster-freeze implementation

Prepared:

`research/sc001/sc001_b13c_s0_exact_cluster_freeze_v0_1.py`

SHA256:

`0f7c27e84c960d41a7dcbd1a058ba4b8b1b3b6865aabe97493a4ea810c7cb9d4`

It reuses the already self-tested cluster analyzer SHA and must reproduce exactly:
- unique events = 32,381;
- raw clusters = 10,734;
- under-min clusters = 8,743;
- mixed-side excluded = 83;
- gap-censored = 3;
- eligible clusters = 1,905;
- required archives = 76;
- merged source gaps = 15 / 324,430 ms.

Only after exact aggregate agreement does it emit:
- cluster id;
- symbol;
- liquidation side;
- reversal sign;
- start/end timestamps;
- event count;
- frozen entry bucket;
- frozen exit bucket;
- required archive day(s).

No price, return or PnL.

## Next state

`BUILD_AND_SEAL_B13C_S0_EXACT_CLUSTER_FREEZE_BUNDLE`
