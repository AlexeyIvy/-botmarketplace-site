# SC001 Current Roadmap and Stop Rules v5.159

Date: 2026-09-27
Status: **B15-P2 PARSER-RESILIENCE V0.1.1 OFFLINE SELFTEST SEALED / AWAITING EXPLICIT APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.158.md`

## Root cause and correction

The live source-only attempt exposed:

`RuntimeError: announcement publishTime missing`

The v0.1 implementation required numeric `publishTime` for every returned historical announcement row before establishing exact-symbol relevance.

The v0.1.1 implementation corrects that sequencing while preserving the causal rule that only numeric `publishTime` may establish publication timing.

No `dateTimestamp` fallback is allowed.

## Proactive hardening frozen

The v0.1.1 implementation additionally covers:

- legacy/unrelated rows without `publishTime`;
- exact in-scope missing/invalid `publishTime` -> fail-closed REVIEW;
- milliseconds plausibility checks;
- `launchTime` lower-bound protection against older listing episodes;
- post-delivery notice exclusion from causal evidence;
- robust pre-listing boolean/string normalization;
- pagination de-duplication;
- pagination without mandatory `total`;
- transient-only HTTP/network retries;
- deterministic schema/retCode failures without blind retry;
- persistent source-only REVIEW output on live exceptions.

## Exact sealed offline self-test

Bundle:

`bundle_20260927T180555Z_bc1ff4ec`

SHA256:

`5aab363e11e57dab6992292176e677542519d0a4ce31ae8be69df2ac7fd252ba`

Approval:

`BM-5AAB363E11E5`

Expected PASS:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V011_SELF_TEST_PASS`

Bundle has:
- no external inputs;
- no network;
- no real announcements;
- no real instrument census;
- no price/basis/PnL.

## Research strategy consequence

This is still an implementation/source-parser correction only.

No mechanism/economic/evidence-maturity/contamination/reusable-block state changed.

Therefore:

`NO STRATEGY REVIEW TRIGGER`

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
v0.1.1 parser-resilience self-test sealed and unrun.

## Next state

`AWAIT_EXPLICIT_APPROVAL_TO_RUN_B15P2_V011_OFFLINE_SELFTEST_BM-5AAB363E11E5`
