# SC001 — B15-P1 Transferability-Shock Four-Role Optimization Review v0.2

Date: 2026-09-19
Status: **DEEP SECOND-PASS REVIEW / NO PRICE OUTCOME / NO CANDIDATE ID**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b15-independent-base-multi-role-critical-review-v0.1.md`;
- `docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.28.md`.

## 1. Corrected mechanism name

Do not call P1 a risk-free arbitrage before full-cycle economics are proven.

Preferred research name:

`B15-P1 INVENTORY-BACKED TRANSFERABILITY-SHOCK RELATIVE VALUE`

Economic mechanism remains:

`LOSS OF EFFECTIVE CROSS-VENUE TRANSFERABILITY -> CAPITAL/INVENTORY SEGMENTATION -> POSSIBLE PRICE DISLOCATION`

## 2. Financial expert review

### 2.1 Immediate trade architecture

With pre-positioned base asset and USDT on both venues, a detected rich/cheap dislocation can be monetized initially with two market trades:

- sell pre-positioned base asset on rich venue;
- buy same base asset on cheap venue.

No short borrow is required for this primary architecture.

### 2.2 Full-cycle economics correction

Two market fills do NOT complete the economic cycle.

After the trade:

- cheap venue holds excess base asset / reduced USDT;
- rich venue holds reduced base asset / excess USDT.

To restore the original inventory allocation conservatively requires:

1. base-asset transfer from cheap venue to rich venue after the relevant route reopens;
2. quote-asset transfer from rich venue back to cheap venue, unless offset by a separately governed netting process.

Therefore first structural card must include:

- 2 taker fees;
- 2 bid/ask + depth/slippage burdens;
- base-asset withdrawal/network fee;
- quote-asset withdrawal/network fee;
- capital lock/opportunity-cost reserve;
- venue/counterparty reserve;
- inventory imbalance duration;
- minimum withdrawal/deposit constraints;
- confirmation delay.

Do not assume free inventory rebalance.

### 2.3 Capital requirement

The strategy is inventory-backed.

Capital must be pre-positioned BEFORE the outage event.

This creates:

- idle-capital opportunity cost;
- exchange credit/custody exposure;
- finite per-venue inventory capacity;
- depletion after repeated same-direction events.

Capacity is therefore path-dependent.

### 2.4 Financial conclusion

Mechanism remains economically promising only if:

`raw dislocation > full-cycle restoration burden + economic reserve`

The two-fill opening architecture is still attractive, but the full-cycle hurdle will be materially above two trading fees.

---

## 3. Trader expert review

### 3.1 Effective transferability, not one-chain status

A suspension on one network is NOT sufficient to define a segmentation event.

If the same asset can still move between the two venues through another common active network, the arbitrage loop is not truly blocked.

Define the relevant state as a directed route graph.

For each asset and venue pair determine all common economically valid networks.

A clean segmentation event requires loss of the relevant transfer direction across ALL frozen common routes.

Example:

If USDT-TRC20 is disabled but USDT-ERC20 remains open on both venues, that is not full USDT transfer segmentation.

### 3.2 Direction matters

Maintain separate directed capabilities:

- venue A withdrawal -> venue B deposit;
- venue B withdrawal -> venue A deposit.

The strategy may have a different feasible direction for rich-A/cheap-B than for rich-B/cheap-A.

Never collapse this into one symmetric outage boolean.

### 3.3 Event-cause taxonomy

Not every suspension is the same economic event.

Primary clean stratum:

`VENUE_SPECIFIC_OPERATIONAL/WALLET_MAINTENANCE`

where:

- affected venue route is disabled;
- counterpart venue remains operational;
- underlying network itself is operational;
- trading remains live.

Separate/non-primary strata:

- chain-wide mainnet halt/upgrade;
- protocol exploit/security incident;
- token migration/swap;
- delisting;
- compliance/account-specific restriction;
- project failure.

These latter classes may contain fundamental asset risk and must not be mixed into the clean segmentation test.

### 3.4 Scheduled versus unscheduled

Keep separate strata:

- scheduled maintenance;
- unscheduled suspension.

Scheduled events are especially useful for clean prospective testing because:

- event time may be announced in advance;
- capital can be pre-positioned before the event;
- a price protocol can be frozen before the state transition.

Do not pool scheduled and unscheduled events without a later predeclared rule.

### 3.5 Trader conclusion

P1 remains promising, but only under a route-level, direction-specific and cause-aware event definition.

---

## 4. Programmer / systems expert review

### 4.1 Credential/domain layer

OKX API domain is registration-region dependent.

Capability preflight must determine the correct production REST domain from the user's actual OKX entity/account setup.

Bybit capability preflight must run from the actual VPS egress path; regional API restrictions can block otherwise-valid credentials.

Never infer domain from device location.

### 4.2 Permission verification

OKX:

- dedicated API key;
- Read permission only;
- verify reported account/API permission is read-only;
- no Trade;
- no Withdraw.

Bybit:

- dedicated API key;
- verify `readOnly = 1` through API-key information endpoint;
- inspect returned permission structure;
- no withdrawal authority.

### 4.3 Polling

Supersede preliminary 30-second cadence before collector launch.

Freeze source polling at:

`15 seconds`

Reason:

- materially tighter causal transition interval;
- still orders of magnitude below documented endpoint limits;
- no price outcome was used to choose cadence.

Poll OKX and Bybit concurrently, not serially.

Record for each request:

- monotonic request start;
- wall-clock UTC request start;
- response receive time;
- venue/server response time when provided;
- HTTP/API code;
- schema version/hash;
- normalized state hash.

### 4.4 Snapshot/event storage

Use three append-only layers:

1. raw authenticated response snapshots;
2. normalized chain-state snapshots;
3. derived state-transition events.

Do not overwrite prior chain records when a chain disappears.

Emit explicit:

- CHAIN_APPEARED;
- CHAIN_DISAPPEARED;
- DEP_OFF/ON;
- WD_OFF/ON;
- SOURCE_INVALID;
- SCHEMA_REVIEW.

### 4.5 Route graph

Normalize to a directed multigraph:

nodes:
`venue × canonical asset inventory`

edges:
`withdraw venue A on network N -> deposit venue B on same canonical network/asset`

Each edge has:

- active/inactive;
- withdrawal fee;
- minimum withdrawal;
- confirmations;
- contract/native identity;
- last observation interval.

Effective transferability is computed from frozen route identity, not from coin ticker.

### 4.6 Operational hardening

Reuse SC001 systemd pattern:

- restart on failure;
- boot persistence;
- time synchronization;
- source-gap ledger;
- heartbeat;
- fail-closed schema drift;
- secret EnvironmentFile mode 0600.

Do not put secrets in Git, logs or chat.

---

## 5. Mathematics / statistics expert review

### 5.1 Correct inference unit

Do NOT count asset/network rows or price ticks as independent samples.

Primary independent unit:

`VENUE-LEVEL TRANSFERABILITY OUTAGE CLUSTER`

Nested observations:

- asset;
- network;
- transfer direction;
- venue pair.

If OKX disables the Solana network for ten tokens simultaneously, that is primarily one infrastructure episode, not ten independent trials.

### 5.2 Cluster hierarchy

Record:

- outage cluster ID;
- venue;
- cause class;
- scheduled/unscheduled;
- start observation interval;
- end observation interval;
- affected network(s);
- affected asset count.

Later inference should use cluster-aware summaries/bootstrap, not tick-IID tests.

### 5.3 Selection discipline

Freeze universe and route identities before price inspection.

Do not:

- select the assets that later show the largest spread;
- select the network with best PnL;
- choose scheduled vs unscheduled after seeing price;
- treat one spectacular outage as confirmation.

### 5.4 Opportunity frequency

Because SC001's main mission remains practical/scalping-oriented, event frequency is a first-class non-price metric.

Prospective status collection must report:

- clean outage clusters/month;
- median duration;
- scheduled vs unscheduled breadth;
- share of events with complete source integrity.

If clean events are extremely rare, P1 may remain a useful opportunistic strategy but should not replace the main scalping search.

### 5.5 Evidence stages

Source evidence and price evidence remain separate.

A source-only first event can establish operational semantics but cannot be retroactively used to tune thresholds.

For scheduled future events, price/headroom protocol may be frozen before the announced event and therefore tested prospectively.

---

## 6. Meta-review beyond the four roles

### 6.1 Quote-side restoration was previously undercounted

The original P1 description emphasized base-asset transfer after reopening.

That was incomplete.

Full inventory restoration normally also requires quote capital to move in the opposite direction.

This must be priced into the first conservative structural burden.

### 6.2 Alternative route leakage

A single chain outage can falsely appear to segment venues while another chain remains available.

Therefore the state variable must be:

`EFFECTIVE DIRECTED TRANSFERABILITY`

not:

`ONE_CHAIN_DISABLED`.

### 6.3 Fundamental-risk confounding

Chain/security/project incidents are not clean arbitrage-friction events.

Primary research should first isolate venue-specific operational suspensions while the underlying network and counterpart venue remain functional.

### 6.4 B15 is not a replacement for scalping

P1 is a bounded side investigation.

B13-C remains the principal active source-building branch for future liquidation scalping.

If P1 source census shows low opportunity frequency, keep its collector cheaply in background and return active research budget to a new scalping mechanism.

### 6.5 Historical announcements are useful only as non-price context

Official exchange announcements show that deposit/withdrawal suspensions are a real recurring operational class.

They may be used to:

- build cause taxonomy;
- validate source semantics;
- estimate rough event availability.

They must not be used to choose winning assets from historical price reactions.

---

## 7. Optimized stage plan

### Stage A — Account / domain / credential capability

No prices.

Verify:

- correct OKX regional API domain;
- OKX dedicated Read-only key;
- Bybit dedicated read-only key;
- VPS egress can reach both regional APIs;
- source endpoints return required schemas;
- permissions are fail-closed.

### Stage B — Canonical identity / route universe freeze

No prices.

Initial preferred market class:

`COMMON MATURE SPOT-USDT ASSETS`

Initial exclusions:

- stablecoin base assets;
- leveraged tokens;
- wrapped/rebased/rebranded ambiguity;
- pre-market/recent launch assets;
- delisting/migration state;
- unresolved contract-address/network identity.

Freeze:

- asset identity;
- common networks;
- network mappings;
- quote asset;
- transfer directions.

### Stage C — Full-cycle Edge-to-Fill card

Still no price outcomes.

Freeze conservative costs:

- two taker fills;
- spread/depth reserve;
- base transfer/rebalance fee;
- quote transfer/rebalance fee;
- confirmation/latency reserve;
- capital-lock reserve;
- inventory/counterparty reserve.

No netting benefit in first sentinel.

### Stage D — Prospective status collector

Poll both venues every 15 seconds.

No price feed in the collector.

Produce:

- raw snapshots;
- normalized states;
- transition events;
- route graph;
- outage clusters;
- source-gap ledger.

### Stage E — Source-only opportunity-rate checkpoint

Report only:

- clean outage-cluster frequency;
- duration;
- route breadth;
- scheduled/unscheduled split;
- source completeness.

No price ranking.

### Stage F — Event-specific price protocol

Only after A-E and Edge-to-Fill are frozen.

For scheduled events:

freeze event-specific price protocol before the announced outage.

For unscheduled events:

do not retrospectively redesign the protocol after the first observed event.

### Stage G — Headroom sentinel

First price-bearing question:

`Does raw executable cross-venue dislocation exceed frozen full-cycle structural burden?`

No PnL optimization.

### Stage H — Convergence/rebalance/execution

Only headroom survivors proceed to:

- outage-duration risk;
- inventory restoration;
- depth/capacity;
- convergence;
- eventual PnL.

---

## 8. Final second-pass disposition

P1 remains the preferred B15 side investigation, but under a stricter definition:

`B15-P1 INVENTORY-BACKED EFFECTIVE-TRANSFERABILITY SEGMENTATION`

Current status:

`SOURCE-CONCEPT SURVIVES SECOND-PASS REVIEW`

Not established:

- profitable arbitrage;
- adequate event frequency;
- adequate price headroom;
- executable capacity;
- acceptable full-cycle economics.

Next action remains credential/domain capability preflight after account setup.
