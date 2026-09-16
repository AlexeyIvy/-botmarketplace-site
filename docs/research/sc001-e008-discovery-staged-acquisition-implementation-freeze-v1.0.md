# SC001-E008 — Discovery Staged Acquisition Implementation Freeze v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE FIRST PROMOTIONAL BODY DOWNLOAD**

Parent protocol:
`docs/research/sc001-e008-discovery-staged-acquisition-protocol-v1.0.md`

Frozen implementation:
`research/sc001/sc001_e008_discovery_staged_acquisition.py`

Git blob SHA:
`99cc3c0d9dccad2eae3bf446cfae9a3ddfb112a0`

Frozen properties:
- exact eight Discovery dates only;
- source identities read only from exact `E008_DISCOVERY_METADATA_PREFLIGHT_PASS` report;
- no automatic rediscovery/substitution during acquisition;
- exact HTTPS `static.okx.com` filename/Content-Length recheck before GET;
- resumable `.part` downloads;
- 10 GB free-space reserve;
- trade stage plus four fixed two-day L2 batches A-D;
- all L2 batches <1.2 GB compressed under frozen metadata;
- local SHA256 after completion;
- ZIP CRC/basic schema check for trades;
- full compressed tar/gzip readability + single regular member for L2;
- no fills/spread capture/markout/fees/inventory P&L/profitability;
- Confirmation/Q2/Validation/Final remain closed.

Any implementation change after first body download requires a new implementation version and explicit defect-only justification; date/source/strategy semantics may not be tuned from outcomes.
