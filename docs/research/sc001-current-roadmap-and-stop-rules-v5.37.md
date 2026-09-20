# SC001 Current Roadmap and Stop Rules v5.37

Date: 2026-09-20
Status: **CURRENT SC001 ROADMAP — B15-P1 CANONICAL IDENTITY RULES FROZEN / NON-PRICE INVENTORY PROBE NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.36.md`

## 1. Protected background branches

B13-C and B14-A remain protected under systemd.

- B13-C protected liquidation data remains closed to alpha inspection.
- B14-A remains frozen until the 2026-09-25 event.
- Historical C1-C12 and B13-A/B13-B verdicts remain terminal/frozen.

## 2. B15-P1 capability state

`B15_P1_READONLY_CAPABILITY_PASS`

OKX + Bybit authenticated read-only source access is available.

Security invariants remain binding:

- no Trade permission;
- no Withdraw authority;
- local credentials only;
- no secrets in Git/log/chat;
- B15 authenticated REST uses IPv4-only transport.

## 3. Canonical identity design state

The canonical route/universe rules are now frozen before live identity inventory.

Binding protocol:

`docs/research/sc001-b15-p1-canonical-route-universe-identity-freeze-protocol-v0.1.md`

Rule-freeze token:

`B15_P1_CANONICAL_IDENTITY_RULES_FROZEN`

Binding implementation freeze:

`docs/research/sc001-b15-p1-canonical-identity-inventory-probe-freeze-v0.1.json`

Frozen runner:

`research/sc001/sc001_b15_p1_nonprice_identity_inventory_probe_v0_1.py`

## 4. Critical frozen rules

Primary universe class:

`COMMON_MATURE_SPOT_USDT_CRYPTO`

Frozen maturity guard:

`90 completed days`

Universe selection may use only non-price market/identity/maturity evidence.

Current deposit/withdraw ON/OFF state MUST NOT determine membership.

Ticker equality alone is forbidden as identity proof.

Every admitted asset must ultimately have:

- canonical asset identity;
- exact canonical network identity;
- native/token representation identity;
- exact contract/native rules;
- every proven common network;
- both directed transfer edges.

USDT is excluded as a base candidate but requires a separate frozen quote-rebalance route graph.

## 5. Fail-closed semantics already frozen

Later aggregate transferability states:

- `ACTIVE`: at least one frozen route validly active;
- `BLOCKED`: every frozen route validly observed and explicitly blocked;
- `UNKNOWN`: no route active and at least one route unknown/invalid/missing;
- `ROUTE_SET_REVIEW`: new possible common route or identity change.

`UNKNOWN != BLOCKED`

Chain disappearance never equals transfer OFF.

Schema drift never equals outage.

New network after freeze is not ignored and not auto-admitted; it triggers route-set review.

## 6. Exact next stage

`NONPRICE_IDENTITY_INVENTORY_PROBE`

Run the frozen one-shot probe on the VPS.

It is allowed to call only the endpoints listed in the implementation freeze.

It produces:

- OKX SPOT-USDT market identity inventory;
- Bybit SPOT-USDT market identity inventory;
- OKX identity-only chain view;
- Bybit identity-only chain view;
- common base candidates;
- exact chain alias census;
- recent Bybit Spot listing/delisting evidence;
- source hashes and run manifest.

Review-facing chain files intentionally omit deposit/withdraw ON/OFF fields so those states cannot influence identity mapping.

## 7. Inventory probe terminal states

PASS:

`B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS`

REVIEW:

`B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_REVIEW`

A PASS does NOT mean final route/universe freeze is complete.

It only authorizes exact network-alias/native/token review.

## 8. After inventory probe PASS

Next work inside the same canonical-freeze stage:

1. inspect exact observed OKX/Bybit network aliases;
2. freeze canonical network registry;
3. freeze native-asset registry;
4. resolve token-contract equality rules by network;
5. resolve/exclude ambiguity, migration, rebrand and delisting cases;
6. run final canonical identity builder;
7. emit `ADMITTED / IDENTITY_REVIEW / EXCLUDED`;
8. emit frozen base directed route graph;
9. emit frozen USDT quote-rebalance graph.

Only then can the stage end with:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

or:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW`

## 9. Collector remains blocked

Do NOT design or launch the 15-second prospective transferability-state collector yet.

Collector design is authorized only after:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

## 10. Price firewall

Still forbidden:

- prices;
- bid/ask;
- spread;
- depth;
- returns;
- execution;
- PnL;
- price-based asset/network selection.

Future sequence remains:

1. final canonical route/universe identity freeze;
2. 15-second status collector design/launch;
3. source-only opportunity-rate checkpoint;
4. full-cycle Edge-to-Fill card;
5. event-specific price protocol freeze;
6. first headroom sentinel;
7. only survivors proceed to convergence/rebalance/execution/PnL.
