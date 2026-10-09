# SC001 — X1 PIT Universe Source Freeze v0.1

Date: 2026-10-09
TASK_ID: SC001-X1-002B
WORKER_ID: X1_CROSS_ASSET_STRUCTURE
Authorization: T0_DESIGN_AND_REPOSITORY_IMPLEMENTATION
Terminal status: X1_PIT_UNIVERSE_SOURCE_STRATEGY_ATTENTION_REQUIRED

## Decision

No sufficiently complete official/public historical metadata lineage was established that can mechanically reconstruct every Binance USD-M perpetual contract identity, original listing epoch, terminal state/time, rename/redenomination and relisting before the exclusive cutoff `2026-10-01T00:00:00Z`.

The task therefore fails closed. Current `exchangeInfo`, first/last archive month, kline/trade bodies, present survivors and inferred symbol history MUST NOT be substituted for a point-in-time instrument ledger. X1-003 and every price/return/correlation/lag/PnL action remain unauthorized.

This is a source-strategy defer, not a negative market result and not a claim that the required history cannot exist in a licensed or privately retained venue feed.

## Official-source findings

Documentation was inspected only; no market endpoint, websocket, announcement acquisition job or market body was executed.

1. Binance documents `GET https://fapi.binance.com/fapi/v1/exchangeInfo` as **current** exchange trading rules and symbol information. Its symbol object includes `symbol`, `pair`, `contractType`, `deliveryDate`, `onboardDate`, `status`, `baseAsset`, `quoteAsset` and `marginAsset`. The documentation does not specify a historical/as-of parameter, immutable snapshot archive or inclusion guarantee for every delisted identity.
2. Binance documents `wss://fstream.binance.com/market/ws/!contractInfo` as a real-time stream emitted when contract information changes for listing, settlement or bracket updates. It carries event time, symbol, contract type, delivery time, onboard time and contract status. The documentation exposes no replay cursor or official historical event archive. A collector started now cannot reconstruct events that occurred before collection.
3. Official Binance Support listing/delisting announcements can provide named launch and scheduled settlement times. The public categories mix products and individual detail pages may have both published and updated timestamps. No inspected documentation promises an immutable, exhaustive, machine-readable USD-M perpetual event ledger across all historical listings, relistings, renames and redenominations.
4. A delisting notice may state that contracts are delisted after settlement. That is adequate evidence of a scheduled action for named contracts but does not, by itself, prove the actual terminal state transition time for an exhaustive retrospective ledger.
5. `data.binance.vision` archive-key presence proves only archive coverage. Per the task contract, first/last archive month cannot establish listing, delisting or identity truth.

Official references inspected on 2026-10-09:

- https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data#exchange-information
- https://developers.binance.info/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Mini-Tickers-Stream#contract-info-stream
- https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/common-definition
- https://www.binance.com/en/support/announcement/list/48
- https://www.binance.com/en/support/announcement/list/161
- Example official delisting notice: https://www.binance.com/en/support/announcement/detail/2f1a743334f044abbd82e34093c7b771

## Required lineage contract

A future source may qualify only if one immutable capture manifest proves all of the following before market-body access:

- exhaustive event coverage for every candidate USD-M perpetual identity through the frozen cutoff;
- venue, market type, original symbol identity, listing epoch, base/quote/margin assets, contract type and denomination/multiplier version;
- actual terminal status and effective terminal time for delisted identities;
- explicit rename, redenomination, contract-size change, rebase and relisting links without silently splicing identities;
- source publication/capture time, source URL or stream identity, response/content SHA256 and acquisition ordering;
- documented completeness or an independently auditable completeness proof that does not use realized price/volume/performance;
- deterministic exclusions for non-USDT settlement, dated contracts, leveraged/index-basket tokens, stablecoin underlyings and ambiguous mappings.

Any missing event, uncertain mapping, unexplained duplicate epoch, non-official source, hash mismatch or incomplete pagination yields `AMBIGUOUS_SOURCE_LINEAGE`; it cannot be repaired with market files.

## Deterministic resolver freeze

The companion resolver implements the part that can be frozen without pretending the source gap is closed. It consumes a normalized metadata ledger only; it performs no network access.

Canonical input schema: `sc001.x1_pit_universe_metadata_ledger.v0.1`.

Each record must bind:

- `venue=BINANCE`, `market_type=USD_M`, `contract_type=PERPETUAL`;
- `symbol`, `pair`, `base_asset`, `quote_asset=USDT`, `margin_asset=USDT`;
- integer `onboard_ms`, nullable integer `delist_effective_ms`;
- non-empty `multiplier_version`;
- `listing_notice_url` plus SHA256; for delisted records, `delisting_notice_url` plus SHA256 and terminal status in `DELIVERED` or `CLOSE`;
- `classification` in `ORDINARY_CRYPTO`, `STABLECOIN_UNDERLYING`, `LEVERAGED_TOKEN`, `INDEX_BASKET`, `DATED_CONTRACT`, `AMBIGUOUS`;
- `classification_source_url`, capture timestamp and response SHA256.

Only `https://www.binance.com/` and `https://developers.binance.com/` evidence URLs are accepted. Redirected or alternate hosts require a separately frozen rule.

`contract_identity` is the UTF-8 string:

`BINANCE|USD_M|PERPETUAL|<symbol>|<onboard_ms>|<base_asset>|USDT|USDT|<multiplier_version>`

Identical canonical identities must be byte-identical. A symbol reused with a different onboard epoch or multiplier becomes a separate identity. Any overlapping active interval for the same symbol fails closed.

Eligibility rules are fixed:

- listing epoch is strictly before the cutoff;
- only `ORDINARY_CRYPTO` records enter the pool;
- anchors are exactly qualified `BTCUSDT` and `ETHUSDT`; neither may be replaced;
- non-anchors are ordered by `SHA256(UTF-8("SC001-X1-ATLAS-v0.1|" + contract_identity))`, then bytewise identity;
- retain the first 24 non-anchors or all if fewer; fewer than 8 fails;
- of N retained non-anchors, the last `ceil(N/4)` are `NODE_RESERVE`; the rest are `DISCOVERY_POOL`;
- at UTC month start, membership requires 180 complete elapsed calendar days since listing and no terminal time at or before month start;
- choose the first 10 eligible discovery identities in frozen hash order; anchors are added separately; no mid-month replacement.

The resolver deliberately emits `SOURCE_STRATEGY_ATTENTION_REQUIRED` unless the ledger-level `completeness_attestation` is `OFFICIAL_IMMUTABLE_OR_AUDITABLE_COMPLETE` and every record passes. This attestation cannot be generated by the resolver itself.

## Frozen one-shot T1 source budget — not executed

If Strategy Manager authorizes one bounded source-resolution attempt, use exactly one metadata-only job `X1-PIT-METADATA-LINEAGE-01`:

| Request class | Hard request cap | Hard response-byte cap |
|---|---:|---:|
| `GET /fapi/v1/exchangeInfo` current control snapshot | 1 | 8,388,608 |
| Official Support announcement index pages under categories 48 and 161 | 128 total | 16,777,216 |
| Official `support/announcement/detail/<id>` pages discovered only from those bounded indexes | 1,024 total | 134,217,728 |
| Official API definition pages for response-schema pinning | 2 | 2,097,152 |
| **Whole job** | **1,155** | **161,480,704** |

Additional hard limits: one process; wall time 30 minutes; redirects remain on `binance.com`; no JavaScript/browser expansion beyond returned official pages; no market-data body URL; no websocket collection; no retries beyond the caps; no external search result may become evidence. Capture raw response bytes, URL, UTC request/response times, HTTP status, content type, ETag/Last-Modified when present and SHA256.

Passing the byte/request budget is not source qualification. The job must return `SOURCE_INCOMPLETE` if pagination, historical coverage, mutation history, actual terminal time or identity continuity cannot be proved. No second acquisition or relaxed lineage rule is authorized by this freeze.

## Safety and accounting

- outcome_accessed=false
- protected_evidence_accessed=false
- market_rows_read=false
- market_body_accessed=false
- research_source_acquisition_executed=false
- test_executor_job_launched=false
- runner_bundle_created=false
- runner_bundle_executed=false
- vps_data_read=false
- collector_changed=false
- returns_or_correlations_computed=false
- pnl_computed=false
- X1_003_executed=false

Documentation lookup occurred; no research-source acquisition run occurred. No shared roadmap, governance, Strategy State, contamination registry or reusable-block registry was changed. No reusable market block is claimed.

## Disposition

`X1_PIT_UNIVERSE_SOURCE_STRATEGY_ATTENTION_REQUIRED`.

Strategy Manager must choose one of: (a) authorize the exact bounded T1 lineage attempt above, accepting that it may fail; (b) provide/approve an immutable official or licensed historical contract-master source with retrospective completeness; or (c) defer the multi-year broad-network atlas. Current-survivor-only, price-derived dates and heuristic reconstruction are forbidden.

CONTINUATION_REVIEW_REQUIRED: true
STRATEGY_REVIEW_REQUIRED: true
MERGE_AUTHORIZED: false
SHARED_STATE_WRITE_AUTHORIZED: false

