# SC001 Current Roadmap and Stop Rules v5.36

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 READ-ONLY CAPABILITY PASS / ROUTE IDENTITY FREEZE NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.35.md`

## 1. Background branches

B13-C and B14-A remain protected under systemd.

## 2. B15-P1 capability gate

`B15_P1_READONLY_CAPABILITY_PASS`

Both OKX and Bybit authenticated source endpoints are available through dedicated read-only, IP-bound credentials.

## 3. Security state

OKX:
- read_only only.

Bybit:
- readOnly = 1;
- no Withdraw permission token.

## 4. Next stage

`CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE`

Before starting the prospective status collector, freeze:

- mature common spot-USDT asset universe;
- exact cross-venue asset identity;
- exact network identity mapping;
- native/token distinction;
- contract-address rules;
- effective directed transferability graph;
- exclusions for ambiguous/migrating/delisting assets.

## 5. After identity freeze

Design and launch the 15-second prospective transferability-state collector.

Collector remains status-only:

- no prices;
- no spreads;
- no returns;
- no PnL.

## 6. Price firewall

No B15 price-bearing research until:

- route identity freeze;
- prospective source collection;
- source-only opportunity-rate checkpoint;
- full-cycle Edge-to-Fill card.
