# SC001 / B15-P1 — dialog handoff v6.12 — 2026-09-24

Latest state:

`B15_P1_15_SECOND_NONPRICE_COLLECTOR_DESIGN_PREFLIGHT_PASS`

The collector has not been launched.

## Design-preflight provenance

- bundle: `bundle_20260924T101653Z_04b3927c`
- SHA256: `abd2de854537e8d886e472a46fcf5bb97eee0c4407b15cf406e3733b54a154d0`
- job: `job_20260924T103023Z_d7063dd4`
- manifest SHA256: `5066d1e91e6b8e122ef1289a35b1747f18a2e68cc3692d8e4c999692db8a03a9`
- failed_checks = []

## Verified operational design

- 15s fast cadence;
- 12s request deadline;
- no catch-up / no overlap;
- 75x Bybit / 90x OKX fast-lane rate-limit margin;
- 6h fee refresh;
- 8h fee staleness limit;
- <=30s heartbeat;
- systemd before launch;
- restart-gap accounting;
- storage pressure fail-closed;
- append-only evidence + poll hash chain;
- one-sided quote routes excluded;
- no prices / PnL / live execution.

## Next state

`PREPARE_B15P1_COLLECTOR_IMPLEMENTATION_SELF_TEST`

Implementation contract candidate SHA256:

`150044900060297ba775c51d780ea466ac56c5245332a4ed3cb5e118c736df9e`

Collector launch remains unauthorized.
