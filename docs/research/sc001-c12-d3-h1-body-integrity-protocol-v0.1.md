# SC001 — C12-D3 H1 Historical Spot Body Integrity v0.1

Date: 2026-09-18
Status: **FROZEN BODY-INTEGRITY STAGE AFTER C12-S0 RULE FREEZE / NO PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c12-d2-v0.2-h1-archive-metadata-pass-result-v0.1.md`;
- `docs/research/sc001-c12-d1-spot-trade-semantics-pass-result-v0.1.md`;
- `docs/research/sc001-c12-s0-parity-reversion-sentinel-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.17.json`.

## 1. Purpose

Download and integrity-verify the exact 182 H1-2025 USDC-USDT historical trade archives **after** the C12-S0 parity/reversion rules have already been frozen.

D3 must not calculate peg deviation or reversion.

## 2. Exact source set

Exactly the 182 metadata-qualified archives:

`2025-01-01 through 2025-07-01`

inclusive.

No date may be added/dropped.

## 3. Acquisition

For every archive:

- re-resolve exact trusted priapi SPOT URL;
- sequential requests;
- same rate-limit-safe 429/backoff policy as C12-D2 v0.2;
- GET final URL must remain exact trusted `static.okx.com`;
- downloaded byte count must equal D2 frozen Content-Length;
- exact-size local body may be reused.

Total source budget is the D2-qualified ~61 MB set.

## 4. Body integrity

For every archive require:

- ZIP CRC PASS;
- exactly one regular CSV member;
- exact header:
  `instrument_name,trade_id,side,price,size,created_time`;
- exact instrument `USDC-USDT`;
- side in `buy/sell`;
- finite positive price/size;
- resolvable timestamp scale;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- zero malformed rows;
- source row count >0.

Price may be validated numerically only.

It must not be compared with 1.0000 in D3.

## 5. Persistent checkpoint

After each archive passes download + integrity:

record atomically:

- date;
- filename;
- bytes;
- SHA256;
- source row count;
- first/last timestamp;
- timestamp scale.

Resume must reverify local file bytes + SHA before accepting checkpoint state.

## 6. PASS

Exact:

`C12_D3_H1_BODY_INTEGRITY_PASS`

requires `182 / 182` exact archives to pass.

REVIEW:

`C12_D3_H1_BODY_INTEGRITY_REVIEW`

is engineering/data state only.

## 7. Firewalls

Must remain false:

- peg_deviation_calculated;
- parity_episode_calculated;
- reversion_outcome_calculated;
- strategy_signal_calculated;
- fill_model_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. Consequence of PASS

Only after D3 PASS may the already-frozen C12-S0 parity/reversion runner be implemented and executed.

No threshold may change after D3.
