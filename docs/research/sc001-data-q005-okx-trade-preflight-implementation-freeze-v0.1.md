# SC001-DATA-Q005 OKX Tick-Trade Preflight — Implementation Freeze v0.1

Status: **FROZEN BEFORE RUN**

Protocol:
`docs/research/sc001-data-q005-okx-trade-preflight-v0.1.md`

Protocol commit:
`61cc27cf43a7d767af501f48ef5b9b295de4477b`

Engine:
`research/sc001/sc001_data_q005_okx_trade_preflight.py`

Engine commit:
`fdac05c8b190c731b8374765001475d5e533ab8d`

Pinned mobile launcher:
`research/sc001/sc001_data_q005_okx_trade_preflight_mobile_launcher.py`

Launcher commit:
`e06dfaa96f0906d88c276a677af056fb89ba437a`

Frozen properties:
- 2024-Q1 only: five predeclared dates;
- target `BTC-USDT-SWAP` / family `BTC-USDT` / `SWAP`;
- finite module probe set `1..5` on fixed 2024-01-05;
- metadata/HEAD only;
- trusted HTTPS `static.okx.*` URLs only;
- no archive body GET;
- no strategy feature/P&L;
- no formal Validation/Final access;
- 20 MB network/workspace caps;
- 4 GB minimum free-space reserve.

A `REDESIGN` result is acceptable and must not be rescued by expanding the module search or switching dates after seeing output. Any such expansion requires a versioned protocol change.
