# SC001-E008 — Conservative Queue-Model Feasibility Audit Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN DATA-MODEL AUDIT — NO FILLS / NO P&L**

Parent plan: `docs/research/sc001-e008-passive-maker-spread-capture-research-plan-v0.1.md`  
Required upstream status: `E008_DATA_INVENTORY_PASS`

## 1. Purpose

Determine whether the already-qualified four Q1 OKX `BTC-USDT-SWAP` L2 days plus corresponding transaction tapes support a deterministic, deliberately pessimistic passive-order queue model.

This audit is **not** a market-making backtest. It must not create hypothetical orders, fills, spread capture, inventory, maker P&L or profitability output.

## 2. Frozen days and contamination boundary

Audit exactly:

- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

These four days were already used in E002 infrastructure/midquote research. They are allowed only for E008 data-model feasibility / simulator engineering. They are **not** promotional E008 Discovery evidence.

No new L2 acquisition is authorized by this audit. No Q2 / Validation / Final access.

## 3. Input identities

L2 source per day:

- previously-qualified Q009A/Q009B `BTC-USDT-SWAP-L2orderbook-400lv-D.tar.gz`;
- parent day status must be `FULL_DAY_PASS`;
- local compressed bytes and SHA256 must match parent report.

Trade source per target UTC day D:

- Q006R-qualified exact archive D;
- Q006R-qualified neighbor archive D+1;
- reconstruct target UTC day `[D 00:00:00, D+1 00:00:00)` exactly as in Q006R;
- both archive identities/SHA256 must match qualified parents.

## 4. L2 semantics

Replay the 400-level stream causally in source order.

Each level has only:

`[price, aggregate_size, aggregate_order_count]`.

Therefore exact order IDs and exact FIFO priority are **not available**. The audit must explicitly record this limitation and must not pretend to reconstruct order-level queue priority.

A usable L2 state requires:

- a prior snapshot;
- nonempty best bid and best ask;
- best bid < best ask;
- positive displayed size at both best levels;
- positive aggregate order count at both best levels.

## 5. Deterministic L2/trade alignment

Trade and book streams have independent records but millisecond timestamps.

For a transaction at timestamp `T`, the audit may use only a book state whose timestamp is **strictly less than T**.

A book update with timestamp equal to the trade timestamp is not ordered relative to that trade by the available data and therefore may not be used to infer queue state for that trade.

Same-millisecond cases are explicitly counted as `same_ms_ambiguous` and excluded from side/price compatibility gates rather than resolved optimistically.

Book-state age:

`trade_ts - prior_book_state_ts`.

Report shares at age <=100 / 250 / 500 / 1000 / 5000 ms.

## 6. Transaction/book compatibility facts

The OKX historical trade `side` is treated only as a structural aggressor-side label for this audit.

For an aligned non-ambiguous trade:

- buy-side transaction is book-compatible when trade price >= prior best ask;
- sell-side transaction is book-compatible when trade price <= prior best bid.

Also count exact-best versus through-best observations.

These are data synchronization facts only. They are not fill claims.

## 7. Frozen pessimistic queue principle for later E008

If this feasibility audit PASSes, a later separately-frozen simulator may use the following lower-bound principle:

1. hypothetical passive order starts **behind the full displayed quantity** already present at its price;
2. quote disappearance / displayed-size reduction by itself gives **zero** queue progress;
3. queue-ahead may decrease only from causally observed transaction volume that is compatible with execution at the resting price;
4. cancellations are never credited as queue progress;
5. if displayed quantity at the same price increases while our order is resting, base/stress rules must never assume those new orders are safely behind us; at minimum a pessimistic stress model treats additions as ahead;
6. price-level deletion without sufficient observed executed volume does not imply our fill;
7. price-through may be used only under a separately frozen execution rule and only with causally compatible transaction evidence;
8. partial fills must be explicit;
9. exact FIFO is never claimed because order IDs are absent.

This protocol does not yet simulate any of these fills.

## 8. Required structural diagnostics

For each day and pooled where meaningful, report only:

- source identity/hash PASS;
- reconstructed transaction count and 1,440/1,440 minute coverage;
- L2 records/snapshots/updates;
- number/share of usable best-book states;
- positive best-level size/order-count share;
- transaction count by buy/sell;
- same-ms ambiguous transaction count/share;
- transactions with a strictly prior valid book;
- prior-book age distribution and <=100/250/500/1000/5000 ms shares;
- side/price-compatible share among non-ambiguous aligned transactions with book age <=5 s;
- exact-best and through-best shares;
- whether aggregate best-level size/order count are available;
- explicit `exact_order_ids_available = false`;
- explicit `conservative_trade_volume_only_queue_model_possible` verdict.

Forbidden:

- hypothetical order placement;
- queue-ahead trajectories for a hypothetical order;
- fill count/rate;
- maker spread capture;
- inventory;
- markout after hypothetical fill;
- fees/rebates;
- P&L/profitability.

## 9. PASS gates

Exact terminal `E008_QUEUE_MODEL_FEASIBILITY_PASS` requires all:

1. upstream inventory exact PASS;
2. all four L2 parent/day states are qualified and local archive hash/size matches;
3. Q006R is PASS and exact+D+1 transaction identities/hash/size match;
4. all four target UTC transaction days reconstruct with 1,440/1,440 minute coverage and zero timestamp/trade-ID reversal;
5. all L2 replays have a valid initial snapshot, zero malformed/crossed/empty book states under qualified replay semantics;
6. >=99.9% of non-same-ms transactions have a strictly prior valid book state;
7. >=99.5% of non-same-ms transactions have prior-book age <=5,000 ms;
8. >=95.0% of non-same-ms, <=5 s aligned transactions are side/price-compatible with the prior best quote;
9. >=99.99% of usable L2 states expose positive best-level size and positive aggregate order count on both sides;
10. both buy and sell transaction counts are nonzero on every day;
11. output firewall confirms no fills/spread capture/inventory/P&L/profitability were calculated;
12. Q2/Validation/Final remain closed.

Any failure yields exact token:

`E008_QUEUE_MODEL_FEASIBILITY_REVIEW`.

A REVIEW does not authorize weakening these gates after seeing the data. It requires investigating the data-model mismatch before any maker profitability work.

## 10. Interpretation of PASS

A PASS means only:

- historical L2 and transaction tapes are causally alignable enough;
- best-level aggregate size/order-count exist;
- a **pessimistic transaction-volume-only queue model** can be implemented without pretending to know exact FIFO.

It does not authorize maker P&L on these four days and does not select quoting width, order size, cancel interval, inventory rule, maker fee, Discovery dates or promotion gates.

## 11. Next step after PASS

Only after PASS:

1. freeze the conservative queue simulator semantics on synthetic fixtures;
2. validate simulator mechanics on these four contaminated engineering days **without using them as promotional evidence**;
3. freeze new untouched Q1 E008 Discovery dates before opening/downloading their L2 bodies for profitability;
4. only then run one E008 Discovery.
