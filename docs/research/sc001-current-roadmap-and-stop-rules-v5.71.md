# SC001 Current Roadmap and Stop Rules v5.71

Date: 2026-09-24  
Status: **B15-P1 LIVE API SCHEMA AUDIT COMPLETE / COLLECTOR v0.1.3 + CAPABILITY v0.2 COMBINED OFFLINE VALIDATION NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.70.md`

## Latest live attempt

The safe-staging permission correction worked: the probe executed as `botmarket` and reached authenticated OKX source metadata.

The v0.1 capability probe then stopped fail-closed with:

`OKX currencies schema missing required fields in 591 rows`

Safety remained intact:
- secrets printed = false;
- collector launch = false;
- price/PnL = false.

## Root cause and broader audit

Immediate cause:

`feeCcy` was incorrectly required on every row returned by OKX `GET /api/v5/asset/currencies`.

The current Get currencies schema does not require `feeCcy`.

A broader API-compatibility audit identified additional issues before retry:

1. OKX current `GET /api/v5/account/trade-fee` uses `feeGroup[]` with `groupId`;
2. top-level OKX maker/taker fields are deprecated compatibility fields;
3. Bybit Spot instruments do not support pagination;
4. absent `burningFeeRate` must not silently become zero;
5. `maxWd` is optional for the Stage C source model.

## Collector v0.1.3

The collector itself was hardened before another live attempt so that a future slow fee refresh cannot fail on the current OKX schema.

Runner SHA256:

`f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`

Library SHA256:

`f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5`

Freeze SHA256:

`cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`

Hardening:
- OKX feeCcy optional;
- absent feeCcy explicitly classified as withdrawn-asset fee units for Get currencies;
- missing burningFeeRate fails closed;
- nonzero burningFeeRate remains REVIEW;
- maxWd optional;
- feeGroup/groupId primary trade-fee parser;
- deprecated top-level fee fields explicit fallback;
- ambiguous multi-group fee response fails closed;
- Bybit Spot no-pagination behavior bound.

Frozen identity/route, 15-second cadence and Stage C 61/71 bps rules are unchanged.

## Capability probe v0.2

Probe SHA256:

`29a2f2c19573512e09b2b2175527f584c4f6dbe73d59fba457507d8771c3576a`

Freeze SHA256:

`eb4b9bb380dd046df00da1da6284a5af311c45def8974858e3882cc6543af872`

The v0.2 probe:
- profiles OKX optional/economic fields rather than requiring feeCcy;
- stores OKX instrument groupId in capability metadata;
- directly tests feeGroup parsing and ambiguity fail-closed;
- removes Bybit Spot cursor/limit logic;
- still contains no price/order/transfer/withdrawal call.

## Combined offline validation

Instead of separate collector and capability test runs, the next Runner bundle will execute them atomically in one offline gate.

Combined harness SHA256:

`c5a7e33db4442ce16027d3e78fb082488c1b900b7ef8234b10b3cef722fc666a`

Combined spec SHA256:

`70d0907b185d16c18fb321e84a4479f1802e9b4063e88cfed56fedc6fd65de90`

Combined freeze SHA256:

`ede0497bd335a861266f4e554ec53ff0a9484ffbe6aba7301a873f0834735e96`

The combined gate requires:
- collector v0.1.3 compile+self-test PASS;
- all 28 collector mandatory tests PASS;
- capability v0.2 compile+self-test PASS;
- no credentials/network calls;
- no capability live snapshot;
- no collector launch;
- no price/PnL.

## Important

Do **not** rerun the old v0.1 live wrapper yet.

A new v0.2 safe-staging live wrapper will be created only after the combined offline validation PASS.

## Next state

`RUN_B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_AFTER_USER_APPROVAL`
