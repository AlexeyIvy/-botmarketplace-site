# SC001 — B15-P1 Canonical Network and Native Registry Freeze v0.1

Date: 2026-09-21
Status: **FROZEN BEFORE FINAL CANONICAL IDENTITY BUILDER**
Source run: `20260920T210446Z`

This freeze is intentionally conservative.

## Binding rules

- only explicit registry rows may map OKX/Bybit network aliases;
- no fuzzy matching;
- no contract-only network inference;
- contract equality is evaluated only after canonical network equality;
- empty contract is admitted only through the explicit native registry;
- unmapped aliases remain `IDENTITY_REVIEW`;
- new aliases after this freeze trigger `ROUTE_SET_REVIEW`;
- USDT0/bridged/special representations not explicitly resolved here remain review-only;
- current deposit/withdraw ON/OFF state is not used.

## Important corrections frozen before builder

- Bybit maturity cannot use generic ticker occurrence in announcement text; only strict listing-title evidence may establish recent listing.
- Leveraged-token exclusion cannot use bare suffix matching such as `UP`, because ordinary tickers such as JUP would false-positive.

## Registry artifacts

- `docs/research/sc001-b15-p1-canonical-network-registry-v0.1.json`
- `docs/research/sc001-b15-p1-native-asset-registry-v0.1.json`

Next exact action:

`FREEZE_AND_RUN_FINAL_CANONICAL_IDENTITY_BUILDER_V01`

The 15-second collector remains blocked.
