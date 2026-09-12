# SC001-DATA-Q009A Implementation Freeze v0.1

Status: **FROZEN BEFORE BATCH-A DOWNLOAD**

Protocol:
`docs/research/sc001-data-q009a-okx-l2-q1-batch-a-protocol-v0.1.md`

Protocol commit:
`c8db51f50ccea43f70dfc89cd641e333b8068b49`

Engine:
`research/sc001/sc001_data_q009a_okx_l2_batch_a.py`

Engine commit:
`92e59c728b55a77ac068cc4970f4503dc63d3c73`

Frozen scope:
- 2024-01-14 L2, 426,641,072 bytes;
- 2024-01-31 L2, 519,114,508 bytes;
- expected market-data total 945,755,580 bytes;
- full-day replay qualification only;
- no TFI;
- no midquote response;
- no strategy/execution P&L;
- no Q2, formal Validation or Final.

The engine reuses the Q008 full-day semantic replay implementation from pinned commit `d4aa9720e43a39e215af7d866bd273c68340381c` and keeps the cumulative market-data network cap at 1.2 GB, below the project's 2 GB/run hard limit.
