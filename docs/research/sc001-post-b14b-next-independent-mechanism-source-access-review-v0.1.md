# SC001 — Post-B14B Next Independent Mechanism Source/Access Review v0.1

Date: 2026-09-27
Status: **NON-PRICE SOURCE/ACCESS SELECTION COMPLETE**

## 1. Context

Active parallel states:
- B15-P1 remains operationally frozen and accumulates W1;
- B14-A waits for a future prospective expiry after transport repair;
- B13-C S0 and B14-B are terminal architectures with reusable blocks RB021 and RB022 retained.

The next mechanism must not rescue either terminal branch.

## 2. B15-P3 fixed conversion/redemption anchor

Source/access review outcome:

`DEFER_ACCESS / DO_NOT PRICE-TEST`

Official-source findings:
- OKX Convert is quote-based and the quote expires/refreshes; it is not a universal fixed redemption anchor.
- Bybit Convert uses a real-time exchange rate based on market-maker quotes/index context.
- Circle states native USDC is redeemable 1:1, but direct Circle Mint access is for qualified businesses/institutions, not ordinary individual users.
- Tether direct redemption requires KYC approval and currently has a 100,000 USD minimum redemption amount plus fees.

Conclusion:
P3 remains theoretically clean but lacks a broadly accessible deterministic redemption rail suitable for the current research architecture.

Do not open P3 price outcomes.

## 3. B15-P2 scheduled delisting / forced close

Source/access review outcome:

`ADVANCE_TO_SOURCE_ONLY_EVENT_CENSUS_AND_SEMANTIC_AUDIT`

Official-source findings:
- Bybit exposes public announcements through GET /v5/announcements/index with publishTime and announcement metadata.
- Bybit instruments-info exposes status and deliveryTime; documentation explicitly states deliveryTime is perpetual delisting time.
- Bybit delisting announcements provide exact UTC times and can specify automatic position closure based on a pre-delisting index averaging window.
- OKX delisting announcements provide exact UTC delisting times and explicit settlement/forced-close rules.
- OKX settlement windows are not globally constant across announcements; event-specific rules must therefore be captured from the authoritative announcement rather than assumed.

## 4. Source-only next stage

Do not inspect price outcomes.

Build a source/event census that records, per scheduled perpetual delisting:
- venue;
- exact contract identity;
- announcement publication timestamp;
- scheduled delisting timestamp;
- announcement lead time;
- announcement revision/postponement state;
- affected product type;
- forced-close/settlement rule;
- index averaging window if stated;
- funding handling if stated;
- API instrument status/deliveryTime when available;
- source URL identity/hash where practical.

Primary inference unit:

`VENUE x PERPETUAL_CONTRACT x SCHEDULED_DELISTING_EVENT`

## 5. Semantic guardrails

Fail closed on:
- ambiguous symbol identity;
- spot-only delisting mistaken for perpetual delisting;
- announcement update/postponement not reconciled;
- missing exact UTC event time;
- region/product mismatch;
- inferred settlement rule not stated by source.

No:
- price;
- basis;
- external hedge return;
- PnL;
- event ranking by subsequent movement.

## 6. Disposition

Current next independent branch:

`B15-P2 SCHEDULED DELISTING / FORCED-CLOSE SOURCE-ONLY EVENT CENSUS`

P3 remains deferred for access.

B14-C remains lower priority because authoritative event census and public-cloud execution latency are both less favorable.
