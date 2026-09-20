# SC001 — B15-P1 Canonical Route / Universe Identity Freeze Protocol v0.1

Date: 2026-09-20
Status: **FROZEN RULES BEFORE LIVE NON-PRICE IDENTITY INVENTORY**
Scope: `SCALPING RESEARCH / SC001 / B15-P1`

Parent context:

- `docs/research/dialog-handoff-2026-09-20-v7.0.md`
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.36.md`
- `docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`
- `docs/research/sc001-b15-p1-readonly-capability-pass-v0.1.md`
- `docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md`
- `docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md`

## 1. Research firewall

This stage is strictly non-price.

Forbidden:

- price;
- bid/ask;
- spread;
- depth;
- returns;
- execution;
- PnL;
- price-derived ranking;
- price-derived route selection.

Current deposit/withdraw ON/OFF state MUST NOT determine universe membership.

The identity freeze is based on market availability, maturity, asset identity, network identity and representation identity only.

## 2. Exact objective

Freeze a reproducible first primary universe of common mature OKX/Bybit SPOT-USDT crypto assets together with every proven common transfer network and both directed transfer edges.

The freeze must prevent three false conclusions:

1. ticker equality being mistaken for asset identity;
2. one disabled network being mistaken for full transfer segmentation while another valid route exists;
3. missing/changed source data being mistaken for a real outage.

## 3. Market universe gate

Primary market class:

`COMMON_MATURE_SPOT_USDT_CRYPTO`

An asset may proceed to identity review only if a SPOT-USDT market exists on both venues.

OKX market gate:

- `instType == SPOT`;
- `quoteCcy == USDT`;
- `state == live`;
- `instCategory == 1`;
- base currency is non-empty;
- no announced offline time represented by a non-empty future/active `expTime`.

Bybit market gate:

- `category == spot`;
- `quoteCoin == USDT`;
- `status == Trading`;
- `stTag == 0`;
- `symbolType` must be empty for primary v1.

Any non-empty Bybit `symbolType` is excluded from the primary clean v1 stratum. This conservatively excludes special categories such as adventure/xstocks/mstocks without trying to rank them.

## 4. Maturity gate

Frozen maturity guard:

`90 completed days`

OKX maturity anchor:

- use `contTdSwTime` when present and valid;
- otherwise use `listTime`;
- require anchor <= freeze_time - 90 days.

Bybit spot instrument metadata does not provide a documented spot launch timestamp suitable for this gate. Therefore Bybit maturity is checked prospectively/conservatively using official announcement evidence:

- query official Bybit announcements with `type=new_crypto`;
- restrict to Spot / Spot Listings evidence;
- if a common base ticker is identified in a qualifying new-listing announcement published within the prior 90 days, exclude it as `RECENT_BYBIT_LISTING`;
- inability to obtain complete announcement evidence is `MATURITY_REVIEW`, not mature-by-default.

No maturity threshold may be changed after transfer-state or price outcomes are observed.

## 5. Base-asset exclusions

Primary v1 excludes:

- stablecoin / fiat-like base assets;
- leveraged-token style bases;
- current/suspected migration, token swap, redenomination or unresolved rebrand;
- active delisting/offline state;
- unresolved wrapped/native ambiguity;
- unresolved synthetic/receipt-token ambiguity;
- unresolved cross-venue asset identity;
- unresolved network identity;
- unresolved contract/native identity.

These exclusions are structural. They are not selected from observed transferability or price outcomes.

## 6. Asset identity

Ticker equality is necessary for automated candidate construction but is never sufficient proof.

Canonical asset identity is represented by a versioned internal `asset_uid`.

For v1:

- venue base tickers must match exactly after uppercase normalization;
- at least one common representation must pass exact network + representation identity;
- if evidence conflicts, status is `IDENTITY_REVIEW`;
- no fuzzy ticker/name matching is allowed.

A canonical asset is an inventory unit, not merely a display symbol.

## 7. Network identity

Every venue chain label is an alias, not a canonical network identifier.

A separate versioned network registry must map exact observed aliases to a canonical `network_uid`.

Rules:

- no runtime fuzzy matching;
- no substring guessing;
- no automatic mapping from similar-looking labels;
- an unknown venue alias is `NETWORK_REVIEW`;
- mapping changes require a new freeze version.

Prefer stable namespace-like canonical IDs where unambiguous, e.g. CAIP-2 style identifiers for chains with established namespace/reference identities.

## 8. Representation identity

For every asset/network pair define `representation_uid`.

### Token representation

Admission requires:

- same canonical `asset_uid`;
- same canonical `network_uid`;
- non-empty contract/token identifier on both venues;
- equality under a network-specific canonicalization rule.

EVM contract rule:

- must match `0x[0-9a-fA-F]{40}`;
- compare lowercase canonical form.

Non-EVM identifiers:

- MUST NOT be lowercased generically;
- compare using a network-specific frozen rule;
- absent rule => `IDENTITY_REVIEW`.

Contract mismatch => route representation is rejected.

### Native representation

Empty contract identifiers do NOT prove native identity.

Native admission requires a frozen registry entry asserting that:

- the canonical asset is the native asset of the canonical network;
- both venue aliases map to that same network;
- both source rows are consistent with native representation.

Otherwise => `IDENTITY_REVIEW`.

### Mixed empty/non-empty case

If one venue reports a contract and the other reports empty for the proposed common representation:

`IDENTITY_REVIEW`

No automatic coercion is allowed.

## 9. Common route-set rule

For every admitted asset, the frozen route set contains ALL proven common representations across OKX and Bybit.

It is forbidden to select only:

- default network;
- cheapest network;
- fastest network;
- currently active network;
- historically most profitable network.

Current transfer ON/OFF state is not part of route-set admission.

If a new potential common network appears after freeze:

- do not auto-admit it;
- do not ignore it;
- set the asset aggregate state to `ROUTE_SET_REVIEW`;
- suppress segmentation classification until a new versioned identity freeze resolves it.

## 10. Directed graph

Nodes:

`venue × asset_uid inventory`

For each admitted representation/network create two edges:

1. `OKX --withdraw(network)--> BYBIT deposit(network)`
2. `BYBIT --withdraw(network)--> OKX deposit(network)`

Direction is never collapsed into a symmetric boolean.

USDT is excluded as a base trading candidate but MUST have a separate frozen `QUOTE_REBALANCE_ROUTE_GRAPH` because full-cycle inventory restoration may require quote transfer in the opposite direction.

## 11. Aggregate transferability semantics for later collector

For a frozen asset/direction with route set R:

- `ACTIVE` iff at least one frozen route is validly observed active;
- `BLOCKED` iff every frozen route is validly observed and explicitly blocked;
- `UNKNOWN` iff no route is active and at least one route is unknown/invalid/missing;
- `ROUTE_SET_REVIEW` iff a new potential common representation appears or identity changes.

`UNKNOWN` is never converted to `BLOCKED`.

This rule is frozen now, before prospective status collection.

## 12. Chain disappearance and identity changes

A previously frozen row disappearing from a source is NOT equivalent to deposit/withdraw OFF.

Required behavior:

- emit `CHAIN_DISAPPEARED`;
- route state becomes `UNKNOWN`;
- aggregate cannot become `BLOCKED` solely because of disappearance.

A changed contract/native identity emits:

`IDENTITY_CHANGED`

and quarantines the affected asset to `ROUTE_SET_REVIEW`.

A new chain emits:

`CHAIN_APPEARED`

and triggers route-set review if it could be common across the venue pair.

## 13. Schema drift

Required source fields are versioned.

If required fields disappear, change incompatible type, or source shape becomes ambiguous:

- poll/source state = `SOURCE_INVALID`;
- emit `SCHEMA_REVIEW`;
- no outage/segmentation event may be inferred from that poll.

Additive unknown fields may be retained/logged without failing if all frozen required semantics remain intact.

## 14. Epoch/version discipline

The final identity freeze must contain:

- freeze timestamp UTC;
- protocol version;
- source snapshot hashes;
- asset universe file hash;
- network registry hash;
- representation/route graph hash;
- exclusions/review file hash.

Universe membership is immutable inside one research epoch.

Any later admission/removal/remap requires a new version and new epoch. Historical observations remain associated with the old epoch.

## 15. Two-step implementation inside this stage

Because exact venue chain aliases are live source metadata, the freeze stage is split without opening outcomes.

### Step A — NONPRICE_IDENTITY_INVENTORY_PROBE

Collect current non-price identity metadata only and produce:

- OKX live crypto SPOT-USDT market inventory;
- Bybit Trading SPOT-USDT inventory;
- OKX currency/chain identity rows with transfer status removed from the review view;
- Bybit coin/chain identity rows with transfer status removed from the review view;
- common base candidate list;
- exact observed chain-alias census;
- recent Bybit Spot listing/delisting announcement evidence;
- hashes and source completeness report.

This probe MUST NOT decide fuzzy network mappings.

### Step B — FINAL_CANONICAL_IDENTITY_BUILDER

After exact aliases are observed, freeze:

- canonical network registry;
- native-asset registry;
- any explicit exclusion/review overrides based only on identity/maturity evidence.

Then run the final builder to emit exactly:

- `ADMITTED`;
- `IDENTITY_REVIEW`;
- `EXCLUDED`;
- frozen base directed route graph;
- frozen USDT quote-rebalance graph.

Only a PASS allows 15-second collector design.

## 16. Terminal states

Rules frozen / inventory probe allowed:

`B15_P1_CANONICAL_IDENTITY_RULES_FROZEN`

Final identity freeze PASS:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

Unresolved final identity:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW`

## 17. Next exact action

Run the frozen non-price identity inventory probe on the VPS using the already installed read-only credentials and IPv4-only B15 transport.

Do not design or launch the 15-second prospective collector yet.
