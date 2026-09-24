# SC001 — B15-P1 15-Second Non-Price Transferability Collector Protocol v0.1

Date: 2026-09-24  
Status: **DESIGN CANDIDATE / LAUNCH NOT AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001 / B15-P1`

Parents:

- `docs/research/sc001-b15-p1-final-identity-route-v0.2.2-freeze-v1.json`;
- `docs/research/sc001-b15-p1-v0.2.2-final-freeze-artifact-supplement-v1.json`;
- `docs/research/artifacts/b15-p1-stage-c/20260924T100910Z/stage_c_structural_preflight_manifest.json`;
- `docs/research/sc001-b15-p1-full-cycle-edge-to-fill-card-v0.1.md`;
- `docs/research/sc001-b15-p1-stage-c-source-semantics-evidence-v0.3.json`.

## 1. Purpose

Create a protected prospective chronology of Bybit/OKX transferability and restoration-cost source metadata without collecting market prices.

The collector is evidence acquisition only.

It must not decide whether an observed transferability event is profitable.

## 2. Frozen source pair

Venues:

- Bybit;
- OKX.

Fast source endpoints:

- Bybit: `GET /v5/asset/coin/query-info`;
- OKX: `GET /api/v5/asset/currencies`.

Both require authenticated read-only credentials.

No Trade or Withdraw permission is required or allowed for the collector credentials.

## 3. Frozen fast cadence

`15 seconds`

Schedule is phase-aligned to UTC epoch multiples of 15 seconds.

Rules:

- no adaptive cadence;
- no event-triggered faster polling;
- no price-triggered cadence changes;
- no catch-up burst after a missed slot;
- a missed slot is recorded as `MISSED_POLL_SLOT`;
- resume at the next future 15-second phase.

The cadence may change only in a new version frozen before observing any price outcome linked to B15 source events.

## 4. Per-poll concurrency

At each scheduled slot:

1. start Bybit and OKX source calls independently;
2. record per-venue request-start timestamp;
3. record receive timestamp;
4. record HTTP/API status;
5. preserve exact raw response bytes or exact UTF-8 response body;
6. normalize only after raw preservation;
7. derive canonical source state using frozen v0.2.2 mappings.

One venue failure does not discard a valid response from the other venue.

A failed venue becomes source-unknown for that poll.

No carry-forward may fabricate an observed source state across a failed poll.

## 5. Request deadline / scheduler overrun

Per-venue fast request deadline:

`12 seconds`

The request implementation may split this into connect/read timeouts, but total venue request lifetime may not exceed the frozen 12-second deadline.

If the previous fast request for a venue is still in flight when the next 15-second slot arrives:

- do not start an overlapping request for that venue;
- emit `SCHEDULER_OVERRUN`;
- mark the affected venue source as unknown for that slot;
- resume at the next future phase;
- do not catch up missed slots.

Fast lane has priority over the slow fee lane.

The slow fee lane must yield when a fast slot is imminent and may never delay a scheduled fast poll.

## 6. Storage pressure guard

Check filesystem free space at least every 5 minutes.

Warning state:

- free bytes < 20 GiB; OR
- free filesystem percentage < 25%.

Fail-closed stop state:

- free bytes < 10 GiB; OR
- free filesystem percentage < 15%.

On fail-closed threshold:

`STORAGE_PRESSURE_REVIEW`

Collector must:

1. finish/flush the current append operation if safe;
2. persist state and heartbeat;
3. record the stop reason;
4. stop without deleting or rotating away protected evidence.

Automatic deletion of protected B15 raw files is forbidden.

## 7. Time semantics

For every source poll retain:

- scheduled slot timestamp;
- request-start timestamp;
- response-receive timestamp;
- source/server timestamp when supplied;
- process monotonic timing;
- connection/process epoch.

No exact exchange-internal transition timestamp is invented.

If state is observed OLD at poll N and NEW at poll N+1:

`transition_interval = (receive_time_N, receive_time_N+1]`

If a source gap lies between those observations, mark:

`TRANSITION_INTERVAL_WITH_SOURCE_GAP`

and retain the gap explicitly.

## 8. Frozen identity boundary

Collector input identity is the final v0.2.2 artifact set.

Binding hashes include:

- full route graph SHA256:
  `06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928`;
- asset universe SHA256:
  `fa9f97ab1e70b30bdb196fd6f4d49a8cbc7462d13424644ddb7b88cdd9f431b0`;
- quote graph SHA256:
  `1c5a225e35c0e346819608ecca652c3c4005e57422fda44db0ed68f1db5593f5`.

Collector may observe chains outside the frozen graph in raw source responses.

They must be classified:

`OUTSIDE_FROZEN_ROUTE_GRAPH`

and may not be auto-admitted.

## 9. Normalized venue-chain state

For each frozen venue × asset × canonical representation observation retain as applicable:

- venue;
- asset;
- network_uid;
- representation_identity;
- venue chain code;
- raw contract/native marker;
- deposit state;
- withdrawal state;
- fixed withdrawal fee;
- percentage withdrawal fee;
- fee currency;
- minimum withdrawal;
- minimum deposit;
- maximum withdrawal if available;
- withdrawal precision if available;
- confirmation metadata;
- source timestamps;
- raw response SHA256;
- normalization version.

Missing required metadata is explicit, never silently converted to zero.

## 10. Derived directed route state

For every frozen common representation:

### Bybit -> OKX

ACTIVE only if:

- Bybit withdrawal = enabled;
- OKX deposit = enabled;
- both source rows valid in the current poll.

### OKX -> Bybit

ACTIVE only if:

- OKX withdrawal = enabled;
- Bybit deposit = enabled;
- both source rows valid in the current poll.

Derived states:

- `ACTIVE`;
- `BLOCKED_SOURCE_WITHDRAWAL`;
- `BLOCKED_DESTINATION_DEPOSIT`;
- `BLOCKED_BOTH`;
- `SOURCE_UNKNOWN`;
- `METADATA_INVALID`.

Known-one-sided quote identities never become cross-venue routes.

## 11. Protected event taxonomy

Source-state events:

- `DEP_OFF`;
- `DEP_ON`;
- `WD_OFF`;
- `WD_ON`;
- `CHAIN_APPEARED`;
- `CHAIN_DISAPPEARED`;
- `SOURCE_INVALID`;
- `SOURCE_RECOVERED`.

Derived route events:

- `ROUTE_ACTIVE_TO_BLOCKED`;
- `ROUTE_BLOCKED_TO_ACTIVE`;
- `ROUTE_TO_UNKNOWN`;
- `ROUTE_UNKNOWN_TO_OBSERVED`.

Economic-source metadata events:

- `WITHDRAW_FIXED_FEE_CHANGED`;
- `WITHDRAW_PERCENTAGE_FEE_CHANGED`;
- `MIN_WITHDRAW_CHANGED`;
- `MIN_DEPOSIT_CHANGED`;
- `MAX_WITHDRAW_CHANGED`;
- `FEE_CURRENCY_CHANGED`;
- `CONFIRMATION_METADATA_CHANGED`.

No event is labeled profitable/unprofitable.

## 12. Fast-lane raw preservation

For each venue poll store:

- exact response body;
- local request/receive timestamps;
- HTTP status;
- API result code/message;
- response headers needed for rate-limit diagnostics, excluding secrets;
- SHA256 of exact response body;
- collector version;
- process epoch.

Never log:

- API key;
- HMAC signature;
- OKX passphrase;
- secret key;
- private request headers containing credentials.

Daily raw files are append-only.

## 13. Fast-lane normalized storage

Daily files:

- poll ledger;
- normalized venue-chain snapshots;
- derived directed-route snapshots;
- source/route event log;
- source-gap ledger;
- invalid-row log.

Normalized snapshot records may be compact state maps, but every poll must be independently attributable to its raw response hashes.

## 14. Slow account-fee lane

Trading fee metadata must not block the 15-second fast lane.

Separate low-priority fee-refresh lane:

`every 6 hours`

Use exact frozen/qualified spot USDT pairs.

Bybit:

`GET /v5/account/fee-rate?category=spot&symbol=...`

OKX:

`GET /api/v5/account/trade-fee?instType=SPOT&instId=...`

Throttle design:

- maximum 1 request/second per venue;
- no burst catch-up;
- pair errors recorded individually;
- fast lane continues independently.

For each pair snapshot retain:

- venue;
- exact instrument;
- taker fee;
- maker fee;
- account level / fee group when available;
- source timestamp / receive interval;
- raw response hash.

A missing/stale fee snapshot cannot be replaced by the 10 bps floor for a later primary headroom PASS.

It produces:

`FEE_RATE_UNKNOWN`

until causal account/pair metadata exists.

## 15. Fee snapshot staleness

Fee refresh target:

`6 hours`

A fee snapshot older than:

`8 hours`

at the relevant later event time is:

`FEE_SNAPSHOT_STALE`

for primary economic admission.

The 2-hour grace absorbs one missed refresh without silently accepting indefinite stale metadata.

## 16. Source gaps

Record:

- request timeout;
- HTTP transport error;
- exchange API error;
- schema invalidity;
- process restart;
- VPS reboot;
- scheduler overrun;
- missed poll slot.

Gap interval starts from the last complete relevant source observation and ends at the first subsequent complete observation.

No future analysis may assume availability or unavailability inside a gap.

## 17. Heartbeat and persistent state

Persist heartbeat at least once per 30 seconds.

Persistent state includes:

- collector version;
- frozen artifact hashes;
- process epoch;
- last scheduled slot;
- last successful poll per venue;
- last normalized state hash per venue;
- poll count;
- invalid poll count;
- source gap count;
- process restart count;
- fee-refresh progress;
- last fee snapshot per pair;
- last heartbeat.

State updates are atomic.

Event/raw files are append-only.

## 18. Restart semantics

On process start:

- create a new process epoch;
- read persisted state;
- if a prior heartbeat exists, record `PROCESS_RESTART_GAP`;
- resume at the next future 15-second slot;
- do not backfill missed polls;
- do not rewrite prior files.

Run under systemd after implementation self-test PASS.

Recommended service properties:

- starts after network-online and time-sync;
- restart on failure;
- 15-second restart backoff;
- graceful SIGTERM;
- run as `botmarket`;
- explicit protected data root;
- no shell logging of secrets.

## 19. Storage layout

Suggested root:

`~/sc001_data/SC001_B15P1_TRANSFERABILITY/`

Structure:

- `raw/bybit/YYYY-MM-DD.jsonl`;
- `raw/okx/YYYY-MM-DD.jsonl`;
- `polls/YYYY-MM-DD.jsonl`;
- `normalized/venue_chain/YYYY-MM-DD.jsonl`;
- `normalized/routes/YYYY-MM-DD.jsonl`;
- `events/YYYY-MM-DD.jsonl`;
- `gaps/source_gaps.jsonl`;
- `fees/bybit/YYYY-MM-DD.jsonl`;
- `fees/okx/YYYY-MM-DD.jsonl`;
- `invalid/YYYY-MM-DD.jsonl`;
- `collector_state.json`;
- `collector_manifest.json`.

Daily UTC rotation.

## 20. Hash / integrity chain

Each poll ledger entry contains:

- previous poll-ledger entry hash;
- current raw Bybit SHA256 if available;
- current raw OKX SHA256 if available;
- normalized state SHA256;
- derived route-state SHA256.

This creates a tamper-evident chronological chain.

Daily close writes:

- row counts;
- first/last scheduled slot;
- source gap summary;
- file SHA256 values;
- terminal daily-chain hash.

## 21. Storage / retention

Initial protected horizon:

`OPEN_ENDED_BACKGROUND_COLLECTION`

First source-only operational review:

`after 7 complete UTC days`

Review is limited to:

- poll completeness;
- source error rate;
- gap duration;
- number of raw state transitions;
- fee metadata completeness;
- storage growth.

Do not inspect price response to events.

Collector continues unless explicitly stopped or a fail-closed source review requires intervention.

## 22. Allowed diagnostics

Allowed while protected collection runs:

- poll count;
- successful/invalid poll count;
- per-venue source uptime;
- gap counts/durations;
- state-change counts by taxonomy;
- number of currently active/blocked/unknown frozen routes;
- fee snapshot completeness/staleness counts;
- storage size;
- heartbeat/restart counters.

Not allowed:

- cross-venue prices;
- spread distributions;
- event profitability;
- returns around events;
- best assets/networks;
- price threshold optimization;
- PnL.

## 23. Source credentials

Use dedicated read-only exchange keys.

Self-test must verify:

- Bybit key is read-only;
- OKX permission is read-only;
- withdrawal capability is absent;
- required source endpoints are callable;
- secrets are never printed.

User must never paste API secrets into chat.

## 24. Implementation gates

Before launch:

1. collector design preflight PASS;
2. implementation code freeze;
3. offline parser/state-machine fixtures PASS;
4. local output/write/restart fixtures PASS;
5. live read-only source capability revalidation PASS;
6. systemd unit verification PASS;
7. explicit collector-launch authorization.

Only then may the 15-second source collector start.

## 25. Current authorization

`collector_authorized = false`

`collector_launch_authorized = false`

`price_economic_research_authorized = false`

## 26. Next state

After design preflight PASS:

`PREPARE_B15P1_COLLECTOR_IMPLEMENTATION_SELF_TEST`
