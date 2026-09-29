# SC001 — Next Primary Forced-Flow Relative Dislocation Source-Semantic Gate v0.2

Date: 2026-09-29
Status: PREFROZEN FAIL-CLOSED GATE / QUALIFICATION INCOMPLETE / NO PRICE OUTCOME AUTHORIZED
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01

Supersedes:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-source-semantic-gate-v0.1.md

## Frozen sources

Use only:
- existing B13-C Bybit explicit-liquidation semantics; no collector change;
- Bybit public linear-USDT-perpetual trades for the affected frozen contract;
- OKX public same-underlying USDT perpetual trades as observation-only reference;
- official Bybit/OKX instrument metadata.

Frozen universe:
BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

No symbol may be silently removed because of later outcome.

## Fee/product qualification

Binding fee card:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-fee-qualification-v0.1.md.

Common conservative regular-user Bybit taker fee for S0:
11 bps/fill.

This fee choice is frozen before outcome and cannot be lowered using S0 evidence.

## Economic identity gate

Before any cross-venue price ratio, record and PASS for both instruments:
1. matching asset class;
2. full underlying identity;
3. perpetual contract type;
4. compatible price economic unit;
5. compatible quote currency semantics;
6. compatible settlement denomination;
7. contract face-value/multiplier semantics that cannot distort the ratio;
8. standard trading state, not pre-market;
9. timestamp unit and trade-time semantics.

For Bybit, require exact linear perpetual identity, USDT quote/settlement compatibility and active standard trading state.
For OKX, require same underlying, linear USDT perpetual/swap identity, USDT settlement compatibility, and recorded contract-value semantics.

Ticker equality or a simple SYMBOLUSDT -> SYMBOL-USDT-SWAP mapping is not proof of identity. Do not infer normalization from observed price ratios.

Any unresolved item gives PREOUTCOME_ECONOMIC_IDENTITY_REVIEW and no S0 ratio may be calculated until resolved from official source semantics.

## Strict-coactive clock

Freeze STRICT_COACTIVE_1S_NO_CARRY_FORWARD.

For UTC bucket [s,s+1s):
- Bybit price = chronologically last valid public trade inside that bucket;
- OKX price = chronologically last valid public trade inside that bucket;
- bucket eligible only when both venues trade in the exact same second;
- no carry-forward, interpolation, nearest-second, mark/index/premium/spot substitution.

For eligible seconds only:
raw_basis_bps(s) = 10000 * ln(P_Bybit(s) / P_OKX(s)).

Causal reference:
- wall-clock lookback [s-300s,s);
- current second excluded;
- strict-coactive observations only;
- minimum 120;
- reference = median prior raw basis.

Fewer than 120 prior coactive observations => event is not basis-reference eligible at that observation.

## Event/source integrity

Inherited B13-C/RB021 liquidation-gap censor remains binding:
- censor cluster if the liquidation window overlaps a recorded source gap within +/-5s;
- never interpret a source gap as absence of liquidations.

Observation bucket:
- first strict-coactive 1-second bucket whose start is >= cluster_end+1s and < cluster_end+2s;
- if unavailable: SOURCE_OR_LATENCY_INELIGIBLE_EVENT;
- do not open a later bucket as rescue.

Implementation must fail closed for malformed/unknown external schemas under the binding pre-outcome semantic/implementation gate.

## Operational continuity gate

Binding qualification:
docs/research/sc001-next-primary-forced-flow-relative-dislocation-operational-source-continuity-qualification-v0.1.md.

Current state:
B13C_FRESH_WINDOW_CONTINUITY_NOT_ESTABLISHED_READONLY.

The fresh window may not be moved or reconstructed. S0 remains unauthorized until continuity is established read-only.

S0 remains forbidden from L1/L2, mark/premium/index substitutes, funding, spot, external hedge trades, later convergence price, returns and PnL.

This gate freezes design only. Full source-semantic qualification, implementation handshake and operational continuity must PASS before any S0 outcome access.
