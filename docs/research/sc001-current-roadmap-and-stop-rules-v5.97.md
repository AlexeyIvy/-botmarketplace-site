# SC001 Current Roadmap and Stop Rules v5.97

Date: 2026-09-26  
Status: **B15-P1 recovery v0.1.2 offline preflight sealed / awaiting approval**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.96.md`

## v0.1.1 host failure diagnosis

Recovery v0.1.1 was run twice on VPS and stopped before archive mutation.

Observed:
- embedded Python line 112;
- AssertionError;
- no evidence archive started.

Exact failing assertion:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V022_PASS in cap_log`

Root cause:

`source_capability_revalidation_v0.2.2_run.log` is produced by `tee` only around the live capability probe process.

The following tokens are printed later by the outer live wrapper and therefore are not present in that log:
- `B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V022_PASS`;
- `security_firewall = PASS`;
- final wrapper-level `...=False` lines.

Thus v0.1.1 required an impossible log contract.

All snapshot/safe-summary semantic assertions preceding line 112 passed, so this was not a capability or parser failure.

## Recovery v0.1.2 correction

New wrapper:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.2.sh`

SHA256:

`04d6f49a38882e94928ae7fef0b1068670dfb536361cd72c77659aefc17bac20`

The v0.2.2 snapshot/safe-summary semantic contract remains unchanged.

The run-log check now requires only probe-level tokens that are actually inside `tee` output:
- `B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`;
- no probe REVIEW token;
- `Bybit parser v0.1.4 compatible = True`;
- `price endpoints called = False`;
- `order/transfer/withdraw endpoints called = False`;
- `collector_launch_authorized = False`.

Wrapper-level PASS is proven by the validated snapshot and safe-summary, not by the probe log.

## v0.1.2 offline-preflight hardening

Dynamic fixtures include:
- valid semantic snapshot A with generated SHA A;
- valid semantic snapshot B with different generated SHA B;
- mismatched safe-summary snapshot SHA -> fail closed;
- realistic probe-only tee log -> PASS;
- same probe log without probe PASS token -> fail closed.

Static regression guards explicitly reject reintroduction of:
- wrapper-level COMMAND_V022_PASS assertion inside probe log;
- wrapper-level security_firewall assertion inside probe log.

The preflight harness also validates the entire freeze-chain:
wrapper, harness, bootstrap, spec and v0.1.1 failure diagnostic SHA values.

## Sealed bundle

- bundle ID: `bundle_20260926T115009Z_9a599660`
- SHA256: `6ec32292acaccf905cc25c0dc6f15e126cb1067fc5463e9257ab7f0f82c8c707`
- approval code: `BM-6EC32292ACAC`
- files: 6
- bytes: 40164
- runtime: offline-research-v1
- inputs: none

The bundle has NOT been run.

## Stop rule

Do not run recovery v0.1 or v0.1.1.

Do not relaunch collector.

Run only the v0.1.2 offline preflight after explicit Runner approval.

## Next state

`RUN_RECOVERY_V012_OFFLINE_PREFLIGHT_AFTER_EXPLICIT_APPROVAL`
