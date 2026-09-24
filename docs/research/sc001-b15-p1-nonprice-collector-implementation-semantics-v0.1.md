# SC001 — B15-P1 Non-Price Collector Implementation Semantics v0.1

Date: 2026-09-24  
Status: **IMPLEMENTATION-BINDING / PRE-LAUNCH**

Parents:

- `sc001-b15-p1-15-second-nonprice-collector-protocol-v0.1.md`;
- collector design preflight PASS;
- final v0.2.2 frozen identity/route artifacts.

## 1. Frozen live-normalization sources

The implementation must not re-infer identity from current exchange naming.

For the original 146 base-v0.1 admitted assets, build expected venue matchers from:

`docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/ADMITTED.json`

For the former 46 review assets and USDT, build exact row matchers from:

`docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_resolved_rows_v0.2.2.json`

Common route membership is frozen from:

- base v0.1 admitted representations;
- final v0.2.2 asset dispositions;
- final v0.2.2 quote classification.

Current exchange rows may not create new canonical identities or routes.

## 2. Base-v0.1 matcher rule

Bybit:

- exact asset;
- exact frozen `bybit_chain`;
- exact frozen `bybit_chainType`;
- live contract/native identity must match the frozen representation identity after only deterministic contract canonicalization.

OKX:

- exact asset;
- exact frozen full `okx_chain`;
- live contract/native identity must match the frozen representation identity after only deterministic contract canonicalization.

No fuzzy alias matching.

## 3. v0.2.2 exact matcher rule

Rows from final resolved replay are matched by the full frozen source tuple:

- venue;
- asset;
- raw network;
- raw chainType where applicable;
- raw contract/native marker.

No generalized XLM native-prefix rule is allowed.

## 4. Live contract canonicalization

For base-v0.1 token matchers only:

- `0x` + 40 hex EVM addresses: lowercase;
- all other non-empty identities: case-sensitive exact string;
- frozen `native:<ASSET>` identity requires empty live contract unless an exact v0.2.2 special matcher handles the row.

No contract-only network inference.

## 5. Duplicate alias aggregation

More than one exact venue row may map to the same canonical representation.

Preserve every raw row.

A venue/representation aggregate is valid only if all matched rows agree after canonical parsing on:

- deposit state;
- withdrawal state;
- fixed withdrawal fee;
- percentage withdrawal fee;
- fee currency when present;
- minimum withdrawal;
- minimum deposit;
- maximum withdrawal when present;
- withdrawal precision when present;
- confirmation metadata.

If they disagree:

`METADATA_INVALID_ALIAS_CONFLICT`

That venue side is not route-ACTIVE for the poll.

Do not choose the cheaper alias.

## 6. Missing / extra rows

Frozen matcher absent in current source response:

`CHAIN_DISAPPEARED`

Current source row with no frozen matcher:

`OUTSIDE_FROZEN_ROUTE_GRAPH`

Raw evidence is retained, but the row is never auto-admitted.

## 7. Capability snapshot before run

`--mode run` requires a separate capability snapshot created by the later live read-only capability gate.

Required snapshot state:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

It must bind:

- collector runner SHA256;
- implementation-freeze SHA256;
- final route-graph SHA256;
- Bybit read-only permission;
- OKX read-only permission;
- absence of withdrawal capability;
- successful authenticated source-endpoint probes;
- exact qualified spot USDT pair list for the slow fee lane.

Offline `--mode self-test` must perform zero exchange calls and does not require credentials or capability snapshot.

## 8. Credential environment

Runtime credentials use the already provisioned B15 read-only environment names:

- `SC001_B15_BYBIT_API_KEY`;
- `SC001_B15_BYBIT_API_SECRET`;
- `SC001_B15_BYBIT_BASE_URL`;
- `SC001_B15_OKX_API_KEY`;
- `SC001_B15_OKX_API_SECRET`;
- `SC001_B15_OKX_PASSPHRASE`;
- `SC001_B15_OKX_BASE_URL`.

The systemd candidate sources them from the existing protected B15 environment file:

`/home/botmarket/.config/sc001/b15-p1.env`

No credential value may be written to raw logs, normalized logs, state, manifest, status output or exception text.

## 9. Slow fee lane

Use only pairs present in the capability snapshot.

Do not infer pair existence from asset symbol at runtime.

Per-pair failure:

- retain failure record;
- do not block fast source polling;
- later event fee status becomes unknown/stale as applicable.

## 10. Price firewall

Implementation source must contain no market-price endpoint.

Offline static self-test must fail if any forbidden price/orderbook endpoint family appears in executable source.

No current price is needed to collect transferability source evidence.


## 11. Exact raw-body content-addressed storage

To control evidence growth without losing any raw bytes, the implementation stores exact HTTP response bodies by SHA256 content address.

Logical rule:

`raw_object_id = SHA256(exact_response_bytes)`

Physical object path:

`raw_objects/<venue>/<sha256[0:2]>/<sha256>.bin`

For every poll, the append-only poll ledger records:

- venue;
- scheduled slot;
- request/receive timing;
- HTTP/API status;
- raw body SHA256;
- raw body byte length;
- whether the content object was newly written or already present.

If the same exact response repeats across polls, its bytes are stored once and every poll references the same immutable object.

Before reusing an existing object, the implementation re-hashes it and requires exact SHA256 equality.

Hash mismatch:

`RAW_OBJECT_INTEGRITY_FAIL`

and collector stops fail-closed.

This is evidence deduplication only. No raw response content is discarded.

## 12. Raw-object retention

Protected raw objects are immutable.

Automatic deletion or garbage collection during protected collection is forbidden.

Daily manifests enumerate every raw-object SHA referenced by that UTC day’s poll ledger.


## 13. Explicit launch authorization file

A valid capability snapshot is necessary but not sufficient for `--mode run`.

Run mode also requires:

`collector_launch_authorization.json`

with status:

`B15P1_NONPRICE_COLLECTOR_LAUNCH_AUTHORIZED`

and token:

`B15P1_NONPRICE_COLLECTOR_LAUNCH_PASS`

The authorization must bind exact SHA256 values for:

- collector runner;
- implementation freeze;
- capability snapshot;
- systemd service candidate.

Without this file, or on any hash mismatch:

`COLLECTOR_LAUNCH_NOT_AUTHORIZED`

and run mode exits before any exchange call.

Offline self-test does not require launch authorization.
