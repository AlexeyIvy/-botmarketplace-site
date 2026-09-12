# SC001-DATA-Q007 Implementation Freeze v0.1

Status: **FROZEN BEFORE Q007 RUN**

Protocol: `docs/research/sc001-data-q007-okx-l2-q1-preflight-v0.1.md`  
Protocol commit: `448c29985811044b2717bdb592a5eb4810461bc5`  
Engine commit: `47b156d28ab6bbf8aef98ea14b21833860b4566e`  
Launcher commit: `cc4d01ddf5f3e5a265a58e8b5763e3da4cb2e859`

Frozen properties:

- exactly five already-open 2024-Q1 OKX dates;
- module `4` only;
- exact `BTC-USDT-SWAP-L2orderbook-400lv-YYYY-MM-DD.tar.gz` identity;
- metadata/HEAD only;
- zero L2 body downloads;
- no strategy or midpoint calculations;
- Q2, formal Validation, and Final remain closed;
- 20 MB network/workspace caps and 4 GB free-space reserve.

Any change after observing Q007 sizes requires a separately versioned acquisition protocol; sizes may be used only to construct safe staged batches, not to choose performance dates.
