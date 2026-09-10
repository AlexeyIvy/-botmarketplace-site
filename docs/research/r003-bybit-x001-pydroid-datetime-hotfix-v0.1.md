# R003-X001 Bybit — Pydroid datetime compatibility hotfix v0.1

**Date:** 2026-09-10  
**Status:** technical compatibility correction before result inspection  
**Frozen research engine:** `c411a1a92f5682f2a5af33871c22064311c4cb86`

## Problem

On Android/Pydroid with a newer pandas build, `merge_asof` failed because the funding timestamp column was retained as `datetime64[ms, UTC]` while the causally derived daily index close timestamp became `datetime64[us, UTC]`.

Observed error class:

`pandas.errors.MergeError: incompatible merge keys ... datetime64[ms, UTC] and datetime64[us, UTC]`

## Correction

A launcher-only compatibility shim normalizes both merge keys to `datetime64[ns, UTC]` immediately before the existing causal backward `merge_asof`.

This changes timestamp storage precision only. It does **not** change:

- venue or symbol;
- funding observations;
- index-price observations;
- timestamps or their chronological values;
- causal backward matching rule;
- `allow_exact_matches=True`;
- funding sign;
- slices, rolling windows or gates;
- crisis drawdown buckets;
- first-run snapshot cutoff;
- checkpoint data;
- any result-selection rule.

Therefore this is a technical implementation hotfix, not a strategy/protocol revision and not result chasing.

## Resume behavior

The corrected launcher uses the same persistent workspace:

`/storage/emulated/0/Download/R003_X001_BYBIT`

Existing `snapshot.json`, instrument metadata and downloaded checkpoint pages remain reusable. No restart of the historical download is required.

## Hotfix launcher

`research/r003/r003_x001_bybit_structural_replication_mobile_hotfix.py`

Commit introducing launcher: `409df6252abc50bd7fc1954f8ab86a9c4ab55dcc`.
