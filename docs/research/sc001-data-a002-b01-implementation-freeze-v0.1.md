# SC001-DATA-A002-B01 — Implementation freeze v0.1

This note freezes the executable identities for the first DEV aggTrades batch.

- Protocol: `docs/research/sc001-data-a002-b01-protocol-v0.1.md`, commit `74866fa1d0f5176104a07c649d9b7e4a4d3d65cb`.
- Engine: `research/sc001/sc001_data_a002_b01_2023q2.py`, commit `7c72f2c27d41c4a546bc87369671bda33e6ab7c5`.
- Mobile launcher: `research/sc001/sc001_data_a002_b01_mobile_launcher.py`, commit `8077c9355b8eb030e8c0289bd6d45680954edbc1`.

Pre-execution review completed before user run:
- Python syntax compilation passed locally for the frozen engine logic.
- Synthetic 1,440-minute aggTrades ZIP test passed the validator with contiguous aggregate IDs, contiguous underlying trade ranges, both maker flags and exact UTC-minute coverage.
- Engine is restartable and reuses a local archive only after exact frozen size + SHA256 verification.
- It re-reads the A002-PREFLIGHT report and refuses to run if the frozen calendar SHA, 25/25 preflight status, five B01 dates, sizes or checksums do not match.
- Live checksum and Content-Length are checked again immediately before each download; remote mutation causes STOP/ERROR rather than silent acceptance.
- ZIP contents are streamed from compressed archives; raw CSV is not extracted to disk.
- Decimal is used for price/quantity validity checks; no floating-point validation is used.
- Mandatory data-quality gates are fixed before the run. Underlying trade-ID gaps are diagnostic only; overlaps/backward ranges are failures.
- Strategy features, P&L and VALIDATION/FINAL access are explicitly disabled by scope.

No gate is to be loosened after seeing B01 results. Any genuine implementation defect requires a separately documented revision rather than reinterpretation of the frozen run.