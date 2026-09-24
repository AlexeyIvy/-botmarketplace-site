# SC001 / B15-P1 — dialog handoff v6.22 — 2026-09-24

Current state:

`B15P1_LIVE_READ_ONLY_CAPABILITY_REVALIDATION_V021_READY_AWAITING_APPROVAL`

## Combined offline gate

PASS:
- bundle `bundle_20260924T163807Z_a5599568`
- job `job_20260924T170906Z_810905df`
- collector v0.1.3: 28/28 mandatory + 8/8 extra PASS
- capability v0.2.1: compile+self-test PASS

## Live-wrapper offline preflight

PASS:
- bundle `bundle_20260924T171540Z_9f83d965`
- job `job_20260924T172500Z_45b04565`
- manifest SHA256 `192df55653161fe88d27e49eed03b7238dc617917f2074407e659a8a8ff66f70`

Verified:
- bash syntax;
- two embedded Python blocks compile;
- 10/10 staged dependency SHA pins;
- one and only one `--mode run`;
- no direct curl/wget/nc/socat/URL command;
- no systemd service mutation;
- no launch-authorization creation;
- no GitHub Control permission mutation;
- staging delete scoped only to staging root.

No credentials or exchange calls occurred in this preflight.

## Live wrapper candidate

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

SHA256:

`0bc379933be07fb7b31e2efe4a2f06b4b7b99ad2fdc4db403dbffbe63ebc556e`

This wrapper is ready for the separate authenticated read-only capability retry.

It must not be run without explicit user approval.

Even after live PASS:
- do not start collector automatically;
- do not create launch authorization automatically;
- do not enable price/PnL or live trading;
- collector launch remains a separate gate.

## Next

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P1_LIVE_READ_ONLY_CAPABILITY_REVALIDATION_V021`
