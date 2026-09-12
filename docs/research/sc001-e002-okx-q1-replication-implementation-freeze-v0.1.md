# SC001-E002 OKX Q1 Replication Implementation Freeze v0.1

Status: **FROZEN BEFORE RUN**

Experiment: `SC001-E002-OKX-Q1-REPLICATION`

Protocol:
`docs/research/sc001-e002-okx-q1-replication-freeze-v0.1.md`

Protocol commit:
`dccf2fd4e95996a77b980e1ca0c3ad0c5662416f`

Engine:
`research/sc001/sc001_e002_okx_q1_replication.py`

Engine commit:
`b0dbd0fabf7d0bf665282c65a71f37df97b48dbe`

Pinned Android launcher:
`research/sc001/sc001_e002_okx_q1_replication_mobile_launcher.py`

Launcher commit:
`8b068110239d92ed04ffc04e707aefc022f8e0a8`

Frozen boundaries before execution:

- five Q006R-qualified 2024-Q1 OKX UTC dates only;
- exact 5-second TFI economic mechanism;
- OKX `buy` taker side positive / `sell` taker side negative;
- 5-second non-overlapping grid/lookback/horizon;
- 100 ms primary, 250 ms stress, 500 ms diagnostic;
- 5/5 positive-day primary gate;
- 5/5 positive extreme-spread primary gate;
- >=4/5 positive-day 250 ms stress gate;
- lag diagnostics reported but not filtered;
- no threshold tuning;
- no 2024-Q2 OKX;
- no L2 execution P&L;
- no formal Validation/Final.

Any implementation change affecting feature, timing, sample, sign, gates, or filtering after result inspection requires a new experiment/version and cannot overwrite this frozen run.
