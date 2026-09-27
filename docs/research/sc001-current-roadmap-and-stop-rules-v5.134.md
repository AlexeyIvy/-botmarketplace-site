# SC001 Current Roadmap and Stop Rules v5.134

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 price-anchor extractor offline self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.133.md`

## B13-C current frozen state

Canonical exact cluster freeze:
- 1,905 eligible clusters;
- IDs `S0C000001 .. S0C001905`;
- 76 required archives;
- master SHA `0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b`.

Archive HEAD preflight:
- 76/76 PASS;
- total compressed bytes = 2,633,144,445;
- total compressed GiB = 2.452.

Real price bodies remain unopened.

## Exact extractor self-test bundle

Bundle ID:

`bundle_20260927T074816Z_abb0ce4f`

SHA256:

`e9fdaa98fe9950d173ba5a136e4e9b2dafed095237be23baac581b499cd9a568`

Approval code:

`BM-E9FDAA98FE99`

Runtime:

`offline-research-v1`

Inputs:
none

Package files:
17

Package bytes:
1,054,178

Entrypoint:

`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1.py`

SHA256:

`f4a337fb8ff8f001e239ac0de8b33dcbb3fbdbbdfa2b3387e3f4ead6c60fbe07`

Expected PASS:

`B13C_S0_PRICE_ANCHOR_EXTRACTOR_V01_SELF_TEST_PASS`

## Self-test scope

The offline test verifies:
- exact master SHA;
- all 10 chunk SHA bindings;
- exact 1,905 contiguous cluster IDs;
- exact 76 archive identities;
- gzip CSV parser;
- Bybit first-five header semantics;
- timestamp ordering;
- chronologically-last trade selection in frozen one-second buckets.

It performs:
- no network calls;
- no real price-body access;
- no return calculation;
- no threshold outcome;
- no PnL.

## After PASS

Prepare the networked VPS extraction command, but require a separate explicit approval because that step will open real historical price bodies for the first time.

## Next state

`RUN_B13C_S0_PRICE_ANCHOR_EXTRACTOR_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
