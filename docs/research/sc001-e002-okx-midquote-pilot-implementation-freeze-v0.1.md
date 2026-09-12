# SC001-E002 OKX Midquote Pilot Implementation Freeze v0.1

Status: **FROZEN BEFORE MIDQUOTE RESPONSE RUN**

Protocol:
`docs/research/sc001-e002-okx-midquote-pilot-protocol-v0.1.md`

Protocol commit:
`4408d09e9a746804cfe2f65d01c0917100196c03`

Engine:
`research/sc001/sc001_e002_okx_midquote_pilot.py`

Engine commit:
`94c77febc73601c76976da4ab71bedecc69a485a`

Pinned Android launcher:
`research/sc001/sc001_e002_okx_midquote_pilot_mobile_launcher.py`

Launcher commit:
`1111d4e5fdadf91b8bf2720692be123863c86c48`

Frozen implementation properties:
- fixed UTC date `2024-01-05`;
- exact existing E002 OKX 5-second TFI;
- 5-second decision grid and horizon;
- latency tuple 100/250/500 ms;
- L2 midquote = `(best_bid + best_ask)/2`;
- causal as-of sampling: last valid L2 state with timestamp <= target;
- known decision-count integrity reference `17109`;
- primary pilot verdict uses 100ms Spearman sign + extreme-decile spread sign only;
- book-state age is reported but cannot be used post hoc to filter observations;
- no bid/ask execution P&L, fees, depth consumption, capital sizing, Q2 OKX, formal Validation or Final.

Any material change after the pilot is opened requires a new experiment/version and cannot overwrite this frozen run.
