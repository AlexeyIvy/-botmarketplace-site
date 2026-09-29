# SC001 B15-P2 P0S — 2025 Fresh Holdout Source Census Protocol v0.1

Date: 2026-09-29
Status: **FROZEN BEFORE ANY P0S PRICE / INDEX / BASIS ACCESS**

Scope:
`SCALPING RESEARCH / SC001 / B15-P2 / P0S SOURCE-ROBUST SUCCESSOR / SOURCE-ONLY HOLDOUT CENSUS`

## Purpose

Establish whether calendar-year 2025 contains a disjoint official-Bybit scheduled USDT perpetual delisting event pool that can serve as a fresh candidate holdout for a source-robust successor to B15-P2 P0.

This is not a price experiment and does not rescue the frozen 2026 P0.

## Why this window is admissible

Frozen source window:

`2025-01-01T00:00:00Z <= deliveryTime < 2026-01-01T00:00:00Z`

It is disjoint by delivery time from the frozen P0 event window beginning 2026-01-01.

The 2025 window is fixed before any P0S affected-contract price, observed index value, basis, return or PnL access.

A later contamination audit is still required before any 2025 event may be promoted as confirmatory price evidence.

## Authoritative sources

Use only official Bybit public APIs:

1. `GET /v5/announcements/index`
   - locale = en-US
   - type = delistings

2. `GET /v5/market/instruments-info`
   - category = linear
   - status = Closed

No market-kline endpoint is authorized by this protocol.

## Product scope

Admit instrument metadata only when:
- contractType = `LinearPerpetual`;
- quoteCoin = `USDT`;
- symbol ends in `USDT`;
- status = `Closed`;
- deliveryTime is positive and inside the frozen 2025 window.

Exclude:
- spot;
- dated futures with ordinary expiry;
- options;
- pre-market-only failed launches;
- event contracts;
- non-USDT perpetuals.

## Announcement matching and causal clock

Use the same fail-closed source semantics as the frozen B15-P2 v0.1.1 source census:
- exact uppercase symbol matching in title + description;
- derivative relevance from Derivatives/Futures tags or PERPETUAL wording;
- numeric plausible-millisecond `publishTime` required for causal notice;
- `dateTimestamp` is never a causal fallback;
- notice must be before deliveryTime;
- when launchTime exists, pre-launch same-symbol notices do not establish the current listing episode.

Event identity:

`BYBIT x EXACT_USDT_PERPETUAL_SYMBOL x DELIVERY_TIME`

For each admitted event record:
- symbol;
- deliveryTime;
- first valid pre-event notice;
- last valid pre-event notice;
- notice count;
- lead hours;
- official announcement URL identities.

## Source-only feasibility gate

This gate checks only whether a usable disjoint event source exists. It does not determine statistical adequacy of a later price experiment.

PASS requires all:
- in-scope closed USDT linear perpetuals >= 5;
- admitted events with causal official notice >= 5;
- announcement match coverage >= 0.80;
- every admitted event has positive lead time;
- admitted events span >= 3 distinct delivery months.

PASS:
`B15P2_P0S_2025_HOLDOUT_SOURCE_CENSUS_PASS`

DEFER:
`B15P2_P0S_2025_HOLDOUT_SOURCE_CENSUS_DEFER`

Schema/integrity/transport failure:
`B15P2_P0S_2025_HOLDOUT_SOURCE_CENSUS_REVIEW`

## Allowed outputs

May report:
- announcement counts;
- closed in-scope instrument count;
- admitted event count;
- unmatched exact symbols;
- coverage ratio;
- lead-time distribution;
- distinct delivery months;
- per-event source identities and causal timestamps;
- source-integrity diagnostics.

## Firewalls

Forbidden:
- affected-contract price;
- index level/value;
- basis;
- spread;
- returns;
- PnL;
- L1/L2;
- individual trades;
- funding;
- mark/premium/spot;
- external venues;
- event ranking by outcome;
- horizon/symbol/threshold search;
- trading or order execution.

## Consequence

If PASS:
1. canonicalize the exact source-only result;
2. freeze the exact admitted 2025 event set;
3. perform a body-level semantic audit of the official matched announcements only;
4. run a contamination audit for the proposed holdout;
5. only then design a source-robust P0S price specification before any P0S price/index/basis access.

If DEFER:
review source feasibility without opening prices. Extension to another disjoint source-only window requires a separate preregistration before acquisition.

The frozen 2026 P0 remains `DEFER_SOURCE_COVERAGE` and is never rerun as a rescue.
