# SC001 Current Roadmap and Stop Rules v5.90

Date: 2026-09-25  
Status: **B15-P1 BYBIT withdrawMax SENTINEL ROOT CAUSE CONFIRMED / COLLECTOR v0.1.4 OFFLINE SELFTEST SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.89.md`

## Source-invalid diagnosis

Saved evidence from the v0.1.1 launch attempt showed:

- total polls = 10;
- invalid polls = 10;
- valid polls = 0;
- Bybit HTTP 200 = 10/10;
- Bybit SOURCE_INVALID = 10/10;
- Bybit exact parser error:
  `ValueError: invalid nonnegative decimal '-1'`;
- OKX OK = 8/10;
- OKX request deadline exceeded = 2/10.

Thus the primary blocker is Bybit parser compatibility, not credentials or HTTP transport.

## Confirmed Bybit semantics

Bybit Get Coin Info documents:

`withdrawMax = "-1"`

as:

`NO LIMIT`

The old v0.1.3 parser passed `withdrawMax` through the generic nonnegative-decimal parser and therefore rejected a legal source value.

## Collector v0.1.4 correction

Generic `decimal_text()` is unchanged.

New field-specific helper:

`bybit_withdraw_max_text()`

Rules:
- `withdrawMax == -1` -> `UNLIMITED`;
- other negative withdrawMax -> fail closed;
- negative withdrawFee -> fail closed;
- negative withdrawMin -> fail closed;
- negative depositMin -> fail closed.

The existing `MAX_WITHDRAW_CHANGED` event remains usable for:

`UNLIMITED <-> finite value`

Route-state logic is unchanged.

Fast cadence remains 15 seconds.
Request deadline remains 12 seconds.
Price/PnL remain closed.

## v0.1.4 anchors

- runner SHA256:
  `280253b060f65517548054b3d8c33c315013d724ef2b836e9b8fef14628be213`
- library SHA256:
  `eaa925b71a7f33ec59de69f32dd0fb06f85bac67e89101b6f2ad50c1d792fd3f`
- service SHA256:
  `7a0f1742481b92f4d2590f09defcc5b287baaf1a9ba50f0da27488f8f5272f9d`
- implementation freeze SHA256:
  `80928b0a11dac333b7844aa15bcdf399fd4db8739a4845e6118ebb576153b38c`
- contract mandatory tests = 32.

New mandatory fixtures:
- BYBIT_WITHDRAW_MAX_UNLIMITED_SENTINEL;
- BYBIT_WITHDRAW_MAX_OTHER_NEGATIVE_FAIL_CLOSED;
- BYBIT_NONMAX_NEGATIVE_FAIL_CLOSED;
- BYBIT_MAX_WITHDRAW_TRANSITION_FIXTURE.

## OKX note

The 2/10 OKX request-deadline polls are not currently the primary blocker.

Because OKX already produced 8/10 valid polls, no cadence/deadline change is authorized at this stage.

Changing request timing now would mix two separate failure classes and alter the frozen collection design unnecessarily.

## Capability binding rule

The previous live capability snapshot was anchored to collector v0.1.3 hashes.

It must NOT be reused for v0.1.4 runtime launch.

After v0.1.4 offline PASS, prepare a new read-only capability revalidation bound to the v0.1.4 runner/freeze/service hashes.

## Sealed offline self-test bundle

- bundle ID: `bundle_20260925T185135Z_6c28a359`
- SHA256: `cec279cbdb2768003f35ae9d1388d883caff6e3b8472ed4d6fc09bc8b3242e17`
- approval code: `BM-CEC279CBDB27`
- files: 23
- bytes: 297879
- runtime: `offline-research-v1`
- inputs: none

This bundle has NOT been run.

## Stop rule

Do not retry collector launch yet.

Run v0.1.4 offline compile+self-test first.

Only after PASS prepare the v0.1.4-bound capability revalidation.

## Next state

`RUN_B15P1_NONPRICE_COLLECTOR_V014_OFFLINE_SELFTEST_AFTER_USER_APPROVAL`
