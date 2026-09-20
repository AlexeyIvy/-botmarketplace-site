# SC001 — B15-P1 Network Alias / Native Identity Critical Review v0.1

Date: 2026-09-21
Status: **LIVE SAFE-INVENTORY REVIEW / FINAL BUILDER NOT YET AUTHORIZED**
Source run: `20260920T210446Z`
Parent status: `B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS`

## 1. Source integrity

Safe export is present in GitHub.

Observed manifest:

- 201 common primary base candidates;
- 265 OKX identity chain rows;
- 300 Bybit identity chain rows;
- price endpoints called = false;
- order endpoints called = false;
- transfer endpoints called = false;
- withdrawal endpoints called = false;
- secret values printed = false.

## 2. Alias census finding

Observed unique identity aliases:

- OKX normalized chain aliases: 98;
- Bybit chain codes: 81.

Only a small subset of raw labels match literally across venues.

Therefore raw string equality is not a sufficient network registry.

Examples requiring explicit canonical mapping include:

- OKX `ERC20` <-> Bybit `ETH / Ethereum`;
- OKX `Solana` <-> Bybit `SOL / Solana`;
- OKX `Base` <-> Bybit `BASE / Base Mainnet`;
- OKX `Arbitrum One` <-> Bybit `ARBI / Arbitrum One`;
- OKX `Optimism` <-> Bybit `OP / OP Mainnet`;
- OKX `Polygon` <-> Bybit `MATIC / Polygon PoS`;
- OKX `TRC20` <-> Bybit `TRX / TRX`;
- OKX `The Open Network (TON)` <-> Bybit `TON`;
- OKX `Avalanche C-Chain` <-> Bybit `CAVAX`.

No fuzzy runtime matching is allowed.

## 3. Contract-address finding

185 cross-venue row pairs share an exact non-empty contract/token identifier under the probe's safe inventory.

This is useful evidence but MUST NOT be used without network identity.

Critical counterexample:

Some omnichain representations expose the same address value on multiple EVM networks. Naively joining only by `coin + contract` creates false cross-network matches such as Arbitrum <-> Base/BSC/Avalanche/Ethereum/Polygon/Optimism.

Therefore final representation identity requires:

`canonical asset + canonical network + network-specific canonical contract/native identity`

Contract equality alone is never sufficient.

## 4. Native-asset finding

Many legitimate native assets have empty contract fields on both venues.

Examples include BTC, ADA, ALGO, APT, ATOM, BCH, BNB, DOGE, DOT, ETH, LTC, SOL, SUI, XRP and others.

Empty+empty is NOT proof of native equivalence.

A curated native registry is required.

Assets with multiple empty-contract network rows require special care. Examples include:

- BTC: Bitcoin plus OKX Lightning;
- AVAX: C-Chain and X-Chain;
- ETH: multiple L2/native-style representations;
- SEI: native and EVM;
- ZETA: ZetaChain and ZetaChain EVM.

The final builder may admit a native representation only when the exact network pair is frozen in the registry.

## 5. Maturity / exclusion heuristic audit

The first safe inventory exposed two important false-positive risks before the final builder.

### 5.1 Announcement ticker substring risk

The preliminary announcement helper can generate false maturity hits for very short tickers or mentions unrelated to the listed asset.

Observed examples:

- ticker `A` matched ordinary article text;
- `WLFI` matched an announcement whose headline was for USD1 but mentioned WLFI in the prize text.

Therefore final Bybit maturity logic MUST NOT use generic ticker occurrence in title/description.

Frozen correction for final builder:

- only explicit listing-title grammar counts as a listing event for maturity, e.g. a title semantically equivalent to `Bybit to List <name> (<TICKER>) on Spot` or `New listing: <TICKER>/USDT`;
- Token Splash/promotional mentions do not establish listing date;
- ambiguous evidence => `MATURITY_REVIEW`;
- no mature-by-default inference from unrelated ticker mentions.

### 5.2 Leveraged-token suffix risk

A generic suffix rule such as `UP/DOWN` creates false positives for ordinary tickers such as `JUP`.

Therefore final exclusion logic MUST NOT classify leveraged tokens by bare suffix matching.

Frozen correction:

- use explicit venue instrument classification/name evidence or a curated exact leveraged-token list;
- otherwise do not exclude merely because a ticker ends in `UP`, `DOWN`, etc.

## 6. Direct non-price exclusions already safe

The common candidate inventory contains clear stablecoin/fiat-like base candidates that are structurally excluded from the primary base universe, including:

- PYUSD;
- RLUSD;
- USD1;
- USDC;
- USDS.

USDT remains excluded as a base candidate and retained only for the quote-rebalance graph.

## 7. OKX 90-day maturity evidence

Four common candidates are not 90-day mature by the frozen OKX continuous-trading anchor:

- DATA;
- GRVT;
- SLX;
- VVV.

These are excluded from the primary v1 universe by the already frozen 90-day rule independent of prices.

## 8. Bybit special-market gate

The source inventory confirms Bybit exposes special `symbolType` / `stTag` classes.

The primary candidate probe already requires:

- `symbolType == ""`;
- `stTag == 0`.

Thus xstocks/adventure/special-treatment rows are not admitted into the primary common candidate set.

## 9. Required architecture for final registry

Use a versioned registry with explicit rows containing at least:

- `network_uid`;
- `network_family`;
- `identity_kind`;
- exact OKX alias set;
- exact Bybit chain-code set;
- accepted Bybit chainType variants;
- contract canonicalization rule;
- native asset, when applicable;
- review notes.

No alias not present in the registry may be auto-mapped.

## 10. Final-builder preconditions

Before final canonical builder is frozen:

1. create explicit canonical network registry from observed aliases;
2. create explicit native-asset registry;
3. define network-specific contract normalization;
4. replace preliminary announcement ticker-hit logic with strict listing-title parsing;
5. remove bare ticker-suffix leveraged classification;
6. preserve `IDENTITY_REVIEW` for all unresolved cases.

## 11. Current disposition

The inventory PASS stands.

No source contamination or price-firewall violation was found.

However, the final canonical universe MUST NOT yet be declared PASS.

Current exact state:

`B15_P1_NETWORK_ALIAS_NATIVE_IDENTITY_REVIEW_IN_PROGRESS`

Next exact action:

`FREEZE_CANONICAL_NETWORK_AND_NATIVE_REGISTRY_V01`

The 15-second collector remains blocked.
