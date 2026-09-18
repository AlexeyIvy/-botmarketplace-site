# SC001 — C7-D1 DOGE Leading-Update Diagnostic Result v0.1

Date: 2026-09-18
Status: **DIAGNOSTIC PASS — FIRST FULL SNAPSHOT FOUND AFTER LEADING UPDATES / NO PRICE OUTCOME**

Parent:

`docs/research/sc001-c7-d1-v0.1-doge-leading-action-review-v0.1.md`

Observed on:

`DOGE-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz`

## 1. Leading-action result

- first records are `update`;
- leading updates before first snapshot: `3609`;
- first snapshot record index: `3610`;
- first snapshot timestamp: `1707696060009`;
- first snapshot UTC: approximately `2024-02-12T00:01:00.009Z`;
- diagnostic result: `FIRST_SNAPSHOT_FOUND`.

The first 20 inspected records were all:

- instrument = `DOGE-USDT-SWAP`;
- action = `update`;
- timestamps nondecreasing in the displayed sample.

## 2. Interpretation

The DOGE daily archive begins with updates whose causal predecessor book is not contained in the same archive.

Applying those updates to an empty book would be invalid.

However, the archive contains a full snapshot shortly after the UTC day begins.

Therefore a fail-closed, causal replay can begin at the first observed full snapshot.

## 3. Frozen repair rule

C7-D1 v0.2 may:

1. scan the source stream from the beginning;
2. validate leading records syntactically/instrument/timestamp/action;
3. discard all leading `update` records before the first `snapshot`;
4. initialize the reconstructed book from that first `snapshot`;
5. continue all later snapshot/update semantics unchanged;
6. leave all grid seconds before that first snapshot missing;
7. never synthesize or backfill the missing initial book.

This is a source-semantics repair only.

## 4. No research-rule changes

Unchanged:

- frozen 7-asset universe;
- 2024-02-12 calibration date;
- 1-second causal grid;
- 1000 ms freshness rule;
- per-asset >=80,000 valid sampled seconds;
- 24 UTC-hour coverage;
- already-frozen C7-S0 spread/headroom rules;
- no maker/fill/queue/adverse-selection/PnL in D1.

## 5. Research integrity

No spread or C7 asset eligibility was calculated during diagnosis.

This diagnostic is not a strategy result and does not authorize dropping DOGE.
