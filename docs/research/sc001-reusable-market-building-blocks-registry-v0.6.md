# SC001 — Reusable Market Building Blocks Registry v0.6

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C12-S0**
Parent: `sc001-reusable-market-building-blocks-registry-v0.5.md`

## 1. Inheritance

RB001-RB018 remain unchanged.

## 2. New reusable block

### RB019 — Direct stablecoin parity-stress state v0.1

- source evidence: C12-S0 / F025-F026;
- reference: fixed external 1.0000 USDC-USDT cross-parity;
- preferred roles:
  - R2 regime/risk state;
  - R3 veto;
  - R5 execution/collateral warning;
  - R6 external reference;
- H1 observation:
  - only 3 >=30 bps episodes;
  - all in one month;
  - 2/3 returned to <=10 bps within 30m;
  - gross reversion magnitude descriptive median ~25.94 bps;
- evidence strength:
  `RARE_CLUSTERED_STATE / DESCRIPTIVE_REVERSION_ONLY`;
- reusable lesson:
  a feature may have adequate economic magnitude yet fail as a systematic strategy because event frequency and regime breadth are too low;
- forbidden reuse:
  threshold lowering or historical stress-period selection under C12.
