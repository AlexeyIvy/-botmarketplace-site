# SC001 Current Roadmap and Stop Rules v5.91

Date: 2026-09-25  
Status: **B15-P1 COLLECTOR v0.1.4 OFFLINE PASS / v0.1.4-BOUND CAPABILITY REVALIDATION NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.90.md`

## v0.1.4 offline result

Bundle:

`bundle_20260925T185135Z_6c28a359`

Job:

`job_20260925T191249Z_2ab861e9`

Result:

`B15P1_NONPRICE_COLLECTOR_V014_COMPILE_AND_SELFTEST_PASS`

Runner self-test:

`B15P1_NONPRICE_COLLECTOR_V014_SELF_TEST_PASS`

Package integrity = true.  
Exit code = 0.

Compile manifest SHA256:

`af676061a954e8ee0328f96ed15ee06d5be925a595559a172a0c6283dd3a642b`

Self-test manifest SHA256:

`3822334fa2faad8eec3fb8a963c5ba26ee03d1ba2c77a9beeb2b213364f88b37`

## Verified v0.1.4 anchors

- runner SHA256:
  `280253b060f65517548054b3d8c33c315013d724ef2b836e9b8fef14628be213`
- library SHA256:
  `eaa925b71a7f33ec59de69f32dd0fb06f85bac67e89101b6f2ad50c1d792fd3f`
- implementation freeze SHA256:
  `80928b0a11dac333b7844aa15bcdf399fd4db8739a4845e6118ebb576153b38c`
- service SHA256:
  `7a0f1742481b92f4d2590f09defcc5b287baaf1a9ba50f0da27488f8f5272f9d`

## Mandatory offline test result

All 32 mandatory tests passed.

New v0.1.4 tests PASS:
- BYBIT_WITHDRAW_MAX_UNLIMITED_SENTINEL;
- BYBIT_WITHDRAW_MAX_OTHER_NEGATIVE_FAIL_CLOSED;
- BYBIT_NONMAX_NEGATIVE_FAIL_CLOSED;
- BYBIT_MAX_WITHDRAW_TRANSITION_FIXTURE.

The generic decimal parser remains strict.

Only Bybit `withdrawMax=-1` is normalized to:

`UNLIMITED`

All other unsupported negative values remain fail-closed.

## Existing protected semantics remain PASS

- frozen identity/mapping counts PASS;
- route-state machine PASS;
- source-gap fixtures PASS;
- fee staleness PASS;
- storage pressure PASS;
- raw-object integrity PASS;
- append-only/state atomicity PASS;
- secret redaction PASS;
- launch authorization fail-closed PASS;
- poll hash-chain tamper PASS;
- systemd candidate guard PASS;
- no-price endpoint guard PASS;
- OKX current-schema compatibility fixtures PASS.

## Safety

During this gate:
- credentials unavailable;
- exchange calls = false;
- collector launch = false;
- price data = false;
- PnL = false;
- live execution = false.

## Next gate

The old live capability snapshot is anchored to v0.1.3 and MUST NOT be reused.

Prepare a new read-only capability revalidation bound exactly to:
- v0.1.4 runner SHA;
- v0.1.4 implementation freeze SHA;
- v0.1.4 service SHA;
- existing frozen route graph.

The revalidation must specifically prove the real Bybit Get Coin Info response now parses successfully with the `withdrawMax=-1` sentinel handling.

Do not relaunch the collector before that new capability PASS.

## Next state

`PREPARE_V014_BOUND_READ_ONLY_CAPABILITY_REVALIDATION`
