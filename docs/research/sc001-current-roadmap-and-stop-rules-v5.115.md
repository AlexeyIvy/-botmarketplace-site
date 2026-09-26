# SC001 Current Roadmap and Stop Rules v5.115

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / parallel B14-A P0 frozen prospective readout prepared**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.114.md`

## B15-P1 remains unchanged

Primary collector state remains:

`B15P1_COLLECTOR_V014_OPERATIONAL_FREEZE`

W1 observation window continues to accumulate independently. Do not restart or retune B15-P1.

## Parallel active research: B14-A P0

B14-A P0 is eligible for post-event readout because its outcome rule was frozen before the 2026-09-25 expiry event.

Frozen event:
- expiry = 2026-09-25T08:00:00Z;
- T0 = 2026-09-25T07:30:00Z;
- BTC pair = BTC-USD-260925 vs BTC-USD-SWAP;
- ETH pair = ETH-USD-260925 vs ETH-USD-SWAP;
- representation = STRICT_COACTIVE_1S_NO_CARRY_FORWARD;
- search only the five frozen one-second buckets beginning at T0;
- use the chronologically last captured real trade on each leg in the earliest coactive bucket;
- headroom hurdle = 50 bps.

No rule may be changed from the observed result.

## B14-A readout implementation

Analyzer:

`research/sc001/sc001_b14a_p0_headroom_readout_v0_1.py`

SHA256:

`919c0d75e3459c0039f63915fd55347eb09590d22b29a10d4070bdcad5622279`

Contract:

`docs/research/sc001-b14a-p0-headroom-readout-contract-v0.1.json`

Offline self-test spec:

`docs/research/sc001-b14a-p0-headroom-readout-offline-selftest-spec-v0.1.json`

## Fail-closed data validity

Before basis is calculated:
- collector state must be COMPLETE;
- subscription ACK must be true;
- collector basis/convergence/PnL flags must remain false;
- no connection gap may intersect [T0-1s, T0+6s];
- no process-restart gap may intersect [T0-1s, T0+6s].

If the state/gap gate fails, outcome calculation is suppressed and result is DEFER_DATA.

Each family also requires at least one frozen one-second bucket with a real trade on both FUTURES and SWAP legs.

## Allowed classifications

- B14A_P0_STRONG_HEADROOM_2_OF_2
- B14A_P0_MIXED_HEADROOM_1_OF_2
- B14A_P0_WEAK_HEADROOM_0_OF_2
- B14A_P0_DEFER_DATA

This P0 readout is not Confirmation and does not authorize PnL.

## Stop rules

Do not:
- move T0;
- widen the five-second search;
- use carry-forward/interpolation;
- search other expiries after seeing the result;
- lower the 50 bps hurdle;
- calculate convergence, settlePx alpha, execution PnL, or promotional claims.

## Next state

`SEAL_B14A_P0_READOUT_OFFLINE_SELFTEST_BUNDLE`
