# SC001 — B15-P1 Transferability Shock Source / Access / Semantic Feasibility Audit v0.1

Date: 2026-09-19
Status: **SOURCE-FEASIBLE / AUTHENTICATED READ-ONLY ACCESS REQUIRED / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-b15-independent-base-multi-role-critical-review-v0.1.md`

## 1. Objective

Determine whether B15-P1 can be observed prospectively and causally before any cross-venue price/headroom outcome is opened.

No price, spread, return or PnL data is used in this audit.

## 2. Preferred first venue pair

Use:

- OKX;
- Bybit.

Reason:

- both already have qualified SC001 market-data infrastructure;
- both expose chain-level deposit/withdraw capability metadata;
- the required state can be observed without trading permissions.

No claim is made yet that this pair has profitable transferability-shock dislocations.

## 3. OKX source

Endpoint:

`GET /api/v5/asset/currencies`

Access:

`AUTHENTICATED`

The OKX Funding/Asset module requires authentication.

Relevant chain-level fields include:

- `ccy`;
- `chain`;
- `ctAddr`;
- `canDep`;
- `canWd`;
- `depEstOpenTime`;
- `wdEstOpenTime`;
- `fee`;
- `minDep`;
- `minWd`;
- `mainNet`;
- confirmation fields.

Semantics:

- `canDep=false` => on-chain deposit unavailable for that chain;
- `canWd=false` => on-chain withdrawal unavailable for that chain.

Important:

OKX explicitly distinguishes multiple chains for one currency.

Therefore coin ticker alone is not a valid identity key.

Access-control requirement:

use an API key with Read permission only.

Do not grant Trade or Withdraw permission for B15 source collection.

## 4. Bybit source

Endpoint:

`GET /v5/asset/coin/query-info`

Access:

`AUTHENTICATED`

Relevant chain-level fields include:

- `coin`;
- `chain`;
- `chainType`;
- `contractAddress`;
- `chainDeposit`;
- `chainWithdraw`;
- `withdrawFee`;
- `withdrawPercentageFee`;
- `depositMin`;
- `withdrawMin`;
- confirmation fields.

Semantics:

- `chainDeposit=0` => deposit suspended;
- `chainDeposit=1` => deposit normal;
- `chainWithdraw=0` => withdrawal suspended;
- `chainWithdraw=1` => withdrawal normal.

Bybit API keys support a read-only mode.

Live B15 preflight must verify that the exact read-only key created for this collector can call the coin-info endpoint before collection starts.

## 5. Security posture

B15 source collector must use dedicated read-only credentials.

Required:

- no Trade permission;
- no Withdraw permission;
- bind keys to VPS IP where exchange policy supports it;
- secrets never committed to Git;
- secrets never printed to logs;
- secrets never pasted into research reports;
- secrets stored in a local root/user-readable-only EnvironmentFile or existing project secret manager.

## 6. Causal time semantics

Neither selected status endpoint is treated as a historical event archive.

B15 will create its own prospective chronology.

For every poll record:

- local request-start timestamp;
- local receive timestamp;
- venue response/server timestamp when available;
- normalized chain state;
- hash of normalized response state.

A state change is not assigned a fabricated exact exchange timestamp.

If state changed between poll N and poll N+1, causal transition time is an interval:

`(last_seen_old_state, first_seen_new_state]`

Later price analysis may use only information available at or after first observation of the new state.

No backdating to the unknown true exchange-internal transition time.

## 7. Required normalized identity

Canonical B15 transfer identity must be at least:

`venue × asset × network × contract/native identity`

Required mapping fields:

- venue;
- venue coin code;
- venue chain code;
- normalized network family;
- native-vs-token flag;
- contract address when applicable;
- deposit state;
- withdrawal state.

Cross-venue pairing is allowed only after explicit identity sign-off.

Ticker-only mapping is forbidden.

## 8. Native-asset caveat

Some native assets have no token contract address.

For those cases, identity cannot be proven by empty contractAddress equality.

A separate canonical network mapping must be frozen before admission.

If chain identity is ambiguous:

`IDENTITY_REVIEW`

No price comparison.

## 9. Prospective collector architecture

Preferred source collector:

- one OKX currencies poll;
- one Bybit coin-info poll;
- fixed cadence;
- append-only raw + normalized snapshots;
- emit explicit state-change records;
- no price feed in the same process.

Preliminary safe cadence:

`30 seconds`

This is far below documented endpoint rate limits and is sufficient for first source-feasibility collection.

Cadence may not later be tuned using observed price outcomes.

## 10. Initial event taxonomy

Without using prices, classify state changes as:

- `DEP_OFF`;
- `DEP_ON`;
- `WD_OFF`;
- `WD_ON`;
- `CHAIN_APPEARED`;
- `CHAIN_DISAPPEARED`;
- `IDENTITY_CHANGED`;
- `SOURCE_INVALID`.

Do not classify an event as profitable/unprofitable.

## 11. Transferability-shock state

Do not collapse all outages into one boolean.

Per venue/network maintain four directional capabilities:

- can receive asset on-chain;
- can send asset on-chain;
- counterpart can receive;
- counterpart can send.

A later arbitrage architecture must specify which transfer direction is economically blocked.

## 12. Source audit verdict

`B15_P1_SOURCE_FEASIBILITY_PASS_AUTH_READ_ONLY_REQUIRED`

Reasons:

- both preferred venues expose chain-level transferability state;
- required semantics are explicit enough for a fail-closed prospective collector;
- no paid dataset is required;
- no trading permission is required in principle;
- causal transition chronology can be created prospectively by polling.

Remaining blocker:

`LIVE_READ_ONLY_CREDENTIAL_CAPABILITY_PREFLIGHT`

Until both venue credentials pass read-only source calls:

- do not start B15 status collector;
- do not open cross-venue prices;
- do not define a price threshold.

## 13. Next exact step

Prepare a credential-safe read-only capability preflight for OKX + Bybit.

The user must never paste API secrets into chat.

Credentials should be created with the minimum permissions and installed directly on the VPS in a protected local env file.

After credential preflight PASS, freeze:

- poll cadence;
- raw/normalized schema;
- chain identity mapping rules;
- source-gap semantics;

then start prospective transferability-state collection.

Only after clean status events exist may an Edge-to-Fill/headroom protocol be frozen.
