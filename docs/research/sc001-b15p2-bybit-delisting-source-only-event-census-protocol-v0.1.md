# SC001 — B15-P2 Bybit Scheduled Perpetual Delisting Source-Only Event Census Protocol v0.1

Date: 2026-09-27
Status: **FROZEN BEFORE ANY B15-P2 PRICE OUTCOME ACCESS**
Scope: `SCALPING RESEARCH / SC001 / B15-P2 / SOURCE-ONLY CENSUS`

## 1. Purpose

Determine whether scheduled Bybit USDT perpetual delistings form a sufficiently broad, causally timestamped event source for a later forced-close/dislocation mechanism.

This stage is source/event-clock research only.

It does **not** inspect:
- affected-contract price;
- external-reference price;
- index level;
- basis;
- spread;
- post-announcement return;
- pre-delisting return;
- PnL.

## 2. Authoritative sources

Use only official Bybit public APIs:

1. Announcements:
   `GET /v5/announcements/index`
   with:
   - locale = en-US;
   - type = delistings.

2. Instrument metadata:
   `GET /v5/market/instruments-info`
   with:
   - category = linear;
   - status = Closed.

No web-search result is itself an event source.

## 3. Census window

Closed perpetual event time:

`2026-01-01T00:00:00Z <= deliveryTime < 2026-09-27T00:00:00Z`

This historical window is used only to establish:
- source coverage;
- announcement lead-time availability;
- event breadth/opportunity rate;
- exact event identity.

No price outcome from this window is authorized.

## 4. Product scope

Admit instrument metadata only when:
- contractType = `LinearPerpetual`;
- quoteCoin = `USDT`;
- symbol ends in `USDT`;
- status = `Closed`;
- deliveryTime is positive and inside the census window.

Exclude:
- spot;
- futures with normal expiry;
- options;
- pre-market-only failed launches;
- event contracts;
- non-USDT perpetuals.

## 5. Announcement matching

Fetch all official Bybit announcements with type key `delistings`.

An announcement is derivative-relevant when at least one is true:
- tags contain `Derivatives`;
- tags contain `Futures`;
- title/description contains `PERPETUAL`.

For each closed perpetual instrument in scope:
- search exact uppercase symbol string in title + description;
- retain every matching derivative-relevant announcement;
- require numeric `publishTime`.

Do not infer symbol identity from a partial base token alone.

## 6. Event identity

Primary unit:

`BYBIT x EXACT_USDT_PERPETUAL_SYMBOL x DELIVERY_TIME`

For each symbol:
- canonical event clock = instrument metadata `deliveryTime`;
- first notice = earliest matching announcement publishTime strictly before deliveryTime;
- last pre-event notice = latest matching announcement publishTime strictly before deliveryTime;
- notice count = count of matched announcements published before deliveryTime;
- lead time = deliveryTime - first notice.

Announcements at or after deliveryTime do not establish causal notice.

## 7. Revision semantics

This first census does not interpret settlement-window text.

Multiple matched announcements are preserved as revision evidence.

A later semantic audit must read the exact announcement body and reconcile:
- postponements;
- revised delisting time;
- settlement/index averaging rule;
- funding treatment;
- automatic closure semantics.

Do not assume one global settlement formula across all events.

## 8. Source-only feasibility gates

Let:
- `N_closed` = all in-scope closed USDT linear perpetuals in the window;
- `N_admitted` = those with >=1 matched official pre-event announcement.

PASS requires all:
- `N_closed >= 5`;
- `N_admitted >= 5`;
- announcement match coverage `N_admitted / N_closed >= 0.80`;
- every admitted event has positive lead time;
- admitted events span >=3 distinct delivery calendar months.

Then:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_PASS`

Otherwise:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_DEFER`

An API/schema/integrity error gives:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_REVIEW`

## 9. Allowed diagnostics

May report:
- total delisting announcements retrieved;
- derivative-relevant delisting announcement count;
- in-scope closed perpetual count;
- admitted event count;
- unmatched exact symbols;
- coverage ratio;
- first-notice lead p25/median/p75/min/max hours;
- distinct delivery months;
- per-event symbol, deliveryTime, first/last notice timestamps, notice count, lead hours, announcement URL identities.

Do not report any market price.

## 10. Consequence

If PASS:
1. freeze the exact admitted event set;
2. perform an announcement-body semantic audit only;
3. classify forced-close/index-window/funding rules per event;
4. only after that design a non-price edge-to-fill/headroom protocol.

If DEFER:
do not lower coverage/event-count gates by looking at prices.

No B15-P2 price outcome is authorized by this protocol.
