# SC001-DATA-Q006R Implementation Freeze v0.1

Status: **FROZEN BEFORE Q006R RUN**

Protocol:
`docs/research/sc001-data-q006r-utc-stitch-protocol-v0.1.md`

Protocol commit:
`12f6541067c08d94cede1ba17a714636265c0935`

Engine:
`research/sc001/sc001_data_q006r_okx_utc_stitch.py`

Engine commit:
`f1e7bf4071b63ad466f490d09d990afc3e01fc34`

Pinned mobile launcher:
`research/sc001/sc001_data_q006r_mobile_launcher.py`

Launcher commit:
`016a2e2c91eb4e8cd2e4af29f2c066d589295993`

## Frozen behavior

- five unchanged 2024-Q1 UTC target dates;
- OKX `BTC-USDT-SWAP` trade module `1` only;
- explicit observed CSV mapping including `created_time` and `instrument_name`;
- reuse and SHA-verify Q006 exact-date archives;
- discover/download only exact `D+1` neighbor archive for each target day;
- reconstruct UTC day by filtering union of `D` and `D+1` archives to `[D,D+1)` UTC;
- full source timestamp-range diagnostics;
- 1,440 UTC minute-bucket gate;
- no TFI, future returns, P&L, 2024-Q2 OKX, Validation, or Final.

No implementation edit is allowed after Q006R output is seen under this version. Any material repair requires a separately versioned stage.
