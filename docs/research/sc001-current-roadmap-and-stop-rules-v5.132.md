# SC001 Current Roadmap and Stop Rules v5.132

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 exact 1,905-cluster freeze PASS**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.131.md`

## B13-C exact cluster freeze

Runner job:
`job_20260927T073756Z_d064e97b`

PASS:
`B13C_S0_EXACT_CLUSTER_FREEZE_MANIFEST_PASS`

Observed:
- eligible clusters = 1,905;
- required price archives = 76;
- package integrity = PASS;
- exit code = 0;
- stderr empty;
- price/returns/PnL = CLOSED.

Authoritative Runner artifact:
- SHA256 = `1138d6a034eb4a7269b8649272e375e5056e2f5b2d361bad3ea6ba54ddc7861c`;
- size = 996,099 bytes.

Because GitHub Control rejects a ~1 MB single-file write, the exact manifest is cached in GitHub as 10 deterministic cluster chunks plus a master index. This is a storage-layer representation only; research semantics are unchanged.

Canonical GitHub master:
`docs/research/artifacts/b13c-s0/exact-cluster-freeze-v0.1/master-index.json`

Reconstruction:
concatenate chunk `eligible_clusters` arrays in part order and require contiguous IDs `S0C000001..S0C001905`.

## Price archive state

HEAD-only preflight:
- 76/76 PASS;
- compressed total = 2,633,144,445 bytes = 2.452 GiB.

## Next architecture

Build a networked streaming price-anchor extractor that:
1. verifies the master/chunk SHAs and reconstructs exactly 1,905 clusters;
2. reads the exact 76-file HEAD metadata report;
3. downloads one archive at a time;
4. requires expected Content-Length and trusted Bybit URL identity;
5. computes archive SHA256 while downloading;
6. validates gzip + CSV schema and timestamp monotonicity;
7. extracts only trades inside frozen entry/exit 1-second buckets;
8. persists normalized anchor evidence + archive integrity ledger;
9. deletes the compressed archive after successful extraction;
10. does **not** calculate returns.

Only after normalized-anchor completeness PASS may the separate S0 outcome analyzer calculate the frozen 30-second signed reversal metric.

## Current next state

`PREPARE_B13C_S0_STREAMING_PRICE_ANCHOR_EXTRACTOR`
