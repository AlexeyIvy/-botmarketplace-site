# SC001 / B15-P1 — dialog handoff v6.24 — 2026-09-24

Current state:

`B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_SEALED_AWAITING_APPROVAL`

## Live capability checkpoint

Live authenticated source capability v0.2.1 PASS is frozen.

Snapshot SHA256:

`14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`

Coverage:
- Bybit 192/192;
- OKX 192/192;
- both venues 192/192.

Security:
- read-only credentials;
- Withdraw absent on Bybit;
- IP-bound keys;
- price/order/transfer/withdraw endpoints not called;
- collector launch false;
- price/PnL false.

## Prelaunch gate prepared

New files:
- `docs/research/sc001-b15-p1-collector-launch-authorization-candidate-v0.1.json`
- `docs/research/sc001-b15-p1-collector-prelaunch-readiness-spec-v0.1.json`
- `docs/research/sc001-b15-p1-collector-prelaunch-readiness-freeze-v0.1.json`
- `research/sc001/sc001_b15p1_collector_prelaunch_readiness_v0_1.py`

Preparation commit:

`8d48584eb8c4ec3dd67083a0111dccf4e36dad26`

The authorization candidate is intentionally non-active:
- top-level status = `CANDIDATE_NOT_ACTIVE`;
- runtime_install_authorized = false;
- collector_start_authorized = false.

The proposed runtime payload is tested only inside the offline gate against the collector's exact validator.

## Sealed bundle

- bundle ID: `bundle_20260924T180410Z_997301cb`
- bundle SHA256: `e287545e7911aa160a12b0c0df89d84fb2f00fe15961704785e92291c3ebd370`
- approval code: `BM-E287545E7911`
- files: 26
- bytes: 322419
- runtime: `offline-research-v1`
- inputs: none

The bundle has NOT been run.

## Next

After explicit user approval, run exactly the sealed offline prelaunch gate.

Only if it returns:

`B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS`

prepare a separate host systemd deployment-readiness wrapper.

Do not start or enable the collector automatically.

Do not create the runtime launch authorization automatically.
