# SC001 Current Roadmap and Stop Rules v5.133

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A DEFER_DATA / B13-C S0 price-anchor extractor frozen, offline self-test next**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.132.md`

## B13-C current evidence state

Exact source-only cluster freeze:
- 1,905 clusters;
- 76 required Bybit archives;
- canonical master SHA `0636ac25d6b7a484a4a9959f256aa57e0a1ead7f4e228423715f688b194fb87b`.

Archive metadata:
- 76/76 HEAD PASS;
- total compressed bytes = 2,633,144,445;
- price bodies still unopened.

## Price-anchor extraction protocol frozen

Protocol:
`docs/research/sc001-b13c-s0-streaming-price-anchor-extraction-protocol-v0.1.md`

SHA256:
`be87a3e480d6e21b8a5f6bcac9871ad03b7125dccd8fc04797e27beb49fa5b46`

Extractor:
`research/sc001/sc001_b13c_s0_streaming_price_anchor_extractor_v0_1.py`

SHA256:
`f4a337fb8ff8f001e239ac0de8b33dcbb3fbdbbdfa2b3387e3f4ead6c60fbe07`

Architecture:
- one archive at a time;
- exact frozen URL/Content-Length;
- compressed SHA256;
- gzip/CSV/schema/timestamp checks;
- exact frozen entry/exit bucket extraction;
- archive deleted after successful extraction;
- resume via per-archive ledger/candidate SHA;
- no returns, signed reversal, threshold result or PnL.

## Next gate

Run an offline synthetic self-test in Research Runner before any price body access.

Expected:
`B13C_S0_PRICE_ANCHOR_EXTRACTOR_V01_SELF_TEST_PASS`

Only after self-test PASS and a separate explicit approval may the networked VPS extractor open the 76 price bodies.

## Current next state

`SEAL_B13C_S0_PRICE_ANCHOR_EXTRACTOR_OFFLINE_SELFTEST`
