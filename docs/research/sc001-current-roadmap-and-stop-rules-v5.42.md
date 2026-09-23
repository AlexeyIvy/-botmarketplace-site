# SC001 Current Roadmap and Stop Rules v5.42

Date: 2026-09-23  
Status: **B15-P1 IDENTITY / ROUTE v0.2.1 SNAPSHOT FROZEN WITH EXPLICIT QUARANTINE**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.41.md`

## 1. Global isolation remains binding

SC001 remains independent from R009, R003, R010 and Safe-Sleeve S002. No frozen decision, forward clock, universe or stop rule in those branches may be changed by B15.

## 2. Source and exact replay

Frozen non-price source run:

`20260920T210446Z`

Exact v0.2.1 replay:

- bundle: `bundle_20260923T193413Z_733e8dda`
- SHA256: `430bc2adcbf35f64f80a82ccbd92535d1a23aa371947049555c32842e6244ece`
- job: `job_20260923T194025Z_8f4da99e`
- status: `B15_P1_INTEGRATED_CANONICAL_REGISTRY_V021_EXACT_REPLAY_PASS`

Exact replay result:

- replayed raw rows = 182
- resolved rows = 173
- unresolved rows = 9
- v0.2.1 review-set assets = GRAM, QTUM, STX, XLM
- newly identity-closed assets from the old review set = 42
- asset common representations = 48
- USDT common representations = 12
- alias collisions = 0
- disposition mismatches = 0
- special oracle hits = 10
- price/PnL = not used
- transfer status for selection = not used

## 3. Freeze-preflight result

Freeze-preflight:

- bundle: `bundle_20260923T194658Z_c19d9497`
- SHA256: `f660a6e0cadf4e1ccf4e8a35534131a6de3a33827b9898e4682a83c885f3ed2f`
- job: `job_20260923T200352Z_e656f035`
- status: `B15_P1_IDENTITY_ROUTE_V021_SNAPSHOT_FREEZE_PREFLIGHT_PASS_WITH_QUARANTINE`
- failed checks: none

Freeze candidate manifest SHA256:

`63393e97573b9d64980f671f08e14071473d624682e4f8d67a2d21236ef0307d`

Freeze file map SHA256:

`4f269e2759edfb525439e7b367bbdf032e78787a158d2f01b48d80b7a33e3406`

## 4. Composite frozen snapshot

The v0.2.1 snapshot is an additive identity-resolution overlay on top of the prior v0.1 canonical state.

Base v0.1:

- admitted assets = 146
- review assets = 46
- excluded assets = 9
- canonical representations = 155
- directed edges = 310
- USDT common representations = 9

v0.2.1 overlay:

- closes 42 of the old 46 review assets
- adds 48 COMMON_PROVEN canonical representations
- adds 96 directed identity edges
- adds 3 USDT common representations
- does not overlap any base edge

Composite snapshot:

- total assets = 201
- admitted assets = 188
- review/quarantine assets = 4
- excluded assets = 9
- canonical representations = 203
- directed identity edges = 406
- USDT common representations = 12
- quote_review = true

## 5. Explicit quarantine / hold set

The following base assets remain quarantined and MUST NOT be silently admitted:

- GRAM
- QTUM
- STX
- XLM

Unresolved rows remain exactly 9:

- GRAM = 2
- QTUM = 2
- STX = 2
- XLM = 1
- USDT = 2

The two USDT hold rows are:

- Bybit CORN
- OKX Tempo

This snapshot freeze is therefore **not** the terminal zero-review route-universe PASS.

## 6. Identity / route separation

Five explicit native identities are known-one-sided and do not grant cross-venue route admission:

- ETH / arbitrum:nova
- BTC / bitcoin:lightning
- G / gravity:alpha
- ETH / robinhood:mainnet
- ETH / unichain:mainnet

Binding rule:

`native identity known != cross-venue route admitted`

A cross-venue route requires a `COMMON_PROVEN` representation. Identity-only rows have no route effect.

ZetaChain uses exact metadata variant `ZetaChain EVM`; no fuzzy matching is allowed.

## 7. Special semantics preserved

The snapshot preserves:

- `BRC20_TICKER_NORMALIZATION`
- `CARDANO_POLICY_ASSET_ORDER_NORMALIZATION`
- `CELO_GOLDTOKEN_NATIVE_INTERFACE`
- `WAXP_EOSIO_TOKEN_NATIVE_INTERFACE`
- `ZKSYNC_ERA_ETH_SYSTEM_BASE_TOKEN`

Gravity Alpha lifecycle remains:

- before 2026-11-01: `REVALIDATION_REQUIRED_BEFORE_RUNTIME_ROUTE`
- on/after 2026-11-01: `ROUTE_DISABLED_DEPRECATED`
- automatic route enablement: forbidden

## 8. Current authorization gates

Still forbidden:

- 15-second collector launch
- final zero-review route-universe PASS claim
- price/PnL research
- transfer-status-driven selection
- rescue tuning of unresolved identity cases

Current flags:

- `collector_authorized=false`
- `price_economic_research_authorized=false`
- `terminal_final_route_universe_pass_claimed=false`

## 9. Persistent freeze artifacts

Stored under:

`docs/research/artifacts/b15-p1-identity-route-v0.2.1-freeze/20260920T210446Z/`

Key artifacts include:

- freeze candidate manifest
- freeze file map
- freeze preflight manifest
- composition candidate
- identity/route overlay candidate
- quote overlay candidate
- quarantine candidate

Freeze record:

`docs/research/sc001-b15-p1-identity-route-v0.2.1-snapshot-freeze-v0.1.json`

## 10. Mandatory next action

Current next state:

`CHECKPOINT_BACKUP_AFTER_IDENTITY_ROUTE_V021_SNAPSHOT_FREEZE`

Required order:

1. persist and commit this freeze;
2. create a portable VPS checkpoint;
3. verify archive hashes;
4. perform restore verification;
5. only then continue with remaining GRAM/QTUM/STX/XLM and USDT CORN/Tempo hold-resolution work;
6. require a new versioned preflight before any terminal zero-review PASS or price/economic stage.

The backup must not place plaintext secrets in the normal archive.
