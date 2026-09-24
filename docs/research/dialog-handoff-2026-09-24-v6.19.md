# SC001 / B15-P1 — dialog handoff v6.19 — 2026-09-24

Current state:

`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PREPARED`

## Live schema finding

The safe-staged live probe executed and failed closed at current OKX currencies schema validation:

`OKX currencies schema missing required fields in 591 rows`

Immediate root cause: v0.1 wrongly required `feeCcy` on every Get currencies row.

No secret leak, collector launch, price or PnL occurred.

## Preventive compatibility audit

Before another live attempt we also corrected:
- OKX feeGroup/groupId trade-fee schema;
- deprecated fee fallback;
- missing burningFeeRate fail-closed;
- optional maxWd;
- Bybit Spot no-pagination behavior.

## Collector v0.1.3

- runner SHA256: `f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`
- library SHA256: `f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5`
- freeze SHA256: `cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`

## Capability v0.2

- probe SHA256: `29a2f2c19573512e09b2b2175527f584c4f6dbe73d59fba457507d8771c3576a`
- freeze SHA256: `eb4b9bb380dd046df00da1da6284a5af311c45def8974858e3882cc6543af872`

## Combined offline gate

- harness SHA256: `c5a7e33db4442ce16027d3e78fb082488c1b900b7ef8234b10b3cef722fc666a`
- spec SHA256: `70d0907b185d16c18fb321e84a4479f1802e9b4063e88cfed56fedc6fd65de90`
- freeze SHA256: `ede0497bd335a861266f4e554ec53ff0a9484ffbe6aba7301a873f0834735e96`

All freeze-to-file audits passed before commit.

Next:

`RUN_B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_AFTER_USER_APPROVAL`

Do not rerun the old live wrapper.
