# SC001-DATA-Q008 — Implementation Freeze v0.1

Status: **FROZEN BEFORE FULL L2 DOWNLOAD**

Purpose: one complete-day OKX `BTC-USDT-SWAP` 400-level L2 engineering/replay pilot on the fixed date `2024-01-05`.

Frozen artifacts:

- protocol: `docs/research/sc001-data-q008-okx-l2-full-day-pilot-protocol-v0.1.md`
  - commit: `ada4a6d2ef95fca1bb40f37553d6d630afa00579`
- engine: `research/sc001/sc001_data_q008_okx_l2_full_day_pilot.py`
  - commit: `d4aa9720e43a39e215af7d866bd273c68340381c`
- pinned Android/Pydroid launcher: `research/sc001/sc001_data_q008_mobile_launcher.py`
  - commit: `458178c99f94c55e1d488d9fe189beeeb8a9986f`

Frozen archive identity:

- date: `2024-01-05`
- filename: `BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz`
- bytes: `500060536`

Frozen safety:

- session download cap: 700,000,000 bytes;
- workspace cap: 700,000,000 bytes;
- per-file cap: 650,000,000 bytes;
- free-space reserve: 4,000,000,000 bytes;
- streamed tar/gzip replay only; no expanded L2 member written to disk;
- resumable `.part` transfer is allowed after interruption.

Frozen research firewall:

- strategy features: NO;
- midquote response: NO;
- strategy P&L: NO;
- execution profitability: NO;
- Q2 OKX: NO;
- formal Validation/Final: NO.

No implementation or gate may be changed after observing Q008 output under the same stage ID. A correction must receive a separately versioned repair stage.
