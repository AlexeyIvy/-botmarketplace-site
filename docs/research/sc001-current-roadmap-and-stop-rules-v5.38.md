# SC001 Current Roadmap and Stop Rules v5.38

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 NON-PRICE IDENTITY INVENTORY PASS / NETWORK ALIAS REVIEW NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.37.md`

## 1. Protected history/background

All previous terminal/frozen decisions remain binding.

B13-C protected data remains closed to alpha inspection.

B14-A remains unchanged before the 2026-09-25 event.

## 2. B15 source capability

`B15_P1_READONLY_CAPABILITY_PASS`

Read-only, IP-bound OKX + Bybit capability remains valid.

B15 authenticated REST remains IPv4-only.

## 3. Canonical identity rules

Binding:

`docs/research/sc001-b15-p1-canonical-route-universe-identity-freeze-protocol-v0.1.md`

Rules remain frozen before outcomes.

## 4. Non-price inventory probe

Observed PASS:

`B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS`

Binding result record:

`docs/research/sc001-b15-p1-nonprice-identity-inventory-probe-pass-v0.1.md`

Observed:

- 201 common primary base candidates;
- 265 OKX identity chain rows;
- 300 Bybit identity chain rows;
- no price/order/transfer/withdraw endpoint calls;
- no secret values printed.

## 5. Current exact stage

`NETWORK_ALIAS_AND_NATIVE_IDENTITY_REVIEW`

Before final universe construction, inspect exact safe identity inventory and freeze:

- exact OKX chain aliases;
- exact Bybit chain aliases / chainType;
- canonical network IDs;
- network-specific contract comparison rules;
- native-asset identities;
- ambiguous aliases;
- migration/rebrand/delisting exclusions.

No fuzzy alias mapping.

No runtime guessing.

## 6. Safe artifact policy

Only review-safe outputs may be persisted to GitHub:

- normalized market identity inventory;
- chain identity views;
- common candidate identity view;
- chain alias census;
- recent official listing/delisting evidence;
- run manifest.

Raw authenticated API responses remain local on VPS and are not committed.

## 7. After network/native registry freeze

Run the final canonical identity builder and emit:

- `ADMITTED`;
- `IDENTITY_REVIEW`;
- `EXCLUDED`;
- frozen base directed route graph;
- frozen USDT quote-rebalance graph.

Final stage token must be either:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

or:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW`

## 8. Collector still blocked

Do not design or launch the 15-second collector until final canonical identity freeze PASS.

## 9. Price firewall

Still forbidden:

- price;
- bid/ask;
- spread;
- depth;
- returns;
- execution;
- PnL;
- price-derived selection.
