# SC001 Current Roadmap and Stop Rules v2.7

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.6.md`

## 1. Terminal history

E001-E007 remain terminal/closed exactly as previously recorded. SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E008 current state

- `E008_DATA_INVENTORY_PASS`: all four contaminated engineering L2 days + trade tapes are present on VPS.
- `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` v0.1 remains unchanged.
- Failure driver: 2024-02-13 prior-book age <=5 s share about 96.92% versus frozen >=99.5% gate.
- Feb-13 forensic completed with category `CONCENTRATED_SOURCE_GAPS`:
  - stale >5 s trades: 34,386;
  - stale episodes: 6;
  - top-10 episode trade share: 1.0;
  - L2 gaps >5 s: 9;
  - max L2 gap: 22,170 ms.
- No fill simulation, maker P&L or profitability has been calculated.

## 3. Interpretation

The v0.1 REVIEW is not converted to PASS and its 5-second gate is not weakened.

Because the stale observations are concentrated in explicit source gaps, E008 may test a new stricter live-implementable **fail-closed stale-latch data model** before any fill simulation:

- book age >5 s => `STALE_LATCH`;
- no quoting/fill/queue progress while latched;
- incremental updates do not restore trust;
- only a later full snapshot restores trusted book state.

## 4. Frozen v0.2 data-model audit

Protocol:
`docs/research/sc001-e008-stale-latch-data-model-protocol-v0.2.md`

Runner:
`research/sc001/sc001_e008_stale_latch_audit_v0_2.py`

This stage calculates no fills/spread capture/inventory/markout/fees/P&L/profitability.

Allowed terminal states:
- `E008_STALE_LATCH_MODEL_PASS`;
- `E008_STALE_LATCH_MODEL_REVIEW`.

## 5. Stop rules

Do not:
- relabel queue-feasibility v0.1 as PASS;
- weaken the 5-second stale threshold;
- let cancellations advance queue;
- let incremental updates after a detected gap immediately restore trust;
- calculate maker profitability before stale-latch semantics pass and a separate conservative simulator is frozen;
- add TFI or prior strategy features;
- open Q2/Validation/Final.

## 6. Immediate next action

On VPS:
1. `git pull --ff-only`;
2. syntax-check `sc001_e008_stale_latch_audit_v0_2.py`;
3. run only the no-fill stale-latch audit;
4. inspect terminal result;
5. do not run any maker simulator yet.
