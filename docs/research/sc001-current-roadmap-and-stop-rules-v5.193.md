# SC001 Current Roadmap and Stop Rules v5.193

Date: 2026-09-28
Status: **B15-P2 HYDRATION SMOKE PASS / POST-SMOKE LAUNCHER FAILURE DIAGNOSED / RECOVERY V0.4.1 READY**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.192.md`

## Hydration extractor is validated

The v0.1.5 DOGUSDT/TONUSDT hydration smoke passed.

Both events:
- used the frozen title path;
- used `articleDetail.content.json.children` as primary body;
- produced 858 normalized primary-body characters;
- produced 9 text leaves;
- had the secondary CMS duplicate present;
- had primary/secondary normalized body SHA256 equality.

No semantic classification was performed by the smoke.

## Full 94-event audit did not start

The runtime snapshot showed:
- smoke: present;
- persistent log: smoke only;
- launch marker: absent;
- terminal result: absent;
- exit code: absent.

Therefore the v0.4 wrapper stopped after smoke and before a confirmed systemd launch.

Canonical diagnostic:

`docs/research/sc001-b15p2-semantic-v04-post-smoke-launch-failure-diagnostic-v0.1.json`

## Root cause

The wrapper generated its live helper with an unquoted heredoc.

Helper-local shell variables were expanded in the parent wrapper while the helper file was being created. Under `set -u`, undefined helper-local variables caused the parent wrapper to abort.

This is a host-launcher bug only.

It does not invalidate:
- frozen events;
- curl transport;
- hydration body selection;
- v0.1.5 semantic implementation;
- DOG/TON smoke PASS.

## Recovery architecture

Dynamic helper generation is removed.

Static helper:

`scripts/research/run-b15p2-semantic-live-helper-v0.1.sh`

SHA256:

`ce3d20648a6c835295ae3c2e49d1d5f22a9f12860ccaaf5cf363d7fb68317ca1`

Recovery wrapper:

`scripts/research/run-b15p2-announcement-body-semantic-audit-v0.4.1.sh`

SHA256:

`1ebadef385e4636bbb9adc990b8d467a8ed8deb6074e5ca5f58e5a7020cf6470`

Recovery contract:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-networked-launch-contract-v0.4.1.json`

## Recovery execution

v0.4.1 will:

1. validate the same frozen contracts;
2. validate and preserve the previous smoke PASS;
3. recreate exact read-only stage;
4. rerun v0.1.5 offline self-test;
5. run a fresh DOG/TON hydration smoke;
6. validate smoke;
7. install the exact static helper read-only;
8. start the 94-event semantic audit through systemd;
9. write a recovery-specific marker/log/exit code;
10. publish structured progress on every `--status`.

## Progress handoff

`--status` now writes:

`docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-progress.json`

Therefore the normal user workflow is:

- run recovery `--launch`;
- later run recovery `--status`;
- tell ChatGPT “готово”.

No multi-screen terminal capture is required.

## Iteration budget

Recovery iteration **1 / 5 is prepared but not yet consumed**.

It becomes consumed only when v0.4.1 is actually re-executed.

## Firewalls

Still closed:
- price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Next state

`RUN_RECOVERY_ITERATION_1_B15P2_SEMANTIC_V041`
