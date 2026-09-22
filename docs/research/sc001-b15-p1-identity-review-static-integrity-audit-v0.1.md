# SC001 — B15-P1 Identity Review Static Integrity Audit v0.1

Date: 2026-09-23  
Source run: `20260920T210446Z`  
Parent state: `B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW`  
Scope: non-price identity/route integrity only.

## 1. Canonical counts revalidated

Canonical safe export:
`docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/`

Exact `final_builder_manifest.json` values:

- admitted assets: **146**
- identity review assets: **46**
- excluded assets: **9**
- directed edges: **310**
- proven USDT quote routes: **9**
- quote_review: **true**
- price_data_used: **false**
- transfer_status_used_for_selection: **false**

The 46 identity-review assets split exactly into:

- `UNRESOLVED_OBSERVED_ROUTE_OR_IDENTITY`: **16**
- `NO_PROVEN_COMMON_REPRESENTATION`: **30**

No price/PnL stage is authorized.

## 2. The 16 assets with at least one already-proven representation

`AVAX, BABYDOGE, BCH, BTC, ETC, ETH, FIL, G, LINK, LTC, SHIB, SOL, SUSHI, TRX, UNI, XRP`

These assets already contain at least one representation that satisfies the v0.1 registry, but remain review because another observed OKX identity row is unmapped or conflicts with the current representation rules.

Observed blockers include:

- Avalanche X-Chain;
- OKTC and asset-specific `*K-OKTC` rows;
- X Layer / X Layer (WETH);
- Bitcoin Lightning;
- FEVM;
- Gravity Alpha Mainnet;
- Robinhood Chain;
- Unichain;
- ETH metadata discrepancies on Optimism / zkSync Era.

These must not be cleared by fuzzy alias matching.

## 3. The 30 assets with no proven common representation

`CC, CELO, DOT, EGLD, ENJ, FLR, FOGO, GRAM, HBAR, HYPE, ICP, KAIA, KSM, LUNA, MINA, MON, NIGHT, ORDI, QTUM, RVN, S, SATS, STX, THETA, TIA, WAXP, XLM, XPL, ZETA, ZIL`

### 3.1 Network/native registry candidates requiring explicit evidence

The following 24 cases structurally look like missing explicit network/native registry coverage, but are **not auto-admitted**:

`CC, CELO, DOT, EGLD, ENJ, FLR, FOGO, HBAR, HYPE, ICP, KAIA, KSM, LUNA, MINA, MON, QTUM, RVN, S, STX, THETA, TIA, XPL, ZETA, ZIL`

Each needs exact network identity plus native-asset semantics (or a representation-specific rule) before registry expansion.

Special cautions:

- CELO also exposes an OKX `CELO-TOKEN` representation, so one native match must not silently absorb a distinct token representation.
- DOT has an additional OKTC row.
- ZETA exposes Bybit `ZetaChain` and `ZetaChain EVM`; these must not be collapsed without explicit identity semantics.

### 3.2 Special normalization / ambiguity cases

These 6 cases require representation-specific handling, not a generic native rule:

- **GRAM** — both venues expose TON with empty contract identity, but GRAM is not proven native by the current registry. Remain review unless explicit token identity evidence is frozen.
- **NIGHT** — Cardano identifiers contain the same apparent components in reversed order:
  - OKX: `4e49474854:0691...f1fa`
  - Bybit: `0691...f1fa:4e49474854`
  Requires a Cardano-specific canonicalization rule; raw string equality is insufficient.
- **ORDI** — OKX uses `BRC20` with empty contract, Bybit uses Bitcoin with `ordi`. Requires a BRC-20 representation rule.
- **SATS** — same issue as ORDI, with Bybit identity `sats`.
- **WAXP** — OKX uses `eosio.token`, Bybit leaves contract empty. Requires explicit WAX native-token semantics.
- **XLM** — current registry accepts Bybit chainType `XLM`, while observed chainType is `Stellar Lumens`; after that mismatch is fixed, OKX still exposes a non-empty `native:...` marker while Bybit is empty. Requires an explicit Stellar native-marker rule.

## 4. Builder v0.1 integrity findings

The current v0.1 builder must not simply be rescue-tuned by adding aliases until REVIEW becomes PASS.

### 4.1 Contract whitespace normalization

`canon_contract()` does not trim whitespace.

Observed example:

- OKX ETH/Optimism contract value is `" "`
- Bybit OP contract value is empty

This creates an avoidable `EMPTY_NONEMPTY_MISMATCH`.

Required correction: normalize surrounding whitespace before empty/non-empty identity logic.

### 4.2 Case-sensitive chainType false mismatch

The builder trims Bybit `chainType` but compares it case-sensitively against registry variants.

Observed example:

- registry: `ZKsync Era`
- source: `zkSync Era`

This is a metadata spelling/case discrepancy, not representation proof by itself.

Any relaxation must be explicit and deterministic (for example frozen exact variants), not fuzzy runtime matching.

### 4.3 Multiple representations on the same network

The current nested loop can mark an asset unresolved when one venue exposes multiple different representations on the same network and the other venue exposes only one.

A valid match and a distinct one-sided representation should be tracked separately. They must not be conflated as a pairwise contract mismatch.

CELO is the immediate example:
- native-like CELO row;
- separate `CELO-TOKEN` row.

### 4.4 One-sided observed network handling

Known one-sided representations should be explicitly classified as such after their network identity is frozen.

A known OKX-only route is not a proven cross-venue route, but it also should not require inventing a counterpart merely to clear REVIEW.

The registry must distinguish:
- mapped common representation;
- known one-sided representation;
- unresolved/ambiguous representation.

### 4.5 Non-EVM network-specific canonicalization

The current non-EVM rule is generic case-sensitive string equality.

That is insufficient for at least:
- Cardano asset-id formatting;
- BRC-20 ticker identity;
- Stellar native markers;
- WAX native-token semantics.

No generic cross-network normalization is allowed. Rules must be network-specific and versioned.

## 5. Quote graph audit

The currently proven USDT cross-venue routes are exactly 9:

- Aptos
- Arbitrum One
- Avalanche C-Chain
- Ethereum
- Optimism
- Polygon PoS
- Solana
- Tron
- TON

However, `quote_review=true`.

The source contains additional OKX USDT representations such as:

- Berachain (USDT0)
- Monad (USDT0)
- OKTC
- Optimism (USDT0)
- Plasma
- Tempo
- Unichain (USDT0)
- X Layer
- X Layer (USDT0)

and additional Bybit representations such as BSC, CELO, HyperEVM, KavaEVM, Kaia, Mantle, Plasma, Monad, Berachain, etc.

The v0.1 quote loop sets `quote_review=true` whenever an OKX USDT row has no exact Bybit match. Therefore a known one-sided representation can keep REVIEW permanently even when every actual common route is fully classified.

This should be corrected by an explicit route disposition model rather than by forcing aliases to match unrelated networks.

The frozen stop rule remains unchanged:

`pass_requires_quote_graph_complete = true`

For v0.2, “complete” must mean:
- every observed representation is explicitly classified;
- every proven common representation is present in the cross-venue graph;
- one-sided known representations are recorded separately;
- no unresolved aliases/identities remain.

This is a clarification of graph completeness, not a relaxation of the stop rule.

## 6. Required next action

Before any rerun:

1. freeze an explicit v0.2 representation-disposition schema;
2. add deterministic network-specific normalization only where evidence supports it;
3. represent known one-sided networks explicitly;
4. preserve unresolved cases as `IDENTITY_REVIEW`;
5. fix builder technical normalization/pairing issues;
6. freeze new code/registry hashes;
7. only then create and seal a Runner bundle for a non-price B15 identity rerun.

No price endpoints, PnL, transfer-status selection, or rescue tuning are authorized.

## 7. Tooling note

During this dialog, canonical files were re-read successfully from the GitHub mirror at the canonical artifact path.

The Production Runner connector initially responded in this conversation, but later calls returned:

`FORBIDDEN: This conversation does not support developer MCPs`

This is treated as a conversation/tool-routing restriction, not as a VPS/Runner research failure. No manual Termux fallback is authorized.
