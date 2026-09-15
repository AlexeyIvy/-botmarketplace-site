# SC001-E007 — Implementation Preflight Specification v1.0

Date: 2026-09-15  
Status: **FROZEN BEFORE FIRST E007 ALPHA**

Parent protocol: `docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md`

## 1. Purpose

Prove that the implementation exactly reproduces E007 v1.0 causal/event/execution semantics without reading or emitting E007 real-data displacement, response or P&L.

Only exact `E007_PREFLIGHT_PASS` with matching engine/config SHA256 may open one DEV-DISCOVERY run.

## 2. Real-data output firewall

During preflight, real March data may be used only for source identity, chronology, timestamp/bucket availability, memory/disk and state-machine input feasibility.

Forbidden real-data outputs/calculations during preflight:

- real 5-second VWAP values;
- real 60-second displacement values;
- event threshold crossings;
- real entry/exit prices;
- real E007 returns/P&L;
- any comparison revealing whether reversal is profitable.

Synthetic fixtures may calculate prices/displacements because their outcomes are hand-constructed.

## 3. Frozen implementation resolutions

### 3.1 5-second grid indexing

A VWAP bucket indexed `k` covers `[start + k*5s, start + (k+1)*5s)` and is known only at its right boundary.

For current bucket `k`, anchor bucket is exactly `k-12`, yielding `[t-65s,t-60s)` versus `[t-5s,t)`.

### 3.2 Trigger chronology across midnight

Displacement validity/crossing state is chronological and may carry across UTC midnight. Trading state and daily decision count reset at midnight. Resetting trading state must not manufacture a fresh threshold crossing.

### 3.3 Already-reverted entry

If a valid execution proxy exists but its raw trade price is already at or beyond the frozen 50% retracement target in the reversal direction, no position is opened. Event status is `entry_already_reverted`; it counts toward the daily decision cap and starts a 10-minute cooldown from that observed proxy timestamp.

### 3.4 Missing entry

If no entry proxy exists within the inclusive 5,000 ms tolerance, event is incomplete; it counts toward daily cap and cooldown begins at `entry_target + 5,000 ms`.

### 3.5 Exit grid ceiling

Maximum-hold decision timestamp is the first 5-second UTC grid boundary at or after `actual_entry_ts + 600,000 ms`.

Causal target checks start at the first 5-second boundary strictly after actual entry.

### 3.6 Exit proxy failure

If an opened position has no valid exit proxy within tolerance or the proxy would cross UTC midnight, the event is incomplete and the UTC day is locked against further entries.

### 3.7 Stress replay

1,000/2,000 ms stresses reuse exactly the primary accepted trigger events, frozen anchor/current/target, direction and primary exit-decision timestamp.

They do not discover new triggers or change target/hold. If stress entry occurs after the frozen exit-decision timestamp or after the raw proxy has already reached the target, that stress event is incomplete.

## 4. Synthetic tests

At minimum assert:

1. current window excludes trade exactly at `t`;
2. includes trade at `t-1 ms`;
3. 5-second VWAP is size-weighted;
4. anchor bucket offset is exactly 12 buckets;
5. displacement formula/sign;
6. invalid current/anchor blocks event;
7. previous invalid observation blocks crossing;
8. `79.999 -> 80.000` qualifies;
9. `80 -> 81` does not retrigger;
10. negative threshold creates LONG reversal;
11. positive threshold creates SHORT reversal;
12. 50% target arithmetic is exact;
13. frozen target does not roll;
14. 500 ms proxy selects first trade at/after target time;
15. 5,000 ms tolerance is inclusive;
16. 5,001 ms is rejected;
17. already-reverted entry is not opened;
18. convergence target equality qualifies;
19. convergence check uses first valid grid strictly after actual entry;
20. 10-minute time exit uses grid ceiling;
21. convergence wins if it occurs before time exit;
22. no exit proxy locks the day;
23. cooldown is exactly 10 minutes and half-open;
24. fifth daily decision is blocked;
25. no overlap/concurrency >1;
26. no new decision after 23:49 UTC;
27. gross LONG sign formula;
28. gross SHORT sign formula;
29. stress replay does not discover new triggers;
30. stress entry after frozen exit decision is incomplete;
31. price-scale invariance;
32. future rows cannot change an earlier VWAP/displacement/trigger;
33. Confirmation is fail-closed without exact Discovery PASS token;
34. auxiliary-feature/L2/Q2/Validation/Final firewalls are false.

## 5. Real-data no-alpha dry run

Using qualified March SWAP archives only:

- verify required archive identities/SHA/CRC/schema/order;
- reconstruct Discovery input interval causally;
- record 5-second bucket-presence counts only, not VWAP values;
- record count/share where both the current and anchor 5-second buckets are non-empty;
- first structurally eligible grid must be no earlier than 65 seconds after the loaded start;
- verify all target UTC minutes are represented;
- verify required labels stop at 2024-03-21;
- no E007 trigger/displacement/return calculation.

Structural counts may not be used to retune the frozen protocol.

## 6. Resource gates

On qualified VPS:

- peak RSS < 6 GiB;
- free disk >= 10 GiB reserve;
- malformed/missing/hash-mismatch/invariant breach => FAIL;
- no overwrite of an existing completed Discovery output directory.

## 7. Confirmation gates frozen before Discovery

Confirmation performance interval: 2024-03-22..30, with March 21 warm-up/boundary-only.

Frozen Confirmation gates:

- completed trades: 10..36;
- active days >=5;
- completion rate >=0.95;
- mean >=30 bps;
- 10% trimmed mean >=25 bps;
- median >=20 bps;
- median active-day mean >=25 bps;
- positive active-day share >=0.67;
- day-block bootstrap 95% LCB >15 bps;
- top-1 absolute day contribution <=0.35;
- top-3 <=0.70;
- each reversal sign >=2 completed trades;
- max one-sign share <=0.85;
- 1,000 ms mean >=25 bps and trimmed >=20 bps;
- 2,000 ms mean >=20 bps and trimmed >=15 bps;
- max decisions/day <=4;
- max concurrent positions <=1.

## 8. PASS

`E007_PREFLIGHT_PASS` requires all synthetic tests, real-data no-alpha checks, hashes, firewalls, invariants and resource gates to PASS.

Any failure gives `E007_PREFLIGHT_FAIL`; Discovery remains blocked.
