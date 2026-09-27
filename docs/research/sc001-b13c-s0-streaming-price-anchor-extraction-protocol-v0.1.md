# SC001 — B13-C S0 Streaming Price-Anchor Extraction Protocol v0.1

Date: 2026-09-27  
Status: **FROZEN BEFORE ANY B13-C PRICE BODY ACCESS**  
Scope: `SCALPING RESEARCH / SC001 / B13-C / S0 / PRICE-ANCHOR EXTRACTION`

## 1. Purpose

Materialize only the exact Bybit public-trade observations required by the already frozen S0 cluster entry/exit buckets.

This stage opens historical trade bodies and price fields for source extraction only.

It does **not** calculate:
- returns;
- signed reversal;
- threshold outcome;
- PnL;
- per-symbol performance.

## 2. Immutable event parent

Canonical cluster master:

`docs/research/artifacts/b13c-s0/exact-cluster-freeze-v0.1/master-index.json`

Expected SHA256:

`0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b`

The master reconstructs exactly:
- 1,905 eligible clusters;
- IDs `S0C000001 .. S0C001905`;
- 76 required Bybit price archives.

No cluster, symbol, side, entry bucket or exit bucket may be altered after price access.

## 3. Exact source metadata parent

HEAD-only preflight status:

`B13C_S0_PRICE_ARCHIVE_METADATA_PREFLIGHT_PASS`

Required archives:

`76 / 76`

Frozen total compressed Content-Length:

`2,633,144,445 bytes`

The networked extractor must read the full VPS metadata report:

`SC001_B13C_S0_PRICE_ARCHIVE_PREFLIGHT/b13c_s0_price_archive_metadata_preflight_v0_1.json`

and require its exact archive identity set to equal the 76-file source-only census list.

## 4. Trusted network scope

Allowed host only:

`public.bybit.com`

Allowed URL form only:

`https://public.bybit.com/trading/SYMBOL/SYMBOLYYYY-MM-DD.csv.gz`

No alternate price source.

No redirect to another host/path identity.

## 5. Sequential acquisition

Process one archive at a time.

For each required archive:

1. require the frozen HEAD metadata row;
2. require sufficient local free space for one archive plus reserve;
3. download to a temporary file;
4. require exact compressed byte count = frozen Content-Length;
5. calculate SHA256 over compressed bytes;
6. validate gzip stream;
7. stream-parse CSV;
8. validate source schema/clock;
9. extract only target buckets touched by the archive;
10. persist archive integrity ledger and anchor candidates;
11. fsync outputs;
12. delete the compressed temporary body.

Do not retain all 2.452 GiB merely for convenience.

## 6. Bybit CSV semantics

Reuse the already-qualified SC001 Bybit trade schema:

first five semantic columns must be exactly:

1. `timestamp`
2. `symbol`
3. `side`
4. `size`
5. `price`

For every row:
- timestamp = Unix seconds with fractional precision;
- normalize to integer microseconds;
- symbol must equal the archive symbol;
- side must be `Buy` or `Sell`;
- size finite >0;
- price finite >0;
- timestamp must fall inside the archive UTC day;
- timestamps must be nondecreasing.

Any malformed row or timestamp reversal:

`B13C_S0_PRICE_ANCHOR_EXTRACTION_REVIEW`

No silent row dropping.

## 7. Frozen bucket semantics

For each exact frozen cluster:

Entry bucket:

`[cluster_end+1s, cluster_end+2s)`

Exit bucket:

`[cluster_end+31s, cluster_end+32s)`

Select:

`chronologically last real Bybit trade inside the bucket`

No:
- carry-forward;
- interpolation;
- nearest-trade substitution;
- alternate delay;
- alternate exit horizon.

If a bucket crosses a UTC boundary, candidates from all touched required day archives are combined and the chronologically last in-bucket trade is selected.

## 8. Missing-bucket semantics

A fully qualified source archive may legitimately contain no trade in a frozen one-second bucket.

Do not invent a price.

Persist:
- entry_found true/false;
- exit_found true/false.

A cluster is `VALID_PRICE_CLUSTER` only when both are present.

This stage may report only aggregate counts:
- clusters_with_both_anchors;
- missing_entry_count;
- missing_exit_count;
- missing_both_count.

It must not report return or performance by symbol/side.

## 9. Resume semantics

Per-archive completed evidence may be reused only if:
- archive identity matches;
- frozen Content-Length matches;
- archive ledger status PASS;
- persisted candidate file SHA matches its ledger.

Otherwise reprocess that archive from source.

This permits safe restart without changing data-selection semantics.

## 10. Outputs

Persist:

`SC001_B13C_S0_PRICE_ANCHORS_V01/`

- `archive_ledger/FILENAME.json`
- `candidates/FILENAME.jsonl`
- `price_anchors.jsonl`
- `price_anchor_extraction_manifest.json`

Each final cluster row may contain the exact entry/exit source trade timestamps and prices because price extraction is now explicitly authorized.

## 11. Firewalls

Mandatory final manifest:

- price_bodies_opened = true;
- price_rows_parsed = true;
- frozen_price_anchors_extracted = true;
- returns_calculated = false;
- signed_reversal_calculated = false;
- threshold_outcome_calculated = false;
- per_symbol_performance_ranked = false;
- pnl_calculated = false;
- collector_mutation_performed = false.

## 12. PASS gate

`B13C_S0_PRICE_ANCHOR_EXTRACTION_PASS`

requires:
- exact master/chunk integrity;
- exact 1,905 cluster reconstruction;
- exact 76 metadata/source identities;
- all 76 archives downloaded and source-qualified;
- compressed byte sizes all exact;
- gzip parse PASS;
- schema PASS;
- zero malformed rows;
- zero timestamp reversals;
- final anchor dataset contains exactly 1,905 cluster rows;
- every source candidate is traceable to archive SHA256.

Missing one-second price anchors do not by themselves fail extraction; they reduce later `valid_price_cluster` count.

## 13. Consequence

Only after extraction PASS may a separate immutable **offline** S0 outcome bundle read `price_anchors.jsonl` and calculate the one frozen signed 30-second reversal metric.

No S0 outcome calculation is authorized by this protocol.
