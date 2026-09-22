# SC001 — B15-P1 Representation Disposition Builder v0.2 Design

Date: 2026-09-23  
Status: **DESIGN CANDIDATE — NOT YET FROZEN / NOT YET RUN**  
Parent: `B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW`  
Source run: `20260920T210446Z`

## 1. Purpose

Correct the representation-resolution semantics exposed by the v0.1 final builder without changing B15 hypotheses, universe policy, maturity rule, cost/risk model, or stop rules.

The v0.2 design remains strictly non-price.

## 2. Binding principles retained

- no fuzzy runtime network matching;
- no ticker-only cross-venue identity;
- contract equality is evaluated only after canonical network equality;
- empty contract is never sufficient proof of native identity;
- ambiguous identity stays `IDENTITY_REVIEW`;
- transfer ON/OFF status is not used for selection;
- price data is forbidden;
- pass still requires zero unresolved identity-review assets;
- pass still requires a complete USDT quote route graph.

## 3. Representation disposition model

Every observed venue representation row must receive exactly one disposition:

1. `COMMON_PROVEN`
   - both venues map to the same canonical network;
   - representation identity is canonically equal;
   - route can enter the cross-venue graph.

2. `KNOWN_ONE_SIDED`
   - network and representation identity are explicitly classified;
   - no identical representation exists on the opposite venue;
   - not a cross-venue route;
   - not automatically an identity error.

3. `UNRESOLVED_ALIAS`
   - network alias/code is not frozen in the registry.

4. `UNRESOLVED_IDENTITY`
   - network is known but native/token identity cannot be proven.

5. `CONFLICTING_IDENTITY`
   - same canonical network has competing non-equivalent representation identities requiring manual review.

Only (1) may create a cross-venue route.

(2) is recorded explicitly so known one-sided support does not disappear from the audit trail.

(3)-(5) keep the asset in `IDENTITY_REVIEW`.

## 4. Row-first canonicalization

v0.1 performs nested pair comparison too early.

v0.2 must first canonicalize each venue row independently into:

- venue;
- asset;
- raw network label;
- canonical `network_uid`;
- identity kind: `native` or `token`;
- canonical `representation_identity`;
- evidence rule used;
- disposition readiness.

Only after independent row canonicalization may venue intersections be computed.

This avoids false conflicts when one venue exposes multiple representations on the same network.

## 5. Contract normalization

Before empty/non-empty logic:

- convert null to empty string;
- trim surrounding whitespace.

EVM token identity:
- require exact `0x` + 40 hex;
- lowercase after network equality.

Non-EVM identity:
- use network-specific rules only;
- no generic fuzzy normalization.

## 6. Native identity

A row with an empty contract may become `native:<asset>` only when the explicit native registry contains:

`(network_uid, asset)`

A non-empty venue-specific native marker may be accepted only through an explicit network-specific rule.

No bare asset-symbol inference.

## 7. Network-specific rules required by current review set

Candidate rules to research and freeze separately:

### Cardano
Canonical token identity must be based on policy ID + asset name, independent of venue ordering/format.

Current NIGHT evidence shows the same two components in opposite order.

### BRC-20
If adopted, identity must be based on the BRC-20 ticker under an explicitly frozen BRC-20 network/protocol mapping.

Do not treat BRC-20 assets as native BTC.

### Stellar
XLM native identity must use explicit Stellar-native semantics.

Venue-specific `native:...` metadata must not be treated as a generic token contract without review.

### WAX
WAXP may use venue-specific native-token metadata such as `eosio.token`; this requires explicit WAX-specific evidence.

### EVM native metadata
Native ETH representations may be encoded as empty on one venue and a system/native marker on another. Any exception must be network-specific and frozen; no generic “zero/system address means native” rule.

## 8. Alias registry

Network registry rows may represent:

- shared cross-venue networks;
- known one-sided networks.

A network may therefore have an empty alias/code set for one venue if that absence is intentional and documented.

Adding an alias does not by itself admit an asset.

## 9. Asset decision

For each candidate asset:

1. apply frozen structural exclusions/maturity rules;
2. canonicalize all observed OKX rows;
3. canonicalize all observed Bybit rows;
4. if any row is unresolved/conflicting => `IDENTITY_REVIEW`;
5. compute exact intersection of canonical representation identities;
6. if intersection is empty => `IDENTITY_REVIEW`;
7. otherwise admit asset and create directed routes only for the common proven intersection;
8. record all remaining classified rows as `KNOWN_ONE_SIDED`.

This preserves fail-closed semantics while avoiding pairwise false mismatches.

## 10. USDT quote graph

Apply the same row-first representation disposition model to USDT.

`quote_review = true` only if any observed USDT representation remains:
- unresolved alias;
- unresolved identity;
- conflicting identity.

A fully classified one-sided USDT representation is not a missing cross-venue route.

The quote graph is complete when:

- every observed USDT row has an explicit disposition;
- every `COMMON_PROVEN` representation is present in the graph;
- all one-sided rows are recorded;
- zero unresolved/conflicting USDT rows remain.

This preserves `pass_requires_quote_graph_complete=true`.

## 11. Outputs required from v0.2 audit/builder

Before any final PASS decision, produce:

- `representation_disposition_okx.json`
- `representation_disposition_bybit.json`
- `identity_review_v02.json`
- `known_one_sided_representations.json`
- `common_proven_representations.json`
- `directed_route_graph_v02.json`
- `usdt_quote_common_routes_v02.json`
- `usdt_quote_one_sided_v02.json`
- `builder_manifest_v02.json`

Manifest must include:
- counts by disposition;
- unresolved alias count;
- unresolved identity count;
- conflict count;
- admitted/review/excluded asset counts;
- common route count;
- quote common route count;
- quote one-sided count;
- price_data_used=false;
- transfer_status_used_for_selection=false.

## 12. Control gate

Do not run v0.2 yet.

Required order:

1. review this design;
2. create evidence-backed registry/native/normalization candidate;
3. create v0.2 audit code;
4. freeze exact code + registry hashes;
5. create and seal immutable Runner bundle;
6. show bundle SHA256 + approval code to user;
7. run only after explicit approval.

No price/PnL stage is authorized.
