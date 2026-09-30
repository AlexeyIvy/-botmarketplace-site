# SC001 — Forced-Flow Relative Dislocation Source-Semantic Qualification Protocol v0.1

Date: 2026-09-30
Status: FROZEN PRE-OUTCOME METADATA-ONLY QUALIFICATION / NO S0 OUTCOME
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION

## Purpose

Complete the pre-outcome economic-identity/source-semantic gate for the exact 12-symbol frozen universe without opening any S0 price/outcome.

This qualification may access only official public instrument metadata from Bybit and OKX.

It must not call:
- trade/recent-trade endpoints;
- order-book/L1/L2 endpoints;
- mark/index/premium/funding endpoints;
- historical trade bodies;
- returns/PnL/trading endpoints.

## Frozen universe

Bybit -> OKX:
- BTCUSDT -> BTC-USDT-SWAP
- ETHUSDT -> ETH-USDT-SWAP
- SOLUSDT -> SOL-USDT-SWAP
- DOGEUSDT -> DOGE-USDT-SWAP
- ORDIUSDT -> ORDI-USDT-SWAP
- FILUSDT -> FIL-USDT-SWAP
- UNIUSDT -> UNI-USDT-SWAP
- XRPUSDT -> XRP-USDT-SWAP
- LTCUSDT -> LTC-USDT-SWAP
- OPUSDT -> OP-USDT-SWAP
- BCHUSDT -> BCH-USDT-SWAP
- SUIUSDT -> SUI-USDT-SWAP

No symbol substitution.

## Official metadata sources

Bybit:
GET /v5/market/instruments-info
category=linear
symbol=EXACT_FROZEN_SYMBOL

Require:
- symbol exact;
- contractType = LinearPerpetual;
- status = Trading;
- baseCoin = expected frozen base;
- quoteCoin = USDT;
- settleCoin = USDT;
- isPreListing is false.

Record symbolType/fullName only as non-alpha metadata.

OKX:
GET /api/v5/public/instruments
instType=SWAP
instId=EXACT_FROZEN_INST_ID

Require:
- instId exact;
- instType = SWAP;
- state = live;
- uly = BASE-USDT;
- instFamily = BASE-USDT;
- ctType = linear;
- settleCcy = USDT;
- ctValCcy = BASE;
- ctVal is finite and >0.

Record ctVal/ctMult only as contract-unit metadata.

## Economic identity interpretation

Ticker equality alone is insufficient.

A pair passes only when both venues independently assert:
- the same frozen base asset code;
- USDT quote/settlement semantics;
- linear perpetual/swap contract type;
- live/standard trading state;
- compatible contract-value currency semantics;
- no Bybit pre-market state.

For the fixed SC001 universe, this joint metadata contract is the permitted proof for derivative economic-unit compatibility before a price ratio. Any disagreement is fail-closed.

No multiplicative normalization may be inferred from observed prices.

## Trade-clock semantics

No live trade body is opened in this qualification.

Strict-coactive trade-clock semantics are inherited from validated RB011 / C8:
- exact UTC one-second coactivity;
- chronologically last valid trade inside the same second;
- exchange trade timestamp in milliseconds;
- no carry-forward;
- current-second exclusion from the 300-second causal basis reference.

Implementation parser fixtures must accept the frozen Bybit/OKX documented trade schemas and reject malformed timestamp fixtures without making a network trade request.

## Gate

PASS only if:
- all 12 Bybit instruments pass;
- all 12 OKX instruments pass;
- all 12 pair-level economic-identity checks pass;
- parser/self-test fixtures pass;
- every forbidden endpoint counter remains zero/false.

PASS:
FORCED_FLOW_SOURCE_SEMANTIC_PREFLIGHT_PASS

Otherwise:
FORCED_FLOW_SOURCE_SEMANTIC_PREFLIGHT_REVIEW

PASS authorizes only completion of the pre-outcome implementation handshake. It does not authorize S0 execution.

## Firewalls

Must remain false:
- trade_body_accessed;
- price_outcome_accessed;
- cross_venue_price_ratio_calculated;
- return_calculated;
- pnl_calculated;
- l1_l2_accessed;
- mark_index_premium_accessed;
- funding_accessed;
- trading_accessed.
