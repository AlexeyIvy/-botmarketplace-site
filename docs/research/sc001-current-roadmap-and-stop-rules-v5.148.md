# SC001 Current Roadmap and Stop Rules v5.148

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A P0 DEFER_DATA / B13-C S0 terminal REJECT with RB021 retained / B14-B self-test PASS, fresh funding screen awaiting approval**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.147.md`

## B14-B offline validation

Runner job:

`job_20260927T092950Z_3f4b8e6f`

PASS:

`B14B_PERSISTENT_CARRY_V01_SELF_TEST_PASS`

Observed:
- exit code = 0;
- package integrity = PASS;
- stderr empty;
- network calls = none;
- fresh 2026 funding values = unopened;
- price/basis/PnL = CLOSED.

## Next boundary

Binding networked launch contract:

`docs/research/sc001-b14b-networked-fresh-funding-screen-launch-contract-v0.1.json`

Exact script SHA:

`cb288810ef8871ea1de3bfe9decf6e372cb525c1c62d0123969d4f7f459793f4`

Frozen fresh window:

`2026-07-01T00:00:00Z .. 2026-09-27T00:00:00Z`

The run will access only public OKX/Bybit funding histories and apply the already frozen 3-confirmation / 7-day / non-overlap architecture.

It will not access price, basis, trade bodies, L2 or calculate price PnL.

## Reusable-block requirement

If B14-B terminates as REJECT or DEFER, reusable-block extraction is mandatory under:

`docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_NETWORKED_B14B_FRESH_FUNDING_SCREEN`
