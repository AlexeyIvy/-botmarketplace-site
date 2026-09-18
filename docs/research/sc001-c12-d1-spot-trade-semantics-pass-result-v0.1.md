# SC001 — C12-D1 Spot Trade Semantics PASS Result v0.1

Date: 2026-09-18
Status: **PASS — USDC-USDT SPOT ARCHIVE SCHEMA/TIMESTAMP/UTC-STITCH QUALIFIED / PEG OUTCOME CLOSED**

Exact terminal state:

`C12_D1_SPOT_TRADE_SEMANTICS_PASS`

Observed:

- target UTC rows: `24,424`;
- D contribution: `18,388`;
- D+1 contribution: `6,036`;
- both source archives passed schema/timestamp/order integrity;
- peg deviation/threshold/reversion/signal/PnL: `False`;
- promotional alpha accessed: `False`;
- exit code: `0`.

Interpretation:

C12 historical SPOT trade semantics require D+D1 UTC stitching and are now qualified for later parity research.

No trade price was compared with the 1.0000 parity anchor.
