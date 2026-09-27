# SC001 Current Roadmap and Stop Rules v5.157

Date: 2026-09-27
Status: **B15-P2 NETWORKED SOURCE-ONLY V0.1 TECHNICAL FAILURE / V0.1.1 OBSERVABILITY RETRY FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.156.md`

## Binding governance

`docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`

remains binding.

No research-methodology change is introduced here.

## B15-P2 v0.1 networked attempt

The approved source-only host wrapper reached the live transient systemd unit after:
- canonical offline prerequisite PASS;
- staged synthetic self-test PASS.

The transient unit then exited with code 2 after approximately six seconds.

Observed systemd state:

`failed / exit-code / status=2`

No source-feasibility verdict was recovered.

Canonical diagnostic:

`docs/research/sc001-b15p2-networked-source-census-v0.1-host-failure-diagnostic.json`

### Observability defect

The v0.1 wrapper redirected the underlying Python exception to a dedicated log but deleted that log when `systemd-run` returned nonzero.

Therefore the available journal contains only the generic child exit status.

This is a host-wrapper observability failure, not an economic or source-feasibility result.

## Research firewalls remain intact

No authorization was granted for price, external-reference price, index, basis, spread, returns, PnL, event ranking or trading.

No strategy outcome was observed.

Therefore:

`NO STRATEGY REVIEW TRIGGER`

## V0.1.1 retry boundary

Research implementation and protocol remain byte-identical.

Only the host wrapper changes.

New wrapper:

`scripts/research/run-b15p2-bybit-delisting-source-census-v0.1.1.sh`

SHA256:

`d15db20c2f9a732ec886138b5e80edaca8b179c64b2f74f99d0b90c4816d1f95`

New launch contract:

`docs/research/sc001-b15p2-networked-bybit-source-only-event-census-launch-contract-v0.1.1.json`

Approval code:

`BM-D15DB20C2F9A`

The v0.1.1 wrapper:
- uses distinct versioned attempt paths;
- preserves log, exit code and launch marker on failure;
- mirrors Python stdout/stderr to persistent log and journal;
- automatically emits status/log tail after unit failure;
- keeps existing one-shot/fail-closed semantics.

Networked retry is NOT authorized by this roadmap update.

## Timing clue

The approximately six-second v0.1 runtime is consistent with four immediately failing request attempts plus retry sleeps of 1 + 2 + 3 seconds.

This makes the first Bybit public request a leading diagnostic hypothesis only.

It is NOT treated as the root cause until v0.1.1 preserves the actual exception.

## Current branch states

B15-P1:
W1 accumulation / operational freeze unchanged.

B14-A:
`B14A_P0_DEFER_DATA` retained.

B13-C:
terminal S0 / RB021 retained; no same-evidence rescue.

B14-B:
terminal / RB022 retained; no same-window rescue.

B15-P2:
source-only research remains active; v0.1 networked attempt is technical REVIEW only; v0.1.1 exact retry boundary is frozen and unrun.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_NETWORKED_SOURCE_ONLY_RETRY_BM-D15DB20C2F9A`
