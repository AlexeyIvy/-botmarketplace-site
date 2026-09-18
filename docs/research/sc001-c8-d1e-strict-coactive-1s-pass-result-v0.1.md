# SC001 — C8-D1E Strict Coactive 1s Clock PASS Result v0.1

Date: 2026-09-18
Status: **PASS — STRICT COACTIVE 1s CLOCK REPRESENTATION QUALIFIED / NO PRICE OUTCOME**

Exact terminal state:

`C8_D1E_STRICT_COACTIVE_1S_PASS`

Observed on the frozen engineering day 2025-01-15:

- OKX active seconds: `80,640`;
- Bybit active seconds: `77,076`;
- joint coactive seconds: `72,539`;
- joint coactive share of UTC day: about `0.83957`;
- minimum joint-active seconds in any UTC hour: `2,378`;
- median absolute last-event timestamp skew: `150.5 ms`;
- p99 absolute last-event timestamp skew: `846.7 ms`;
- failed gates: none;
- cross-venue price/return/dislocation/lag: false;
- leader/signal/PnL: false;
- promotional alpha: false;
- exit code: `0`.

Interpretation:

Free historical OKX and Bybit trade streams are sufficiently synchronized for second-level cross-venue research **when restricted to strict same-second coactivity with no carry-forward**.

Qualified representation:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

The prior full-day carry-forward representation remains not qualified.

The 2025-01-15 bodies remain engineering-only evidence and are not clean price/dislocation Selection evidence.
