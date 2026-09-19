# SC001 — B13-B Cross-Venue Underlying Identity Audit v0.1

Date: 2026-09-19
Status: **MANDATORY SOURCE-SEMANTIC CORRECTION BEFORE B13-B RESEARCH VERDICT**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b13b-s0-raw-run-output-v0.1.md`;
- `docs/research/sc001-b13b-d0-launch-source-census-protocol-v0.1.md`;
- `docs/research/sc001-b13b-exact-7-event-launch-set-freeze-v0.1.md`.

## 1. Audit trigger

The raw S0 output contained two extreme observations:

- BB ~58,606 bps;
- QNT ~1,291 bps.

Before any convergence outcome, the same-underlying assumption was re-audited against official venue product descriptions.

## 2. BB identity collision

Frozen pairing:

- OKX: `BB-USDT-SWAP`, listTime 2026-06-01 09:00 UTC;
- Bybit: `BBUSDT`.

Official OKX listing materials classify the June 1, 2026 BB perpetual among selected stock/equity perpetuals.

Bybit's BB asset is BounceBit crypto.

Therefore:

`BB_OKX_2026_EQUITY != BB_BYBIT_BOUNCEBIT_CRYPTO`

Classification:

`SEMANTIC_IDENTITY_INVALID_TICKER_COLLISION`

The ~58,606 bps raw comparison is not a same-underlying launch dislocation.

## 3. QNT identity collision

Frozen pairing:

- OKX: `QNT-USDT-SWAP`, listTime 2026-06-05 10:30 UTC;
- Bybit: `QNTUSDT`.

Official OKX listing materials classify QNT/USDT as an equity perpetual.

Bybit identifies QNT as the Quant cryptocurrency.

Therefore:

`QNT_OKX_2026_EQUITY != QNT_BYBIT_QUANT_CRYPTO`

Classification:

`SEMANTIC_IDENTITY_INVALID_TICKER_COLLISION`

The ~1,291 bps raw comparison is not a same-underlying launch dislocation.

## 4. Remaining five events

The remaining OKX launch materials classify:

- KITE as crypto / Kite AI;
- UB as crypto / Unibase;
- MEGA as crypto / MegaETH;
- IRYS as crypto / Irys;
- VVV as crypto / Venice.

No equity-vs-crypto ticker collision analogous to BB/QNT is identified for these five.

Their raw headroom observations remain descriptive nonpromotional evidence only.

KITE additionally warrants explicit quote-unit/contract-denomination corroboration before any future convergence study.

## 5. D0 design defect

The original D0 source census effectively treated:

`same ticker string == same underlying`

This is insufficient when equity perpetuals and crypto perpetuals can share ticker strings across venues.

Classification:

`D0_CROSS_VENUE_UNDERLYING_IDENTITY_ADMISSION_DEFECT`

## 6. Correct S0 sample accounting

The frozen S0 sample gate required the intended same-underlying source pair and >=6/7 coactive-valid events.

BB and QNT fail the same-underlying prerequisite.

Maximum semantically valid historical sample:

`5 / 7`

Therefore the frozen sample gate fails.

Correct research state:

`B13B_S0_DEFER_SAMPLE`

Reason:

`CROSS_VENUE_UNDERLYING_IDENTITY_FAILURE_2_OF_7`

The raw implementation SURVIVE token remains in the audit trail but is not the binding research verdict.

## 7. Descriptive information only

Without creating a five-event substitute verdict, the five non-collision raw observations were all above 50 bps:

- KITE ~300.59;
- UB ~303.63;
- MEGA ~386.38;
- IRYS ~138.98;
- VVV ~253.96.

No five-event promotion is authorized.

## 8. No-replacement rule

Do not:

- replace BB/QNT with other historical launches;
- expand the historical window;
- lower the 6/7 sample gate;
- call the five-event subset SURVIVE;
- proceed to historical convergence on this set.

## 9. Prospective fix

For every future B13-B event, admission must occur before price access and require:

- venue/instrument;
- asset class;
- full underlying/project/company name;
- official reference;
- base/quote;
- price quotation unit;
- contract/face-value semantics;
- launch timestamp;
- mature-reference age.

Cross-venue admission requires explicit underlying and denomination compatibility.

## 10. Candidate state

B13-B remains:

`B13-B_NOT_YET_C13`

Historical S0 is:

`B13B_S0_DEFER_SAMPLE`

No convergence, execution, PnL or candidate-ID assignment is authorized.
