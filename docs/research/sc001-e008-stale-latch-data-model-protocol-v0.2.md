# SC001-E008 — Fail-Closed Stale-Latch Data Model Protocol v0.2

Date: 2026-09-16  
Status: **FROZEN DATA-MODEL AUDIT — NO FILLS / NO P&L**

Parent results:
- `E008_DATA_INVENTORY_PASS`;
- `E008_QUEUE_MODEL_FEASIBILITY_REVIEW` v0.1;
- `E008_FEB13_STALE_BOOK_FORENSIC_COMPLETE`, category `CONCENTRATED_SOURCE_GAPS`.

## 1. Purpose

Define and audit a live-implementable, fail-closed book-validity rule for historical E008 simulation without weakening or reclassifying queue-feasibility v0.1.

Queue-feasibility v0.1 remains REVIEW permanently.

## 2. Frozen stale-latch semantics

For each qualified L2 day:

1. the book becomes trusted only after a valid full snapshot;
2. while trusted, maintain `last_l2_ts`;
3. if wall-clock/book age exceeds `5,000 ms` since `last_l2_ts`, enter `STALE_LATCH` at exact time `last_l2_ts + 5,000 ms`;
4. once latched, no hypothetical maker order may be placed, maintained, filled or advanced in queue;
5. all trade volume during the latch gives zero queue progress;
6. incremental L2 updates after the gap do **not** clear the latch, because missing updates may have corrupted reconstructed state;
7. only the next full `snapshot` clears the latch and re-establishes a trusted book;
8. if no later snapshot exists before UTC day end, the latch remains active to day end;
9. same-millisecond ordering ambiguity remains unresolved and may not be used optimistically.

This rule is causal and directly implementable in live operation: a quoting engine can detect book age >5 s and withdraw/disable quoting.

## 3. Why this is not a rescue of v0.1

- v0.1 still fails its frozen `>=99.5% age<=5s` gate on 2024-02-13;
- no v0.1 threshold is changed;
- no maker fills, spread capture, markouts, inventory or P&L have been observed;
- v0.2 introduces a stricter operational data-validity state, not a looser pass threshold.

## 4. Audit scope

Use only the four contaminated engineering days:
- 2024-01-14;
- 2024-01-31;
- 2024-02-12;
- 2024-02-13.

These days remain forbidden as sole promotional E008 evidence.

## 5. Required diagnostics

Per day report:
- source identity PASS;
- number of source inter-record L2 gaps >5 s;
- number of stale-latch episodes;
- stale-latch total duration and share of UTC day;
- number/share of transactions occurring while latched;
- delay from latch start to recovery snapshot;
- maximum recovery delay;
- unrecovered latch count at UTC day end;
- trusted-book interval count;
- explicit no-fill/no-P&L firewall.

## 6. PASS rule

`E008_STALE_LATCH_MODEL_PASS` requires:
- all four qualified sources load and replay deterministically;
- every stale transition is generated exactly at `last_l2_ts + 5000 ms`;
- a latch is cleared only by a later full snapshot;
- no stale episode leaks queue/fill semantics;
- at least one trusted interval exists on every day;
- no source/invariant exception;
- no fills/spread capture/inventory/markout/fees/P&L/profitability calculated;
- Q2/Validation/Final remain closed.

No threshold on stale-time share is introduced after seeing v0.1. The audit is about deterministic safety semantics, not promotional data quality.

## 7. Next step after PASS

Only after PASS may E008 freeze a conservative queue simulator on synthetic fixtures. The four engineering days may then be used only to validate simulator mechanics, never to select profitable parameters.
