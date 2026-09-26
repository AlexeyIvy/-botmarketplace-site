# SC001 / B15-P1 — dialog handoff v6.43 — 2026-09-26

Current state:

`B15P1_ROLLING_SNAPSHOT_SAFE_RECOVERY_V011_PREFLIGHT_SEALED`

The user reran capability v0.2.2 instead of recovery. The capability run passed, but regenerated the snapshot and therefore changed its full-file SHA.

This is not a capability failure.

Recovery was hardened to v0.1.1 so it validates the current v0.2.2 snapshot semantically and then requires pre/post SHA identity instead of relying on one pre-known snapshot SHA.

Recovery v0.1.1 wrapper SHA:

`2a14da8e599feb0f2e075144bd64b269de44c916715790152e71ae5cc67eb2a7`

Sealed offline-preflight bundle:

- ID: `bundle_20260926T101521Z_09b874f8`
- SHA256: `c6aed1d393ed470a18c674e45ae9ad5b36ad612cde5a140d99f475fe80bebe72`
- approval code: `BM-C6AED1D393ED`

Not run yet.

After PASS, the next user-visible action will be the v0.1.1 recovery command on VPS.
